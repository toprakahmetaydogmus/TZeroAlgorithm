# -*- coding: utf-8 -*-
"""Unit tests for prompt template engine and context tree generation."""

import unittest
from tzero_v3 import (
    TemplateEngine,
    count_tokens_precise,
    get_budgeted_snippets,
    generate_offline_context,
)


class TestGenerator(unittest.TestCase):
    def test_template_engine_render(self):
        engine = TemplateEngine()
        rendered = engine.render({
            "PROJECT_NAME": "AlphaBot",
            "MODULES_REFERENCE": "### Core Modules",
            "HALLUCINATION_GUARDRAILS": "Do not fabricate code."
        })
        self.assertIn("# AlphaBot Context Tree", rendered)
        self.assertIn("### Core Modules", rendered)
        self.assertIn("Do not fabricate code.", rendered)

    def test_count_tokens_precise(self):
        import tiktoken
        text = "Hello world! This is a test for token estimation across programming interfaces and type hints."
        toks = count_tokens_precise(text, "gpt-4o")
        expected_o200k = len(tiktoken.get_encoding("o200k_base").encode(text))
        self.assertEqual(toks, expected_o200k)
        self.assertNotEqual(toks, len(text) // 4)

        toks_claude = count_tokens_precise(text, "claude-3-7-sonnet")
        expected_cl100k = len(tiktoken.get_encoding("cl100k_base").encode(text))
        self.assertEqual(toks_claude, expected_cl100k)

    def test_count_tokens_precise_fallback(self):
        from unittest import mock
        import tzero_v3
        text = "Hello world! Fallback estimation check."
        with mock.patch.dict("sys.modules", {"tiktoken": None}):
            if hasattr(tzero_v3, "_BPE_ENCODING_CACHE"):
                tzero_v3._BPE_ENCODING_CACHE.clear()
            toks = tzero_v3.count_tokens_precise(text, "gpt-4o")
            self.assertEqual(toks, max(1, len(text) // 4))

    def test_get_budgeted_snippets(self):
        selected = ["main.py", "utils.py"]
        snippets = {
            "main.py": "def main(): pass",
            "utils.py": "def helper(): pass",
        }
        budgeted = get_budgeted_snippets(selected, snippets)
        self.assertIn("main.py", budgeted)
        self.assertIn("utils.py", budgeted)

    def test_generate_offline_context(self):
        selected = ["app.py", "db.py"]
        snippets = {
            "app.py": "import os\ndef run(): pass",
            "db.py": "import sqlite3\nclass DB: pass"
        }
        res = generate_offline_context("C:/projects/demo", selected, snippets)
        self.assertIn("# demo — T-Zero Context Tree", res)
        self.assertIn("Architecture Overview", res)
        self.assertIn("Module Reference & Signatures", res)
        self.assertIn("### `app.py`", res)
        self.assertIn("### `db.py`", res)
        self.assertIn("100% Zero-Leak", res)
        # Verify 4-Tier Context hierarchy
        self.assertIn("Tier T-1", res)
        self.assertIn("Tier T-2", res)
        self.assertIn("Tier T-3", res)
        self.assertIn("Tier T-4", res)
        # Verify canonical T-Zero Algorithm rules
        self.assertIn("Rule T-001: Zero-Leak Isolation", res)
        self.assertIn("Rule T-002: Architectural Boundary Enforcement", res)
        self.assertIn("Rule T-003: AST Interface Contract Fidelity", res)
        self.assertIn("Rule T-004: Anti-Pattern & Maintainability Guard", res)


if __name__ == "__main__":
    unittest.main()
