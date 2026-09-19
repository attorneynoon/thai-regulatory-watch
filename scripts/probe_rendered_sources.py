"""Read-only GitHub Chromium qualification for unhealthy HTML sources."""
import json
import os
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import yaml
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from regwatch.collector import collect_source
from regwatch.browser_transport import RenderedTransport
from regwatch.engine import empty_state


MARKUP_TARGETS = {
    'dlt-watch', 'etda-listing-01', 'etda-listing-02', 'mot-watch',
    'ocs-council-of-state-law-search-application', 'set-watch', 'tsd-watch',
}


def save_safe_markup(source_id, body):
    output = os.environ.get('RENDERED_PROBE_OUTPUT')
    if not output or source_id not in MARKUP_TARGETS or not body:
        return
    soup = BeautifulSoup(body, 'html.parser')
    for node in soup.select('script,style,noscript,iframe,form,input,textarea,meta'):
        node.decompose()
    path = Path(output)
    path.mkdir(parents=True, exist_ok=True)
    (path/f'{source_id}.html').write_text(str(soup), encoding='utf-8')


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
                    save_safe_markup(source['id'], transport.last_body)
                    examples = [
                        {
                            'title': row.get('title'),
                            'url': row.get('canonical_url'),
                            'published_at': row.get('published_at'),
                        }
                        for row in list(result.get('observations', {}).values())[:5]
                    ]
                    print(json.dumps({'source':source['id'],'url':source['url'],'status':result['status'],'records':result['last_count'],'pages':result.get('listing_pages_checked'),'examples':examples,'error':result.get('last_error')},ensure_ascii=False),flush=True)
                finally:
                    transport.close()
        finally:
            browser.close()


if __name__ == '__main__':
    main()
