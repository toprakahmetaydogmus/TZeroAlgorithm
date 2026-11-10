# -*- coding: utf-8 -*-
"""Verification tests for GitHub Composite Action (action.yml)."""

import pathlib
import unittest

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent


class TestActionYml(unittest.TestCase):
    def setUp(self):
        self.text = (ROOT_DIR / "action.yml").read_text(encoding="utf-8")

    def test_action_uses_installed_cli_not_relative_script(self):
        self.assertNotIn("python tzero_v3.py", self.text)
        self.assertIn("tzero ", self.text)

    def test_action_handles_all_declared_inputs_and_modes(self):
        self.assertIn('"$MODE" = "review"', self.text)
        self.assertIn('"$MODE" = "tree"', self.text)
        self.assertIn("inputs.audit-level", self.text)
        self.assertIn("inputs.enforce-boundaries", self.text)
        self.assertIn("inputs.export-rules", self.text)

    def test_action_writes_all_declared_github_outputs(self):
        self.assertIn("GITHUB_OUTPUT", self.text)
        self.assertIn("token-savings-pct=", self.text)
        self.assertIn("secret-findings=", self.text)
        self.assertIn("blast-radius-score=", self.text)


if __name__ == "__main__":
    unittest.main()
