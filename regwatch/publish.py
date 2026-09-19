import json
from collections import Counter
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
from pathlib import Path
from xml.etree import ElementTree as ET
from defusedxml import ElementTree as SafeXML
from jsonschema import Draft202012Validator
from .contracts import SCHEMAS
from .storage import write_changed, encode, validate_state

NS='https://attorneynoon.github.io/thai-regulatory-watch/ns/v1'
ET.register_namespace('regwatch',NS)
ET.register_namespace('atom','http://www.w3.org/2005/Atom')


def element(parent,name,value,**attributes):
    node=ET.SubElement(parent,name,attributes)
    if value is not None: node.text=str(value)
    return node


def rss(name,events,base,limit):
    root=ET.Element('rss',version='2.0')
    channel=ET.SubElement(root,'channel')
    element(channel,'title','Thai Regulatory Watch — '+name)
    element(channel,'link',base+'/')
    element(channel,'description','Public observations for review. Dates in pubDate are observation times; legal effect is Not assessed. RSS window: '+str(limit)+'. Full history: '+base+'/api/v1/events.json')
    element(channel,'{http://www.w3.org/2005/Atom}link',None,href=base+'/feeds/'+name+'.xml',rel='self',type='application/rss+xml')
    for e in events[:limit]:
        item=ET.SubElement(channel,'item')
        health='event_type' not in e
        label=e.get('event_type',e.get('status',''))
        element(item,'title','['+label+'] '+e.get('title',e['source_id']))
        element(item,'link',e.get('official_url') or base+'/')
        element(item,'guid',e['event_id'],isPermaLink='false')
        dt=datetime.fromisoformat(e['observed_at'].replace('Z','+00:00')).astimezone(timezone.utc)
        element(item,'pubDate',format_datetime(dt,usegmt=True))
        description=(e.get('message') or '') if health else ' | '.join([e['regulator_id'],', '.join(e['topics']),'Published: '+str(e['published_at'] or 'unknown'),'Legal effect: Not assessed','Review: unreviewed',*e['limitations']])
        element(item,'description',description)
        for topic in e.get('topics',[]): element(item,'category',topic)
        # All contract fields are available in the extension; arrays are JSON.
        for key,value in sorted(e.items()):
            if value is not None:
                element(item,'{'+NS+'}'+key,json.dumps(value,ensure_ascii=False) if isinstance(value,(list,dict)) else value)
        element(item,'{'+NS+'}record_url',base+'/api/v1/events.json#'+e['event_id'] if not health else base+'/api/v1/health.json#'+e['event_id'])
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)


def public_sources(state,sources):
    result=[]
    for s in sources:
        health=state['sources'].get(s['id'],{})
        row={k:s.get(k) for k in ['id','regulator_id','title','url','topics','jurisdiction','language','document_type','authority_class','enabled','validation_status','limitations','origin_ids','max_items','max_pages','asset_budget']}
        row.update({k:health.get(k) for k in ['last_attempt_at','last_success_at','last_error','last_count','attachment_backlog','attachment_checks','listing_pages_checked','pagination_truncated','item_limit_reached']})
        row['status']=health.get('status','not-run' if s.get('enabled',True) else 'pending')
        result.append(row)
    return result


def dashboard(state,sources,events,items,base):
    counts=Counter(s['status'] for s in sources)
    latest=state['last_run_at']
    def link(url,text): return '<a href="'+escape(url or '#',quote=True)+'">'+escape(str(text))+'</a>'
    rows=[]
    for s in sources:
        rows.append('<tr><td>'+link('feeds/'+s['id']+'.xml',s['id'])+'</td><td>'+escape(s['title'])+'</td><td>'+escape(s['status'])+'</td><td>'+escape(s['validation_status'])+'</td><td>'+escape(s.get('last_success_at') or 'Never')+'</td><td>'+escape(s.get('last_error') or '; '.join(s['limitations']))+'</td></tr>')
    def event_list(es):
        if not es:
            return '<p>No post-baseline events recorded. Check source coverage before interpreting this as no change.</p>'
        return '<ul>'+''.join('<li><span class="tag">'+escape(e.get('event_type','ITEM'))+'</span> '+link(e['official_url'],e['title'])+' <small>'+escape(e['regulator_id']+' · '+e['observed_at'])+'</small></li>' for e in es)+'</ul>'
    current=[]
    event_map={e['event_id']:e for e in events}
    for item in items:
        observations=item['observations']
        if observations:
            current.append(event_map[max(observations,key=lambda o:o['last_seen_at'])['event_id']])
    subscriptions=''.join('<li>'+link('feeds/'+r+'.xml',r.upper())+'</li>' for r in sorted({s['regulator_id'] for s in sources}))
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Thai Regulatory Watch</title>
<style>:root{font-family:system-ui,sans-serif;color:#14312c;background:#f5f7f4}body{max-width:1200px;margin:auto;padding:32px 20px}a{color:#075b77}header{border-bottom:3px solid #22846c;padding:12px 0 24px}h1{font-size:clamp(2rem,5vw,3.5rem);margin:.3em 0}h2{margin-top:2em}.eyebrow{letter-spacing:.15em;font-size:.8rem}nav{display:flex;flex-wrap:wrap;gap:18px}section{background:white;border:1px solid #d8e2dd;padding:20px;margin-top:22px;border-radius:8px}.table{overflow-x:auto}table{border-collapse:collapse;width:100%;min-width:850px}td,th{text-align:left;padding:10px;border-bottom:1px solid #e5eae6;vertical-align:top;font-size:.85rem}td:last-child{max-width:350px}li{padding:8px 0}small{display:block;color:#536a65}.tag{font-size:.72rem;background:#e4f1e9;padding:3px 6px}#freshness{padding:12px;background:#fff0ce}#subscriptions{columns:3}input{padding:10px;max-width:90%;width:360px}footer{padding:30px 0;color:#536a65}@media(max-width:600px){body{padding:16px}section{padding:12px}#subscriptions{columns:2}}</style></head><body>
<header><div class="eyebrow">PUBLIC REGULATORY OBSERVATIONS · THAILAND</div><h1>Thai Regulatory Watch</h1><p>One collection. Feeds for people and structured observations for GRC review.</p><nav><a href="feeds/changes.xml">Subscribe to changes</a><a href="feeds/all.xml">All events</a><a href="api/v1/events.json">GRC JSON</a><a href="feeds/health.xml">Source health RSS</a><a href="subscriptions.opml">Import subscriptions</a><a href="https://github.com/attorneynoon/thai-regulatory-watch">GitHub</a></nav></header>'''+ '<p id="freshness" data-time="'+escape(latest or '')+'">'+escape('NOT RUN' if not latest else 'Last collection: '+latest)+'</p><p>'+escape(' · '.join(f'{k}: {v}' for k,v in sorted(counts.items())))+'</p><p>Candidate collection does not establish complete coverage. Pending scopes are included in the inventory but are not being collected. Publication dates may be unknown. All observations require review; legal effect is Not assessed.</p>'+ '<section><h2>Recent changes</h2>'+event_list([e for e in events if e['event_type']!='BASELINE'][:100])+'</section><section><h2>Current inventory</h2><p>'+str(len(items))+' retained items. Full metadata: '+link('api/v1/items.json','items.json')+'</p>'+event_list(current)+'</section><section><h2>Regulator subscriptions</h2><ul id="subscriptions">'+subscriptions+'</ul></section><section><h2>Source coverage</h2><input id="filter" aria-label="Filter sources" placeholder="Filter regulator, source or status"><div class="table"><table><thead><tr><th>Source RSS</th><th>Publisher</th><th>Run status</th><th>Validation</th><th>Last success</th><th>Limitations</th></tr></thead><tbody id="sources">'+''.join(rows)+'</tbody></table></div></section><footer>RSS keeps the latest 500 events per view by default. JSON preserves the retained history. A source failure is a coverage limitation, not evidence of no regulatory change.</footer>'+'''<script>const f=document.getElementById('freshness');const t=Date.parse(f.dataset.time);if(t&&Date.now()-t>10800000){f.textContent+=' — STALE: more than 3 hours';f.style.background='#ffd8ce'}document.getElementById('filter').addEventListener('input',e=>{for(const r of document.querySelectorAll('#sources tr'))r.hidden=!r.textContent.toLowerCase().includes(e.target.value.toLowerCase())});</script></body></html>'''


def build_site(state,sources,out,base,limit=500):
    validate_state(state)
    out=Path(out)
    base=base.rstrip('/')
    events=sorted(state['events'],key=lambda e:(e['observed_at'],e['event_id']),reverse=True)
    health=sorted(state['health_events'],key=lambda e:(e['observed_at'],e['event_id']),reverse=True)
    inventory=[]
    for item in sorted(state['items'].values(),key=lambda x:x['item_id']):
        inventory.append({**item,'observations':[state['sources'][sid]['observations'][item['item_id']] for sid in item['source_ids']]})
    public=public_sources(state,sources)
    values={'events':events,'items':inventory,'sources':public,'health':health}
    for name,records in values.items():
        payload={'schema_version':'1.0','generated_at':state['last_run_at'],'records':records}
        Draft202012Validator(SCHEMAS[name]).validate(payload)
        write_changed(out/'api/v1'/f'{name}.json',encode(payload))
        write_changed(out/'api/v1'/f'{name}.schema.json',encode(SCHEMAS[name]))
    feeds={'all':events,'changes':[e for e in events if e['event_type']!='BASELINE'],'baseline':[e for e in events if e['event_type']=='BASELINE'],'health':health}
    for regulator in sorted({s['regulator_id'] for s in sources}):
        feeds[regulator]=[e for e in events if e['regulator_id']==regulator]
    for topic in sorted({t for s in sources for t in s['topics']}):
        feeds['topic-'+topic]=[e for e in events if topic in e['topics']]
    for s in sources: feeds[s['id']]=[e for e in events if e['source_id']==s['id']]
    for name,es in feeds.items(): write_changed(out/'feeds'/f'{name}.xml',rss(name,es,base,limit))
    root=ET.Element('opml',version='2.0')
    element(ET.SubElement(root,'head'),'title','Thai Regulatory Watch')
    body=ET.SubElement(root,'body')
    for r in sorted({s['regulator_id'] for s in sources}): ET.SubElement(body,'outline',text=r,title=r,type='rss',xmlUrl=base+'/feeds/'+r+'.xml')
    write_changed(out/'subscriptions.opml',ET.tostring(root,encoding='utf-8',xml_declaration=True))
    write_changed(out/'index.html',dashboard(state,public,events,inventory,base))
    write_changed(out/'.nojekyll','')
    return {'items':len(inventory),'events':len(events),'feeds':len(feeds),'sources':len(sources)}


def check_site(out):
    out=Path(out)
    for path in list((out/'feeds').glob('*.xml'))+[out/'subscriptions.opml']:
        SafeXML.parse(path)
    for name,schema in SCHEMAS.items():
        Draft202012Validator(schema).validate(json.loads((out/'api/v1'/f'{name}.json').read_text('utf-8')))
