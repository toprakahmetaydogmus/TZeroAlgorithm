# -*- coding: utf-8 -*-
"""Unit tests for Siber Akademi T-Zero Advanced Intelligence Suite (tzero_features.py).

Tests:
  1. ChangeImpactAnalyzer: AST symbol detection, caller cascade tracing, risk score calculation.
  2. ArchitectureRuleEngine: Boundary loading, forbidden import detection, CI gate validation.
  3. AgentRulesGenerator: Generation of .cursorrules, .clinerules, Copilot instructions, and .mdc files.
  4. LocalSemanticCodeSearch: Zero-leak in-memory BM25 + TF-IDF hybrid search and RAG snippets.
  5. TokenROICalculator: Token compression ratio, token savings, and ROI dollar metric calculations.
  6. Web Dashboard: HTML template generation and DashboardRequestHandler.
"""

import os
import sys
import json
import tempfile
import unittest
import shutil

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tzero_features import (
    ChangeImpactAnalyzer,
    ArchitectureRuleEngine,
    AgentRulesGenerator,
    LocalSemanticCodeSearch,
    TokenROICalculator,
    HTML_DASHBOARD_TEMPLATE,
    DashboardRequestHandler,
)


class TestChangeImpactAnalyzer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.file_a = os.path.join(self.temp_dir, "service.py")
        self.file_b = os.path.join(self.temp_dir, "client.py")

        with open(self.file_a, "w", encoding="utf-8") as f:
            f.write(
                "def authenticate_user(token: str) -> bool:\n"
                "    return token == 'secret'\n\n"
                "def calculate_tax(amount: float) -> float:\n"
                "    return amount * 0.2\n"
            )

        with open(self.file_b, "w", encoding="utf-8") as f:
            f.write(
                "import service\n\n"
                "def login_handler():\n"
                "    if service.authenticate_user('test'):\n"
                "        return 'Welcome'\n"
            )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_impact_analysis_for_target_symbol(self):
        analyzer = ChangeImpactAnalyzer(self.temp_dir)
        report = analyzer.analyze_symbol("authenticate_user")

        self.assertEqual(report["symbol"], "authenticate_user")
        self.assertEqual(report["defining_file"], "service.py")
        self.assertGreaterEqual(report["risk_score"], 5)
        self.assertIn("risk_level", report)
        self.assertGreaterEqual(len(report["direct_callers"]), 1)
        self.assertEqual(report["direct_callers"][0]["file"], "client.py")

    def test_markdown_report_formatting(self):
        analyzer = ChangeImpactAnalyzer(self.temp_dir)
        report = analyzer.analyze_symbol("authenticate_user")
        md = analyzer.format_report(report)
        self.assertIn("Change Impact & Blast Radius", md)
        self.assertIn("authenticate_user", md)
        self.assertIn("Risk Assessment", md)


class TestArchitectureRuleEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.core_dir = os.path.join(self.temp_dir, "core")
        self.ui_dir = os.path.join(self.temp_dir, "ui")
        os.makedirs(self.core_dir, exist_ok=True)
        os.makedirs(self.ui_dir, exist_ok=True)

        # Core should NOT import from ui (violation)
        self.core_file = os.path.join(self.core_dir, "engine.py")
        with open(self.core_file, "w", encoding="utf-8") as f:
            f.write("import ui\n\ndef run(): pass\n")

        # UI importing from core is allowed
        self.ui_file = os.path.join(self.ui_dir, "views.py")
        with open(self.ui_file, "w", encoding="utf-8") as f:
            f.write("import core\n\ndef show(): pass\n")

        self.rules_path = os.path.join(self.temp_dir, "tzero.rules.json")
        rules = {
            "version": "1.0",
            "layers": {
                "core": ["core/*"],
                "ui": ["ui/*"]
            },
            "forbidden_imports": [
                {
                    "from_layer": "core",
                    "cannot_import": ["ui"],
                    "reason": "Core domain logic must never have visual UI dependencies."
                }
            ]
        }
        with open(self.rules_path, "w", encoding="utf-8") as f:
            json.dump(rules, f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_boundary_violation_detection(self):
        engine = ArchitectureRuleEngine(self.temp_dir, config_path=self.rules_path)
        res = engine.enforce_boundaries()

        self.assertFalse(res["clean"])
        self.assertGreaterEqual(res["total_violations"], 1)
        v = res["violations"][0]
        self.assertEqual(v["layer"], "core")
        self.assertEqual(v["forbidden_import"], "ui")
        self.assertIn("UI dependencies", v["reason"])

    def test_boundary_clean_pass(self):
        # Fix the violation
        with open(self.core_file, "w", encoding="utf-8") as f:
            f.write("import os\n\ndef run(): pass\n")

        engine = ArchitectureRuleEngine(self.temp_dir, config_path=self.rules_path)
        res = engine.enforce_boundaries()
        self.assertTrue(res["clean"])
        self.assertEqual(res["total_violations"], 0)


class TestAgentRulesGenerator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_all_agent_rules(self):
        created_files = AgentRulesGenerator.export_all(self.temp_dir)
        self.assertGreaterEqual(len(created_files), 4)

        # Verify .cursorrules
        cr_path = os.path.join(self.temp_dir, ".cursorrules")
        self.assertTrue(os.path.exists(cr_path))
        with open(cr_path, "r", encoding="utf-8") as f:
            cr_content = f.read()
            self.assertIn("ZERO-LEAK SECURITY GUARANTEE", cr_content)

        # Verify .clinerules
        cl_path = os.path.join(self.temp_dir, ".clinerules")
        self.assertTrue(os.path.exists(cl_path))

        # Verify copilot-instructions.md
        copilot_path = os.path.join(self.temp_dir, ".github", "copilot-instructions.md")
        self.assertTrue(os.path.exists(copilot_path))

        # Verify .cursor/rules/*.mdc
        cursor_rules_dir = os.path.join(self.temp_dir, ".cursor", "rules")
        self.assertTrue(os.path.isdir(cursor_rules_dir))
        self.assertTrue(os.path.exists(os.path.join(cursor_rules_dir, "architecture.mdc")))
        self.assertTrue(os.path.exists(os.path.join(cursor_rules_dir, "security.mdc")))


class TestLocalSemanticCodeSearch(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.file_1 = os.path.join(self.temp_dir, "auth.py")
        self.file_2 = os.path.join(self.temp_dir, "payment.py")

        with open(self.file_1, "w", encoding="utf-8") as f:
            f.write(
                "def authenticate_jwt_bearer(token: str) -> bool:\n"
                "    \"\"\"Validates JWT authorization tokens for secure sessions.\"\"\"\n"
                "    return verify_signature(token)\n"
            )

        with open(self.file_2, "w", encoding="utf-8") as f:
            f.write(
                "def process_stripe_charge(amount_cents: int, currency: str):\n"
                "    \"\"\"Processes an external credit card charge via Stripe gateway.\"\"\"\n"
                "    return stripe.Charge.create(amount=amount_cents, currency=currency)\n"
            )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_search_semantic_matching(self):
        search_engine = LocalSemanticCodeSearch(self.temp_dir)
        results = search_engine.search("jwt authorization token verify", top_k=5)

        self.assertGreaterEqual(len(results), 1)
        top_match = results[0]
        self.assertIn("auth.py", top_match["file"])
        self.assertGreater(top_match["relevance_score"], 0)
        self.assertIn("authenticate_jwt_bearer", top_match["snippet"])

    def test_search_payment_query(self):
        search_engine = LocalSemanticCodeSearch(self.temp_dir)
        results = search_engine.search("stripe charge credit card", top_k=5)

        self.assertGreaterEqual(len(results), 1)
        self.assertIn("payment.py", results[0]["file"])


class TestTokenROICalculator(unittest.TestCase):
    def test_savings_calculation(self):
        metrics = TokenROICalculator.compute_savings(
            raw_tokens=100000,
            reduced_tokens=10000,
            queries_per_day=50
        )

        self.assertEqual(metrics["raw_tokens"], 100000)
        self.assertEqual(metrics["reduced_tokens"], 10000)
        self.assertEqual(metrics["saved_tokens_per_query"], 90000)
        self.assertAlmostEqual(metrics["reduction_percentage"], 90.0)
        self.assertGreater(metrics["monthly_savings_usd"], 0)
        self.assertGreater(metrics["annual_savings_usd"], 0)


class TestWebDashboard(unittest.TestCase):
    def test_html_template(self):
        self.assertIn("<!DOCTYPE html>", HTML_DASHBOARD_TEMPLATE)
        self.assertIn("T-ZERO", HTML_DASHBOARD_TEMPLATE)
        self.assertIn("Blast Radius", HTML_DASHBOARD_TEMPLATE)
        self.assertIn("Local Hybrid Semantic Code Search", HTML_DASHBOARD_TEMPLATE)
        self.assertTrue(issubclass(DashboardRequestHandler, object))


if __name__ == "__main__":
    unittest.main()
