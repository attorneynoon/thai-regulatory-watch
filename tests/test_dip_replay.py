"""DIP bounded-window acceptance, using the real collector and state engine."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import yaml
from regwatch.collector import collect_source
from regwatch.engine import empty_state
from scripts import qualify_dip

ROOT = Path(__file__).resolve().parents[1]
NOW = '2026-11-11T06:31:24Z'


def source():
    return next(s for s in yaml.safe_load((ROOT/'config/sources.yml').read_text())['sources'] if s['id']=='dip-listing-01')


def payload(n=10, title='ข่าวทรัพย์สินทางปัญญา'):
    return json.dumps([{'id':i,'link':f'https://webnew.ipthailand.go.th/news/{i}/','title':{'rendered':title},'date':'2026-07-21T00:00:00','modified':'2026-07-21T00:00:00'} for i in range(n)],ensure_ascii=False).encode()


class DIPReplayTests(unittest.TestCase):
    def test_acceptance_replays_history_identity_and_old_new_events(self):
        s=source(); state=empty_state()
        collect_source(state,s,NOW,transport=qualify_dip.ResponseTransport(payload(10),s['url']))
        original=copy.deepcopy(state)
        result=qualify_dip.replay(state,s,payload(12),'2026-11-12T00:00:00Z')
        self.assertTrue(result['accepted']); self.assertTrue(result['history_preserved'])
        self.assertTrue(result['repeat_idempotent']); self.assertEqual(result['new_events'],2)
        self.assertEqual(result['new_with_older_publication_date'],2)
        self.assertEqual(state,original)

    def test_actual_collector_count_drop_boundary_and_retention(self):
        s=source(); state=empty_state()
        collect_source(state,s,NOW,transport=qualify_dip.ResponseTransport(payload(10),s['url']))
        original=copy.deepcopy(state)
        failed=qualify_dip.replay(state,s,payload(4),'2026-11-12T00:00:00Z')
        self.assertFalse(failed['accepted']); self.assertTrue(failed['history_preserved'])
        self.assertEqual(failed['new_events'],0)
        self.assertTrue(qualify_dip.replay(state,s,payload(5),'2026-11-12T00:00:00Z')['accepted'])
        self.assertEqual(state,original)

    def test_duplicate_urls_do_not_inflate_collector_count(self):
        s=source(); rows=json.loads(payload(2)); rows.append(rows[0])
        result=qualify_dip.replay(empty_state(),s,json.dumps(rows).encode(),NOW)
        self.assertEqual(result['last_count'],2)
        self.assertTrue(result['repeat_idempotent'])

    def test_existing_exclusions_and_broad_recruitment_limit(self):
        s=source()
        for word in ['จัดซื้อ','จัดจ้าง','ประกวดราคา','รับสมัคร','สมัครสอบ','ผู้ชนะการเสนอราคา']:
            with self.subTest(word=word):
                result=qualify_dip.replay(empty_state(),s,payload(1,word+' งาน'),NOW)
                self.assertFalse(result['accepted']); self.assertEqual(result['last_count'],0)
        # Characterize, do not silently change, the broad existing exclusion.
        self.assertFalse(qualify_dip.replay(empty_state(),s,payload(1,'เปิดรับสมัครโครงการ IP'),NOW)['accepted'])
        self.assertTrue(qualify_dip.replay(empty_state(),s,payload(1,'แนวปฏิบัติด้านลิขสิทธิ์'),NOW)['accepted'])

    def test_replay_transport_rejects_unplanned_fetch(self):
        s=source(); t=qualify_dip.ResponseTransport(payload(),s['url'])
        with self.assertRaises(ValueError): t.fetch('https://example.org/')

    def test_repeated_observation_mutation_is_rejected(self):
        real = qualify_dip.collect_source
        def corrupt(state, source, now, **kwargs):
            result = real(state, source, now, **kwargs)
            for observation in result['observations'].values():
                observation['revision'] += 1
            return result
        with patch.object(qualify_dip, 'collect_source', side_effect=corrupt):
            result = qualify_dip.replay(empty_state(), source(), payload(2), NOW)
        self.assertFalse(result['repeat_idempotent'])
        self.assertFalse(result['accepted'])

    def test_workflow_covers_config_and_runtime_dependencies(self):
        workflow=yaml.load((ROOT/'.github/workflows/source-contract-qualification.yml').read_text(),Loader=yaml.BaseLoader)
        paths=workflow['on']['pull_request']['paths']
        for p in ['config/sources.yml','regwatch/**','requirements.txt','tests/**','scripts/qualify_dip.py']:
            self.assertIn(p,paths)
        self.assertEqual(workflow['permissions'],{'contents':'read'})
        self.assertIn('python -m scripts.qualify_dip',(ROOT/'.github/workflows/source-contract-qualification.yml').read_text())


class AcceptanceGateTests(unittest.TestCase):
    def result(self):
        return {'protected_files_unchanged':True,'responses':{'20':{'http_status':200},'100':{'http_status':200,'accepted_rows':2,'unique_urls':2,'replay':{'accepted':True}}}}

    def test_requires_both_observed_responses(self):
        value=self.result(); value['responses']['20']={'error':'unavailable'}
        self.assertFalse(qualify_dip.acceptance(value))

    def test_requires_candidate_replay_and_unique_urls(self):
        value=self.result(); value['responses']['100']['unique_urls']=1
        self.assertFalse(qualify_dip.acceptance(value))
        value=self.result(); value['responses']['100']['replay']['accepted']=False
        self.assertFalse(qualify_dip.acceptance(value))

    def test_requires_protected_files_unchanged(self):
        value=self.result(); value['protected_files_unchanged']=False
        self.assertFalse(qualify_dip.acceptance(value))

    def test_accepts_complete_read_only_evidence(self):
        self.assertTrue(qualify_dip.acceptance(self.result()))
