# -*- coding: utf-8 -*-
"""Unit tests for T-Zero Autonomous PC-Fixer & Environment Doctor."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from tzero_pc_fixer import DiagnosticIssue, HealAction, PCFixerDoctor


class TestPCFixerDoctor(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="tzero_fixer_test_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_check_tools_on_path(self):
        tools = PCFixerDoctor.check_tools_on_path()
        self.assertIsInstance(tools, dict)
        self.assertIn("python", tools)
        self.assertTrue(tools["python"])

    def test_diagnose_clean_directory(self):
        # Create valid python file
        valid_file = Path(self.test_dir) / "clean.py"
        valid_file.write_text("import sys\n\ndef add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8")

        rep = PCFixerDoctor.diagnose(self.test_dir)
        self.assertGreaterEqual(rep.health_score_pct, 95)
        self.assertEqual(rep.syntax_errors, 0)

    def test_detect_and_heal_missing_colon(self):
        broken_file = Path(self.test_dir) / "broken_syntax.py"
        broken_file.write_text("def hello()\n    return 42\n", encoding="utf-8")

        rep_before = PCFixerDoctor.diagnose(self.test_dir)
        self.assertEqual(rep_before.syntax_errors, 1)

        heal_res = PCFixerDoctor.auto_heal(self.test_dir, dry_run=False)
        self.assertEqual(heal_res.issues_healed, 1)

        # After healing, file should be parseable
        content = broken_file.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("def hello():"))
        rep_after = PCFixerDoctor.diagnose(self.test_dir)
        self.assertEqual(rep_after.syntax_errors, 0)

    def test_detect_and_heal_python2_print(self):
        py2_file = Path(self.test_dir) / "legacy.py"
        py2_file.write_text('print "Welcome to Python"\n', encoding="utf-8")

        rep_before = PCFixerDoctor.diagnose(self.test_dir)
        self.assertEqual(rep_before.syntax_errors, 1)

        heal_res = PCFixerDoctor.auto_heal(self.test_dir, dry_run=False)
        self.assertEqual(heal_res.issues_healed, 1)

        content = py2_file.read_text(encoding="utf-8")
        self.assertIn('print("Welcome to Python")', content)

    def test_detect_and_heal_missing_import(self):
        missing_file = Path(self.test_dir) / "uses_sys.py"
        missing_file.write_text("def exit_app():\n    sys.exit(0)\n", encoding="utf-8")

        rep_before = PCFixerDoctor.diagnose(self.test_dir)
        self.assertEqual(rep_before.missing_imports, 1)

        heal_res = PCFixerDoctor.auto_heal(self.test_dir, dry_run=False)
        self.assertGreaterEqual(heal_res.issues_healed, 1)

        content = missing_file.read_text(encoding="utf-8")
        self.assertIn("import sys", content)

    def test_detect_and_strip_bom(self):
        bom_file = Path(self.test_dir) / "bom.py"
        with open(bom_file, "wb") as f:
            f.write(b"\xef\xbb\xbfdef test():\n    return 1\n")

        rep_before = PCFixerDoctor.diagnose(self.test_dir)
        self.assertTrue(any(i.metadata.get("action") == "strip_bom" for i in rep_before.issues))

        heal_res = PCFixerDoctor.auto_heal(self.test_dir, dry_run=False)
        self.assertGreaterEqual(heal_res.issues_healed, 1)

        with open(bom_file, "rb") as f:
            data = f.read()
        self.assertFalse(data.startswith(b"\xef\xbb\xbf"))

    def test_dry_run_does_not_modify_files(self):
        broken_file = Path(self.test_dir) / "broken.py"
        orig_content = "def test()\n    pass\n"
        broken_file.write_text(orig_content, encoding="utf-8")

        heal_res = PCFixerDoctor.auto_heal(self.test_dir, dry_run=True)
        self.assertTrue(heal_res.dry_run)
        self.assertEqual(broken_file.read_text(encoding="utf-8"), orig_content)


if __name__ == "__main__":
    unittest.main()
