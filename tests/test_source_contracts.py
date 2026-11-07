"""No-write AMLO/DIP diagnostics regressions (synthetic and existing fixtures)."""
import json
import unittest
from pathlib import Path
import yaml

from scripts.probe_source_contracts import (
    inspect_amlo_form, inspect_dip_json, inspect_dip_public_listing,
    extended_dip_source
)

ROOT = Path(__file__).resolve().parents[1]


class SourceContractTests(unittest.TestCase):
    def test_amlo_reports_hidden_names_but_redacts_values(self):
        html = b"""<html><form method="post" action="https://www.amlo.go.th/index.php/th/">
<input name="intro_page" type="hidden" value="1">
<input name="csrf_guard" type="hidden" value="SECRET_VALUE_NEVER_LOG">
</form></html>"""
        result = inspect_amlo_form(html)
        self.assertTrue(result["contract_requires_review"])
        self.assertEqual(result["same_entry_post_form_count"], 1)
        self.assertEqual(result["forms"][0]["hidden_names"],
                         ["csrf_guard", "intro_page"])
        self.assertNotIn("SECRET_VALUE_NEVER_LOG", json.dumps(result))
        self.assertFalse(result["form_submitted"])

    def test_dip_count_drop_guard_not_weakened(self):
        sources = yaml.safe_load((ROOT / "config/sources.yml").read_text("utf-8"))["sources"]
        dip = next(s for s in sources if s["id"] == "dip-listing-01")
        fixture = (ROOT / "tests/fixtures/repairs/enforcement-dip.json").read_bytes()
        result = inspect_dip_json(fixture, dip, previous_count=13)
        self.assertEqual(result["accepted_rows"], 2)
        self.assertTrue(result["count_drop_guard_would_trigger"])
        self.assertFalse(result["retained_state_written"])
        self.assertFalse(inspect_dip_json(fixture, dip, previous_count=3)
                         ["count_drop_guard_would_trigger"])

    def test_separate_official_dip_listing_is_not_promoted(self):
        body = """<html><h1>ข่าวประชาสัมพันธ์</h1>
<p>วันศุกร์, 06 พฤศจิกายน 2569</p>
<a href="/th/dip-news.html">Same host</a>
<a href="https://example.org/test">Other host</a></html>""".encode("utf-8")
        result = inspect_dip_public_listing(body)
        self.assertTrue(result["official_listing_marker"])
        self.assertTrue(result["mentions_november_2569"])
        self.assertEqual(result["same_host_link_count"], 1)
        self.assertFalse(result["feed_contract_qualified"])

    def test_extended_dip_probe_is_scoped_to_exact_official_api(self):
        sources = yaml.safe_load((ROOT / "config/sources.yml").read_text("utf-8"))["sources"]
        dip = next(s for s in sources if s["id"] == "dip-listing-01")
        self.assertIn("per_page=100", dip["url"])
        previous = {**dip, "url": dip["url"].replace("per_page=100", "per_page=20")}
        expanded = extended_dip_source(previous)
        self.assertEqual(expanded["url"], dip["url"])
        self.assertEqual(extended_dip_source(dip)["url"], dip["url"])
        self.assertEqual(expanded["allowed_hosts"], dip["allowed_hosts"])
        self.assertTrue(expanded["url"].startswith("https://webnew.ipthailand.go.th/wp-json/wp/v2/news?"))
        self.assertRaises(ValueError, extended_dip_source, {**dip, "url": "https://example.org/wp-json/wp/v2/news?per_page=20"})

    def test_new_qualification_workflow_is_read_only(self):
        s = (ROOT / ".github/workflows/source-contract-qualification.yml").read_text("utf-8")
        workflow = yaml.load(s, Loader=yaml.BaseLoader)
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        self.assertIn("pull_request", workflow["on"])
        self.assertNotIn("git push", s)
        self.assertNotIn("actions/deploy-pages", s)
        self.assertNotIn("regwatch collect", s)

    def test_existing_amlo_and_dip_source_configurations_unchanged(self):
        by_id = {s["id"]: s for s in
                 yaml.safe_load((ROOT / "config/sources.yml").read_text("utf-8"))["sources"]}
        self.assertEqual(by_id["amlo-listing-01"]["public_form"], {"intro_page": "1"})
        self.assertEqual(by_id["dip-listing-01"]["mode"], "json")
        self.assertEqual(by_id["dip-listing-01"]["validation_status"], "verified")
        self.assertIn("per_page=100", by_id["dip-listing-01"]["url"])


if __name__ == "__main__":
    unittest.main()
