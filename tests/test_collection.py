import unittest
from regwatch.adapters import parse_document
from regwatch.models import canonical_url, parse_date

class ParsingTests(unittest.TestCase):
    def test_source_excerpt_and_document_number_are_extracted_not_invented(self):
        source={'mode':'html','allowed_hosts':['example.org'],'item_selector':'article','summary_selector':'.excerpt','document_id_pattern':r'ฉบับที่\s+(\d+/\d+)'}
        rows,_=parse_document(source,'<article><a href="/a">[ฉบับที่ 20/2569] ประกาศ</a><p class="excerpt">ข้อความจากเว็บไซต์</p></article>'.encode(),'https://example.org/')
        self.assertEqual(rows[0]['document_id'],'20/2569')
        self.assertEqual(rows[0]['summary'],'ข้อความจากเว็บไซต์')
        self.assertIsNone(rows[0]['published_at'])

    def test_rss_summary_is_bounded_plain_source_text(self):
        body=b'<rss><channel><item><title>A</title><link>https://example.org/a</link><description><![CDATA[<p>Public excerpt &amp; evidence</p><script>bad()</script>]]></description></item></channel></rss>'
        rows,_=parse_document({'mode':'rss','allowed_hosts':['example.org']},body,'https://example.org/rss')
        self.assertEqual(rows[0]['summary'],'Public excerpt & evidence')

    def test_full_title_attribute_on_selected_title_node_ignores_counter(self):
        source={'mode':'html','allowed_hosts':['example.org'],'item_selector':'a','title_selector':'span[title]','title_attribute':'title'}
        rows,_=parse_document(source,b'<a href="/item"><span title="Complete official headline">Complete...</span><b>Views 99</b></a>','https://example.org/')
        self.assertEqual(rows[0]['title'],'Complete official headline')

    def test_json_html_fragment_discards_date_counter(self):
        import json
        source={'mode':'json-html','json_html_field':'html','allowed_hosts':['example.org'],
                'item_selector':'article','date_selector':'.date','date_pattern':r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2})'}
        payload={'html':'<article><a href="/item">A</a><span class="date">2026-09-18 15:40 | 5</span></article>'}
        rows,_=parse_document(source,json.dumps(payload).encode(),'https://example.org/api')
        self.assertEqual(rows[0]['published_at'],'2026-09-18')
        self.assertEqual(rows[0]['publication_date_raw'],'2026-09-18 15:40')

    def test_page_empty_title_uses_configured_publisher(self):
        rows,_=parse_document({'mode':'page','allowed_hosts':['example.org'],'content_selector':'main','title':'Official enforcement'},b'<title> </title><main>Enforcement report</main>','https://example.org/')
        self.assertEqual(rows[0]['title'],'Official enforcement')

    def test_explicit_localized_dates(self):
        self.assertEqual(parse_date('ก.ค. 6, 2026'),'2026-07-06')
        self.assertEqual(parse_date('18 ก.ย. 2026 16:33'),'2026-09-18')

    def test_attribute_title_and_ajax_base_url(self):
        source={'mode':'html','allowed_hosts':['example.org'],'title_attribute':'title','item_base_url':'https://example.org/list/'}
        rows,_=parse_document(source,b'<a title="Complete official title" href="detail?id=1">Complete...</a>','https://example.org/list/ajax/part')
        self.assertEqual(rows[0]['title'],'Complete official title')
        self.assertEqual(rows[0]['url'],'https://example.org/list/detail?id=1')

    def test_html_visible_title_date_and_filters(self):
        source = dict(mode="html", url="https://example.org/news", link_selector="article a", date_selector="time", item_selector="article", include_url=r"/docs/", allowed_hosts=["example.org"])
        html = '<article><time>๑๙ กันยายน ๒๕๖๙</time><a href="/docs/1.pdf" title="Download">คำวินิจฉัย 1</a></article>'
        rows, pages = parse_document(source, html.encode(), source["url"])
        self.assertEqual(rows[0]["title"], "คำวินิจฉัย 1")
        self.assertEqual(rows[0]["published_at"], "2026-09-19")
        self.assertEqual(rows[0]["document_url"], "https://example.org/docs/1.pdf")
        self.assertEqual(pages, [])

    def test_date_and_url_uncertainty(self):
        self.assertIsNone(parse_date("No date"))
        self.assertIsNone(parse_date("31/02/2569"))
        self.assertEqual(canonical_url("https://example.org/item?id=1&utm_source=x#top"), "https://example.org/item?id=1")
        with self.assertRaises(ValueError):
            canonical_url("https://user:pass@example.org/")

    def test_rss_publication_timestamp(self):
        self.assertEqual(parse_date('Sat, 19 Sep 2026 01:00:00 GMT'),'2026-09-19T01:00:00+00:00')

    def test_reject_external_entities(self):
        xml = b'<!DOCTYPE rss [<!ENTITY x SYSTEM "file:///etc/passwd">]><rss><channel><item><title>&x;</title></item></channel></rss>'
        with self.assertRaises(Exception):
            parse_document(dict(mode="rss", allowed_hosts=["example.org"]), xml, "https://example.org/feed")
