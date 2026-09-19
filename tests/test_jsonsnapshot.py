import json
import unittest
from regwatch.jsonsnapshot import parse_json_snapshot


class JsonSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.source = {'title': 'Public knowledge snapshot', 'allowed_hosts': ['example.org'], 'json_rows': 'data', 'json_filter': {'status': 1}, 'json_snapshot_fields': ['id', 'subject']}
        self.url = 'https://example.org/api/public/knowledge'

    def parse(self, rows):
        return parse_json_snapshot(self.source, json.dumps({'data': rows}).encode(), self.url)[0][0]

    def test_filters_disabled_records_and_retains_actual_endpoint(self):
        row = self.parse([{'id': 1, 'status': 1, 'subject': 'Public', 'user_id': 54}, {'id': 2, 'status': 0, 'subject': 'Disabled'}])
        self.assertEqual(self.url, row['url'])
        self.assertEqual(self.source['title'], row['title'])
        self.assertIsNone(row['published_at'])
        self.assertIn('1 selected', row['summary'])
        self.assertNotIn('user_id', str(row))
        self.assertNotIn('Disabled', str(row))

    def test_order_and_unselected_fields_do_not_change_hash(self):
        a = [{'id': 1, 'status': 1, 'subject': 'A', 'views': 1}, {'id': 2, 'status': 1, 'subject': 'B'}]
        b = [{'id': 2, 'status': 1, 'subject': 'B'}, {'id': 1, 'status': 1, 'subject': 'A', 'views': 999}]
        self.assertEqual(self.parse(a)['selected_text_sha256'], self.parse(b)['selected_text_sha256'])
        b[1]['subject'] = 'Changed'
        self.assertNotEqual(self.parse(a)['selected_text_sha256'], self.parse(b)['selected_text_sha256'])

    def test_schema_and_empty_results_fail_closed(self):
        for value in ({}, {'data': {}}, {'data': []}, {'data': [{'id': 1, 'status': 1}]}, {'data': [None]}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_json_snapshot(self.source, json.dumps(value).encode(), self.url)
        self.source['json_snapshot_fields'] = []
        with self.assertRaises(ValueError):
            self.parse([{'id': 1, 'status': 1, 'subject': 'A'}])


if __name__ == '__main__':
    unittest.main()
