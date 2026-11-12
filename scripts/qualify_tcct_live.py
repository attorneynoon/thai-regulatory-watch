#!/usr/bin/env python3
"""Qualify TCCT listings with production transport and disposable in-memory state.

This command never reads or writes monitor state, generated feeds, or schemas.
PDF bytes are outside this listing-only qualification; their metadata is retained.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from regwatch.collector import collect_source
from regwatch.engine import empty_state
from regwatch.models import utcnow
from regwatch.registry import load_registry
from regwatch.tcct_api import ENDPOINT, PAGE_LIMIT, _decode, request_payload
from regwatch.transport import Transport

CATEGORY_KEYS = (
    "verdict", "verdict-mergers", "draft-principles-hearing",
    "tcct-draft-laws-hearing", "giveaway-news-2569", "activity-news-2569",
    "giveaway-news", "activity-news",
)


def _public_fields(value, fields):
    """Select scalar evidence explicitly; never recursively export source data."""
    if not isinstance(value, dict):
        return {"invalid_type": type(value).__name__}
    result = {}
    for key in fields:
        if key not in value:
            continue
        raw = value[key]
        if isinstance(raw, str):
            result[key] = raw[:600]
            if len(raw) > 600:
                result.setdefault("truncated_fields", []).append(key)
        elif raw is None or type(raw) in (bool, int):
            result[key] = raw
        else:
            result[key] = {"invalid_type": type(raw).__name__}
    return result


def _taxonomy(value):
    if value is None:
        return None
    return _public_fields(value, ("id", "key", "parent_id", "is_active", "is_delete"))


def taxonomy_projection(payload, category_key, page_number):
    """Public taxonomy only. This deliberately cannot qualify a record or page."""
    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    data = data if isinstance(data, dict) else {}
    listing = data.get("category")
    listing = listing if isinstance(listing, dict) else {}
    output = {"category_key": category_key, "page": page_number,
              "category": _taxonomy(data.get("category")),
              "meta": _public_fields(data.get("meta"), (
                  "total", "page", "limit", "totalPages", "hasNextPage", "hasPreviousPage")),
              "records": []}
    records = data.get("contents")
    if not isinstance(records, list):
        output["projection_error"] = "contents is not an array"
        return output
    if len(records) > PAGE_LIMIT:
        output["projection_truncated"] = True
    for raw in records[:PAGE_LIMIT]:
        if not isinstance(raw, dict):
            output["records"].append({"invalid_type": type(raw).__name__, "issues": ["record is not an object"]})
            continue
        row = _public_fields(raw, ("id", "title", "code", "category_id", "sub_category_id"))
        row.update(category=_taxonomy(raw.get("category")), sub_category=_taxonomy(raw.get("sub_category")),
                   categories=[], issues=[])
        primary = raw.get("category") if isinstance(raw.get("category"), dict) else {}
        sub = raw.get("sub_category") if isinstance(raw.get("sub_category"), dict) else {}
        if raw.get("category_id") != primary.get("id"):
            row["issues"].append("primary category_id differs from category.id")
        if raw.get("sub_category_id") != sub.get("id"):
            row["issues"].append("primary sub_category_id differs from sub_category.id")
        if sub and sub.get("parent_id") != raw.get("category_id"):
            row["issues"].append("primary sub_category.parent_id differs from category_id")
        members = raw.get("categories")
        if not isinstance(members, list):
            row["issues"].append("categories is not an array")
            members = []
        if len(members) > 32:
            row["projection_truncated"] = True
        matched_listing = False
        for index, member in enumerate(members[:32]):
            if not isinstance(member, dict):
                row["categories"].append({"invalid_type": type(member).__name__})
                row["issues"].append(f"categories[{index}] is not an object")
                continue
            selected = _public_fields(member, ("id", "category_id", "sub_category_id", "sequence"))
            selected.update(category=_taxonomy(member.get("category")), sub_category=_taxonomy(member.get("sub_category")))
            row["categories"].append(selected)
            category = member.get("category") if isinstance(member.get("category"), dict) else {}
            child = member.get("sub_category") if isinstance(member.get("sub_category"), dict) else {}
            if member.get("category_id") != category.get("id"):
                row["issues"].append(f"categories[{index}].category_id differs from category.id")
            if member.get("sub_category_id") != child.get("id"):
                row["issues"].append(f"categories[{index}].sub_category_id differs from sub_category.id")
            if child and child.get("parent_id") != member.get("category_id"):
                row["issues"].append(f"categories[{index}].sub_category.parent_id differs from category_id")
            for label, item in (("category", category), ("sub_category", child)):
                if not item:
                    continue
                if "parent_id" not in item:
                    row["issues"].append(f"categories[{index}].{label}.parent_id is missing")
                if item.get("is_active") is not True or item.get("is_delete") is not False:
                    row["issues"].append(f"categories[{index}].{label} is inactive or deleted")
                if item.get("key") == category_key and item.get("id") == listing.get("id"):
                    matched_listing = True
        if not matched_listing:
            row["issues"].append("requested listing category identifier absent from memberships")
        output["records"].append(row)
    return output


class DiagnosticTransport(Transport):
    """Use ordinary transport and keep only a bounded taxonomy projection."""
    def __init__(self, source):
        super().__init__(source["allowed_hosts"])
        self.category_key = source["tcct_category_key"]
        self.max_pages = min(source.get("max_pages", 1), 50)
        self.max_items = min(source.get("max_items", 100), 1000)
        self.max_bytes = min(source.get("max_response_bytes", 4_000_000), 4_000_000)
        self.last_projection = None
        self.pages_inspected = []
        self.anomalies = []
        self.first_meta = None
        self.first_category = None
        self.continuation_error = None
        self.last_api_request = None

    def _inspect(self, payload, page_number):
        projected = taxonomy_projection(payload, self.category_key, page_number)
        self.last_projection = projected
        self.pages_inspected.append(page_number)
        self.anomalies.extend({"page": page_number, "record": row}
                              for row in projected["records"] if row.get("issues"))
        data = payload.get("data")
        if not isinstance(data, dict) or payload.get("status") != "success":
            self.continuation_error = "Invalid diagnostic response envelope"
            return
        meta = data.get("meta")
        if not isinstance(meta, dict) or any(type(meta.get(key)) is not int for key in ("total", "page", "limit", "totalPages")):
            self.continuation_error = "Invalid diagnostic pagination metadata"
            return
        total, pages = meta["total"], meta["totalPages"]
        if total > self.max_items or pages > self.max_pages:
            self.continuation_error = "Advertised diagnostic page/item bound exceeded"
            return
        category = projected["category"]
        rows = data.get("contents")
        if (total < 1 or pages < 1 or meta["limit"] != PAGE_LIMIT or meta["page"] != page_number
                or pages != (total + PAGE_LIMIT - 1) // PAGE_LIMIT or page_number > pages
                or type(meta.get("hasNextPage")) is not bool or meta["hasNextPage"] != (page_number < pages)
                or type(meta.get("hasPreviousPage")) is not bool or meta["hasPreviousPage"] != (page_number > 1)
                or not isinstance(rows, list) or len(rows) != min(PAGE_LIMIT, total - (page_number - 1) * PAGE_LIMIT)
                or not isinstance(category, dict) or category.get("key") != self.category_key):
            self.continuation_error = "Invalid diagnostic pagination or category metadata"
            return
        identity = {key: meta[key] for key in ("total", "limit", "totalPages")}
        if page_number == 1:
            self.first_meta, self.first_category = identity, category
        elif identity != self.first_meta or category != self.first_category:
            self.continuation_error = "Diagnostic pagination/category metadata drift"

    def fetch(self, url, **kwargs):
        request = kwargs.get("json_body")
        is_listing = url == ENDPOINT and isinstance(request, dict)
        if is_listing:
            self.last_api_request = {"category_key": request.get("category_key"), "page_number": request.get("page_number")}
            self.last_projection = None
        try:
            response = super().fetch(url, **kwargs)
        except Exception as exc:
            if is_listing:
                self.continuation_error = str(exc)[:250]
            raise
        if is_listing:
            status, headers, body, final = response
            try:
                if (status not in (200, 201) or final != ENDPOINT
                        or headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json"):
                    raise ValueError("Unexpected response contract")
                self._inspect(_decode(body), request["page_number"])
            except (ValueError, TypeError, UnicodeError, OverflowError, KeyError):
                self.continuation_error = "Response cannot be projected as bounded JSON taxonomy"
        return response

    def diagnose_failure(self):
        failed_request = deepcopy(self.last_api_request)
        failed_page = deepcopy(self.last_projection)
        if not self.continuation_error and self.first_meta:
            for page in range(1, self.first_meta["totalPages"] + 1):
                if page in self.pages_inspected:
                    continue
                try:
                    self.fetch(ENDPOINT, json_body=request_payload(self.category_key, page), max_bytes=self.max_bytes)
                except Exception:
                    break  # Access failures are not retried or bypassed.
                if self.continuation_error:
                    break
        elif not self.continuation_error:
            self.continuation_error = "No valid first-page metadata for diagnostic continuation"
        return {"qualifies_scope": False, "purpose": "taxonomy evidence only; original qualification remains failed",
                "failed_request": failed_request, "failed_page": failed_page,
                "advertised_meta": self.first_meta, "pages_inspected": list(self.pages_inspected),
                "anomalies": deepcopy(self.anomalies), "continuation_error": self.continuation_error}


def qualify_sources(sources, category_keys, *, collector=collect_source, root=ROOT,
                    diagnose_taxonomy=False, transport_factory=None):
    keys = list(dict.fromkeys(category_keys))
    if not keys or any(key not in CATEGORY_KEYS for key in keys):
        raise ValueError("Only explicitly observed TCCT category keys may be qualified")
    selected = {}
    for key in keys:
        matches = [source for source in sources
                   if source.get("mode") == "tcct-api"
                   and source.get("regulator_id") == "tcct"
                   and source.get("tcct_category_key") == key]
        if not matches:
            raise ValueError("No TCCT API source configured for " + key)
        selected[key] = matches
    now = utcnow()
    result = {"qualified_at": now, "complete": True,
              "scope": "current API listing traversal; publisher archive completeness unassessed",
              "production_state_reads": 0, "production_state_writes": 0,
              "pdf_bytes_qualified": False, "scopes": []}
    for key in keys:
        matches = selected[key]
        candidate = deepcopy(matches[0])
        candidate["asset_budget"] = 0
        state = empty_state()
        transport = None
        if transport_factory is not None or diagnose_taxonomy:
            transport = (transport_factory or DiagnosticTransport)(candidate)
        kwargs = {"root": root}
        if transport is not None:
            kwargs["transport"] = transport
        source_result = collector(state, candidate, now, **kwargs)
        count = source_result.get("last_count", 0)
        observations = source_result.get("observations", {})
        pages = source_result.get("listing_pages_checked", 0)
        complete = (
            source_result.get("status") == "healthy"
            and type(count) is int and count > 0
            and isinstance(observations, dict) and len(observations) == count
            and type(pages) is int and pages > 0
            and source_result.get("pagination_truncated") is False
        )
        error = source_result.get("last_error")
        if not complete and not error:
            error = "Incomplete listing or inconsistent observation count"
        scope = {
            "category_key": key, "source_id": candidate["id"],
            "configured_source_ids": [source["id"] for source in matches],
            "status": source_result.get("status"), "complete": complete,
            "records": count, "distinct_observations": len(observations),
            "pages": pages, "error": error,
        }
        if diagnose_taxonomy and not complete:
            scope["taxonomy_diagnostic"] = transport.diagnose_failure()
        result["scopes"].append(scope)
        result["complete"] = result["complete"] and complete
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", choices=CATEGORY_KEYS, action="append")
    parser.add_argument("--diagnose-taxonomy", action="store_true",
                        help="After failed qualification, inspect bounded remaining pages for public taxonomy evidence only")
    args = parser.parse_args(argv)
    try:
        result = qualify_sources(load_registry(ROOT / "config" / "sources.yml"),
                                 args.category or CATEGORY_KEYS, diagnose_taxonomy=args.diagnose_taxonomy)
    except Exception as exc:
        print(json.dumps({"complete": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
