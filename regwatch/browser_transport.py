"""Bounded browser rendering for public pages that require JavaScript."""
import time
from urllib.parse import urlsplit

from .registry import allowed_url
from .transport import AccessBlocked, CHALLENGE_MARKERS, Transport, public_address


class RenderedTransport:
    """Render an allowlisted top-level document after the normal robots gate."""

    def __init__(self, source, browser, safety=None):
        self.source = source
        self.safety = safety or Transport(
            source['allowed_hosts'],
            tls_intermediates=source.get('tls_intermediates'),
        )
        self.context = browser.new_context()
        self._public_hosts = set()
        self._navigation_block = None
        self.last_body = None
        self.context.route('**/*', self._route_request)

    def _route_request(self, route):
        request = route.request
        try:
            url = allowed_url(request.url, self.source['allowed_hosts'])
            host = urlsplit(url).hostname
            if urlsplit(url).scheme != 'https':
                raise AccessBlocked('Rendered requests require HTTPS')
            if host not in self._public_hosts:
                public_address(url)
                self._public_hosts.add(host)
            if request.is_navigation_request():
                self.safety._policy(url)
            if request.resource_type in {'image', 'media', 'font'}:
                route.abort()
            else:
                route.continue_()
        except Exception as exc:
            # Third-party page assets are simply omitted. A blocked navigation
            # is surfaced as a source failure rather than followed.
            if request.is_navigation_request():
                self._navigation_block = exc
            route.abort()

    def close(self):
        self.context.close()

    def fetch(self, url, headers=None, max_bytes=4_000_000, form=None):
        if form is not None:
            raise ValueError('Browser rendering does not submit forms')
        url = allowed_url(url, self.source['allowed_hosts'])
        public_address(url)
        delay = self.safety._policy(url)
        host = urlsplit(url).hostname
        wait = self.safety.last_request.get(host, 0) + delay - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self.safety.last_request[host] = time.monotonic()
        self._navigation_block = None
        self.last_body = None
        page = self.context.new_page()
        try:
            try:
                # Commit proves the top-level response without making a broken
                # third-party frame a 30-second source failure. The bounded
                # load waits below still give first-party JavaScript time to
                # populate the publication cards.
                response = page.goto(url, wait_until='commit', timeout=30_000)
            except Exception as exc:
                if self._navigation_block is not None:
                    raise AccessBlocked('Rendered navigation blocked: ' + str(self._navigation_block)) from exc
                raise
            if response is None:
                raise AccessBlocked('Browser navigation returned no document response')
            try:
                page.wait_for_load_state('domcontentloaded', timeout=15_000)
            except Exception:
                pass
            try:
                page.wait_for_load_state('networkidle', timeout=10_000)
            except Exception:
                pass
            final = allowed_url(page.url, self.source['allowed_hosts'])
            public_address(final)
            status = response.status
            if status in (401, 403, 429):
                raise AccessBlocked('Rendered access unavailable: HTTP ' + str(status))
            if status != 200:
                raise ValueError('Rendered HTTP ' + str(status))
            body = page.content().encode('utf-8')
            if len(body) > max_bytes:
                raise ValueError('Rendered response exceeds byte budget')
            if any(marker in body[:20000].lower() for marker in CHALLENGE_MARKERS):
                raise AccessBlocked('Rendered challenge page')
            self.last_body = body
            return status, dict(response.headers), body, final
        finally:
            page.close()
