import copy,json,unittest
from regwatch import tcct

ROW=dict(category={'key':'verdict'},id='75ad3a91-53ed-4ac0-ac65-27f357b38ee3',code='CTN260920125848',title='คำวินิจฉัยทดสอบ',start_date='2026-09-17T00:00:00.000Z',is_active=True,is_draft=False,owner={'secret':'excluded'},view_count=4,file_list=[{'fileUrl':'https://api.tcct.or.th/upload/private','isPublic':False}])
def payload():
 return dict(status='success',data=dict(category={'key':'verdict'},contents=[copy.deepcopy(ROW)],meta=dict(total=1,page=1,limit=12,totalPages=1,hasNextPage=False,hasPreviousPage=False)))
class TCCTTests(unittest.TestCase):
 def test_public_whitelist_keeps_identity_not_private_files(self):
  rows,meta=tcct.parse_page(json.dumps(payload()).encode(),'verdict',1)
  self.assertEqual(rows[0]['content_id'],ROW['id']); self.assertEqual(rows[0]['source_start_date'],ROW['start_date'])
  self.assertNotIn('owner',rows[0]);self.assertNotIn('view_count',rows[0]);self.assertEqual(rows[0]['public_files'],[])
 def test_schema_category_page_and_flags_fail_closed(self):
  for mutate in [lambda x:x.update(status='error'),lambda x:x['data']['category'].update(key='other'),lambda x:x['data']['meta'].update(page=2),lambda x:x['data']['meta'].update(hasNextPage=True),lambda x:x['data'].update(contents={}),lambda x:x['data']['contents'][0].update(is_draft=True),lambda x:x['data']['contents'][0].update(category={'key':'other'})]:
   x=payload();mutate(x)
   with self.assertRaises(ValueError):tcct.parse_page(json.dumps(x).encode(),'verdict',1)
 def test_external_or_unknown_public_file_is_not_emitted(self):
  x=payload();x['data']['contents'][0]['file_list']=[{'isPublic':True,'fileUrl':'https://evil.example/file'},{'fileUrl':'https://api.tcct.or.th/upload/unknown'}]
  rows,_=tcct.parse_page(json.dumps(x).encode(),'verdict',1);self.assertEqual(rows[0]['public_files'],[])
 def test_duplicate_id_rejected(self):
  x=payload();x['data']['contents']*=2;x['data']['meta']['total']=2
  with self.assertRaises(ValueError):tcct.parse_page(json.dumps(x).encode(),'verdict',1)
 def test_bounded_scan_reports_incomplete_without_state_writes(self):
  class T:
   def fetch_tcct_page(self,category,page,limit):
    x=payload();x['data']['meta'].update(total=25,totalPages=3,hasNextPage=True);x['data']['contents']=[{**ROW,'id':f'00000000-0000-4000-8000-{i:012d}'} for i in range(12)]
    return 201,{},json.dumps(x).encode(),'https://www.tcct.or.th/api/proxy/contents/now'
  r=tcct.qualify('verdict',max_pages=1,transport=T());self.assertFalse(r['terminal_page_reached']);self.assertEqual(r['pages_checked'],1);self.assertEqual(len(r['items']),12)
 def test_sanitized_official_first_page_fixtures(self):
  from pathlib import Path
  from regwatch.transport import TCCT_CATEGORIES
  for category in TCCT_CATEGORIES:
   rows,meta=tcct.parse_page((Path(__file__).parent/'fixtures'/'tcct-api'/(category+'.json')).read_bytes(),category,1)
   self.assertEqual(len(rows),min(meta['total'],12))
 def test_total_changes_and_duplicate_cross_page_are_rejected(self):
  for changing_total in (True,False):
   class T:
    def fetch_tcct_page(self,category,page,limit):
     x=payload();total=25 if changing_total and page==2 else 24
     x['data']['meta'].update(total=total,page=page,totalPages=(total+11)//12,hasNextPage=page<(total+11)//12,hasPreviousPage=page>1)
     x['data']['contents']=[{**ROW,'id':f'00000000-0000-4000-8000-{i:012d}'} for i in range(12)]
     return 201,{},json.dumps(x).encode(),'https://www.tcct.or.th/api/proxy/contents/now'
   with self.assertRaises(ValueError):tcct.qualify('verdict',max_pages=2,transport=T())
