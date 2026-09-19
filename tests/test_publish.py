import unittest
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET
from regwatch.engine import empty_state, apply_observations, set_health
from regwatch.publish import build_site, check_site
from test_engine import SOURCE
from copy import deepcopy
from bs4 import BeautifulSoup

class PublishTests(unittest.TestCase):
    def test_current_configuration_and_collector_summary_are_labeled(self):
        s=empty_state()
        source={**SOURCE,'mode':'json-page'}
        apply_observations(s,source,[dict(url='https://example.org/snapshot',title='Snapshot',summary='12 records')],'2026-09-19T01:00:00Z')
        before=deepcopy(s)
        configured={**source,'document_type':'rules','topics':['competition']}
        with tempfile.TemporaryDirectory() as d:
            build_site(s,[configured],Path(d),'https://example.org/watch')
            row=ET.parse(Path(d)/'feeds/all.xml').find('./channel/item')
            html=BeautifulSoup(row.findtext('description'),'html.parser')
            self.assertEqual(html.find('dt',string='Document type (configured)').find_next_sibling('dd').get_text(),'rules')
            self.assertEqual(html.find('dt',string='Document type at observation').find_next_sibling('dd').get_text(),'publication')
            self.assertEqual(html.find('dt',string='Topics (configured)').find_next_sibling('dd').get_text(),'competition')
            self.assertEqual(html.find('dt',string='Topics at observation').find_next_sibling('dd').get_text(),'news')
            self.assertEqual(html.find('dt',string='Collector snapshot summary').find_next_sibling('dd').get_text(),'12 records')
            self.assertEqual(row.findtext('{*}document_type'),'publication')
        self.assertEqual(before,s)

    def test_dashboard_preview_is_bounded_and_metadata_is_expandable(self):
        import json
        s=empty_state()
        source={**SOURCE,'publisher_name':'Full agency','title':'News section'}
        apply_observations(s,source,[dict(url=f'https://example.org/item/{i}',title=f'Headline {i}',published_at='2026-09-18') for i in range(102)],'2026-09-19T01:00:00Z')
        before=deepcopy(s)
        with tempfile.TemporaryDirectory() as d:
            build_site(s,[source],Path(d),'https://example.org/watch')
            page=BeautifulSoup((Path(d)/'index.html').read_text('utf-8'),'html.parser')
            current=page.find('h2',string='Current regulatory inventory').parent
            self.assertEqual(len(current.select('li')),100)
            self.assertIn('Showing 100 of 102',current.get_text())
            self.assertIn('retained regulatory-focus items',current.get_text())
            self.assertIsNotNone(current.find('a',href='api/v1/items.json'))
            entry=current.find('li')
            self.assertIsNotNone(entry.find('h3').find('a'))
            details=entry.find('details')
            self.assertEqual(details.find('summary').get_text(),'Metadata and source evidence')
            self.assertFalse(details.has_attr('open'))
            details.decompose()
            for expected in ('Full agency','News section','Source published: 2026-09-18','Observed: 2026-09-19T01:00:00Z'):
                self.assertIn(expected,entry.get_text())
            self.assertEqual(len(json.loads((Path(d)/'api/v1/items.json').read_text('utf-8'))['records']),102)
            rss=ET.parse(Path(d)/'feeds/all.xml').findall('./channel/item')
            self.assertEqual(len(rss),102)
            self.assertIn('Source publication date (raw)',rss[0].findtext('description'))
            self.assertNotIn('<details>',rss[0].findtext('description'))
            self.assertIsNotNone(page.find('a',href='#subscriptions'))
            self.assertIsNotNone(page.find('a',href='#source-coverage'))
        self.assertEqual(before,s)

    def test_current_feeds_deduplicate_without_removing_observation_events(self):
        s=empty_state()
        second={**SOURCE,'id':'example-laws','title':'Laws'}
        other={**SOURCE,'id':'another-source','regulator_id':'another'}
        apply_observations(s,SOURCE,[dict(url='https://example.org/shared',title='Dated',published_at='2026-09-18')],'2026-09-19T01:00:00Z')
        apply_observations(s,second,[dict(url='https://example.org/shared',title='Undated overlap')],'2026-09-19T02:00:00Z')
        apply_observations(s,other,[dict(url='https://example.org/shared',title='Other regulator',published_at='2026-09-18')],'2026-09-19T03:00:00Z')
        with tempfile.TemporaryDirectory() as d:
            build_site(s,[SOURCE,second,other],Path(d),'https://example.org/watch')
            self.assertEqual(len(ET.parse(Path(d)/'feeds/all.xml').findall('./channel/item')),3)
            self.assertEqual(len(ET.parse(Path(d)/'feeds/current/all.xml').findall('./channel/item')),1)
            rows=ET.parse(Path(d)/'feeds/current/example.xml').findall('./channel/item')
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0].findtext('guid'),s['events'][0]['event_id'])
            self.assertIn('Dated',rows[0].findtext('title'))
            self.assertIn('Other regulator',ET.parse(Path(d)/'feeds/current/another.xml').findtext('./channel/item/title'))
            self.assertEqual(ET.parse(Path(d)/'feeds/current/all.xml').findtext('./channel/item/guid'),s['events'][2]['event_id'])
            page=BeautifulSoup((Path(d)/'index.html').read_text('utf-8'),'html.parser')
            self.assertIsNotNone(page.find('a',href='feeds/current/example.xml'))
            check_site(Path(d))

    def test_regulator_sections_and_health_detection_are_explicit(self):
        sources=[{**SOURCE,'id':'tcct-news','regulator_id':'tcct','title':'News section','publisher_name':'Full commission'},
                 {**SOURCE,'id':'tcct-laws','regulator_id':'tcct','title':'Laws section','publisher_name':'Full commission'}]
        s=empty_state()
        set_health(s,sources[0],'failed','2026-09-19T01:00:00Z','<script>bad</script>')
        set_health(s,sources[1],'blocked','2026-09-19T02:00:00Z','Denied')
        with tempfile.TemporaryDirectory() as d:
            build_site(s,sources,Path(d),'https://example.org/watch')
            page=BeautifulSoup((Path(d)/'index.html').read_text('utf-8'),'html.parser')
            subscriptions=page.find(id='subscriptions')
            self.assertEqual(len(subscriptions.find_all('a',href='feeds/tcct.xml')),1)
            self.assertEqual(subscriptions.find('a',href='feeds/tcct-news.xml').get_text(),'News section')
            self.assertEqual(subscriptions.find('a',href='feeds/tcct-laws.xml').get_text(),'Laws section')
            self.assertIn('Full commission',subscriptions.get_text())
            rows=ET.parse(Path(d)/'feeds/health.xml').findall('./channel/item')
            self.assertEqual(rows[0].findtext('{*}source_id'),'tcct-laws')
            self.assertEqual(rows[0].findtext('pubDate'),'Sat, 19 Sep 2026 02:00:00 GMT')
            self.assertIn('Detection time, not publication time',rows[0].findtext('description'))
            self.assertIsNone(BeautifulSoup(rows[1].findtext('description'),'html.parser').find('script'))

    def test_readable_safe_metadata_does_not_rewrite_event_provenance(self):
        s=empty_state()
        source={**SOURCE,'title':'Original publisher','limitations':['<img src=x onerror=alert(1)>']}
        apply_observations(s,source,[dict(url='https://example.org/item/1',title='Full <script>alert(1)</script> headline',summary='<b>Source summary</b>',published_at='2026-09-18',publication_date_raw='18 กันยายน 2569',modified_at='2026-09-19T00:00:00Z',document_id='DOC-1',document_url='javascript:alert(1)')],'2026-09-19T01:00:00Z')
        configured={**source,'publisher_name':'Full agency name','title':'Configured section <news>'}
        before=deepcopy(s)
        with tempfile.TemporaryDirectory() as d:
            build_site(s,[configured],Path(d),'https://example.org/watch')
            row=ET.parse(Path(d)/'feeds/all.xml').find('./channel/item')
            description=row.findtext('description')
            html=BeautifulSoup(description,'html.parser')
            for expected in ('Full <script>alert(1)</script> headline','Full agency name','Original publisher','Configured section <news>','example-news','Document type (configured)','Topics (configured)','18 กันยายน 2569','2026-09-18','2026-09-19T00:00:00Z','Detected / observed','2026-09-19T01:00:00Z','DOC-1','<b>Source summary</b>','Not assessed','unreviewed','midnight UTC'):
                self.assertIn(expected,html.get_text(' ',strip=True))
            self.assertIsNone(html.find(['script','img','b']))
            self.assertTrue(all(a['href'].startswith(('https://','http://')) for a in html.find_all('a')))
            self.assertEqual(row.findtext('guid'),s['events'][0]['event_id'])
            self.assertEqual(row.findtext('{*}publisher'),'Original publisher')
            page=BeautifulSoup((Path(d)/'index.html').read_text('utf-8'),'html.parser')
            current=page.find('h2',string='Current regulatory inventory').parent
            self.assertIn('Full agency name',current.get_text())
            self.assertIsNone(current.find(['script','img','b']))
        self.assertEqual(before,s)

    def test_source_chronology_is_distinct_from_detection_chronology(self):
        s=empty_state()
        apply_observations(s,SOURCE,[dict(url='https://example.org/new',title='Newest official',published_at='2026-09-18')],'2026-09-19T01:00:00Z')
        apply_observations(s,SOURCE,[dict(url='https://example.org/old',title='Old official',published_at='2020-01-01'),dict(url='https://example.org/unknown',title='Undated')],'2026-09-19T02:00:00Z')
        apply_observations(s,SOURCE,[dict(url='https://example.org/modified',title='Modified only',modified_at='2026-09-17T10:30:00+07:00')],'2026-09-19T03:00:00Z')
        apply_observations(s,SOURCE,[dict(url='https://example.org/old',title='Old official revised',published_at='2020-01-01')],'2026-09-19T04:00:00Z')
        with tempfile.TemporaryDirectory() as d:
            build_site(s,[SOURCE],Path(d),'https://example.org/watch')
            for name in ('all','example','example-news','topic-news'):
                rows=ET.parse(Path(d)/f'feeds/{name}.xml').findall('./channel/item')
                self.assertIn('Newest official',rows[0].findtext('title'))
                self.assertIn('Undated',rows[-1].findtext('title'))
                self.assertEqual(rows[0].findtext('pubDate'),'Fri, 18 Sep 2026 00:00:00 GMT')
                self.assertEqual(rows[0].findtext('{*}rss_date_basis'),'published_at')
                self.assertEqual(rows[0].findtext('{*}rss_date_precision'),'day')
                self.assertEqual(rows[1].findtext('pubDate'),'Thu, 17 Sep 2026 03:30:00 GMT')
                self.assertEqual(rows[1].findtext('{*}rss_date_basis'),'modified_at')
                self.assertIsNone(rows[-1].find('pubDate'))
            changes=ET.parse(Path(d)/'feeds/changes.xml').findall('./channel/item')
            self.assertIn('Old official revised',changes[0].findtext('title'))
            self.assertEqual(changes[0].findtext('pubDate'),'Sat, 19 Sep 2026 04:00:00 GMT')
            self.assertEqual(changes[0].findtext('{*}rss_date_basis'),'observed_at')
            self.assertEqual(ET.parse(Path(d)/'feeds/baseline.xml').findtext('./channel/item/pubDate'),'Fri, 18 Sep 2026 00:00:00 GMT')
            current=(Path(d)/'index.html').read_text('utf-8').split('<h2>Current regulatory inventory</h2>')[1].split('</section>')[0]
            self.assertLess(current.index('Newest official'),current.index('Modified only'))
            self.assertLess(current.index('Old official revised'),current.index('Undated'))

    def test_state_reload_preserves_generated_bytes(self):
        import json
        from regwatch.storage import encode
        s=empty_state()
        apply_observations(s,SOURCE,[dict(url='https://example.org/item/1',title='A')],'2026-09-19T01:00:00Z')
        with tempfile.TemporaryDirectory() as d:
            build_site(s,[SOURCE],Path(d),'https://example.org/watch')
            before={p.relative_to(d):p.read_bytes() for p in Path(d).rglob('*') if p.is_file()}
            build_site(json.loads(encode(s)),[SOURCE],Path(d),'https://example.org/watch')
            after={p.relative_to(d):p.read_bytes() for p in Path(d).rglob('*') if p.is_file()}
            self.assertEqual(before,after)

    def test_window_does_not_remove_json_history(self):
        import json
        s=empty_state()
        apply_observations(s,SOURCE,[dict(url=f'https://example.org/item/{i}',title=f'A {i}') for i in range(3)],'2026-09-19T01:00:00Z')
        with tempfile.TemporaryDirectory() as d:
            build_site(s,[SOURCE],Path(d),'https://example.org/watch',limit=2)
            self.assertEqual(len(ET.parse(Path(d)/'feeds/all.xml').findall('./channel/item')),2)
            self.assertEqual(len(json.loads((Path(d)/'api/v1/events.json').read_text('utf-8'))['records']),3)

    def test_feed_retention_and_machine_identity(self):
        s=empty_state()
        apply_observations(s,SOURCE,[dict(url='https://example.org/item/1',title='A & <B>')],'2026-09-19T01:00:00Z')
        with tempfile.TemporaryDirectory() as d:
            build_site(s,[SOURCE],Path(d),'https://example.org/watch')
            before=(Path(d)/'feeds/all.xml').read_bytes()
            self.assertIn('No post-baseline events recorded', (Path(d)/'index.html').read_text('utf-8'))
            self.assertEqual(len(ET.fromstring(before).findall('./channel/item')),1)
            self.assertEqual(len(ET.parse(Path(d)/'feeds/changes.xml').findall('./channel/item')),0)
            set_health(s,SOURCE,'failed','2026-09-19T02:00:00Z','timeout')
            build_site(s,[SOURCE],Path(d),'https://example.org/watch')
            self.assertEqual(before,(Path(d)/'feeds/all.xml').read_bytes())
            check_site(Path(d))
