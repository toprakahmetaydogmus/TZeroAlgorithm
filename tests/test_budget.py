# -*- coding: utf-8 -*-
"""Unit tests for T-Zero Autonomous AST Token Budget Enforcer (tzero_budget.py)."""

import os
import unittest
from tzero_budget import ASTTokenBudgetOptimizer, CompressionCertificate


class TestASTTokenBudgetOptimizer(unittest.TestCase):
    def test_estimate_raw_tokens(self):
        tokens, count, content_hash = ASTTokenBudgetOptimizer.estimate_raw_tokens("tests", max_files=10)
        self.assertGreater(tokens, 0)
        self.assertGreater(count, 0)
        self.assertEqual(len(content_hash), 64)

    def test_optimize_budget_large(self):
        # With a very large budget (e.g. 10,000,000), Tier 1 should be selected
        cert = ASTTokenBudgetOptimizer.optimize_budget("tests", target_tokens=10_000_000)
        self.assertTrue(cert.fits_budget)
        self.assertIn("Tier 1", cert.tier_applied)
        self.assertGreater(cert.savings_percentage, 0.0)
        self.assertEqual(len(cert.sha256_checksum), 64)

    def test_optimize_budget_small(self):
        # With a tiny budget (e.g. 10 tokens), Tier 4 should be selected
        cert = ASTTokenBudgetOptimizer.optimize_budget("tests", target_tokens=10)
        self.assertIn("Tier 4", cert.tier_applied)

    def test_save_and_format_certificate(self):
        cert = ASTTokenBudgetOptimizer.optimize_budget("tests", target_tokens=50_000, model_name="claude-3-7")
        md = ASTTokenBudgetOptimizer.format_markdown_certificate(cert)
        self.assertIn("T-Zero Context Budget & Compression Certificate", md)
        self.assertIn("claude-3-7", md)

        out_path = os.path.join("tests", ".test_cert.json")
        try:
            saved_p = ASTTokenBudgetOptimizer.save_certificate(cert, out_path)
            self.assertTrue(os.path.exists(saved_p))
        finally:
            if os.path.exists(out_path):
                os.remove(out_path)


if __name__ == "__main__":
    unittest.main()

