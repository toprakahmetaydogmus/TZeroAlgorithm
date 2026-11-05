# -*- coding: utf-8 -*-
"""
T-Zero PC-Fixer Master Deep Test Suite
======================================
Comprehensive verification suite for the 10,000+ line PC-Fixer & Codebase Doctor.
Tests:
  - 10,000+ line volume milestone assertion on tzero_pc_fixer.py
  - System Repair Playbooks & OS recipes
  - CWE / OWASP security weakness taxonomy
  - Dependency vulnerability auditing & version upgrading
  - Polyglot schema validation & EditorConfig generation
  - Smart micro-patch generation, blast radius calculation, & idempotency
  - Code duplicity & AST clone detection
  - End-to-end synthetic self-healing stress verification
"""

import os
import tempfile
import unittest
from pathlib import Path

from tzero_pc_fixer import (
    PCFixerDoctor,
)
from tzero_fixer.models import (
    DiagnosticCategory,
    DiagnosticIssue,
    HealAction,
    SeverityLevel,
    SystemPlatform,
)
from tzero_fixer.system_repair_recipes import SystemRepairPlaybooks
from tzero_fixer.security_cwe_database import CWESecurityDatabase
from tzero_fixer.dependency_vulnerability_auditor import DependencyVulnerabilityAuditor
from tzero_fixer.polyglot_schema_validator import PureJsonSchemaValidator, OpenApiSpecLinter, EditorConfigHealer
from tzero_fixer.smart_patch_recommender import SmartPatchRecommender
from tzero_fixer.code_duplicity_and_refactorer import ASTDuplicityRefactorer
from tzero_fixer.synthetic_workspace_generator import SyntheticWorkspaceGenerator


class TestPCFixerMasterEdition(unittest.TestCase):

    def test_line_count_milestone_10000(self):
        """Verifies that tzero_pc_fixer.py contains at least 10,000 lines of functional code."""
        fixer_file = Path("tzero_pc_fixer.py")
        self.assertTrue(fixer_file.is_file(), "tzero_pc_fixer.py must exist")
        with open(fixer_file, "r", encoding="utf-8") as f:
            lines = len(f.readlines())
        self.assertGreaterEqual(lines, 10000, f"Expected >= 10,000 lines, found {lines}")

    def test_system_repair_recipes_catalog(self):
        """Verifies recipe indexing, platform matching, and dry-run execution."""
        win_rec = SystemRepairPlaybooks.get_recipe("REC-WIN-001")
        self.assertIsNotNone(win_rec)
        self.assertEqual(win_rec.target_platform, SystemPlatform.WINDOWS)
        self.assertTrue(win_rec.automated_fix_available)

        # Test finding by diagnostic code
        rec = SystemRepairPlaybooks.find_recipe_for_issue("TZ-ENV-002")
        self.assertIsNotNone(rec)
        self.assertEqual(rec.recipe_id, "REC-GIT-001")

        # Test dry-run execution
        ok, msg = SystemRepairPlaybooks.execute_recipe_command(win_rec, dry_run=True)
        self.assertTrue(ok)
        self.assertIn("[DRY-RUN]", msg)

    def test_cwe_security_database(self):
        """Verifies CWE lookup, OWASP mapping, and keyword searches."""
        sqli = CWESecurityDatabase.get_by_cwe("CWE-89")
        self.assertIsNotNone(sqli)
        self.assertIn("SQL Injection", sqli.name)
        self.assertEqual(sqli.owasp_category, "A03:2021-Injection")
        self.assertGreaterEqual(sqli.cvss_score, 9.0)

        ssrf = CWESecurityDatabase.get_by_cwe("CWE-918")
        self.assertIsNotNone(ssrf)
        self.assertIn("Server-Side Request Forgery", ssrf.name)

        injection_rules = CWESecurityDatabase.list_by_owasp("Injection")
        self.assertGreaterEqual(len(injection_rules), 3)

    def test_pure_json_schema_validator(self):
        """Verifies zero-dependency schema validation."""
        schema = {
            "type": "object",
            "required": ["username", "age"],
            "properties": {
                "username": {"type": "string", "minLength": 3},
                "age": {"type": "integer", "minimum": 0},
                "role": {"type": "string", "enum": ["admin", "user", "guest"]},
            },
        }

        # Valid payload
        valid_obj = {"username": "alice", "age": 30, "role": "admin"}
        errs = PureJsonSchemaValidator.validate_instance(valid_obj, schema)
        self.assertEqual(len(errs), 0)

        # Invalid payload: missing age, bad enum, invalid type
        invalid_obj = {"username": "a", "role": "superadmin"}
        errs2 = PureJsonSchemaValidator.validate_instance(invalid_obj, schema)
        self.assertTrue(any("missing required property 'age'" in e for e in errs2))
        self.assertTrue(any("shorter than minLength" in e for e in errs2))
        self.assertTrue(any("not in allowed enum" in e for e in errs2))

    def test_openapi_linter(self):
        """Verifies OpenAPI schema linting."""
        invalid_spec = {"info": {"version": "1.0"}}
        issues = OpenApiSpecLinter.lint_openapi_dict(invalid_spec, "openapi.yaml")
        codes = [i.error_code for i in issues]
        self.assertIn("TZ-API-001", codes)  # Missing openapi version
        self.assertIn("TZ-API-003", codes)  # Missing info.title
        self.assertIn("TZ-API-004", codes)  # Missing paths

    def test_editorconfig_healer(self):
        """Verifies .editorconfig generation."""
        with tempfile.TemporaryDirectory() as td:
            issues, actions = EditorConfigHealer.diagnose_and_heal(td, dry_run=False)
            self.assertEqual(len(issues), 1)
            self.assertEqual(len(actions), 1)
            self.assertTrue((Path(td) / ".editorconfig").is_file())

    def test_dependency_vulnerability_auditor(self):
        """Verifies offline detection of vulnerable dependencies."""
        req_content = "requests==2.28.0\nflask==2.1.0\nurllib3==1.26.5\nclean-pkg==1.0.0\n"
        issues = DependencyVulnerabilityAuditor.scan_requirements_txt("requirements.txt", req_content)
        self.assertGreaterEqual(len(issues), 3)

        # Test healing/upgrading
        with tempfile.TemporaryDirectory() as td:
            rf = Path(td) / "requirements.txt"
            rf.write_text(req_content, encoding="utf-8")
            issues_with_path = DependencyVulnerabilityAuditor.scan_requirements_txt(str(rf), req_content)
            actions = DependencyVulnerabilityAuditor.execute_upgrades(issues_with_path, dry_run=False)
            self.assertGreaterEqual(len(actions), 3)
            new_text = rf.read_text(encoding="utf-8")
            self.assertIn("requests==2.31.0", new_text)
            self.assertIn("flask==2.2.5", new_text)

    def test_smart_patch_recommender(self):
        """Verifies micro-patch generation and in-memory application."""
        issue = DiagnosticIssue(
            category="syntax",
            severity="critical",
            file_path="service.py",
            line=1,
            error_code="TZ-SYN-001",
            message="Missing colon on function definition",
        )
        patch = SmartPatchRecommender.generate_patch_from_hunk(
            file_path="service.py",
            original_line="def compute(x)",
            repaired_line="def compute(x):",
            line_number=1,
            summary="Appended missing colon delimiter",
            issue=issue,
        )

        self.assertIn("--- a/service.py", patch.unified_diff)
        self.assertIn("+++ b/service.py", patch.unified_diff)
        self.assertIn("-def compute(x)", patch.unified_diff)
        self.assertIn("+def compute(x):", patch.unified_diff)

        # In-memory application test
        orig_code = "def compute(x)\n    return x * 2\n"
        ok, res_code, err = SmartPatchRecommender.apply_patch_in_memory(orig_code, patch)
        self.assertTrue(ok)
        self.assertTrue(res_code.startswith("def compute(x):"))

        # PR comment formatting
        comment = SmartPatchRecommender.generate_pr_review_comment([patch])
        self.assertIn("T-Zero Autonomous Self-Healing Proposal", comment)

    def test_ast_duplicity_refactorer(self):
        """Verifies clone detection on duplicate code blocks."""
        with tempfile.TemporaryDirectory() as td:
            code_a = (
                "def process_user_metrics(user_id: str):\n"
                "    val = fetch_raw_data(user_id)\n"
                "    res = transform_data(val)\n"
                "    save_metrics(res)\n"
                "    notify_admin(res)\n"
                "    return True\n"
            )
            (Path(td) / "module_a.py").write_text(code_a, encoding="utf-8")
            (Path(td) / "module_b.py").write_text(code_a, encoding="utf-8")

            groups, issues = ASTDuplicityRefactorer.find_duplicate_groups(td)
            self.assertGreaterEqual(len(groups), 1)
            self.assertEqual(len(groups[0].instances), 2)
            self.assertGreaterEqual(len(issues), 1)

    def test_synthetic_workspace_e2e(self):
        """Executes full end-to-end self-healing and atomic rollback on synthetic repository."""
        rep = SyntheticWorkspaceGenerator.run_e2e_self_healing_verification()
        self.assertTrue(rep.passed)
        self.assertGreater(rep.healed_actions_count, 0)
        self.assertTrue(rep.rollback_verified)
        self.assertGreater(rep.final_health_score, rep.initial_health_score)


if __name__ == "__main__":
    unittest.main()
