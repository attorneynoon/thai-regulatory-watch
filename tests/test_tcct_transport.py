"""The TCCT read-only JSON POST is a narrow exception, not a general POST API."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from regwatch.transport import AccessBlocked, AGENT, Transport

ENDPOINT = 'https://www.tcct.or.th/api/proxy/contents/now'
PAYLOAD = {'category_key': 'verdict', 'is_active': True, 'page_number': 1,
           'limit': 12, 'sort_by': 'start_date', 'sort_direction': 'desc'}


class Response:
    def __init__(self, status, body=b'{}', headers=None):
        self.status_code, self.body = status, body
        self.headers = headers or {'Content-Type': 'application/json'}
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def iter_content(self, size): yield self.body


class Session:
    def __init__(self, responses):
        from requests.cookies import RequestsCookieJar
        self.cookies = RequestsCookieJar()
        self.calls = []
        self.responses = iter(responses)
    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return next(self.responses)


class TcctTransportTests(unittest.TestCase):
    def test_posts_json_after_robots_and_accepts_201_only_for_exact_contract(self):
        session = Session([Response(200, b'User-agent: *\nDisallow:'), Response(201)])
        transport = Transport(['www.tcct.or.th'], session=session)
        with patch('regwatch.transport.public_address'), patch('regwatch.transport.time.sleep'):
            result = transport.fetch(ENDPOINT, json_body=PAYLOAD)
        self.assertEqual(result[0], 201)
        self.assertEqual([r[0] for r in session.calls], ['GET', 'POST'])
        self.assertEqual(session.calls[0][1], 'https://www.tcct.or.th/robots.txt')
        request = session.calls[1][2]
        self.assertEqual(request['json'], PAYLOAD)
        self.assertIsNone(request.get('data'))
        self.assertEqual(request['headers']['User-Agent'], AGENT)
        self.assertFalse(request['allow_redirects'])
        self.assertEqual(request['timeout'], (8, 20))
        self.assertFalse(session.trust_env)

    def test_ordinary_get_still_rejects_201(self):
        session = Session([Response(200, b''), Response(201)])
        with patch('regwatch.transport.public_address'), patch('regwatch.transport.time.sleep'):
            with self.assertRaisesRegex(ValueError, 'HTTP 201'):
                Transport(['www.tcct.or.th'], session=session).fetch(ENDPOINT)

    def test_wrong_endpoint_fields_types_and_scope_are_rejected_before_network(self):
        variants = [
            ('https://www.tcct.or.th/api/other', PAYLOAD),
            (ENDPOINT + '?x=1', PAYLOAD),
            (ENDPOINT, {**PAYLOAD, 'category_key': 'arbitrary-key'}),
            (ENDPOINT, {**PAYLOAD, 'page_number': True}),
            (ENDPOINT, {**PAYLOAD, 'page_number': 101}),
            (ENDPOINT, {**PAYLOAD, 'limit': True}),
            (ENDPOINT, {**PAYLOAD, 'is_active': 1}),
            (ENDPOINT, {**PAYLOAD, 'sort_by': 'owner'}),
            (ENDPOINT, {**PAYLOAD, 'extra': 'not allowed'}),
        ]
        for url, payload in variants:
            with self.subTest(url=url, payload=payload):
                session = Session([])
                transport = Transport(['www.tcct.or.th'], session=session)
                with self.assertRaises(ValueError):
                    transport.fetch(url, json_body=payload)
                self.assertEqual(session.calls, [])

    def test_form_and_json_cannot_be_combined(self):
        session = Session([])
        with self.assertRaises(ValueError):
            Transport(['www.tcct.or.th'], session=session).fetch(ENDPOINT, json_body=PAYLOAD, form={'a': 'b'})
        self.assertEqual(session.calls, [])

    def test_tcct_post_redirect_is_never_replayed_or_converted_to_get(self):
        for status in (301, 302, 303, 307, 308):
            with self.subTest(status=status):
                session = Session([Response(200, b''), Response(status, headers={'Location': '/api/other'})])
                with patch('regwatch.transport.public_address'), patch('regwatch.transport.time.sleep'):
                    with self.assertRaisesRegex(ValueError, 'redirect'):
                        Transport(['www.tcct.or.th'], session=session).fetch(ENDPOINT, json_body=PAYLOAD)
                self.assertEqual(len(session.calls), 2)

    def test_disallow_access_block_and_byte_guard_remain_active(self):
        session = Session([Response(200, b'User-agent: *\nDisallow: /api/')])
        with patch('regwatch.transport.public_address'), patch('regwatch.transport.time.sleep'):
            with self.assertRaises(AccessBlocked):
                Transport(['www.tcct.or.th'], session=session).fetch(ENDPOINT, json_body=PAYLOAD)
        self.assertEqual(len(session.calls), 1)
        for status in (403, 429):
            session = Session([Response(200, b''), Response(status)])
            with patch('regwatch.transport.public_address'), patch('regwatch.transport.time.sleep'):
                with self.assertRaises(AccessBlocked):
                    Transport(['www.tcct.or.th'], session=session).fetch(ENDPOINT, json_body=PAYLOAD)
        session = Session([Response(200, b''), Response(201, b'12345')])
        with patch('regwatch.transport.public_address'), patch('regwatch.transport.time.sleep'):
            with self.assertRaisesRegex(ValueError, r'limit=4; received_at_least=5; HTTP=201; content_type=application/json'):
                Transport(['www.tcct.or.th'], session=session).fetch(ENDPOINT, json_body=PAYLOAD, max_bytes=4)


if __name__ == '__main__':
    unittest.main()
