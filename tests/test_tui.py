# -*- coding: utf-8 -*-
import os
import tempfile
import unittest
from tzero.tzero_tui import TZeroTerminalCockpit


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

    def test_render_cockpit_displays_dynamic_zero_leak_warning(self):
        warn_metrics = {
            "workspace_name": "LeakyWS",
            "total_files": 5,
            "raw_tokens": 1000,
            "pruned_tokens": 200,
            "savings_pct": 80.0,
            "monthly_roi_saved": 12.0,
            "zero_leak_status": "WARNING: 2 SECRET(S)",
            "languages": {"python": 5},
        }
        screen = TZeroTerminalCockpit.render_cockpit(warn_metrics)
        self.assertIn("WARNING: 2 SECRET(S)", screen)
        self.assertNotIn("100% ZERO-LEAK PASSED", screen)

    def test_gather_workspace_metrics_samples_code_beyond_250_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(260):
                with open(os.path.join(tmp, f"00_asset_{i:03d}.txt"), "w", encoding="utf-8") as fh:
                    fh.write("asset\n")
            code = "\n".join(
                f"def fn_{i}(a: int, b: int) -> int:\n    res = a + b + {i}\n    return res\n"
                for i in range(10)
            )
            with open(os.path.join(tmp, "zz_module.py"), "w", encoding="utf-8") as fh:
                fh.write(code)
            metrics = TZeroTerminalCockpit.gather_workspace_metrics(tmp)
            self.assertGreater(metrics["raw_tokens"], 0)
            self.assertGreater(metrics["savings_pct"], 0.0)

    def test_menu_wrap_around_and_navigation(self):
        menu_len = len(TZeroTerminalCockpit.MENU_OPTIONS)
        self.assertEqual(menu_len, 12)
        # Wrap up from top to bottom
        top_idx = 0
        wrap_up = (top_idx - 1) % menu_len
        self.assertEqual(wrap_up, menu_len - 1)
        self.assertEqual(TZeroTerminalCockpit.MENU_OPTIONS[wrap_up][0], "0")

        # Wrap down from bottom to top
        bottom_idx = menu_len - 1
        wrap_down = (bottom_idx + 1) % menu_len
        self.assertEqual(wrap_down, 0)
        self.assertEqual(TZeroTerminalCockpit.MENU_OPTIONS[wrap_down][0], "1")

    def test_render_cockpit_with_selection(self):
        dummy_metrics = {
            "workspace_name": "TestWorkspace",
            "total_files": 10,
            "raw_tokens": 5000,
            "pruned_tokens": 500,
            "savings_pct": 90.0,
            "monthly_roi_saved": 50.0,
            "zero_leak_status": "100% SECURE (VERIFIED)",
            "languages": {"python": 10}
        }
        # Top item highlighted
        screen_top = TZeroTerminalCockpit.render_cockpit(dummy_metrics, selected_index=0)
        self.assertIn("▶", screen_top)
        self.assertIn("Pack Context Window", screen_top)

        # Bottom item (Exit TUI) highlighted
        screen_bottom = TZeroTerminalCockpit.render_cockpit(dummy_metrics, selected_index=11)
        self.assertIn("▶", screen_bottom)
        self.assertIn("Exit TUI", screen_bottom)

    def test_execute_action_exit_codes(self):
        self.assertFalse(TZeroTerminalCockpit.execute_action("0"))
        self.assertFalse(TZeroTerminalCockpit.execute_action("q"))
        self.assertFalse(TZeroTerminalCockpit.execute_action("Q"))
        self.assertFalse(TZeroTerminalCockpit.execute_action("exit"))
        self.assertFalse(TZeroTerminalCockpit.execute_action("quit"))

    def test_visual_width_calculation(self):
        self.assertEqual(TZeroTerminalCockpit.visual_width("Hello World"), 11)
        self.assertEqual(TZeroTerminalCockpit.visual_width("\033[32mHello\033[0m"), 5)
        # Emojis occupy 2 visual columns
        self.assertEqual(TZeroTerminalCockpit.visual_width("⚡"), 2)
        self.assertEqual(TZeroTerminalCockpit.visual_width("🗜️"), 2)

    def test_render_cockpit_exact_box_alignment(self):
        metrics_cases = [
            {},
            {
                "workspace_name": "TestWorkspaceWithALongName",
                "total_files": 482,
                "raw_tokens": 11011279,
                "pruned_tokens": 1321353,
                "savings_pct": 88.0,
                "monthly_roi_saved": 2150.80,
                "zero_leak_status": "100% SECURE (VERIFIED)",
                "languages": {"python": 350, "typescript": 80, "json": 52},
            },
            {
                "workspace_name": "Minimal",
                "total_files": 1,
                "raw_tokens": 100,
                "pruned_tokens": 10,
                "savings_pct": 90.0,
                "monthly_roi_saved": 0.05,
                "zero_leak_status": "WARNING: 1 SECRET(S)",
                "languages": {},
            },
        ]
        for m in metrics_cases:
            for sel_idx in range(len(TZeroTerminalCockpit.MENU_OPTIONS)):
                screen = TZeroTerminalCockpit.render_cockpit(m, selected_index=sel_idx)
                lines = screen.split("\n")
                self.assertGreater(len(lines), 15)
                for line in lines:
                    vw = TZeroTerminalCockpit.visual_width(line)
                    self.assertEqual(
                        vw,
                        80,
                        f"Line '{line}' has width {vw} != 80 in cockpit screen",
                    )


if __name__ == "__main__":
    unittest.main()
