from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import os

from tzero.tzero_jarvis.self_healing import (
    ExecutionResult, SelfHealingExecutionEngine, agent_command_execution_enabled,
)


class GuardedHealingTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
