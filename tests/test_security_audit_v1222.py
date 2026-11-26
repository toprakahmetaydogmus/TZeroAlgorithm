# -*- coding: utf-8 -*-
"""Acceptance regression tests covering all 14+ v12.2.2 security & Anti-REA hardening fixes."""

import ast
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class TestSecurityAndAntiREAHardening(unittest.TestCase):
    def test_01_pem_multiline_redaction_and_incomplete_block_abort(self):
        from tzero.tzero_security import ZeroLeakEngine

        complete_pem = (
            "HEADER_KEEP = 'ok'\n"
            "KEY = '''-----BEGIN RSA PRIVATE KEY-----\n"
            "MIIEowIBAAKCAQEA0FAKEBODYLINEONE1234567890\n"
            "SECONDFAKEBODYLINEABCDEFGHIJKLMN\n"
            "-----END RSA PRIVATE KEY-----'''\n"
            "FOOTER_KEEP = 'still_here'\n"
        )
        sanitized = ZeroLeakEngine.sanitize_text(complete_pem)
        self.assertNotIn("MIIEowIBAAKCAQEA0FAKEBODYLINEONE1234567890", sanitized)
        self.assertNotIn("SECONDFAKEBODYLINEABCDEFGHIJKLMN", sanitized)
        self.assertIn("[ZERO_LEAK_MASKED_PRIVATE_KEY]", sanitized)
        self.assertIn("HEADER_KEEP", sanitized)
        self.assertIn("FOOTER_KEEP", sanitized)

        incomplete_pem = "-----BEGIN EC PRIVATE KEY-----\nUNCLOSED_BODY_SECRET_DATA_12345"
        with self.assertRaises(ValueError):
            ZeroLeakEngine.sanitize_text(incomplete_pem)

    def test_02_ast_and_text_redaction_parity(self):
        from tzero.tzero_security import ZeroLeakEngine

        fake_secret = "q7X9mLz2vBw4kP8jR5tY1nEaBcDeFgHiJkLmNoPqRsTuVw"
        src = f'NORMAL = "hello world"\nSECRET = "{fake_secret}"\n'
        sanitized_text = ZeroLeakEngine.sanitize_text(src)
        tree = ZeroLeakEngine.sanitize_ast(ast.parse(src))
        unparsed_ast = ast.unparse(tree)

        self.assertNotIn(fake_secret, sanitized_text)
        self.assertNotIn(fake_secret, unparsed_ast)
        self.assertIn("hello world", unparsed_ast)
        self.assertEqual(ZeroLeakEngine.scan_text(unparsed_ast), [])

    def test_03_04_05_06_autovault_atomic_collision_lhs_and_gitignore(self):
        from tzero.tzero_security import ZeroLeakEngine

        k1 = "sk-" + "proj-" + "111122223333444455556666777788889999aaaa"
        k2 = "sk-" + "proj-" + "bbbbccccddddeeeeffff00001111222233334444"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / ".gitignore").write_text("# .env comment only\n.env.example\n", encoding="utf-8")
            gi_status_before = ZeroLeakEngine.check_env_git_status(str(p / ".env"), str(p / ".gitignore"))
            self.assertFalse(gi_status_before["ignored"])

            f1 = p / "a.py"
            f2 = p / "b.py"
            f1.write_text(f'api_key = "{k1}"\ndef get_val():\n    return api_key\n', encoding="utf-8")
            f2.write_text(f'api_key = "{k2}"\ndef get_val():\n    return api_key\n', encoding="utf-8")

            # Simulated write failure must preserve original files untouched
            with patch("tempfile.NamedTemporaryFile", side_effect=PermissionError("read-only .env")):
                fail_res = ZeroLeakEngine.migrate_files_atomically([str(f1)], str(p / ".env"), str(p / ".gitignore"))
            self.assertFalse(fail_res["success"])
            self.assertIn(k1, f1.read_text(encoding="utf-8"))

            res = ZeroLeakEngine.migrate_files_atomically([str(f1), str(f2)], str(p / ".env"), str(p / ".gitignore"))
            self.assertTrue(res["success"], res)
            env_txt = (p / ".env").read_text(encoding="utf-8")
            self.assertIn(f"={k1}", env_txt)
            self.assertIn(f"={k2}", env_txt)

            # LHS assignment preserved and resolves to distinct env vars
            code1 = f1.read_text(encoding="utf-8")
            code2 = f2.read_text(encoding="utf-8")
            self.assertIn("api_key = os.environ.get(", code1)
            self.assertIn("api_key = os.environ.get(", code2)

            # Verify migrated programs resolve their distinct original secrets
            ns1, ns2 = {}, {}
            with patch.dict(os.environ, {"OPENAI_API_KEY": k1, "OPENAI_API_KEY_2": k2}, clear=False):
                exec(code1, ns1)
                exec(code2, ns2)
            self.assertNotEqual(ns1["get_val"](), ns2["get_val"]())
            self.assertEqual({ns1["get_val"](), ns2["get_val"]()}, {k1, k2})

            # Repeat migration is idempotent (zero duplicate .env lines)
            res_repeat = ZeroLeakEngine.migrate_files_atomically([str(f1), str(f2)], str(p / ".env"), str(p / ".gitignore"))
            self.assertEqual(res_repeat["migrated_count"], 0)
            self.assertEqual((p / ".env").read_text(encoding="utf-8"), env_txt)
            self.assertTrue(ZeroLeakEngine.check_env_git_status(str(p / ".env"), str(p / ".gitignore"))["ignored"])

    def test_07_armor_directory_separate_output_preserves_originals(self):
        from tzero.tzero_armor import protect_path_with_armor

        with tempfile.TemporaryDirectory() as tmp:
            src_dir = Path(tmp) / "src"
            out_dir = Path(tmp) / "out"
            src_dir.mkdir()
            orig_code = "def mul2(x):\n    return x * 2\n"
            f_ok = src_dir / "mod.py"
            f_ok.write_text(orig_code, encoding="utf-8")

            res = protect_path_with_armor(str(src_dir), output_path=str(out_dir), vm_container=False, anti_vm=False, rdtsc_guard=False)
            self.assertTrue(res["success"])
            self.assertEqual(res["files_failed"], 0)
            self.assertEqual(f_ok.read_text(encoding="utf-8"), orig_code, "Originals must remain unmodified when out_dir is separate")
            self.assertTrue((out_dir / "mod.py").is_file())

    def test_08_mcp_scan_inspects_full_raw_bodies_including_beyond_15k(self):
        from tzero.tzero_mcp import create_mcp_server

        server = create_mcp_server()
        self.assertIsNotNone(server)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "worker.py"
            body = "def process():\n" + ("    x = 1\n" * 3000) + '    tok = "ghp_' + ("A1b2C3d4E5f6" * 3) + '"\n    return tok\n'
            p.write_text(body, encoding="utf-8")
            tool = server._tool_manager._tools.get("verify_security_guard")
            report = tool.fn(action="scan", project_root=tmp)
            self.assertIn("[ZERO-LEAK ALERT]", report)
            self.assertIn("worker.py", report)
            self.assertIn("Line 3002", report)

    def test_09_10_git_hook_preserves_custom_hook_and_fails_on_git_error(self):
        from tzero.tzero_guard import GitSecurityGuard

        with tempfile.TemporaryDirectory() as tmp:
            hooks_dir = Path(tmp) / ".git" / "hooks"
            hooks_dir.mkdir(parents=True)
            hook = hooks_dir / "pre-commit"
            custom = "#!/bin/sh\necho CUSTOM_TEAM_HOOK\nexit 0\n"
            hook.write_text(custom, encoding="utf-8")

            r1 = GitSecurityGuard.install_hook(tmp)
            self.assertTrue(r1["success"])
            self.assertTrue(r1["preserved_existing"])
            self.assertIn("pre-commit.user-backup", hook.read_text(encoding="utf-8"))
            self.assertEqual((hooks_dir / "pre-commit.user-backup").read_text(encoding="utf-8"), custom)

            # Second install remains idempotent and preserves backup
            r2 = GitSecurityGuard.install_hook(tmp)
            self.assertTrue(r2["success"])
            self.assertEqual((hooks_dir / "pre-commit.user-backup").read_text(encoding="utf-8"), custom)

            # Uninstall restores original custom hook cleanly
            GitSecurityGuard.uninstall_hook(tmp)
            self.assertEqual(hook.read_text(encoding="utf-8"), custom)

            # Simulate failing git diff --cached -> must exit 1, never 0
            with patch("subprocess.run", return_value=subprocess.CompletedProcess(["git"], 128, "", "fatal: corrupt index")):
                self.assertEqual(GitSecurityGuard.run_cli_check(tmp), 1)

    def test_11_mcp_skeleton_blocks_traversal_and_symlink_escape(self):
        from tzero.tzero_mcp import create_mcp_server

        server = create_mcp_server()
        tpl = server._resource_manager._templates.get("tzero://file/{path}/skeleton")
        self.assertIsNotNone(tpl)
        blocked = tpl.fn("../outside.py")
        self.assertIn("[BLOCKED]", blocked)

    def test_12_legacy_backup_schema_validation_blocks_corrupt_payload(self):
        from tzero.tzero_v3 import KeyringSecretsBackupManager

        with tempfile.TemporaryDirectory() as tmp:
            bad_path = os.path.join(tmp, "bad.dat")
            # XOR encrypt non-dict payload [1, 2, 3]
            raw = b"[1, 2, 3]"
            key = b"pass"
            enc = bytes([b ^ key[i % len(key)] for i, b in enumerate(raw)])
            Path(bad_path).write_bytes(enc)
            calls = []
            with patch("keyring.set_password", side_effect=lambda *a: calls.append(a)):
                ok = KeyringSecretsBackupManager.restore_credentials(bad_path, "pass")
            self.assertFalse(ok)
            self.assertEqual(calls, [])

    def test_13_proxy_enforces_body_size_limits_and_recovers(self):
        from tzero.tzero_proxy import start_context_proxy

        srv = start_context_proxy(host="127.0.0.1", port=0, max_concurrent=4)
        port = srv.server_address[1]
        try:
            oversized_req = urllib.request.Request(
                f"http://127.0.0.1:{port}/v1/chat/completions",
                data=b"x" * (2 * 1024 * 1024 + 64),
                headers={"Content-Type": "application/json"},
            )
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(oversized_req, timeout=5)
            self.assertEqual(ctx.exception.code, 413)
            ctx.exception.close()

            # Subsequent valid request still succeeds cleanly
            ok_req = urllib.request.Request(
                f"http://127.0.0.1:{port}/v1/chat/completions",
                data=json.dumps({"messages": [{"role": "user", "content": "hi"}]}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(ok_req, timeout=5) as resp:
                self.assertEqual(resp.status, 200)
        finally:
            srv.shutdown()
            srv.server_close()

    def test_anti_rea_future_annotations_utf8_integrity_and_cli_missing(self):
        from tzero.anti_rea.engine import AntiREAEngine
        from tzero.anti_rea.string_vault import StringVault
        from tzero.anti_rea.auditor import AIResistanceAuditor

        # 1. StringVault preserves Turkish UTF-8 strings faithfully
        src_utf8 = 'def selam():\n    return "Türkçe Şığüöç"\n'
        vaulted = StringVault.vault_source_code(src_utf8)
        ns = {}
        exec(vaulted, ns)
        self.assertEqual(ns["selam"](), "Türkçe Şığüöç")

        # 2. from __future__ import annotations stays valid & compiles under protect_python_source
        src_future = 'from __future__ import annotations\n\ndef f(x: int) -> int:\n    return x + 1\n'
        protected = AntiREAEngine.protect_python_source(
            src_future, flatten=False, anti_vm=False, rdtsc_guard=False, anti_debugger=False, timing_guard=False, anti_agent_guard=False, vm_container=False
        )
        compile(protected, "<test>", "exec")

        # 3. Turkish-only comments must NOT earn homoglyph 10/100 score
        audit_tr = AIResistanceAuditor.audit_python_source("# Merhaba Türkçe yorum\nx = 1\n")
        self.assertEqual(audit_tr["score"], 0)
        self.assertEqual(audit_tr["score_kind"], "static_textual_indicator")

        # 4. Windows/Python CLI exits non-zero on missing audit-rea target
        missing = REPO_ROOT / "nonexistent_target_xyz_123.py"
        cli_res = subprocess.run(
            [sys.executable, "-m", "tzero.tzero_v3", "audit-rea", str(missing)],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=10,
        )
        self.assertNotEqual(cli_res.returncode, 0)


if __name__ == "__main__":
    unittest.main()
