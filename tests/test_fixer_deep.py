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
import time
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
from tzero_fixer.hardware_and_disk_doctor import HardwareAndDiskSurgeon
from tzero_fixer.packaging_abi_surgeon import PackagingAbiSurgeon
from tzero_fixer.git_advanced_surgeon import GitAdvancedSurgeon
from tzero_fixer.polyglot_build_healer import PolyglotBuildHealer
from tzero_fixer.cwe_remediator import SecurityCweRemediator
from tzero_fixer.dead_code_eliminator import DeadCodeEliminator
from tzero_fixer.async_io_modernizer import AsyncIoModernizer
from tzero_fixer.mcp_server import PCFixerMcpServer


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

    def test_packaging_abi_surgeon(self):
        """Verifies PEP 517 detection and pyvenv.cfg repair."""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            # Create a broken pyproject.toml missing build-system
            (p / "pyproject.toml").write_text("[project]\nname = 'demo'\nversion = '1.0.0'\n", encoding="utf-8")
            issues = PackagingAbiSurgeon.diagnose_workspace(td)
            self.assertTrue(any(i.metadata.get("issue_type") == "missing_build_system" for i in issues))

            # Heal it
            for i in issues:
                if i.metadata.get("issue_type") == "missing_build_system":
                    action = PackagingAbiSurgeon.heal_issue(i, dry_run=False)
                    self.assertTrue(action.success)
            self.assertIn("[build-system]", (p / "pyproject.toml").read_text(encoding="utf-8"))

    def test_git_advanced_surgeon(self):
        """Verifies stale lock detection and .gitattributes generation."""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            git_dir = p / ".git"
            git_dir.mkdir()
            # Stale lock
            lock = git_dir / "index.lock"
            lock.write_text("lock", encoding="utf-8")
            # Fake old timestamp
            old_time = time.time() - 600
            os.utime(lock, (old_time, old_time))

            issues = GitAdvancedSurgeon.diagnose_workspace(td)
            self.assertTrue(any(i.metadata.get("issue_type") == "stale_git_lock" for i in issues))

            # Remove lock
            for i in issues:
                if i.metadata.get("issue_type") == "stale_git_lock":
                    res = GitAdvancedSurgeon.heal_issue(i, dry_run=False)
                    self.assertTrue(res.success)
            self.assertFalse(lock.exists())

    def test_polyglot_build_healer(self):
        """Verifies Makefile space-to-tab repair and .dockerignore creation."""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            makefile = p / "Makefile"
            makefile.write_text("build:\n    python setup.py build\n", encoding="utf-8")
            dockerfile = p / "Dockerfile"
            dockerfile.write_text("FROM python:3.11\nRUN pip install requests\n", encoding="utf-8")

            issues = PolyglotBuildHealer.diagnose_workspace(td)
            self.assertTrue(any(i.metadata.get("issue_type") == "makefile_spaces_to_tabs" for i in issues))
            self.assertTrue(any(i.metadata.get("issue_type") == "missing_dockerignore" for i in issues))

            for i in issues:
                PolyglotBuildHealer.heal_issue(i, dry_run=False)

            self.assertIn("\tpython setup.py build", makefile.read_text(encoding="utf-8"))
            self.assertTrue((p / ".dockerignore").is_file())

    def test_hardware_and_mcp_server(self):
        """Verifies hardware checks and MCP tool dispatching."""
        # Hardware check
        disk_health = HardwareAndDiskSurgeon.check_disk_space()
        self.assertGreater(len(disk_health), 0)

        # MCP Server initialize and tools/list
        mcp = PCFixerMcpServer()
        init_res = mcp.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        self.assertEqual(init_res["result"]["serverInfo"]["name"], "tzero-pc-fixer-mcp")

        list_res = mcp.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = list_res["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        self.assertIn("pc_fixer_diagnose", tool_names)
        self.assertIn("pc_fixer_auto_heal", tool_names)
        self.assertIn("pc_fixer_check_system", tool_names)



    def test_cwe_remediator(self):
        """Verifies CWE-78 and CWE-327 detection and autonomous remediation."""
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "sec.py"
            f.write_text("import subprocess, hashlib\nhashlib.md5()\nsubprocess.run(f'ls {x}', shell=True)\n", encoding="utf-8")
            issues = SecurityCweRemediator.diagnose_file(str(f))
            self.assertGreaterEqual(len(issues), 2)

            for i in issues:
                SecurityCweRemediator.heal_issue(i, dry_run=False)

            new_code = f.read_text(encoding="utf-8")
            self.assertIn("usedforsecurity=False", new_code)
            self.assertIn("shell=False", new_code)

    def test_dead_code_eliminator(self):
        """Verifies unreachable code detection after return."""
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "dead.py"
            f.write_text("def compute():\n    return 42\n    print('dead')\n", encoding="utf-8")
            issues = DeadCodeEliminator.diagnose_file(str(f))
            self.assertTrue(any(i.error_code == "TZ-DEAD-UNREACHABLE" for i in issues))

            for i in issues:
                DeadCodeEliminator.heal_issue(i, dry_run=False)

            self.assertIn("# [T-Zero Dead Code]", f.read_text(encoding="utf-8"))

    def test_async_io_modernizer(self):
        """Verifies conversion of blocking time.sleep to await asyncio.sleep in async def."""
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "async_service.py"
            f.write_text("import time\nasync def process():\n    time.sleep(1)\n", encoding="utf-8")
            issues = AsyncIoModernizer.diagnose_file(str(f))
            self.assertTrue(any(i.error_code == "TZ-ASYNC-BLOCKING-SLEEP" for i in issues))

            for i in issues:
                AsyncIoModernizer.heal_issue(i, dry_run=False)

            new_code = f.read_text(encoding="utf-8")
            self.assertIn("await asyncio.sleep(1)", new_code)
            self.assertIn("import asyncio", new_code)

if __name__ == "__main__":
    unittest.main()
