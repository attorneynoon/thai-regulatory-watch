"""Read-only qualification must never use retained state to mask a failed fetch."""
import importlib.util
import json
from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("tcct_live_qualification", ROOT / "scripts" / "qualify_tcct_live.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def source(key, sid="tcct-test"):
    return {"id": sid, "regulator_id": "tcct", "mode": "tcct-api",
            "tcct_category_key": key, "asset_budget": 3}


def successful_collector(state, selected, now, **kwargs):
    assert state["items"] == {}
    assert state["events"] == []
    return {"status": "healthy", "last_count": 2, "listing_pages_checked": 1,
            "pagination_truncated": False,
            "observations": {"first": {}, "second": {}}, "last_error": None}


class LiveQualificationTests(unittest.TestCase):
    def test_unresolved_receipt_retains_relation_state_and_only_public_ids(self):
        observations = {}
        for state in ("omitted", "null", "resolved"):
            observations[state] = {"source_metadata": {
                "id": "public-" + state, "category_id": "parent", "sub_category_id": "child",
                "sub_category_relation_state": state,
                "warnings": ["source_subcategory_unresolved"],
                "body_text": "PRIVATE_BODY", "owner": "PRIVATE_OWNER",
                "categories": [{"category_id": "parent", "sub_category_id": "child",
                                "sub_category": None, "owner": "PRIVATE_MEMBERSHIP"}],
            }}
        before = deepcopy(observations)
        receipt = MODULE.unresolved_subcategory_receipt(observations)
        self.assertEqual({row["sub_category_relation_state"] for row in receipt},
                         {"omitted", "null", "resolved"})
        self.assertTrue(all(row["sub_category_id"] == "child" for row in receipt))
        self.assertTrue(all(row["memberships"][0]["sub_category_relation_state"] == "null" for row in receipt))
        self.assertNotIn("PRIVATE_", json.dumps(receipt))
        self.assertEqual(observations, before)

    def test_missing_or_unknown_scope_fails_before_network(self):
        calls = []
        for sources, keys in [([], ["verdict"]), ([source("verdict")], ["unverified-key"])]:
            with self.subTest(keys=keys):
                with self.assertRaises(ValueError):
                    MODULE.qualify_sources(sources, keys, collector=lambda *a, **k: calls.append(a))
        self.assertEqual(calls, [])

    def test_duplicate_registry_scopes_are_qualified_once(self):
        calls = []
        def collect(state, selected, now, **kwargs):
            calls.append(selected["id"])
            return successful_collector(state, selected, now, **kwargs)
        result = MODULE.qualify_sources(
            [source("verdict", "tcct-first"), source("verdict", "tcct-second")],
            ["verdict", "verdict"], collector=collect)
        self.assertTrue(result["complete"])
        self.assertEqual(calls, ["tcct-first"])
        self.assertEqual(result["scopes"][0]["configured_source_ids"], ["tcct-first", "tcct-second"])

    def test_attachment_budget_is_zero_without_mutating_registry(self):
        selected = source("verdict")
        warnings = {"source_subcategory_unresolved": 1}
        def collect(state, candidate, now, **kwargs):
            self.assertEqual(candidate["asset_budget"], 0)
            self.assertEqual(kwargs["root"], ROOT)
            return {**successful_collector(state, candidate, now, **kwargs),
                    "tcct_listing_warnings": warnings}
        result = MODULE.qualify_sources([selected], ["verdict"], collector=collect, root=ROOT)
        self.assertTrue(result["complete"])
        self.assertEqual(selected["asset_budget"], 3)
        self.assertFalse(result["pdf_bytes_qualified"])
        self.assertEqual(result["scopes"][0]["listing_warnings"], warnings)
        result["scopes"][0]["listing_warnings"]["source_subcategory_unresolved"] = 9
        self.assertEqual(warnings["source_subcategory_unresolved"], 1)

    def test_blocked_scope_is_not_a_successful_inventory(self):
        def blocked(*args, **kwargs):
            return {"status": "blocked", "last_count": 0, "observations": {},
                    "last_error": "Access unavailable: HTTP 403"}
        result = MODULE.qualify_sources([source("verdict")], ["verdict"], collector=blocked)
        self.assertFalse(result["complete"])
        self.assertEqual(result["scopes"][0]["status"], "blocked")
        self.assertIn("403", result["scopes"][0]["error"])

    def test_healthy_with_collapsed_items_or_truncated_pages_is_not_complete(self):
        for change in [{"last_count": 3}, {"pagination_truncated": True}, {"listing_pages_checked": 0}]:
            def incomplete(state, selected, now, **kwargs):
                return {**successful_collector(state, selected, now, **kwargs), **change}
            with self.subTest(change=change):
                result = MODULE.qualify_sources([source("verdict")], ["verdict"], collector=incomplete)
                self.assertFalse(result["complete"])

    def test_each_scope_starts_with_empty_ephemeral_state(self):
        calls = []
        def collect(state, selected, now, **kwargs):
            self.assertEqual(state["items"], {})
            calls.append(selected["tcct_category_key"])
            state["items"]["temporary"] = {}
            return {"status": "healthy", "last_count": 1, "listing_pages_checked": 1,
                    "observations": {"temporary": {}}, "pagination_truncated": False}
        result = MODULE.qualify_sources(
            [source("verdict"), source("verdict-mergers", "tcct-mergers")],
            ["verdict", "verdict-mergers"], collector=collect)
        self.assertTrue(result["complete"])
        self.assertEqual(calls, ["verdict", "verdict-mergers"])


def parent_pages(total=25):
    from test_tcct_collection import api_pages
    payloads = api_pages(total, key='activity-news-2569')
    for page in payloads.values():
        page['data']['category'] = deepcopy(page['data']['contents'][0]['category'])
    return payloads


def parent_source(**changes):
    from test_tcct_collection import SOURCE
    return {**SOURCE, 'id': 'tcct-activities-diagnostic',
            'url': 'https://www.tcct.or.th/category/activity-news',
            'tcct_category_key': 'activity-news', **changes}


class TaxonomyDiagnosticTests(unittest.TestCase):
    def test_projection_distinguishes_omitted_relations_from_explicit_null(self):
        payloads = parent_pages(1)
        row = payloads[1]['data']['contents'][0]
        row['sub_category'] = None
        row['categories'][0]['sub_category'] = None
        explicit = MODULE.taxonomy_projection(payloads[1], 'activity-news', 1)['records'][0]
        self.assertTrue(explicit['relation_field_presence']['sub_category'])
        self.assertTrue(explicit['categories'][0]['relation_field_presence']['sub_category'])
        row.pop('sub_category')
        row['categories'][0].pop('sub_category')
        omitted = MODULE.taxonomy_projection(payloads[1], 'activity-news', 1)['records'][0]
        self.assertFalse(omitted['relation_field_presence']['sub_category'])
        self.assertFalse(omitted['categories'][0]['relation_field_presence']['sub_category'])
        self.assertEqual(omitted['sub_category_id'], explicit['sub_category_id'])
        self.assertIsNone(omitted['sub_category'])

    def factory(self, source):
        self.assertTrue(hasattr(MODULE, 'DiagnosticTransport'), 'Taxonomy diagnostics are not implemented')
        return MODULE.DiagnosticTransport(source)

    def response(self, payloads, calls):
        def fetch(transport, url, **kwargs):
            from regwatch.tcct_api import ENDPOINT
            self.assertEqual(url, ENDPOINT)
            number = kwargs['json_body']['page_number']
            calls.append(number)
            value = payloads[number]
            if isinstance(value, Exception):
                raise value
            return 201, {'Content-Type': 'application/json'}, json.dumps(value).encode(), url
        return fetch

    def test_failed_scope_continues_remaining_pages_only_for_sanitized_diagnostics(self):
        from regwatch.transport import Transport
        payloads, calls = parent_pages(), []
        for page in payloads.values():
            for row in page['data']['contents']:
                row.update(owner={'email': 'PRIVATE_OWNER_SENTINEL'}, content='PRIVATE_BODY_SENTINEL',
                           description='PRIVATE_DESCRIPTION_SENTINEL', view_count=42424242)
                row['category']['owner'] = {'name': 'PRIVATE_TAXONOMY_OWNER'}
                row['categories'][0]['owner'] = 'PRIVATE_MEMBERSHIP_OWNER'
        for number in (2, 3):
            payloads[number]['data']['contents'][0]['categories'][0]['sub_category']['parent_id'] = 'other-parent'
        with patch.object(Transport, 'fetch', self.response(payloads, calls)), \
                patch('pathlib.Path.write_text', side_effect=AssertionError('No state or evidence writes')), \
                patch('pathlib.Path.write_bytes', side_effect=AssertionError('No binary writes')), \
                patch('regwatch.storage.load_state', side_effect=AssertionError('No production state reads')):
            result = MODULE.qualify_sources([parent_source()], ['activity-news'],
                diagnose_taxonomy=True, transport_factory=self.factory)
        scope = result['scopes'][0]
        self.assertFalse(result['complete'])
        self.assertFalse(scope['complete'])
        self.assertEqual(scope['status'], 'failed')
        self.assertEqual(scope['records'], 0)
        self.assertEqual(scope['distinct_observations'], 0)
        self.assertEqual(calls, [1, 2, 3])
        diagnostic = scope['taxonomy_diagnostic']
        self.assertFalse(diagnostic['qualifies_scope'])
        self.assertEqual(diagnostic['failed_request']['page_number'], 2)
        self.assertEqual(diagnostic['pages_inspected'], [1, 2, 3])
        self.assertEqual([row['page'] for row in diagnostic['anomalies']], [2, 3])
        first = diagnostic['anomalies'][0]['record']
        self.assertIn('id', first)
        self.assertIn('title', first)
        self.assertIn('code', first)
        self.assertEqual(first['categories'][0]['sub_category']['parent_id'], 'other-parent')
        encoded = json.dumps(result)
        for forbidden in ('PRIVATE_', '42424242', 'file_list', 'view_count', '"owner"', '"body"', '"content"'):
            self.assertNotIn(forbidden, encoded)
        self.assertEqual(result['production_state_writes'], 0)

    def test_diagnostics_off_stops_at_the_collector_failure(self):
        from regwatch.transport import Transport
        payloads, calls = parent_pages(), []
        payloads[2]['data']['contents'][0]['categories'][0]['sub_category']['parent_id'] = 'wrong-parent'
        with patch.object(Transport, 'fetch', self.response(payloads, calls)):
            result = MODULE.qualify_sources([parent_source()], ['activity-news'], transport_factory=self.factory)
        self.assertEqual(calls, [1, 2])
        self.assertFalse(result['complete'])
        self.assertNotIn('taxonomy_diagnostic', result['scopes'][0])

    def test_diagnostics_stop_on_access_block_without_retry_or_false_health(self):
        from regwatch.transport import Transport, AccessBlocked
        payloads, calls = parent_pages(37), []
        payloads[2]['data']['contents'][0]['categories'][0]['sub_category']['parent_id'] = 'wrong-parent'
        payloads[3] = AccessBlocked('Access unavailable: HTTP 403')
        with patch.object(Transport, 'fetch', self.response(payloads, calls)):
            result = MODULE.qualify_sources([parent_source()], ['activity-news'],
                diagnose_taxonomy=True, transport_factory=self.factory)
        self.assertEqual(calls, [1, 2, 3])
        self.assertFalse(result['complete'])
        diagnostic = result['scopes'][0]['taxonomy_diagnostic']
        self.assertEqual(diagnostic['pages_inspected'], [1, 2])
        self.assertIn('403', diagnostic['continuation_error'])

    def test_advertised_bounds_and_metadata_drift_stop_diagnostic_continuation(self):
        from regwatch.transport import Transport
        for changes in ({'max_pages': 2}, {'max_items': 24}):
            payloads, calls = parent_pages(), []
            with self.subTest(changes=changes), patch.object(Transport, 'fetch', self.response(payloads, calls)):
                result = MODULE.qualify_sources([parent_source(**changes)], ['activity-news'],
                    diagnose_taxonomy=True, transport_factory=self.factory)
            self.assertEqual(calls, [1])
            self.assertFalse(result['complete'])
            self.assertIn('bound', result['scopes'][0]['taxonomy_diagnostic']['continuation_error'])
        payloads, calls = parent_pages(), []
        payloads[2]['data']['meta']['total'] = 26
        payloads[2]['data']['contents'][0]['categories'][0]['sub_category']['parent_id'] = 'wrong-parent'
        with patch.object(Transport, 'fetch', self.response(payloads, calls)):
            result = MODULE.qualify_sources([parent_source()], ['activity-news'],
                diagnose_taxonomy=True, transport_factory=self.factory)
        self.assertEqual(calls, [1, 2])
        self.assertFalse(result['complete'])
        self.assertIn('metadata', result['scopes'][0]['taxonomy_diagnostic']['continuation_error'])

    def test_json_projection_does_not_recurse_into_unexpected_field_values(self):
        payloads = parent_pages(1)
        payloads[1]['data']['contents'][0]['title'] = {'nested': 'PRIVATE_NESTED_SENTINEL'}
        payloads[1]['data']['contents'][0]['categories'][0]['sub_category']['parent_id'] = {'private': 'PRIVATE_NESTED_SENTINEL'}
        self.assertTrue(hasattr(MODULE, 'taxonomy_projection'), 'Taxonomy projection is not implemented')
        projected = MODULE.taxonomy_projection(payloads[1], 'activity-news', 1)
        encoded = json.dumps(projected)
        self.assertNotIn('PRIVATE_', encoded)
        self.assertIn('invalid_type', encoded)

    def test_cli_flag_does_not_convert_failed_qualification_to_success(self):
        from contextlib import redirect_stdout
        from io import StringIO
        result = {'complete': False, 'scopes': [{'status': 'failed'}]}
        with patch.object(MODULE, 'load_registry', return_value=[parent_source()]), \
                patch.object(MODULE, 'qualify_sources', return_value=result) as qualify, redirect_stdout(StringIO()):
            code = MODULE.main(['--category', 'activity-news', '--diagnose-taxonomy'])
        self.assertEqual(code, 1)
        self.assertTrue(qualify.call_args.kwargs['diagnose_taxonomy'])


if __name__ == "__main__":
    unittest.main()
