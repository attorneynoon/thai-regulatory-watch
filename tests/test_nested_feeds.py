import tempfile
import unittest
from pathlib import Path
from regwatch.engine import empty_state
from regwatch.publish import build_site,check_site
from test_engine import SOURCE

class NestedFeedTests(unittest.TestCase):
    def test_current_feed_xml_is_validated_not_skipped(self):
        with tempfile.TemporaryDirectory() as temp:
            build_site(empty_state(),[SOURCE],Path(temp),'https://example.org/')
            (Path(temp)/'feeds/current/all.xml').write_text('<broken>','utf8')
            with self.assertRaises(Exception):check_site(Path(temp))
