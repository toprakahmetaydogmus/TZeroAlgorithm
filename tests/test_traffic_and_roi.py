# -*- coding: utf-8 -*-
"""Comprehensive tests for T-Zero Traffic, Update, Crypto Support, and ROI Engine.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: AGPL-3.0-only
"""

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from tzero.tzero_traffic import (
    CURRENT_VERSION,
    CRYPTO_USDT_TRC20,
    CRYPTO_BTC,
    REPO_URL,
    BIO_URL,
    LLM_PRICING,
    check_version_and_updates,
    print_crypto_support_card,
    open_github_star_page,
    run_live_roi_dashboard,
    run_system_disk_doctor,
)
from tzero.tzero_rust_bridge import RustCoreBridge, get_bridge


class TestTrafficAndSupport(unittest.TestCase):
    def test_crypto_addresses_and_links(self):
        self.assertEqual(CRYPTO_USDT_TRC20, "TE7uKxZJ414u938gWf6bYh9QvRk2141517")
        self.assertEqual(CRYPTO_BTC, "bc1q9k4hvd6c2g8l9w3z7v8f2k3j5l8n9m1p4q7r0s")
        self.assertIn("github.com", REPO_URL)
        self.assertIn("hopp.bio", BIO_URL)

    def test_support_card_output(self):
        res = print_crypto_support_card()
        self.assertEqual(res["usdt_trc20"], CRYPTO_USDT_TRC20)
        self.assertEqual(res["btc"], CRYPTO_BTC)
        self.assertEqual(res["repo"], REPO_URL)
        self.assertEqual(res["bio"], BIO_URL)

    def test_open_github_star_page(self):
        res = open_github_star_page(open_browser=False)
        self.assertEqual(res["repo_url"], REPO_URL)
        self.assertEqual(res["current_stars"], 45)
        self.assertEqual(res["target_stars"], 100)
        self.assertFalse(res["opened_browser"])

    @patch("urllib.request.urlopen")
    def test_check_version_and_updates_mocked(self, mock_urlopen):
        class MockResp:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def read(self):
                return b'{"info": {"version": "12.0.0"}, "tag_name": "v12.0.0"}'

        mock_urlopen.return_value = MockResp()
        res = check_version_and_updates(open_browser=False)
        self.assertEqual(res["current_version"], "12.0.0")
        self.assertEqual(res["pypi_version"], "12.0.0")
        self.assertEqual(res["github_version"], "12.0.0")
        self.assertFalse(res["is_outdated"])

    def test_live_roi_dashboard_execution(self):
        # Run on tests/ directory for quick deterministic scan
        tests_dir = Path(__file__).resolve().parent
        metrics = run_live_roi_dashboard(workspace_dir=str(tests_dir))
        self.assertIn("scanned_files", metrics)
        self.assertGreater(metrics["scanned_files"], 0)
        self.assertIn("dollar_savings", metrics)
        self.assertIn("Claude 3.7 Sonnet", metrics["dollar_savings"])
        self.assertIn("GPT-4o", metrics["dollar_savings"])
        self.assertGreaterEqual(metrics["reduction_pct"], 0.0)

    def test_system_disk_doctor(self):
        tests_dir = Path(__file__).resolve().parent
        res = run_system_disk_doctor(clean=False, workspace_dir=str(tests_dir))
        self.assertIn("workspace", res)
        self.assertIn("total_mb", res)
        self.assertFalse(res["cleaned"])

    def test_rust_bridge_bm25_and_symbols(self):
        bridge = get_bridge()
        docs = [
            {"id": "doc1", "path": "engine.py", "content": "def calculate_shannon_entropy(x): pass"},
            {"id": "doc2", "path": "pruner.py", "content": "def prune_ast_signatures(code): pass"},
        ]
        results = bridge.bm25_search(docs, "shannon entropy", top_k=2)
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["id"], "doc1")
        self.assertIn("snippet", results[0])

        syms = bridge.extract_symbols("test_mod.py", "import os\ndef helper(): pass\nclass Core: pass\n")
        self.assertIn("symbols", syms)
        self.assertIn("edges", syms)
        self.assertEqual(len(syms["symbols"]), 2)
        self.assertEqual(len(syms["edges"]), 1)


if __name__ == "__main__":
    unittest.main()
