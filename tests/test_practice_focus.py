import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

from regwatch.engine import apply_observations, empty_state, set_health
from regwatch.practices import load_practices
from regwatch.publish import build_site
from test_engine import SOURCE


class PracticeFocusTests(unittest.TestCase):
    def test_repository_practices_include_cross_cutting_tech_lawyer_view(self):
        root=Path(__file__).resolve().parents[1]
        sources=__import__('regwatch.registry',fromlist=['load_registry']).load_registry(root/'config/sources.yml')
        practices=load_practices(root/'config/practices.yml',sources)
        self.assertEqual(len(practices),9)
        tech=next(p for p in practices if p['slug']=='tech-lawyer-digital-platforms')
        for regulator in ('pdpc','etda','mdes','nbtc','tcct','ocpb','tcc','ncsa','thaicert','ccib'):
            self.assertIn(regulator,tech['regulator_ids'])

    def test_unknown_regulator_and_duplicate_slug_fail_closed(self):
        sources=[{**SOURCE,'regulator_id':'pdpc'}]
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'practices.yml'
            path.write_text('schema_version: "1.0"\npractices:\n- slug: privacy\n  title: Privacy\n  summary: Review\n  regulator_ids: [missing]\n',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'Unknown practice regulator'):
                load_practices(path,sources)
            path.write_text('schema_version: "1.0"\npractices:\n- &p\n  slug: privacy\n  title: Privacy\n  summary: Review\n  regulator_ids: [pdpc]\n- <<: *p\n',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'Duplicate practice slug'):
                load_practices(path,sources)

    def test_practice_page_and_feeds_are_scoped_and_disclose_coverage(self):
        pdpc={**SOURCE,'id':'pdpc-law','regulator_id':'pdpc','title':'PDPC laws','publisher_name':'PDPC'}
        tcct={**SOURCE,'id':'tcct-orders','regulator_id':'tcct','title':'TCCT orders','publisher_name':'TCCT'}
        tax={**SOURCE,'id':'rd-tax','regulator_id':'rd','title':'Revenue notices','publisher_name':'Revenue Department'}
        state=empty_state()
        apply_observations(state,pdpc,[{'url':'https://example.org/privacy','title':'Privacy regulation','published_at':'2026-09-18'}],'2026-09-19T01:00:00Z')
        apply_observations(state,tcct,[{'url':'https://example.org/platform','title':'Platform competition order','published_at':'2026-09-19'}],'2026-09-19T02:00:00Z')
        apply_observations(state,tcct,[{'url':'https://example.org/platform','title':'Platform competition order revised','published_at':'2026-09-19'}],'2026-09-19T03:00:00Z')
        apply_observations(state,tax,[{'url':'https://example.org/tax','title':'Unrelated tax notice','published_at':'2026-09-19'}],'2026-09-19T04:00:00Z')
        set_health(state,pdpc,'blocked','2026-09-19T05:00:00Z','HTTP 403')
        practice={'slug':'tech-lawyer-digital-platforms','title':'Tech Lawyer & Digital Platforms','summary':'Cross-cutting digital practice view.','regulator_ids':['pdpc','tcct']}
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)
            result=build_site(state,[pdpc,tcct,tax],out,'https://example.org/watch',practices=[practice])
            page=BeautifulSoup((out/'practice/tech-lawyer-digital-platforms/index.html').read_text('utf-8'),'html.parser')
            text=page.get_text(' ',strip=True)
            self.assertIn('Tech Lawyer & Digital Platforms',text)
            self.assertIn('Platform competition order revised',text)
            self.assertIn('Privacy regulation',text)
            self.assertNotIn('Unrelated tax notice',text)
            self.assertIn('Incomplete coverage',text)
            self.assertIn('PDPC laws',text)
            self.assertEqual(page.find('a',string='Current-items RSS')['href'],'../../feeds/practice-tech-lawyer-digital-platforms.xml')
            self.assertEqual(page.find('a',string='Changes RSS')['href'],'../../feeds/practice-tech-lawyer-digital-platforms-changes.xml')
            current=ET.parse(out/'feeds/practice-tech-lawyer-digital-platforms.xml').findall('./channel/item')
            changes=ET.parse(out/'feeds/practice-tech-lawyer-digital-platforms-changes.xml').findall('./channel/item')
            self.assertEqual(len(current),2)
            self.assertIn('Platform competition order revised',current[0].findtext('title'))
            self.assertEqual(len(changes),1)
            self.assertIn('Platform competition order revised',changes[0].findtext('title'))
            self.assertIn('Incomplete coverage',ET.parse(out/'feeds/practice-tech-lawyer-digital-platforms.xml').findtext('./channel/description'))
            home=BeautifulSoup((out/'index.html').read_text('utf-8'),'html.parser')
            self.assertEqual(home.find('a',string='Tech Lawyer & Digital Platforms')['href'],'practice/tech-lawyer-digital-platforms/')
            self.assertEqual(result['practices'],1)


if __name__=='__main__':
    unittest.main()
