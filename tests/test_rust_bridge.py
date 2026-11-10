# -*- coding: utf-8 -*-
"""TDD tests for Rust Core FFI/subprocess bridge and Agent Kernel sandbox."""

import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import tzero_rust_bridge


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

    def test_cli_agent_kernel_dry_run(self):
        proc = subprocess.run(
            [sys.executable, "tzero_v3.py", "agent-kernel", "--dir", "."],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(proc.stdout)
        self.assertTrue(data["zero_leak"])
        self.assertIn("backend", data)


if __name__ == "__main__":
    unittest.main()
