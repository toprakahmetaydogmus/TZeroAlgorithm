# -*- coding: utf-8 -*-
"""Unit tests for T-Zero Autonomous Sync, Token Cost Cockpit, and Drift Analyzer."""

import os
import json
import shutil
import tempfile
import unittest

from tzero.tzero_sync import WorkspaceSyncManager, SyncResult
from tzero.tzero_cost import TokenCostCalculator, CostReport
from tzero.tzero_drift import DriftAnalyzer, DriftReport


class TestSyncCostDrift(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="tzero_test_sync_")
        # Create a sample python file in test dir
        sample_code = '''# sample module
class PaymentProcessor:
    def process_charge(self, amount: float) -> bool:
        return amount > 0

def format_currency(val: float) -> str:
    return f"${val:.2f}"
'''
        with open(os.path.join(self.test_dir, "payments.py"), "w", encoding="utf-8") as f:
            f.write(sample_code)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_sync_manager_scan_and_sync(self):
        symbols = WorkspaceSyncManager.scan_symbols(self.test_dir)
        self.assertGreaterEqual(symbols["module_count"], 1)
        self.assertGreaterEqual(symbols["class_count"], 1)
        self.assertGreaterEqual(symbols["function_count"], 1)
        self.assertTrue(any("PaymentProcessor" in c for c in symbols["classes"]))
        self.assertTrue(any("format_currency" in f for f in symbols["functions"]))

        res = WorkspaceSyncManager.sync(self.test_dir)
        self.assertTrue(res.success)
        self.assertIn(".cursorrules", res.synced_files)
        self.assertIn("CLAUDE.md", res.synced_files)
        self.assertIn(".windsurfrules", res.synced_files)

        # Verify file content
        with open(os.path.join(self.test_dir, ".cursorrules"), "r", encoding="utf-8") as f:
            cursor_content = f.read()
            self.assertIn("PaymentProcessor", cursor_content)
            self.assertIn("format_currency", cursor_content)

        with open(os.path.join(self.test_dir, "CLAUDE.md"), "r", encoding="utf-8") as f:
            claude_content = f.read()
            self.assertIn("PaymentProcessor", claude_content)

    def test_cost_calculator(self):
        rep = TokenCostCalculator.calculate_cost(self.test_dir)
        self.assertIsInstance(rep, CostReport)
        self.assertGreater(rep.raw_tokens, 0)
        self.assertGreater(rep.tzero_pruned_tokens, 0)
        self.assertGreaterEqual(rep.tokens_saved, 0)
        self.assertGreaterEqual(len(rep.comparisons), 5)

        model_names = [c.model_name for c in rep.comparisons]
        self.assertIn("Anthropic Claude 3.5 Sonnet", model_names)
        self.assertIn("OpenAI GPT-4o", model_names)
        self.assertIn("DeepSeek V3", model_names)

        # JSON output verification
        json_str = TokenCostCalculator.to_json(rep)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["total_files"], rep.total_files)
        self.assertGreaterEqual(len(parsed["comparisons"]), 5)

    def test_drift_analyzer_clean(self):
        rep = DriftAnalyzer.analyze_workspace(self.test_dir)
        self.assertIsInstance(rep, DriftReport)
        self.assertEqual(rep.drift_score, 0.0)
        self.assertEqual(rep.adherence_pct, 100.0)
        self.assertIn("EXCELLENT", rep.snr_rating)
        self.assertEqual(len(rep.findings), 0)

    def test_drift_analyzer_violations(self):
        drift_code = '''# Drift module with violations
def risky_action():
    try:
        call_api()
    except:
        pass

def very_long_monolith_function():
''' + "\n".join(f"    x_{i} = {i}" for i in range(70)) + "\n    return x_69\n"

        with open(os.path.join(self.test_dir, "drifted.py"), "w", encoding="utf-8") as f:
            f.write(drift_code)

        rep = DriftAnalyzer.analyze_workspace(self.test_dir)
        self.assertGreater(rep.drift_score, 0.0)
        self.assertLess(rep.adherence_pct, 100.0)
        categories = [f.category for f in rep.findings]
        self.assertIn("Error Handling", categories)
        self.assertIn("Architectural Modularity", categories)

        json_str = DriftAnalyzer.to_json(rep)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["findings_count"], len(rep.findings))


if __name__ == "__main__":
    unittest.main()
