# -*- coding: utf-8 -*-
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
