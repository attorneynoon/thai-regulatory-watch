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

CATEGORY_KEYS = (
    "verdict", "verdict-mergers", "draft-principles-hearing",
    "tcct-draft-laws-hearing", "giveaway-news-2569", "activity-news-2569",
    "giveaway-news", "activity-news",
)


def qualify_sources(sources, category_keys, *, collector=collect_source, root=ROOT):
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
        source_result = collector(state, candidate, now, root=root)
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
        result["scopes"].append({
            "category_key": key, "source_id": candidate["id"],
            "configured_source_ids": [source["id"] for source in matches],
            "status": source_result.get("status"), "complete": complete,
            "records": count, "distinct_observations": len(observations),
            "pages": pages, "error": error,
        })
        result["complete"] = result["complete"] and complete
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", choices=CATEGORY_KEYS, action="append")
    args = parser.parse_args(argv)
    try:
        result = qualify_sources(load_registry(ROOT / "config" / "sources.yml"),
                                 args.category or CATEGORY_KEYS)
    except Exception as exc:
        print(json.dumps({"complete": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
