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
    GitDiffContextBuilder,
    DeadCodeFinder,
    detect_circular_dependencies,
    ZeroHallucinationGuard,
    ReusableHelperSuggester,
    SmartSkeletonContextBuilder,
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
        self.assertGreaterEqual(len(created_files), 6)

        # Verify .cursorrules
        cr_path = os.path.join(self.temp_dir, ".cursorrules")
        self.assertTrue(os.path.exists(cr_path))
        with open(cr_path, "r", encoding="utf-8") as f:
            cr_content = f.read()
            self.assertIn("ZERO-LEAK SECURITY GUARANTEE", cr_content)

        # Verify .clinerules
        cl_path = os.path.join(self.temp_dir, ".clinerules")
        self.assertTrue(os.path.exists(cl_path))

        # Verify .windsurfrules
        ws_path = os.path.join(self.temp_dir, ".windsurfrules")
        self.assertTrue(os.path.exists(ws_path))

        # Verify CLAUDE.md
        claude_path = os.path.join(self.temp_dir, "CLAUDE.md")
        self.assertTrue(os.path.exists(claude_path))

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


class TestGitDiffContextBuilder(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.file_1 = os.path.join(self.temp_dir, "core.py")
        with open(self.file_1, "w", encoding="utf-8") as f:
            f.write("def core_function():\n    return 42\n")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_git_diff_clean_directory(self):
        builder = GitDiffContextBuilder(self.temp_dir)
        res = builder.build_diff_context("HEAD")
        self.assertIn("markdown", res)
        self.assertEqual(res["changed_files_count"], 0)

    def test_git_diff_context_structure(self):
        builder = GitDiffContextBuilder(self.temp_dir)
        builder.get_diff_changed_files = lambda ref="HEAD~1": [{"status": "M", "file": "core.py"}]
        res = builder.build_diff_context("HEAD~1")
        self.assertEqual(res["changed_files_count"], 1)
        self.assertIn("Incremental PR Context", res["markdown"])
        self.assertIn("core.py", res["markdown"])
        self.assertGreater(res["token_savings_percent"], 0.0)


class TestDeadCodeFinder(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        with open(os.path.join(self.temp_dir, "lib.py"), "w", encoding="utf-8") as f:
            f.write(
                "def used_function():\n    return 1\n\n"
                "def orphan_function():\n    return 2\n\n"
                "class OrphanClass:\n    pass\n"
            )
        with open(os.path.join(self.temp_dir, "main.py"), "w", encoding="utf-8") as f:
            f.write(
                "import lib\n\n"
                "def run():\n    return lib.used_function()\n"
            )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_find_unused_symbols(self):
        finder = DeadCodeFinder(self.temp_dir)
        dead = finder.find_unused_symbols()
        dead_names = [d["symbol"] for d in dead["dead_symbols"]]
        self.assertIn("orphan_function", dead_names)
        self.assertIn("OrphanClass", dead_names)
        self.assertNotIn("used_function", dead_names)


class TestCircularDependencies(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        with open(os.path.join(self.temp_dir, "mod_a.py"), "w", encoding="utf-8") as f:
            f.write("import mod_b\n")
        with open(os.path.join(self.temp_dir, "mod_b.py"), "w", encoding="utf-8") as f:
            f.write("import mod_a\n")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_detect_cycles(self):
        cycles = detect_circular_dependencies(self.temp_dir)
        self.assertTrue(len(cycles) > 0)
        cycle_str = " -> ".join(cycles[0])
        self.assertTrue("mod_a" in cycle_str and "mod_b" in cycle_str)


class TestZeroHallucinationGuard(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        with open(os.path.join(self.temp_dir, "calc.py"), "w", encoding="utf-8") as f:
            f.write(
                "class Calculator:\n"
                "    def add_numbers(self, a: int, b: int) -> int:\n"
                "        return a + b\n"
            )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_fuzzy_did_you_mean_suggestion(self):
        guard = ZeroHallucinationGuard(self.temp_dir)
        # 1. Mismatched import with typo
        proposed_import_typo = "from calc import Calculater\n"
        res_import = guard.validate_code(proposed_import_typo)
        self.assertFalse(res_import["passed"])
        self.assertIn("Calculator", res_import["report"])

        # 2. Mismatched keyword argument
        proposed_kwarg_typo = "from calc import Calculator\nc = Calculator()\nc.add_numbers(a=1, bx=2)\n"
        res_kwarg = guard.validate_code(proposed_kwarg_typo)
        self.assertFalse(res_kwarg["passed"])
        self.assertIn("b", res_kwarg["report"])

    def test_ghost_dependency_detection(self):
        guard = ZeroHallucinationGuard(self.temp_dir)
        # Fake hallucinated package not in stdlib or requirements
        fake_code = "import phantom_fake_sdk_cloud_999\nfrom phantom_fake_sdk_cloud_999 import Client\n"
        res = guard.validate_code(fake_code)
        self.assertFalse(res["passed"])
        self.assertTrue(any("Ghost Dependency Hallucination" in v for v in res["violations"]))

        # Real stdlib imports must pass
        valid_stdlib = "import os\nimport sys\nimport json\nimport ast\n"
        res_valid = guard.validate_code(valid_stdlib)
        self.assertTrue(res_valid["passed"])

    def test_self_healing_ast_patcher(self):
        guard = ZeroHallucinationGuard(self.temp_dir)
        broken_code = (
            "from calc import Calculater\n"
            "calc = Calculater()\n"
            "calc.add_numbers(a=5, bx=10)\n"
        )
        res = guard.validate_code(broken_code)
        self.assertFalse(res["passed"])
        self.assertTrue(res["can_auto_heal"])
        self.assertIn("Calculator", res["repaired_code"])
        self.assertIn("b=10", res["repaired_code"])

        # Validate repair_code method
        healed = guard.repair_code(broken_code)
        self.assertIn("from calc import Calculator", healed)
        self.assertIn("b=10", healed)

    def test_schema_field_contract_guard(self):
        models_file = os.path.join(self.temp_dir, "models.py")
        with open(models_file, "w", encoding="utf-8") as f:
            f.write(
                "class UserAccount:\n"
                "    username: str\n"
                "    email: str\n"
                "    def __init__(self, username: str, email: str):\n"
                "        self.username = username\n"
                "        self.email = email\n"
            )
        guard = ZeroHallucinationGuard(self.temp_dir)
        bad_instantiation = "from models import UserAccount\nu = UserAccount(username='bob', ghost_field=123)\n"
        res = guard.validate_code(bad_instantiation)
        self.assertFalse(res["passed"])
        self.assertTrue(any("Schema Field Hallucination" in v for v in res["violations"]))

    def test_return_type_contract_guard(self):
        svc_file = os.path.join(self.temp_dir, "svc.py")
        with open(svc_file, "w", encoding="utf-8") as f:
            f.write(
                "def emit_metric(name: str) -> None:\n"
                "    pass\n"
            )
        guard = ZeroHallucinationGuard(self.temp_dir)
        
        # Test invalid loop over None return
        loop_code = "import svc\nfor x in svc.emit_metric('cpu'): pass\n"
        res_loop = guard.validate_code(loop_code)
        self.assertFalse(res_loop["passed"])
        self.assertTrue(any("Return Contract Hallucination" in v for v in res_loop["violations"]))

        # Test invalid attribute access on None return
        attr_code = "import svc\nval = svc.emit_metric('cpu').non_existent_prop\n"
        res_attr = guard.validate_code(attr_code)
        self.assertFalse(res_attr["passed"])
        self.assertTrue(any("Return Contract Hallucination" in v for v in res_attr["violations"]))

    def test_grounding_contract_generation(self):
        guard = ZeroHallucinationGuard(self.temp_dir)
        contract = guard.generate_grounding_contract(task_intent="Mathematical Additions")
        self.assertIn("IMMUTABLE AST GROUNDING CONTRACT", contract)
        self.assertIn("Calculator", contract)
        self.assertIn("add_numbers", contract)
        self.assertIn("Mathematical Additions", contract)


class TestReusableHelperSuggester(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.utils_file = os.path.join(self.temp_dir, "date_utils.py")
        self.client_file = os.path.join(self.temp_dir, "app.py")

        with open(self.utils_file, "w", encoding="utf-8") as f:
            f.write(
                "def parse_iso_datetime(date_str: str) -> str:\n"
                "    \"\"\"Parses ISO 8601 formatted date string safely.\"\"\"\n"
                "    return date_str.strip()\n\n"
                "def format_currency_amount(amount: float, currency: str = 'USD') -> str:\n"
                "    \"\"\"Formats a numeric amount with standard currency code.\"\"\"\n"
                "    return f'{currency} {amount:.2f}'\n"
            )

        with open(self.client_file, "w", encoding="utf-8") as f:
            f.write(
                "import date_utils\n\n"
                "def main():\n"
                "    print(date_utils.format_currency_amount(100.0))\n"
            )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_suggest_helpers_by_query(self):
        suggester = ReusableHelperSuggester(self.temp_dir)
        matches = suggester.suggest_helpers("parse date string")
        self.assertTrue(len(matches) > 0)
        top = matches[0]
        self.assertEqual(top["name"], "parse_iso_datetime")
        self.assertIn("from date_utils import parse_iso_datetime", top["import_stmt"])
        self.assertIn("parse_iso_datetime", top["signature"])

    def test_check_reinvention_guard_detects_duplicate(self):
        suggester = ReusableHelperSuggester(self.temp_dir)
        snippet = (
            "def parse_date(date_str):\n"
            "    \"\"\"Parses ISO formatted date string\"\"\"\n"
            "    return date_str\n"
        )
        guard_res = suggester.check_reinvention_guard(snippet)
        self.assertTrue(guard_res["has_reinventions"])
        self.assertEqual(guard_res["total_warnings"], 1)
        w = guard_res["warnings"][0]
        self.assertEqual(w["new_symbol"], "parse_date")
        self.assertEqual(w["matched_helper"], "parse_iso_datetime")

    def test_format_helpers_report(self):
        suggester = ReusableHelperSuggester(self.temp_dir)
        matches = suggester.suggest_helpers("currency")
        report = suggester.format_helpers_report(matches, query="currency")
        self.assertIn("Reusable Repository Helpers", report)
        self.assertIn("format_currency_amount", report)
        self.assertIn("from date_utils import format_currency_amount", report)

    def test_smart_skeleton_includes_reusable_helpers(self):
        builder = SmartSkeletonContextBuilder(self.temp_dir)
        context = builder.build_skeleton("app.py", task_intent="parse date string")
        self.assertIn("Reusable Repository Helpers Available", context)
        self.assertIn("parse_iso_datetime", context)


if __name__ == "__main__":
    unittest.main()

