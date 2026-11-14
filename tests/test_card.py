# -*- coding: utf-8 -*-
"""Unit tests for T-Zero Showcase Card and Viral Badge Generator."""

import os
import sys
import tempfile
import unittest
import subprocess

from tzero.tzero_card import TZeroShowcaseGenerator


class TestTZeroShowcaseGenerator(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="tzero_card_test_")

    def test_generate_svg_banner_card(self):
        out_svg = os.path.join(self.tmp_dir, "test_card.svg")
        res = TZeroShowcaseGenerator.generate_svg_banner_card(
            repo_name="AwesomeAI",
            savings_pct=92.5,
            raw_tokens=500000,
            pruned_tokens=37500,
            annual_savings_usd=12000.0,
            output_file=out_svg
        )
        self.assertEqual(res, out_svg)
        self.assertTrue(os.path.isfile(out_svg))
        with open(out_svg, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("<svg", content)
        self.assertIn("-92.5%", content)
        self.assertIn("ZERO-LEAK", content)
        self.assertIn("REALITY-LOCK", content)
        self.assertIn("STAR ON GITHUB", content)

    def test_generate_readme_markdown_badges(self):
        md = TZeroShowcaseGenerator.generate_readme_markdown_badges(savings_pct=95.0)
        self.assertIn("https://github.com/toprakahmetaydogmus/TZeroAlgorithm", md)
        self.assertIn("-95.0%", md)
        self.assertIn("Zero--Leak", md)

    def test_generate_interactive_showcase_html(self):
        out_html = os.path.join(self.tmp_dir, "showcase.html")
        res = TZeroShowcaseGenerator.generate_interactive_showcase_html(output_file=out_html)
        self.assertEqual(res, out_html)
        self.assertTrue(os.path.isfile(out_html))
        with open(out_html, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("T-Zero Token Optimization Showcase", content)
        self.assertIn("Star T-Zero on GitHub", content)

    def test_cli_card_and_showcase(self):
        res_card = subprocess.run(
            [sys.executable, "-m", "tzero.tzero_v3", "--card", os.path.join(self.tmp_dir, "cli_card.svg")],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res_card.returncode, 0)
        self.assertIn("Generated Viral T-Zero GitHub Showcase Card", res_card.stdout)

        res_showcase = subprocess.run(
            [sys.executable, "-m", "tzero.tzero_v3", "--showcase", os.path.join(self.tmp_dir, "cli_showcase.html")],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res_showcase.returncode, 0)
        self.assertIn("Generated Interactive Split-Screen Showcase Slider", res_showcase.stdout)


if __name__ == "__main__":
    unittest.main()
