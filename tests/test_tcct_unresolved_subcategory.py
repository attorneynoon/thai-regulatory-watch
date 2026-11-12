"""Actual CI taxonomy projections with explicitly reconstructed record scaffolding."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from regwatch import tcct_api
from regwatch.collector import collect_source
from regwatch.engine import empty_state
from regwatch.storage import validate_state
from test_tcct_collection import ApiTransport, SOURCE, api_pages, NOW, LATER

FIXTURE = Path(__file__).parent / 'fixtures/tcct-api/activity-news-unresolved-subcategory-projection.json'
PARENT_SOURCE = {**SOURCE, 'id': 'tcct-parent-regression', 'tcct_category_key': 'activity-news',
                 'url': 'https://www.tcct.or.th/category/activity-news'}


def unresolved_fixture():
    return json.loads(FIXTURE.read_text('utf-8'))


def reconstructed_parent_pages(omit_top_level_relation=False):
    """25-record synthetic pagination; five taxonomy records came from CI pages2/3."""
    fixture = unresolved_fixture()
    payloads = api_pages(25, key='activity-news-2569')
    for page in payloads.values():
        page['data']['category'] = deepcopy(fixture['listing_category'])
    payloads[2]['data']['contents'][:4] = [deepcopy(row['record']) for row in fixture['records'][:4]]
    payloads[3]['data']['contents'][0] = deepcopy(fixture['records'][4]['record'])
    if omit_top_level_relation:
        projected_ids = {row['record']['id'] for row in fixture['records']}
        for page in payloads.values():
            for row in page['data']['contents']:
                if row['id'] in projected_ids:
                    row.pop('sub_category')
    return payloads


class UnresolvedSubcategoryParserTests(unittest.TestCase):
    def test_actual_five_projected_ids_and_reconstructed_nulls_preserve_warning(self):
        fixture = unresolved_fixture()
        self.assertEqual(fixture['provenance']['observed_unresolved_records'], 5)
        self.assertIs(fixture['provenance']['top_level_sub_category_presence_captured'], False)
        for entry in fixture['records']:
            raw = entry['record']
            before = deepcopy(raw)
            with self.subTest(record=raw['id']):
                record = tcct_api.normalize_record(raw, 'activity-news')
                self.assertEqual(record['id'], raw['id'])
                self.assertEqual(record['category_id'], raw['category_id'])
                self.assertEqual(record['sub_category_id'], raw['sub_category_id'])
                self.assertIsNone(record['sub_category'])
                self.assertEqual(record['categories'][0]['sub_category_id'], raw['sub_category_id'])
                self.assertIsNone(record['categories'][0]['sub_category'])
                self.assertIn('source_subcategory_unresolved', record['warnings'])
                self.assertEqual(record['category_years_buddhist'], [])
                self.assertNotIn('deleted', record['warnings'])
                self.assertEqual(raw, before)

    def test_top_level_omitted_null_and_resolved_relation_states_remain_distinct(self):
        null_row = unresolved_fixture()['records'][0]['record']
        omitted_row = deepcopy(null_row)
        omitted_row.pop('sub_category')
        resolved_row = api_pages(1, key='activity-news-2569')[1]['data']['contents'][0]
        for state, raw in (('omitted', omitted_row), ('null', null_row), ('resolved', resolved_row)):
            with self.subTest(state=state):
                record = tcct_api.normalize_record(raw, 'activity-news')
                self.assertEqual(record['sub_category_relation_state'], state)
                self.assertEqual(record['sub_category_id'], raw['sub_category_id'])
                if state == 'resolved':
                    self.assertEqual(record['sub_category']['id'], raw['sub_category_id'])
                    self.assertNotIn('source_subcategory_unresolved', record['warnings'])
                else:
                    self.assertIsNone(record['sub_category'])
                    self.assertIn('source_subcategory_unresolved', record['warnings'])

    def test_raw_child_uuid_alone_cannot_prove_a_requested_year_scope(self):
        known_child_id = api_pages(1, key='activity-news-2569')[1]['data']['contents'][0]['sub_category_id']
        for child_id in (None, known_child_id):
            for omitted in (False, True):
                record = unresolved_fixture()['records'][0]['record']
                if child_id:
                    record['sub_category_id'] = child_id
                    record['categories'][0]['sub_category_id'] = child_id
                if omitted:
                    record.pop('sub_category')
                with self.subTest(child_id=child_id, omitted=omitted):
                    with self.assertRaisesRegex(ValueError, 'requested scope'):
                        tcct_api.normalize_record(record, 'activity-news-2569')

    def test_primary_ids_and_mandatory_membership_fields_remain_strict(self):
        mutations = (
            lambda row: row.update(sub_category_id='different-raw-child'),
            lambda row: row['categories'][0].update(sub_category_id=None),
            lambda row: row['categories'][0].pop('sub_category'),
            lambda row: row['categories'][0].pop('sub_category_id'),
        )
        for mutate in mutations:
            row = unresolved_fixture()['records'][0]['record']
            mutate(row)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                tcct_api.normalize_record(row, 'activity-news')

    def test_populated_child_id_parent_and_visibility_checks_remain_strict(self):
        template = api_pages(1, key='activity-news-2569')[1]['data']['contents'][0]
        mutations = (
            lambda row: row['sub_category'].update(id='wrong-populated-id'),
            lambda row: row['sub_category'].update(parent_id='wrong-parent'),
            lambda row: row['categories'][0]['sub_category'].update(id='wrong-populated-id'),
            lambda row: row['categories'][0]['sub_category'].update(parent_id='wrong-parent'),
            lambda row: row['categories'][0]['sub_category'].update(is_active=False),
            lambda row: row['categories'][0]['sub_category'].update(is_delete=True),
        )
        for mutate in mutations:
            row = deepcopy(template)
            mutate(row)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                tcct_api.normalize_record(row, 'activity-news')

    def test_unresolved_child_does_not_relax_record_or_parent_visibility(self):
        mutations = (
            lambda row: row.update(is_active=False),
            lambda row: row.update(is_draft=True),
            lambda row: row['category'].update(is_active=False),
            lambda row: row['categories'][0]['category'].update(is_delete=True),
        )
        for mutate in mutations:
            row = unresolved_fixture()['records'][0]['record']
            mutate(row)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                tcct_api.normalize_record(row, 'activity-news')

    def test_resolved_parent_must_still_match_the_requested_listing_id(self):
        payload = reconstructed_parent_pages()[3]
        payload['data']['category']['id'] = 'different-listing-id'
        with self.assertRaisesRegex(ValueError, 'listing category identifiers'):
            tcct_api.parse_page(payload, 'activity-news', 3)


class UnresolvedSubcategoryCollectionTests(unittest.TestCase):
    def test_complete_parent_is_atomic_retains_all_five_and_is_stable_on_rerun(self):
        for omitted in (False, True):
            with self.subTest(omitted=omitted):
                self.assert_complete_parent(omitted)

    def assert_complete_parent(self, omitted):
        state = empty_state()
        payloads = reconstructed_parent_pages(omit_top_level_relation=omitted)
        test = self

        class InspectBeforeApply(ApiTransport):
            def fetch(self, url, **kwargs):
                test.assertEqual(state['items'], {})
                test.assertEqual(state['events'], [])
                test.assertNotIn('tcct_migration_version', state['sources'][PARENT_SOURCE['id']])
                return super().fetch(url, **kwargs)

        transport = InspectBeforeApply(payloads)
        status = collect_source(state, PARENT_SOURCE, NOW, transport)
        self.assertEqual(status['status'], 'healthy', status.get('last_error'))
        self.assertEqual(status['last_count'], 25)
        self.assertEqual(status['listing_pages_checked'], 3)
        self.assertEqual(status['tcct_listing_warnings']['source_subcategory_unresolved'], 5)
        expected_ids = {entry['record']['id'] for entry in unresolved_fixture()['records']}
        observed = {row['tcct_record_id']: row for row in status['observations'].values()}
        self.assertTrue(expected_ids <= observed.keys())
        for ident in expected_ids:
            metadata = observed[ident]['source_metadata']
            self.assertIsNone(metadata['sub_category'])
            self.assertEqual(metadata['sub_category_relation_state'], 'omitted' if omitted else 'null')
            self.assertTrue(metadata['sub_category_id'])
            self.assertEqual(metadata['category_years_buddhist'], [])
        events = deepcopy(state['events'])
        self.assertEqual(len(events), 25)
        self.assertTrue(all(event['event_type'] == 'BASELINE' for event in events))
        status = collect_source(state, PARENT_SOURCE, LATER, ApiTransport(payloads))
        self.assertEqual(status['status'], 'healthy')
        self.assertEqual(state['events'], events)
        validate_state(state)

    def test_later_failure_after_unresolved_records_never_applies_partial_parent(self):
        for failure in ('timeout', 'draft', 'wrong-membership'):
            payloads = reconstructed_parent_pages()
            if failure == 'timeout':
                payloads[3] = TimeoutError('Synthetic final-page failure')
            elif failure == 'draft':
                payloads[3]['data']['contents'][0]['is_draft'] = True
            else:
                payloads[3]['data']['contents'][0]['categories'][0]['category_id'] = 'wrong-parent'
            state = empty_state()
            with self.subTest(failure=failure):
                status = collect_source(state, PARENT_SOURCE, NOW, ApiTransport(payloads))
                self.assertEqual(status['status'], 'failed')
                self.assertEqual(state['items'], {})
                self.assertEqual(state['events'], [])
                self.assertEqual(status['observations'], {})
                self.assertNotIn('tcct_migration_version', status)


if __name__ == '__main__':
    unittest.main()
