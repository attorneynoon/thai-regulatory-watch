from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = ROOT / "prototypes" / "tcct-ocr-deep-analysis-v0.2" / "tests"


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


if __name__ == "__main__":
    unittest.main()
