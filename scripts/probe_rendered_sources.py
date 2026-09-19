"""Read-only GitHub Chromium qualification for unhealthy HTML sources."""
import json
import sys
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from regwatch.collector import collect_source
from regwatch.engine import empty_state
from regwatch.registry import allowed_url
from regwatch.transport import AccessBlocked, CHALLENGE_MARKERS, Transport, public_address


class RenderedTransport:
    """Render only the allowlisted top-level document after the normal robots gate."""

    def __init__(self, source, browser):
        self.source = source
        self.safety = Transport(source['allowed_hosts'])
        self.context = browser.new_context()

    def close(self):
        self.context.close()

    def fetch(self, url, headers=None, max_bytes=4_000_000, form=None):
        if form is not None:
            raise ValueError('Rendered probe does not submit forms')
        url = allowed_url(url, self.source['allowed_hosts'])
        public_address(url)
        delay = self.safety._policy(url)
        host = __import__('urllib.parse').parse.urlsplit(url).hostname
        wait = self.safety.last_request.get(host, 0) + delay - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self.safety.last_request[host] = time.monotonic()
        page = self.context.new_page()
        try:
            response = page.goto(url, wait_until='domcontentloaded', timeout=30_000)
            if response is None:
                raise AccessBlocked('Browser navigation returned no document response')
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
            head = body[:20000].lower()
            if any(marker in head for marker in CHALLENGE_MARKERS):
                raise AccessBlocked('Rendered challenge page')
            return status, dict(response.headers), body, final
        finally:
            page.close()


def main():
    sources = yaml.safe_load((ROOT/'config/sources.yml').read_text('utf-8'))['sources']
    production = json.loads((ROOT/'state/monitor.json').read_text('utf-8'))
    targets = [s for s in sources if s['enabled'] and s['mode'] in {'html','page'} and production['sources'].get(s['id'],{}).get('status') in {'blocked','failed'}]
    now = datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
    print(json.dumps({'probe':'ordinary Chromium rendering after robots gate','targets':len(targets)}),flush=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            for source in targets:
                test_source = deepcopy(source)
                test_source['asset_budget'] = 0
                state = empty_state()
                transport = RenderedTransport(test_source,browser)
                try:
                    result = collect_source(state,test_source,now,transport=transport,root=ROOT)
                    print(json.dumps({'source':source['id'],'url':source['url'],'status':result['status'],'records':result['last_count'],'pages':result.get('listing_pages_checked'),'error':result.get('last_error')},ensure_ascii=False),flush=True)
                finally:
                    transport.close()
        finally:
            browser.close()


if __name__ == '__main__':
    main()
