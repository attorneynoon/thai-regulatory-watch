import json
import unittest
from pathlib import Path

import yaml

from regwatch.adapters import parse_document


ROOT = Path(__file__).resolve().parents[1]


class InstitutionQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ids={s['id'] for s in yaml.safe_load((ROOT / 'config/repairs/institutions.yml').read_text(encoding='utf-8'))['sources']}
        cls.sources=[s for s in yaml.safe_load((ROOT / 'config/sources.yml').read_text(encoding='utf-8'))['sources'] if s['id'] in ids]
        cls.evidence = {e['id']: e for e in json.loads((ROOT / 'tests/fixtures/repairs/institution-evidence.json').read_text(encoding='utf-8'))}

    def test_all_assigned_ids_have_explicit_official_destinations(self):
        self.assertEqual(len(self.sources), 25)
        self.assertEqual(len({s['id'] for s in self.sources}), 25)
        for source in self.sources:
            self.assertTrue(source['url'].startswith('https://'))
            self.assertTrue(source['allowed_hosts'])
            self.assertTrue(source['limitations'])

    def test_actual_official_markup_title_url_date_and_count(self):
        for source in self.sources:
            if not source['enabled']:
                continue
            with self.subTest(source=source['id']):
                body = (ROOT / source['fixture']).read_bytes()
                rows, pages = parse_document(source, body, source['url'])
                evidence = self.evidence[source['id']]
                self.assertEqual(len(rows), evidence['fixture_count'])
                for field in ('title', 'url', 'published_at', 'publication_date_raw'):
                    self.assertEqual(rows[0][field], evidence['fixture_example'][field])
                self.assertEqual(pages, [])
                self.assertNotIn(rows[0]['title'], ('อ่านต่อ', 'ดาวน์โหลด', 'รายละเอียด'))

    def test_navigation_and_counter_changes_do_not_create_publications(self):
        for source in self.sources:
            if not source['enabled'] or source['mode'] != 'html':
                continue
            with self.subTest(source=source['id']):
                body = (ROOT / source['fixture']).read_bytes()
                original, _ = parse_document(source, body, source['url'])
                polluted = b'<nav><a href="/2026-menu">Menu</a></nav><footer>12345 visits</footer>' + body
                changed, _ = parse_document(source, polluted, source['url'])
                self.assertEqual(original, changed)

    def test_blocked_or_unqualified_are_not_enabled(self):
        for source in self.sources:
            if not source['enabled']:
                self.assertEqual(source['validation_status'], 'pending')
                self.assertIn('error', self.evidence[source['id']])

    def test_no_date_inferred_from_ccib_url_or_wage_title(self):
        for key in ('ccib-watch', 'wage-committee-watch', 'labour-relations-watch'):
            source = next(s for s in self.sources if s['id'] == key)
            rows, _ = parse_document(source, (ROOT / source['fixture']).read_bytes(), source['url'])
            self.assertTrue(all(row['published_at'] is None for row in rows))

    def test_doe_new_badge_is_not_part_of_publication_title(self):
        source = next(s for s in self.sources if s['id'] == 'doe-watch')
        body = (ROOT / source['fixture']).read_bytes()
        rows, _ = parse_document(source, body, source['url'])
        changed, _ = parse_document(source, body.replace(b'>New<', b'>Old<'), source['url'])
        self.assertEqual(rows, changed)
        self.assertFalse(any(row['title'].endswith('New') for row in rows))
