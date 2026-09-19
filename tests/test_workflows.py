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
        for job in jobs.values():
            for step in job.get('steps',[]):
                if 'uses' in step:
                    self.assertRegex(step['uses'],r'@[a-f0-9]{40}$')
