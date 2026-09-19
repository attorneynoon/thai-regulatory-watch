import argparse
import json
import os
import tempfile
from datetime import datetime,timezone,timedelta
from pathlib import Path
from .registry import load_registry
from .storage import load_state,writer_lock,write_changed,encode
from .models import utcnow,canonical_url
from .collector import collect_source
from .publish import build_site,check_site
from .contracts import SCHEMAS


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
    if args.source and set(args.source)-{s['id'] for s in sources}:
        parser.error('Unknown source id')
    state=load_state(root/'state/monitor.json')
    if args.command=='validate':
        print(encode({'sources':len(sources),'regulators':len({s['regulator_id'] for s in sources}),'enabled':sum(s['enabled'] for s in sources),'pending':sum(not s['enabled'] for s in sources)}))
        return 0
    if args.command=='check':
        check_site(root/'site'); print('XML and JSON contracts passed'); return 0
    if args.command=='health':
        problems=[]
        for s in sources:
            status=state['sources'].get(s['id'],{}).get('status','not-run')
            success=state['sources'].get(s['id'],{}).get('last_success_at')
            if status=='healthy' and success and datetime.now(timezone.utc)-datetime.fromisoformat(success.replace('Z','+00:00'))>timedelta(hours=3):
                status='stale'
            if s['enabled'] and status!='healthy' or args.strict_coverage and s['validation_status']!='verified': problems.append({'source':s['id'],'status':status,'validation':s['validation_status']})
        print(encode(problems)); return 1 if problems else 0
    canonical_url(args.base_url)
    with writer_lock(root):
        if args.command=='collect':
            now=utcnow()
            for s in sources:
                if s['enabled'] and (not args.source or s['id'] in args.source):
                    print('Collecting '+s['id'],flush=True)
                    result=collect_source(state,s,now)
                    print(result['status']+': '+str(result.get('last_count',0))+' items; '+str(result.get('last_error') or ''),flush=True)
        # All artifacts validate before promotion. Git commits are the atomic
        # externally visible generation boundary; no remote push occurs here.
        with tempfile.TemporaryDirectory(prefix='.build-',dir=root) as temp:
            counts=build_site(state,sources,Path(temp),args.base_url)
            check_site(Path(temp))
            for path in Path(temp).rglob('*'):
                if path.is_file(): write_changed(root/'site'/path.relative_to(temp),path.read_bytes())
            write_changed(root/'state/monitor.json',encode(state))
        for name,schema in SCHEMAS.items(): write_changed(root/'schemas'/f'{name}-v1.schema.json',encode(schema))
        print(encode(counts))
    if args.command=='collect' and not args.allow_source_errors:
        return int(any(state['sources'].get(s['id'],{}).get('status')!='healthy' for s in sources if s['enabled'] and (not args.source or s['id'] in args.source)))
    return 0
