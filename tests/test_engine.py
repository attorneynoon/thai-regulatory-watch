import unittest
from regwatch.engine import empty_state, apply_observations

SOURCE = dict(id="example-news", regulator_id="example", title="Example", url="https://example.org/news", topics=["news"], jurisdiction="TH", language="th", document_type="publication", authority_class="official-publication", validation_status="candidate", enabled=True, limitations=[])
SOURCE['feed_priority']='regulatory'

class EngineTests(unittest.TestCase):
    def test_baseline_unchanged_revision_reversion(self):
        state = empty_state()
        a = dict(url="https://example.org/item/1", title="A", published_at=None)
        apply_observations(state, SOURCE, [a], "2026-09-19T01:00:00Z")
        apply_observations(state, SOURCE, [a], "2026-09-19T02:00:00Z")
        self.assertEqual(len(state["events"]), 1)
        apply_observations(state, SOURCE, [{**a, "title": "B"}], "2026-09-19T03:00:00Z")
        apply_observations(state, SOURCE, [a], "2026-09-19T04:00:00Z")
        self.assertEqual([e["event_type"] for e in state["events"]], ["BASELINE", "UPDATED", "UPDATED"])
        self.assertEqual(len({e["event_id"] for e in state["events"]}), 3)
        self.assertTrue(all(e["legal_effect"] == "Not assessed" for e in state["events"]))

if __name__ == "__main__":
    unittest.main()
