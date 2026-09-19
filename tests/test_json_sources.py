import json
import unittest
from regwatch.adapters import parse_document


class PublicJsonTests(unittest.TestCase):
    def test_embedded_json_script_and_explicit_buddhist_iso_date(self):
        source={'mode':'json-script','allowed_hosts':['example.org'],'json_script_selector':'script#__NEXT_DATA__',
                'json_rows':'props.rows','json_fields':{'title':'title','modified_at':'updated'},
                'url_template':'https://example.org/item/{id}','date_calendar':'buddhist'}
        body=b'<script>throw Error("never execute")</script><script id="__NEXT_DATA__" type="application/json">{"props":{"rows":[{"title":"A","id":"1","updated":"2569-09-18T08:25:22.428Z"}]}}</script>'
        rows,_=parse_document(source,body,'https://example.org/')
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['modified_at'],'2026-09-18T08:25:22.428000+00:00')
        self.assertIsNone(rows[0]['published_at'])
        with self.assertRaises(ValueError): parse_document(source,b'<script>missing data</script>','https://example.org/')

    def test_categories_and_newest_first_export(self):
        source={'mode':'json','allowed_hosts':['example.org'],'json_rows':'',
                'json_fields':{'title':'title','url':'link','published_at':'date'},
                'json_filter':{'active':1},'json_contains':{'categories':'news'},
                'json_sort':{'field':'date','descending':True}}
        payload=[{'title':'Old','link':'/old','date':'2025-01-01','active':1,'categories':['news']},
                 {'title':'New','link':'/new','date':'2026-09-19','active':1,'categories':['news','notice']},
                 {'title':'Excluded','link':'/x','date':'2026-09-20','active':1,'categories':['staff']}]
        rows,_=parse_document(source,json.dumps(payload).encode(),'https://example.org/')
        self.assertEqual([r['title'] for r in rows],['New','Old'])

    def test_public_api_mapping_filters_unpublished_and_keeps_dates(self):
        source={'mode':'json','allowed_hosts':['example.org'],'json_rows':'data.result',
                'json_fields':{'title':'title.rendered','published_at':'date','document_id':'id','summary':'excerpt'},
                'url_template':'https://example.org/news/{slug}','json_filter':{'status':'publish'}}
        payload={'data':{'result':[
            {'id':12,'slug':'new rule','title':{'rendered':'<b>Order &amp; notice</b>'},'date':'19/09/2569','excerpt':'<p>Public summary</p>','status':'publish'},
            {'id':13,'slug':'draft','title':{'rendered':'Do not publish'},'status':'draft'}]}}
        rows,_=parse_document(source,json.dumps(payload).encode(),'https://example.org/api')
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['url'],'https://example.org/news/new%20rule')
        self.assertEqual(rows[0]['title'],'Order & notice')
        self.assertEqual(rows[0]['published_at'],'2026-09-19')
        self.assertEqual(rows[0]['document_id'],'12')
        self.assertEqual(rows[0]['summary'],'Public summary')

    def test_changed_api_shape_fails_instead_of_accepting_empty(self):
        source={'mode':'json','allowed_hosts':['example.org'],'json_rows':'data.result','json_fields':{'title':'title','url':'link'}}
        with self.assertRaises(ValueError):
            parse_document(source,b'{"data":{"error":"maintenance"}}','https://example.org/api')

    def test_json_pointer_and_link_allowlist(self):
        source={'mode':'json','allowed_hosts':['example.org'],'json_rows':'',
                'json_fields':{'title':'/metadata/dc.title/0/value','url':'link'}}
        body=[{'metadata':{'dc.title':[{'value':'A'}]},'link':'https://example.org/a'},
              {'metadata':{'dc.title':[{'value':'B'}]},'link':'https://evil.example/b'}]
        rows,_=parse_document(source,json.dumps(body).encode(),'https://example.org/api')
        self.assertEqual([r['title'] for r in rows],['A'])
        self.assertIsNone(rows[0]['published_at'])
