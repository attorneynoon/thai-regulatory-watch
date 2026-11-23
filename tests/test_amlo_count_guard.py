"""Offline recovery-count regressions; all content responses are synthetic."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

from regwatch.collector import collect_source
from regwatch.engine import empty_state
from regwatch.registry import load_registry


ROOT = Path(__file__).resolve().parents[1]
BEFORE = '2026-10-20T00:24:04Z'
AFTER = '2026-11-14T11:32:44Z'


class OfflineTransport:
    def __init__(self, bodies):
        self.bodies = iter(bodies)

    def fetch(self, url, **kwargs):
        return 200, {}, next(self.bodies), url


class AmloCountGuardTests(unittest.TestCase):
    def setUp(self):
        self.source = next(s for s in load_registry(ROOT / 'config/sources.yml')
                           if s['id'] == 'amlo-listing-01')
        self.entry = (ROOT / 'tests/fixtures/repairs/enforcement-amlo-entry.html').read_bytes()
        network = patch('requests.Session.request', side_effect=AssertionError('Offline test attempted network'))
        network.start()
        self.addCleanup(network.stop)

    def collect(self, state, source, count, now):
        body = ''.join(
            '<div class="title-hilight2f"><a href="https://www.amlo.go.th/index.php/news/detail/'
            + str(90000 + i) + '">Synthetic article ' + str(i) + '</a></div>'
            for i in range(count)).encode()
        return collect_source(state, source, now, OfflineTransport([self.entry, body]))

    def seeded(self, source, count=6):
        state = empty_state()
        result = self.collect(state, source, count, BEFORE)
        self.assertEqual(result['status'], 'healthy')
        self.assertEqual(result['last_count'], count)
        return state

    def test_small_inventory_drop_preserves_content_and_successful_count(self):
        source = {**self.source, 'count_drop_min_previous': 1}
        for count in (1, 2):
            with self.subTest(count=count):
                state = self.seeded(source)
                before = deepcopy(state)
                result = self.collect(state, source, count, AFTER)
                self.assertEqual(result['status'], 'failed')
                self.assertIn('count drop', result['last_error'])
                self.assertEqual(result['last_count'], 6)
                self.assertEqual(result['last_success_at'], BEFORE)
                self.assertEqual(result['last_attempt_at'], AFTER)
                self.assertEqual(result['baseline_complete'], before['sources'][source['id']]['baseline_complete'])
                self.assertEqual(result['observations'], before['sources'][source['id']]['observations'])
                self.assertEqual(state['items'], before['items'])
                self.assertEqual(state['events'], before['events'])

    def test_exactly_half_is_accepted_without_discarding_omitted_history(self):
        source = {**self.source, 'count_drop_min_previous': 1}
        state = self.seeded(source)
        before = deepcopy(state['events'])
        result = self.collect(state, source, 3, AFTER)
        self.assertEqual(result['status'], 'healthy')
        self.assertEqual(result['last_count'], 3)
        self.assertEqual(result['last_success_at'], AFTER)
        self.assertEqual(len(result['observations']), 6)
        self.assertEqual(len(state['items']), 6)
        self.assertEqual(state['events'], before)

    def test_fresh_source_uses_min_items_without_a_previous_count(self):
        source = {**self.source, 'count_drop_min_previous': 1}
        for minimum, status in ((1, 'healthy'), (2, 'failed')):
            with self.subTest(min_items=minimum):
                state = empty_state()
                result = self.collect(state, {**source, 'min_items': minimum}, 1, AFTER)
                self.assertEqual(result['status'], status)
                self.assertEqual(result['last_count'], 1 if status == 'healthy' else 0)
                self.assertEqual([e['event_type'] for e in state['events']],
                                 ['BASELINE'] if status == 'healthy' else [])

    def test_absent_setting_preserves_existing_ten_item_threshold(self):
        source = deepcopy(self.source)
        source.pop('count_drop_min_previous', None)
        for previous, status in ((6, 'healthy'), (10, 'failed')):
            with self.subTest(previous_count=previous):
                state = self.seeded(source, previous)
                result = self.collect(state, source, 1, AFTER)
                self.assertEqual(result['status'], status)
                self.assertEqual(result['last_count'], 1 if status == 'healthy' else previous)

    def test_registry_and_replayed_repair_both_protect_amlo_small_inventory(self):
        repairs = yaml.safe_load((ROOT / 'config/repairs/enforcement.yml').read_text())['sources']
        repair = next(s for s in repairs if s['id'] == 'amlo-listing-01')
        replayed = deepcopy(self.source)
        replayed.pop('count_drop_min_previous', None)
        replayed.update(repair)
        for label, source in (('registry', self.source), ('replayed repair', replayed)):
            with self.subTest(configuration=label):
                state = self.seeded(source)
                result = self.collect(state, source, 1, AFTER)
                self.assertEqual(result['status'], 'failed')
                self.assertEqual(result['last_count'], 6)

    def test_registry_rejects_invalid_count_guard_bounds(self):
        # Use a disabled source so this isolated registry needs no fixture files.
        source = {**self.source, 'enabled': False}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'sources.yml'
            for value in (0, -1, 1001, True, False, 1.5, '1', None):
                with self.subTest(value=value):
                    path.write_text(yaml.safe_dump({'schema_version': '1.0', 'sources': [
                        {**source, 'count_drop_min_previous': value}]}))
                    with self.assertRaisesRegex(ValueError, 'Invalid bound: count_drop_min_previous'):
                        load_registry(path)
            for value in (1, 1000):
                with self.subTest(valid=value):
                    path.write_text(yaml.safe_dump({'schema_version': '1.0', 'sources': [
                        {**source, 'count_drop_min_previous': value}]}))
                    self.assertEqual(len(load_registry(path)), 1)
