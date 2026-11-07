"""Read-only AMLO/DIP source contract probes. No form submission or response persistence."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
from regwatch.adapters import parse_document
from regwatch.registry import load_registry
from regwatch.storage import load_state
from regwatch.transport import Transport

ROOT = Path(__file__).resolve().parents[1]
AMLO_ENTRY = "https://www.amlo.go.th/index.php/th/"
DIP_NEWS = "https://www.ipthailand.go.th/th/dip-news.html"
SAFE_FIELD = re.compile(r"[A-Za-z_][A-Za-z0-9_:-]{0,79}\Z")


def inspect_amlo_form(body, entry_url=AMLO_ENTRY):
    """Expose names only; never serialize hidden values, cookies, HTML or tokens."""
    soup = BeautifulSoup(body, "html.parser")
    matches = []
    for form in soup.find_all("form"):
        if str(form.get("method", "get")).lower() != "post":
            continue
        if urljoin(entry_url, form.get("action", "")) != entry_url:
            continue
        fields = form.select("input[name], button[name], select[name], textarea[name]")
        hidden = sorted(
            str(e.get("name")) if SAFE_FIELD.fullmatch(str(e.get("name"))) else "[nonstandard]"
            for e in fields
            if e.name == "input" and str(e.get("type", "text")).lower() == "hidden"
        )
        other = sum(
            e.name != "input" or str(e.get("type", "text")).lower() != "hidden"
            for e in fields
        )
        matches.append({"hidden_names": hidden, "other_controls": other,
                        "input_count": len(fields)})
    return {"same_entry_post_form_count": len(matches), "forms": matches[:3],
            "contract_requires_review": len(matches) != 1 or (
                bool(matches) and (matches[0]["hidden_names"] != ["intro_page"]
                                   or matches[0]["other_controls"] != 0)),
            "form_submitted": False}


def inspect_dip_json(body, source, previous_count=0):
    """Apply existing parser in memory and report the unchanged count-drop gate."""
    raw = json.loads(body)
    if not isinstance(raw, list):
        raise ValueError("DIP JSON root must be an array")
    rows, pages = parse_document(source, body, source["url"])
    count = len(rows)
    return {"raw_rows": len(raw), "accepted_rows": count,
            "unique_urls": len({r["url"] for r in rows}),
            "previous_count": previous_count,
            "count_drop_guard_would_trigger": previous_count >= 10
                                              and count < previous_count * 0.5,
            "pagination_links": len(pages), "retained_state_written": False}


def inspect_dip_public_listing(body, base_url=DIP_NEWS):
    """Separate publisher page only; NOT a qualified substitute for the JSON API."""
    soup = BeautifulSoup(body, "html.parser")
    text = soup.get_text(" ", strip=True)
    host = urlsplit(base_url).hostname
    links = {
        urljoin(base_url, a.get("href", ""))
        for a in soup.select("a[href]")
        if urlsplit(urljoin(base_url, a.get("href", ""))).hostname == host
    }
    return {"official_listing_marker": "ข่าวประชาสัมพันธ์" in text,
            "same_host_link_count": len(links),
            "mentions_november_2569": "พฤศจิกายน 2569" in text,
            "feed_contract_qualified": False}


def fetch_summary(url, hosts, budget, parser):
    """GET only, using existing host, TLS, robots and bounded transport policy."""
    transport = Transport(hosts)
    try:
        status, headers, body, final = transport.fetch(url, max_bytes=budget)
        return {"status": "observed", "http_status": status,
                "final_url": final, "content_type": headers.get("Content-Type", "")[:100],
                "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                "diagnostic": parser(body)}
    except Exception as exc:
        return {"status": "unavailable", "error": str(exc)[:250]}
    finally:
        transport.session.close()



def extended_dip_source(source):
    """Read-only 100-row alternative of the exact existing official API."""
    parts = urlsplit(source["url"])
    if (parts.scheme != "https" or parts.hostname != "webnew.ipthailand.go.th"
            or parts.path != "/wp-json/wp/v2/news"):
        raise ValueError("Unexpected DIP API host or path")
    query = parse_qsl(parts.query, keep_blank_values=True)
    if [v for k, v in query if k == "per_page"] != ["20"]:
        raise ValueError("Expected the configured 20-row DIP API")
    candidate = [(k, "100" if k == "per_page" else v) for k, v in query]
    return {**source, "url": urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(candidate), parts.fragment)
    )}


def main():
    registry = {s["id"]: s for s in load_registry(ROOT / "config/sources.yml")}
    state = load_state(ROOT / "state/monitor.json")
    amlo, dip = registry["amlo-listing-01"], registry["dip-listing-01"]
    previous = state["sources"].get(dip["id"], {}).get("last_count", 0)
    expanded = extended_dip_source(dip)
    outcome = {
        "purpose": "read_only_contract_qualification_not_source_recovery",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "production_files_written": False,
        "amlo_intro_get": fetch_summary(
            amlo["url"], amlo["allowed_hosts"], 1_000_000, inspect_amlo_form),
        "dip_existing_api_get": fetch_summary(
            dip["url"], dip["allowed_hosts"], 2_000_000,
            lambda body: inspect_dip_json(body, dip, previous)),
        "dip_extended_api_get": fetch_summary(
            expanded["url"], dip["allowed_hosts"], 2_000_000,
            lambda body: inspect_dip_json(body, expanded, previous)),
        "dip_public_news_get": fetch_summary(
            DIP_NEWS, ["www.ipthailand.go.th"], 2_000_000,
            inspect_dip_public_listing),
    }
    print(json.dumps(outcome, ensure_ascii=False, sort_keys=True))
    # Exit 0 signifies only that the diagnostic finished, not source recovery.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
