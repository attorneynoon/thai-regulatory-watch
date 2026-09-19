import re
from pathlib import Path
from urllib.parse import urlsplit
import yaml
import soupsieve
from .models import canonical_url


def allowed_url(url, hosts):
    url = canonical_url(url)
    if urlsplit(url).hostname not in hosts:
        raise ValueError("Host outside explicit allowlist: " + urlsplit(url).hostname)
    return url


def load_registry(path):
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != "1.0" or not isinstance(data.get("sources"), list):
        raise ValueError("Unsupported source registry")
    sources = data["sources"]
    used = {"all", "changes", "changes-all", "regulatory", "baseline", "health"}
    regulators = {s["regulator_id"] for s in sources}
    topics = {"topic-" + t for s in sources for t in s["topics"]}
    if regulators & used or regulators & topics:
        raise ValueError("Reserved regulator feed name")
    used |= regulators | topics
    for s in sources:
        if s.get('feed_priority','radar') not in {'regulatory','radar'}:
            raise ValueError('Invalid feed priority')
        if s.get('render') not in {None, 'browser'}:
            raise ValueError('Invalid render mode')
        if s.get('render') == 'browser' and (s.get('mode') not in {'html', 'page'} or s.get('public_form')):
            raise ValueError('Browser rendering requires an HTML GET source')
        for name in [s["id"], s["regulator_id"], *s["topics"]]:
            if not re.fullmatch(r"[a-z][a-z0-9-]{1,79}", name):
                raise ValueError("Invalid identifier: " + name)
        if s["id"] in used:
            raise ValueError("Duplicate or reserved feed name: " + s["id"])
        used.add(s["id"])
        if s.get("validation_status") not in {"pending", "candidate", "verified", "disabled"}:
            raise ValueError("Invalid validation status")
        if type(s.get("enabled")) is not bool or not s["topics"]:
            raise ValueError("enabled must be boolean and topics nonempty")
        if s.get("url"):
            allowed_url(s["url"], s["allowed_hosts"])
        if not isinstance(s.get('tls_intermediates',{}),dict): raise ValueError('TLS intermediate map required')
        for host,cert in s.get('tls_intermediates',{}).items():
            cert_path=(path.parent.parent/cert).resolve()
            if host not in s['allowed_hosts'] or not cert_path.is_relative_to((path.parent/'tls').resolve()) or not cert_path.is_file():
                raise ValueError('TLS intermediate must be a repository config/tls file for an allowed host')
        if s.get('public_form'):
            if not isinstance(s['public_form'],dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in s['public_form'].items()) or len(s['public_form'])>10:
                raise ValueError('Public navigation form must be an explicit bounded string mapping')
            if s.get('public_form_url')!=s['url'] or s.get('max_pages',1)!=1 or s.get('start_urls'):
                raise ValueError('Public form must target the exact single observed source URL')
        if not isinstance(s.get('start_urls',[]),list) or len(s.get('start_urls',[]))>9:
            raise ValueError('At most nine additional discovery URLs allowed')
        for url in s.get('start_urls',[]): allowed_url(url,s['allowed_hosts'])
        if s.get('item_base_url'): allowed_url(s['item_base_url'],s['allowed_hosts'])
        if not isinstance(s.get('json_contains',{}),dict): raise ValueError('JSON membership filters must be a mapping')
        if s.get('json_sort'):
            if not isinstance(s['json_sort'],dict) or not isinstance(s['json_sort'].get('field'),str) or type(s['json_sort'].get('descending',True)) is not bool:
                raise ValueError('Invalid JSON sort definition')
        if s["enabled"]:
            if s.get("mode") not in {"html", "rss", "page", "json", "next-data", "json-html", "json-script", "json-page"} or not s.get("url") or s["validation_status"] not in {"candidate", "verified"}:
                raise ValueError("Enabled source requires a supported adapter and candidate/verified status")
            fixture = (path.parent.parent / s.get("fixture", "MISSING")).resolve()
            if not fixture.is_relative_to(path.parent.parent.resolve()) or not fixture.is_file():
                raise ValueError("Source fixture missing or outside repository: " + s["id"])
            if s.get("mode") == "page" and not s.get("content_selector"):
                raise ValueError("Page mode requires an explicit content selector")
            if s.get('mode')=='json-html' and not isinstance(s.get('json_html_field'),str):
                raise ValueError('JSON HTML mode requires an explicit string field path')
            if s.get('mode')=='json-page':
                fields=s.get('json_snapshot_fields')
                if not isinstance(s.get('json_rows'),str) or not isinstance(fields,list) or not fields or any(not isinstance(f,str) or not f for f in fields):
                    raise ValueError('JSON snapshot requires explicit row path and public field whitelist')
                if not isinstance(s.get('json_filter',{}),dict): raise ValueError('JSON filters must be an equality mapping')
            if s.get('mode')=='json-script' and not s.get('json_script_selector'):
                raise ValueError('JSON script mode requires an explicit selector')
            if s.get('date_calendar','gregorian') not in {'gregorian','buddhist'}:
                raise ValueError('Unknown date calendar')
            if s.get('mode') in {'json','next-data','json-script'}:
                if not isinstance(s.get('json_rows'),str) or not isinstance(s.get('json_fields'),dict) or 'title' not in s['json_fields']:
                    raise ValueError('JSON mode requires explicit row and title field mappings')
                if not all(isinstance(v,str) for v in s['json_fields'].values()):
                    raise ValueError('JSON field paths must be strings')
                if not isinstance(s.get('json_filter',{}),dict): raise ValueError('JSON filters must be an equality mapping')
                if s.get('url_template'):
                    template=s['url_template']
                    if '{' in urlsplit(template).netloc: raise ValueError('URL template cannot change host')
                    allowed_url(re.sub(r'\{[^{}]+\}','example',template),s['allowed_hosts'])
                elif 'url' not in s['json_fields']: raise ValueError('JSON item URL mapping missing')
                if s.get('item_base_url'): allowed_url(s['item_base_url'],s['allowed_hosts'])
        for key in ("link_selector", "item_selector", "content_selector", "date_selector", "pagination_selector", "title_selector", "json_script_selector", "summary_selector"):
            if s.get(key):
                soupsieve.compile(s[key])
        for key in ("include_url", "exclude_url", "include_title", "exclude_title", "date_pattern", "document_id_pattern"):
            if s.get(key):
                re.compile(s[key])
        for key, low, high, default in [("max_pages", 1, 10, 1), ("max_items", 1, 1000, 100), ("asset_budget", 0, 20, 2), ("min_items", 0, 1000, 1), ('max_response_bytes',1000,64_000_000,4_000_000)]:
            val = s.get(key, default)
            if type(val) is not int or not low <= val <= high:
                raise ValueError("Invalid bound: " + key)
    return sources
