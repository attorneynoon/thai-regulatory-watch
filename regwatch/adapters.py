"""Pure parsers. A source's explicit selectors define its collection scope."""
import re
import json
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup
from defusedxml import ElementTree as XML
from .models import clean_text, parse_date, digest
from .registry import allowed_url


def accepted(source, url, title):
    for field, value in (("url", url), ("title", title)):
        inc, exc = source.get("include_" + field), source.get("exclude_" + field)
        if inc and not re.search(inc, value, re.I):
            return False
        if exc and re.search(exc, value, re.I):
            return False
    return bool(title)


def record(source, url, title, raw_date=None, **extra):
    url = allowed_url(url, source["allowed_hosts"])
    if source.get('document_id_pattern'):
        match=re.search(source['document_id_pattern'],title)
        extra['document_id']=(match.group(1) if match.lastindex else match.group(0)) if match else None
    return {"url": url, "title": clean_text(title), "published_at": parse_date(raw_date), "publication_date_raw": raw_date, "document_url": url if urlsplit(url).path.lower().endswith(".pdf") else None, **extra}


def source_excerpt(value):
    if not value: return None
    soup=BeautifulSoup(value,'html.parser')
    for node in soup.select('script,style,noscript'):node.decompose()
    value=clean_text(soup.get_text(' ',strip=True))
    return (value[:600]+'…' if len(value)>600 else value) or None


def parse_document(source, body, final_url):
    mode = source["mode"]
    if mode=='json-page':
        from .jsonsnapshot import parse_json_snapshot
        return parse_json_snapshot(source,body,final_url)
    if mode in {'json','next-data','json-script'}:
        from .json_sources import parse_json_rows
        return parse_json_rows(source,body,final_url)
    if mode=='json-html':
        from .json_sources import field
        body=field(json.loads(body),source['json_html_field'])
        if not isinstance(body,str): raise ValueError('Public JSON HTML fragment missing')
    if mode == "rss":
        root = XML.fromstring(body)
        rows = []
        atom = "{http://www.w3.org/2005/Atom}"
        if root.tag == atom + "feed":
            entries = root.findall(atom + "entry")
            for e in entries:
                links = [n.get("href") for n in e.findall(atom + "link") if n.get("rel", "alternate") == "alternate"]
                if not links:
                    continue
                title = e.findtext(atom + "title", "")
                try:
                    rows.append(record(source, urljoin(final_url, links[0]), title, e.findtext(atom + "published"), modified_at=parse_date(e.findtext(atom + "updated")),summary=source_excerpt(e.findtext(atom+'summary'))))
                except ValueError:
                    continue
        else:
            for e in root.findall("./channel/item"):
                if not e.findtext("link"):
                    continue
                try:
                    rows.append(record(source, urljoin(final_url, e.findtext("link")), e.findtext("title", ""), e.findtext("pubDate"),summary=source_excerpt(e.findtext('description'))))
                except ValueError:
                    continue
        rows = [r for r in rows if accepted(source, r["url"], r["title"])]
        # Some official feeds publish oldest-first. Sort before the collector's
        # item bound so a large archive cannot crowd out current publications.
        rows.sort(key=lambda row: (row.get("published_at") is not None, row.get("published_at") or ""), reverse=True)
        return rows, []
    soup = BeautifulSoup(body, "html.parser")
    for node in soup.select("script, style, noscript, nav, header, footer, .menu-root, #sitemap"):
        node.decompose()
    if mode == "page":
        selected = soup.select(source["content_selector"])
        text = clean_text(" ".join(n.get_text(" ", strip=True) for n in selected))
        if not text:
            raise ValueError("Selected content missing")
        title = (clean_text(soup.title.get_text(' ',strip=True)) if soup.title else '') or source['title']
        return [record(source, final_url, title, selected_text_sha256=digest(text), pinpoint=source["content_selector"])], []
    scope = soup.select_one(source["content_selector"]) if source.get("content_selector") else soup
    if scope is None:
        raise ValueError("Content scope missing")
    rows, seen = [], set()
    for a in scope.select(source.get("link_selector", "a[href]")):
        href = a.get(source.get('href_attribute','href'), "")
        title = clean_text(a.get_text(" ", strip=True)) or clean_text(a.get("title", ""))
        if source.get('title_attribute'):
            title=clean_text(a.get(source['title_attribute'],'')) or title
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        try:
            url = allowed_url(urljoin(source.get('item_base_url',final_url), href), source["allowed_hosts"])
        except ValueError:
            continue
        container = a
        item_selector = source.get("item_selector")
        if item_selector:
            container = next((p for p in a.parents if getattr(p, "name", None) and p.select_one and __import__("soupsieve").match(item_selector, p)), a)
        else:
            container = a.parent
        if source.get('title_selector'):
            title_node=container.select_one(source['title_selector'])
            title=clean_text(title_node.get_text(' ',strip=True)) if title_node else ''
            if title_node and source.get('title_attribute'):
                title=clean_text(title_node.get(source['title_attribute'],'')) or title
        if url in seen or not accepted(source, url, title):
            continue
        date = container.select_one(source.get("date_selector", "time"))
        raw_date = (date.get("datetime") or date.get_text(" ", strip=True)) if date else None
        if raw_date and source.get('date_pattern'):
            match=re.search(source['date_pattern'],raw_date)
            raw_date=(match.group(1) if match.lastindex else match.group(0)) if match else None
        summary_node=container.select_one(source['summary_selector']) if source.get('summary_selector') else None
        rows.append(record(source, url, title, raw_date, summary=source_excerpt(str(summary_node)) if summary_node else None,pinpoint=source.get("link_selector", "a[href]")))
        seen.add(url)
    pages = []
    if source.get("pagination_selector"):
        for a in soup.select(source["pagination_selector"]):
            try:
                pages.append(allowed_url(urljoin(final_url, a.get("href", "")), source["allowed_hosts"]))
            except ValueError:
                continue
    return rows, pages
