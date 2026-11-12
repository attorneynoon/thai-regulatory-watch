from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
import yaml

from regwatch.adapters import parse_document
from regwatch.registry import load_registry
from test_tcct_collection import SOURCE

ROOT = Path(__file__).resolve().parents[1]
MAPPINGS = {
    'tcct-unfair': 'verdict', 'tcct-merger': 'verdict-mergers',
    'tcct-listing-02': 'giveaway-news', 'tcct-listing-03': 'giveaway-news',
    'tcct-listing-04': 'activity-news', 'tcct-listing-05': 'activity-news',
    'tcct-draft-principles-hearing': 'draft-principles-hearing',
    'tcct-draft-laws-hearing': 'tcct-draft-laws-hearing',
    'tcct-press-2569': 'giveaway-news-2569', 'tcct-activities-2569': 'activity-news-2569',
}


class TcctRegistryTests(unittest.TestCase):
    def load(self, changes=None):
        source = {**deepcopy(SOURCE), 'enabled': True, 'fixture': 'tests/fixture.json', **(changes or {})}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'config').mkdir()
            (root / 'tests').mkdir()
            (root / 'tests/fixture.json').write_text('{}')
            path = root / 'config/sources.yml'
            path.write_text(yaml.safe_dump({'schema_version': '1.0', 'sources': [source]}))
            return load_registry(path)[0]

    def test_exact_tcct_mode_can_traverse_fifty_pages_with_source_specific_pdf_budget(self):
        source = self.load()
        self.assertEqual(source['max_pages'], 50)
        self.assertEqual(source['max_asset_bytes'], 40_000_000)

    def test_tcct_fields_and_bounds_fail_closed(self):
        variants = [
            {'tcct_category_key': 'unobserved'},
            {'url': 'https://www.tcct.or.th/category/wrong'},
            {'tcct_migration_version': 'reset-whenever'},
            {'regulator_id': 'unrelated'},
            {'allowed_hosts': ['www.tcct.or.th']},
            {'start_urls': ['https://www.tcct.or.th/category/verdict']},
            {'max_pages': 101}, {'max_pages': True},
            {'max_asset_bytes': True}, {'max_asset_bytes': 64_000_001},
            {'min_items': 100, 'max_items': 99},
        ]
        for changes in variants:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    self.load(changes)

    def test_generic_sources_keep_ten_page_and_default_asset_contract(self):
        with self.assertRaisesRegex(ValueError, 'max_pages'):
            self.load({'mode': 'html', 'max_pages': 11, 'max_asset_bytes': 15_000_000})
        with self.assertRaises(ValueError):
            self.load({'mode': 'html', 'max_pages': 1, 'max_asset_bytes': 40_000_000})

    def test_tcct_cannot_accidentally_use_generic_single_document_parser(self):
        with self.assertRaisesRegex(ValueError, 'complete-page-set'):
            parse_document(SOURCE, b'{}', SOURCE['url'])

    def test_migration_preserves_old_ids_parent_archives_and_exact_new_scopes(self):
        from regwatch.tcct_api import LISTING_URLS, parse_page
        from regwatch.tcct_collector import candidate
        sources = {source['id']: source for source in load_registry(ROOT / 'config/sources.yml')}
        prior_ids = {'tcct-announcements', 'tcct-orders', 'tcct-unfair', 'tcct-merger',
                     'tcct-official-complaints-prosecution', 'tcct-official-rules-guidelines',
                     *('tcct-listing-0' + str(n) for n in range(1, 8))}
        self.assertTrue(prior_ids <= sources.keys())
        for ident, key in MAPPINGS.items():
            with self.subTest(source=ident):
                source = sources[ident]
                self.assertEqual(source['mode'], 'tcct-api')
                self.assertEqual(source['tcct_category_key'], key)
                self.assertEqual(source['url'], LISTING_URLS[key])
                self.assertEqual(source['validation_status'], 'candidate')
                body = (ROOT / source['fixture']).read_bytes()
                page = parse_page(body, key, 1)
                rows = [candidate(source, record, 'a' * 64) for record in page['records']]
                self.assertGreater(len(rows), 0)
                self.assertEqual(len(rows), len({row['tcct_record_id'] for row in rows}))
                self.assertTrue(all(row['published_at'] is None for row in rows))
                self.assertTrue(all(row['source_metadata']['detail_url'] is None for row in rows))
                self.assertNotIn(b'"owner"', body)
        for ident in prior_ids - MAPPINGS.keys():
            self.assertNotEqual(sources[ident]['mode'], 'tcct-api')


if __name__ == '__main__':
    unittest.main()
