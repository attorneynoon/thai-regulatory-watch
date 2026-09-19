import json
import re
from collections import Counter
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
from pathlib import Path
from urllib.parse import urlsplit
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


def presentation_date(value):
    """A date-only midnight is an RSS presentation convention, not a source time."""
    if not value:
        return None, 'unknown'
    try:
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):
            return datetime.fromisoformat(value).replace(tzinfo=timezone.utc), 'day'
        parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
        if parsed.tzinfo is not None:
            return parsed.astimezone(timezone.utc), 'timestamp'
    except (TypeError, ValueError):
        pass
    return None, 'unknown'


def source_date(event):
    for field in ('published_at','modified_at'):
        dt,precision=presentation_date(event.get(field))
        if dt is not None:
            return dt,field,precision
    return None,'unknown','unknown'


def ordered_events(events,detected=False):
    if detected:
        return sorted(events,key=lambda e:(e['observed_at'],e['event_id']),reverse=True)
    def key(event):
        dt,_,_=source_date(event)
        return (dt is not None,dt or datetime.min.replace(tzinfo=timezone.utc),event['observed_at'],event['event_id'])
    return sorted(events,key=key,reverse=True)


def current_events(items,events,regulator=None):
    """One representative current observation per canonical item, never a new event."""
    event_map={e['event_id']:e for e in events}
    current=[]
    for item in items:
        candidates=[(o,event_map[o['event_id']]) for o in item['observations']]
        if regulator is not None:
            candidates=[(o,e) for o,e in candidates if e['regulator_id']==regulator]
        if candidates:
            _,event=max(candidates,key=lambda pair:(source_date(pair[1])[0] is not None,pair[0]['last_seen_at'],pair[1]['observed_at'],pair[1]['event_id']))
            current.append(event)
    return ordered_events(current)


def source_link(url,label):
    """Only public web links may become active; source strings are never markup."""
    text=escape(str(label))
    try:
        parsed=urlsplit(url or '')
        if parsed.scheme in ('http','https') and parsed.netloc:
            return '<a href="'+escape(url,quote=True)+'">'+text+'</a>'
    except ValueError:
        pass
    return text


def event_description(event,source=None,detected=False):
    source=source or {}
    health='event_type' not in event
    rows=[]
    def field(label,value):
        if isinstance(value,list):
            value='; '.join(str(v) for v in value)
        rows.append('<dt>'+escape(label)+'</dt><dd>'+escape(str(value) if value not in (None,'',[]) else 'Not available')+'</dd>')
    field('Publisher (current configuration)',source.get('publisher_name') or event.get('publisher') or source.get('title'))
    if event.get('publisher'):
        field('Publisher / section recorded at observation',event['publisher'])
    field('Section (configured scope)',source.get('title') or event.get('publisher'))
    field('Source ID',event['source_id'])
    field('Regulator ID',event['regulator_id'])
    if health:
        field('Status',event.get('status'))
        field('Previous status',event.get('previous_status'))
        field('Message',event.get('message'))
    else:
        for key,label in (('document_type','Document type'),('topics','Topics')):
            configured=source.get(key,event.get(key))
            field(label+' (configured)',configured)
            if configured!=event.get(key):
                field(label+' at observation',event.get(key))
        field('Classification basis',event.get('classification_basis'))
        field('Source publication date (normalized)',event.get('published_at'))
        field('Source publication date (raw)',event.get('publication_date_raw'))
        field('Source modification date',event.get('modified_at'))
        field('Document ID',event.get('document_id'))
        if event.get('summary'):
            field('Collector snapshot summary' if event.get('extraction_method')=='json-page' else 'Official excerpt (when available)',event['summary'])
    field('Detected / observed',event['observed_at'])
    if not health:
        field('First observed',event.get('first_observed_at'))
        field('Change',event.get('event_type'))
        field('Changed fields',event.get('changed_fields'))
        field('Review status',event.get('review_status'))
        field('Legal effect',event.get('legal_effect'))
        field('Coverage status',event.get('coverage_status'))
        field('Limitations',event.get('limitations'))
    if detected:
        field('RSS date meaning','Detection time, not publication time')
    else:
        _,basis,precision=source_date(event)
        field('RSS date meaning',basis if basis!='unknown' else 'Unknown; pubDate omitted')
        if precision=='day':
            field('RSS date precision','day; midnight UTC is presentation only, not a known source publication time')
    links=[]
    for key,label in (('official_url','Original page'),('listing_url','Source listing'),('document_url','Document')):
        if event.get(key):
            links.append(source_link(event[key],label)+' — '+escape(event[key]))
    return '<h3>'+escape(event.get('title') or event['source_id'])+'</h3><dl>'+''.join(rows)+'</dl><p>'+'<br>'.join(links)+'</p>'


def rss(name,events,base,limit,source_map=None):
    root=ET.Element('rss',version='2.0')
    channel=ET.SubElement(root,'channel')
    element(channel,'title','Thai Regulatory Watch — '+name)
    element(channel,'link',base+'/')
    detected=name in ('changes','health')
    date_note='Detection order; pubDate is detected/observed time.' if detected else 'Newest source publication first, falling back to source modification. Undated items follow dated items; no pubDate is invented. Date-only pubDate uses midnight UTC for presentation, not a known publication time.'
    element(channel,'description','Public observations for review. '+date_note+' Legal effect is Not assessed. RSS window: '+str(limit)+'. Full history: '+base+'/api/v1/events.json')
    element(channel,'{http://www.w3.org/2005/Atom}link',None,href=base+'/feeds/'+name+'.xml',rel='self',type='application/rss+xml')
    for e in ordered_events(events,detected)[:limit]:
        item=ET.SubElement(channel,'item')
        health='event_type' not in e
        label=e.get('event_type',e.get('status',''))
        element(item,'title','['+label+'] '+e.get('title',e['source_id']))
        element(item,'link',e.get('official_url') or base+'/')
        element(item,'guid',e['event_id'],isPermaLink='false')
        if detected:
            dt,precision=presentation_date(e['observed_at'])
            basis='observed_at'
        else:
            dt,basis,precision=source_date(e)
        if dt is not None:
            element(item,'pubDate',format_datetime(dt,usegmt=True))
        description=event_description(e,(source_map or {}).get(e['source_id']),detected)
        element(item,'description',description)
        for topic in e.get('topics',[]): element(item,'category',topic)
        # All contract fields are available in the extension; arrays are JSON.
        for key,value in sorted(e.items()):
            if value is not None:
                element(item,'{'+NS+'}'+key,json.dumps(value,ensure_ascii=False) if isinstance(value,(list,dict)) else value)
        element(item,'{'+NS+'}rss_date_basis',basis)
        element(item,'{'+NS+'}rss_date_precision',precision)
        element(item,'{'+NS+'}record_url',base+'/api/v1/events.json#'+e['event_id'] if not health else base+'/api/v1/health.json#'+e['event_id'])
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)


def public_sources(state,sources):
    result=[]
    for s in sources:
        health=state['sources'].get(s['id'],{})
        row={k:s.get(k) for k in ['id','regulator_id','title','url','topics','jurisdiction','language','document_type','authority_class','enabled','validation_status','limitations','origin_ids','max_items','max_pages','asset_budget']}
        if s.get('publisher_name'):
            row['publisher_name']=s['publisher_name']
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
    source_map={s['id']:s for s in sources}
    def event_list(es,detected=False):
        if not es:
            return '<p>No post-baseline events recorded. Check source coverage before interpreting this as no change.</p>'
        cards=[]
        for e in es:
            source=source_map.get(e['source_id'],{})
            publisher=source.get('publisher_name') or e.get('publisher') or 'Not available'
            section=source.get('title') or e.get('publisher') or e['source_id']
            dates='Source published: '+str(e.get('published_at') or 'Unknown')
            if e.get('modified_at'):
                dates+=' · Source modified: '+e['modified_at']
            dates+=' · Observed: '+e['observed_at']
            cards.append('<li><span class="tag">'+escape(e.get('event_type','ITEM'))+'</span><h3>'+source_link(e['official_url'],e['title'])+'</h3><small>'+escape(publisher+' · Section: '+section)+'</small><small>'+escape(dates)+'</small><details><summary>Metadata and source evidence</summary>'+event_description(e,source,detected)+'</details></li>')
        return '<ul class="event-list">'+''.join(cards)+'</ul>'
    current=current_events(items,events)
    subscriptions=[]
    for regulator in sorted({s['regulator_id'] for s in sources}):
        sections=sorted((s for s in sources if s['regulator_id']==regulator),key=lambda s:s['id'])
        agency=next((s['publisher_name'] for s in sections if s.get('publisher_name')),regulator.upper())
        subscriptions.append('<li>'+escape(agency)+'<br>'+link('feeds/current/'+regulator+'.xml','Current items — all sections')+' · '+link('feeds/'+regulator+'.xml','Observation events — all sections')+'<ul>'+''.join('<li>'+link('feeds/'+s['id']+'.xml',s['title'])+' <small>'+escape(s['id'])+' — observation events</small></li>' for s in sections)+'</ul></li>')
    subscriptions=''.join(subscriptions)
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Thai Regulatory Watch</title>
<style>:root{font-family:system-ui,sans-serif;color:#14312c;background:#f5f7f4}body{max-width:1200px;margin:auto;padding:32px 20px;overflow-wrap:anywhere}a{color:#075b77}header{border-bottom:3px solid #22846c;padding:12px 0 24px}h1{font-size:clamp(2rem,5vw,3.5rem);margin:.3em 0}h2{margin-top:2em}.eyebrow{letter-spacing:.15em;font-size:.8rem}nav{display:flex;flex-wrap:wrap;gap:18px}section{background:white;border:1px solid #d8e2dd;padding:20px;margin-top:22px;border-radius:8px}.table{overflow-x:auto}table{border-collapse:collapse;width:100%;min-width:850px}td,th{text-align:left;padding:10px;border-bottom:1px solid #e5eae6;vertical-align:top;font-size:.85rem}td:last-child{max-width:350px}li{padding:8px 0}small{display:block;color:#536a65}.tag{font-size:.72rem;background:#e4f1e9;padding:3px 6px}#freshness{padding:12px;background:#fff0ce}#subscriptions{columns:3}#subscriptions>li{break-inside:avoid}input{padding:10px;max-width:90%;width:360px}footer{padding:30px 0;color:#536a65}.event-list{list-style:none;padding:0}.event-list>li{padding:18px 0;border-bottom:1px solid #e5eae6}.event-list h3{margin:.5em 0}details{margin-top:10px}summary{cursor:pointer;color:#075b77}details[open]{padding:12px;background:#f5f7f4}dl{display:grid;grid-template-columns:minmax(140px,1fr) minmax(0,3fr);gap:8px 16px;font-size:.9rem}dt{font-weight:600}dd{margin:0;min-width:0}@media(max-width:600px){body{padding:16px}section{padding:12px}#subscriptions{columns:1}dl{grid-template-columns:1fr;gap:4px}dd{margin-bottom:8px}}</style></head><body>
<header><div class="eyebrow">PUBLIC REGULATORY OBSERVATIONS · THAILAND</div><h1>Thai Regulatory Watch</h1><p>One collection. Feeds for people and structured observations for GRC review.</p><nav><a href="#subscriptions">Regulator / section feeds</a><a href="#source-coverage">Source coverage</a><a href="feeds/changes.xml">Subscribe to changes</a><a href="feeds/all.xml">All events</a><a href="api/v1/events.json">GRC JSON</a><a href="feeds/health.xml">Source health RSS</a><a href="subscriptions.opml">Import subscriptions</a><a href="https://github.com/attorneynoon/thai-regulatory-watch">GitHub</a></nav></header>'''+ (
        '<p id="freshness" data-time="'+escape(latest or '')+'">'+escape('NOT RUN' if not latest else 'Last collection: '+latest)+'</p><p>'+
        escape(' · '.join(f'{k}: {v}' for k,v in sorted(counts.items())))+'</p><p>Candidate collection does not establish complete coverage. Pending scopes are included in the inventory but are not being collected. Publication dates may be unknown. All observations require review; legal effect is Not assessed.</p>'+
        '<section><h2>Recent changes</h2><p>Latest detections first; an update to an old document appears here.</p>'+event_list(ordered_events([e for e in events if e['event_type']!='BASELINE'],detected=True)[:100],detected=True)+'</section>'+
        '<section><h2>Current inventory</h2><p>Showing '+str(min(100,len(current)))+' of '+str(len(current))+' retained items. One representative current observation per canonical item. Newest source publication first, then source modification as fallback; undated items follow dated items. RSS up to 500 by default: '+link('feeds/current/all.xml','Subscribe to current items')+' · Full JSON (all retained items): '+link('api/v1/items.json','items.json')+'</p>'+event_list(current[:100])+'</section>'+
        '<section><h2>Regulator subscriptions</h2><p>Choose all sections for a regulator, or subscribe to an individual configured source section.</p><ul id="subscriptions">'+subscriptions+'</ul></section>'+
        '<section id="source-coverage"><h2>Source coverage</h2><input id="filter" aria-label="Filter sources" placeholder="Filter regulator, source or status"><div class="table"><table><thead><tr><th>Source RSS</th><th>Publisher / configured section</th><th>Run status</th><th>Validation</th><th>Last success</th><th>Limitations</th></tr></thead><tbody id="sources">'+''.join(rows)+'</tbody></table></div></section>'+
        '<footer>RSS keeps up to 500 events per view by default in the order described above. JSON preserves the retained history. A source failure is a coverage limitation, not evidence of no regulatory change.</footer>'
    )+'''<script>const f=document.getElementById('freshness');const t=Date.parse(f.dataset.time);if(t&&Date.now()-t>10800000){f.textContent+=' — STALE: more than 3 hours';f.style.background='#ffd8ce'}document.getElementById('filter').addEventListener('input',e=>{for(const r of document.querySelectorAll('#sources tr'))r.hidden=!r.textContent.toLowerCase().includes(e.target.value.toLowerCase())});</script></body></html>'''


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
    feeds['current/all']=current_events(inventory,events)
    for regulator in sorted({s['regulator_id'] for s in sources}):
        feeds[regulator]=[e for e in events if e['regulator_id']==regulator]
        feeds['current/'+regulator]=current_events(inventory,events,regulator)
    for topic in sorted({t for s in sources for t in s['topics']}):
        feeds['topic-'+topic]=[e for e in events if topic in e['topics']]
    for s in sources: feeds[s['id']]=[e for e in events if e['source_id']==s['id']]
    source_map={s['id']:s for s in sources}
    for name,es in feeds.items(): write_changed(out/'feeds'/f'{name}.xml',rss(name,es,base,limit,source_map))
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
    for path in list((out/'feeds').rglob('*.xml'))+[out/'subscriptions.opml']:
        SafeXML.parse(path)
    for name,schema in SCHEMAS.items():
        Draft202012Validator(schema).validate(json.loads((out/'api/v1'/f'{name}.json').read_text('utf-8')))
