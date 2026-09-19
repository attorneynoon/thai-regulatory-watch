import unittest
from pathlib import Path
from regwatch.registry import load_registry
from regwatch.adapters import parse_document
from regwatch.models import parse_date

ROOT=Path(__file__).resolve().parents[1]

class OfficialFixtureTests(unittest.TestCase):
    def test_tcct_date_and_direct_document(self):
        s=next(s for s in load_registry(ROOT/'config/sources.yml') if s['id']=='tcct-unfair')
        rows,_=parse_document(s,(ROOT/s['fixture']).read_bytes(),s['url'])
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['published_at'],'2026-09-17')
        self.assertTrue(rows[0]['document_url'].endswith('/platform_promotion.pdf'))

    def test_pdpc_attachment_box_duplicate_buttons(self):
        s=next(s for s in load_registry(ROOT/'config/sources.yml') if s['id']=='pdpc-official-consultations')
        rows,_=parse_document(s,(ROOT/s['fixture']).read_bytes(),s['url'])
        self.assertEqual(len(rows),1)
        self.assertTrue(rows[0]['title'].startswith('ข้อหารือที่ ๒/๒๕๖๘'))
        self.assertEqual(rows[0]['published_at'],'2025-07-04')

    def test_english_be_date(self):
        self.assertEqual(parse_date('4 Jul 2568'),'2025-07-04')
