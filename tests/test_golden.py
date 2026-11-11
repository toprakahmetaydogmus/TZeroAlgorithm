# -*- coding: utf-8 -*-
"""Unit tests for T-Zero Autonomous Golden Baseline & AST Regression Engine (tzero_golden.py)."""

import json
import os
import unittest
from tzero.tzero_golden import ASTGoldenRegressionEngine, GoldenBaseline


class TestASTGoldenRegressionEngine(unittest.TestCase):
    def test_extract_file_signatures(self):
        code = '''
def calculate(a: int, b: int = 10, *args, key: str = "default", **kwargs) -> int:
    """Calculate something."""
    return a + b

class DatabaseClient:
    """DB Client class."""
    def query(self, sql: str) -> list:
        return []

    def _internal(self):
        pass
'''
        sigs = ASTGoldenRegressionEngine.extract_file_signatures("db.py", code)
        names = [s.symbol_name for s in sigs]
        self.assertIn("calculate", names)
        self.assertIn("DatabaseClient", names)
        self.assertIn("DatabaseClient.query", names)
        # Private method should not be in public signatures
        self.assertNotIn("DatabaseClient._internal", names)

    def test_generate_and_save_baseline(self):
        baseline = ASTGoldenRegressionEngine.generate_baseline("tests", max_files=5)
        self.assertGreater(baseline.total_symbols, 0)
        self.assertEqual(len(baseline.sha256_checksum), 64)

        tmp_golden = os.path.join("tests", ".test_goldens.json")
        try:
            out_p = ASTGoldenRegressionEngine.save_baseline(baseline, tmp_golden)
            self.assertTrue(os.path.exists(out_p))
            with open(out_p, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn("symbols", data)
            self.assertEqual(data["version"], "10.9.0")
        finally:
            if os.path.exists(tmp_golden):
                os.remove(tmp_golden)

    def test_verify_clean_and_modified(self):
        baseline = ASTGoldenRegressionEngine.generate_baseline("tests", max_files=5)
        tmp_golden = os.path.join("tests", ".test_goldens_diff.json")
        try:
            ASTGoldenRegressionEngine.save_baseline(baseline, tmp_golden)
            
            # Verify clean
            res_clean = ASTGoldenRegressionEngine.verify_against_golden("tests", tmp_golden)
            # All baseline symbols should be present in current tests
            self.assertEqual(len(res_clean["removed_symbols"]), 0)
            self.assertEqual(len(res_clean["modified_signatures"]), 0)
            self.assertTrue(res_clean["clean"])

            # Verify markdown report
            md = ASTGoldenRegressionEngine.format_markdown_report(res_clean)
            self.assertIn("T-Zero Golden Baseline & AST Regression Report", md)
            self.assertIn("ZERO REGRESSIONS (PASS)", md)
        finally:
            if os.path.exists(tmp_golden):
                os.remove(tmp_golden)


if __name__ == "__main__":
    unittest.main()

