import io
import json
import unittest
from contextlib import redirect_stdout
from copy import deepcopy
from datetime import datetime, timezone
from unittest.mock import patch

from regwatch import cli
from regwatch.engine import empty_state, source_state


NOW = datetime(2026, 10, 17, 1, tzinfo=timezone.utc)
SOURCE = {
    'id': 'example-source', 'enabled': True,
    'validation_status': 'verified', 'url': 'https://example.org/news',
    'max_response_bytes': 4_000_000,
}


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW if tz is not None else NOW.replace(tzinfo=None)


class HealthTests(unittest.TestCase):
    def run_health(self, source=None, status='healthy', success='2026-10-17T00:30:00Z',
                   error=None, strict=False):
        source = deepcopy(source or SOURCE)
        state = empty_state()
        source_state(state, source['id']).update(
            status=status, last_success_at=success,
            last_attempt_at='2026-10-17T00:40:00Z', last_error=error,
        )
        before = deepcopy(state)
        output = io.StringIO()
        argv = ['regwatch', 'health'] + (['--strict-coverage'] if strict else [])
        # Only replace filesystem inputs and the clock; exercise the real CLI gate.
        with patch('sys.argv', argv), patch.object(cli, 'load_registry', return_value=[source]), \
                patch.object(cli, 'load_practices', return_value=[]), \
                patch.object(cli, 'load_state', return_value=state), \
                patch.object(cli, 'datetime', FrozenDateTime), redirect_stdout(output):
            code = cli.main()
        self.assertEqual(state, before, 'Health evaluation must never rewrite retained state')
        return code, json.loads(output.getvalue())

    def test_verified_and_candidate_failures_both_remain_fatal(self):
        for validation in ('verified', 'candidate'):
            for status in ('failed', 'blocked', 'degraded', 'not-run'):
                with self.subTest(validation=validation, status=status):
                    code, problems = self.run_health({**SOURCE, 'validation_status': validation}, status)
                    self.assertEqual(code, 1)
                    self.assertEqual(problems[0]['status'], status)
                    self.assertEqual(problems[0]['validation'], validation)

    def test_healthy_candidate_is_not_promoted_by_success(self):
        candidate = {**SOURCE, 'validation_status': 'candidate'}
        self.assertEqual(self.run_health(candidate), (0, []))
        code, problems = self.run_health(candidate, strict=True)
        self.assertEqual(code, 1)
        self.assertEqual(problems[0]['validation'], 'candidate')
        self.assertEqual(problems[0].get('reasons'), ['unverified_coverage'])

    def test_pending_disabled_scope_requires_strict_coverage(self):
        pending = {**SOURCE, 'enabled': False, 'validation_status': 'pending'}
        self.assertEqual(self.run_health(pending, status='not-run', success=None), (0, []))
        code, problems = self.run_health(pending, status='not-run', success=None, strict=True)
        self.assertEqual(code, 1)
        self.assertEqual(problems[0].get('enabled'), False)
        self.assertEqual(problems[0].get('reasons'), ['unverified_coverage'])

    def test_diagnostics_expose_original_access_error_and_retained_timestamps(self):
        code, problems = self.run_health(
            {**SOURCE, 'validation_status': 'candidate'}, status='blocked',
            success='2026-09-19T08:22:41Z', error='Access unavailable: HTTP 403',
        )
        self.assertEqual(code, 1)
        problem = problems[0]
        self.assertEqual(problem.get('stored_status'), 'blocked')
        self.assertEqual(problem.get('last_error'), 'Access unavailable: HTTP 403')
        self.assertEqual(problem.get('last_success_at'), '2026-09-19T08:22:41Z')
        self.assertEqual(problem.get('last_attempt_at'), '2026-10-17T00:40:00Z')
        self.assertEqual(problem.get('max_response_bytes'), 4_000_000)
        self.assertEqual(problem.get('url'), 'https://example.org/news')

    def test_three_hour_boundary_and_stored_status_are_separate(self):
        self.assertEqual(self.run_health(success='2026-10-16T22:00:00Z'), (0, []))
        code, problems = self.run_health(success='2026-10-16T21:59:59Z')
        self.assertEqual(code, 1)
        self.assertEqual(problems[0]['status'], 'stale')
        self.assertEqual(problems[0].get('stored_status'), 'healthy')
        self.assertEqual(problems[0].get('reasons'), ['stale_success'])

    def test_missing_success_timestamp_never_passes_as_healthy(self):
        for success in (None, ''):
            with self.subTest(success=success):
                code, problems = self.run_health(success=success)
                self.assertEqual(code, 1)
                self.assertEqual(problems[0]['status'], 'invalid')
                self.assertEqual(problems[0].get('reasons'), ['missing_success_timestamp'])

    def test_malformed_or_naive_success_is_reported_without_a_traceback(self):
        for success in ('not-a-time', '2026-10-17T00:30:00', 1234, '2026-10-17'):
            with self.subTest(success=success):
                try:
                    code, problems = self.run_health(success=success)
                except (ValueError, TypeError, AttributeError) as exc:
                    self.fail('Health must report invalid success timestamps: ' + str(exc))
                self.assertEqual(code, 1)
                self.assertEqual(problems[0].get('reasons'), ['invalid_success_timestamp'])

    def test_future_success_never_extends_freshness(self):
        code, problems = self.run_health(success='2026-10-17T01:00:01Z')
        self.assertEqual(code, 1)
        self.assertEqual(problems[0].get('reasons'), ['future_success_timestamp'])
        self.assertEqual(self.run_health(success='2026-10-17T07:30:00+07:00'), (0, []))


if __name__ == '__main__':
    unittest.main()
