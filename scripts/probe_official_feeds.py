"""Read-only qualification for newly discovered official feed endpoints."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from regwatch.collector import collect_source
from regwatch.engine import empty_state
from regwatch.transport import Transport


SOURCE_IDS = {'etda-listing-01', 'etda-listing-02'}


def main():
    sources = yaml.safe_load((ROOT/'config/sources.yml').read_text('utf-8'))['sources']
    selected = [source for source in sources if source['id'] in SOURCE_IDS]
    if {source['id'] for source in selected} != SOURCE_IDS:
        raise SystemExit('ETDA feed source missing from registry')
    now = datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
    failed = False
    for source in selected:
        state = empty_state()
        transport = Transport(source['allowed_hosts'])
        result = collect_source(state,source,now,transport=transport,root=ROOT)
        observations = list(result.get('observations',{}).values())
        latest = observations[0] if observations else {}
        print(json.dumps({
            'source': source['id'],
            'status': result['status'],
            'records': result.get('last_count'),
            'latest_title': latest.get('title'),
            'latest_published_at': latest.get('published_at'),
            'error': result.get('last_error'),
        },ensure_ascii=False),flush=True)
        failed = failed or result['status'] != 'healthy'
    if failed:
        raise SystemExit('One or more official feed probes failed')


if __name__ == '__main__':
    main()
