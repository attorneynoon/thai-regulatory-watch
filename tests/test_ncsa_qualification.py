import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import yaml

from regwatch.engine import apply_observations, empty_state
from regwatch.registry import load_registry
from regwatch.transport import AccessBlocked


ROOT = Path(__file__).resolve().parents[1]
URL = 'https://www.ncsa.or.th/data/output/news.json'
SOURCE_IDS = ('ncsa-listing-01', 'ncsa-listing-02', 'ncsa-listing-03')
NOW = '2026-10-17T04:00:00Z'


class FakeNetwork:
    """Replace only the external fetch, leaving the real collector in use."""

    def __init__(self, body=b'', status=200, final_url=URL, error=None):
        self.response = (status, {'Content-Type': 'application/json'}, body, final_url)
        self.error = error
        self.requests = []
        self.session = self

    def close(self):
        pass

    def fetch(self, url, **kwargs):
        self.requests.append((url, kwargs.get('max_bytes')))
        if self.error is not None:
            raise self.error
        return self.response


def file_hashes(root):
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for directory in ('state', 'site', 'schemas')
        for path in (root / directory).rglob('*') if path.is_file()
    }


class NcsaQualificationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='regwatch-ncsa-qualification-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.sources = [s for s in load_registry(ROOT / 'config/sources.yml') if s['id'] in SOURCE_IDS]
        for source in self.sources:
            target = self.root / source['fixture']
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / source['fixture']).read_bytes())
        self.write_registry()
        self.raw = json.loads((ROOT / self.sources[0]['fixture']).read_bytes())
        unpublished = {**self.raw[0], '_id': 'unpublished', '_state': 0,
                       'showdate': '2026-10-17', 'title': 'DO_NOT_PRINT_RAW_PAYLOAD'}
        self.body = json.dumps([unpublished, *self.raw], ensure_ascii=False).encode('utf-8')
        self.state = self.seed_state(2)
        self.write_state(self.state)
        for directory in ('site', 'schemas'):
            (self.root / directory).mkdir()
            (self.root / directory / 'retained.json').write_text('{"unchanged":true}\n')

    def module(self):
        path = ROOT / 'scripts/qualify_ncsa.py'
        self.assertTrue(path.is_file(), 'Read-only NCSA qualification helper is missing')
        spec = importlib.util.spec_from_file_location('qualify_ncsa_test_module', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def write_registry(self):
        path = self.root / 'config/sources.yml'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump({'schema_version': '1.0', 'sources': self.sources}), encoding='utf-8')

    def seed_state(self, count):
        state = empty_state()
        for source in self.sources:
            rows = [
                {'url': URL.replace('/data/output/news.json', '/news/' + self.raw[0]['_id']),
                 'document_id': self.raw[0]['_id'],
                 'title': 'Earlier source-specific title for ' + source['id'],
                 'published_at': '2026-09-14'},
                *({'url': 'https://www.ncsa.or.th/news/retained-' + str(i),
                   'document_id': 'retained-' + str(i),
                   'title': 'Retained publication ' + str(i) + ' from ' + source['id']}
                  for i in range(count - 1)),
            ]
            apply_observations(state, source, rows, '2026-09-19T00:00:00Z')
        return state

    def write_state(self, state):
        path = self.root / 'state/monitor.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, ensure_ascii=False), encoding='utf-8')

    def evaluate(self, network):
        before_files = file_hashes(self.root)
        before_state = json.loads((self.root / 'state/monitor.json').read_text())
        result = self.module().qualify(self.root, transport=network, now=NOW)
        self.assertEqual(file_hashes(self.root), before_files)
        self.assertEqual(json.loads((self.root / 'state/monitor.json').read_text()), before_state)
        self.assertTrue(result['history_preserved'])
        self.assertEqual(result['checked_at'], NOW)
        self.assertEqual([row['source'] for row in result['sources']], list(SOURCE_IDS))
        return result

    def test_valid_export_uses_one_fetch_and_real_category_and_history_rules(self):
        network = FakeNetwork(self.body)
        result = self.evaluate(network)
        self.assertEqual(result['status'], 'healthy')
        self.assertEqual(network.requests, [(URL, max(s['max_response_bytes'] for s in self.sources))])
        self.assertEqual(result['http_status'], 200)
        self.assertEqual(result['bytes'], len(self.body))
        self.assertEqual(result['sha256'], hashlib.sha256(self.body).hexdigest())
        self.assertEqual(result['content_type'], 'application/json')
        self.assertEqual([row['count'] for row in result['sources']], [1, 2, 2])
        self.assertEqual([row['prior_observations'] for row in result['sources']], [2, 2, 2])
        self.assertEqual([row['observations'] for row in result['sources']], [2, 3, 3])
        self.assertTrue(all(row['count_basis'] == 'current-response' for row in result['sources']))
        self.assertNotIn('DO_NOT_PRINT_RAW_PAYLOAD', json.dumps(result))
        self.assertNotIn('Earlier source-specific title', json.dumps(result))

    def test_access_failure_reports_all_sources_without_losing_history(self):
        network = FakeNetwork(error=AccessBlocked('Access unavailable: HTTP 403'))
        result = self.evaluate(network)
        self.assertEqual(len(network.requests), 1)
        self.assertEqual(result['status'], 'blocked')
        self.assertIsNone(result['bytes'])
        self.assertTrue(all(row['status'] == 'blocked' for row in result['sources']))
        self.assertTrue(all('HTTP 403' in row['last_error'] for row in result['sources']))
        self.assertTrue(all(row['count_basis'] == 'retained-state' for row in result['sources']))

    def test_denied_response_cannot_qualify_even_if_body_is_valid_json(self):
        result = self.evaluate(FakeNetwork(self.body, status=403))
        self.assertEqual(result['status'], 'blocked')
        self.assertTrue(all(row['status'] == 'blocked' for row in result['sources']))

    def test_oversized_prefetched_body_is_rejected_at_each_source_limit(self):
        for source in self.sources:
            source['max_response_bytes'] = 1000
        self.write_registry()
        result = self.evaluate(FakeNetwork(self.body + b' ' * 1001))
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(all('Response exceeds byte budget' in row['last_error'] for row in result['sources']))
        self.assertEqual([row['observations'] for row in result['sources']], [2, 2, 2])

    def test_prefetched_body_obeys_each_source_budget_not_just_largest_budget(self):
        self.sources[0]['max_response_bytes'] = 1000
        for source in self.sources[1:]:
            source['max_response_bytes'] = 10000
        self.write_registry()
        network = FakeNetwork(self.body + b' ' * 1001)
        result = self.evaluate(network)
        self.assertEqual(network.requests, [(URL, 10000)])
        self.assertEqual([row['status'] for row in result['sources']], ['failed', 'healthy', 'healthy'])
        self.assertEqual(result['status'], 'failed')

    def test_invalid_json_or_changed_shape_fails_actual_collector(self):
        for body in (b'not JSON', b'{"items": []}', b'[1]'):
            with self.subTest(body=body):
                result = self.evaluate(FakeNetwork(body))
                self.assertEqual(result['status'], 'failed')
                self.assertTrue(all(row['status'] == 'failed' for row in result['sources']))
                self.assertEqual([row['observations'] for row in result['sources']], [2, 2, 2])

    def test_suspicious_count_drop_is_not_mistaken_for_qualification_success(self):
        self.write_state(self.seed_state(10))
        result = self.evaluate(FakeNetwork(self.body))
        self.assertEqual(result['status'], 'failed')
        self.assertEqual([row['count'] for row in result['sources']], [10, 10, 10])
        self.assertTrue(all('count drop greater than 50%' in row['last_error'] for row in result['sources']))
        self.assertEqual([row['observations'] for row in result['sources']], [10, 10, 10])

    def test_unexpected_final_endpoint_cannot_qualify(self):
        result = self.evaluate(FakeNetwork(self.body, final_url='https://www.ncsa.or.th/other.json'))
        self.assertEqual(result['status'], 'blocked')
        self.assertTrue(all(row['status'] == 'blocked' for row in result['sources']))

    def test_replay_rejects_other_urls_forms_and_bytes_over_requested_limit(self):
        replay = self.module().PrefetchedTransport(FakeNetwork(self.body).response)
        self.assertEqual(replay.fetch(URL, max_bytes=len(self.body))[2], self.body)
        with self.assertRaisesRegex(ValueError, 'Response exceeds byte budget'):
            replay.fetch(URL, max_bytes=len(self.body) - 1)
        for other in ('https://www.ncsa.or.th/news/one', 'https://other.example/export.json'):
            with self.subTest(url=other), self.assertRaises(AccessBlocked):
                replay.fetch(other)
        with self.assertRaises(AccessBlocked):
            replay.fetch(URL, form={'field': 'value'})

    def test_cli_reports_compact_json_and_nonzero_failure_without_writes(self):
        module = self.module()
        for body, expected_exit in ((self.body, 0), (b'{"changed":true}', 1)):
            with self.subTest(expected_exit=expected_exit):
                before = file_hashes(self.root)
                output = io.StringIO()
                with patch.object(module, 'Transport', return_value=FakeNetwork(body)), contextlib.redirect_stdout(output):
                    code = module.main(['--root', str(self.root)])
                self.assertEqual(code, expected_exit)
                report = json.loads(output.getvalue())
                self.assertTrue(report['history_preserved'])
                self.assertNotIn('DO_NOT_PRINT_RAW_PAYLOAD', output.getvalue())
                self.assertLess(len(output.getvalue()), 8000)
                self.assertEqual(before, file_hashes(self.root))

    def test_default_root_is_repository_and_protected_repository_files_stay_identical(self):
        module = self.module()
        before = file_hashes(ROOT)
        network = FakeNetwork(error=AccessBlocked('Public access unavailable for test'))
        output = io.StringIO()
        previous_cwd = Path.cwd()
        try:
            os.chdir(self.root)
            with patch.object(module, 'Transport', return_value=network), contextlib.redirect_stdout(output):
                code = module.main([])
        finally:
            os.chdir(previous_cwd)
        report = json.loads(output.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual([row['source'] for row in report['sources']], list(SOURCE_IDS))
        original = json.loads((ROOT / 'state/monitor.json').read_text())
        self.assertEqual([row['prior_observations'] for row in report['sources']],
                         [len(original['sources'][sid]['observations']) for sid in SOURCE_IDS])
        self.assertEqual(before, file_hashes(ROOT))

    def test_missing_state_is_a_failure_and_never_triggers_network(self):
        module = self.module()
        (self.root / 'state/monitor.json').unlink()
        network = FakeNetwork(self.body)
        result = module.qualify(self.root, transport=network, now=NOW)
        self.assertEqual(result['status'], 'failed')
        self.assertFalse(result['history_preserved'])
        self.assertEqual(network.requests, [])
        self.assertFalse((self.root / 'state/monitor.json').exists())


class NcsaQualificationWorkflowTests(unittest.TestCase):
    def test_workflow_qualifies_exact_pr_head_with_read_only_permissions(self):
        path = ROOT / '.github/workflows/ncsa-qualification.yml'
        self.assertTrue(path.is_file(), 'Manual read-only NCSA qualification workflow is missing')
        workflow = yaml.load(path.read_text('utf-8'), Loader=yaml.BaseLoader)
        self.assertEqual(set(workflow['on']), {'workflow_dispatch', 'pull_request'})
        self.assertIn('.github/workflows/ncsa-qualification.yml', workflow['on']['pull_request']['paths'])
        self.assertIn('config/sources.yml', workflow['on']['pull_request']['paths'])
        self.assertEqual(workflow['permissions'], {'contents': 'read'})
        self.assertEqual(len(workflow['jobs']), 1)
        job = next(iter(workflow['jobs'].values()))
        self.assertEqual(job['timeout-minutes'], '5')
        self.assertNotIn('permissions', job)
        steps = job['steps']
        checkout = next(s for s in steps if s.get('uses', '').startswith('actions/checkout@'))
        self.assertEqual(checkout['uses'], 'actions/checkout@11d5960a326750d5838078e36cf38b85af677262')
        self.assertEqual(checkout['with']['persist-credentials'], 'false')
        self.assertEqual(checkout['with']['ref'], '${{ github.event.pull_request.head.sha || github.sha }}')
        setup = next(s for s in steps if s.get('uses', '').startswith('actions/setup-python@'))
        self.assertEqual(setup['uses'], 'actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065')
        self.assertEqual(setup['with']['python-version'], '3.12')
        commands = [s['run'] for s in steps if 'run' in s]
        self.assertEqual(commands[:2], [
            'python -m pip install --upgrade pip==26.2.1',
            'python -m pip install -r requirements.txt',
        ])
        qualification = next(s for s in steps if s.get('id') == 'qualification')
        self.assertEqual(qualification['run'], 'python scripts/qualify_ncsa.py')
        self.assertNotIn('continue-on-error', qualification)
        verification = next(s for s in steps if s.get('id') == 'verify')
        self.assertEqual(verification['if'], "${{ always() && steps.baseline.outcome == 'success' }}")
        self.assertLess(steps.index(qualification), steps.index(verification))
        self.assertNotIn('continue-on-error', job)

    def test_workflow_file_comparison_detects_changed_added_and_deleted_files(self):
        workflow = yaml.load(
            (ROOT / '.github/workflows/ncsa-qualification.yml').read_text('utf-8'),
            Loader=yaml.BaseLoader,
        )
        steps = workflow['jobs']['qualify']['steps']
        baseline = next((s for s in steps if s.get('id') == 'baseline'), None)
        verification = next((s for s in steps if s.get('id') == 'verify'), None)
        self.assertIsNotNone(baseline, 'Live qualification needs a protected-file baseline')
        self.assertIsNotNone(verification, 'Live qualification needs a file comparison')
        for mutation in ('none', 'changed', 'added', 'deleted', 'registry'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                for name in ('state', 'site', 'schemas', 'config', 'runner-temp'):
                    (root / name).mkdir()
                for name in ('state/monitor.json', 'site/index.html', 'schemas/monitor.json', 'config/sources.yml'):
                    (root / name).write_text('retained\n')
                env = {**os.environ, 'RUNNER_TEMP': str(root / 'runner-temp')}

                def run(step):
                    self.assertEqual(step['shell'], 'bash')
                    return subprocess.run(
                        ['bash', '-e', '-o', 'pipefail', '-c', step['run']],
                        cwd=root, env=env, capture_output=True, text=True,
                    )

                before = run(baseline)
                self.assertEqual(before.returncode, 0, before.stdout + before.stderr)
                if mutation == 'changed':
                    (root / 'state/monitor.json').write_text('changed\n')
                elif mutation == 'added':
                    (root / 'site/new.json').write_text('new\n')
                elif mutation == 'deleted':
                    (root / 'schemas/monitor.json').unlink()
                elif mutation == 'registry':
                    (root / 'config/sources.yml').write_text('changed\n')
                after = run(verification)
                if mutation == 'none':
                    self.assertEqual(after.returncode, 0, after.stdout + after.stderr)
                    self.assertIn('protected_files_unchanged=true', after.stdout)
                else:
                    self.assertNotEqual(after.returncode, 0, after.stdout + after.stderr)


if __name__ == '__main__':
    unittest.main()
