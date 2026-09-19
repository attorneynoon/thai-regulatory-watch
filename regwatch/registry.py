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
    used = {"all", "changes", "baseline", "health"}
    regulators = {s["regulator_id"] for s in sources}
    topics = {"topic-" + t for s in sources for t in s["topics"]}
    if regulators & used or regulators & topics:
        raise ValueError("Reserved regulator feed name")
    used |= regulators | topics
    for s in sources:
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
        if s["enabled"]:
            if s.get("mode") not in {"html", "rss", "page"} or not s.get("url") or s["validation_status"] not in {"candidate", "verified"}:
                raise ValueError("Enabled source requires a supported adapter and candidate/verified status")
            fixture = (path.parent.parent / s.get("fixture", "MISSING")).resolve()
            if not fixture.is_relative_to(path.parent.parent.resolve()) or not fixture.is_file():
                raise ValueError("Source fixture missing or outside repository: " + s["id"])
            if s.get("mode") == "page" and not s.get("content_selector"):
                raise ValueError("Page mode requires an explicit content selector")
        for key in ("link_selector", "item_selector", "content_selector", "date_selector", "pagination_selector", "title_selector"):
            if s.get(key):
                soupsieve.compile(s[key])
        for key in ("include_url", "exclude_url", "include_title", "exclude_title"):
            if s.get(key):
                re.compile(s[key])
        for key, low, high, default in [("max_pages", 1, 10, 1), ("max_items", 1, 1000, 100), ("asset_budget", 0, 20, 2), ("min_items", 0, 1000, 1)]:
            val = s.get(key, default)
            if type(val) is not int or not low <= val <= high:
                raise ValueError("Invalid bound: " + key)
    return sources
