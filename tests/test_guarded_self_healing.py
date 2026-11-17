# -*- coding: utf-8 -*-
from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from tzero.tzero_jarvis.self_healing import (
    ExecutionResult,
    SelfHealingExecutionEngine,
    agent_command_execution_enabled,
    RepairProposal,
)
from tzero.tzero_jarvis.agent_guard import (
    CommandRiskLevel,
    CommandRiskAssessor,
    CommandExecutionPolicy,
    PathGuard,
    SecretRedactor,
    AIGroundingVerifier,
    MultiFileRollbackStack,
    SecurityAuditLogger,
    GLOBAL_AUDIT_LOGGER,
)
from tzero.tzero_jarvis.orchestrator import JarvisOrchestrator


class GuardedHealingTests(unittest.TestCase):
    # -------------------------------------------------------------------------
    # Baseline Existing Tests
    # -------------------------------------------------------------------------

    def test_agent_shell_requires_explicit_operator_opt_in(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(agent_command_execution_enabled())
            os.environ["TZERO_ALLOW_AGENT_SHELL"] = "true"
            self.assertFalse(agent_command_execution_enabled())
            os.environ["TZERO_ALLOW_AGENT_SHELL"] = "1"
            self.assertTrue(agent_command_execution_enabled())

    def test_successful_repair_and_diff(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.py"
            path.write_text("if True\n    print('ok')\n", encoding="utf-8")
            engine = SelfHealingExecutionEngine(work_dir=directory)
            result = engine.execute_and_heal('"{}" "{}"'.format(sys.executable, path))
            self.assertTrue(result.success)
            self.assertTrue(result.applied_patches)
            self.assertIn("+if True:", result.applied_patches[0])

    def test_failed_verification_rolls_back(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.py"
            source = "if True\n    raise ValueError('still broken')\n"
            path.write_text(source, encoding="utf-8")
            engine = SelfHealingExecutionEngine(work_dir=directory)
            result = engine.execute_and_heal('"{}" "{}"'.format(sys.executable, path))
            self.assertFalse(result.success)
            self.assertEqual(path.read_text(encoding="utf-8"), source)
            self.assertIn("restored", result.diagnostics[0])

    def test_rejects_external_paths_and_unsupported_errors(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as other:
            path = Path(other) / "outside.py"
            path.write_text("if True\n    pass\n", encoding="utf-8")
            engine = SelfHealingExecutionEngine(work_dir=directory)
            self.assertIsNone(engine.propose_repair(str(path), "SyntaxError", 1, "SyntaxError: expected ':'"))
            local = Path(directory) / "local.py"
            local.write_text("print(missing)\n", encoding="utf-8")
            self.assertIsNone(engine.propose_repair(str(local), "NameError", 1, "name 'missing' is not defined"))

    def test_preview_does_not_mutate(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.py"
            source = "if True\n    pass\n"
            path.write_text(source, encoding="utf-8")
            proposal = SelfHealingExecutionEngine(work_dir=directory).propose_repair(
                str(path), "SyntaxError", 1, "SyntaxError: expected ':'")
            self.assertIsNotNone(proposal)
            self.assertEqual(path.read_text(encoding="utf-8"), source)

    def test_successful_command_that_changes_file_is_not_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.py"
            path.write_text("if True\n    pass\n", encoding="utf-8")
            engine = SelfHealingExecutionEngine(work_dir=directory)
            first = ExecutionResult("test", 1, "", "SyntaxError: expected ':'", 1, False,
                                    "SyntaxError", 1, str(path))

            def run(command):
                path.write_text("# external edit\n", encoding="utf-8")
                return ExecutionResult(command, 0, "", "", 1, True, resolved=True)

            def calls(command):
                if path.read_text(encoding="utf-8").startswith("if True:"):
                    return run(command)
                return first

            with patch.object(engine, "run_command", side_effect=calls):
                result = engine.execute_and_heal("test")
            self.assertFalse(result.success)
            self.assertFalse(result.resolved)
            self.assertEqual(path.read_text(encoding="utf-8"), "# external edit\n")
            self.assertIn("changed during verification", result.diagnostics[0])

    def test_atomic_replace_rejects_stale_proposal(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.py"
            path.write_text("if True\n    pass\n", encoding="utf-8")
            engine = SelfHealingExecutionEngine(work_dir=directory)
            proposal = engine.propose_repair(str(path), "SyntaxError", 1, "SyntaxError: expected ':'")
            path.write_text("# newer edit\n", encoding="utf-8")
            self.assertFalse(engine._replace_if_unchanged(proposal.path, proposal.original, proposal.replacement))
            self.assertEqual(path.read_text(encoding="utf-8"), "# newer edit\n")
            self.assertFalse(list(Path(directory).glob(".tzero-heal-*")))

    # -------------------------------------------------------------------------
    # 20+ New Advanced Guardrails & AI Safety Tests
    # -------------------------------------------------------------------------

    # 1. Command Risk Assessor: Classification
    def test_command_risk_assessor_classification(self):
        # Read-only commands
        ev_ro = CommandRiskAssessor.assess("git status")
        self.assertEqual(ev_ro.risk_level, CommandRiskLevel.SAFE_READ_ONLY)
        self.assertTrue(ev_ro.allowed)

        # Network tools
        ev_net = CommandRiskAssessor.assess("curl https://example.com")
        self.assertEqual(ev_net.risk_level, CommandRiskLevel.NETWORK_OR_PACKAGE)
        self.assertTrue(ev_net.involves_network)

        # Package manager installation
        ev_pip = CommandRiskAssessor.assess("pip install requests")
        self.assertEqual(ev_pip.risk_level, CommandRiskLevel.NETWORK_OR_PACKAGE)
        self.assertTrue(ev_pip.involves_package_install)

        # Destructive commands
        ev_rm = CommandRiskAssessor.assess("rm -rf /")
        self.assertEqual(ev_rm.risk_level, CommandRiskLevel.DESTRUCTIVE)
        self.assertTrue(ev_rm.involves_destruction)

        # Shell chaining and redirection
        ev_chain = CommandRiskAssessor.assess("echo 1 && echo 2")
        self.assertEqual(ev_chain.risk_level, CommandRiskLevel.BLOCKED_OR_SUSPICIOUS)
        self.assertTrue(ev_chain.is_chained)

        ev_redir = CommandRiskAssessor.assess("echo test > out.txt")
        self.assertEqual(ev_redir.risk_level, CommandRiskLevel.BLOCKED_OR_SUSPICIOUS)
        self.assertTrue(ev_redir.has_redirection)

    # 2. Operator vs Agent Privilege Separation Policy
    def test_command_execution_policy_from_environment(self):
        with patch.dict(os.environ, {}, clear=True):
            pol = CommandExecutionPolicy.from_environment()
            self.assertFalse(pol.allow_agent_shell)
            self.assertFalse(pol.allow_network)
            self.assertFalse(pol.allow_package_install)
            self.assertFalse(pol.allow_destructive)

        with patch.dict(os.environ, {
            "TZERO_ALLOW_AGENT_SHELL": "1",
            "TZERO_ALLOW_NETWORK": "1",
            "TZERO_ALLOW_PACKAGE_INSTALL": "1"
        }):
            pol_opt = CommandExecutionPolicy.from_environment()
            self.assertTrue(pol_opt.allow_agent_shell)
            self.assertTrue(pol_opt.allow_network)
            self.assertTrue(pol_opt.allow_package_install)

    # 3. Agent Shell Default-Deny Policy Enforcement in Engine
    def test_agent_policy_enforcement_in_engine(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {}, clear=True):
                # When enforce_agent_policy is True, default policy rejects execution
                engine = SelfHealingExecutionEngine(work_dir=directory, enforce_agent_policy=True)
                res = engine.run_command("git status")
                self.assertFalse(res.success)
                self.assertTrue(res.blocked_by_policy)
                self.assertIn("Agent shell execution is disabled by default", res.stderr)

    # 4. Argv Execution Without Host Shell (shell=False)
    def test_argv_execution_without_host_shell(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = SelfHealingExecutionEngine(work_dir=directory)
            # Standard single command runs with argv
            res = engine.run_command('python -c "import sys; print(sys.argv)"')
            self.assertTrue(res.success)
            self.assertEqual(res.exit_code, 0)

    # 5. Network and Package Installation Blocked Even When Shell Opt-In Is Given
    def test_package_and_network_blocked_by_default_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"TZERO_ALLOW_AGENT_SHELL": "1"}):
                engine = SelfHealingExecutionEngine(work_dir=directory, enforce_agent_policy=True)
                res_pip = engine.run_command("pip install requests")
                self.assertFalse(res_pip.success)
                self.assertTrue(res_pip.blocked_by_policy)
                self.assertIn("zero-spend policy forbids", res_pip.stderr)

                res_curl = engine.run_command("curl http://example.com")
                self.assertFalse(res_curl.success)
                self.assertTrue(res_curl.blocked_by_policy)
                self.assertIn("zero-spend & privacy policy forbids", res_curl.stderr)

    # 6. Path Guard: Directory Traversal Protection
    def test_path_guard_directory_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            valid, reason, resolved = PathGuard.validate_target_path("../outside.py", directory)
            self.assertFalse(valid)
            self.assertIn("traversal", reason.lower())

    # 7. Path Guard: Workspace Boundary Enforcement
    def test_path_guard_workspace_boundary(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            outside_file = Path(outside) / "forbidden.py"
            outside_file.write_text("x = 1\n", encoding="utf-8")
            valid, reason, resolved = PathGuard.validate_target_path(str(outside_file), directory)
            self.assertFalse(valid)
            self.assertIn("escapes workspace", reason)

    # 8. Path Guard: Protected Files and Directories Protection
    def test_path_guard_protected_files(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("SECRET=123\n", encoding="utf-8")
            valid, reason, _ = PathGuard.validate_target_path(str(env_file), directory)
            self.assertFalse(valid)
            self.assertIn("protected configuration file", reason)

            key_file = Path(directory) / "server.key"
            key_file.write_text("key\n", encoding="utf-8")
            valid_key, reason_key, _ = PathGuard.validate_target_path(str(key_file), directory)
            self.assertFalse(valid_key)
            self.assertIn("protected key/certificate", reason_key)

    # 9. Path Guard: Maximum File Size Limit
    def test_path_guard_file_size_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            large_file = Path(directory) / "huge.py"
            # Write a file slightly over limit
            large_file.write_bytes(b"a" * (PathGuard.MAX_SAFE_FILE_SIZE_BYTES + 10))
            valid, reason, _ = PathGuard.validate_target_path(str(large_file), directory)
            self.assertFalse(valid)
            self.assertIn("exceeds maximum safe repair threshold", reason)

    # 10. Secret Redaction: Pattern-based Masking
    def test_secret_redactor_patterns(self):
        raw = (
            "Traceback: AWS AKIAIOSFODNN7EXAMPLE and "
            "token ghp_123456789012345678901234567890123456 "
            "and Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-ID"
        )
        clean = SecretRedactor.sanitize(raw)
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", clean)
        self.assertNotIn("ghp_123456789012345678901234567890123456", clean)
        self.assertIn("[REDACTED_SECRET]", clean)

    # 11. Secret Redaction: Shannon Entropy Masking
    def test_secret_redactor_shannon_entropy(self):
        high_entropy_token = "K8xZ7wQ1vP9mN4bV2cX0lJ3hG5fD6sA7"
        raw = f"Encountered mystery API token: {high_entropy_token}"
        clean = SecretRedactor.sanitize(raw)
        self.assertNotIn(high_entropy_token, clean)
        self.assertIn("[REDACTED_SECRET]", clean)

    # 12. Secret Redaction in Engine Output
    def test_secret_redaction_in_engine_output(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = SelfHealingExecutionEngine(work_dir=directory)
            res = engine.run_command('python -c "print(\'leak AKIAIOSFODNN7EXAMPLE\')"', timeout=10)
            self.assertTrue(res.success)
            self.assertNotIn("AKIAIOSFODNN7EXAMPLE", res.stdout)
            self.assertIn("[REDACTED_SECRET]", res.stdout)

    # 13. AI Grounding: File and Line Verification
    def test_ai_grounding_file_and_line_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            f = Path(directory) / "sample.py"
            f.write_text("line 1\nline 2\nline 3\n", encoding="utf-8")

            # Existing file & valid line
            f_ok, _, _ = AIGroundingVerifier.verify_file(directory, "sample.py")
            self.assertTrue(f_ok)

            l_ok, _ = AIGroundingVerifier.verify_line(directory, "sample.py", 2)
            self.assertTrue(l_ok)

            # Line out of bounds (hallucinated line)
            l_fail, reason = AIGroundingVerifier.verify_line(directory, "sample.py", 99)
            self.assertFalse(l_fail)
            self.assertIn("out of bounds", reason)

            # Non-existent file (hallucinated file)
            f_fail, reason_f, _ = AIGroundingVerifier.verify_file(directory, "ghost.py")
            self.assertFalse(f_fail)
            self.assertIn("not found in workspace", reason_f)

    # 14. AI Grounding: Python AST Symbol Verification
    def test_ai_grounding_python_symbol_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "symbols.py"
            p.write_text("class MyService:\n    def execute(self):\n        return True\n", encoding="utf-8")

            # Existing class & method
            ok_cls, _, kind_cls, l_cls = AIGroundingVerifier.verify_python_symbol(directory, "symbols.py", "MyService")
            self.assertTrue(ok_cls)
            self.assertEqual(kind_cls, "class")
            self.assertEqual(l_cls, 1)

            ok_fn, _, kind_fn, _ = AIGroundingVerifier.verify_python_symbol(directory, "symbols.py", "execute")
            self.assertTrue(ok_fn)
            self.assertEqual(kind_fn, "function")

            # Phantom function (hallucinated symbol)
            ok_ghost, reason_g, _, _ = AIGroundingVerifier.verify_python_symbol(directory, "symbols.py", "phantom_method")
            self.assertFalse(ok_ghost)
            self.assertIn("not found in AST", reason_g)

    # 15. AI Grounding: Traceback Evidence Audit
    def test_ai_grounding_traceback_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            real_file = Path(directory) / "app.py"
            real_file.write_text("def run():\n    pass\n", encoding="utf-8")

            tb = f'''Traceback (most recent call last):
  File "{real_file}", line 1, in run
  File "phantom_lib.py", line 42, in ghost_call
'''
            audit = AIGroundingVerifier.audit_traceback_evidence(directory, tb)
            self.assertEqual(audit["total_frames"], 2)
            self.assertEqual(len(audit["verified_frames"]), 1)
            self.assertEqual(len(audit["unverified_frames"]), 1)
            self.assertTrue(audit["has_grounded_target"])

    # 16. AI Grounding: Unverified / Absolute Claim Flagging
    def test_flag_unverified_claims(self):
        claim_text = "This engine provides 100% guaranteed leak-proof operations and a zero defect guarantee."
        flags = AIGroundingVerifier.flag_unverified_claims(claim_text)
        self.assertTrue(len(flags) >= 2)
        self.assertTrue(any("cannot be verified mathematically" in f for f in flags))

    # 17. Multi-File Rollback Stack: Transactional Reversal
    def test_multi_file_rollback_stack(self):
        with tempfile.TemporaryDirectory() as directory:
            f1 = Path(directory) / "file1.py"
            f2 = Path(directory) / "file2.py"
            f1.write_bytes(b"original 1\n")
            f2.write_bytes(b"original 2\n")

            stack = MultiFileRollbackStack()
            # Step 1: modify file 1
            f1.write_bytes(b"modified 1\n")
            stack.push(f1, b"original 1\n", b"modified 1\n", "patch 1")

            # Step 2: modify file 2
            f2.write_bytes(b"modified 2\n")
            stack.push(f2, b"original 2\n", b"modified 2\n", "patch 2")

            # Transaction fails -> rollback all
            diag = stack.rollback_all()
            self.assertEqual(f1.read_bytes(), b"original 1\n")
            self.assertEqual(f2.read_bytes(), b"original 2\n")
            self.assertTrue(len(diag) >= 2)

    # 18. Anti-Cycling Guard: Prevent Reapplying Same Failed Patch
    def test_anti_cycling_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cycle.py"
            path.write_text("if True\n    raise RuntimeError('permanent error')\n", encoding="utf-8")
            engine = SelfHealingExecutionEngine(work_dir=directory)

            # First attempt fails verification and rolls back
            res1 = engine.execute_and_heal('"{}" "{}"'.format(sys.executable, path))
            self.assertFalse(res1.success)

            # Second attempt with same patch should trigger anti-cycling guard
            res2 = engine.execute_and_heal('"{}" "{}"'.format(sys.executable, path))
            self.assertFalse(res2.success)
            self.assertTrue(any("Anti-cycling guard" in d for d in res2.diagnostics))

    # 19. Dry-Run Mode in Engine
    def test_dry_run_mode_in_engine(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dry.py"
            source = "if True\n    print('dry')\n"
            path.write_text(source, encoding="utf-8")
            engine = SelfHealingExecutionEngine(work_dir=directory)

            res = engine.execute_and_heal('"{}" "{}"'.format(sys.executable, path), dry_run=True)
            self.assertTrue(res.dry_run)
            self.assertEqual(path.read_text(encoding="utf-8"), source)
            self.assertTrue(any("[Dry-Run]" in d for d in res.diagnostics))

    # 20. Security Audit Logger
    def test_security_audit_logger(self):
        logger = SecurityAuditLogger(capacity=10)
        logger.record("COMMAND_BLOCKED", "rm -rf /", "DENY", "Destructive operation", {"user": "agent"})
        events = logger.get_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "COMMAND_BLOCKED")
        self.assertEqual(events[0]["verdict"], "DENY")

    # 21. Jarvis Orchestrator Guarded Terminal Execution
    def test_orchestrator_execute_terminal_guarded(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"TZERO_ENFORCE_AGENT_POLICY": "1"}, clear=True):
                orch = JarvisOrchestrator(workspace_root=directory)
                # Without TZERO_ALLOW_AGENT_SHELL, execution is blocked
                res = orch.execute_terminal("python -c \"print('orchestrator')\"")
                self.assertFalse(res["success"])
                self.assertIn("blocked by safety policy", res["stderr"])

    # 22. Strict Verification Evidence for Success
    def test_strict_verification_evidence_for_success(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fail.py"
            path.write_text("if True\n    exit(1)\n", encoding="utf-8")
            engine = SelfHealingExecutionEngine(work_dir=directory)
            res = engine.execute_and_heal('"{}" "{}"'.format(sys.executable, path))
            self.assertFalse(res.success)
            self.assertFalse(res.resolved)


if __name__ == "__main__":
    unittest.main()
