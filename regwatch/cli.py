import argparse
import json
import os
import re
import tempfile
from datetime import datetime,timezone,timedelta
from pathlib import Path
from .registry import load_registry
from .practices import load_practices
from .storage import load_state,writer_lock,write_changed,encode
from .models import utcnow,canonical_url
from .collector import collect_source
from .browser_transport import RenderedTransport
from .publish import build_site,check_site
from .contracts import SCHEMAS


_AMLO_FORM_ERROR = 'Public navigation form fields changed'
_AMLO_FORM_DIAGNOSTIC = re.compile(
    r'Public navigation form fields changed '
    r'\(stage=pre_post; observed_field_count=([1-9][0-9]{0,8}|0); '
    r'csrf_token_present=(True|False); intro_page_matches=(True|False); '
    r'response_sha256=[a-f0-9]{64}\)'
)
_UTC_TIMESTAMP = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?Z')


def _safe_health_metadata(source_id, health):
    """Never copy arbitrary error history into GitHub Actions stdout."""
    error=health.get('last_error')
    diagnostic=None
    if error:
        diagnostic={'code':'error_details_redacted'}
        if source_id=='amlo-listing-01' and isinstance(error,str):
            match=_AMLO_FORM_DIAGNOSTIC.fullmatch(error)
            if match or error==_AMLO_FORM_ERROR:
                diagnostic={'code':'amlo_public_form_fields_changed','stage':'pre_post'}
                if match:
                    count, token_present, intro_matches=match.groups()
                    diagnostic.update(observed_field_count=int(count),
                                      csrf_token_present=token_present=='True',
                                      intro_page_matches=intro_matches=='True')
    last_count=health.get('last_count')
    timestamps={key:health.get(key) for key in ('last_attempt_at','last_success_at')}
    return {'diagnostic':diagnostic,
            'last_count':last_count if type(last_count) is int and last_count>=0 else None,
            **{key:value if isinstance(value,str) and _UTC_TIMESTAMP.fullmatch(value) else None
               for key,value in timestamps.items()}}


def main():
    parser=argparse.ArgumentParser(description='Public regulatory observations and review-only GRC feeds')
    parser.add_argument('command',choices=['validate','collect','build','health','check'])
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--source',action='append')
    parser.add_argument('--allow-source-errors',action='store_true')
    parser.add_argument('--strict-coverage',action='store_true')
    parser.add_argument('--base-url',default=os.environ.get('FEED_BASE_URL','https://attorneynoon.github.io/thai-regulatory-watch'))
    args=parser.parse_args()
    root=args.root.resolve()
    sources=load_registry(root/'config/sources.yml')
    practices=load_practices(root/'config/practices.yml',sources)
    if args.source and set(args.source)-{s['id'] for s in sources}:
        parser.error('Unknown source id')
    state=load_state(root/'state/monitor.json')
    if args.command=='validate':
        print(encode({'sources':len(sources),'regulators':len({s['regulator_id'] for s in sources}),'practices':len(practices),'enabled':sum(s['enabled'] for s in sources),'pending':sum(not s['enabled'] for s in sources)}))
        return 0
    if args.command=='check':
        check_site(root/'site'); print('XML and JSON contracts passed'); return 0
    if args.command=='health':
        problems=[]
        for s in sources:
            health=state['sources'].get(s['id'],{})
            status=health.get('status','not-run')
            success=health.get('last_success_at')
            if status=='healthy' and success and datetime.now(timezone.utc)-datetime.fromisoformat(success.replace('Z','+00:00'))>timedelta(hours=3):
                status='stale'
            if s['enabled'] and status!='healthy' or args.strict_coverage and s['validation_status']!='verified':
                problems.append({'source':s['id'],'status':status,'validation':s['validation_status'],
                                 **_safe_health_metadata(s['id'],health)})
        print(encode(problems)); return 1 if problems else 0
    canonical_url(args.base_url)
    with writer_lock(root):
        if args.command=='collect':
            now=utcnow()
            playwright=browser=None
            try:
                for s in sources:
                    if s['enabled'] and (not args.source or s['id'] in args.source):
                        transport=None
                        print('Collecting '+s['id'],flush=True)
                        try:
                            if s.get('render')=='browser':
                                if browser is None:
                                    from playwright.sync_api import sync_playwright
                                    playwright=sync_playwright().start()
                                    browser=playwright.chromium.launch(headless=True)
                                transport=RenderedTransport(s,browser)
                            result=collect_source(state,s,now,transport=transport,root=root)
                            count=str(result.get('last_count',0))
                            inventory=count+' items'
                            if result['status'] in {'failed','blocked'}: inventory='retained_last_count='+count
                            elif result['status']!='healthy': inventory='last_count='+count
                            print(result['status']+': '+inventory+'; '+str(result.get('last_error') or ''),flush=True)
                        finally:
                            if transport is not None: transport.close()
            finally:
                if browser is not None: browser.close()
                if playwright is not None: playwright.stop()
        # All artifacts validate before promotion. Git commits are the atomic
        # externally visible generation boundary; no remote push occurs here.
        with tempfile.TemporaryDirectory(prefix='.build-',dir=root) as temp:
            counts=build_site(state,sources,Path(temp),args.base_url,practices=practices)
            check_site(Path(temp))
            for path in Path(temp).rglob('*'):
                if path.is_file(): write_changed(root/'site'/path.relative_to(temp),path.read_bytes())
            write_changed(root/'state/monitor.json',encode(state))
        for name,schema in SCHEMAS.items(): write_changed(root/'schemas'/f'{name}-v1.schema.json',encode(schema))
        print(encode(counts))
    if args.command=='collect' and not args.allow_source_errors:
        return int(any(state['sources'].get(s['id'],{}).get('status')!='healthy' for s in sources if s['enabled'] and (not args.source or s['id'] in args.source)))
    return 0
