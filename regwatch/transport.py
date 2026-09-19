"""Bounded public HTTPS with robots checks on each content redirect."""
import ipaddress
import socket
import time
from urllib.parse import urlsplit, urljoin
from urllib.robotparser import RobotFileParser
import requests
from .registry import allowed_url

AGENT = "ThaiRegulatoryWatch/1.0 (+https://github.com/attorneynoon/thai-regulatory-watch)"


class AccessBlocked(ValueError):
    pass


def public_address(url):
    host = urlsplit(url).hostname
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise AccessBlocked("Non-public destination")


class Transport:
    def __init__(self, hosts, session=None):
        self.hosts = hosts
        self.session = session or requests.Session()
        self.session.trust_env = False
        self.robots = {}
        self.last_request = {}

    def _raw(self, url, headers=None, max_bytes=4_000_000, delay=1.0):
        allowed_url(url, self.hosts)
        public_address(url)
        host = urlsplit(url).hostname
        wait = self.last_request.get(host, 0) + delay - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self.last_request[host] = time.monotonic()
        self.session.cookies.clear()
        with self.session.get(url, headers={"User-Agent": AGENT, **(headers or {})}, timeout=(8, 20), allow_redirects=False, stream=True) as r:
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
                    status, headers, body = self._raw(location, max_bytes=256_000)
                    if status in (301, 302, 303, 307, 308):
                        location = allowed_url(urljoin(location, headers.get("Location", "")), self.hosts)
                        continue
                    policy = RobotFileParser()
                    if status in (404, 410):
                        policy.parse([])
                    elif status == 200 and not body.lstrip().lower().startswith((b"<!doctype html", b"<html")):
                        policy.parse(body.decode("utf-8", "replace").splitlines())
                    else:
                        raise AccessBlocked("Robots unavailable: HTTP " + str(status))
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
            except Exception as exc:
                self.robots[origin] = AccessBlocked("Robots unavailable: " + str(exc)[:200])
        result = self.robots[origin]
        if isinstance(result, Exception):
            raise result
        policy, delay = result
        if not policy.can_fetch(AGENT, url):
            raise AccessBlocked("Disallowed by robots.txt")
        return delay

    def fetch(self, url, headers=None, max_bytes=4_000_000):
        for _ in range(5):
            url = allowed_url(url, self.hosts)
            delay = self._policy(url)
            status, response_headers, body = self._raw(url, headers, max_bytes, delay)
            if status in (301, 302, 303, 307, 308):
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
                if any(x in head for x in (b"cf-chl-", b"verify you are human", b"<title>just a moment", b"<title>access denied")):
                    raise AccessBlocked("Challenge page")
            return status, response_headers, body, url
        raise AccessBlocked("Redirect limit exceeded")
