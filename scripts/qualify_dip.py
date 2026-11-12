"""DIP-only bounded GET qualification. Replay copied state; never persist it."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from regwatch.adapters import parse_document
from regwatch.collector import collect_source
from regwatch.registry import load_registry
from regwatch.storage import load_state, validate_state
from regwatch.transport import Transport

ROOT = Path(__file__).resolve().parents[1]


class ResponseTransport:
    """Replay one captured listing without network or attachment traversal."""
    def __init__(self, body, url):
        self.body, self.url = body, url

    def fetch(self, url, **kwargs):
        if url != self.url:
            raise ValueError('Unexpected replay fetch; manual qualification required')
        return 200, {}, self.body, self.url


def replay(retained, source, body, now):
    state = deepcopy(retained)
    old_events = deepcopy(state['events'])
    old_health = deepcopy(state['health_events'])
    old_items = set(state['items'])
    old_observations = deepcopy(state['sources'].get(source['id'], {}).get('observations', {}))
    result = collect_source(state, source, now, transport=ResponseTransport(body, source['url']))
    history = (state['events'][:len(old_events)] == old_events
               and state['health_events'][:len(old_health)] == old_health
               and old_items <= set(state['items'])
               and set(old_observations) <= set(result['observations'])
               and all(result['observations'][key]['first_observed_at'] == value['first_observed_at']
                       for key, value in old_observations.items()))
    added = deepcopy(state['events'][len(old_events):])
    validate_state(state)
    first_state = deepcopy(state)
    collect_source(state, source, now, transport=ResponseTransport(body, source['url']))
    validate_state(state)
    repeat = state == first_state
    return {'accepted': result['status'] == 'healthy' and history and repeat,
            'status': result['status'], 'last_error': result.get('last_error'),
            'last_count': result['last_count'], 'history_preserved': history,
            'repeat_idempotent': repeat, 'new_events': sum(e['event_type']=='NEW' for e in added),
            'added_event_count': len(added),
            'new_with_older_publication_date': sum(e['event_type']=='NEW' and bool(e.get('published_at')) and e['published_at'][:10] < now[:10] for e in added),
            'note': 'NEW means newly observed, not newly published; no archive completeness claim.'}


def protected_manifest():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for name in ('state','site','schemas') for p in (ROOT/name).rglob('*') if p.is_file()}


def acceptance(outcome):
    legacy = outcome['responses'].get('20', {})
    expanded = outcome['responses'].get('100', {})
    return bool(legacy.get('http_status') == 200 and expanded.get('http_status') == 200
                and expanded.get('replay', {}).get('accepted')
                and outcome['protected_files_unchanged']
                and expanded.get('accepted_rows') == expanded.get('unique_urls'))


def main():
    now = datetime.now(timezone.utc).isoformat()
    source = next(s for s in load_registry(ROOT/'config/sources.yml') if s['id']=='dip-listing-01')
    # Fail closed if this stops being the approved endpoint/window.
    expected = 'https://webnew.ipthailand.go.th/wp-json/wp/v2/news?per_page=100&orderby=date&order=desc&_fields=id,date,modified,link,title'
    if source['url'] != expected:
        raise ValueError('DIP endpoint differs from approved bounded contract')
    before = protected_manifest()
    retained = load_state(ROOT/'state/monitor.json')
    outcome = {'purpose':'DIP read-only acceptance; not production recovery', 'checked_at':now,
               'checkout_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
               'state_sha256':before['state/monitor.json'], 'responses':{}}
    transport = Transport(source['allowed_hosts'])
    try:
        for window in (20,100):
            candidate = {**source,'url':source['url'].replace('per_page=100',f'per_page={window}')}
            try:
                status, headers, body, final = transport.fetch(candidate['url'],max_bytes=2_000_000)
                if status != 200:
                    raise ValueError('Full HTTP 200 response required')
                rows, _ = parse_document(candidate,body,final)
                outcome['responses'][str(window)] = {
                    'http_status':status,'response_sha256':hashlib.sha256(body).hexdigest(),
                    'raw_rows':len(json.loads(body)),'accepted_rows':len(rows),
                    'unique_urls':len({r['url'] for r in rows}),
                    'replay':replay(retained,candidate,body,now)}
            except Exception as exc:
                outcome['responses'][str(window)] = {'accepted':False,'error':str(exc)[:250]}
    finally:
        transport.session.close()
    outcome['protected_files_unchanged'] = before == protected_manifest()
    outcome['accepted'] = acceptance(outcome)
    print(json.dumps(outcome,ensure_ascii=False,sort_keys=True))
    return 0 if outcome['accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
