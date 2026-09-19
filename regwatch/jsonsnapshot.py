"""Explicitly partial snapshots of selected public JSON fields.

One endpoint remains one observation. This adapter does not invent reader URLs,
publication dates or individual-publication coverage for API records.
"""
import json
from .models import clean_text, digest
from .registry import allowed_url


def _field(value, path):
    for part in path.split('.'):
        if not isinstance(value, dict) or part not in value:
            raise ValueError('JSON snapshot field missing: ' + path)
        value = value[part]
    return value


def parse_json_snapshot(source, body, final_url):
    fields = source.get('json_snapshot_fields')
    if not isinstance(fields, list) or not fields or any(not isinstance(f, str) or not f for f in fields):
        raise ValueError('JSON snapshot requires explicit public field whitelist')
    document = json.loads(body)
    rows = _field(document, source['json_rows']) if source.get('json_rows') else document
    if not isinstance(rows, list):
        raise ValueError('JSON snapshot rows must be an array')
    selected = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('JSON snapshot row must be an object')
        if any(_field(row, key) != value for key, value in source.get('json_filter', {}).items()):
            continue
        projection = {field: _field(row, field) for field in fields}
        if any(isinstance(value, (dict, list)) for value in projection.values()):
            raise ValueError('JSON snapshot whitelist must select scalar public fields')
        selected.append(projection)
    if not selected:
        raise ValueError('Suspicious empty JSON snapshot; previous observation retained')
    selected.sort(key=lambda row: json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')))
    return [{
        'url': allowed_url(final_url, source['allowed_hosts']),
        'title': clean_text(source['title']),
        'published_at': None,
        'publication_date_raw': None,
        'document_url': None,
        'summary': f'{len(selected)} selected public records; aggregate content snapshot, not individual publications.',
        'selected_text_sha256': digest(selected),
        'pinpoint': 'JSON ' + source.get('json_rows', '$') + '; fields: ' + ', '.join(fields),
    }], []
