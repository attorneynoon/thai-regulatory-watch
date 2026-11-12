import unittest
from pathlib import Path
from regwatch.registry import load_registry
from regwatch.adapters import parse_document
from regwatch.models import parse_date

ROOT=Path(__file__).resolve().parents[1]

class OfficialFixtureTests(unittest.TestCase):
    def test_retained_legacy_tcct_html_date_and_direct_document(self):
        s={'mode':'html','allowed_hosts':['www.tcct.or.th'],
           'url':'https://www.tcct.or.th/view/1/verdict/TH-TH',
           'link_selector':'.detail a[href], li.list-news a[href]',
           'item_selector':'.detail, li.list-news','date_selector':'.text-red2',
           'include_title':'คำวินิจฉัย'}
        rows,_=parse_document(s,(ROOT/'tests/fixtures/tcct-ruling.html').read_bytes(),s['url'])
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['published_at'],'2026-09-17')
        self.assertTrue(rows[0]['document_url'].endswith('/platform_promotion.pdf'))

    def test_tcct_api_keeps_raw_date_separate_from_unverified_publication_date(self):
        from regwatch.tcct_api import parse_page
        from regwatch.tcct_collector import candidate
        s=next(s for s in load_registry(ROOT/'config/sources.yml') if s['id']=='tcct-unfair')
        page=parse_page((ROOT/s['fixture']).read_bytes(),s['tcct_category_key'],1)
        rows=[candidate(s,record,'a'*64) for record in page['records']]
        self.assertEqual(len(rows),12)
        self.assertIsNone(rows[0]['published_at'])
        self.assertEqual(rows[0]['source_metadata']['source_start_date'],'2026-09-17T00:00:00.000Z')
        self.assertEqual(rows[0]['document_url'],'https://api.tcct.or.th/upload/f0b69f4d-257c-4acc-8434-5111573e0058')

    def test_pdpc_attachment_box_duplicate_buttons(self):
        s=next(s for s in load_registry(ROOT/'config/sources.yml') if s['id']=='pdpc-official-consultations')
        rows,_=parse_document(s,(ROOT/s['fixture']).read_bytes(),s['url'])
        self.assertEqual(len(rows),1)
        self.assertTrue(rows[0]['title'].startswith('ข้อหารือที่ ๒/๒๕๖๘'))
        self.assertEqual(rows[0]['published_at'],'2025-07-04')

    def test_english_be_date(self):
        self.assertEqual(parse_date('4 Jul 2568'),'2025-07-04')
