"""Read-only GitHub Chromium qualification for unhealthy HTML sources."""
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from regwatch.collector import collect_source
from regwatch.browser_transport import RenderedTransport
from regwatch.engine import empty_state


def main():
    sources = yaml.safe_load((ROOT/'config/sources.yml').read_text('utf-8'))['sources']
    production = json.loads((ROOT/'state/monitor.json').read_text('utf-8'))
    targets = [
        s for s in sources
        if s['mode'] in {'html','page'} and (
            not s['enabled'] or
            production['sources'].get(s['id'],{}).get('status') in {'blocked','failed'}
        )
    ]
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
