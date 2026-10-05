# -*- coding: utf-8 -*-
"""Regression tests for headless use: no tkinter, clean MCP output, and secret scanning."""

import asyncio
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestHeadlessSupport(unittest.TestCase):
    def test_core_and_mcp_import_without_tkinter(self):
        """The engine, CLI and MCP server must import on Pythons that lack tkinter."""
        code = (
            "import sys\n"
            "sys.modules['tkinter'] = None\n"  # makes `import tkinter` raise ImportError
            "import tzero_v3, tzero_mcp\n"
            "assert tzero_v3.TK_AVAILABLE is False\n"
            "print('ok')\n"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, timeout=120
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ok", proc.stdout)

    def test_gui_flag_fails_cleanly_without_tkinter(self):
        """--gui should print a helpful message and exit 1 instead of crashing with a traceback."""
        code = (
            "import sys\n"
            "sys.modules['tkinter'] = None\n"
            "sys.argv = ['main.py', '--gui']\n"
            "import tzero_v3\n"
            "tzero_v3.main()\n"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, timeout=120
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("tkinter", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)


class TestMCPOutputQuality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tzero_mcp
        cls.server = tzero_mcp.create_mcp_server()

    def call(self, name, args):
        res = asyncio.run(self.server.call_tool(name, args))
        return res.content[0].text

    def test_audit_detects_openai_style_key(self):
        """The OpenAI key pattern must actually match a key (it was malformed before)."""
        fake_key = "sk-" + "a" * 24 + "T3BlbkFJ" + "b" * 24
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "leak.py"), "w", encoding="utf-8") as f:
                f.write(f'TOKEN = "{fake_key}"\n')
            text = self.call("audit_codebase_quality", {"project_root": tmp})
        self.assertIn("OpenAI API Key Pattern", text)

    def test_enforce_boundaries_output_has_no_ansi_codes(self):
        text = self.call("enforce_architecture_boundaries", {"project_root": ROOT})
        self.assertNotIn("\x1b[", text)


if __name__ == "__main__":
    unittest.main()
