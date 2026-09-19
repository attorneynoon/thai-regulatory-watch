import unittest,tempfile
from pathlib import Path
from xml.etree import ElementTree as ET
from regwatch.engine import empty_state,apply_observations
from regwatch.publish import build_site
from test_engine import SOURCE

class PriorityFeeds(unittest.TestCase):
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
            self.assertEqual(len(titles('cifs')),2)
            self.assertIn('feeds/regulatory.xml',(Path(d)/'index.html').read_text('utf8'))
        self.assertEqual(len(state['events']),before)
