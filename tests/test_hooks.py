# -*- coding: utf-8 -*-
"""TDD tests for T-Zero lifecycle hook runner (PreToolUse / PostToolUse)."""

import io
import json
import unittest
from contextlib import redirect_stdout

import tzero_hooks


class TestTZeroHooks(unittest.TestCase):
    def test_pre_tool_use_blocks_secret_leak_on_write(self):
        fake_key = "sk" + "-proj-" + "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8"
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "src/config.py",
                "content": f'API_TOKEN = "{fake_key}"\n',
            },
        }
        verdict = tzero_hooks.evaluate_pre_tool_use(payload)
        self.assertEqual(verdict["decision"], "block")
        self.assertEqual(verdict["exit_code"], 2)
        self.assertGreaterEqual(verdict["findings"], 1)
        self.assertIn("Zero-Leak", verdict["reason"])

    def test_pre_tool_use_allows_clean_code(self):
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "src/service.py",
                "new_string": "import os\nAPI_TOKEN = os.environ.get('API_TOKEN', '')\n",
            },
        }
        verdict = tzero_hooks.evaluate_pre_tool_use(payload)
        self.assertEqual(verdict["decision"], "allow")
        self.assertEqual(verdict["exit_code"], 0)

    def test_post_tool_use_auto_prunes_oversized_read(self):
        large_py = "\n".join(
            f"def compute_{i}(x: int, y: int) -> int:\n"
            f"    acc = x * {i + 1} + y\n"
            f"    for k in range(20):\n"
            f"        acc += k\n"
            f"    return acc\n"
            for i in range(60)
        )
        payload = {
            "hook_event_name": "PostToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": "heavy_module.py"},
            "tool_response": large_py,
        }
        verdict = tzero_hooks.evaluate_post_tool_use(payload, max_chars=800)
        self.assertEqual(verdict["decision"], "prune")
        self.assertEqual(verdict["exit_code"], 0)
        self.assertLess(verdict["pruned_tokens"], verdict["raw_tokens"])
        self.assertGreater(verdict["savings_pct"], 30.0)
        self.assertIn("def compute_0", verdict["additionalContext"])

    def test_run_hook_cli_returns_exit_2_on_block(self):
        fake_key = "ghp_" + "9z8y7x6w5v4u3t2s1r0q9p8o7n6m5l4k3j2i"
        raw_in = json.dumps({
            "tool_name": "Write",
            "tool_input": {"file_path": "leak.ts", "content": f"export const T = '{fake_key}';"},
        })
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = tzero_hooks.run_hook_cli("PreToolUse", payload_json=raw_in)
        self.assertEqual(code, 2)
        parsed = json.loads(buf.getvalue())
        self.assertEqual(parsed["decision"], "block")

    def test_cli_hook_subcommand_blocks_secret(self):
        import subprocess
        import sys
        fake_key = "sk" + "-proj-" + "z9y8x7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2"
        payload = json.dumps({
            "tool_name": "Write",
            "tool_input": {"file_path": "cli_leak.py", "content": f"K = '{fake_key}'"},
        })
        proc = subprocess.run(
            [sys.executable, "tzero_v3.py", "hook", "--event", "PreToolUse"],
            input=payload,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)
        parsed = json.loads(proc.stdout)
        self.assertEqual(parsed["decision"], "block")


if __name__ == "__main__":
    unittest.main()
