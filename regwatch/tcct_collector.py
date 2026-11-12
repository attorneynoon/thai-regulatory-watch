"""Complete TCCT API listings, applied atomically without resetting old history."""
from copy import deepcopy

from .engine import apply_observations, item_identity, set_health, source_state
from .models import digest
from .registry import allowed_url
from .tcct_api import (ENDPOINT, LISTING_URLS, MIGRATION_VERSION, MAX_LIVE_PAGES,
                       parse_page, qualify_page_set, request_payload)
from .transport import AccessBlocked, Transport


def candidate(source, record, response_hash):
    """A listing link is honest provenance, never an invented article permalink."""
    pdfs = [download for download in record['downloads']
            if download['file_extension'].lower().lstrip('.') == 'pdf'
            or download['file_type'].lower() == 'application/pdf']
    document = allowed_url(pdfs[0]['fileUrl'], source['allowed_hosts']) if pdfs else None
    document_only = document and not (record['body_text'] or record['description_text'] or record['reference_links'])
    metadata = deepcopy(record)
    metadata.update(detail_url=None, link_role='document' if document_only else 'listing',
                    attachment_coverage='primary PDF only; all listed files retained as metadata')
    row = {
        'url': document if document_only else source['url'],
        'title': record['title'], 'tcct_record_id': record['id'],
        'summary': (record['description_text'] or record['body_text'])[:600] or None,
        'published_at': None, 'publication_date_raw': None, 'modified_at': None,
        'document_url': document, 'document_id': record['document_number'] or None,
        'selected_text_sha256': record['content_sha256'], 'source_metadata': metadata,
        'source_response_sha256': response_hash,
        'pinpoint': 'TCCT contents API record ' + record['id'],
    }
    item_identity(source, row)
    return row


def _check_assets(state, source, rows, now, transport):
    """Budgeted primary-PDF checks include retained records absent from a scan."""
    from .collector import age_days
    observations = source_state(state, source['id'])['observations']
    current = {item_identity(source, row): row for row in rows}
    assets = dict(current)
    fields = ('title', 'summary', 'published_at', 'publication_date_raw', 'modified_at',
              'selected_text_sha256', 'document_url', 'document_id', 'tcct_record_id', 'source_metadata')
    for ident, old in observations.items():
        if old.get('document_url') and ident not in assets:
            assets[ident] = {key: deepcopy(old[key]) for key in fields if key in old}
            assets[ident]['url'] = old['canonical_url']
    due = []
    for ident, row in assets.items():
        old = observations.get(ident, {})
        asset = old.get('asset', {}) if old.get('document_url') == row.get('document_url') else {}
        if row.get('document_url') and age_days(asset.get('last_check_at'), now) >= 1:
            due.append((asset.get('last_attempt_at') or '', ident, row, old, asset))
    due.sort(key=lambda value: (value[0], value[1]))
    errors, extras = [], []
    budget = source.get('asset_budget', 2)
    for _, ident, row, old, asset in due[:budget]:
        next_asset = {**asset, 'last_attempt_at': now}
        try:
            validators = {}
            same_document = old.get('document_url') == row['document_url']
            if same_document and age_days(asset.get('last_download_at'), now) < 7 and old.get('attachment_sha256'):
                if asset.get('etag'):
                    validators['If-None-Match'] = asset['etag']
                if asset.get('last_modified'):
                    validators['If-Modified-Since'] = asset['last_modified']
            status, headers, body, final = transport.fetch(row['document_url'], headers=validators,
                max_bytes=source.get('max_asset_bytes', 15_000_000))
            if status == 304:
                if not same_document or not old.get('attachment_sha256'):
                    raise ValueError('304 without prior fingerprint for this document')
                row['attachment_sha256'] = old['attachment_sha256']
            elif status == 200:
                if not body.lstrip().startswith(b'%PDF-'):
                    raise ValueError('Document is not a PDF')
                row['attachment_sha256'] = digest(body)
                next_asset.update(last_download_at=now, etag=headers.get('ETag'),
                                  last_modified=headers.get('Last-Modified'), final_url=final)
            else:
                raise ValueError('Unexpected document HTTP ' + str(status))
            next_asset.update(last_check_at=now, last_error=None)
        except Exception as exc:
            next_asset['last_error'] = str(exc)[:250]
            errors.append(str(exc)[:250])
        row['asset'] = next_asset
        if ident not in current:
            extras.append((ident, row, old))
    return extras, errors, len(due), min(len(due), budget)


def collect_tcct(state, source, now, transport=None):
    ss = source_state(state, source['id'])
    ss['last_attempt_at'] = now
    try:
        key = source['tcct_category_key']
        if source.get('regulator_id') != 'tcct' or source['url'] != LISTING_URLS.get(key):
            raise ValueError('TCCT source must use its exact observed category listing')
        if source.get('tcct_migration_version') != MIGRATION_VERSION:
            raise ValueError('Unsupported TCCT migration version')
        max_pages, max_items = source.get('max_pages', 1), source.get('max_items', 100)
        if type(max_pages) is not int or not 1 <= max_pages <= MAX_LIVE_PAGES:
            raise ValueError('Invalid TCCT page bound')
        transport = transport or Transport(source['allowed_hosts'])
        captures, response_hashes = {}, {}

        def fetch_page(number):
            status, headers, body, final = transport.fetch(ENDPOINT,
                json_body=request_payload(key, number), max_bytes=source.get('max_response_bytes', 4_000_000))
            if status not in (200, 201) or final != ENDPOINT:
                raise ValueError('TCCT listing requires a full response at the exact endpoint')
            if headers.get('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
                raise ValueError('TCCT listing requires application/json')
            parsed = parse_page(body, key, number)
            captures[number] = body
            response_hash = digest(body)
            for record in parsed['records']:
                response_hashes[record['id']] = response_hash
            return parsed

        first = fetch_page(1)
        total, page_count = first['meta']['total'], first['meta']['totalPages']
        if page_count > max_pages or total > max_items:
            raise ValueError('TCCT complete listing exceeds configured page/item bounds; previous inventory retained')
        for number in range(2, page_count + 1):
            fetch_page(number)
        report = qualify_page_set(key, captures)
        if not report['complete']:
            raise ValueError('TCCT incomplete listing: ' + '; '.join(report['errors']))
        if total < source.get('min_items', 1):
            raise ValueError('Suspicious empty/undersized parse; previous inventory retained')
        if ss.get('last_count', 0) >= 10 and total < ss['last_count'] * 0.5:
            raise ValueError('Suspicious count drop greater than 50%; previous inventory retained')
        rows = [candidate(source, record, response_hashes[record['id']]) for record in report['records']]
        extras, errors, due, checked = _check_assets(state, source, rows, now, transport)
        # No page or transition may partially apply rows, events or the marker.
        staged = deepcopy(state)
        apply_observations(staged, source, rows + [row for _, row, _ in extras], now,
                           mark_healthy=False, baseline_new=ss.get('tcct_migration_version') != MIGRATION_VERSION)
        staged_source = source_state(staged, source['id'])
        for ident, _, old in extras:
            staged_source['observations'][ident]['last_seen_at'] = old['last_seen_at']
            staged['items'][ident]['last_seen_at'] = max(
                staged['sources'][sid]['observations'][ident]['last_seen_at']
                for sid in staged['items'][ident]['source_ids'])
        staged_source.update(tcct_migration_version=MIGRATION_VERSION, last_count=total,
            listing_pages_checked=page_count, pagination_truncated=False, item_limit_reached=False,
            listing_complete=True, attachment_backlog=max(0, due - checked), attachment_checks=checked,
            tcct_listing_warnings=report['warnings'], tcct_download_count=report['download_count'])
        set_health(staged, source, 'degraded' if errors else 'healthy', now,
                   'Attachment checks: ' + '; '.join(sorted(set(errors))) if errors else None)
        state.clear()
        state.update(staged)
    except Exception as exc:
        set_health(state, source, 'blocked' if isinstance(exc, AccessBlocked) else 'failed', now, str(exc)[:350])
    state['last_run_at'] = now
    return source_state(state, source['id'])
