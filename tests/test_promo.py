# -*- coding: utf-8 -*-
"""Unit tests for T-Zero Organic Promotion & Launch Toolkit."""

import io
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from tzero.tzero_promo import (
    get_current_version,
    build_show_hn,
    build_reddit_localllama,
    build_reddit_cursor,
    build_twitter_thread,
    build_product_hunt,
    build_discord_showcase,
    build_readme_index,
    generate_all_launch_files,
    launch_interactive_browser_hub,
    main as promo_main,
)


class TestPromoToolkit(unittest.TestCase):
    def test_version_detection(self):
        v = get_current_version()
        self.assertTrue(v.startswith("v12.") or v.startswith("v11."))

    def test_show_hn_structure(self):
        v = get_current_version()
        hn = build_show_hn(v)
        self.assertIn("Show HN: T-Zero", hn["title"])
        self.assertIn("Disclosure:", hn["body"])
        self.assertIn("Siber Akademi", hn["body"])
        self.assertIn("-88.0%", hn["body"])

    def test_reddit_localllama_structure_and_unslop(self):
        v = get_current_version()
        reddit = build_reddit_localllama(v)
        self.assertEqual(reddit["subreddit"], "r/LocalLLaMA")
        self.assertIn("Disclosure:", reddit["title"])
        self.assertIn("Affiliation Disclosure", reddit["body"])
        self.assertIn("100% free under the MIT license", reddit["body"])
        self.assertIn("Qwen 2.5 Coder", reddit["body"])
        self.assertIn("PageRank", reddit["body"])
        self.assertIn("Limitations & Trade-Offs", reddit["body"])

    def test_reddit_cursor_structure(self):
        v = get_current_version()
        cursor = build_reddit_cursor(v)
        self.assertEqual(cursor["subreddit"], "r/Cursor")
        self.assertIn("Disclosure:", cursor["title"])
        self.assertIn("Affiliation Disclosure", cursor["body"])
        self.assertIn("Composer", cursor["body"])
        self.assertIn("~/.cursor/mcp.json", cursor["body"])
        self.assertIn("get_smart_skeleton_context", cursor["body"])

    def test_twitter_thread_structure(self):
        v = get_current_version()
        thread = build_twitter_thread(v)
        self.assertEqual(len(thread), 7)
        self.assertIn("1/7", thread[0])
        self.assertIn("7/7", thread[6])
        for tweet in thread:
            self.assertLessEqual(len(tweet), 280)

    def test_product_hunt_structure(self):
        v = get_current_version()
        ph = build_product_hunt(v)
        self.assertEqual(ph["name"], "T-Zero Context Architect")
        self.assertIn("AST pruning", ph["tagline"])
        self.assertIn("Product Hunt", ph["maker_comment"])

    def test_discord_showcase_structure(self):
        v = get_current_version()
        discord = build_discord_showcase(v)
        self.assertIn("mcpServers", discord["content"])
        self.assertIn("winget install", discord["content"])

    def test_generate_all_launch_files(self):
        with tempfile.TemporaryDirectory() as td:
            out_dir = pathlib.Path(td)
            results = generate_all_launch_files(out_dir)
            self.assertEqual(len(results), 7)
            self.assertIn("reddit_cursor", results)
            for key, path in results.items():
                self.assertTrue(path.is_file(), f"Missing file: {path}")
                self.assertGreater(path.stat().st_size, 100, f"File too small: {path}")

    @patch("webbrowser.open")
    def test_launch_interactive_browser_hub(self, mock_webopen):
        res = launch_interactive_browser_hub(channel="cursor", open_browser=True)
        self.assertIn("cursor", res["opened"])
        self.assertIn("r/Cursor", res["urls"]["cursor"])
        mock_webopen.assert_called_once()

        mock_webopen.reset_mock()
        res_all = launch_interactive_browser_hub(channel="all", open_browser=True)
        self.assertEqual(len(res_all["opened"]), 6)
        self.assertEqual(mock_webopen.call_count, 6)

    @patch("webbrowser.open")
    def test_promo_cli_handles_open_flag(self, mock_webopen):
        rc = promo_main(["--open", "--channel", "hn"])
        self.assertEqual(rc, 0)
        mock_webopen.assert_called_once()

    def test_promo_cli_check_mode(self):
        with tempfile.TemporaryDirectory() as td:
            out_dir = pathlib.Path(td)
            # Before generating, check should fail
            rc_fail = promo_main(["--output-dir", str(out_dir), "--check"])
            self.assertEqual(rc_fail, 1)

            # Generate
            generate_all_launch_files(out_dir)

            # Now check should succeed
            rc_ok = promo_main(["--output-dir", str(out_dir), "--check"])
            self.assertEqual(rc_ok, 0)

    def test_promo_cli_handles_promo_flag(self):
        with tempfile.TemporaryDirectory() as td:
            out_dir = pathlib.Path(td)
            # Passing --promo along with output dir should not crash with unrecognized arguments
            rc = promo_main(["--promo", "--output-dir", str(out_dir)])
            self.assertEqual(rc, 0)
            self.assertTrue((out_dir / "README.md").is_file())

    def test_promo_cli_handles_aliases_and_extraneous_args(self):
        with tempfile.TemporaryDirectory() as td:
            out_dir = pathlib.Path(td)
            # Test --out alias and extraneous arguments passed from parent CLI
            rc = promo_main(["--promo", "--dir", ".", "--unknown-parent-flag", "--out", str(out_dir)])
            self.assertEqual(rc, 0)
            self.assertTrue((out_dir / "README.md").is_file())
            self.assertTrue((out_dir / "show_hn.md").is_file())


if __name__ == "__main__":
    unittest.main()
