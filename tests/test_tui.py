# -*- coding: utf-8 -*-
import os
import tempfile
import unittest
from tzero_tui import TZeroTerminalCockpit


class TestTZeroTerminalCockpit(unittest.TestCase):
    """Exhaustive tests for the terminal user interface and cockpit."""

    def test_gather_workspace_metrics(self):
        metrics = TZeroTerminalCockpit.gather_workspace_metrics(".")
        self.assertIn("workspace_name", metrics)
        self.assertIn("total_files", metrics)
        self.assertIn("savings_pct", metrics)
        self.assertGreater(metrics["total_files"], 0)
        self.assertGreaterEqual(metrics["savings_pct"], 0.0)

    def test_gather_workspace_metrics_uses_real_reduction_not_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = "\n".join(
                f"def compute_{i}(x: int, y: int) -> int:\n"
                f"    acc = x + y + {i}\n"
                f"    for step in range(5):\n"
                f"        acc += step * 2\n"
                f"    return acc\n"
                for i in range(12)
            )
            with open(os.path.join(tmp, "sample.py"), "w", encoding="utf-8") as fh:
                fh.write(code)
            metrics = TZeroTerminalCockpit.gather_workspace_metrics(tmp)
            self.assertNotEqual(metrics["raw_tokens"], metrics["total_files"] * 450)
            self.assertGreater(metrics["pruned_tokens"], 0)
            self.assertLess(metrics["pruned_tokens"], metrics["raw_tokens"])
            self.assertGreater(metrics["savings_pct"], 0.0)

    def test_gather_workspace_metrics_reports_real_zero_leak_violation(self):
        with tempfile.TemporaryDirectory() as tmp:
            synthetic_tok = "sk" + "-proj-" + "99a8b7c6d5e4f3a2b1c099887766554433221100aa"
            with open(os.path.join(tmp, "leaky.py"), "w", encoding="utf-8") as fh:
                fh.write(f'API_KEY = "{synthetic_tok}"\n')
            metrics = TZeroTerminalCockpit.gather_workspace_metrics(tmp)
            self.assertNotIn("SECURE", metrics["zero_leak_status"])
            self.assertIn("WARNING", metrics["zero_leak_status"])

    def test_render_gauge(self):
        gauge_50 = TZeroTerminalCockpit.render_gauge(50.0, width=10)
        self.assertIn("50.0%", gauge_50)

        gauge_95 = TZeroTerminalCockpit.render_gauge(94.8, width=20)
        self.assertIn("94.8%", gauge_95)

    def test_render_cockpit(self):
        dummy_metrics = {
            "workspace_name": "TestWorkspace",
            "total_files": 42,
            "raw_tokens": 100000,
            "pruned_tokens": 5200,
            "savings_pct": 94.8,
            "monthly_roi_saved": 426.60,
            "zero_leak_status": "100% ZERO-LEAK PASSED",
            "languages": {"python": 30, "typescript": 12}
        }
        screen = TZeroTerminalCockpit.render_cockpit(dummy_metrics)

        self.assertIn("TestWorkspace", screen)
        self.assertIn("42", screen)
        self.assertIn("94.8%", screen)
        self.assertIn("$426.60", screen)
        self.assertIn("QUICK COMMAND DISPATCH", screen)
        self.assertIn("Pack Context Window", screen)
        self.assertIn("Generate PEP-484 Type Stubs", screen)


if __name__ == "__main__":
    unittest.main()
