import copy
import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit

import yaml
from regwatch.adapters import parse_document
from regwatch.collector import collect_source
from regwatch.engine import empty_state

ROOT = Path(__file__).resolve().parents[1]


class FixtureTransport:
    def __init__(self, body):
        self.body = body

    def fetch(self, url, **kwargs):
        return 200, {}, self.body, url


class CourtHostRotationTests(unittest.TestCase):
    def setUp(self):
        self.source = next(s for s in yaml.safe_load((ROOT / 'config/sources.yml').read_text())['sources'] if s['id'] == 'courts-watch')
        self.body = (ROOT / 'tests/fixtures/repairs/courts-20261104.json').read_bytes()

    def test_current_official_cards_have_exact_qualified_hosts_and_dates(self):
        rows, pages = parse_document(self.source, self.body, self.source['url'])
        self.assertEqual(len(rows), 6)
        self.assertEqual({urlsplit(r['url']).hostname for r in rows}, {'lbrmc.coj.go.th', 'cmic.coj.go.th', 'crmc.coj.go.th', 'pttc.coj.go.th', 'crimsb.coj.go.th'})
        self.assertEqual(rows[0]['publication_date_raw'], '2026-11-04 13:54')
        self.assertEqual(rows[0]['published_at'], '2026-11-04')
        self.assertIn('ศาลแขวงลพบุรี', rows[0]['title'])
        self.assertEqual(pages, [])

    def test_unqualified_hosts_still_fail_closed_and_preserve_inventory(self):
        state = empty_state()
        collect_source(state, self.source, '2026-11-04T09:00:00Z', FixtureTransport(self.body))
        self.assertEqual(state['sources']['courts-watch']['status'], 'healthy')
        prior = copy.deepcopy(state['sources']['courts-watch']['observations'])
        events = copy.deepcopy(state['events'])
        payload = json.loads(self.body)
        for host in ('lbrmc', 'cmic', 'crmc', 'pttc', 'crimsb'):
            payload['html'] = payload['html'].replace(host + '.coj.go.th', 'unqualified.coj.go.th')
        collect_source(state, self.source, '2026-11-04T10:00:00Z', FixtureTransport(json.dumps(payload).encode()))
        self.assertEqual(state['sources']['courts-watch']['status'], 'failed')
        self.assertIn('undersized', state['sources']['courts-watch']['last_error'])
        self.assertEqual(state['sources']['courts-watch']['observations'], prior)
        self.assertEqual(state['events'], events)
