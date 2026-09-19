"""Explicit field maps for observed public JSON contracts; never execute data."""
import json
import re
from urllib.parse import quote,urljoin
from bs4 import BeautifulSoup
from .models import clean_text,parse_date
from .registry import allowed_url


def field(value,path):
    if path in ('',None): return value if path=='' else None
    parts=[p.replace('~1','/').replace('~0','~') for p in path[1:].split('/')] if path.startswith('/') else path.split('.')
    for part in parts:
        if isinstance(value,dict): value=value.get(part)
        elif isinstance(value,list) and part.isdigit() and int(part)<len(value): value=value[int(part)]
        else: return None
    return value


def text(value):
    if value is None: return None
    if not isinstance(value,(str,int,float)): raise ValueError('Expected a scalar JSON field')
    return clean_text(BeautifulSoup(str(value),'html.parser').get_text(' ',strip=True))


def parse_json_rows(source,body,final_url):
    if source['mode']=='next-data':
        from .nextdata import extract_next_rows
        rows=extract_next_rows(body,source['json_rows'])
    elif source['mode']=='json-script':
        nodes=BeautifulSoup(body,'html.parser').select(source['json_script_selector'])
        if len(nodes)!=1 or nodes[0].name!='script' or nodes[0].get('type')!='application/json':
            raise ValueError('Expected exactly one inert application/json script')
        rows=field(json.loads(nodes[0].string or ''),source['json_rows'])
    else:
        rows=field(json.loads(body),source['json_rows'])
    if not isinstance(rows,list) or any(not isinstance(r,dict) for r in rows):
        raise ValueError('Public JSON record array missing or changed shape')
    if source.get('json_sort'):
        order=source['json_sort']
        rows=sorted(rows,key=lambda r:(field(r,order['field']) is not None,str(field(r,order['field']) or '')),reverse=order.get('descending',True))
    result=[]
    for row in rows:
        if any(field(row,k)!=v for k,v in source.get('json_filter',{}).items()): continue
        if any(not isinstance(field(row,k),list) or v not in field(row,k) for k,v in source.get('json_contains',{}).items()): continue
        values={k:field(row,v) for k,v in source['json_fields'].items()}
        title=text(values.get('title'))
        if not title: continue
        url=values.get('url')
        if source.get('url_template'):
            def substitute(match):
                value=field(row,match.group(1))
                if not isinstance(value,(str,int)): raise ValueError('Missing public URL identifier')
                return quote(str(value),safe='')
            url=re.sub(r'\{([^{}]+)\}',substitute,source['url_template'])
        if not isinstance(url,str) or not url: continue
        try: url=allowed_url(urljoin(source.get('item_base_url',final_url),url),source['allowed_hosts'])
        except ValueError: continue
        raw_date=values.get('published_at')
        from .adapters import record,accepted
        if not accepted(source,url,title): continue
        def source_date(value):
            if source.get('date_calendar')=='buddhist' and isinstance(value,str) and re.match(r'^\d{4}-\d{2}-\d{2}',value):
                value=str(int(value[:4])-543).zfill(4)+value[4:]
            return parse_date(value)
        result.append(record(source,url,title,raw_date,
            published_at=source_date(raw_date),
            modified_at=source_date(values.get('modified_at')),
            summary=text(values.get('summary')),
            document_id=str(values['document_id']) if values.get('document_id') is not None else None,
            pinpoint='json:'+source['json_rows']))
    return result,[]
