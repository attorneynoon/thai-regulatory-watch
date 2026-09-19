import ssl
import unittest
from pathlib import Path
from unittest.mock import patch
from regwatch.transport import Transport
from regwatch.collector import collect_source
from regwatch.engine import empty_state
from test_engine import SOURCE

ROOT=Path(__file__).resolve().parents[1]
CERT=ROOT/'config/tls/globalsign-gcc-r6-alphassl-2025.pem'

class TlsRepairTests(unittest.TestCase):
    def test_collection_resolves_intermediate_against_explicit_root(self):
        source={**SOURCE,'mode':'html','allowed_hosts':['example.org'],'url':'https://example.org/',
                'tls_intermediates':{'example.org':'config/tls/globalsign-gcc-r6-alphassl-2025.pem'}}
        state=empty_state()
        with patch('regwatch.collector.Transport') as transport:
            transport.return_value.fetch.return_value=(200,{},b'<a href="/a">A</a>',source['url'])
            collect_source(state,source,'2026-09-19T00:00:00Z',root=ROOT)
            self.assertEqual(transport.call_args.kwargs['tls_intermediates']['example.org'],str(CERT))
        with patch('regwatch.collector.Transport',side_effect=ValueError('bad certificate')):
            result=collect_source(state,source,'2026-09-19T01:00:00Z',root=ROOT)
            self.assertEqual(result['status'],'failed')
            self.assertEqual(len(state['items']),1)

    def test_intermediate_is_host_scoped_and_never_disables_verification(self):
        t=Transport(['pr.tisi.go.th','example.org'],tls_intermediates={'pr.tisi.go.th':str(CERT)})
        adapter=t.session.get_adapter('https://pr.tisi.go.th/feed/')
        self.assertIsNot(adapter,t.session.get_adapter('https://example.org/'))
        self.assertIsNot(adapter,t.session.get_adapter('https://pr.tisi.go.th.evil.test/'))
        self.assertEqual(adapter.context.verify_mode,ssl.CERT_REQUIRED)
        self.assertTrue(adapter.context.check_hostname)
        self.assertFalse(adapter.context.verify_flags & ssl.VERIFY_X509_PARTIAL_CHAIN)
        self.assertTrue(t.session.verify)

    def test_unknown_tls_host_rejected(self):
        with self.assertRaises(ValueError):
            Transport(['example.org'],tls_intermediates={'other.example':str(CERT)})

    def test_form_redirect_does_not_resubmit_or_skip_robots(self):
        t=Transport(['example.org'])
        with patch.object(t,'_raw',side_effect=[(404,{},b''),(303,{'Location':'/result'},b''),(200,{},b'ok')]) as raw:
            self.assertEqual(t.fetch('https://example.org/',form={'intro_page':'1'})[2],b'ok')
            self.assertEqual(raw.call_args_list[1].kwargs['form'],{'intro_page':'1'})
            self.assertIsNone(raw.call_args_list[2].kwargs.get('form'))
        t=Transport(['example.org'])
        with patch.object(t,'_raw',side_effect=[(404,{},b''),(307,{'Location':'/other'},b'')]):
            with self.assertRaises(ValueError): t.fetch('https://example.org/',form={'intro_page':'1'})
