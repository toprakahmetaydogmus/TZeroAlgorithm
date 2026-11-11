# -*- coding: utf-8 -*-
"""
Tests for T-Zero AST Semantic 3-Way Merge & Conflict Healer.
Siber Akademi - 100% Free & Zero-Leak Test Suite.
"""

import unittest
import tempfile
import os
import shutil
import subprocess
import sys
import ast

from tzero.tzero_semantic_merge import ASTSemanticMerger, heal_conflicts


class TestSemanticMerger(unittest.TestCase):
    """Verifies automated AST healing of git conflict markers and disjoint symbols."""

    def test_auto_heal_disjoint_functions(self):
        conflicted_code = """
import os

<<<<<<< HEAD
def calculate_tax(amount: float) -> float:
    return amount * 0.18
=======
def calculate_discount(amount: float, percent: float) -> float:
    return amount * (1.0 - percent / 100.0)
>>>>>>> feature-discount

def main():
    pass
"""
        res = heal_conflicts(conflicted_code)
        self.assertTrue(res.success)
        self.assertEqual(res.auto_resolved_conflicts, 1)
        self.assertEqual(res.unresolved_conflicts, 0)
        self.assertIn("def calculate_tax", res.merged_code)
        self.assertIn("def calculate_discount", res.merged_code)
        self.assertNotIn("<<<<<<<", res.merged_code)
        self.assertNotIn("=======", res.merged_code)
        self.assertNotIn(">>>>>>>", res.merged_code)

        # Assert resulting code is 100% syntactically valid Python
        tree = ast.parse(res.merged_code)
        func_names = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
        self.assertIn("calculate_tax", func_names)
        self.assertIn("calculate_discount", func_names)
        self.assertIn("main", func_names)

    def test_auto_heal_with_imports(self):
        conflicted_code = """
<<<<<<< HEAD
import math
import sys
=======
import json
import math
>>>>>>> feature-json

def compute():
    return 42
"""
        res = heal_conflicts(conflicted_code)
        self.assertTrue(res.success)
        self.assertIn("import math", res.merged_code)
        self.assertIn("import sys", res.merged_code)
        self.assertIn("import json", res.merged_code)
        # Deduplication check: math should only appear once
        self.assertEqual(res.merged_code.count("import math"), 1)
        ast.parse(res.merged_code)

    def test_no_conflict_passthrough(self):
        clean_code = "def foo():\n    return 'bar'\n"
        res = heal_conflicts(clean_code)
        self.assertTrue(res.success)
        self.assertEqual(res.auto_resolved_conflicts, 0)
        self.assertEqual(res.merged_code, clean_code)

    def test_collision_sanitization(self):
        conflicted_code = """
<<<<<<< HEAD
def process_data(x):
    return x + 1
=======
def process_data(x):
    return x * 10
>>>>>>> feature-multiplier
"""
        res = heal_conflicts(conflicted_code)
        # Collision detected because both define process_data
        self.assertFalse(res.success)
        self.assertEqual(res.unresolved_conflicts, 1)
        # Broken <<<<<<< markers are converted to safe comments
        self.assertNotIn("<<<<<<<", res.merged_code)
        self.assertNotIn(">>>>>>>", res.merged_code)
        self.assertIn("# --- T-ZERO AST MERGE CONFLICT", res.merged_code)

    def test_cli_merge_heal_flag(self):
        temp_dir = tempfile.mkdtemp()
        try:
            file_path = os.path.join(temp_dir, "conflicted.py")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("""
<<<<<<< HEAD
def alpha(): return 1
=======
def beta(): return 2
>>>>>>> branch-beta
""")
            cmd = [
                sys.executable,
                "tzero/tzero_v3.py",
                "--merge-heal",
                file_path
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(res.returncode, 0)
            self.assertIn("T-ZERO AST SEMANTIC MERGE", res.stdout)
            self.assertIn("Auto-Healed Blocks:", res.stdout)
            self.assertIn("1", res.stdout)

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("def alpha(): return 1", content)
            self.assertIn("def beta(): return 2", content)
            self.assertNotIn("<<<<<<<", content)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
