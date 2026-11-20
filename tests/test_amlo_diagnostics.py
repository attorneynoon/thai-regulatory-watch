import hashlib
import json
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import yaml

from regwatch.collector import collect_source
from regwatch.engine import apply_observations, empty_state


ROOT = Path(__file__).resolve().parents[1]
LAST_SUCCESS = '2026-11-01T00:00:00Z'
ATTEMPT = '2026-11-13T15:32:26Z'
TOKEN = b'synthetic-token-do-not-log'


class EntryTransport:
    """Record the request boundary without sending any HTTP request."""
    def __init__(self, body, final_url=None):
        self.body = body
        self.final_url = final_url
        self.calls = []

    def fetch(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if kwargs.get('form') is not None:
            raise AssertionError('Unexpected POST after invalid form')
        return 200, {'Set-Cookie': 'synthetic-session-do-not-log'}, self.body, self.final_url or url


class AmloDiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sources = yaml.safe_load((ROOT / 'config/sources.yml').read_text(encoding='utf-8'))['sources']
        cls.source = next(s for s in sources if s['id'] == 'amlo-listing-01')
        cls.entry = (ROOT / 'tests/fixtures/repairs/enforcement-amlo-entry.html').read_bytes()
        cls.two_field_entry = cls.entry.replace(
            b'</form>', b'<input type="hidden" name="csrf_token" value="' + TOKEN + b'"></form>')

    def setUp(self):
        guard = patch('requests.sessions.Session.request', side_effect=AssertionError('Offline test attempted HTTP'))
        guard.start()
        self.addCleanup(guard.stop)

    def seeded_state(self):
        state = empty_state()
        rows = [{'url': f'https://www.amlo.go.th/index.php/news/detail/{i}',
                 'title': f'Retained public item {i}'} for i in range(1, 7)]
        apply_observations(state, self.source, rows, LAST_SUCCESS)
        return state

    def assert_one_get(self, transport):
        self.assertEqual(transport.calls, [(self.source['url'], {
            'max_bytes': self.source.get('max_response_bytes', 4_000_000)})])

    def test_two_field_rejection_retains_six_records_before_post(self):
        state = self.seeded_state()
        before = deepcopy(state)
        transport = EntryTransport(self.two_field_entry)
        result = collect_source(state, self.source, ATTEMPT, transport=transport)

        self.assert_one_get(transport)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['last_count'], 6)
        self.assertEqual(len(result['observations']), 6)
        self.assertEqual(result['observations'], before['sources'][self.source['id']]['observations'])
        self.assertEqual(state['items'], before['items'])
        self.assertEqual(state['events'], before['events'])
        self.assertTrue(result['baseline_complete'])
        self.assertEqual(result['last_success_at'], LAST_SUCCESS)
        self.assertEqual(result['last_attempt_at'], ATTEMPT)
        self.assertEqual(state['last_run_at'], ATTEMPT)
        self.assertEqual(state['health_events'][:-1], before['health_events'])
        self.assertEqual(state['health_events'][-1]['status'], 'failed')
        self.assertEqual(state['health_events'][-1]['previous_status'], 'healthy')

        error = result['last_error']
        self.assertTrue(error.startswith('Public navigation form fields changed'))
        for part in ('stage=pre_post', 'observed_field_count=2', 'csrf_token_present=True',
                     'intro_page_matches=True', 'response_sha256=' + hashlib.sha256(self.two_field_entry).hexdigest()):
            self.assertIn(part, error)
        self.assertLessEqual(len(error), 350)
        self.assertEqual(state['health_events'][-1]['message'], error)
        serialized = json.dumps(state)
        for secret in (TOKEN.decode(), 'synthetic-session-do-not-log', '<input', '<form'):
            self.assertNotIn(secret, serialized)

    def test_repeated_rejection_updates_attempt_without_duplicate_health_event(self):
        state = self.seeded_state()
        first = EntryTransport(self.two_field_entry)
        collect_source(state, self.source, ATTEMPT, transport=first)
        after_first = deepcopy(state)
        later = '2026-11-13T16:32:26Z'
        body = self.two_field_entry.replace(TOKEN, b'different-synthetic-token')
        second = EntryTransport(body)
        result = collect_source(state, self.source, later, transport=second)

        self.assert_one_get(first)
        self.assert_one_get(second)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['last_attempt_at'], later)
        self.assertEqual(result['last_success_at'], LAST_SUCCESS)
        self.assertEqual(result['last_count'], 6)
        self.assertEqual(result['observations'], after_first['sources'][self.source['id']]['observations'])
        self.assertEqual(state['items'], after_first['items'])
        self.assertEqual(state['events'], after_first['events'])
        self.assertEqual(state['health_events'], after_first['health_events'])
        self.assertIn('response_sha256=' + hashlib.sha256(body).hexdigest(), result['last_error'])
        self.assertNotEqual(result['last_error'], after_first['sources'][self.source['id']]['last_error'])
        self.assertNotIn('different-synthetic-token', json.dumps(state))

    def test_unknown_control_names_and_values_never_enter_bounded_diagnostics(self):
        unknown_name = b'unknown-control-do-not-log-' + b'x' * 1000
        unknown_value = b'unknown-value-do-not-log-' + b'y' * 1000
        body = self.two_field_entry.replace(
            b'</form>', b'<input type="hidden" name="' + unknown_name + b'" value="' + unknown_value + b'"></form>')
        state = self.seeded_state()
        transport = EntryTransport(body)
        result = collect_source(state, self.source, ATTEMPT, transport=transport)
        self.assert_one_get(transport)
        self.assertEqual(result['status'], 'failed')
        self.assertLessEqual(len(result['last_error']), 350)
        self.assertIn('observed_field_count=3', result['last_error'])
        self.assertIn('response_sha256=' + hashlib.sha256(body).hexdigest(), result['last_error'])
        for secret in (unknown_name[:25].decode(), unknown_value[:24].decode(), TOKEN.decode(), '<input'):
            self.assertNotIn(secret, json.dumps(state))

    def test_missing_or_wrong_intro_is_diagnosed_without_exposing_values(self):
        for old, new, count in (
            (b'<input name="intro_page" type="hidden" value="1" />', b'', 0),
            (b'value="1"', b'value="wrong-intro-value-do-not-log"', 1),
            (b'value="1"', b'', 1),
        ):
            with self.subTest(replacement=new):
                body = self.entry.replace(old, new)
                transport = EntryTransport(body)
                result = collect_source(self.seeded_state(), self.source, ATTEMPT, transport=transport)
                self.assert_one_get(transport)
                self.assertEqual(result['status'], 'failed')
                self.assertIn('observed_field_count=' + str(count), result['last_error'])
                self.assertIn('csrf_token_present=False', result['last_error'])
                self.assertIn('intro_page_matches=False', result['last_error'])
                self.assertNotIn('wrong-intro-value-do-not-log', result['last_error'])

    def test_invalid_controls_forms_and_destinations_still_stop_before_post(self):
        cases = {
            'duplicate intro': self.entry.replace(b'</form>', b'<input name="intro_page" type="hidden" value="1"></form>'),
            'duplicate csrf': self.two_field_entry.replace(b'</form>', b'<input name="csrf_token" type="hidden" value="other"></form>'),
            'visible control': self.entry.replace(b'type="hidden"', b'type="text"'),
            'disabled control': self.entry.replace(b'type="hidden"', b'type="hidden" disabled'),
            'named button': self.entry.replace(b'<button ', b'<button name="submit" '),
            'wrong action': self.entry.replace(self.source['url'].encode(), b'https://www.amlo.go.th/submit'),
            'external action': self.entry.replace(self.source['url'].encode(), b'https://example.org/submit'),
            'wrong method': self.entry.replace(b'method="post"', b'method="get"'),
            'missing form': b'<html></html>',
            'duplicate form': self.entry + self.entry,
        }
        for label, body in cases.items():
            with self.subTest(case=label):
                state = self.seeded_state()
                before = deepcopy(state)
                transport = EntryTransport(body)
                result = collect_source(state, self.source, ATTEMPT, transport=transport)
                self.assert_one_get(transport)
                self.assertEqual(result['status'], 'failed')
                self.assertEqual(result['last_count'], 6)
                self.assertEqual(state['items'], before['items'])
                self.assertEqual(state['events'], before['events'])
        transport = EntryTransport(self.entry, final_url='https://www.amlo.go.th/changed')
        result = collect_source(self.seeded_state(), self.source, ATTEMPT, transport=transport)
        self.assert_one_get(transport)
        self.assertEqual(result['status'], 'failed')
        self.assertIn('page changed destination', result['last_error'])
