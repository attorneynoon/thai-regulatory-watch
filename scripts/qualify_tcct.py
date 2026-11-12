#!/usr/bin/env python3
"""Qualify saved TCCT category responses without fetching or changing monitoring state.

Run with an existing directory containing ``CATEGORY-pageN.json`` captures.
The JSON report must be written outside both the repository and capture directory.
Exit 0 means all six saved page sets passed; it does not establish live availability,
publication completeness beyond the API totals, or production source recovery.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    captures = args.capture_dir.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if output.is_relative_to(captures) or output.is_relative_to(ROOT):
        print(json.dumps({
            "error": "output-location-rejected",
            "message": "Output must be outside the capture directory and repository.",
        }), file=sys.stderr)
        return 2
    if not captures.is_dir():
        print(json.dumps({"error": "capture-directory-missing"}), file=sys.stderr)
        return 2

    from regwatch.tcct_api import CATEGORIES, qualify_page_set

    scopes = []
    for key in CATEGORIES:
        pages, read_errors = {}, []
        pattern = re.compile(re.escape(key) + r"-page([0-9]+)\.json")
        for path in sorted(captures.iterdir()):
            match = pattern.fullmatch(path.name)
            if match is None:
                continue
            page_number = int(match.group(1))
            if page_number in pages:
                read_errors.append(f"Duplicate capture filename for page {page_number}")
                continue
            try:
                pages[page_number] = path.read_bytes()
            except OSError as exc:
                read_errors.append(f"{path.name}: cannot read capture ({type(exc).__name__})")
        result = qualify_page_set(key, pages)
        if read_errors:
            result.update(complete=False, status="incomplete", records=[])
            result["errors"].extend(read_errors)
        scopes.append(result)

    report = {
        "schema_version": "1.0",
        "qualification_kind": "offline-capture-validation",
        "complete": all(scope["complete"] for scope in scopes),
        "records_qualified": sum(len(scope["records"]) for scope in scopes),
        "scopes": scopes,
        "limitations": [
            "Saved responses only; this command makes no network requests.",
            "Complete means consistency with the saved API pagination contract and totals.",
            "No production collector, registry, state, validation label or site is changed.",
            "Document and reference URLs are not dereferenced or independently qualified.",
        ],
    }
    temporary = None
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output.parent,
            prefix=".tcct-qualification-", suffix=".json", delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, output)
    except OSError as exc:
        print(json.dumps({"error": "report-write-failed", "kind": type(exc).__name__}),
              file=sys.stderr)
        return 2
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

    print(json.dumps({
        "complete": report["complete"],
        "scopes_complete": sum(scope["complete"] for scope in scopes),
        "scopes_expected": len(CATEGORIES),
        "records_qualified": report["records_qualified"],
    }, sort_keys=True))
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
