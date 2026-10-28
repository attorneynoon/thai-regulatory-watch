import os
import subprocess
import tempfile
import unittest
from pathlib import Path
import yaml


class WorkflowTests(unittest.TestCase):
    def test_serialized_hourly_publish_with_separate_health(self):
        root=Path(__file__).resolve().parents[1]
        workflow=yaml.load((root/'.github/workflows/monitor.yml').read_text('utf-8'),Loader=yaml.BaseLoader)
        self.assertEqual(workflow['on']['schedule'][0]['cron'],'17 * * * *')
        self.assertEqual(workflow['concurrency']['cancel-in-progress'],'false')
        self.assertEqual(workflow['permissions'],{'contents':'read'})
        jobs=workflow['jobs']
        self.assertEqual(jobs['deploy']['needs'],'collect')
        self.assertEqual(jobs['health']['needs'],'collect')
        self.assertEqual(jobs['deploy']['permissions'],{'pages':'write','id-token':'write'})
        self.assertNotIn('pull_request',workflow['on'])
        self.assertEqual(workflow['on']['workflow_dispatch']['inputs']['collection_scope']['default'],'all')
        collection=next(s for s in jobs['collect']['steps'] if s.get('name')=='Collect public sources')
        self.assertIn('--source pdpc-official-orders',collection['run'])
        self.assertIn('else\n',collection['run'])
        for job in jobs.values():
            for step in job.get('steps',[]):
                if 'uses' in step:
                    self.assertRegex(step['uses'],r'@[a-f0-9]{40}$')


class PreservedSnapshotTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.workflow = yaml.load(
            (root / '.github/workflows/monitor.yml').read_text('utf-8'),
            Loader=yaml.BaseLoader,
        )
        self.preservation = next(
            step for step in self.workflow['jobs']['collect']['steps']
            if step.get('name') == 'Preserve collected public state and outputs'
        )
        temporary = tempfile.TemporaryDirectory(prefix='regwatch-workflow-')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.remote = self.directory / 'origin.git'
        self.work = self.directory / 'collect'
        self.work.mkdir()
        self.output = self.directory / 'step-output'
        self.env = {
            key: value for key, value in os.environ.items()
            if not key.startswith('GIT_')
        }
        self.env.update({
            'GIT_CONFIG_NOSYSTEM': '1',
            'GIT_CONFIG_GLOBAL': os.devnull,
            'GIT_TERMINAL_PROMPT': '0',
            'GIT_ALLOW_PROTOCOL': 'file',
            'GITHUB_OUTPUT': str(self.output),
        })
        self.git(self.directory, 'init', '--bare', '--initial-branch=main', self.remote)
        self.git(self.work, 'init', '--initial-branch=main')
        self.configure_identity(self.work)
        for directory in ('state', 'site', 'schemas'):
            (self.work / directory).mkdir()
        (self.work / 'state/monitor.json').write_text('{"snapshot": "initial"}\n')
        (self.work / 'site/index.html').write_text('Initial site\n')
        (self.work / 'schemas/monitor.json').write_text('{}\n')
        self.git(self.work, 'add', '.')
        self.git(self.work, 'commit', '-m', 'test: initial collection')
        self.git(self.work, 'remote', 'add', 'origin', self.remote)
        self.git(self.work, 'push', 'origin', 'HEAD:main')
        self.initial_sha = self.git(self.work, 'rev-parse', 'HEAD')

    def git(self, repository, *arguments):
        result = subprocess.run(
            ['git', '-C', str(repository), *(str(arg) for arg in arguments)],
            env=self.env, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout.strip()

    def configure_identity(self, repository):
        self.git(repository, 'config', 'user.name', 'github-actions[bot]')
        self.git(
            repository, 'config', 'user.email',
            '41898282+github-actions[bot]@users.noreply.github.com',
        )

    def run_preservation(self):
        self.output.write_text('')
        return subprocess.run(
            ['bash', '-e', '-c', self.preservation['run']],
            cwd=self.work, env=self.env, capture_output=True, text=True,
        )

    def state_sha(self):
        outputs = dict(line.split('=', 1) for line in self.output.read_text().splitlines())
        self.assertIn('state_sha', outputs, 'Preservation did not emit the collected commit')
        self.assertRegex(outputs['state_sha'], r'^[a-f0-9]{40}$')
        return outputs['state_sha']

    def test_changed_state_emits_the_commit_successfully_pushed(self):
        content = '{"snapshot": "collected"}\n'
        (self.work / 'state/monitor.json').write_text(content)

        result = self.run_preservation()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        sha = self.state_sha()
        self.assertNotEqual(sha, self.initial_sha)
        self.assertEqual(sha, self.git(self.remote, 'rev-parse', 'refs/heads/main'))
        self.assertEqual(sha, self.git(self.work, 'rev-parse', 'HEAD'))
        self.assertEqual(self.git(self.remote, 'show', f'{sha}:state/monitor.json'), content.strip())
        self.git(self.remote, 'merge-base', '--is-ancestor', self.initial_sha, sha)

    def test_no_change_emits_existing_commit_without_committing_or_pushing(self):
        self.git(
            self.work, 'remote', 'set-url', '--push', 'origin',
            self.directory / 'not-a-repository',
        )

        result = self.run_preservation()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.state_sha(), self.initial_sha)
        self.assertEqual(self.git(self.work, 'rev-list', '--count', 'HEAD'), '1')
        self.assertEqual(self.git(self.remote, 'rev-parse', 'refs/heads/main'), self.initial_sha)

    def test_failed_push_emits_no_snapshot(self):
        (self.work / 'state/monitor.json').write_text('{"snapshot": "unpublished"}\n')
        rejection = self.remote / 'hooks/pre-receive'
        rejection.write_text('#!/bin/sh\nexit 1\n')
        rejection.chmod(0o755)

        result = self.run_preservation()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('pre-receive hook declined', result.stderr)
        self.assertEqual(self.output.read_text(), '')
        self.assertEqual(self.git(self.remote, 'rev-parse', 'refs/heads/main'), self.initial_sha)
        self.assertNotEqual(self.git(self.work, 'rev-parse', 'HEAD'), self.initial_sha)

    def test_health_snapshot_stays_fixed_when_remote_main_moves(self):
        content = '{"snapshot": "collected"}\n'
        (self.work / 'state/monitor.json').write_text(content)
        result = self.run_preservation()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        sha = self.state_sha()
        jobs = self.workflow['jobs']
        self.assertEqual(self.preservation.get('id'), 'persist')
        self.assertEqual(
            jobs['collect']['outputs']['state_sha'],
            '${{ steps.persist.outputs.state_sha }}',
        )
        checkout = next(
            step for step in jobs['health']['steps']
            if step.get('uses', '').startswith('actions/checkout@')
        )
        self.assertEqual(checkout['with']['ref'], '${{ needs.collect.outputs.state_sha }}')

        other_writer = self.directory / 'other-writer'
        self.git(self.directory, 'clone', self.remote, other_writer)
        self.configure_identity(other_writer)
        (other_writer / 'state/monitor.json').write_text('{"snapshot": "later"}\n')
        self.git(other_writer, 'commit', '-am', 'test: later collection')
        self.git(other_writer, 'push', 'origin', 'HEAD:main')
        self.assertNotEqual(self.git(self.remote, 'rev-parse', 'refs/heads/main'), sha)

        health = self.directory / 'health'
        health.mkdir()
        self.git(health, 'init')
        self.git(health, 'remote', 'add', 'origin', self.remote)
        self.git(health, 'fetch', '--depth=1', 'origin', sha)
        self.git(health, 'checkout', '--detach', 'FETCH_HEAD')
        self.assertEqual(self.git(health, 'rev-parse', 'HEAD'), sha)
        self.assertEqual((health / 'state/monitor.json').read_text(), content)
