# -*- coding: utf-8 -*-
"""
Tests for T-Zero Multi-Agent Swarm Blackboard & Working Memory.
Siber Akademi - 100% Free & Zero-Leak Test Suite.
"""

import unittest
import tempfile
import os
import shutil

from tzero_blackboard import MultiAgentBlackboard, get_shared_blackboard


class TestMultiAgentBlackboard(unittest.TestCase):
    """Verifies thread-safe symbol locking, invariants, discoveries, and AST caching."""

    def setUp(self):
        MultiAgentBlackboard.reset_instance()
        self.temp_dir = tempfile.mkdtemp()
        self.bb = MultiAgentBlackboard(workspace_root=self.temp_dir)

    def tearDown(self):
        MultiAgentBlackboard.reset_instance()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_symbol_locking_and_conflict(self):
        # Agent A acquires lock
        granted_a = self.bb.claim_symbol("AgentA", "auth/service.py", "UserAuthService")
        self.assertTrue(granted_a)

        # Agent A re-acquires (reentrant)
        reentrant = self.bb.claim_symbol("AgentA", "auth/service.py", "UserAuthService")
        self.assertTrue(reentrant)

        # Agent B attempts to acquire same symbol (should be rejected)
        granted_b = self.bb.claim_symbol("AgentB", "auth/service.py", "UserAuthService")
        self.assertFalse(granted_b)

        # Agent B cannot release Agent A's lock
        failed_release = self.bb.release_symbol("AgentB", "auth/service.py", "UserAuthService")
        self.assertFalse(failed_release)

        # Agent A releases lock
        ok_release = self.bb.release_symbol("AgentA", "auth/service.py", "UserAuthService")
        self.assertTrue(ok_release)

        # Now Agent B can acquire
        granted_b2 = self.bb.claim_symbol("AgentB", "auth/service.py", "UserAuthService")
        self.assertTrue(granted_b2)

    def test_shared_invariants(self):
        inv_id1 = self.bb.post_invariant(
            source_agent="SecuritySentinel",
            description="All SQL queries in repository must use parameterized binds",
            severity="CRITICAL"
        )
        self.assertTrue(inv_id1.startswith("INV-"))

        invs = self.bb.get_invariants()
        self.assertEqual(len(invs), 1)
        self.assertEqual(invs[0].severity, "CRITICAL")
        self.assertIn("parameterized", invs[0].description)

    def test_discoveries_and_filtering(self):
        self.bb.post_discovery("ArchitectAgent", "ast_analysis", {"classes": 12}, tags=["ast", "backend"])
        self.bb.post_discovery("SecurityAgent", "vuln_scan", {"cwe_count": 0}, tags=["security", "audit"])

        # Filter by topic
        ast_entries = self.bb.query_discoveries(topic="ast_analysis")
        self.assertEqual(len(ast_entries), 1)
        self.assertEqual(ast_entries[0].author_agent, "ArchitectAgent")

        # Filter by tag
        audit_entries = self.bb.query_discoveries(tag="audit")
        self.assertEqual(len(audit_entries), 1)
        self.assertEqual(audit_entries[0].author_agent, "SecurityAgent")

    def test_zero_token_ast_cache(self):
        file_path = "models/user.py"
        ast_summary = "class User:\n  id: str\n  email: str"
        self.bb.cache_ast_summary(file_path, ast_summary)

        cached = self.bb.get_ast_summary(file_path)
        self.assertEqual(cached, ast_summary)

        missing = self.bb.get_ast_summary("unknown.py")
        self.assertIsNone(missing)

    def test_export_status_markdown(self):
        self.bb.claim_symbol("Coder1", "app.py", "MainApp")
        self.bb.post_invariant("Guard", "Never commit plain-text tokens", "CRITICAL")
        self.bb.post_discovery("Worker", "test_run", "All green")

        md = self.bb.export_status_markdown()
        self.assertIn("T-Zero Multi-Agent Blackboard State", md)
        self.assertIn("MainApp", md)
        self.assertIn("Never commit plain-text tokens", md)
        self.assertIn("Worker", md)

    def test_persistence_roundtrip(self):
        json_file = os.path.join(self.temp_dir, "bb.json")
        self.bb.claim_symbol("AgentX", "core.py", "CoreEngine")
        self.bb.post_invariant("Sentinel", "Pure offline mode only", "HIGH")
        self.bb.post_discovery("Reporter", "status", "ready")
        self.bb.persist_to_disk(json_file)

        # Fresh instance loading from disk
        fresh_bb = MultiAgentBlackboard(workspace_root=self.temp_dir)
        loaded = fresh_bb.load_from_disk(json_file)
        self.assertTrue(loaded)

        locks = fresh_bb.get_active_locks()
        self.assertEqual(len(locks), 1)
        self.assertEqual(locks[0].agent_id, "AgentX")

        invs = fresh_bb.get_invariants()
        self.assertEqual(len(invs), 1)
        self.assertEqual(invs[0].source_agent, "Sentinel")


if __name__ == "__main__":
    unittest.main()

