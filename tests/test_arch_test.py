# -*- coding: utf-8 -*-
"""Unit tests for T-Zero Architecture Test Suite Generator & Validator."""

import json
import os
import shutil
import tempfile
import unittest
from tzero.tzero_arch_test import ArchitectureTestSuiteGenerator, _extract_ast_imports


class TestArchitectureTestSuiteGenerator(unittest.TestCase):
    """Verifies functionality of the automated architecture test generator and auditor."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="tzero_arch_test_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_default_rules_fallback(self):
        gen = ArchitectureTestSuiteGenerator(self.test_dir, rules_path=os.path.join(self.test_dir, "nonexistent.json"))
        rules = gen._load_rules()
        self.assertIn("layers", rules)
        self.assertIn("forbidden_imports", rules)
        self.assertTrue(rules["security"]["zero_leak_enforced"])

    def test_generate_test_code_content(self):
        gen = ArchitectureTestSuiteGenerator(".")
        code = gen.generate_test_code()
        self.assertIn("class TestArchitectureGuard(unittest.TestCase):", code)
        self.assertIn("test_layer_boundaries_and_forbidden_imports", code)
        self.assertIn("test_zero_circular_imports", code)
        self.assertIn("test_zero_leak_security_policy", code)

    def test_write_test_file_to_custom_path(self):
        gen = ArchitectureTestSuiteGenerator(".")
        out_path = os.path.join(self.test_dir, "custom_guard_test.py")
        res = gen.write_test_file(out_path)
        self.assertEqual(res, out_path)
        self.assertTrue(os.path.isfile(out_path))
        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("TestArchitectureGuard", content)

    def test_run_live_audit_current_workspace(self):
        gen = ArchitectureTestSuiteGenerator(".")
        report = gen.run_live_audit()
        self.assertTrue(report["success"])
        self.assertGreater(report["scanned_files"], 100)
        self.assertEqual(report["layer_violations"], [])
        self.assertEqual(report["circular_cycles"], [])
        self.assertEqual(report["secret_leaks"], [])

    def test_synthetic_boundary_violation_detection(self):
        # Create a mini project in tempdir with layers and a violation
        rules = {
            "version": "5.0.0",
            "project_name": "SyntheticViolation",
            "layers": {
                "core": ["core/**"],
                "ui": ["ui/**"]
            },
            "forbidden_imports": [
                {
                    "from_layer": "core",
                    "cannot_import": ["ui"],
                    "reason": "Core must not depend on UI."
                }
            ],
            "security": {
                "zero_leak_enforced": True
            }
        }
        rules_path = os.path.join(self.test_dir, "tzero.rules.json")
        with open(rules_path, "w", encoding="utf-8") as f:
            json.dump(rules, f)

        core_dir = os.path.join(self.test_dir, "core")
        ui_dir = os.path.join(self.test_dir, "ui")
        os.makedirs(core_dir)
        os.makedirs(ui_dir)

        with open(os.path.join(ui_dir, "window.py"), "w", encoding="utf-8") as f:
            f.write("def show(): pass\n")

        # Offending file in core importing ui
        with open(os.path.join(core_dir, "engine.py"), "w", encoding="utf-8") as f:
            f.write("import ui\ndef run(): ui.show()\n")

        gen = ArchitectureTestSuiteGenerator(self.test_dir, rules_path=rules_path)
        res = gen.run_live_audit()
        self.assertFalse(res["success"])
        self.assertEqual(len(res["layer_violations"]), 1)
        self.assertEqual(res["layer_violations"][0]["from_layer"], "core")
        self.assertEqual(res["layer_violations"][0]["imported"], "ui")

    def test_synthetic_secret_leak_detection(self):
        rules = {
            "version": "5.0.0",
            "layers": {},
            "forbidden_imports": [],
            "security": {"zero_leak_enforced": True}
        }
        rules_path = os.path.join(self.test_dir, "tzero.rules.json")
        with open(rules_path, "w", encoding="utf-8") as f:
            json.dump(rules, f)

        src_dir = os.path.join(self.test_dir, "src")
        os.makedirs(src_dir)
        with open(os.path.join(src_dir, "config.py"), "w", encoding="utf-8") as f:
            # Simulate a leak dynamically so the test file itself does not match secret scanning regexes
            fake_key = "ghp_" + ("1234567890" * 4)
            f.write(f'API_KEY = "{fake_key}"\n')

        gen = ArchitectureTestSuiteGenerator(self.test_dir, rules_path=rules_path)
        res = gen.run_live_audit()
        self.assertFalse(res["success"])
        self.assertEqual(len(res["secret_leaks"]), 1)
        self.assertIn("config.py", res["secret_leaks"][0]["file"])


if __name__ == "__main__":
    unittest.main()
