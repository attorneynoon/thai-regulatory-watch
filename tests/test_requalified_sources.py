from pathlib import Path
import unittest
import yaml
from regwatch.adapters import parse_document

ROOT=Path(__file__).resolve().parents[1]

class RequalifiedSources(unittest.TestCase):
    def parse(self,sid):
        source=next(s for s in yaml.safe_load((ROOT/'config/sources.yml').read_text(encoding='utf8'))['sources'] if s['id']==sid)
        return parse_document(source,(ROOT/source['fixture']).read_bytes(),source['url'])[0]

    def test_gppc_article_metadata_not_navigation(self):
        rows=self.parse('pdpc-official-gppc')
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['published_at'],'2026-04-21T14:44:18+07:00')
        self.assertIn('GPPC',rows[0]['summary'])

    def test_dsi_headlines_leave_unknown_dates_unknown(self):
        rows=self.parse('dsi-listing-01')
        self.assertEqual(len(rows),2)
        self.assertTrue(all(r['published_at'] is None for r in rows))
        self.assertTrue(all(r['title']!='Read more' for r in rows))

    def test_etda_featured_and_regular_cards_preserve_raw_dates(self):
        rows=self.parse('etda-listing-03')
        self.assertEqual(len(rows),2)
        self.assertEqual([r['publication_date_raw'] for r in rows],['10 ก.ย. 69','02 ก.ค. 69'])
        self.assertTrue(all(r['summary'] and r['published_at'] is None for r in rows))
