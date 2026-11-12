"""End-to-end checks for the offline capture qualification command."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "qualify_tcct.py"
KEYS = (
    "verdict", "verdict-mergers", "draft-principles-hearing",
    "tcct-draft-laws-hearing", "giveaway-news-2569", "activity-news-2569",
)


def synthetic_page(key, *, total=1, page=1):
    """Synthetic schema fixture; titles/IDs do not represent publications."""
    def ident(label):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, "https://example.org/" + label))

    category = {
        "id": ident(key), "key": key, "name": "Synthetic category " + key,
        "parent_id": None, "is_active": True, "is_delete": False,
    }
    count = min(12, max(0, total - (page - 1) * 12))
    rows = []
    for index in range((page - 1) * 12, (page - 1) * 12 + count):
        row = {
            "id": ident(key + "/item/" + str(index)),
            "code": "SYNTHETIC-" + str(index), "document_number": None,
            "title": "Synthetic public listing " + str(index),
            "content": None, "description": None,
            "is_active": True, "is_draft": False,
            "start_date": "2026-11-12T00:00:00.000Z", "end_date": None,
            "category_id": category["id"], "sub_category_id": None,
            "category": copy.deepcopy(category), "sub_category": None,
            "categories": [{
                "id": ident(key + "/membership/" + str(index)),
                "category_id": category["id"], "sub_category_id": None,
                "sequence": 0, "category": copy.deepcopy(category),
                "sub_category": None,
            }],
            "file_list": [], "is_reference_link": False, "url_link": None,
        }
        rows.append(row)
    pages = max(1, (total + 11) // 12)
    return {
        "status": "success",
        "data": {
            "category": category, "contents": rows,
            "meta": {
                "total": total, "page": page, "limit": 12,
                "totalPages": pages, "hasNextPage": page < pages,
                "hasPreviousPage": page > 1,
            },
        },
    }


class OfflineQualificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.captures = self.directory / "captures"
        self.captures.mkdir()
        self.output = self.directory / "qualification.json"
        for key in KEYS:
            self.write_page(key, synthetic_page(key))

    def write_page(self, key, page):
        number = page["data"]["meta"]["page"]
        path = self.captures / f"{key}-page{number}.json"
        path.write_text(json.dumps(page, ensure_ascii=False), encoding="utf-8")

    def run_command(self, output=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--capture-dir", str(self.captures),
             "--output", str(output or self.output)],
            cwd=ROOT, text=True, capture_output=True, timeout=20,
        )

    def captured_hashes(self):
        return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.captures.iterdir() if p.is_file()}

    def test_all_six_complete_scopes_write_report_and_preserve_captures(self):
        # Unrelated parent probes must never be mistaken for category pages.
        (self.captures / "giveaway-news-parent-page1.json").write_text("not JSON")
        before = self.captured_hashes()
        result = self.run_command()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(self.output.read_text())
        self.assertTrue(report["complete"])
        self.assertEqual(report["qualification_kind"], "offline-capture-validation")
        self.assertEqual(report["records_qualified"], 6)
        self.assertEqual([s["category_key"] for s in report["scopes"]], list(KEYS))
        self.assertTrue(all(s["complete"] and len(s["records"]) == 1
                            for s in report["scopes"]))
        self.assertEqual(before, self.captured_hashes())

    def test_missing_last_page_fails_scope_without_partial_records(self):
        self.write_page("verdict", synthetic_page("verdict", total=13))
        result = self.run_command()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertTrue(self.output.is_file(), result.stderr)
        report = json.loads(self.output.read_text())
        self.assertFalse(report["complete"])
        scopes = {s["category_key"]: s for s in report["scopes"]}
        self.assertFalse(scopes["verdict"]["complete"])
        self.assertEqual(scopes["verdict"]["records"], [])
        self.assertTrue(scopes["verdict"]["errors"])
        self.assertTrue(scopes["verdict-mergers"]["complete"])

    def test_malformed_json_is_a_reported_noncomplete_scope(self):
        (self.captures / "verdict-page1.json").write_text('{"status":')
        before = self.captured_hashes()
        result = self.run_command()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertTrue(self.output.is_file(), result.stderr)
        report = json.loads(self.output.read_text())
        self.assertFalse(report["complete"])
        verdict = report["scopes"][0]
        self.assertFalse(verdict["complete"])
        self.assertEqual(verdict["records"], [])
        self.assertTrue(verdict["errors"])
        self.assertEqual(before, self.captured_hashes())

    def test_output_cannot_replace_a_capture(self):
        before = self.captured_hashes()
        result = self.run_command(self.captures / "verdict-page1.json")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("output-location-rejected", result.stderr)
        self.assertEqual(before, self.captured_hashes())

    def test_output_cannot_add_files_to_the_capture_directory(self):
        destination = self.captures / "new-report.json"
        result = self.run_command(destination)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("output-location-rejected", result.stderr)
        self.assertFalse(destination.exists())

    def test_symlink_output_cannot_replace_capture(self):
        target = self.captures / "verdict-page1.json"
        self.output.symlink_to(target)
        before = target.read_bytes()
        result = self.run_command()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("output-location-rejected", result.stderr)
        self.assertEqual(before, target.read_bytes())


if __name__ == "__main__":
    unittest.main()
