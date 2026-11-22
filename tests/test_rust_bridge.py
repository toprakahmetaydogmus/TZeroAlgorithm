# -*- coding: utf-8 -*-
"""TDD tests for Rust Core FFI/subprocess bridge and Agent Kernel sandbox."""

import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tzero import tzero_rust_bridge


class TestRustBridgeAndAgentKernel(unittest.TestCase):
    def test_fallback_hash_and_shingle_similarity_deterministic(self):
        bridge = tzero_rust_bridge.RustCoreBridge()
        self.assertIn(bridge.backend(), ("ctypes", "pyo3", "subprocess", "python-fallback"))
        h1 = bridge.fnv1a_hash("OrderController.processPayment")
        h2 = bridge.fnv1a_hash("OrderController.processPayment")
        h3 = bridge.fnv1a_hash("DifferentSymbol")
        self.assertEqual(h1, h2)
        self.assertNotEqual(h1, h3)

        sim_same = bridge.shingle_similarity("def compute(x): return x + 1", "def compute(x): return x + 1")
        sim_diff = bridge.shingle_similarity("def compute(x): return x + 1", "class LedgerAccount: pass")
        self.assertAlmostEqual(sim_same, 1.0, places=3)
        self.assertLess(sim_diff, 0.4)

    def test_ctypes_native_library_dispatch_when_present(self):
        fake_lib = mock.MagicMock()
        fake_lib.tzero_jaccard_shingles_f64.return_value = 0.875
        with mock.patch.object(tzero_rust_bridge.RustCoreBridge, "_try_load_pyo3", return_value=None):
            with mock.patch.object(tzero_rust_bridge.RustCoreBridge, "_try_load_cdylib", return_value=fake_lib):
                bridge = tzero_rust_bridge.RustCoreBridge(prefer_native=True)
                self.assertEqual(bridge.backend(), "ctypes")
                val = bridge.shingle_similarity("alpha", "beta")
                self.assertAlmostEqual(val, 0.875, places=3)
                fake_lib.tzero_jaccard_shingles_f64.assert_called_once()

    def test_agent_kernel_sandbox_blocks_network_and_unsafe_paths(self):
        with tempfile.TemporaryDirectory() as ws:
            kernel = tzero_rust_bridge.AgentKernelSandbox(workspace_dir=ws)
            clean = kernel.validate_execution_plan(
                {"action": "audit", "allow_network": False, "read_paths": [ws]}
            )
            self.assertTrue(clean["allowed"])
            self.assertEqual(clean["backend"], kernel.bridge.backend())

            unsafe_net = kernel.validate_execution_plan(
                {"action": "upload", "allow_network": True, "read_paths": [ws]}
            )
            self.assertFalse(unsafe_net["allowed"])
            self.assertIn("network", unsafe_net["reason"].lower())

            unsafe_path = kernel.validate_execution_plan(
                {"action": "read", "allow_network": False, "read_paths": ["/etc/shadow"]}
            )
            self.assertFalse(unsafe_path["allowed"])

            unsafe_write = kernel.validate_execution_plan(
                {"action": "write", "allow_network": False, "write_paths": ["/etc/cron.d/pwn"]}
            )
            self.assertFalse(unsafe_write["allowed"])

    def test_cli_agent_kernel_dry_run(self):
        proc = subprocess.run(
            [sys.executable, "tzero/tzero_v3.py", "agent-kernel", "--dir", "."],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(proc.stdout)
        self.assertTrue(data["zero_leak"])
        self.assertIn("backend", data)

    def test_shannon_entropy_calculation_and_scanning(self):
        bridge = tzero_rust_bridge.RustCoreBridge()
        self.assertEqual(bridge.calculate_entropy(""), 0.0)
        self.assertEqual(tzero_rust_bridge.calculate_shannon_entropy(""), 0.0)
        self.assertEqual(bridge.calculate_entropy("aaaaaaa"), 0.0)

        token = "aB9_xK2mP9qR3sTuVwXyZ1234567890QWE"
        ent = bridge.calculate_entropy(token)
        self.assertGreaterEqual(ent, 4.75)

        text = f'secret_payload = "{token}"'
        findings = bridge.scan_entropy_secrets(text, threshold=4.75, min_length=28)
        self.assertGreaterEqual(len(findings), 1)
        self.assertIn(token, findings[0]["token"])
        self.assertTrue(findings[0]["is_anomaly"])

        ph_text = 'dummy_key = "YOUR_API_KEY_HERE_123456789012345"'
        ph_findings = bridge.scan_entropy_secrets(ph_text, threshold=4.75, min_length=28)
        self.assertEqual(len(ph_findings), 0)

    def test_prune_ast_and_bpe_token_counting(self):
        bridge = tzero_rust_bridge.RustCoreBridge()
        py_code = 'def process_order(order_id: int) -> bool:\n    """Doc."""\n    val = order_id * 2\n    return val > 0\n'
        pruned = bridge.prune_ast(py_code, language="python")
        self.assertIn("def process_order", pruned)
        self.assertIn("...", pruned)

        tokens = bridge.count_bpe_tokens("hello world from t-zero turbo core", model_name="gpt-4o")
        self.assertGreaterEqual(tokens, 1)

    def test_prune_ast_stats_and_redaction(self):
        bridge = tzero_rust_bridge.RustCoreBridge()
        code = 'def compute_total(a: int, b: int) -> int:\n    """Sum numbers."""\n    res = a + b\n    return res\n'
        stats = bridge.prune_ast_stats(code, language="python")
        self.assertIn("pruned_code", stats)
        self.assertIn("original_lines", stats)
        self.assertIn("pruned_lines", stats)
        self.assertIn("reduction_ratio", stats)
        self.assertEqual(stats["original_lines"], 4)
        self.assertLess(stats["pruned_lines"], stats["original_lines"])

        mod_stats = tzero_rust_bridge.prune_ast_stats(code, language="python")
        self.assertEqual(mod_stats["original_lines"], stats["original_lines"])

        token = "aB9_xK2mP9qR3sTuVwXyZ1234567890QWE"
        secret_line = f'api_key = "{token}"'
        sanitized, count = bridge.redact_entropy_secrets(secret_line)
        self.assertEqual(count, 1)
        self.assertNotIn(token, sanitized)

        mod_sanitized, mod_count = tzero_rust_bridge.redact_entropy_secrets(secret_line)
        self.assertEqual(mod_count, 1)
        self.assertNotIn(token, mod_sanitized)

    def test_multi_language_pruning(self):
        bridge = tzero_rust_bridge.RustCoreBridge()

        # TypeScript
        ts_code = 'export function addNumbers(a: number, b: number): number {\n  const sum = a + b;\n  return sum;\n}\n'
        pruned_ts = bridge.prune_ast(ts_code, language="typescript")
        self.assertIn("addNumbers", pruned_ts)

        # Rust
        rs_code = 'pub fn calculate_area(width: f64, height: f64) -> f64 {\n    let area = width * height;\n    area\n}\n'
        pruned_rs = bridge.prune_ast(rs_code, language="rust")
        self.assertIn("calculate_area", pruned_rs)

        # Go
        go_code = 'func ProcessPayment(amount int) (bool, error) {\n    if amount <= 0 {\n        return false, nil\n    }\n    return true, nil\n}\n'
        pruned_go = bridge.prune_ast(go_code, language="go")
        self.assertIn("ProcessPayment", pruned_go)

    def test_unicode_and_turkish_shannon_entropy(self):
        bridge = tzero_rust_bridge.RustCoreBridge()
        text = "Türkçe karakter desteği: çığöşü — Toprak Ahmet Aydoğmuş (Siber Akademi)"
        ent = bridge.calculate_entropy(text)
        self.assertGreater(ent, 3.0)

    def test_pyo3_mock_dispatch_when_available(self):
        fake_pyo3 = mock.MagicMock()
        fake_pyo3.calculate_shannon_entropy.return_value = 5.25
        fake_pyo3.prune_ast.return_value = "def pruned(): ..."
        fake_pyo3.prune_ast_stats.return_value = {
            "pruned_code": "def pruned(): ...",
            "original_lines": 10,
            "pruned_lines": 2,
            "reduction_ratio": 80.0,
            "language": "python",
        }
        fake_pyo3.count_bpe_tokens.return_value = 42
        fake_pyo3.scan_entropy_secrets.return_value = [{"token": "secret", "entropy": 5.25}]
        fake_pyo3.redact_entropy_secrets.return_value = ("sanitized", 1)
        fake_pyo3.fnv1a_hash.return_value = 99999
        fake_pyo3.shingle_similarity.return_value = 0.95

        with mock.patch.object(tzero_rust_bridge.RustCoreBridge, "_try_load_pyo3", return_value=fake_pyo3):
            bridge = tzero_rust_bridge.RustCoreBridge(prefer_native=True)
            self.assertEqual(bridge.backend(), "pyo3")
            self.assertTrue(bridge.is_native_available())
            self.assertAlmostEqual(bridge.calculate_entropy("test"), 5.25)
            self.assertEqual(bridge.prune_ast("def foo(): pass"), "def pruned(): ...")
            stats = bridge.prune_ast_stats("def foo(): pass")
            self.assertEqual(stats["reduction_ratio"], 80.0)
            self.assertEqual(bridge.count_bpe_tokens("test"), 42)
            findings = bridge.scan_entropy_secrets("test")
            self.assertEqual(len(findings), 1)
            sanitized, count = bridge.redact_entropy_secrets("test")
            self.assertEqual(count, 1)
            self.assertEqual(sanitized, "sanitized")
            self.assertEqual(bridge.fnv1a_hash("test"), 99999)
            self.assertAlmostEqual(bridge.shingle_similarity("a", "b"), 0.95)

    def test_cyclomatic_and_cognitive_complexity(self):
        bridge = tzero_rust_bridge.RustCoreBridge()
        code = (
            "def evaluate(val: int) -> bool:\n"
            "    if val > 10:\n"
            "        for i in range(val):\n"
            "            if i % 2 == 0:\n"
            "                return True\n"
            "    return False\n"
        )
        cc = bridge.calculate_cyclomatic_complexity(code, language="python")
        cog = bridge.calculate_cognitive_complexity(code)
        self.assertGreaterEqual(cc, 3)
        self.assertGreaterEqual(cog, 2)

        health = bridge.analyze_file_complexity("mod.py", code, language="python")
        self.assertEqual(health["file_path"], "mod.py")
        self.assertIn(health["rating"], ("A", "B", "C", "D"))
        self.assertGreater(health["maintainability_index"], 0.0)

    def test_pagerank_computation(self):
        bridge = tzero_rust_bridge.RustCoreBridge()
        edges = [
            {"source": "cli", "target": "core"},
            {"source": "api", "target": "core"},
            {"source": "core", "target": "utils"},
        ]
        ranks = bridge.compute_pagerank(edges)
        self.assertGreaterEqual(len(ranks), 3)
        core_rank = next((r for r in ranks if r["node"] == "core"), None)
        self.assertIsNotNone(core_rank)
        self.assertGreater(core_rank["score"], 0.0)

    def test_reachability_and_dead_code(self):
        bridge = tzero_rust_bridge.RustCoreBridge()
        symbols = [
            {"name": "main", "kind": "function", "line": 1, "path": "app.py", "signature": "def main():"},
            {"name": "helper", "kind": "function", "line": 5, "path": "app.py", "signature": "def helper():"},
            {"name": "dead_func", "kind": "function", "line": 10, "path": "app.py", "signature": "def dead_func():"},
        ]
        invocations = [("main", "helper")]
        entrypoints = ["main"]

        res = bridge.analyze_reachability(symbols, invocations, entrypoints)
        self.assertEqual(res["total_symbols"], 3)
        self.assertEqual(res["reachable_count"], 2)
        self.assertIn("dead_func", res["dead_symbols"])
        self.assertIn("helper", res["reachable_symbols"])

    def test_api_contract_comparison(self):
        bridge = tzero_rust_bridge.RustCoreBridge()
        old_code = "def process_payment(order_id: int): pass\n"
        new_code = "def process_payment(order_id: int, new_flag: bool): pass\n"

        res = bridge.compare_api_contracts(old_code, new_code)
        self.assertIn("recommended_bump", res)
        self.assertIn(res["recommended_bump"], ("MAJOR", "MINOR", "PATCH"))

    def test_duplicity_detection(self):
        bridge = tzero_rust_bridge.RustCoreBridge()
        block = "a = 1\nb = 2\nc = 3\nd = 4\ne = 5\nf = 6\n"
        file1 = f"def first():\n{block}"
        file2 = f"def second():\n{block}"

        rep = bridge.find_code_duplicity([("f1.py", file1), ("f2.py", file2)], min_lines=6)
        self.assertEqual(rep["total_files_scanned"], 2)
        self.assertGreaterEqual(rep["duplicate_block_count"], 1)

    def test_damerau_levenshtein_and_fuzzy(self):
        bridge = tzero_rust_bridge.RustCoreBridge()
        dist = bridge.damerau_levenshtein("teh", "the")
        self.assertEqual(dist, 1)  # transposition

        sim = bridge.fuzzy_similarity("PaymentController", "PaymentControler")
        self.assertGreater(sim, 0.9)

        matches = bridge.fuzzy_symbol_search("OrderCtrl", ["OrderController", "UserAccount", "OrderService"], min_similarity=0.4)
        self.assertGreaterEqual(len(matches), 1)
        self.assertEqual(matches[0]["target"], "OrderController")


if __name__ == "__main__":
    unittest.main()
