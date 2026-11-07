"""Guards for merging PR #15 with PR #16 and PR #17 without weakening controls."""
import unittest
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
COURT_HOSTS = {"lbrmc.coj.go.th", "cmic.coj.go.th", "crmc.coj.go.th",
               "pttc.coj.go.th", "crimsb.coj.go.th"}
NCSA = ("ncsa-listing-01", "ncsa-listing-02", "ncsa-listing-03")


class DraftIntegrationTests(unittest.TestCase):
    def test_collector_runner_and_exact_state_sha_handoff(self):
        cfg = yaml.load((ROOT / ".github/workflows/monitor.yml").read_text("utf-8"),
                        Loader=yaml.BaseLoader)
        jobs = cfg["jobs"]
        self.assertEqual(jobs["collect"]["runs-on"], "ubuntu-24.04")
        self.assertEqual(jobs["health"]["runs-on"], "ubuntu-latest")
        self.assertEqual(jobs["deploy"]["runs-on"], "ubuntu-latest")
        self.assertEqual(jobs["collect"]["outputs"]["state_sha"],
                         "${{ steps.persist.outputs.state_sha }}")
        persistence = next(s for s in jobs["collect"]["steps"]
                           if s.get("name") == "Preserve collected public state and outputs")
        self.assertEqual(persistence["id"], "persist")
        self.assertIn("git push origin HEAD:main", persistence["run"])
        checkout = next(s for s in jobs["health"]["steps"]
                        if s.get("uses", "").startswith("actions/checkout@"))
        self.assertEqual(checkout["with"]["ref"],
                         "${{ needs.collect.outputs.state_sha }}")
        self.assertNotIn("pull_request", cfg["on"])

    def test_court_hosts_and_ncsa_source_only_limits(self):
        registry = yaml.safe_load((ROOT / "config/sources.yml").read_text("utf-8"))
        sources = {s["id"]: s for s in registry["sources"]}
        courts = sources["courts-watch"]
        self.assertEqual(courts["validation_status"], "candidate")
        self.assertTrue(COURT_HOSTS.issubset(set(courts["allowed_hosts"])))
        self.assertEqual(len(courts["allowed_hosts"]), len(set(courts["allowed_hosts"])))
        for ident in NCSA:
            with self.subTest(source=ident):
                self.assertEqual(sources[ident]["max_response_bytes"], 64_000_000)
                self.assertEqual(sources[ident]["allowed_hosts"], ["www.ncsa.or.th"])
                self.assertEqual(sources[ident]["validation_status"], "verified")
        for ident, source in sources.items():
            if ident not in NCSA:
                self.assertNotEqual(source.get("max_response_bytes"), 64_000_000)

    def test_all_triggered_pr_ci_is_read_only(self):
        for name in ("ci.yml", "ncsa-qualification.yml",
                     "rendered-source-qualification.yml"):
            with self.subTest(name=name):
                source = (ROOT / ".github/workflows" / name).read_text("utf-8")
                cfg = yaml.load(source, Loader=yaml.BaseLoader)
                self.assertEqual(cfg["permissions"], {"contents": "read"})
                self.assertIn("pull_request", cfg["on"])
                self.assertNotIn("git push origin", source)
                self.assertNotIn("actions/deploy-pages@", source)

if __name__ == "__main__":
    unittest.main()
