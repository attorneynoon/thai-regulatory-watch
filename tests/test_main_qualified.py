import unittest
from pathlib import Path
import yaml
from regwatch.adapters import parse_document

ROOT=Path(__file__).resolve().parents[1]

class MainQualified(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base={s['id']:s for s in yaml.safe_load((ROOT/'config/sources.yml').read_text('utf8'))['sources']}
        cls.sources={p['id']:base[p['id']] for p in yaml.safe_load((ROOT/'config/repairs/main.yml').read_text('utf8'))['sources']}

    def test_qualified_official_fixtures(self):
        for sid,s in self.sources.items():
            if not s['enabled']:continue
            with self.subTest(source=sid):
                rows,_=parse_document(s,(ROOT/s['fixture']).read_bytes(),s['url'])
                self.assertGreater(len(rows),0)
                self.assertTrue(all(len(r['title'])>10 for r in rows))
                self.assertEqual(len(rows),len({r['url'] for r in rows}))

    def test_legislative_dates_and_scope(self):
        s=self.sources['parliament-einitiative-discovery']
        rows,_=parse_document(s,(ROOT/s['fixture']).read_bytes(),s['url'])
        self.assertTrue(rows[0]['modified_at'].startswith('2026-'))
        self.assertIsNone(rows[0]['published_at'])
        self.assertIn('draftlaw-detail?id=',rows[0]['url'])
        s=self.sources['house-section-77-discovery']
        rows,_=parse_document(s,(ROOT/s['fixture']).read_bytes(),s['url'])
        self.assertIsNone(rows[0]['published_at'])
        self.assertIn('/section77/survey_detail.php?',rows[0]['url'])

    def test_ocs_counter_is_not_title_or_change_signal(self):
        s=self.sources['council-of-state-discovery'];body=(ROOT/s['fixture']).read_bytes()
        a,_=parse_document(s,body,s['url']);b,_=parse_document(s,body.replace(b'55',b'99'),s['url'])
        self.assertEqual(a,b)
        self.assertNotIn('ครั้ง',a[0]['title'])
