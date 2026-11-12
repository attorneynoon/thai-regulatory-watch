"""Read-only qualification must never use retained state to mask a failed fetch."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("tcct_live_qualification", ROOT / "scripts" / "qualify_tcct_live.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def source(key, sid="tcct-test"):
    return {"id": sid, "regulator_id": "tcct", "mode": "tcct-api",
            "tcct_category_key": key, "asset_budget": 3}


def successful_collector(state, selected, now, **kwargs):
    assert state["items"] == {}
    assert state["events"] == []
    return {"status": "healthy", "last_count": 2, "listing_pages_checked": 1,
            "pagination_truncated": False,
            "observations": {"first": {}, "second": {}}, "last_error": None}


class LiveQualificationTests(unittest.TestCase):
    def test_missing_or_unknown_scope_fails_before_network(self):
        calls = []
        for sources, keys in [([], ["verdict"]), ([source("verdict")], ["unverified-key"])]:
            with self.subTest(keys=keys):
                with self.assertRaises(ValueError):
                    MODULE.qualify_sources(sources, keys, collector=lambda *a, **k: calls.append(a))
        self.assertEqual(calls, [])

    def test_duplicate_registry_scopes_are_qualified_once(self):
        calls = []
        def collect(state, selected, now, **kwargs):
            calls.append(selected["id"])
            return successful_collector(state, selected, now, **kwargs)
        result = MODULE.qualify_sources(
            [source("verdict", "tcct-first"), source("verdict", "tcct-second")],
            ["verdict", "verdict"], collector=collect)
        self.assertTrue(result["complete"])
        self.assertEqual(calls, ["tcct-first"])
        self.assertEqual(result["scopes"][0]["configured_source_ids"], ["tcct-first", "tcct-second"])

    def test_attachment_budget_is_zero_without_mutating_registry(self):
        selected = source("verdict")
        def collect(state, candidate, now, **kwargs):
            self.assertEqual(candidate["asset_budget"], 0)
            self.assertEqual(kwargs["root"], ROOT)
            return successful_collector(state, candidate, now, **kwargs)
        result = MODULE.qualify_sources([selected], ["verdict"], collector=collect, root=ROOT)
        self.assertTrue(result["complete"])
        self.assertEqual(selected["asset_budget"], 3)
        self.assertFalse(result["pdf_bytes_qualified"])

    def test_blocked_scope_is_not_a_successful_inventory(self):
        def blocked(*args, **kwargs):
            return {"status": "blocked", "last_count": 0, "observations": {},
                    "last_error": "Access unavailable: HTTP 403"}
        result = MODULE.qualify_sources([source("verdict")], ["verdict"], collector=blocked)
        self.assertFalse(result["complete"])
        self.assertEqual(result["scopes"][0]["status"], "blocked")
        self.assertIn("403", result["scopes"][0]["error"])

    def test_healthy_with_collapsed_items_or_truncated_pages_is_not_complete(self):
        for change in [{"last_count": 3}, {"pagination_truncated": True}, {"listing_pages_checked": 0}]:
            def incomplete(state, selected, now, **kwargs):
                return {**successful_collector(state, selected, now, **kwargs), **change}
            with self.subTest(change=change):
                result = MODULE.qualify_sources([source("verdict")], ["verdict"], collector=incomplete)
                self.assertFalse(result["complete"])

    def test_each_scope_starts_with_empty_ephemeral_state(self):
        calls = []
        def collect(state, selected, now, **kwargs):
            self.assertEqual(state["items"], {})
            calls.append(selected["tcct_category_key"])
            state["items"]["temporary"] = {}
            return {"status": "healthy", "last_count": 1, "listing_pages_checked": 1,
                    "observations": {"temporary": {}}, "pagination_truncated": False}
        result = MODULE.qualify_sources(
            [source("verdict"), source("verdict-mergers", "tcct-mergers")],
            ["verdict", "verdict-mergers"], collector=collect)
        self.assertTrue(result["complete"])
        self.assertEqual(calls, ["verdict", "verdict-mergers"])


if __name__ == "__main__":
    unittest.main()
