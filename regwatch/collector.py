from datetime import datetime, timezone, timedelta
from pathlib import Path
from .adapters import parse_document
from .models import canonical_url, digest
from .engine import apply_observations, set_health, source_state
from .transport import Transport, AccessBlocked


def age_days(stamp, now):
    if not stamp:
        return float('inf')
    return (datetime.fromisoformat(now.replace('Z','+00:00')) - datetime.fromisoformat(stamp.replace('Z','+00:00'))).total_seconds() / 86400


def collect_source(state, source, now, transport=None, root=None):
    ss = source_state(state, source['id'])
    ss['last_attempt_at'] = now
    queue, visited, rows, seen = [source['url'],*source.get('start_urls',[])], set(), [], set()
    try:
        certificates={host:str(Path(root or Path.cwd())/path) for host,path in source.get('tls_intermediates',{}).items()}
        transport = transport or Transport(source['allowed_hosts'],tls_intermediates=certificates)
        while queue and len(visited) < source.get('max_pages', 1):
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)
            status, headers, body, final = transport.fetch(url,max_bytes=source.get('max_response_bytes',4_000_000))
            if source.get('public_form'):
                from .publicform import validate_public_form
                form=validate_public_form(source,body,final)
                status,headers,body,final=transport.fetch(source['public_form_url'],max_bytes=source.get('max_response_bytes',4_000_000),form=form)
            if status != 200:
                raise ValueError('Listing requires a full response')
            candidates, more = parse_document(source, body, final)
            response_hash=digest(body)
            for candidate in candidates:
                if candidate['url'] not in seen:
                    candidate['source_response_sha256'] = response_hash
                    rows.append(candidate)
                    seen.add(candidate['url'])
            queue.extend(p for p in more if p not in visited)
        item_limit_reached = len(rows) >= source.get('max_items', 100)
        rows = rows[:source.get('max_items', 100)]
        if len(rows) < source.get('min_items', 1):
            raise ValueError('Suspicious empty/undersized parse; previous inventory retained')
        if ss.get('last_count', 0) >= 10 and len(rows) < ss['last_count'] * 0.5:
            raise ValueError('Suspicious count drop greater than 50%; previous inventory retained')
        # Check oldest attempted documents first, including retained items absent
        # from today's bounded listing. Date/metadata remain source-observed.
        old_by_url = {o['canonical_url']:o for o in ss['observations'].values()}
        current_by_url = {r['url']:r for r in rows}
        assets = dict(current_by_url)
        for url,o in old_by_url.items():
            if o.get('document_url') and url not in assets:
                assets[url] = {k:o.get(k) for k in ('title','summary','published_at','publication_date_raw','modified_at','selected_text_sha256','document_url','document_id')}
                assets[url]['url'] = url
        due = []
        for url,r in assets.items():
            old = old_by_url.get(url,{})
            asset = old.get('asset',{})
            if r.get('document_url') and age_days(asset.get('last_check_at'), now) >= 1:
                due.append((asset.get('last_attempt_at') or '', url, r, old, asset))
        due.sort(key=lambda t:(t[0],t[1]))
        errors=[]
        budget=source.get('asset_budget',2)
        for _,url,r,old,asset in due[:budget]:
            next_asset={**asset,'last_attempt_at':now}
            try:
                validators={}
                force=age_days(asset.get('last_download_at'),now) >= 7
                if not force and old.get('attachment_sha256'):
                    if asset.get('etag'): validators['If-None-Match']=asset['etag']
                    if asset.get('last_modified'): validators['If-Modified-Since']=asset['last_modified']
                status,headers,body,final=transport.fetch(r['document_url'],headers=validators,max_bytes=15_000_000)
                if status == 304:
                    if not old.get('attachment_sha256'): raise ValueError('304 without prior fingerprint')
                    r['attachment_sha256']=old['attachment_sha256']
                else:
                    if not body.lstrip().startswith(b'%PDF-'):
                        raise ValueError('Document is not a PDF')
                    r['attachment_sha256']=digest(body)
                    next_asset.update(last_download_at=now,etag=headers.get('ETag'),last_modified=headers.get('Last-Modified'),final_url=final)
                next_asset.update(last_check_at=now,last_error=None)
            except Exception as exc:
                next_asset['last_error']=str(exc)[:250]
                errors.append(str(exc)[:250])
            r['asset']=next_asset
        # Don't let attachment-only rechecks distort observed listing counts.
        listing_count=len(rows)
        extras=[r for _,url,r,_,_ in due[:budget] if url not in current_by_url]
        apply_observations(state,source,rows+extras,now,mark_healthy=False)
        for r in extras:
            old=old_by_url[r['url']]
            ss['observations'][old['item_id']]['last_seen_at']=old['last_seen_at']
            state['items'][old['item_id']]['last_seen_at']=max(state['sources'][sid]['observations'][old['item_id']]['last_seen_at'] for sid in state['items'][old['item_id']]['source_ids'])
        ss.update(last_count=listing_count,listing_pages_checked=len(visited),pagination_truncated=bool(queue),item_limit_reached=item_limit_reached,attachment_backlog=max(0,len(due)-budget),attachment_checks=min(len(due),budget))
        if errors:
            set_health(state,source,'degraded',now,'Attachment checks: '+'; '.join(sorted(set(errors))))
        else:
            set_health(state,source,'healthy',now)
    except Exception as exc:
        set_health(state,source,'blocked' if isinstance(exc,AccessBlocked) else 'failed',now,str(exc)[:350])
    state['last_run_at']=now
    return ss
