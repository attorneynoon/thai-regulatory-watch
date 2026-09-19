"""Read-only GitHub runner qualification; never writes production state."""
import json,sys,platform
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from regwatch.transport import Transport
from regwatch.adapters import parse_document

paths=[*(f'/adjudication-panel-decisionsummary/adjudication-panel-decisionsummary-{i}/' for i in range(1,5)),'/consultation/','/category/pdpc-law/announce/','/category/pdpc-law/','/category/pdpc-news/']
t=Transport(['www.pdpc.or.th'])
for i,path in enumerate(paths):
    url='https://www.pdpc.or.th'+path
    result={'runner':platform.system(),'url':url}
    try:
        status,_,body,final=t.fetch(url)
        s={'mode':'html','allowed_hosts':['www.pdpc.or.th']}
        if i<5:s.update(link_selector='.pdpc-attachment-box button[data-href]',href_attribute='data-href',item_selector='.pdpc-attachment-box',title_selector='h3.title',date_selector='.meta .date')
        else:s.update(link_selector='.post-list .post-item h3.title a[href]',item_selector='.post-item',date_selector='.date')
        rows,_=parse_document(s,body,final)
        result.update(status=status,records=len(rows),dated=sum(bool(r.get('published_at')) for r in rows))
    except Exception as exc:result['error']=str(exc)
    print(json.dumps(result,ensure_ascii=False),flush=True)
