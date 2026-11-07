# -*- coding: utf-8 -*-
"""Unit tests for T-Zero AST Mutation & Test Quality Engine."""

import ast
import os
import shutil
import sys
import tempfile
import unittest
from tzero_mutation import ASTMutationEngine, ASTMutationTransformer, Mutant, MutationReport


class TestASTMutationEngine(unittest.TestCase):
    """Verifies mutation generation, execution, and reporting."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="tzero_mutation_test_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_count_mutation_points(self):
        code = (
            "def check(x, y):\n"
            "    if x > 10 and y == 5:\n"
            "        return x + y\n"
            "    return False\n"
        )
        count = ASTMutationEngine.count_mutation_points(code)
        # > (comp), == (comp), and (bool), + (binop), False (const) -> 5 mutation points
        self.assertGreaterEqual(count, 4)

    def test_generate_mutants_valid_python(self):
        code = (
            "def calculate(a, b):\n"
            "    if a < b:\n"
            "        return a * b\n"
            "    return a - b\n"
        )
        mutants = ASTMutationEngine.generate_mutants(code, max_mutants=5)
        self.assertGreater(len(mutants), 0)
        for m in mutants:
            self.assertTrue(m.mutant_id.startswith("MUT_"))
            self.assertGreater(m.line_no, 0)
            # Verify mutated code compiles
            compiled = ast.parse(m.mutated_code)
            self.assertIsNotNone(compiled)

    def test_comparison_swap_transformer(self):
        code = "def is_positive(x): return x > 0\n"
        tree = ast.parse(code)
        transformer = ASTMutationTransformer(target_mutation_index=0)
        mutated_tree = transformer.visit(tree)
        mutated_code = ast.unparse(mutated_tree)
        self.assertIn("x <= 0", mutated_code)
        self.assertEqual(transformer.applied_mutation[1], "ComparisonSwap")

    def test_arithmetic_swap_transformer(self):
        code = "def add(x, y): return x + y\n"
        tree = ast.parse(code)
        transformer = ASTMutationTransformer(target_mutation_index=0)
        mutated_tree = transformer.visit(tree)
        mutated_code = ast.unparse(mutated_tree)
        self.assertIn("x - y", mutated_code)
        self.assertEqual(transformer.applied_mutation[1], "ArithmeticOperatorSwap")

    def test_e2e_mutation_testing_killed_vs_survived(self):
        # 1. Create a module to test
        mod_path = os.path.join(self.test_dir, "calculator.py")
        with open(mod_path, "w", encoding="utf-8") as f:
            f.write(
                "def add(a, b):\n"
                "    return a + b\n"
            )

        # 2. Create a strong test that kills mutants
        strong_test = os.path.join(self.test_dir, "test_calc_strong.py")
        with open(strong_test, "w", encoding="utf-8") as f:
            f.write(
                "import unittest\n"
                "import calculator\n"
                "class TestCalc(unittest.TestCase):\n"
                "    def test_add(self):\n"
                "        self.assertEqual(calculator.add(2, 3), 5)\n"
                "if __name__ == '__main__':\n"
                "    unittest.main()\n"
            )

        cmd_strong = f"{sys.executable} -m unittest test_calc_strong.py"
        report_strong = ASTMutationEngine.run_mutation_analysis(
            target_file=mod_path,
            test_command=cmd_strong,
            max_mutants=3
        )
        self.assertEqual(report_strong.killed, 1)
        self.assertEqual(report_strong.survived, 0)
        self.assertEqual(report_strong.mutation_score, 100.0)

        # 3. Create a weak / tautological test where mutant survives
        weak_test = os.path.join(self.test_dir, "test_calc_weak.py")
        with open(weak_test, "w", encoding="utf-8") as f:
            f.write(
                "import unittest\n"
                "import calculator\n"
                "class TestCalc(unittest.TestCase):\n"
                "    def test_dummy(self):\n"
                "        calculator.add(2, 3)\n"  # No assertion!
                "        self.assertTrue(True)\n"
                "if __name__ == '__main__':\n"
                "    unittest.main()\n"
            )

        cmd_weak = f"{sys.executable} -m unittest test_calc_weak.py"
        report_weak = ASTMutationEngine.run_mutation_analysis(
            target_file=mod_path,
            test_command=cmd_weak,
            max_mutants=3
        )
        self.assertEqual(report_weak.survived, 1)
        self.assertEqual(report_weak.mutation_score, 0.0)

    def test_format_markdown_report(self):
        report = MutationReport(
            file_path="src/engine.py",
            total_mutants=5,
            killed=4,
            survived=1,
            timeouts=0,
            errors=0,
            mutation_score=80.0,
            duration_seconds=1.25,
            mutants=[
                Mutant("MUT_001", 10, "ComparisonSwap", "x > 0", "x <= 0", "...", "KILLED"),
                Mutant("MUT_002", 15, "ArithmeticSwap", "a + b", "a - b", "...", "SURVIVED")
            ]
        )
        md = ASTMutationEngine.format_markdown_report(report)
        self.assertIn("T-Zero AST Mutation & Test Quality Report", md)
        self.assertIn("80.0%", md)
        self.assertIn("4/5 mutants killed", md)
        self.assertIn("MUT_001", md)
        self.assertIn("MUT_002", md)
        self.assertIn("Recommendation for Surviving Mutants", md)


if __name__ == "__main__":
    unittest.main()
