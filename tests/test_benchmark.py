# -*- coding: utf-8 -*-
"""
Tests for T-Zero Autonomous Benchmark & Performance Optimization Engine.
"""

import os
import unittest
import tempfile
import shutil

from tzero_benchmark import TZeroBenchmarkEngine, JarvisBenchmarkOptimizer, BenchmarkReport
from tzero_jarvis.orchestrator import JarvisOrchestrator


class TestTZeroBenchmark(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.file1 = os.path.join(self.test_dir, "service.py")
        with open(self.file1, "w", encoding="utf-8") as f:
            f.write("""
def calculate_tax(amount: float, rate: float = 0.20) -> float:
    \"\"\"Calculates VAT on transaction.\"\"\"
    if amount < 0:
        raise ValueError("Invalid amount")
    return amount * rate

class BillingManager:
    def process_invoice(self, user_id: str, items: list) -> dict:
        total = sum(i['price'] for i in items)
        tax = calculate_tax(total)
        return {"user_id": user_id, "total": total + tax}
""")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_run_benchmark(self):
        rep = TZeroBenchmarkEngine.run_benchmark(self.test_dir)
        self.assertIsInstance(rep, BenchmarkReport)
        self.assertEqual(rep.version, "10.7.0")
        self.assertGreater(rep.raw_tokens, 0)
        self.assertGreater(rep.tzero_tokens, 0)
        self.assertGreater(rep.reduction_pct, 50.0)
        self.assertEqual(len(rep.tiers), 3)
        self.assertEqual(len(rep.models), 4)

    def test_markdown_and_svg_generation(self):
        rep = TZeroBenchmarkEngine.run_benchmark(self.test_dir)
        md = TZeroBenchmarkEngine.export_markdown_table(rep)
        self.assertIn("Frontier LLM Token Reduction & Financial ROI Matrix", md)
        self.assertIn("Claude 3.5 Sonnet", md)

        svg_out = os.path.join(self.test_dir, "test_terminal.svg")
        res_p = TZeroBenchmarkEngine.generate_animated_svg(rep, output_file=svg_out)
        self.assertTrue(os.path.exists(res_p))
        with open(res_p, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("<svg", content)
        self.assertIn("toprak@macbook-pro", content)

    def test_jarvis_auto_tuner(self):
        tuning = JarvisBenchmarkOptimizer.auto_tune_context(self.test_dir, target_token_budget=16000)
        self.assertIn("status", tuning)
        self.assertEqual(tuning["status"], "OPTIMAL")
        self.assertIn("selected_tier", tuning)
        self.assertIn("recommendation", tuning)

    def test_jarvis_orchestrator_benchmark_call(self):
        orch = JarvisOrchestrator(workspace_root=self.test_dir)
        res = orch.run_autonomous_benchmark(target_budget=32000)
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("version"), "10.7.0")
        self.assertIn("tuning", res)


if __name__ == "__main__":
    unittest.main()
