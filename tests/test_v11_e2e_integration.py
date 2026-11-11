# -*- coding: utf-8 -*-
"""End-to-end integration tests for T-Zero v11 Frontier capabilities and --doctor --deep."""

import contextlib
import io
import json
import os
import pathlib
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tzero import tzero_deps
from tzero.tzero_contracts import ASTContractComparator, SemVerBump
from tzero.tzero_federation import FederationSyncEngine
from tzero.tzero_hooks import evaluate_post_tool_use, evaluate_pre_tool_use, install_hooks
from tzero.tzero_lsp import TZeroLSPServer
from tzero.tzero_packer import pack_workspace
from tzero.tzero_rust_bridge import AgentKernelSandbox
from tzero.tzero_scip import ScipIndexImporter
from tzero.tzero_snapshot import SnapshotEngine

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _encode_varint(value: int) -> bytes:
    buf = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            buf.append(byte | 0x80)
        else:
            buf.append(byte)
            break
    return bytes(buf)


def _encode_scip_protobuf_sample(def_file: str, ref_file: str, symbol: str) -> bytes:
    def _field(tag: int, wire_type: int, payload: bytes) -> bytes:
        return _encode_varint((tag << 3) | wire_type) + payload

    def _string(tag: int, text: str) -> bytes:
        raw = text.encode("utf-8")
        return _field(tag, 2, _encode_varint(len(raw)) + raw)

    def _msg(tag: int, inner: bytes) -> bytes:
        return _field(tag, 2, _encode_varint(len(inner)) + inner)

    def_range = _encode_varint(2) + _encode_varint(4)
    def_occ = (
        _field(1, 2, _encode_varint(len(def_range)) + def_range)
        + _string(2, symbol)
        + _field(3, 0, _encode_varint(1))
    )
    def_doc = _string(1, def_file) + _msg(2, def_occ)

    ref_range = _encode_varint(8) + _encode_varint(12)
    ref_occ = (
        _field(1, 2, _encode_varint(len(ref_range)) + ref_range)
        + _string(2, symbol)
        + _field(3, 0, _encode_varint(0))
    )
    ref_doc = _string(1, ref_file) + _msg(2, ref_occ)

    return _msg(2, def_doc) + _msg(2, ref_doc)


class TestV11EndToEndIntegration(unittest.TestCase):
    def test_v11_polyglot_e2e_pipeline(self):
        fake_key = "sk" + "-proj-" + "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8"

        with tempfile.TemporaryDirectory() as host_ws, tempfile.TemporaryDirectory() as peer_ws:
            auth_py = os.path.join(host_ws, "auth.py")
            with open(auth_py, "w", encoding="utf-8") as fh:
                fh.write(
                    "class SessionGuard:\n"
                    "    def validate_session(self, token: str) -> bool:\n"
                    "        cleaned = token.strip()\n"
                    "        return len(cleaned) > 12\n"
                )

            billing_ts = os.path.join(host_ws, "billing.ts")
            with open(billing_ts, "w", encoding="utf-8") as fh:
                fh.write(
                    "export interface Invoice {\n"
                    "    id: string;\n"
                    "    cents: number;\n"
                    "}\n"
                    "export function chargeInvoice(inv: Invoice): boolean {\n"
                    "    const normalized = inv.id.trim();\n"
                    "    return normalized.length > 0 && inv.cents > 0;\n"
                    "}\n"
                )

            peer_ledger_py = os.path.join(peer_ws, "ledger.py")
            with open(peer_ledger_py, "w", encoding="utf-8") as fh:
                fh.write(
                    "class SessionGuard:\n"
                    "    def audit_token(self, token: str) -> bool:\n"
                    f'        secret = "{fake_key}"\n'
                    "        return bool(token and secret)\n"
                )

            # 1. --scan --format json real metrics
            scan_proc = subprocess.run(
                [sys.executable, os.path.join(ROOT_DIR, "tzero", "tzero_v3.py"), "--scan", host_ws, "--format", "json"],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
            scan_data = json.loads(scan_proc.stdout)
            self.assertEqual(scan_data["total_files"], 2)
            self.assertGreater(scan_data["raw_tokens"], 0)
            self.assertLessEqual(scan_data["pruned_tokens"], scan_data["raw_tokens"])
            self.assertIn("savings_pct", scan_data)

            # 2. SnapshotEngine SQLite .tzero/snapshot.db incremental update
            snap = SnapshotEngine.create_snapshot(host_ws)
            self.assertEqual(snap.file_count, 2)
            db_path = SnapshotEngine.get_sqlite_path(host_ws)
            self.assertTrue(os.path.isfile(db_path))
            conn = sqlite3.connect(db_path)
            try:
                rows = conn.execute("SELECT rel_path FROM file_snapshots").fetchall()
                self.assertEqual(len(rows), 2)
            finally:
                conn.close()

            with open(auth_py, "a", encoding="utf-8") as fh:
                fh.write("\ndef issue_refresh_token(user_id: str) -> str:\n    return f'ref:{user_id}'\n")
            updated_snap, inc_stats = SnapshotEngine.update_incremental(host_ws)
            self.assertEqual(inc_stats["reparsed"], 1)
            self.assertEqual(inc_stats["reused"], 1)
            self.assertEqual(inc_stats["deleted"], 0)
            self.assertIn("issue_refresh_token", updated_snap.files["auth.py"].functions)

            # 3. KV-cache aligned packing deterministic static prefix
            pack_a = pack_workspace(host_ws, budget_tokens=6000, focus="auth", cache_aligned=True)
            pack_b = pack_workspace(host_ws, budget_tokens=6000, focus="billing", cache_aligned=True)
            marker = "<!-- TZERO_DYNAMIC_SUFFIX -->"
            self.assertIn(marker, pack_a.bundle_text)
            self.assertIn(marker, pack_b.bundle_text)
            prefix_a, suffix_a = pack_a.bundle_text.split(marker, 1)
            prefix_b, suffix_b = pack_b.bundle_text.split(marker, 1)
            self.assertEqual(prefix_a, prefix_b)
            self.assertIn("auth.py", suffix_a)
            self.assertIn("billing.ts", suffix_b)

            # 4. Polyglot TypeScript breaking contract -> SARIF 2.1.0
            old_ts = pathlib.Path(billing_ts).read_text(encoding="utf-8")
            new_ts = old_ts.replace(
                "export function chargeInvoice(inv: Invoice): boolean",
                "export function chargeInvoice(inv: Invoice, idempotencyKey: string): boolean",
            )
            diff_rep = ASTContractComparator.compare_code(old_ts, new_ts, file_path="billing.ts")
            self.assertTrue(diff_rep.is_breaking)
            self.assertEqual(diff_rep.semver_bump, SemVerBump.MAJOR)
            sarif = ASTContractComparator.format_sarif_report([diff_rep])
            self.assertEqual(sarif.get("version"), "2.1.0")
            self.assertEqual(sarif.get("$schema"), "https://json.schemastore.org/sarif-2.1.0.json")
            self.assertEqual(sarif["runs"][0]["results"][0]["level"], "error")

            # 5. Hooks: .env block, .env.example allow, PostToolUse prune, multi-client install_hooks
            blocked = evaluate_pre_tool_use(
                {"tool_name": "Read", "tool_input": {"file_path": ".env"}},
                workspace_dir=host_ws,
            )
            self.assertEqual(blocked["decision"], "block")
            self.assertEqual(blocked["exit_code"], 2)

            allowed = evaluate_pre_tool_use(
                {"tool_name": "Read", "tool_input": {"file_path": ".env.example"}},
                workspace_dir=host_ws,
            )
            self.assertEqual(allowed["decision"], "allow")
            self.assertEqual(allowed["exit_code"], 0)

            big_code = "\n".join(f"def step_{i}(n: int) -> int:\n    return n + {i}\n" for i in range(15))
            pruned_hook = evaluate_post_tool_use(
                {"tool_name": "Read", "tool_input": {"file_path": "auth.py"}, "tool_response": big_code},
                workspace_dir=host_ws,
                max_chars=100,
            )
            self.assertEqual(pruned_hook["decision"], "prune")

            install_res = install_hooks(workspace_dir=host_ws, client="all")
            self.assertEqual(install_res["count"], 3)
            for rel_cfg in (
                os.path.join(".claude", "settings.local.json"),
                os.path.join(".cursor", "hooks.json"),
                os.path.join(".gemini", "settings.json"),
            ):
                cfg_path = os.path.join(host_ws, rel_cfg)
                self.assertTrue(os.path.isfile(cfg_path))
                self.assertIn("tzero hook", pathlib.Path(cfg_path).read_text(encoding="utf-8"))

            # 6. TZeroLSPServer didOpen -> hover -> codeAction quickfix
            lsp = TZeroLSPServer(workspace_dir=host_ws)
            lsp_file = os.path.join(host_ws, "lsp_sample.py")
            lsp_uri = pathlib.Path(lsp_file).as_uri()
            lsp_code = (
                f'STRIPE_KEY = "{fake_key}"\n'
                "def inspect_guard(token: str) -> bool:\n"
                "    return len(token) > 0\n"
            )
            opened = lsp.handle_message({
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {"textDocument": {"uri": lsp_uri, "text": lsp_code}},
            })
            diags = opened[0]["params"]["diagnostics"]
            self.assertIn("zero-leak", {d["code"] for d in diags})

            hover = lsp.compute_hover(lsp_uri, lsp_code, line=1, character=4)
            self.assertIsNotNone(hover)
            self.assertIn("inspect_guard", hover["contents"]["value"])

            actions = lsp.compute_code_actions(lsp_uri, lsp_code, diags)
            self.assertGreaterEqual(len(actions), 1)
            self.assertEqual(actions[0]["kind"], "quickfix")
            self.assertIn('os.environ.get("STRIPE_KEY"', actions[0]["edit"]["changes"][lsp_uri][0]["newText"])

            # 7. Federation export -> import -> analyze_cross_repo_impact + binary SCIP wire graph
            manifest_file = os.path.join(peer_ws, "peer_manifest.json")
            exported = FederationSyncEngine.export_manifest(peer_ws, repo_name="ledger-peer", out_file=manifest_file)
            self.assertTrue(FederationSyncEngine.verify_manifest(exported))
            self.assertNotIn(fake_key, json.dumps(exported))

            imp = FederationSyncEngine.import_manifest(host_ws, manifest_file)
            self.assertTrue(imp["verified"])

            scip_bin_path = os.path.join(peer_ws, "index.scip")
            with open(scip_bin_path, "wb") as fh:
                fh.write(_encode_scip_protobuf_sample("ledger.py", "auth.py", "SessionGuard"))
            scip_graph = ScipIndexImporter.load(scip_bin_path)
            self.assertEqual(scip_graph.format_name, "scip-protobuf")
            self.assertIn("ledger.py", scip_graph.export_tzero_graph()["edges"].get("auth.py", []))

            impact = FederationSyncEngine.analyze_cross_repo_impact(
                workspace_dir=host_ws,
                symbol_name="SessionGuard",
                scip_path=scip_bin_path,
            )
            self.assertEqual(impact["unverified_peers"], [])
            self.assertGreaterEqual(len(impact["local_hits"]), 1)
            self.assertGreaterEqual(len(impact["impacted_peers"]), 1)
            self.assertEqual(impact["impacted_peers"][0]["repo_name"], "ledger-peer")
            self.assertEqual(impact["scip_trace"]["format"], "scip-protobuf")
            self.assertEqual(len(impact["scip_trace"]["definitions"]), 1)

            kernel = AgentKernelSandbox(workspace_dir=host_ws)
            self.assertTrue(kernel.validate_execution_plan({"allow_network": False, "read_paths": [host_ws]})["allowed"])
            self.assertFalse(kernel.validate_execution_plan({"allow_network": True, "read_paths": [host_ws]})["allowed"])

    def test_run_doctor_deep_direct_and_failure_reporting(self):
        out_shallow = io.StringIO()
        with contextlib.redirect_stdout(out_shallow):
            code_shallow = tzero_deps.run_doctor()
        self.assertEqual(code_shallow, 0)
        self.assertNotIn("Deep Offline Subsystem Self-Check:", out_shallow.getvalue())

        out_deep = io.StringIO()
        tokenizer = mock.Mock()
        with (
            mock.patch("tzero.tzero_polyglot._BPE_ENCODING_CACHE", {}),
            mock.patch.dict(sys.modules, {"tiktoken": tokenizer}),
            mock.patch.object(tzero_deps, "ensure_dependencies") as install_deps,
            contextlib.redirect_stdout(out_deep),
        ):
            code_deep = tzero_deps.run_doctor(deep=True)
        tokenizer.get_encoding.assert_not_called()
        install_deps.assert_not_called()
        deep_text = out_deep.getvalue()
        self.assertEqual(code_deep, 0, deep_text)
        self.assertIn("Deep Offline Subsystem Self-Check:", deep_text)
        self.assertIn("All required checks passed.", deep_text)
        for expected_marker in (
            "BPE Tokenizer",
            "Polyglot AST Reducer",
            "Zero-Leak Engine",
            "LSP Server",
            "Lifecycle Hooks",
            "Federation Sync",
            "SCIP Importer",
            "Contracts & SARIF",
            "Agent Kernel & Snapshot",
        ):
            self.assertIn(expected_marker, deep_text)

        # Ensure failure increments failure count and returns 1
        out_fail = io.StringIO()
        with mock.patch("tzero.tzero_scip.ScipIndexImporter.from_scip_dict", side_effect=RuntimeError("synthetic scip error")), \
                contextlib.redirect_stdout(out_fail):
            code_fail = tzero_deps.run_doctor(deep=True)
        fail_text = out_fail.getvalue()
        self.assertEqual(code_fail, 1, fail_text)
        self.assertIn("[FAIL]", fail_text)
        self.assertIn("synthetic scip error", fail_text)

    def test_cli_doctor_deep_and_help_discovery(self):
        # 8. Subprocess --doctor --deep returns exit code 0
        proc_deep = subprocess.run(
            [sys.executable, os.path.join(ROOT_DIR, "tzero", "tzero_v3.py"), "--doctor", "--deep"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        self.assertEqual(proc_deep.returncode, 0, proc_deep.stdout + proc_deep.stderr)
        self.assertIn("T-Zero Doctor: environment check", proc_deep.stdout)
        self.assertIn("Deep Offline Subsystem Self-Check:", proc_deep.stdout)
        self.assertIn("All required checks passed.", proc_deep.stdout)

        # Natural subcommand `tzero doctor --deep` also works
        proc_sub = subprocess.run(
            [sys.executable, os.path.join(ROOT_DIR, "tzero", "tzero_v3.py"), "doctor", "--deep"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        self.assertEqual(proc_sub.returncode, 0, proc_sub.stdout + proc_sub.stderr)
        self.assertIn("Deep Offline Subsystem Self-Check:", proc_sub.stdout)

        # Help and quickstart surface v11 flags
        proc_help = subprocess.run(
            [sys.executable, os.path.join(ROOT_DIR, "tzero", "tzero_v3.py"), "--help"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        self.assertEqual(proc_help.returncode, 0)
        for flag in ("--deep", "--lsp", "--hook", "--hook-install", "--federation", "--scip-import", "--contracts-sarif"):
            self.assertIn(flag, proc_help.stdout)

        proc_info = subprocess.run(
            [sys.executable, os.path.join(ROOT_DIR, "tzero", "tzero_v3.py"), "--info"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        self.assertEqual(proc_info.returncode, 0)
        for cmd_hint in ("--doctor --deep", "--lsp", "--hook-install", "--federation impact", "--scip-import", "--contracts-sarif"):
            self.assertIn(cmd_hint, proc_info.stdout)


if __name__ == "__main__":
    unittest.main()
