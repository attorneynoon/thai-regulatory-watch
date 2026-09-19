"""Validated human-readable practice views over configured regulator sources."""
import re
from pathlib import Path

import yaml


def load_practices(path, sources):
    path=Path(path)
    data=yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(data,dict) or data.get('schema_version')!='1.0' or not isinstance(data.get('practices'),list):
        raise ValueError('Unsupported practice registry')
    known={source['regulator_id'] for source in sources}
    practices=[]
    slugs=set()
    for practice in data['practices']:
        if not isinstance(practice,dict):
            raise ValueError('Practice must be a mapping')
        slug=practice.get('slug')
        if not isinstance(slug,str) or not re.fullmatch(r'[a-z][a-z0-9-]{1,79}',slug):
            raise ValueError('Invalid practice slug')
        if slug in slugs:
            raise ValueError('Duplicate practice slug')
        slugs.add(slug)
        for field,limit in (('title',120),('summary',500)):
            value=practice.get(field)
            if not isinstance(value,str) or not value.strip() or len(value)>limit:
                raise ValueError('Invalid practice '+field)
        regulator_ids=practice.get('regulator_ids')
        if not isinstance(regulator_ids,list) or not regulator_ids or len(regulator_ids)!=len(set(regulator_ids)):
            raise ValueError('Practice regulator list must be nonempty and unique')
        unknown=set(regulator_ids)-known
        if unknown:
            raise ValueError('Unknown practice regulator: '+', '.join(sorted(unknown)))
        practices.append({
            'slug':slug,
            'title':practice['title'].strip(),
            'summary':practice['summary'].strip(),
            'regulator_ids':list(regulator_ids),
        })
    return practices
