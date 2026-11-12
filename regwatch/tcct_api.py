"""Pure, offline qualification of TCCT's observed November 2026 category API.

This pure parser does not fetch anything, invent article routes, infer
publication dates, or change monitor state. A complete result means the supplied pages satisfy this captured
listing contract; it does not establish live access or archive completeness.
"""
from collections import Counter
from datetime import datetime
from html.parser import HTMLParser
import ipaddress
import json
import re
from urllib.parse import urlsplit

from .models import clean_text, digest

CATEGORIES = (
    "verdict", "verdict-mergers", "draft-principles-hearing",
    "tcct-draft-laws-hearing", "giveaway-news-2569", "activity-news-2569",
)
# The CLI's six requested scopes stay fixed. The production collector also
# supports their two observed all-year news parents, without replacing them
# with a single year and silently narrowing older configured sources.
API_CATEGORIES = CATEGORIES + ("giveaway-news", "activity-news")
ENDPOINT = "https://www.tcct.or.th/api/proxy/contents/now"
MIGRATION_VERSION = "tcct-api-2026-11"
LISTING_URLS = {key: "https://www.tcct.or.th/category/" + key for key in API_CATEGORIES}
LISTING_URLS["giveaway-news-2569"] = "https://www.tcct.or.th/category/giveaway-news/giveaway-news-2569"
LISTING_URLS["activity-news-2569"] = "https://www.tcct.or.th/category/activity-news/activity-news-2569"
PAGE_LIMIT = 12
MAX_CAPTURE_PAGES = 1000
MAX_LIVE_PAGES = 100


def request_payload(category_key, page_number):
    payload = {"category_key": category_key, "is_active": True,
               "page_number": page_number, "limit": PAGE_LIMIT,
               "sort_by": "start_date", "sort_direction": "desc"}
    validate_request(ENDPOINT, payload)
    return payload


def validate_request(url, payload):
    """Allow only the observed public listing query, never arbitrary JSON POST."""
    fields = {"category_key", "is_active", "page_number", "limit", "sort_by", "sort_direction"}
    if url != ENDPOINT or not isinstance(payload, dict) or set(payload) != fields:
        raise ValueError("JSON POST requires the exact TCCT listing endpoint and fields")
    if (not isinstance(payload["category_key"], str) or payload["category_key"] not in API_CATEGORIES
            or payload["is_active"] is not True
            or type(payload["limit"]) is not int or payload["limit"] != PAGE_LIMIT
            or payload["sort_by"] != "start_date" or payload["sort_direction"] != "desc"):
        raise ValueError("Unsupported TCCT public listing query")
    _integer(payload["page_number"], "page_number", 1, MAX_LIVE_PAGES)


def _string(value, label, nullable=False, empty=False):
    if value is None and nullable:
        return None
    if not isinstance(value, str) or (not empty and not value.strip()):
        raise ValueError(label + " must be a string" + (" or null" if nullable else ""))
    return value


def _integer(value, label, low=0, high=1_000_000):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(label + " must be a bounded integer")
    return value


def _object(value, label):
    if not isinstance(value, dict):
        raise ValueError(label + " must be an object")
    return value


def _require_fields(value, fields, label):
    missing = sorted(set(fields) - value.keys())
    if missing:
        raise ValueError(label + " is missing expected fields: " + ", ".join(missing))


def _date(value, label):
    value = _string(value, label, nullable=True)
    if value is not None:
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(label + " is not an ISO source date") from exc
    return value


def safe_reference_url(value):
    """Syntax-only URL screening; never resolve DNS or dereference a reference.

    A DNS hostname that passes this offline check is not proof that its eventual
    destination is public or accessible. Production transport must check it again.
    """
    value = _string(value, "reference URL")
    if any(c.isspace() or ord(c) < 32 for c in value) or "\\" in value:
        raise ValueError("Unsafe URL characters")
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        if parsed.scheme != "https" or not host or parsed.username is not None or parsed.password is not None or parsed.port not in (None, 443):
            raise ValueError("Only HTTPS references without credentials or custom ports are accepted")
        host = host.rstrip(".").lower()
        if "%" in host:
            raise ValueError("Encoded or scoped reference host")
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            labels = host.encode("idna").decode("ascii").split(".")
            if (len(labels) < 2 or host.endswith((".localhost", ".local", ".internal", ".lan", ".home", ".invalid"))
                    or labels[-1].isdigit() or host.startswith("0x")
                    or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in labels)):
                raise ValueError("Non-public-looking reference host")
        else:
            if not address.is_global or address.is_multicast:
                raise ValueError("Non-public reference address")
    except (UnicodeError, ValueError) as exc:
        raise ValueError("Unsafe reference URL: " + str(exc)) from exc
    return value


class _Body(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text = []
        self.links = []
        self.hidden = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "template"}:
            self.hidden.append(tag)
        if self.hidden:
            return
        self.text.append(" ")
        if tag == "a":
            href = dict(attrs).get("href")
            if href is not None:
                self.links.append(href)

    def handle_endtag(self, tag):
        if self.hidden:
            if tag == self.hidden[-1]:
                self.hidden.pop()
            return
        self.text.append(" ")

    def handle_data(self, data):
        if not self.hidden:
            self.text.append(data)


def _body(value, label):
    value = _string(value, label, nullable=True, empty=True)
    parser = _Body()
    parser.feed(value or "")
    parser.close()
    return clean_text("".join(parser.text)), parser.links


def _category(value, label):
    value = _object(value, label)
    _require_fields(value, ("parent_id",), label)
    result = {k: _string(value.get(k), label + "." + k) for k in ("id", "key", "name")}
    result["parent_id"] = _string(value.get("parent_id"), label + ".parent_id", nullable=True)
    if value.get("is_active") is not True or value.get("is_delete") is not False:
        raise ValueError(label + " is not an active, undeleted category")
    result.update(is_active=True, is_delete=False)
    for key in ("description", "filter_category_ids"):
        if key in value:
            result[key] = _string(value[key], label + "." + key, nullable=True, empty=True)
    if "sequence" in value:
        result["sequence"] = None if value["sequence"] is None else _integer(value["sequence"], label + ".sequence")
    return result


def _membership(value):
    value = _object(value, "category membership")
    _require_fields(value, ("id", "category_id", "sub_category_id", "sequence", "category", "sub_category"), "membership")
    result = {k: _string(value.get(k), "membership." + k, nullable=k == "sub_category_id")
              for k in ("id", "category_id", "sub_category_id")}
    result["sequence"] = _integer(value.get("sequence"), "membership.sequence")
    result["category"] = _category(value.get("category"), "membership.category")
    result["sub_category"] = None if value.get("sub_category") is None else _category(value["sub_category"], "membership.sub_category")
    if result["category_id"] != result["category"]["id"]:
        raise ValueError("Category membership identifier mismatch")
    sub = result["sub_category"]
    # Some public parent-archive rows retain a child ID while the expanded
    # relation is explicitly null. Keep that unresolved ID; only a populated
    # child can establish its key, year, parent or visibility.
    if sub and (result["sub_category_id"] != sub["id"] or sub["parent_id"] != result["category_id"]):
        raise ValueError("Subcategory membership identifier mismatch")
    return result


def _download(value):
    value = _object(value, "download")
    result = {k: _string(value.get(k), "download." + k) for k in
              ("id", "file_name", "display_file_name", "file_type", "file_extension", "file_path", "originalName")}
    result["file_size"] = _integer(value.get("file_size"), "download.file_size", high=100_000_000_000)
    if type(value.get("isPublic")) is not bool:
        raise ValueError("download.isPublic must be a boolean")
    # isPublic:false is published metadata, not a reason to discard a link.
    # It is not an authorization to request the file, either.
    result["isPublic"] = value["isPublic"]
    result["fileUrl"] = safe_reference_url(value.get("fileUrl"))
    return result


def normalize_record(record, category_key):
    """Retain public record semantics and every membership/file, without fetching."""
    if category_key not in API_CATEGORIES:
        raise ValueError("Unqualified category key")
    record = _object(record, "record")
    # These fields occur in every captured record. Explicit null is allowed
    # where documented below; omission is a changed contract, not missing data.
    # The top-level expanded sub_category is optional in hearing/archive rows;
    # its raw ID remains required, and expansion presence is preserved below.
    _require_fields(record, (
        "id", "code", "document_number", "title", "content", "description",
        "category_id", "sub_category_id", "file_list", "is_active", "is_draft",
        "start_date", "end_date", "is_reference_link", "url_link", "category", "categories",
    ), "record")
    if record.get("is_active") is not True or record.get("is_draft") is not False:
        raise ValueError("Record is inactive, draft, or has invalid visibility flags")
    raw_categories = record.get("categories")
    raw_files = record.get("file_list")
    if not isinstance(raw_categories, list) or not raw_categories or not isinstance(raw_files, list):
        raise ValueError("Record categories/file_list array missing or changed shape")
    categories = [_membership(value) for value in raw_categories]
    primary = _category(record.get("category"), "record.category")
    category_id = _string(record["category_id"], "record.category_id")
    sub_category_id = _string(record["sub_category_id"], "record.sub_category_id", nullable=True)
    sub_category_relation_state = ("omitted" if "sub_category" not in record else
                                   "null" if record["sub_category"] is None else "resolved")
    sub = None if record.get("sub_category") is None else _category(record["sub_category"], "record.sub_category")
    if category_id != primary["id"] or (sub and sub_category_id != sub["id"]):
        raise ValueError("Primary category identifier mismatch")
    if sub and sub["parent_id"] != primary["id"]:
        raise ValueError("Primary subcategory parent mismatch")
    if not any(m["category_id"] == category_id and m["sub_category_id"] == sub_category_id for m in categories):
        raise ValueError("Primary category is absent from memberships")
    if not any(category_key in {m["category"]["key"], (m["sub_category"] or {}).get("key")} for m in categories):
        raise ValueError("Record category does not match requested scope")
    body, hrefs = _body(record.get("content"), "record.content")
    description, description_hrefs = _body(record.get("description"), "record.description")
    downloads = [_download(value) for value in raw_files]
    if type(record.get("is_reference_link")) is not bool:
        raise ValueError("record.is_reference_link must be a boolean")
    reference = record.get("url_link")
    if reference is not None:
        reference = safe_reference_url(reference)
    if record["is_reference_link"] and reference is None:
        raise ValueError("Reference-link record is missing its URL")
    links, accepted, warnings = [], [], []
    if (sub_category_id is not None and sub is None) or any(
            m["sub_category_id"] is not None and m["sub_category"] is None for m in categories):
        warnings.append("source_subcategory_unresolved")
    if reference:
        accepted.append({"kind": "url_link", "url": reference})
    for kind, values in (("body", hrefs), ("description", description_hrefs)):
        for href in values:
            link = {"kind": kind, "raw_url": href}
            try:
                link.update(accepted=True, url=safe_reference_url(href))
                accepted.append({"kind": kind, "url": link["url"]})
            except ValueError as exc:
                link.update(accepted=False, reason=str(exc))
                warnings.append("rejected_reference")
            links.append(link)
    start = _date(record.get("start_date"), "record.start_date")
    years = sorted({int(match.group(1)) for m in categories
                    for cat in (m["category"], m["sub_category"])
                    if cat and (match := re.fullmatch(r"พ\.ศ\.\s*(\d{4})", cat["name"]))})
    if start and years and any(year - 543 != datetime.fromisoformat(start.replace("Z", "+00:00")).year for year in years):
        warnings.append("source_start_year_differs_from_category_year")
    if not body and not description and not downloads and not reference and not accepted:
        warnings.append("content_missing")
    result = {
        "id": _string(record.get("id"), "record.id"),
        "code": _string(record.get("code"), "record.code"),
        "document_number": _string(record.get("document_number"), "record.document_number", nullable=True, empty=True),
        "title": clean_text(_string(record.get("title"), "record.title")),
        "source_start_date": start,
        "source_end_date": _date(record.get("end_date"), "record.end_date"),
        "category_years_buddhist": years,
        "category_id": category_id, "sub_category_id": sub_category_id,
        "sub_category_relation_state": sub_category_relation_state,
        "category": primary, "sub_category": sub, "categories": categories,
        "body_text": body, "description_text": description,
        "downloads": downloads, "is_reference_link": record["is_reference_link"],
        "url_link": reference, "body_links": links, "reference_links": accepted,
    }
    result["content_sha256"] = digest(result)
    result["warnings"] = sorted(set(warnings))
    return result


def _decode(payload):
    def reject_constant(value):
        raise ValueError("Nonstandard JSON constant: " + value)

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON object key")
            result[key] = value
        return result
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    if isinstance(payload, str):
        payload = json.loads(payload, object_pairs_hook=unique_object, parse_constant=reject_constant)
    return _object(payload, "response")


def parse_page(payload, category_key, expected_page, expected_limit=PAGE_LIMIT):
    """Validate one captured response. This alone does not qualify a full scope."""
    if category_key not in API_CATEGORIES:
        raise ValueError("Unqualified category key")
    _integer(expected_page, "expected page", 1, MAX_CAPTURE_PAGES)
    if type(expected_limit) is not int or expected_limit != PAGE_LIMIT:
        raise ValueError("Only the observed 12-record page contract is supported")
    payload = _decode(payload)
    if payload.get("status") != "success":
        raise ValueError("API response did not report success")
    data = _object(payload.get("data"), "data")
    meta = _object(data.get("meta"), "meta")
    normalized_meta = {key: _integer(meta.get(key), "meta." + key, 1, MAX_CAPTURE_PAGES * PAGE_LIMIT)
                       for key in ("total", "page", "limit", "totalPages")}
    total, page, limit, count = (normalized_meta[k] for k in ("total", "page", "limit", "totalPages"))
    if page != expected_page or limit != expected_limit or count != (total + limit - 1) // limit or page > count or count > MAX_CAPTURE_PAGES:
        raise ValueError("Pagination page/limit/totalPages arithmetic mismatch")
    for key, expected in (("hasNextPage", page < count), ("hasPreviousPage", page > 1)):
        if type(meta.get(key)) is not bool or meta[key] != expected:
            raise ValueError("Pagination " + key + " mismatch")
        normalized_meta[key] = meta[key]
    category = _category(data.get("category"), "listing.category")
    if category["key"] != category_key:
        raise ValueError("Listing category does not match requested scope")
    raw_records = data.get("contents")
    if not isinstance(raw_records, list) or len(raw_records) != min(limit, total - (page - 1) * limit):
        raise ValueError("Page record count is inconsistent with pagination")
    records = [normalize_record(record, category_key) for record in raw_records]
    for record in records:
        matched = [cat for m in record["categories"] for cat in (m["category"], m["sub_category"])
                   if cat and cat["key"] == category_key]
        if not any(cat["id"] == category["id"] for cat in matched):
            raise ValueError("Record and listing category identifiers disagree")
    return {"category_key": category_key, "meta": normalized_meta, "category": category, "records": records}


def qualify_page_set(category_key, pages):
    """Fail the whole offline scope on missing/drifting/duplicate/invalid pages."""
    result = {"category_key": category_key, "complete": False, "status": "incomplete",
              "errors": [], "records": [], "total": None, "pages_expected": None,
              "pages_received": len(pages) if isinstance(pages, dict) else 0,
              "duplicates": [], "capture_sha256": {}}
    errors, parsed = result["errors"], {}
    if not isinstance(pages, dict) or not pages:
        errors.append("Missing captured pages")
        return result
    if len(pages) > MAX_CAPTURE_PAGES or any(type(n) is not int or n < 1 or n > MAX_CAPTURE_PAGES for n in pages):
        errors.append("Invalid captured page numbers or page bound exceeded")
        return result
    for number, payload in sorted(pages.items()):
        try:
            result["capture_sha256"][str(number)] = digest(payload.encode("utf-8") if isinstance(payload, str) else payload)
            parsed[number] = parse_page(payload, category_key, number)
        except (ValueError, TypeError, UnicodeError, OverflowError) as exc:
            errors.append("Page " + str(number) + ": " + str(exc))
    if 1 not in parsed:
        errors.append("Missing or invalid first page; scope cannot be qualified")
        return result
    first = parsed[1]
    total, count = first["meta"]["total"], first["meta"]["totalPages"]
    result.update(total=total, pages_expected=count)
    expected = set(range(1, count + 1))
    missing, extra = sorted(expected - set(pages)), sorted(set(pages) - expected)
    if missing:
        errors.append("Missing pages: " + ",".join(map(str, missing)))
    if extra:
        errors.append("Unexpected pages: " + ",".join(map(str, extra)))
    records = []
    for number, page in sorted(parsed.items()):
        if any(page["meta"][key] != first["meta"][key] for key in ("total", "limit", "totalPages")) or page["category"] != first["category"]:
            errors.append("Page " + str(number) + ": listing metadata drift")
        records.extend(page["records"])
    result["duplicates"] = sorted(key for key, value in Counter(r["id"] for r in records).items() if value > 1)
    if result["duplicates"]:
        errors.append("Duplicate record IDs across captured pages")
    if len(records) != total:
        errors.append("Qualified record count does not match advertised total")
    if errors:
        return result
    result.update(complete=True, status="complete", records=records)
    result["warnings"] = dict(sorted(Counter(warning for row in records for warning in row["warnings"]).items()))
    result["download_count"] = sum(len(row["downloads"]) for row in records)
    return result
