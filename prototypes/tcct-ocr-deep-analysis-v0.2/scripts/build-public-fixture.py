from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
SOURCE_HTML = ROOT / "fixtures" / "public-tcct-shipping-choice.html"
WORK = ROOT / "smoke-work"
PNG_PATH = WORK / "public-tcct-shipping-choice.png"
PDF_PATH = WORK / "public-tcct-shipping-choice-scanned.pdf"
META_PATH = WORK / "fixture-metadata.json"


def main() -> None:
    if not SOURCE_HTML.exists():
        raise SystemExit(f"Missing public fixture HTML: {SOURCE_HTML}")

    WORK.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1240, "height": 1754}, device_scale_factor=1)
        page.goto(SOURCE_HTML.as_uri(), wait_until="load")
        page.evaluate("document.fonts.ready")
        dimensions = page.evaluate(
            "({width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight})"
        )
        if dimensions["width"] > 1240 or dimensions["height"] > 1754:
            raise RuntimeError(f"Fixture overflows one page: {dimensions}")
        page.screenshot(path=str(PNG_PATH), type="png", full_page=False)

        encoded = base64.b64encode(PNG_PATH.read_bytes()).decode("ascii")
        image_page = browser.new_page(viewport={"width": 1240, "height": 1754}, device_scale_factor=1)
        image_page.set_content(
            "<!doctype html><html><head><meta charset='utf-8'><style>"
            "@page{size:A4;margin:0}html,body{margin:0;width:100%;height:100%;overflow:hidden}"
            "img{display:block;width:100%;height:100%;object-fit:contain}"
            "</style></head><body>"
            f"<img alt='' src='data:image/png;base64,{encoded}'>"
            "</body></html>",
            wait_until="load",
        )
        image_page.pdf(
            path=str(PDF_PATH),
            width="210mm",
            height="297mm",
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            print_background=True,
            prefer_css_page_size=True,
        )
        browser.close()

    raw = PDF_PATH.read_bytes()
    if not raw.startswith(b"%PDF-"):
        raise RuntimeError("Generated fixture is not a PDF")
    if len(raw) > 8_000_000:
        raise RuntimeError(f"Fixture exceeds smoke-test size bound: {len(raw)} bytes")

    metadata = {
        "fixtureType": "PUBLIC_DERIVED_SCANNED_PDF",
        "publicSource": True,
        "imageOnlyIntent": True,
        "underlyingDecisionDateBE": "12 มิถุนายน 2568",
        "sourceScope": "Condensed public facts for OCR and analysis smoke testing; not the full ruling",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "pages": 1,
        "expectedFacts": [
            "multi-carrier arrangement",
            "20 June 2567 carrier-change request",
            "3.3 kilometre allegation",
            "approximately 600 metre finding",
            "dominance not reached after pleaded conduct failed",
        ],
    }
    META_PATH.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False))


if __name__ == "__main__":
    main()
