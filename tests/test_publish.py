import unittest
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET
from regwatch.engine import empty_state, apply_observations, set_health
from regwatch.publish import build_site, check_site
from test_engine import SOURCE

class PublishTests(unittest.TestCase):
    def test_state_reload_preserves_generated_bytes(self):
        import json
        from regwatch.storage import encode
        s=empty_state()
        apply_observations(s,SOURCE,[dict(url='https://example.org/item/1',title='A')],'2026-09-19T01:00:00Z')
        with tempfile.TemporaryDirectory() as d:
            build_site(s,[SOURCE],Path(d),'https://example.org/watch')
            before={p.relative_to(d):p.read_bytes() for p in Path(d).rglob('*') if p.is_file()}
            build_site(json.loads(encode(s)),[SOURCE],Path(d),'https://example.org/watch')
            after={p.relative_to(d):p.read_bytes() for p in Path(d).rglob('*') if p.is_file()}
            self.assertEqual(before,after)

    def test_window_does_not_remove_json_history(self):
        import json
        s=empty_state()
        apply_observations(s,SOURCE,[dict(url=f'https://example.org/item/{i}',title=f'A {i}') for i in range(3)],'2026-09-19T01:00:00Z')
        with tempfile.TemporaryDirectory() as d:
            build_site(s,[SOURCE],Path(d),'https://example.org/watch',limit=2)
            self.assertEqual(len(ET.parse(Path(d)/'feeds/all.xml').findall('./channel/item')),2)
            self.assertEqual(len(json.loads((Path(d)/'api/v1/events.json').read_text('utf-8'))['records']),3)

    def test_feed_retention_and_machine_identity(self):
        s=empty_state()
        apply_observations(s,SOURCE,[dict(url='https://example.org/item/1',title='A & <B>')],'2026-09-19T01:00:00Z')
        with tempfile.TemporaryDirectory() as d:
            build_site(s,[SOURCE],Path(d),'https://example.org/watch')
            before=(Path(d)/'feeds/all.xml').read_bytes()
            self.assertIn('No post-baseline events recorded', (Path(d)/'index.html').read_text('utf-8'))
            self.assertEqual(len(ET.fromstring(before).findall('./channel/item')),1)
            self.assertEqual(len(ET.parse(Path(d)/'feeds/changes.xml').findall('./channel/item')),0)
            set_health(s,SOURCE,'failed','2026-09-19T02:00:00Z','timeout')
            build_site(s,[SOURCE],Path(d),'https://example.org/watch')
            self.assertEqual(before,(Path(d)/'feeds/all.xml').read_bytes())
            check_site(Path(d))
