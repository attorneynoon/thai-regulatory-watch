"""Synthetic integration scenarios for the observed TCCT JSON contract."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from uuid import UUID

from regwatch.collector import collect_source
from regwatch.engine import apply_observations, empty_state
from regwatch.models import digest
from regwatch.publish import event_description
from regwatch.storage import validate_state
from test_tcct_api import pages

NOW = '2026-11-12T00:00:00Z'
LATER = '2026-11-13T01:00:00Z'
ENDPOINT = 'https://www.tcct.or.th/api/proxy/contents/now'
SOURCE = {
    'id': 'tcct-unfair', 'regulator_id': 'tcct', 'title': 'TCCT verdicts',
    'topics': ['competition'], 'url': 'https://www.tcct.or.th/category/verdict',
    'allowed_hosts': ['www.tcct.or.th', 'api.tcct.or.th'], 'mode': 'tcct-api',
    'tcct_category_key': 'verdict', 'tcct_migration_version': 'tcct-api-2026-11',
    'max_pages': 50, 'max_items': 1000, 'min_items': 1, 'asset_budget': 0,
    'max_asset_bytes': 40_000_000, 'validation_status': 'candidate',
}


def api_pages(total=13, *, files=False, key='verdict'):
    result = {number: deepcopy(page) for number, page in pages(total, key).items()}
    for page in result.values():
        for raw in page['data']['contents']:
            number = int(raw['id'].split('-')[-1]) + 1
            raw.update(id=str(UUID(int=number)), title='Synthetic publication ' + str(number))
            if not files:
                raw.update(file_list=[], content='<p>Public source body</p>')
    return result


class ApiTransport:
    def __init__(self, payloads, asset=b'%PDF-1.4 synthetic', statuses=None):
        self.payloads, self.asset = payloads, asset
        self.statuses = statuses or {}
        self.calls = []

    def fetch(self, url, **kwargs):
        self.calls.append((url, deepcopy(kwargs)))
        if url == ENDPOINT:
            number = kwargs['json_body']['page_number']
            value = self.payloads[number]
            if isinstance(value, Exception):
                raise value
            return self.statuses.get(number, 201), {'Content-Type': 'application/json'}, json.dumps(value).encode(), url
        if isinstance(self.asset, Exception):
            raise self.asset
        return 200, {'ETag': 'synthetic-v1'}, self.asset, url


class TcctCollectionTests(unittest.TestCase):
    def collect(self, state, payloads, source=None, now=NOW, **transport_kwargs):
        transport = ApiTransport(payloads, **transport_kwargs)
        status = collect_source(state, source or SOURCE, now, transport)
        return status, transport

    def test_page_numbers_and_last_partial_page_keep_distinct_body_only_ids(self):
        state = empty_state()
        status, transport = self.collect(state, api_pages())
        self.assertEqual(status['status'], 'healthy', status.get('last_error'))
        self.assertEqual(len(state['items']), 13)
        self.assertEqual(status['last_count'], 13)
        self.assertEqual(status['listing_pages_checked'], 2)
        self.assertFalse(status['pagination_truncated'])
        self.assertEqual([kw['json_body']['page_number'] for _, kw in transport.calls], [1, 2])
        self.assertEqual(len({row['canonical_url'] for row in state['items'].values()}), 1)
        self.assertEqual(len({row['item_id'] for row in state['items'].values()}), 13)
        event = state['events'][0]
        self.assertEqual(event['tcct_record_id'], str(UUID(int=1)))
        self.assertEqual(event['source_metadata']['link_role'], 'listing')
        self.assertEqual(event['source_metadata']['detail_url'], None)
        self.assertIsNone(event['published_at'])
        self.assertEqual(event['source_metadata']['source_start_date'], '2026-09-17T00:00:00.000Z')
        self.assertEqual(event['review_status'], 'unreviewed')
        self.assertEqual(event['legal_effect'], 'Not assessed')
        self.assertIn('Category listing', event_description(event))
        self.assertNotIn('Original page', event_description(event))
        validate_state(state)

    def test_second_page_failure_does_not_apply_partial_inventory_or_marker(self):
        state = empty_state()
        legacy = {'url': 'https://www.tcct.or.th/old.pdf', 'title': 'Retained legacy record'}
        apply_observations(state, SOURCE, [legacy], NOW)
        before = deepcopy(state)
        payloads = api_pages()
        payloads[2] = TimeoutError('Synthetic page timeout')
        status, _ = self.collect(state, payloads, now=LATER)
        self.assertEqual(status['status'], 'failed')
        self.assertEqual(state['items'], before['items'])
        self.assertEqual(state['events'], before['events'])
        self.assertEqual(status['observations'], before['sources'][SOURCE['id']]['observations'])
        self.assertEqual(status['last_count'], 1)
        self.assertNotIn('tcct_migration_version', status)

    def test_first_complete_migration_baselines_only_unseen_then_new_updates_normally(self):
        state = empty_state()
        legacy = {'url': 'https://www.tcct.or.th/old.pdf', 'title': 'Old publication'}
        apply_observations(state, SOURCE, [legacy], NOW)
        old_item = deepcopy(next(iter(state['items'].values())))
        old_events = deepcopy(state['events'])
        status, _ = self.collect(state, api_pages(2), now=LATER)
        self.assertEqual(status['tcct_migration_version'], SOURCE['tcct_migration_version'])
        self.assertTrue(status['baseline_complete'])
        self.assertEqual(state['events'][:1], old_events)
        self.assertEqual(state['items'][old_item['item_id']], old_item)
        self.assertEqual([e['event_type'] for e in state['events']], ['BASELINE'] * 3)
        payloads = api_pages(3)
        payloads[1]['data']['contents'][0]['title'] = 'Revised synthetic publication'
        self.collect(state, payloads, now='2026-11-14T00:00:00Z')
        self.assertEqual([e['event_type'] for e in state['events'][-2:]], ['UPDATED', 'NEW'])
        self.assertEqual(len(state['items']), 4)
        count = len(state['events'])
        self.collect(state, payloads, now='2026-11-15T00:00:00Z')
        self.assertEqual(len(state['events']), count)

    def test_missing_migration_marker_does_not_rebaseline_existing_uuid_changes(self):
        state = empty_state()
        self.collect(state, api_pages(1))
        state['sources'][SOURCE['id']].pop('tcct_migration_version')
        payloads = api_pages(2)
        payloads[1]['data']['contents'][0]['title'] = 'Changed existing record'
        self.collect(state, payloads, now=LATER)
        self.assertEqual([e['event_type'] for e in state['events'][-2:]], ['UPDATED', 'BASELINE'])

    def test_apply_failure_rolls_back_all_observations_and_migration_marker(self):
        state = empty_state()
        apply_observations(state, SOURCE, [{'url': SOURCE['url'] + '/legacy', 'title': 'Legacy'}], NOW)
        before = deepcopy(state)
        real_apply = apply_observations

        def fail_after_first(staged, source, candidates, now, **kwargs):
            real_apply(staged, source, candidates[:1], now, **kwargs)
            raise ValueError('Synthetic transition failure')

        with patch('regwatch.tcct_collector.apply_observations', side_effect=fail_after_first):
            status, _ = self.collect(state, api_pages(2), now=LATER)
        self.assertEqual(status['status'], 'failed')
        self.assertEqual(state['items'], before['items'])
        self.assertEqual(state['events'], before['events'])
        self.assertEqual(status['observations'], before['sources'][SOURCE['id']]['observations'])
        self.assertNotIn('tcct_migration_version', status)

    def test_duplicates_schema_drift_and_invalid_uuid_fail_the_whole_scope(self):
        mutations = [
            lambda p: p[2]['data']['contents'][0].update(id=p[1]['data']['contents'][0]['id']),
            lambda p: p[2]['data']['contents'][0].update(id='not-a-uuid'),
            lambda p: p[2]['data']['category'].update(name='Metadata drift'),
            lambda p: p[2]['data']['contents'][0].pop('content'),
            lambda p: p[2]['data']['contents'][0].update(is_draft=True),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                payloads = api_pages()
                mutate(payloads)
                state = empty_state()
                status, _ = self.collect(state, payloads)
                self.assertEqual(status['status'], 'failed')
                self.assertEqual(state['items'], {})
                self.assertEqual(state['events'], [])
                self.assertNotIn('tcct_migration_version', status)

    def test_page_and_item_bounds_fail_before_fetching_next_page(self):
        for limit in ({'max_pages': 1}, {'max_items': 12}):
            state = empty_state()
            status, transport = self.collect(state, api_pages(), source={**SOURCE, **limit})
            self.assertEqual(status['status'], 'failed')
            self.assertEqual(len(transport.calls), 1)
            self.assertEqual(state['events'], [])

    def test_large_scope_traverses_more_than_generic_ten_pages(self):
        state = empty_state()
        status, transport = self.collect(state, api_pages(181))
        self.assertEqual(status['status'], 'healthy', status.get('last_error'))
        self.assertEqual(status['last_count'], 181)
        self.assertEqual(len(transport.calls), 16)

    def test_complete_count_drop_retains_last_good_inventory(self):
        state = empty_state()
        self.collect(state, api_pages(13))
        before = deepcopy(state['events'])
        status, _ = self.collect(state, api_pages(2), now=LATER)
        self.assertEqual(status['status'], 'failed')
        self.assertEqual(status['last_count'], 13)
        self.assertEqual(state['events'], before)

    def test_all_downloads_retained_and_extensionless_primary_uses_source_byte_budget(self):
        payloads = api_pages(1, files=True)
        row = payloads[1]['data']['contents'][0]
        row['file_list'].append({**row['file_list'][0], 'id': str(UUID(int=100)),
                                 'fileUrl': 'https://api.tcct.or.th/upload/second'})
        state = empty_state()
        source = {**SOURCE, 'asset_budget': 1}
        status, transport = self.collect(state, payloads, source=source)
        self.assertEqual(status['status'], 'healthy', status.get('last_error'))
        event = state['events'][0]
        self.assertEqual(len(event['source_metadata']['downloads']), 2)
        self.assertFalse(event['source_metadata']['downloads'][0]['isPublic'])
        self.assertEqual(event['attachment_sha256'], digest(b'%PDF-1.4 synthetic'))
        self.assertEqual(transport.calls[-1][1]['max_bytes'], 40_000_000)
        self.assertEqual(event['source_metadata']['link_role'], 'document')

    def test_asset_failure_degrades_complete_listing_and_still_finishes_baseline(self):
        state = empty_state()
        status, _ = self.collect(state, api_pages(1, files=True), source={**SOURCE, 'asset_budget': 1}, asset=ValueError('Synthetic PDF failure'))
        self.assertEqual(status['status'], 'degraded')
        self.assertEqual(status['last_count'], 1)
        self.assertEqual(status['tcct_migration_version'], SOURCE['tcct_migration_version'])
        self.assertEqual(state['events'][0]['event_type'], 'BASELINE')

    def test_changed_primary_url_outside_budget_drops_old_asset_and_is_due_same_day(self):
        state = empty_state()
        payloads = api_pages(1, files=True)
        self.collect(state, payloads, source={**SOURCE, 'asset_budget': 1})
        original_event = deepcopy(state['events'][0])
        replacement = 'https://api.tcct.or.th/upload/replacement'
        payloads[1]['data']['contents'][0]['file_list'][0]['fileUrl'] = replacement
        status, _ = self.collect(state, payloads, now=NOW)
        observation = next(iter(status['observations'].values()))
        self.assertIsNone(observation['attachment_sha256'])
        self.assertEqual(observation['asset'], {})
        self.assertEqual(next(iter(state['items'].values()))['canonical_url'], replacement)
        self.assertEqual(state['events'][0], original_event)
        status, transport = self.collect(state, payloads, source={**SOURCE, 'asset_budget': 1}, now=NOW,
                                         asset=b'%PDF-1.4 replacement')
        self.assertEqual(transport.calls[-1][0], replacement)
        observation = next(iter(status['observations'].values()))
        self.assertEqual(observation['attachment_sha256'], digest(b'%PDF-1.4 replacement'))
        self.assertEqual(observation['asset']['final_url'], replacement)

    def test_counter_changes_do_not_create_event_but_body_changes_do(self):
        state = empty_state()
        payloads = api_pages(1)
        self.collect(state, payloads)
        payloads[1]['data']['contents'][0].update(view_count=9000, owner={'id': 'ignored'})
        self.collect(state, payloads, now=LATER)
        self.assertEqual(len(state['events']), 1)
        payloads[1]['data']['contents'][0]['content'] = '<p>Changed body</p>'
        self.collect(state, payloads, now='2026-11-14T00:00:00Z')
        self.assertEqual(state['events'][-1]['event_type'], 'UPDATED')
        self.assertNotIn('owner', json.dumps(state))

    def test_shared_uuid_merges_memberships_without_conflating_source_observations(self):
        state = empty_state()
        self.collect(state, api_pages(1))
        other = {**SOURCE, 'id': 'tcct-another'}
        self.collect(state, api_pages(1), source=other)
        self.assertEqual(len(state['items']), 1)
        self.assertEqual(next(iter(state['items'].values()))['source_ids'], ['tcct-another', 'tcct-unfair'])
        self.assertEqual(len(state['events']), 2)


class TcctEngineTests(unittest.TestCase):
    def test_non_tcct_identity_and_hash_remain_exactly_legacy_formula(self):
        state = empty_state()
        source = {**SOURCE, 'id': 'ordinary-source', 'regulator_id': 'example', 'mode': 'html'}
        record = {'url': 'https://www.tcct.or.th/ordinary', 'title': 'Ordinary record'}
        apply_observations(state, source, [record], NOW)
        metadata = {k: record.get(k) for k in ('title', 'summary', 'published_at', 'publication_date_raw', 'modified_at', 'selected_text_sha256', 'document_url', 'document_id')}
        event = state['events'][0]
        self.assertEqual(event['item_id'], 'item-' + digest(record['url'])[:32])
        self.assertEqual(event['content_sha256'], digest(metadata))
        self.assertNotIn('source_metadata', event)
        self.assertNotIn('tcct_record_id', event)

    def test_uuid_identity_is_scoped_and_validated_before_any_transition(self):
        for record_id in ('not-a-uuid', True, str(UUID(int=1)).upper() + 'x'):
            with self.subTest(record_id=record_id):
                state = empty_state()
                with self.assertRaises(ValueError):
                    apply_observations(state, SOURCE, [{'url': SOURCE['url'], 'title': 'Bad', 'tcct_record_id': record_id}], NOW)
                self.assertEqual(state['items'], {})
        state = empty_state()
        with self.assertRaises(ValueError):
            apply_observations(state, {**SOURCE, 'regulator_id': 'other'}, [{'url': SOURCE['url'], 'title': 'Bad', 'tcct_record_id': str(UUID(int=1))}], NOW)


if __name__ == '__main__':
    unittest.main()
