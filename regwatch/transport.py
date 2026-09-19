"""Bounded public HTTPS with robots checks on each content redirect."""
import ipaddress
import socket
import time
import ssl
from pathlib import Path
from urllib.parse import urlsplit, urljoin
from protego import Protego
import requests
from .registry import allowed_url

AGENT = "ThaiRegulatoryWatch/1.0 (+https://github.com/attorneynoon/thai-regulatory-watch)"
CHALLENGE_MARKERS = (b'cf-chl-', b'verify you are human', b'<title>just a moment', b'<title>access denied', b'incapsula incident id')


class AccessBlocked(ValueError):
    pass


class IntermediateAdapter(requests.adapters.HTTPAdapter):
    """Supply a missing CA intermediate without trusting it as a root."""
    def __init__(self, certificate):
        self.context=ssl.create_default_context(cafile=requests.certs.where())
        self.context.verify_flags &= ~ssl.VERIFY_X509_PARTIAL_CHAIN
        self.context.load_verify_locations(cafile=str(certificate))
        super().__init__()

    def build_connection_pool_key_attributes(self, request, verify, cert=None):
        if verify is not True:
            raise ValueError('TLS verification must remain enabled')
        host_params,pool_kwargs=super().build_connection_pool_key_attributes(request,verify,cert)
        pool_kwargs['ssl_context']=self.context
        return host_params,pool_kwargs


def public_address(url):
    host = urlsplit(url).hostname
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise AccessBlocked("Non-public destination")


class Transport:
    def __init__(self, hosts, session=None, tls_intermediates=None):
        self.hosts = hosts
        self.session = session or requests.Session()
        self.session.trust_env = False
        for host,certificate in (tls_intermediates or {}).items():
            if host not in hosts: raise ValueError('TLS repair host outside allowlist')
            self.session.mount('https://'+host+'/',IntermediateAdapter(Path(certificate)))
        self.robots = {}
        self.last_request = {}

    def _raw(self, url, headers=None, max_bytes=4_000_000, delay=1.0, form=None):
        allowed_url(url, self.hosts)
        public_address(url)
        host = urlsplit(url).hostname
        wait = self.last_request.get(host, 0) + delay - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self.last_request[host] = time.monotonic()
        self.session.cookies.clear()
        with self.session.request('POST' if form is not None else 'GET',url, data=form, headers={"User-Agent": AGENT, **(headers or {})}, timeout=(8, 20), allow_redirects=False, stream=True) as r:
            data = bytearray()
            for chunk in r.iter_content(65536):
                data.extend(chunk)
                if len(data) > max_bytes:
                    raise ValueError("Response exceeds byte budget")
            return r.status_code, requests.structures.CaseInsensitiveDict(r.headers), bytes(data)

    def _policy(self, url):
        p = urlsplit(url)
        origin = p.scheme + "://" + p.netloc
        if origin not in self.robots:
            location = origin + "/robots.txt"
            policy = None
            try:
                for _ in range(5):
                    status, headers, body = self._raw(location, max_bytes=1_000_000)
                    if status in (301, 302, 303, 307, 308):
                        location = allowed_url(urljoin(location, headers.get("Location", "")), self.hosts)
                        continue
                    # RFC 9309 2.3.1.3: unavailable robots (4xx) is not
                    # an explicit disallow. Content authorization is checked
                    # independently in fetch. Respect rate limiting regardless.
                    if 400 <= status < 500 and status != 429:
                        policy = Protego.parse('')
                    elif status == 200:
                        # RFC 9309 2.3.1.5: keep parseable rules even when the
                        # surrounding response is malformed. A challenge is
                        # not a successful policy response.
                        if any(marker in body.lower() for marker in CHALLENGE_MARKERS):
                            raise AccessBlocked('Robots challenge page')
                        policy = Protego.parse(body.decode("utf-8", "replace"))
                    else:
                        reason = 'unexpected HTML' if status == 200 else 'HTTP ' + str(status)
                        raise AccessBlocked("Robots policy unresolved: " + reason)
                    break
                if policy is None:
                    raise AccessBlocked("Robots redirect limit")
                delay = policy.crawl_delay(AGENT) or policy.crawl_delay("*") or 1
                if delay > 20:
                    raise AccessBlocked("Crawl delay exceeds supported budget")
                rate = policy.request_rate(AGENT) or policy.request_rate("*")
                if rate and rate.requests:
                    delay = max(delay, rate.seconds / rate.requests)
                if delay > 20:
                    raise AccessBlocked("Request rate exceeds supported budget")
                self.robots[origin] = (policy, delay)
            except AccessBlocked as exc:
                self.robots[origin] = exc
            except Exception as exc:
                self.robots[origin] = AccessBlocked("Robots unavailable: " + str(exc)[:200])
        result = self.robots[origin]
        if isinstance(result, Exception):
            raise result
        policy, delay = result
        if not policy.can_fetch(url, 'ThaiRegulatoryWatch'):
            raise AccessBlocked("Disallowed by robots.txt")
        return delay

    def fetch(self, url, headers=None, max_bytes=4_000_000, form=None):
        for _ in range(5):
            url = allowed_url(url, self.hosts)
            delay = self._policy(url)
            status, response_headers, body = self._raw(url, headers, max_bytes, delay,form=form)
            if status in (301, 302, 303, 307, 308):
                if form is not None and status in (307,308):
                    raise ValueError('Public navigation POST cannot be replayed on a redirect')
                form=None
                url = allowed_url(urljoin(url, response_headers.get("Location", "")), self.hosts)
                headers = None
                continue
            if status in (401, 403, 429):
                raise AccessBlocked("Access unavailable: HTTP " + str(status))
            if status not in (200, 304):
                raise ValueError("HTTP " + str(status))
            content_type = response_headers.get("Content-Type", "").lower()
            if "html" in content_type:
                head = body[:20000].lower()
                if any(x in head for x in CHALLENGE_MARKERS):
                    raise AccessBlocked("Challenge page")
            return status, response_headers, body, url
        raise AccessBlocked("Redirect limit exceeded")
