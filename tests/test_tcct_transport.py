"""The TCCT public listing POST is not a general write or redirect facility."""
import json
import unittest
from unittest.mock import patch
from regwatch.transport import Transport, AccessBlocked

URL = 'https://www.tcct.or.th/api/proxy/contents/now'

class TCCTTransportTests(unittest.TestCase):
    def test_fixed_read_payload_and_201(self):
        transport = Transport(['www.tcct.or.th'])
        with patch.object(transport, '_raw', side_effect=[(404, {}, b''), (201, {'Content-Type':'application/json'}, b'{"status":"success"}')]) as raw:
            result = transport.fetch_tcct_page('verdict', 2, 12)
        self.assertEqual(result, (201, {'Content-Type':'application/json'}, b'{"status":"success"}', URL))
        call = raw.call_args
        self.assertEqual(call.args[0], URL)
        self.assertEqual(json.loads(call.kwargs['form']), {'category_key':'verdict','is_active':True,'page_number':2,'limit':12,'sort_by':'start_date','sort_direction':'desc'})
        self.assertEqual(call.kwargs['headers']['Content-Type'], 'application/json')

    def test_bounds_and_category_rejected_before_network(self):
        for category,page,limit in [('other',1,12),('verdict',0,12),('verdict',11,12),('verdict',True,12),('verdict',1,0),('verdict',1,13)]:
            with self.subTest(category=category,page=page,limit=limit):
                with self.assertRaises(ValueError):
                    Transport(['www.tcct.or.th']).fetch_tcct_page(category,page,limit)

    def test_explicit_host_allowlist_required(self):
        with self.assertRaises(ValueError):
            Transport(['example.org']).fetch_tcct_page('verdict')

    def test_robots_disallow_stops_post(self):
        transport = Transport(['www.tcct.or.th'])
        with patch.object(transport,'_raw',return_value=(200,{},b'User-agent: *\nDisallow: /api/')):
            with self.assertRaises(AccessBlocked):
                transport.fetch_tcct_page('verdict')

    def test_no_redirect_replay_or_redirect_get(self):
        for status in (301,302,303,307,308):
            transport = Transport(['www.tcct.or.th'])
            with patch.object(transport,'_raw',side_effect=[(404,{},b''),(status,{'Location':'/somewhere'},b'')]):
                with self.assertRaisesRegex(ValueError,'redirect'):
                    transport.fetch_tcct_page('verdict')

    def test_access_denials_and_non_json_rejected(self):
        for status,headers,body in [(403,{},b''),(429,{},b''),(201,{'Content-Type':'text/html'},b'<html>challenge</html>'),(500,{},b'')]:
            transport=Transport(['www.tcct.or.th'])
            with patch.object(transport,'_raw',side_effect=[(404,{},b''),(status,headers,body)]):
                with self.assertRaises(ValueError):
                    transport.fetch_tcct_page('verdict')

    def test_normal_get_does_not_accept_201(self):
        transport=Transport(['www.tcct.or.th'])
        with patch.object(transport,'_raw',side_effect=[(404,{},b''),(201,{'Content-Type':'application/json'},b'{}')]):
            with self.assertRaisesRegex(ValueError,'HTTP 201'):
                transport.fetch(URL)
