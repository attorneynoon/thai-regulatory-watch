from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = ROOT / "prototypes" / "tcct-ocr-deep-analysis-v0.2" / "tests"
SMOKE_WORKFLOW = ROOT / ".github" / "workflows" / "tcct-public-gemini-smoke.yml"


class TCCTDecisionIntelligenceV02ContractTests(unittest.TestCase):
    def test_node_contract_suite(self) -> None:
        test_files = sorted(str(path) for path in TEST_DIR.glob("*.test.mjs"))
        self.assertTrue(test_files, "No v0.2 Node contract tests were found")
        result = subprocess.run(
            ["node", "--test", *test_files],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f"Node contract suite failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}",
        )

    def test_live_smoke_requires_explicit_label_and_protected_environment(self) -> None:
        workflow = SMOKE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("types: [labeled]", workflow)
        self.assertIn("github.event.label.name == 'run-public-gemini-smoke'", workflow)
        self.assertIn("environment: tcct-public-smoke", workflow)
        self.assertNotIn("    paths:\n", workflow)
        self.assertIn("github.event.pull_request.head.repo.full_name == github.repository", workflow)


if __name__ == "__main__":
    unittest.main()
