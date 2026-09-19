import unittest
from unittest.mock import Mock,patch
from regwatch.browser_transport import RenderedTransport
from regwatch.transport import AccessBlocked

class Response:
    status=200
    headers={'content-type':'text/html'}

class Page:
    def __init__(self,html='<html><article>News</article></html>',url='https://example.org/news',status=200):
        self.html,self.url=html,url
        self.response=Response();self.response.status=status
    def goto(self,*a,**k):self.goto_options=k;return self.response
    def wait_for_load_state(self,*a,**k):pass
    def content(self):return self.html
    def close(self):pass

class Context:
    def __init__(self,page):self.page=page
    def route(self,*a):self.route_handler=a[1]
    def new_page(self):return self.page
    def close(self):pass

class Browser:
    def __init__(self,page):self.page=page
    def new_context(self):return Context(self.page)

class Request:
    def __init__(self,url,resource_type='script',navigation=False):
        self.url,self.resource_type,self.navigation=url,resource_type,navigation
    def is_navigation_request(self):return self.navigation

class Route:
    def __init__(self,request):self.request=request;self.action=None
    def abort(self):self.action='abort'
    def continue_(self):self.action='continue'

class BrowserTransportTests(unittest.TestCase):
    def source(self):return {'allowed_hosts':['example.org']}

    @patch('regwatch.browser_transport.public_address')
    def test_rendered_html_after_robots_gate(self,_):
        safety=Mock();safety._policy.return_value=0;safety.last_request={}
        transport=RenderedTransport(self.source(),Browser(Page()),safety=safety)
        self.assertIn(b'<article>News</article>',transport.fetch('https://example.org/news')[2])
        safety._policy.assert_called_once_with('https://example.org/news')
        self.assertEqual(transport.context.page.goto_options['wait_until'],'commit')

    @patch('regwatch.browser_transport.public_address')
    def test_redirect_outside_allowlist_and_challenge_are_blocked(self,_):
        safety=Mock();safety._policy.return_value=0;safety.last_request={}
        for page in [Page(url='https://evil.example/news'),Page(html='<html>verify you are human</html>')]:
            with self.subTest(page=page.url):
                transport=RenderedTransport(self.source(),Browser(page),safety=safety)
                with self.assertRaises((ValueError,AccessBlocked)):transport.fetch('https://example.org/news')

    @patch('regwatch.browser_transport.public_address')
    def test_http_denial_and_forms_remain_blocked(self,_):
        safety=Mock();safety._policy.return_value=0;safety.last_request={}
        transport=RenderedTransport(self.source(),Browser(Page(status=403)),safety=safety)
        with self.assertRaises(AccessBlocked):transport.fetch('https://example.org/news')
        with self.assertRaises(ValueError):transport.fetch('https://example.org/news',form={'x':'1'})

    def test_browser_context_registers_a_bounded_request_route(self):
        safety=Mock();safety._policy.return_value=0;safety.last_request={}
        transport=RenderedTransport(self.source(),Browser(Page()),safety=safety)
        self.assertTrue(callable(transport.context.route_handler))

    @patch('regwatch.browser_transport.public_address')
    def test_request_route_omits_third_party_assets_and_blocks_redirects(self,_):
        safety=Mock();safety._policy.return_value=0;safety.last_request={}
        transport=RenderedTransport(self.source(),Browser(Page()),safety=safety)
        asset=Route(Request('https://tracker.example/pixel.js'))
        transport._route_request(asset)
        self.assertEqual(asset.action,'abort')
        self.assertIsNone(transport._navigation_block)
        redirect=Route(Request('https://evil.example/news',navigation=True))
        transport._route_request(redirect)
        self.assertEqual(redirect.action,'abort')
        self.assertIsNotNone(transport._navigation_block)
