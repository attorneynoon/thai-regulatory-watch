import unittest
from regwatch.adapters import parse_document
from regwatch.models import canonical_url, parse_date

class ParsingTests(unittest.TestCase):
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
