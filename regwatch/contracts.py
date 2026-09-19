"""Versioned, published JSON contracts used by producer and consumers."""
STRING={'type':'string'}
NULLABLE={'type':['string','null']}
STRINGS={'type':'array','items':STRING}
EVENT_PROPERTIES={k:STRING for k in ['event_id','observation_id','item_id','source_id','regulator_id','publisher','jurisdiction','document_type','authority_class','classification_basis','language','title','official_url','canonical_url','listing_url','first_observed_at','observed_at','content_sha256','extraction_method','extraction_confidence','coverage_status','signal_type','temporal_horizon']}
EVENT_PROPERTIES.update({k:NULLABLE for k in ['previous_event_id','summary','document_url','document_id','published_at','publication_date_raw','modified_at','effective_at','attachment_sha256','source_response_sha256','pinpoint']})
EVENT_PROPERTIES.update(schema_version={'const':'1.0'},event_type={'enum':['BASELINE','NEW','UPDATED','UPDATED_ATTACHMENT']},revision={'type':'integer','minimum':1},topics=STRINGS,limitations=STRINGS,changed_fields=STRINGS,review_status={'const':'unreviewed'},legal_effect={'const':'Not assessed'},signal_candidate={'enum':['Radar','Watch','Action',None]})
EVENT={'type':'object','required':list(EVENT_PROPERTIES),'properties':EVENT_PROPERTIES,'additionalProperties':True}


def envelope_schema(kind,entry):
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','title':'Regulatory Watch '+kind+' v1','type':'object','required':['schema_version','generated_at','records'],'properties':{'schema_version':{'const':'1.0'},'generated_at':NULLABLE,'records':{'type':'array','items':entry}},'additionalProperties':False}


SCHEMAS={
 'events':envelope_schema('events',EVENT),
 'items':envelope_schema('items',{'type':'object','required':['item_id','canonical_url','source_ids','observations'],'properties':{'item_id':STRING,'canonical_url':STRING,'source_ids':STRINGS,'observations':{'type':'array','items':{'type':'object','required':['source_id','event_id','title','revision']}}}}),
 'sources':envelope_schema('sources',{'type':'object','required':['id','regulator_id','title','url','topics','enabled','validation_status','status','limitations'],'properties':{'id':STRING,'url':NULLABLE,'topics':STRINGS,'enabled':{'type':'boolean'},'validation_status':{'enum':['candidate','pending','verified','disabled']},'status':{'enum':['not-run','pending','disabled','healthy','degraded','blocked','failed']},'limitations':STRINGS}}),
 'health':envelope_schema('health',{'type':'object','required':['event_id','source_id','regulator_id','observed_at','status','previous_status','message','official_url'],'properties':{'event_id':STRING,'status':{'enum':['healthy','degraded','blocked','failed']},'message':NULLABLE,'official_url':NULLABLE}})
}
