import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import yaml
from regwatch.engine import empty_state, apply_observations, set_health
from regwatch.collector import collect_source
from regwatch.registry import load_registry, allowed_url
from regwatch.storage import validate_state, load_state, writer_lock
from regwatch.transport import Transport, AccessBlocked
from regwatch.adapters import parse_document
from test_engine import SOURCE

class FakeTransport:
    def __init__(self,responses): self.responses=iter(responses); self.calls=[]
    def fetch(self,url,**kwargs):
        self.calls.append((url,kwargs))
        value=next(self.responses)
        if isinstance(value,Exception): raise value
        return (200,{},value,url)

class StateSafetyTests(unittest.TestCase):
    def test_multiple_declared_discovery_pages_and_response_budget(self):
        s=empty_state()
        source={**SOURCE,'allowed_hosts':['example.org'],'mode':'html','max_pages':2,
                'start_urls':['https://example.org/second'],'max_response_bytes':8_000_000}
        class BoundedTransport:
            def fetch(self,url,**kwargs):
                if kwargs.get('max_bytes',4_000_000)<8_000_000: raise ValueError('response exceeds budget')
                return 200,{},f'<a href="{url}/item">Article</a>'.encode(),url
        collect_source(s,source,'2026-09-19T00:00:00Z',BoundedTransport())
        self.assertEqual(s['sources'][SOURCE['id']]['status'],'healthy')
        self.assertEqual(len(s['items']),2)

    def test_first_pdf_fingerprint_is_not_a_revision(self):
        s=empty_state()
        row={'url':'https://example.org/a.pdf','title':'A','document_url':'https://example.org/a.pdf'}
        apply_observations(s,SOURCE,[row],'2026-09-19T00:00:00Z')
        apply_observations(s,SOURCE,[{**row,'attachment_sha256':'a'*64}],'2026-09-20T00:00:00Z')
        self.assertEqual(len(s['events']),1)
        self.assertEqual(next(iter(s['sources'][SOURCE['id']]['observations'].values()))['attachment_sha256'],'a'*64)
        apply_observations(s,SOURCE,[{**row,'attachment_sha256':'b'*64}],'2026-09-21T00:00:00Z')
        self.assertEqual(s['events'][-1]['event_type'],'UPDATED_ATTACHMENT')

    def test_distinct_source_titles_do_not_flap(self):
        state=empty_state()
        a={'url':'https://example.org/1','title':'A'}
        b={**SOURCE,'id':'example-other'}
        apply_observations(state,SOURCE,[a],'2026-09-19T00:00:00Z')
        apply_observations(state,b,[{**a,'title':'B'}],'2026-09-19T01:00:00Z')
        apply_observations(state,SOURCE,[a],'2026-09-19T02:00:00Z')
        self.assertEqual(len(state['items']),1)
        self.assertEqual(len(state['events']),2)
        validate_state(state)

    def test_same_title_different_urls_are_distinct(self):
        s=empty_state()
        apply_observations(s,SOURCE,[{'url':'https://example.org/1','title':'A'},{'url':'https://example.org/2','title':'A'}],'2026-09-19T00:00:00Z')
        self.assertEqual(len(s['items']),2)

    def test_failure_retains_items_and_events(self):
        s=empty_state()
        apply_observations(s,SOURCE,[{'url':'https://example.org/1','title':'A'}],'2026-09-19T00:00:00Z')
        old=deepcopy(s['events'])
        source={**SOURCE,'allowed_hosts':['example.org'],'mode':'html'}
        collect_source(s,source,'2026-09-20T00:00:00Z',FakeTransport([TimeoutError('timeout')]))
        self.assertEqual(s['events'],old)
        self.assertEqual(len(s['items']),1)
        self.assertEqual(s['sources'][source['id']]['status'],'failed')

    def test_omission_retains_observation(self):
        s=empty_state()
        apply_observations(s,SOURCE,[{'url':'https://example.org/1','title':'A'}],'2026-09-19T00:00:00Z')
        apply_observations(s,SOURCE,[{'url':'https://example.org/2','title':'B'}],'2026-09-20T00:00:00Z')
        self.assertEqual(len(s['sources'][SOURCE['id']]['observations']),2)
        self.assertEqual(s['events'][-1]['event_type'],'NEW')

    def test_pdf_change_and_bad_document_retention(self):
        s=empty_state()
        source={**SOURCE,'allowed_hosts':['example.org'],'mode':'html','asset_budget':1}
        html=b'<a href="/docs/1.pdf">Order A</a>'
        collect_source(s,source,'2026-09-19T00:00:00Z',FakeTransport([html,b'%PDF-1 A']))
        collect_source(s,source,'2026-09-20T01:00:00Z',FakeTransport([html,b'%PDF-1 B']))
        self.assertEqual(s['events'][-1]['event_type'],'UPDATED_ATTACHMENT')
        old=deepcopy(s['events'])
        collect_source(s,source,'2026-09-21T02:00:00Z',FakeTransport([html,b'<html>Error</html>']))
        self.assertEqual(s['events'],old)
        self.assertEqual(s['sources'][SOURCE['id']]['status'],'degraded')

    def test_repeated_attachment_failure_does_not_fake_recovery(self):
        s=empty_state()
        source={**SOURCE,'allowed_hosts':['example.org'],'mode':'html','asset_budget':1}
        html=b'<a href="/docs/1.pdf">Order A</a>'
        for day in [19,20]:
            collect_source(s,source,f'2026-09-{day}T00:00:00Z',FakeTransport([html,b'<html>Error</html>']))
        self.assertEqual([e['status'] for e in s['health_events']],['degraded'])

    def test_suspicious_drop(self):
        s=empty_state(); source={**SOURCE,'mode':'html','allowed_hosts':['example.org']}
        apply_observations(s,source,[{'url':f'https://example.org/{i}','title':str(i)} for i in range(10)],'2026-09-19T00:00:00Z')
        collect_source(s,source,'2026-09-20T00:00:00Z',FakeTransport([b'<a href="/1">1</a>']))
        self.assertEqual(s['sources'][SOURCE['id']]['last_count'],10)
        self.assertEqual(s['sources'][SOURCE['id']]['status'],'failed')

    def test_health_transitions_deduplicated(self):
        s=empty_state()
        for status in ['failed','failed','healthy','healthy']:
            set_health(s,SOURCE,status,'2026-09-19T00:00:00Z','error' if status=='failed' else None)
        self.assertEqual(len(s['health_events']),2)

    def test_corrupt_state_rejected(self):
        for bad in [{}, {'schema_version':'2.0'}, {**empty_state(),'events':[{}]}]:
            with self.assertRaises(ValueError): validate_state(bad)

    def test_missing_state_does_not_reset_history(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError): load_state(Path(d)/'missing.json')

    def test_pdf_validators_and_periodic_full_download(self):
        s=empty_state()
        source={**SOURCE,'allowed_hosts':['example.org'],'mode':'html','asset_budget':1}
        html=b'<a href="/docs/1.pdf">Order A</a>'
        class ConditionalTransport:
            def __init__(self,day): self.day=day; self.headers=None
            def fetch(self,url,**kwargs):
                if not url.endswith('.pdf'): return 200,{},html,url
                self.headers=kwargs.get('headers',{})
                return (304,{},b'',url) if self.day==2 else (200,{'ETag':'v1'},b'%PDF-1 A',url)
        first=ConditionalTransport(1)
        collect_source(s,source,'2026-09-01T00:00:00Z',first)
        second=ConditionalTransport(2)
        collect_source(s,source,'2026-09-02T01:00:00Z',second)
        self.assertEqual(second.headers,{'If-None-Match':'v1'})
        third=ConditionalTransport(9)
        collect_source(s,source,'2026-09-09T00:00:00Z',third)
        self.assertEqual(third.headers,{})
        self.assertEqual(len(s['events']),1)

    def test_lock_is_exclusive(self):
        with tempfile.TemporaryDirectory() as d:
            with writer_lock(d):
                with self.assertRaises(FileExistsError):
                    with writer_lock(d): pass
            self.assertFalse((Path(d)/'.regwatch.lock').exists())

class NetworkSafetyTests(unittest.TestCase):
    def test_robots_literal_query_does_not_become_blanket_denial(self):
        policy=b'User-agent: *\nDisallow: /?\nDisallow: /download/\n'
        t=Transport(['example.org'])
        with patch.object(t,'_raw',side_effect=[(200,{},policy),(200,{},b'news')]):
            self.assertEqual(t.fetch('https://example.org/more_news.php?cid=2')[2],b'news')
        for url in ['https://example.org/?x=1','https://example.org/download/file.pdf']:
            t=Transport(['example.org'])
            with patch.object(t,'_raw',return_value=(200,{},policy)) as req:
                with self.assertRaises(AccessBlocked):t.fetch(url)
                self.assertEqual(req.call_count,1)

    def test_robots_wildcards_longest_match_and_explicit_bot_group(self):
        policy=b'User-agent: *\nDisallow: /private/*\nAllow: /private/public$\nUser-agent: ThaiRegulatoryWatch\nDisallow: /secret/\nDisallow: /*.pdf$'
        t=Transport(['example.org'])
        with patch.object(t,'_raw',return_value=(200,{},policy)):
            with self.assertRaises(AccessBlocked):t.fetch('https://example.org/a.pdf')
            with self.assertRaises(AccessBlocked):t.fetch('https://example.org/secret/a')

    def test_allowlist_exact_host(self):
        for url in ['https://example.org.evil.test/','https://evil.test/','http://example.org/','https://example.org:8443/']:
            with self.assertRaises(ValueError): allowed_url(url,['example.org'])

    def test_robots_disallow(self):
        t=Transport(['example.org'])
        with patch.object(t,'_raw',return_value=(200,{},b'User-agent: *\nDisallow: /private')) as req:
            with self.assertRaises(AccessBlocked): t.fetch('https://example.org/private')
            self.assertEqual(req.call_count,1)

    def test_excessive_delay_remains_blocked(self):
        t=Transport(['example.org'])
        with patch.object(t,'_raw',return_value=(200,{},b'User-agent: *\nCrawl-delay: 100')) as req:
            for _ in range(2):
                with self.assertRaises(AccessBlocked): t.fetch('https://example.org/a')
            self.assertEqual(req.call_count,1)

    def test_redirect_checks_destination_policy(self):
        t=Transport(['example.org','other.example'])
        responses=[(404,{},b''),(302,{'Location':'https://other.example/private'},b''),(200,{},b'User-agent: *\nDisallow: /')]
        with patch.object(t,'_raw',side_effect=responses) as req:
            with self.assertRaises(AccessBlocked): t.fetch('https://example.org/a')
            self.assertEqual(req.call_count,3)

    def test_robots_redirect_loop_bounded(self):
        t=Transport(['example.org'])
        with patch.object(t,'_raw',return_value=(302,{'Location':'/robots.txt'},b'')) as req:
            with self.assertRaises(AccessBlocked): t.fetch('https://example.org/a')
            self.assertEqual(req.call_count,5)

    def test_unavailable_robots_not_allow(self):
        t=Transport(['example.org'])
        with patch.object(t,'_raw',return_value=(503,{},b'')):
            with self.assertRaises(AccessBlocked): t.fetch('https://example.org/a')

    def test_private_destination_rejected(self):
        from regwatch.transport import public_address
        with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('127.0.0.1',443))]):
            with self.assertRaises(AccessBlocked): public_address('https://example.org/')

class ParserSafetyTests(unittest.TestCase):
    def test_page_hash_ignores_scripts(self):
        source={'mode':'page','content_selector':'main','title':'Page','allowed_hosts':['example.org']}
        a,_=parse_document(source,b'<main>Content<script>x</script></main>','https://example.org/a')
        b,_=parse_document(source,b'<main>Content<script>y</script></main>','https://example.org/a')
        self.assertEqual(a[0]['selected_text_sha256'],b[0]['selected_text_sha256'])

    def test_atom_missing_published_does_not_use_updated(self):
        xml=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>A</title><link href="https://example.org/a"/><updated>2026-09-19T00:00:00Z</updated></entry></feed>'
        rows,_=parse_document({'mode':'rss','allowed_hosts':['example.org']},xml,'https://example.org/feed')
        self.assertIsNone(rows[0]['published_at'])
        self.assertIsNotNone(rows[0]['modified_at'])

    def test_title_date_is_not_publication_date(self):
        rows,_=parse_document({'mode':'html','allowed_hosts':['example.org']},b'<a href="/a">Meeting 2026-09-19</a>','https://example.org/')
        self.assertIsNone(rows[0]['published_at'])

    def test_pagination_scoped(self):
        source={'mode':'html','allowed_hosts':['example.org'],'pagination_selector':'a.next','include_url':'/item/','max_pages':1}
        rows,pages=parse_document(source,b'<a href="/item/1">A</a><a class="next" href="?page=2">Next</a><a class="next" href="https://evil.test/">Bad</a>','https://example.org/')
        self.assertEqual(len(rows),1); self.assertEqual(pages,['https://example.org/?page=2'])

class RegistryTests(unittest.TestCase):
    def test_registry_rejects_collisions(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'config'; p.mkdir()
            for sid in ['all','example','topic-news']:
                s={**SOURCE,'id':sid,'enabled':False,'allowed_hosts':['example.org']}
                (p/'sources.yml').write_text(yaml.safe_dump({'schema_version':'1.0','sources':[s]}),'utf-8')
                with self.assertRaises(ValueError): load_registry(p/'sources.yml')
