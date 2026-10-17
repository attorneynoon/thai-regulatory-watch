import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import requests

from regwatch.collector import collect_source
from regwatch.engine import apply_observations, empty_state
from regwatch.registry import load_registry
from regwatch.transport import Transport


class Response:
    def __init__(self, body, status=200, content_type='application/json'):
        self.body, self.status_code = body, status
        self.headers = {'Content-Type': content_type}
        self.bytes_read = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def iter_content(self, size):
        for offset in range(0, len(self.body), size):
            chunk = self.body[offset:offset + size]
            self.bytes_read += len(chunk)
            yield chunk


class Session:
    def __init__(self, response):
        self.response = response
        self.cookies = requests.cookies.RequestsCookieJar()

    def request(self, method, url, **kwargs):
        if method != 'GET' or kwargs.get('allow_redirects') is not False:
            raise AssertionError('Expected bounded ordinary GET transport')
        if url.endswith('/robots.txt'):
            return Response(b'User-agent: *\nAllow: /\n', content_type='text/plain')
        return self.response


class ResponseBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = [s for s in load_registry(Path(__file__).resolve().parents[1] / 'config/sources.yml')
                       if s['id'] in {'ncsa-listing-01', 'ncsa-listing-02', 'ncsa-listing-03'}]
        # Synthetic transport-growth regression, not a claimed live NCSA capture.
        cls.large_json = (
            b'[{"_id":"public-1","title":"Public update","showdate":"2026-10-16",'
            b'"_state":1,"category":["announcement","news"],"unused":"'
            + b'x' * 32_000_000 + b'"}]'
        )

    def setUp(self):
        self.address = patch('regwatch.transport.public_address').start()
        patch('regwatch.transport.time.sleep').start()
        self.addCleanup(patch.stopall)

    def transport(self, response):
        return Transport(['www.ncsa.or.th'], session=Session(response))

    def test_configured_ncsa_scopes_accept_valid_growth_above_old_ceiling(self):
        for source in self.sources:
            with self.subTest(source=source['id']):
                state = empty_state()
                collect_source(state, source, '2026-10-17T00:00:00Z',
                               self.transport(Response(self.large_json)))
                self.assertEqual(state['sources'][source['id']]['status'], 'healthy')
                self.assertEqual(len(state['items']), 1)
                event = state['events'][0]
                self.assertEqual(event['title'], 'Public update')
                self.assertEqual(event['published_at'], '2026-10-16')
                self.assertEqual(event['review_status'], 'unreviewed')
                self.assertEqual(event['legal_effect'], 'Not assessed')
                self.assertNotIn('unused', event)

    def test_stream_accepts_exact_limit_and_stops_one_byte_over(self):
        source = self.sources[0]
        self.assertEqual(self.transport(Response(b'x' * 10)).fetch(source['url'], max_bytes=10)[2], b'x' * 10)
        response = Response(b'x' * 11)
        with self.assertRaisesRegex(ValueError, r'limit=10.*received_at_least=11.*HTTP=200'):
            self.transport(response).fetch(source['url'], max_bytes=10)

    def test_overflow_reports_error_response_status_before_parsing(self):
        with self.assertRaisesRegex(ValueError, r'HTTP=503.*content_type=text/html'):
            self.transport(Response(b'x' * 11, status=503, content_type='text/html')).fetch(
                self.sources[0]['url'], max_bytes=10)

    def test_overflow_retains_prior_items_observations_and_success(self):
        source = {**self.sources[0], 'max_response_bytes': 1000}
        state = empty_state()
        apply_observations(state, source, [{'url': 'https://www.ncsa.or.th/news/old', 'title': 'Old publication'}],
                           '2026-09-29T08:35:30Z')
        before = deepcopy(state)
        collect_source(state, source, '2026-10-17T00:00:00Z', self.transport(Response(b'x' * 1001)))
        self.assertEqual(state['items'], before['items'])
        self.assertEqual(state['events'], before['events'])
        record = state['sources'][source['id']]
        self.assertEqual(record['observations'], before['sources'][source['id']]['observations'])
        self.assertEqual(record['last_success_at'], '2026-09-29T08:35:30Z')
        self.assertEqual(record['status'], 'failed')
        self.assertIn('limit=1000', record['last_error'])

    def test_larger_budget_still_rejects_http_denial_and_invalid_json(self):
        source = self.sources[0]
        denied = empty_state()
        collect_source(denied, source, '2026-10-17T00:00:00Z',
                       self.transport(Response(self.large_json, status=403)))
        self.assertEqual(denied['sources'][source['id']]['status'], 'blocked')
        self.assertEqual(denied['items'], {})
        state = empty_state()
        collect_source(state, source, '2026-10-17T00:00:00Z', self.transport(Response(b'not JSON')))
        self.assertEqual(state['sources'][source['id']]['status'], 'failed')
        self.assertEqual(state['items'], {})


if __name__ == '__main__':
    unittest.main()
