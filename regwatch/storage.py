import json
import os
from contextlib import contextmanager
from pathlib import Path
from jsonschema import Draft202012Validator
from .engine import empty_state


def encode(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n'


def validate_state(state):
    if not isinstance(state,dict) or state.get('schema_version')!='1.0':
        raise ValueError('Unsupported or corrupt state')
    for key,typ in [('items',dict),('sources',dict),('events',list),('health_events',list)]:
        if not isinstance(state.get(key),typ): raise ValueError('Invalid state '+key)
    event_ids=set()
    for e in state['events']:
        if not isinstance(e,dict) or not all(k in e for k in ['event_id','item_id','source_id','title','observed_at','revision','legal_effect','review_status']):
            raise ValueError('Corrupt event')
        if e['event_id'] in event_ids or e['item_id'] not in state['items'] or e['source_id'] not in state['sources']:
            raise ValueError('Broken event identity or reference')
        if e['legal_effect']!='Not assessed' or e['review_status']!='unreviewed': raise ValueError('Non-review-only event')
        event_ids.add(e['event_id'])
    for sid,s in state['sources'].items():
        if not isinstance(s,dict) or type(s.get('baseline_complete')) is not bool or not isinstance(s.get('observations'),dict):
            raise ValueError('Corrupt source state')
        for iid,o in s['observations'].items():
            if iid not in state['items'] or o.get('event_id') not in event_ids or not isinstance(o.get('revision'),int) or o['revision'] < 1:
                raise ValueError('Broken observation reference')


def load_state(path):
    path=Path(path)
    if not path.exists(): raise FileNotFoundError('State missing; restore the tracked state rather than resetting history: '+str(path))
    value=json.loads(path.read_text('utf-8'))
    validate_state(value)
    return value


def write_changed(path,content):
    path=Path(path)
    if isinstance(content,str): content=content.encode('utf-8')
    if path.exists() and path.read_bytes()==content: return False
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_bytes(content)
    os.replace(tmp,path)
    return True


@contextmanager
def writer_lock(root):
    path=Path(root)/'.regwatch.lock'
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    try:
        os.write(fd,str(os.getpid()).encode())
        os.close(fd)
        yield
    finally:
        path.unlink()
