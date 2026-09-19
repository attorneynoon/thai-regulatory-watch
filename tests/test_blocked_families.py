"""Qualified official extracts for the PDPC/ETDA/SEC/TISI repair batch."""
from pathlib import Path
import unittest
import yaml
from regwatch.adapters import parse_document
from regwatch.jsonsnapshot import parse_json_snapshot

ROOT = Path(__file__).resolve().parents[1]


class BlockedFamilyExtracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {s['id']: s for s in yaml.safe_load((ROOT / 'config/sources.yml').read_text(encoding='utf8'))['sources']}

    def parse(self, source_id, body=None):
        s = self.sources[source_id]
        return parse_document(s, body if body is not None else (ROOT / s['fixture']).read_bytes(), s['url'])

    def test_news_cards_exclude_services_and_preserve_displayed_dates(self):
        rows, _ = self.parse('pdpc-official-home')
        self.assertEqual(2, len(rows))
        self.assertEqual('https://www.pdpc.or.th/28468/', rows[0]['url'])
        self.assertEqual('2026-09-10', rows[0]['published_at'])
        self.assertIn('เลิศรัฐ', rows[0]['title'])

    def test_office_order_numeric_permalink(self):
        rows, _ = self.parse('pdpc-official-office-orders')
        self.assertEqual(1, len(rows))
        self.assertEqual('https://www.pdpc.or.th/1626/', rows[0]['url'])
        self.assertEqual('2023-01-06', rows[0]['published_at'])

    def test_order_navigation_and_button_deduplication(self):
        body = (ROOT / 'tests/fixtures/repairs/blocked-pdpc-orders-root.html').read_bytes()
        rows, pages = self.parse('pdpc-official-orders', body)
        self.assertEqual([], rows)
        self.assertEqual({f'https://www.pdpc.or.th/adjudication-panel-decisionsummary-{n}/' for n in (1, 2, 3, 4)}, set(pages))
        rows, _ = self.parse('pdpc-official-orders')
        self.assertEqual(1, len(rows))
        self.assertEqual('2024-11-05', rows[0]['published_at'])
        self.assertTrue(rows[0]['document_url'].endswith('PDPC-Committee1-1.66.pdf'))

    def test_etda_full_title_attribute_and_unknown_publication_date(self):
        rows, pages = self.parse('etda-standards')
        self.assertEqual(3, len(rows))
        self.assertTrue(rows[2]['title'].endswith('Publication of Online Customer Reviews)'))
        self.assertTrue(all(row['published_at'] is None for row in rows))
        self.assertEqual({'https://opendata.etda.or.th/th/group/etda-recommendation?page=2'}, set(pages))

    def test_tisi_cards_and_feed_have_explicit_dates(self):
        for source_id, url, date in (
            ('tisi-listing-04', 'https://pr.tisi.go.th/news_11-9-69/', '2026-09-11'),
            ('tisi-listing-05', 'https://pr.tisi.go.th/tisi_market/', '2026-09-07'),
            ('tisi-listing-06', 'https://pr.tisi.go.th/news_11-9-69/', '2026-09-11T03:24:34+00:00'),
        ):
            with self.subTest(source=source_id):
                rows, _ = self.parse(source_id)
                self.assertEqual(1, len(rows))
                self.assertEqual(url, rows[0]['url'])
                self.assertEqual(date, rows[0]['published_at'])

    def test_pdpc_api_fixtures_are_aggregate_snapshots(self):
        for source_id, count in (('pdpc-listing-02', 2), ('pdpc-listing-03', 1)):
            with self.subTest(source=source_id):
                s = self.sources[source_id]
                rows, _ = parse_json_snapshot(s, (ROOT / s['fixture']).read_bytes(), s['url'])
                self.assertEqual(1, len(rows))
                self.assertEqual(s['url'], rows[0]['url'])
                self.assertIn(f'{count} selected', rows[0]['summary'])
                self.assertIsNone(rows[0]['published_at'])

    def test_partial_pages_exclude_unselected_navigation(self):
        for source_id in ('pdpc-official-private-sector', 'sec-listing-02', 'tisi-listing-03'):
            with self.subTest(source=source_id):
                s = self.sources[source_id]
                original = (ROOT / s['fixture']).read_bytes()
                rows, _ = self.parse(source_id, original)
                changed, _ = self.parse(source_id, original + b'<footer>Counter 99999 menu changed</footer>')
                self.assertEqual(1, len(rows))
                self.assertTrue(rows[0]['title'])
                self.assertIsNone(rows[0]['published_at'])
                self.assertEqual(rows[0]['selected_text_sha256'], changed[0]['selected_text_sha256'])


if __name__ == '__main__':
    unittest.main()
