import unittest,tempfile
from pathlib import Path
from xml.etree import ElementTree as ET
from regwatch.engine import empty_state,apply_observations
from regwatch.publish import build_site
from test_engine import SOURCE

class PriorityFeeds(unittest.TestCase):
    def test_tcct_press_archive_is_in_regulatory_priority(self):
        from regwatch.registry import load_registry
        root=Path(__file__).resolve().parents[1]
        sources=load_registry(root/'config/sources.yml')
        source=next(s for s in sources if s['id']=='tcct-listing-02')
        self.assertEqual(source.get('feed_priority'),'regulatory')

    def test_priority_dedup_uses_regulatory_observation_even_if_news_is_newer(self):
        law={**SOURCE,'id':'pdpc-law','feed_priority':'regulatory'}
        news={**SOURCE,'id':'pdpc-news','feed_priority':'radar'}
        state=empty_state()
        apply_observations(state,law,[{'url':'https://example.org/shared','title':'Regulatory title'}],'2026-09-19T01:00:00Z')
        apply_observations(state,news,[{'url':'https://example.org/shared','title':'News title'}],'2026-09-19T02:00:00Z')
        with tempfile.TemporaryDirectory() as d:
            build_site(state,[law,news],Path(d),'https://example.org')
            rows=ET.parse(Path(d)/'feeds/regulatory.xml').findall('./channel/item')
            self.assertEqual(len(rows),1)
            self.assertIn('Regulatory title',rows[0].findtext('title'))

    def test_pdpc_category_fixtures_keep_dates_and_do_not_select_menus(self):
        from regwatch.registry import load_registry
        from regwatch.adapters import parse_document
        root=Path(__file__).resolve().parents[1]
        sources=load_registry(root/'config/sources.yml')
        for sid in ['pdpc-laws','pdpc-announcements','pdpc-news']:
            source=next(s for s in sources if s['id']==sid)
            rows,_=parse_document(source,(root/source['fixture']).read_bytes()+b'<nav><a href="/12345/">Menu</a></nav>',source['url'])
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]['published_at'],'2026-09-10' if sid=='pdpc-news' else '2025-10-21')

    def test_priority_view_excludes_publicity_without_deleting_history(self):
        law={**SOURCE,'id':'pdpc-law','regulator_id':'pdpc','feed_priority':'regulatory'}
        news={**SOURCE,'id':'cifs-news','regulator_id':'cifs','feed_priority':'radar'}
        state=empty_state()
        for source in [law,news]:
            row={'url':'https://example.org/'+source['id'],'title':source['id'],'published_at':'2026-09-18'}
            apply_observations(state,source,[row],'2026-09-19T01:00:00Z')
            apply_observations(state,source,[{**row,'title':row['title']+' revised'}],'2026-09-19T02:00:00Z')
        before=len(state['events'])
        with tempfile.TemporaryDirectory() as d:
            build_site(state,[law,news],Path(d),'https://example.org')
            def titles(name):return [r.findtext('title') for r in ET.parse(Path(d)/('feeds/'+name+'.xml')).findall('./channel/item')]
            self.assertEqual(len(titles('changes')),1)
            self.assertIn('pdpc-law',titles('changes')[0])
            self.assertEqual(len(titles('changes-all')),2)
            self.assertEqual(len(titles('all')),4)
            self.assertEqual(len(titles('regulatory')),1)
            self.assertIn('Regulatory source coverage:',ET.parse(Path(d)/'feeds/changes.xml').findtext('./channel/description'))
            self.assertEqual(len(titles('cifs')),2)
            self.assertIn('feeds/regulatory.xml',(Path(d)/'index.html').read_text('utf8'))
        self.assertEqual(len(state['events']),before)
