import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import yaml

from regwatch.cli import main
from regwatch.engine import apply_observations, empty_state, set_health


ROOT = Path(__file__).resolve().parents[1]
NOW = '2026-11-13T15:32:26Z'
LAST_SUCCESS = '2026-11-01T00:00:00Z'


class CliHealthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sources = yaml.safe_load((ROOT / 'config/sources.yml').read_text(encoding='utf-8'))['sources']
        cls.source = next(s for s in sources if s['id'] == 'amlo-listing-01')

    def setUp(self):
        guard = patch('requests.sessions.Session.request', side_effect=AssertionError('Offline test attempted HTTP'))
        guard.start()
        self.addCleanup(guard.stop)

    def seeded_state(self, sources):
        state = empty_state()
        rows = [{'url': f'https://www.amlo.go.th/index.php/news/detail/{i}',
                 'title': f'Retained public item {i}'} for i in range(1, 7)]
        for source in sources:
            apply_observations(state, source, rows, LAST_SUCCESS)
        return state

    def run_cli(self, command, state, sources, *options):
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(sys, 'argv', ['regwatch', command, '--root', directory, *options]), \
                patch('regwatch.cli.load_registry', return_value=sources), \
                patch('regwatch.cli.load_practices', return_value=[]), \
                patch('regwatch.cli.load_state', return_value=state), \
                patch('regwatch.cli.utcnow', return_value=NOW), redirect_stdout(output):
            code = main()
        return code, output.getvalue()

    def test_collect_failure_labels_six_as_retained_and_still_exits_one(self):
        state = self.seeded_state([self.source])
        entry = (ROOT / 'tests/fixtures/repairs/enforcement-amlo-entry.html').read_bytes()
        body = entry.replace(b'</form>', b'<input name="csrf_token" type="hidden" value="synthetic-cli-token"></form>')
        with patch('regwatch.collector.Transport') as factory:
            factory.return_value.fetch.return_value = (200, {}, body, self.source['url'])
            code, output = self.run_cli('collect', state, [self.source])
        self.assertEqual(code, 1)
        self.assertIn('failed: retained_last_count=6; Public navigation form fields changed', output)
        self.assertNotIn('failed: 6 items', output)
        self.assertNotIn('synthetic-cli-token', output)
        self.assertEqual(state['sources'][self.source['id']]['last_success_at'], LAST_SUCCESS)

    def test_collect_healthy_output_preserves_items_label(self):
        state = empty_state()
        entry = (ROOT / 'tests/fixtures/repairs/enforcement-amlo-entry.html').read_bytes()
        listing = (ROOT / self.source['fixture']).read_bytes()
        with patch('regwatch.collector.Transport') as factory:
            factory.return_value.fetch.side_effect = [
                (200, {}, entry, self.source['url']),
                (200, {}, listing, self.source['url']),
            ]
            code, output = self.run_cli('collect', state, [self.source])
        self.assertEqual(code, 0)
        self.assertIn('healthy: 3 items; \n', output)
        self.assertNotIn('retained_last_count', output)

    def test_collect_degraded_reports_current_count_after_accepting_new_records(self):
        source = dict(self.source, id='cli-degraded-test', public_form=None,
                      link_selector='a[href]', item_selector=None, title_selector=None,
                      include_url=None, asset_budget=1)
        state = self.seeded_state([source])
        before = deepcopy(state)
        listing = b'''<a href="/documents/current.pdf">New public document</a>
            <a href="/index.php/news/detail/7">New article seven</a>
            <a href="/index.php/news/detail/8">New article eight</a>
            <a href="/index.php/news/detail/9">New article nine</a>'''
        with patch('regwatch.collector.Transport') as factory:
            factory.return_value.fetch.side_effect = [
                (200, {}, listing, source['url']),
                TimeoutError('Synthetic attachment timeout'),
            ]
            code, output = self.run_cli('collect', state, [source])
        result = state['sources'][source['id']]
        self.assertEqual(code, 1)
        self.assertEqual(result['status'], 'degraded')
        self.assertEqual(before['sources'][source['id']]['last_count'], 6)
        self.assertEqual(result['last_count'], 4)
        self.assertEqual(len(result['observations']), 10)
        self.assertEqual(len(state['items']), 10)
        self.assertEqual(state['events'][:6], before['events'])
        self.assertEqual([event['event_type'] for event in state['events'][6:]], ['NEW'] * 4)
        self.assertIn('degraded: last_count=4; Attachment checks: Synthetic attachment timeout', output)
        self.assertNotIn('retained_last_count', output)

    def test_health_lists_verified_and_candidate_failures_with_retained_history(self):
        sources = [dict(self.source, validation_status='verified'),
                   dict(self.source, id='amlo-candidate-test', validation_status='candidate')]
        state = self.seeded_state(sources)
        for source in sources:
            set_health(state, source, 'failed', NOW, 'Public navigation form fields changed')
        before = deepcopy(state)
        code, output = self.run_cli('health', state, sources)
        self.assertEqual(code, 1)
        rows = json.loads(output)
        self.assertEqual([row['source'] for row in rows], [source['id'] for source in sources])
        self.assertEqual([row['validation'] for row in rows], ['verified', 'candidate'])
        self.assertEqual(rows[0]['diagnostic'], {'code':'amlo_public_form_fields_changed','stage':'pre_post'})
        self.assertEqual(rows[1]['diagnostic'], {'code':'error_details_redacted'})
        for row in rows:
            self.assertEqual(row['status'], 'failed')
            self.assertNotIn('last_error', row)
            self.assertEqual(row['last_count'], 6)
            self.assertEqual(row['last_attempt_at'], NOW)
            self.assertEqual(row['last_success_at'], LAST_SUCCESS)
        self.assertEqual(state, before)

    def test_health_emits_only_allowlisted_amlo_metadata_and_redacts_poisoned_history(self):
        sources = [self.source, dict(self.source, id='unrelated-candidate')]
        state = self.seeded_state(sources)
        known = ('Public navigation form fields changed '
                 '(stage=pre_post; observed_field_count=2; csrf_token_present=True; '
                 'intro_page_matches=True; response_sha256=' + 'a'*64 + ')')
        poison = 'SYNTHETIC-SECRET-IN-ERROR-AND-TIMESTAMP'
        set_health(state, sources[0], 'failed', NOW, known)
        set_health(state, sources[1], 'blocked', NOW, known + ' ' + poison)
        state['sources'][sources[1]['id']]['last_attempt_at'] = poison
        state['sources'][sources[1]['id']]['last_count'] = poison
        for amlo_details in (known, known + ' ' + poison):
            with self.subTest(valid=amlo_details==known):
                state['sources'][sources[0]['id']]['last_error'] = amlo_details
                before = deepcopy(state)
                code, output = self.run_cli('health', state, sources)
                self.assertEqual(code, 1)
                self.assertNotIn(poison, output)
                self.assertNotIn('a'*64, output)
                self.assertNotIn('last_error', output)
                amlo, candidate = json.loads(output)
                self.assertEqual(amlo['diagnostic'],
                    {'code':'amlo_public_form_fields_changed','stage':'pre_post',
                     'observed_field_count':2,'csrf_token_present':True,'intro_page_matches':True}
                    if amlo_details==known else {'code':'error_details_redacted'})
                self.assertEqual(candidate['diagnostic'], {'code':'error_details_redacted'})
                self.assertEqual(amlo['last_count'], 6)
                self.assertEqual(amlo['last_success_at'], LAST_SUCCESS)
                self.assertIsNone(candidate['last_attempt_at'])
                self.assertIsNone(candidate['last_count'])
                self.assertEqual([amlo['status'],candidate['status']], ['failed','blocked'])
                self.assertEqual(state, before)

    def test_health_stale_threshold_still_uses_last_success_not_latest_attempt(self):
        sources = [dict(self.source, id='amlo-at-threshold'),
                   dict(self.source, id='amlo-over-threshold')]
        state = self.seeded_state(sources)
        state['sources'][sources[0]['id']]['last_success_at'] = '2026-11-13T12:32:26Z'
        state['sources'][sources[1]['id']]['last_success_at'] = '2026-11-13T12:32:25Z'
        for source in sources:
            state['sources'][source['id']]['last_attempt_at'] = NOW
        before = deepcopy(state)
        with patch('regwatch.cli.datetime') as clock:
            clock.now.return_value = datetime(2026, 11, 13, 15, 32, 26, tzinfo=timezone.utc)
            clock.fromisoformat.side_effect = datetime.fromisoformat
            code, output = self.run_cli('health', state, sources)
        self.assertEqual(code, 1)
        rows = json.loads(output)
        self.assertEqual([(row['source'], row['status']) for row in rows], [('amlo-over-threshold', 'stale')])
        self.assertEqual(state, before)

    def test_health_strict_coverage_and_disabled_source_conditions_are_unchanged(self):
        source = dict(self.source, enabled=False, validation_status='candidate')
        state = self.seeded_state([source])
        set_health(state, source, 'failed', NOW, 'Existing failure')
        code, output = self.run_cli('health', state, [source])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output), [])
        code, output = self.run_cli('health', state, [source], '--strict-coverage')
        self.assertEqual(code, 1)
        self.assertEqual([(row['source'], row['status']) for row in json.loads(output)], [(source['id'], 'failed')])
