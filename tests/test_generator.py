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
        text = "Hello world! This is a test for token estimation."
        toks = count_tokens_precise(text, "meta/llama-3.3-70b-instruct")
        self.assertGreater(toks, 0)
        self.assertEqual(toks, len(text) // 4)

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


if __name__ == "__main__":
    unittest.main()
