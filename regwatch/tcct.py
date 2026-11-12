"""Read-only qualification of TCCT's observed 2026 public listing API.

Not connected to collect/apply_observations: legacy URL identity reconciliation
must precede registry enablement. Never writes production state or downloads files.
"""
import argparse
import json
import re
from .models import clean_text, digest, utcnow
from .transport import Transport, TCCT_CATEGORIES, TCCT_ENDPOINT


def parse_page(body, category, page, limit=12):
    value=json.loads(body)
    if not isinstance(value,dict) or value.get('status')!='success':
        raise ValueError('TCCT API did not report success')
    data=value.get('data')
    if not isinstance(data,dict) or not isinstance(data.get('category'),dict) or data['category'].get('key')!=category:
        raise ValueError('TCCT category identity mismatch')
    meta=data.get('meta'); contents=data.get('contents')
    if not isinstance(meta,dict) or not isinstance(contents,list) or any(not isinstance(r,dict) for r in contents):
        raise ValueError('TCCT listing schema changed')
    for key in ('total','page','limit','totalPages'):
        if type(meta.get(key)) is not int or meta[key]<0: raise ValueError('Invalid TCCT pagination count')
    if meta['page']!=page or meta['limit']!=limit or len(contents)>limit:
        raise ValueError('TCCT pagination request/response mismatch')
    expected_pages=(meta['total']+limit-1)//limit
    if meta['totalPages']!=expected_pages or type(meta.get('hasNextPage')) is not bool or type(meta.get('hasPreviousPage')) is not bool:
        raise ValueError('TCCT pagination schema inconsistent')
    if meta['hasNextPage']!=(page<meta['totalPages']) or meta['hasPreviousPage']!=(page>1):
        raise ValueError('TCCT pagination flags inconsistent')
    if len(contents)!=max(0,min(limit,meta['total']-(page-1)*limit)):
        raise ValueError('TCCT truncated response or count changed')
    rows=[]; seen=set()
    for row in contents:
        ident=row.get('id');title=row.get('title')
        if not isinstance(ident,str) or not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',ident) or ident in seen:
            raise ValueError('TCCT missing or duplicate content identity')
        if not isinstance(title,str) or not title.strip() or row.get('is_active') is not True or row.get('is_draft') is not False:
            raise ValueError('TCCT title or public publication flags invalid')
        memberships=[row.get('category'),row.get('sub_category')]
        for member in row.get('categories',[]):
            if not isinstance(member,dict): raise ValueError('TCCT category membership schema changed')
            memberships.extend([member.get('category'),member.get('sub_category')])
        if not any(isinstance(m,dict) and m.get('key')==category for m in memberships):
            raise ValueError('TCCT content category membership unverified')
        seen.add(ident)
        files=row.get('file_list',[])
        if not isinstance(files,list): raise ValueError('TCCT file schema changed')
        public_files=[]
        for f in files:
            if not isinstance(f,dict): raise ValueError('TCCT file entry changed')
            url=f.get('fileUrl')
            if f.get('isPublic') is True and isinstance(url,str) and re.fullmatch(r'https://api\.tcct\.or\.th/upload/[0-9a-f-]{36}',url):
                public_files.append(url)
        rows.append(dict(content_id=ident,code=row.get('code') if isinstance(row.get('code'),str) else None,
                         title=clean_text(title),source_start_date=row.get('start_date') if isinstance(row.get('start_date'),str) else None,
                         public_files=sorted(set(public_files))))
    return rows,{k:meta[k] for k in ('total','page','limit','totalPages','hasNextPage','hasPreviousPage')}


def qualify(category,max_pages=1,transport=None):
    if category not in TCCT_CATEGORIES or type(max_pages) is not int or not 1<=max_pages<=10:
        raise ValueError('Unsupported TCCT category or qualification bound')
    transport=transport or Transport(['www.tcct.or.th'])
    items=[]; seen=set(); receipts=[]; total=None
    for page in range(1,max_pages+1):
        status,headers,body,final=transport.fetch_tcct_page(category,page,12)
        rows,meta=parse_page(body,category,page)
        if total is not None and total!=meta['total']: raise ValueError('TCCT inventory changed during pagination; retry a new bounded read')
        total=meta['total']
        for row in rows:
            if row['content_id'] in seen: raise ValueError('TCCT repeated identity across pages')
            seen.add(row['content_id']);items.append(row)
        receipts.append(dict(page=page,http_status=status,response_sha256=digest(body),meta=meta))
        if not meta['hasNextPage']: break
    return dict(category=category,endpoint=TCCT_ENDPOINT,retrieved_at=utcnow(),pages_checked=len(receipts),
                terminal_page_reached=not receipts[-1]['meta']['hasNextPage'],items=items,pages=receipts,
                limitations=['Listing metadata only; start_date is source field, not authenticated legal event/effectivity date.',
                             'No document downloads, legacy identity merge, legal classification or completeness certification.',
                             'Private/unmarked files and CMS/user metadata omitted.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('category',choices=sorted(TCCT_CATEGORIES));parser.add_argument('--max-pages',type=int,default=1)
    args=parser.parse_args()
    print(json.dumps(qualify(args.category,args.max_pages),ensure_ascii=False,indent=2))

if __name__=='__main__': main()
