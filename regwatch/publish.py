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

COMMON_CSS='''
:root{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:#14312c;background:#f5f7f4;line-height:1.5}
*{box-sizing:border-box}body{max-width:1200px;margin:auto;padding:32px 20px;overflow-wrap:anywhere}
a{color:#075b77;text-underline-offset:.16em}a:hover{text-decoration-thickness:2px}a:focus-visible,summary:focus-visible,input:focus-visible{outline:3px solid #c26a00;outline-offset:3px;border-radius:3px}
header{border-bottom:3px solid #22846c;padding:12px 0 24px}h1{font-size:clamp(2rem,5vw,3.5rem);line-height:1.05;margin:.3em 0;max-width:18ch}h2{margin-top:2em;line-height:1.15}h3{line-height:1.3}.eyebrow{letter-spacing:.15em;font-size:.8rem}.lede{font-size:clamp(1.05rem,2vw,1.3rem);max-width:72ch}
nav{display:flex;flex-wrap:wrap;gap:4px 18px}nav a{display:inline-block;padding:10px 0;min-height:44px}.skip-link{position:absolute;left:-9999px;top:8px;background:#fff;color:#14312c;padding:10px;z-index:10}.skip-link:focus{left:8px}section{background:white;border:1px solid #d8e2dd;padding:20px;margin-top:22px;border-radius:8px}.table{overflow-x:auto}table{border-collapse:collapse;width:100%;min-width:850px}td,th{text-align:left;padding:10px;border-bottom:1px solid #e5eae6;vertical-align:top;font-size:.85rem}td:last-child{max-width:350px}
li{padding:8px 0}small{display:block;color:#536a65}.tag{font-size:.72rem;background:#e4f1e9;padding:3px 6px;border-radius:3px}.status-line{padding:12px;background:#fff0ce;border-left:4px solid #c26a00}.status-line.complete{background:#e4f1e9;border-color:#22846c}.scope-list,.practice-list,.source-list{list-style:none;padding:0}.scope-list{display:flex;flex-wrap:wrap;gap:8px}.scope-list li{background:#edf3f0;border:1px solid #d8e2dd;border-radius:999px;padding:5px 10px}.practice-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:0 28px}.practice-list li{border-top:1px solid #e5eae6;padding:18px 0}.practice-list strong{display:block;font-size:1.05rem}.practice-list small{margin-top:4px}.source-list>li{border-bottom:1px solid #e5eae6;padding:14px 0}.source-list strong,.source-list small{display:block}
#freshness{padding:12px;background:#fff0ce}#subscriptions{columns:3}#subscriptions>li{break-inside:avoid}input{padding:10px;max-width:90%;width:360px}footer{padding:30px 0;color:#536a65}.event-list{list-style:none;padding:0}.event-list>li{padding:18px 0;border-bottom:1px solid #e5eae6}.event-list h3{margin:.5em 0}details{margin-top:10px}summary{cursor:pointer;color:#075b77;min-height:32px}details[open]{padding:12px;background:#f5f7f4}dl{display:grid;grid-template-columns:minmax(140px,1fr) minmax(0,3fr);gap:8px 16px;font-size:.9rem}dt{font-weight:600}dd{margin:0;min-width:0}
@media(max-width:600px){body{padding:16px}section{padding:14px}#subscriptions{columns:1}dl{grid-template-columns:1fr;gap:4px}dd{margin-bottom:8px}.practice-list{grid-template-columns:1fr}}
'''
FAVICON='''<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='6' fill='%2322846c'/><path d='M8 16h16M16 8v16' stroke='white' stroke-width='3'/></svg>">'''


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


def current_events(items,events,regulator=None,source_ids=None):
    """One representative current observation per canonical item, never a new event."""
    event_map={e['event_id']:e for e in events}
    current=[]
    for item in items:
        candidates=[(o,event_map[o['event_id']]) for o in item['observations']]
        if source_ids is not None:
            candidates=[(o,e) for o,e in candidates if e['source_id'] in source_ids]
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
    field('Feed selection (current configuration)',source.get('feed_priority','radar'))
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


def event_list(events,source_map,detected=False):
    if not events:
        return '<p>No post-baseline events recorded. Check source coverage before interpreting this as no change.</p>' if detected else '<p>No retained items are available for this scope. Check source coverage before interpreting this as no publication.</p>'
    cards=[]
    for event in events:
        source=source_map.get(event['source_id'],{})
        publisher=source.get('publisher_name') or event.get('publisher') or 'Not available'
        section=source.get('title') or event.get('publisher') or event['source_id']
        dates='Source published: '+str(event.get('published_at') or 'Unknown')
        if event.get('modified_at'):
            dates+=' · Source modified: '+event['modified_at']
        dates+=' · Observed: '+event['observed_at']
        cards.append('<li><span class="tag">'+escape(event.get('event_type','ITEM'))+'</span><h3>'+source_link(event['official_url'],event['title'])+'</h3><small>'+escape(publisher+' · Section: '+section)+'</small><small>'+escape(dates)+'</small><details><summary>Metadata and source evidence</summary>'+event_description(event,source,detected)+'</details></li>')
    return '<ul class="event-list">'+''.join(cards)+'</ul>'


def rss(name,events,base,limit,source_map=None,coverage_source_ids=None):
    root=ET.Element('rss',version='2.0')
    channel=ET.SubElement(root,'channel')
    element(channel,'title','Thai Regulatory Watch — '+name)
    element(channel,'link',base+'/')
    detected=name in ('changes','changes-all','health') or name.startswith('practice-') and name.endswith('-changes')
    date_note='Detection order; pubDate is detected/observed time.' if detected else 'Newest source publication first, falling back to source modification. Undated items follow dated items; no pubDate is invented. Date-only pubDate uses midnight UTC for presentation, not a known publication time.'
    coverage_note=''
    if name in ('changes','regulatory') or coverage_source_ids is not None:
        if coverage_source_ids is None:
            selected=[s for s in (source_map or {}).values() if s.get('enabled') and s.get('feed_priority')=='regulatory']
        else:
            selected=[s for s in (source_map or {}).values() if s['id'] in coverage_source_ids]
        unavailable=[s['id'] for s in selected if s.get('status')!='healthy']
        coverage_note=(' Practice source coverage: ' if coverage_source_ids is not None else ' Regulatory source coverage: ')+str(len(selected)-len(unavailable))+'/'+str(len(selected))+' healthy. '
        if unavailable:coverage_note+='Incomplete coverage: '+', '.join(unavailable)+'. No new feed entries is not proof of no regulatory updates. '
    element(channel,'description','Public observations for review. '+date_note+coverage_note+' Legal effect is Not assessed. RSS window: '+str(limit)+'. Full history: '+base+'/api/v1/events.json')
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
        row['feed_priority']=s.get('feed_priority','radar')
        result.append(row)
    return result


def practice_page(practice,sources,events,items,base,latest):
    selected=[source for source in sources if source['regulator_id'] in practice['regulator_ids']]
    source_ids={source['id'] for source in selected}
    source_map={source['id']:source for source in sources}
    current=current_events(items,events,source_ids=source_ids)
    changes=ordered_events([event for event in events if event['event_type']!='BASELINE' and event['source_id'] in source_ids],detected=True)
    unavailable=[source for source in selected if source.get('status')!='healthy']
    status_class='status-line' if unavailable else 'status-line complete'
    if unavailable:
        coverage='<strong>Incomplete coverage:</strong> '+str(len(selected)-len(unavailable))+'/'+str(len(selected))+' configured source sections healthy. Unavailable or pending: '+', '.join(source['id'] for source in unavailable)+'. A missing item is not evidence that no update exists.'
    else:
        coverage='<strong>Coverage status:</strong> all '+str(len(selected))+' configured source sections are healthy for the latest collection.'
    scope=''.join('<li>'+escape(regulator)+'</li>' for regulator in practice['regulator_ids'])
    source_rows=[]
    for source in selected:
        problem=source.get('last_error') or '; '.join(source.get('limitations',[])) or 'No current limitation recorded.'
        source_rows.append('<li><details><summary><strong>'+escape(source.get('publisher_name') or source['title'])+'</strong> — '+escape(source['title'])+' <span class="tag">'+escape(source.get('status','not-run'))+'</span></summary><small>'+escape(source['id']+' · Last success: '+str(source.get('last_success_at') or 'Never'))+'</small><p>'+escape(problem)+'</p><a href="../../feeds/'+escape(source['id'],quote=True)+'.xml">Section RSS</a></details></li>')
    title=escape(practice['title'])
    summary=escape(practice['summary'])
    slug=practice['slug']
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'''+FAVICON+'''<title>'''+title+''' — Thai Regulatory Watch</title><style>'''+COMMON_CSS+'''</style></head><body><a class="skip-link" href="#main">Skip to content</a>
<header><div class="eyebrow">THAI REGULATORY WATCH · PRACTICE FOCUS</div><h1>'''+title+'''</h1><p class="lede">'''+summary+'''</p><nav><a href="../../">All practices</a><a href="../../feeds/practice-'''+slug+'''.xml">Current-items RSS</a><a href="../../feeds/practice-'''+slug+'''-changes.xml">Changes RSS</a><a href="#coverage">Source coverage</a><a href="../../api/v1/items.json">GRC JSON</a></nav></header>
<main id="main">
<p id="freshness" data-time="'''+escape(latest or '')+'''">'''+escape('NOT RUN' if not latest else 'Last collection: '+latest)+'''</p>
<p class="'''+status_class+'''">'''+coverage+''' Legal effect is Not assessed; every item requires review.</p>
<section aria-labelledby="scope-title"><h2 id="scope-title">Included regulator groups</h2><p>Regulators may appear in more than one practice view. This is a reading and subscription scope, not a legal classification.</p><ul class="scope-list">'''+scope+'''</ul></section>
<section aria-labelledby="changes-title"><h2 id="changes-title">Recent changes</h2><p>Showing '''+str(min(15,len(changes)))+''' of '''+str(len(changes))+''' retained post-baseline detections, newest detection first. Use Changes RSS for the full feed window.</p>'''+event_list(changes[:15],source_map,detected=True)+'''</section>
<section aria-labelledby="inventory-title"><h2 id="inventory-title">Current practice inventory</h2><p>Showing '''+str(min(30,len(current)))+''' of '''+str(len(current))+''' current items. Newest source publication first; undated items follow dated items. Use Current-items RSS for the full feed window.</p>'''+event_list(current[:30],source_map)+'''</section>
<section id="coverage" aria-labelledby="coverage-title"><h2 id="coverage-title">Source coverage</h2><p>Transport and parser health is reported separately from legal significance or completeness.</p><ul class="source-list">'''+''.join(source_rows)+'''</ul></section></main>
<footer>Generated from the same retained observations as the regulator feeds. Public-source observations are review-only; legal effect and applicability are Not assessed.</footer>
<script>const f=document.getElementById('freshness');const t=Date.parse(f.dataset.time);if(t&&Date.now()-t>10800000){f.textContent+=' — STALE: more than 3 hours';f.style.background='#ffd8ce'}</script></body></html>'''


def dashboard(state,sources,events,items,base,practices=None):
    practices=practices or []
    counts=Counter(s['status'] for s in sources)
    latest=state['last_run_at']
    def link(url,text): return '<a href="'+escape(url or '#',quote=True)+'">'+escape(str(text))+'</a>'
    rows=[]
    for s in sources:
        rows.append('<tr><td>'+link('feeds/'+s['id']+'.xml',s['id'])+'</td><td>'+escape(s['title'])+'</td><td>'+escape(s['status'])+'</td><td>'+escape(s['validation_status'])+'</td><td>'+escape(s.get('last_success_at') or 'Never')+'</td><td>'+escape(s.get('last_error') or '; '.join(s['limitations']))+'</td></tr>')
    source_map={s['id']:s for s in sources}
    priority_ids={s['id'] for s in sources if s.get('feed_priority')=='regulatory'}
    focused_changes=[e for e in events if e['event_type']!='BASELINE' and e['source_id'] in priority_ids]
    current=current_events(items,events,source_ids=priority_ids)
    subscriptions=[]
    for regulator in sorted({s['regulator_id'] for s in sources}):
        sections=sorted((s for s in sources if s['regulator_id']==regulator),key=lambda s:s['id'])
        agency=next((s['publisher_name'] for s in sections if s.get('publisher_name')),regulator.upper())
        subscriptions.append('<li>'+escape(agency)+'<br>'+link('feeds/current/'+regulator+'.xml','Current items — all sections')+' · '+link('feeds/'+regulator+'.xml','Observation events — all sections')+'<ul>'+''.join('<li>'+link('feeds/'+s['id']+'.xml',s['title'])+' <small>'+escape(s['id'])+' — observation events</small></li>' for s in sections)+'</ul></li>')
    subscriptions=''.join(subscriptions)
    practice_rows=[]
    for practice in practices:
        practice_sources={s['id'] for s in sources if s['regulator_id'] in practice['regulator_ids']}
        unavailable=sum(1 for s in sources if s['id'] in practice_sources and s.get('status')!='healthy')
        count=len(current_events(items,events,source_ids=practice_sources))
        practice_rows.append('<li><strong>'+link('practice/'+practice['slug']+'/',practice['title'])+'</strong><span>'+escape(practice['summary'])+'</span><small>'+str(count)+' retained current items · '+str(len(practice_sources))+' source sections · '+str(unavailable)+' currently unavailable</small></li>')
    practice_directory='<ul class="practice-list">'+''.join(practice_rows)+'</ul>'
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'''+FAVICON+'''<title>Thai Regulatory Watch</title>
<style>'''+COMMON_CSS+'''</style></head><body><a class="skip-link" href="#main">Skip to content</a>
<header><div class="eyebrow">PUBLIC REGULATORY OBSERVATIONS · THAILAND</div><h1>Thai Regulatory Watch</h1><p>One collection. Feeds for people and structured observations for GRC review.</p><nav><a href="#practices">Practice focus</a><a href="#subscriptions">Regulator / section feeds</a><a href="#source-coverage">Source coverage</a><a href="feeds/changes.xml">Subscribe to changes</a><a href="feeds/all.xml">All events</a><a href="api/v1/events.json">GRC JSON</a><a href="feeds/health.xml">Source health RSS</a><a href="subscriptions.opml">Import subscriptions</a><a href="https://github.com/attorneynoon/thai-regulatory-watch">GitHub</a></nav></header>'''+ (
        '<main id="main"><p id="freshness" data-time="'+escape(latest or '')+'">'+escape('NOT RUN' if not latest else 'Last collection: '+latest)+'</p><p>'+
        escape(' · '.join(f'{k}: {v}' for k,v in sorted(counts.items())))+'</p><p>Candidate collection does not establish complete coverage. Pending scopes are included in the inventory but are not being collected. Publication dates may be unknown. All observations require review; legal effect is Not assessed.</p>'+
        '<section><h2>Regulatory focus</h2><p>Selected legal, decision, consultation and guidance sections. This is source-scope curation, not a finding of legal significance. General publicity stays in the full archive. '+link('feeds/regulatory.xml','Subscribe to regulatory inventory')+' · '+link('feeds/changes.xml','Regulatory changes only')+' · '+link('feeds/changes-all.xml','All changes including general news')+'</p></section>'+
        '<section id="practices"><h2>Practice focus</h2><p>Human-readable views that combine relevant regulators. A regulator can appear in more than one practice. Each page has current-items and changes RSS.</p>'+practice_directory+'</section>'+
        '<section><h2>Recent changes</h2><p>Regulatory-focus detections first; an update to an old document appears here.</p>'+event_list(ordered_events(focused_changes,detected=True)[:100],source_map,detected=True)+'</section>'+
        '<section><h2>Current regulatory inventory</h2><p>Showing '+str(min(100,len(current)))+' of '+str(len(current))+' retained regulatory-focus items. One representative current observation per canonical item. Newest source publication first, then source modification as fallback; undated items follow dated items. '+link('feeds/regulatory.xml','Subscribe to regulatory items')+' · '+link('feeds/current/all.xml','Unfiltered current inventory')+' · Full JSON (all retained items): '+link('api/v1/items.json','items.json')+'</p>'+event_list(current[:100],source_map)+'</section>'+
        '<section><h2>Regulator subscriptions</h2><p>Choose all sections for a regulator, or subscribe to an individual configured source section.</p><ul id="subscriptions">'+subscriptions+'</ul></section>'+
        '<section id="source-coverage"><h2>Source coverage</h2><input id="filter" aria-label="Filter sources" placeholder="Filter regulator, source or status"><div class="table"><table><thead><tr><th>Source RSS</th><th>Publisher / configured section</th><th>Run status</th><th>Validation</th><th>Last success</th><th>Limitations</th></tr></thead><tbody id="sources">'+''.join(rows)+'</tbody></table></div></section></main>'+
        '<footer>RSS keeps up to 500 events per view by default in the order described above. JSON preserves the retained history. A source failure is a coverage limitation, not evidence of no regulatory change.</footer>'
    )+'''<script>const f=document.getElementById('freshness');const t=Date.parse(f.dataset.time);if(t&&Date.now()-t>10800000){f.textContent+=' — STALE: more than 3 hours';f.style.background='#ffd8ce'}document.getElementById('filter').addEventListener('input',e=>{for(const r of document.querySelectorAll('#sources tr'))r.hidden=!r.textContent.toLowerCase().includes(e.target.value.toLowerCase())});</script></body></html>'''


def build_site(state,sources,out,base,limit=500,practices=None):
    validate_state(state)
    practices=practices or []
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
    priority_ids={s['id'] for s in sources if s.get('feed_priority')=='regulatory'}
    feeds['changes-all']=feeds['changes']
    feeds['changes']=[e for e in feeds['changes-all'] if e['source_id'] in priority_ids]
    feeds['regulatory']=current_events(inventory,events,source_ids=priority_ids)
    feeds['current/all']=current_events(inventory,events)
    for regulator in sorted({s['regulator_id'] for s in sources}):
        feeds[regulator]=[e for e in events if e['regulator_id']==regulator]
        feeds['current/'+regulator]=current_events(inventory,events,regulator)
    for topic in sorted({t for s in sources for t in s['topics']}):
        feeds['topic-'+topic]=[e for e in events if topic in e['topics']]
    for s in sources: feeds[s['id']]=[e for e in events if e['source_id']==s['id']]
    source_map={s['id']:{**s,**next(p for p in public if p['id']==s['id'])} for s in sources}
    practice_coverage={}
    for practice in practices:
        source_ids={s['id'] for s in sources if s['regulator_id'] in practice['regulator_ids']}
        current_name='practice-'+practice['slug']
        changes_name=current_name+'-changes'
        feeds[current_name]=current_events(inventory,events,source_ids=source_ids)
        feeds[changes_name]=[e for e in events if e['event_type']!='BASELINE' and e['source_id'] in source_ids]
        practice_coverage[current_name]=source_ids
        practice_coverage[changes_name]=source_ids
    for name,es in feeds.items():
        write_changed(out/'feeds'/f'{name}.xml',rss(name,es,base,limit,source_map,practice_coverage.get(name)))
    root=ET.Element('opml',version='2.0')
    element(ET.SubElement(root,'head'),'title','Thai Regulatory Watch')
    body=ET.SubElement(root,'body')
    for r in sorted({s['regulator_id'] for s in sources}): ET.SubElement(body,'outline',text=r,title=r,type='rss',xmlUrl=base+'/feeds/'+r+'.xml')
    if practices:
        group=ET.SubElement(body,'outline',text='Practice focus',title='Practice focus')
        for practice in practices:
            name='practice-'+practice['slug']
            ET.SubElement(group,'outline',text=practice['title']+' — current items',title=practice['title']+' — current items',type='rss',xmlUrl=base+'/feeds/'+name+'.xml')
            ET.SubElement(group,'outline',text=practice['title']+' — changes',title=practice['title']+' — changes',type='rss',xmlUrl=base+'/feeds/'+name+'-changes.xml')
    write_changed(out/'subscriptions.opml',ET.tostring(root,encoding='utf-8',xml_declaration=True))
    write_changed(out/'index.html',dashboard(state,public,events,inventory,base,practices))
    for practice in practices:
        write_changed(out/'practice'/practice['slug']/'index.html',practice_page(practice,public,events,inventory,base,state['last_run_at']))
    write_changed(out/'.nojekyll','')
    return {'items':len(inventory),'events':len(events),'feeds':len(feeds),'sources':len(sources),'practices':len(practices)}


def check_site(out):
    out=Path(out)
    for path in list((out/'feeds').rglob('*.xml'))+[out/'subscriptions.opml']:
        SafeXML.parse(path)
    for name,schema in SCHEMAS.items():
        Draft202012Validator(schema).validate(json.loads((out/'api/v1'/f'{name}.json').read_text('utf-8')))
