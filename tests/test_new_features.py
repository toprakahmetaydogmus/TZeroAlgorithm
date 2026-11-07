# -*- coding: utf-8 -*-
"""
Tests for T-Zero Next-Gen Sovereign Features:
1. SnapshotEngine (sub-10ms AST context cache)
2. ASTHallucinationAutoCorrector (self-healing phantom symbols)
3. PolyglotTypeBridge (transpiles Python models to TS, Rust, Go)
4. HistoricalTokenReplay (git history token & financial ROI)
"""

import os
import sys
import unittest
import tempfile
import shutil

from tzero_snapshot import SnapshotEngine, SnapshotResult
from tzero_fix import ASTHallucinationAutoCorrector, HealingReport
from tzero_bridge import PolyglotTypeBridge, TranspiledModel
from tzero_replay import HistoricalTokenReplay, ReplaySummary


class TestNextGenFeatures(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.sample_py = os.path.join(self.test_dir, "sample_models.py")
        with open(self.sample_py, "w", encoding="utf-8") as f:
            f.write('''
from dataclasses import dataclass
from typing import Optional, List, Dict

@dataclass
class UserProfile:
    """Represents a verified user profile."""
    username: str
    user_id: int
    is_active: bool
    email: Optional[str]
    roles: List[str]
    metadata: Dict[str, str]

def calculate_token_savings(raw: int, pruned: int) -> float:
    """Computes percentage savings."""
    return (1.0 - (pruned / max(1, raw))) * 100.0

class AccountService:
    def get_user_account(self, uid: int):
        return {"id": uid}
''')

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # 1. SnapshotEngine Tests
    def test_snapshot_create_and_load(self):
        snap = SnapshotEngine.create_snapshot(self.test_dir)
        self.assertIsInstance(snap, SnapshotResult)
        self.assertEqual(snap.file_count, 1)
        self.assertGreater(snap.total_raw_tokens, 0)
        self.assertGreater(snap.reduction_pct, 0.0)

        # Load from disk
        loaded = SnapshotEngine.load_snapshot(self.test_dir)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.file_count, snap.file_count)
        self.assertTrue(SnapshotEngine.is_valid(loaded, self.test_dir))

        # Get or create (cached)
        cached_snap, was_cached = SnapshotEngine.get_or_create(self.test_dir)
        self.assertTrue(was_cached)
        self.assertEqual(cached_snap.file_count, 1)

    # 2. ASTHallucinationAutoCorrector Tests
    def test_heal_phantom_import_and_method(self):
        buggy_code = '''
from sample_models import calculate_token_saving, UserProfile

acc = AccountService()
acc.get_user_acc(123)
'''
        report = ASTHallucinationAutoCorrector.heal_code(buggy_code, workspace_dir=self.test_dir)
        self.assertTrue(report.success)
        self.assertGreater(report.total_fixes, 0)
        # Should heal calculate_token_saving -> calculate_token_savings
        self.assertIn("calculate_token_savings", report.healed_code)
        # Should heal get_user_acc -> get_user_account
        self.assertIn("get_user_account", report.healed_code)

    def test_heal_clean_code_noop(self):
        clean_code = '''
from sample_models import calculate_token_savings
val = calculate_token_savings(100, 20)
'''
        report = ASTHallucinationAutoCorrector.heal_code(clean_code, workspace_dir=self.test_dir)
        self.assertTrue(report.success)
        self.assertEqual(report.total_fixes, 0)

    # 3. PolyglotTypeBridge Tests
    def test_polyglot_bridge_transpilation(self):
        with open(self.sample_py, "r", encoding="utf-8") as f:
            code = f.read()

        models = PolyglotTypeBridge.parse_python_models(code)
        self.assertEqual(len(models), 1)
        m = models[0]
        self.assertEqual(m.class_name, "UserProfile")

        # TypeScript check
        ts_out = PolyglotTypeBridge.transpile_file(self.sample_py, "ts")
        self.assertIn("export interface UserProfile", ts_out)
        self.assertIn("username: string;", ts_out)
        self.assertIn("user_id: number;", ts_out)
        self.assertIn("is_active: boolean;", ts_out)
        self.assertIn("email?: string | null;", ts_out)
        self.assertIn("roles: string[];", ts_out)

        # Rust check
        rust_out = PolyglotTypeBridge.transpile_file(self.sample_py, "rust")
        self.assertIn("pub struct UserProfile", rust_out)
        self.assertIn("pub username: String,", rust_out)
        self.assertIn("pub user_id: i64,", rust_out)
        self.assertIn("pub email: Option<String>,", rust_out)

        # Go check
        go_out = PolyglotTypeBridge.transpile_file(self.sample_py, "go")
        self.assertIn("type UserProfile struct", go_out)
        self.assertIn("Username string", go_out)
        self.assertIn("Email *string", go_out)

        # Kotlin check
        kt_out = PolyglotTypeBridge.transpile_file(self.sample_py, "kt")
        self.assertIn("data class UserProfile(", kt_out)
        self.assertIn("val username: String", kt_out)
        self.assertIn("val email: String? = null", kt_out)

        # Swift check
        swift_out = PolyglotTypeBridge.transpile_file(self.sample_py, "swift")
        self.assertIn("public struct UserProfile: Codable, Equatable", swift_out)
        self.assertIn("public let username: String", swift_out)
        self.assertIn("public let email: String?", swift_out)

    # 4. HistoricalTokenReplay Tests
    def test_historical_replay(self):
        # Run replay on active git repo
        rep = HistoricalTokenReplay.replay_history(repo_dir=".", max_commits=5)
        self.assertIsInstance(rep, ReplaySummary)
        self.assertGreaterEqual(rep.commits_analyzed, 1)
        self.assertGreater(rep.total_raw_tokens, 0)
        self.assertGreaterEqual(rep.savings_claude_sonnet, 0.0)

    # 5. PCFixerDoctor Tests
    def test_pc_fixer_doctor(self):
        from tzero_pc_fixer import PCFixerDoctor
        diag = PCFixerDoctor.diagnose(self.test_dir)
        self.assertGreaterEqual(diag.health_score_pct, 90)
        self.assertEqual(diag.syntax_errors, 0)

        # Introduce syntax flaw
        flaw_file = os.path.join(self.test_dir, "flaw.py")
        with open(flaw_file, "w", encoding="utf-8") as f:
            f.write("def broken_func()\n    pass\n")
        diag_flaw = PCFixerDoctor.diagnose(self.test_dir)
        self.assertEqual(diag_flaw.syntax_errors, 1)

        heal_res = PCFixerDoctor.auto_heal(self.test_dir, dry_run=False)
        self.assertGreaterEqual(heal_res.issues_healed, 1)
        diag_fixed = PCFixerDoctor.diagnose(self.test_dir)
        self.assertEqual(diag_fixed.syntax_errors, 0)

    # 6. ArchitecturalPassportGenerator Tests
    def test_architectural_passport(self):
        from tzero_explain import ArchitecturalPassportGenerator, ModulePassport
        passport = ArchitecturalPassportGenerator.explain_file(self.sample_py)
        self.assertIsInstance(passport, ModulePassport)
        self.assertEqual(passport.module_name, "sample_models")
        self.assertIn("class UserProfile", passport.markdown_passport)
        self.assertIn("class AccountService", passport.markdown_passport)
        self.assertGreater(passport.raw_tokens, 0)


if __name__ == "__main__":
    unittest.main()

