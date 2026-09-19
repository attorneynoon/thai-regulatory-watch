"""Pure parsers. A source's explicit selectors define its collection scope."""
import re
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
    return {"url": url, "title": clean_text(title), "published_at": parse_date(raw_date), "publication_date_raw": raw_date, "document_url": url if urlsplit(url).path.lower().endswith(".pdf") else None, **extra}


def parse_document(source, body, final_url):
    mode = source["mode"]
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
                    rows.append(record(source, urljoin(final_url, links[0]), title, e.findtext(atom + "published"), modified_at=parse_date(e.findtext(atom + "updated"))))
                except ValueError:
                    continue
        else:
            for e in root.findall("./channel/item"):
                if not e.findtext("link"):
                    continue
                try:
                    rows.append(record(source, urljoin(final_url, e.findtext("link")), e.findtext("title", ""), e.findtext("pubDate")))
                except ValueError:
                    continue
        return [r for r in rows if accepted(source, r["url"], r["title"])], []
    soup = BeautifulSoup(body, "html.parser")
    for node in soup.select("script, style, noscript, nav, header, footer, .menu-root, #sitemap"):
        node.decompose()
    if mode == "page":
        selected = soup.select(source["content_selector"])
        text = clean_text(" ".join(n.get_text(" ", strip=True) for n in selected))
        if not text:
            raise ValueError("Selected content missing")
        title = soup.title.get_text(strip=True) if soup.title else source["title"]
        return [record(source, final_url, title, selected_text_sha256=digest(text), pinpoint=source["content_selector"])], []
    scope = soup.select_one(source["content_selector"]) if source.get("content_selector") else soup
    if scope is None:
        raise ValueError("Content scope missing")
    rows, seen = [], set()
    for a in scope.select(source.get("link_selector", "a[href]")):
        href = a.get(source.get('href_attribute','href'), "")
        title = clean_text(a.get_text(" ", strip=True)) or clean_text(a.get("title", ""))
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        try:
            url = allowed_url(urljoin(final_url, href), source["allowed_hosts"])
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
        if url in seen or not accepted(source, url, title):
            continue
        date = container.select_one(source.get("date_selector", "time"))
        raw_date = (date.get("datetime") or date.get_text(" ", strip=True)) if date else None
        rows.append(record(source, url, title, raw_date, pinpoint=source.get("link_selector", "a[href]")))
        seen.add(url)
    pages = []
    if source.get("pagination_selector"):
        for a in soup.select(source["pagination_selector"]):
            try:
                pages.append(allowed_url(urljoin(final_url, a.get("href", "")), source["allowed_hosts"]))
            except ValueError:
                continue
    return rows, pages
