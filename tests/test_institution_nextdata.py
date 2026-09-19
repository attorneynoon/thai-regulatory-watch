import json
import unittest

from regwatch.nextdata import extract_next_rows


def flight(payload):
    return ('<script>self.__next_f.push(' + json.dumps([1, 'd:' + json.dumps(payload)]) + ')</script>').encode()


class NextDataTests(unittest.TestCase):
    def test_exact_embedded_listing_excludes_highlights(self):
        body = flight(['$', '$L2d', None, {'content': {'highlights': [{'title': 'old'}], 'list': {'data': [{'uuid': 'abc', 'title': 'New', 'startDate': None}]}}}])
        self.assertEqual(extract_next_rows(body, '3.content.list.data'), [{'uuid': 'abc', 'title': 'New', 'startDate': None}])

    def test_absent_or_changed_contract_fails(self):
        for body in (b'<p>No data</p>', flight({'data': []}), flight(['$', None, None, {'content': {'list': {'data': 'changed'}}}])):
            with self.assertRaises(ValueError):
                extract_next_rows(body, '3.content.list.data')

    def test_no_javascript_execution_or_expression_parsing(self):
        with self.assertRaises(ValueError):
            extract_next_rows(b'<script>self.__next_f.push((function(){return [1,"x"]})())</script>', '3.content.list.data')

    def test_empty_real_list_is_valid(self):
        self.assertEqual(extract_next_rows(flight([None, None, None, {'content': {'list': {'data': []}}}]), '3.content.list.data'), [])
