"""Read-only NCSA qualification: one fetch, production collection in memory.

No fetched body, observations, or generated output is written to disk. A
successful result qualifies this response against the configured collection
rules; it does not promote sources or change the persisted health snapshot.
"""
import sys

sys.dont_write_bytecode = True

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEFAULT_ROOT))

from regwatch.collector import collect_source
from regwatch.models import utcnow
from regwatch.registry import load_registry
from regwatch.storage import load_state
from regwatch.transport import AccessBlocked, Transport


SOURCE_IDS = ('ncsa-listing-01', 'ncsa-listing-02', 'ncsa-listing-03')
EXPORT_URL = 'https://www.ncsa.or.th/data/output/news.json'
EXPORT_HOST = 'www.ncsa.or.th'


class PrefetchedTransport:
    """Replay only the single export while retaining each source's byte limit."""

    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error

    def fetch(self, url, headers=None, max_bytes=4_000_000, form=None):
        if url != EXPORT_URL or form is not None:
            raise AccessBlocked('NCSA qualification only serves the exact export URL')
        if self.error is not None:
            raise self.error
        status, response_headers, body, final_url = self.response
        if final_url != EXPORT_URL:
            raise AccessBlocked('NCSA qualification requires the exact export final URL')
        if len(body) > max_bytes:
            raise ValueError(
                f'Response exceeds byte budget: limit={max_bytes}; observed={len(body)}'
            )
        if status in (401, 403, 429):
            raise AccessBlocked('Access unavailable: HTTP ' + str(status))
        return status, response_headers, body, final_url


def history_preserved(before, after):
    """Check immutable event history and every retained source/item identity."""
    for key in ('events', 'health_events'):
        if after[key][:len(before[key])] != before[key]:
            return False
    for item_id, item in before['items'].items():
        current = after['items'].get(item_id)
        if current is None or current['first_observed_at'] != item['first_observed_at']:
            return False
        if not set(item['source_ids']).issubset(current['source_ids']):
            return False
    stable_fields = ('item_id', 'source_id', 'canonical_url', 'first_observed_at')
    for source_id, source in before['sources'].items():
        current = after['sources'].get(source_id)
        if current is None:
            return False
        if source_id not in SOURCE_IDS and current != source:
            return False
        for item_id, observation in source['observations'].items():
            latest = current['observations'].get(item_id)
            if latest is None or latest['revision'] < observation['revision']:
                return False
            if any(latest.get(key) != observation.get(key) for key in stable_fields):
                return False
    return True


def qualify(root=DEFAULT_ROOT, *, transport=None, now=None):
    """Return compact diagnostics without changing input files or source status."""
    root = Path(root).resolve()
    checked_at = now or utcnow()
    report = {
        'checked_at': checked_at,
        'url': EXPORT_URL,
        'status': 'failed',
        'http_status': None,
        'bytes': None,
        'sha256': None,
        'content_type': None,
        'history_preserved': False,
        'sources': [],
    }
    try:
        registry = {source['id']: source for source in load_registry(root / 'config/sources.yml')}
        sources = [registry[source_id] for source_id in SOURCE_IDS]
        if any(source['url'] != EXPORT_URL or source['allowed_hosts'] != [EXPORT_HOST]
               or source['mode'] != 'json' or not source['enabled'] for source in sources):
            raise ValueError('NCSA qualification requires the three enabled exact-host JSON export scopes')
        original = load_state(root / 'state/monitor.json')
    except OSError:
        report['error'] = 'Unable to read the registry or retained state; no network request made'
        return report
    except Exception as exc:
        report['error'] = str(exc)[:350]
        return report

    working = deepcopy(original)
    budget = max(source.get('max_response_bytes', 4_000_000) for source in sources)
    report['max_response_bytes'] = budget
    network = transport if transport is not None else Transport([EXPORT_HOST])
    try:
        response = network.fetch(EXPORT_URL, max_bytes=budget)
        status, headers, body, final_url = response
        report.update(
            http_status=status,
            bytes=len(body),
            sha256=hashlib.sha256(body).hexdigest(),
            content_type=headers.get('Content-Type', '')[:200],
            final_url=final_url,
        )
        replay = PrefetchedTransport(response)
    except Exception as exc:
        report['error'] = str(exc)[:350]
        replay = PrefetchedTransport(error=exc)
    finally:
        if transport is None:
            network.session.close()

    for source in sources:
        previous = original['sources'].get(source['id'], {})
        result = collect_source(working, source, checked_at, transport=replay, root=root)
        report['sources'].append({
            'source': source['id'],
            'validation': source['validation_status'],
            'status': result['status'],
            'count': result.get('last_count', 0),
            'count_basis': 'current-response' if result['status'] in ('healthy', 'degraded') else 'retained-state',
            'previous_count': previous.get('last_count', 0),
            'prior_observations': len(previous.get('observations', {})),
            'observations': len(result['observations']),
            'max_response_bytes': source.get('max_response_bytes', 4_000_000),
            'last_error': result.get('last_error'),
        })
    report['history_preserved'] = history_preserved(original, working)
    statuses = {source['status'] for source in report['sources']}
    if report['history_preserved'] and statuses == {'healthy'}:
        report['status'] = 'healthy'
    elif report['history_preserved'] and statuses.issubset({'healthy', 'blocked'}):
        report['status'] = 'blocked'
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args(argv)
    result = qualify(args.root)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return int(result['status'] != 'healthy')


if __name__ == '__main__':
    raise SystemExit(main())
