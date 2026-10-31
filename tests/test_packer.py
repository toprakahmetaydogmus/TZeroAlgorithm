# -*- coding: utf-8 -*-
"""Unit tests for T-Zero Dynamic Context Window & Token Budget Packer."""

import os
import tempfile
import unittest

from tzero_packer import TokenBudgetPacker, pack_workspace


class TestTokenBudgetPacker(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.ws = self.test_dir.name

        # Create mock project files
        self.file_main = os.path.join(self.ws, "main.py")
        with open(self.file_main, "w", encoding="utf-8") as f:
            f.write(
                "import os\n"
                "from service import PaymentService\n\n"
                "def start_server():\n"
                "    print('Starting server on port 8080')\n"
                "    svc = PaymentService()\n"
                "    return svc.process()\n"
            )

        self.file_service = os.path.join(self.ws, "service.py")
        with open(self.file_service, "w", encoding="utf-8") as f:
            f.write(
                "class PaymentService:\n"
                "    def __init__(self):\n"
                "        self.gateway = 'https://api.gateway.com'\n"
                "        self.timeout = 30\n\n"
                "    def process(self) -> bool:\n"
                "        # Detailed logic here\n"
                "        for i in range(100):\n"
                "            pass\n"
                "        return True\n"
            )

        self.file_util = os.path.join(self.ws, "util.rs")
        with open(self.file_util, "w", encoding="utf-8") as f:
            f.write(
                "pub struct RingBuffer {\n"
                "    pub size: usize,\n"
                "}\n"
                "impl RingBuffer {\n"
                "    pub fn new() -> Self {\n"
                "        println!('init');\n"
                "        RingBuffer { size: 1024 }\n"
                "    }\n"
                "}\n"
            )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_estimate_tokens(self):
        text = "def hello_world(): return 42"
        tokens = TokenBudgetPacker.estimate_tokens(text)
        self.assertGreater(tokens, 0)
        self.assertLess(tokens, 30)

    def test_pack_within_budget(self):
        budget = 5000
        res = pack_workspace(workspace_dir=self.ws, budget_tokens=budget)
        self.assertLessEqual(res.total_tokens, budget)
        self.assertGreater(res.total_tokens, 0)
        self.assertIn("T-ZERO PACKED CONTEXT BUNDLE", res.bundle_text)
        self.assertIn("main.py", res.bundle_text)
        self.assertIn("service.py", res.bundle_text)

    def test_pack_with_focus_file(self):
        # When focusing on service.py, it should receive Tier 1 representation
        res = pack_workspace(workspace_dir=self.ws, budget_tokens=4000, focus="service.py")
        self.assertIn("Focus: `service.py`", res.bundle_text)
        # Check that service.py was selected as T-1
        service_entry = next((e for e in res.entries if "service.py" in e.rel_path), None)
        self.assertIsNotNone(service_entry)
        self.assertEqual(service_entry.selected_tier, "T-1")

    def test_pack_out_file_export(self):
        out_name = "packed_context.md"
        res = pack_workspace(workspace_dir=self.ws, budget_tokens=8000, out_file=out_name)
        out_path = os.path.join(self.ws, out_name)
        self.assertTrue(os.path.exists(out_path))
        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertEqual(content, res.bundle_text)

    def test_extreme_low_budget_graceful(self):
        # Even with tiny budget, should not crash and stays within reasonable bounds
        res = pack_workspace(workspace_dir=self.ws, budget_tokens=600)
        self.assertIsNotNone(res.bundle_text)


if __name__ == "__main__":
    unittest.main()
