import copy
import json
from pathlib import Path
import unittest
import yaml
from regwatch.adapters import parse_document
from regwatch.publicform import validate_public_form

ROOT=Path(__file__).resolve().parents[1]


class EnforcementQualified(unittest.TestCase):
    def test_amlo_sed_explicit_date_excludes_author(self):
        rows=self.parse('amlo-listing-03')
        self.assertEqual(rows[0]['published_at'],'2026-09-04')
        self.assertEqual(rows[0]['publication_date_raw'],'04/09/2569')

    @classmethod
    def setUpClass(cls):
        base={s['id']:s for s in yaml.safe_load((ROOT/'config/sources.yml').read_text(encoding='utf8'))['sources']}
        cls.sources={p['id']:base[p['id']] for p in yaml.safe_load((ROOT/'config/repairs/enforcement.yml').read_text(encoding='utf8'))['sources']}

    def parse(self, source_id, body=None):
        source=self.sources[source_id]
        return parse_document(source,body if body is not None else (ROOT/source['fixture']).read_bytes(),source['url'])[0]

    def test_all_enabled_representative_fixtures(self):
        for sid,s in self.sources.items():
            if not s['enabled']: continue
            with self.subTest(source=sid):
                rows=self.parse(sid)
                self.assertEqual(len(rows),1 if sid=='ncsa-listing-01' else 3 if sid in {'thaibma-listing-01','amlo-listing-01'} else 2)
                self.assertTrue(all(len(r['title'])>15 for r in rows))
                self.assertEqual(len({r['url'] for r in rows}),len(rows))

    def test_thaibma_image_links_use_rule_text_not_row_numbers(self):
        rows=self.parse('thaibma-listing-01')
        row=next(r for r in rows if r['url'].endswith('/078.pdf'))
        self.assertEqual(row['title'],'การกำกับดูแลการรายงานข้อมูลการซื้อขายตราสารหนี้')
        self.assertEqual(row['document_url'],row['url'])
        self.assertIsNone(row['published_at'])

    def test_news_cards_exclude_menus_and_view_count_titles(self):
        for sid in ['ocpb-home','ocpb-listing-01','amlo-listing-03','customs-listing-01']:
            source=self.sources[sid]
            body=(ROOT/source['fixture']).read_bytes()+b'<nav><a href="news_view.php?nid=99">Administrative menu</a></nav>'
            rows=self.parse(sid,body)
            self.assertEqual(len(rows),2)
            self.assertFalse(any('Administrative menu' in r['title'] for r in rows))
            self.assertFalse(any('| 158' in r['title'] or 'Post by' in r['title'] for r in rows))
        self.assertEqual(self.parse('ocpb-home')[0]['publication_date_raw'],'18 ก.ย. 2569')
        self.assertEqual(self.parse('ocpb-home')[0]['published_at'],'2026-09-18')

    def test_ocpb_views_do_not_change_publication_metadata(self):
        for sid in ['ocpb-home','ocpb-listing-01']:
            source=self.sources[sid]
            body=(ROOT/source['fixture']).read_bytes()
            rows=self.parse(sid,body)
            changed=self.parse(sid,body.replace(b'158',b'999999'))
            self.assertEqual(rows,changed)
            self.assertEqual(rows[0]['publication_date_raw'],'18 ก.ย. 2569')
            self.assertEqual(rows[0]['published_at'],'2026-09-18')
            self.assertFalse(any('|' in r['publication_date_raw'] for r in rows))

    def test_public_json_fields_and_thai_dates(self):
        self.assertEqual(self.parse('bot-listing-01')[0]['published_at'],'2026-09-14')
        self.assertEqual(self.parse('fda-listing-01')[0]['url'],'https://oryor.com/media/newsUpdate/media_news/3617')
        self.assertEqual(self.parse('fda-listing-01')[0]['published_at'],'2026-09-18')
        self.assertEqual(self.parse('dbd-listing-01')[0]['url'],'https://www.dbd.go.th/news/14605032569')

    def test_ncsa_category_sort_and_publication_gate(self):
        source=self.sources['ncsa-listing-01']
        raw=json.loads((ROOT/source['fixture']).read_bytes())
        unpublished=copy.deepcopy(raw[0]); unpublished['_state']=0; unpublished['_id']='unpublished'
        body=json.dumps([unpublished,*raw],ensure_ascii=False).encode('utf8')
        announcements=self.parse('ncsa-listing-01',body)
        self.assertEqual(len(announcements),1)
        self.assertIn('Secure Cloud Adoption',announcements[0]['title'])
        self.assertEqual(self.parse('ncsa-listing-02',body)[0]['published_at'],'2026-09-18')
        self.assertEqual(len(self.parse('ncsa-listing-03',body)),2)

    def test_dip_excludes_procurement_without_losing_ip_news(self):
        rows=self.parse('dip-listing-01')
        self.assertEqual(len(rows),2)
        self.assertIn('DIP e-Exchange',rows[0]['title'])

    def test_tcc_slug_feed_not_date_path_assumption(self):
        rows=self.parse('tcc-listing-01')
        self.assertTrue(any(r['url'].endswith('/fta-thai-eu-2/') for r in rows))

    def test_unresolved_access_is_not_enabled(self):
        for sid in ['diw-listing-01','diw-listing-02','diw-listing-03','excise-listing-01','nbtc-listing-01']:
            self.assertFalse(self.sources[sid]['enabled'])
            self.assertEqual(self.sources[sid]['validation_status'],'pending')

    def test_amlo_public_entry_cards_keep_title_not_day_or_excerpt(self):
        rows=self.parse('amlo-listing-01')
        self.assertEqual(len(rows),3)
        self.assertFalse(any(r['title'].startswith(('18 ','16 ')) or r['title'].endswith('...') for r in rows))
        self.assertTrue(all(r['published_at'] is None for r in rows))
        self.assertTrue(any(r['url'].endswith('/20023') for r in rows))

    def test_amlo_public_form_exact_action_and_field_contract(self):
        source=self.sources['amlo-listing-01']
        body=(ROOT/'tests/fixtures/repairs/enforcement-amlo-entry.html').read_bytes()
        self.assertEqual(validate_public_form(source,body,source['url']),{'intro_page':'1'})
        for changed in [
            body.replace(b'action="https://www.amlo.go.th/index.php/th/"',b'action="https://www.amlo.go.th/submit"'),
            body.replace(b'value="1"',b'value="2"'),
            body.replace(b'value="1"',b''),
            body.replace(b'method="post"',b'method="get"'),
            body.replace(b'</form>',b'<input name="token" type="hidden" value="unexpected"></form>'),
            body.replace(b'</form>',b'<input name="intro_page" type="hidden" value="1"></form>'),
        ]:
            with self.assertRaises(ValueError):
                validate_public_form(source,changed,source['url'])
