# -*- coding: utf-8 -*-
"""Unit tests for T-Zero Autonomous Code Health & Technical Debt Index (tzero_debt.py)."""

import ast
import unittest
from tzero_debt import (
    CodeHealthAnalyzer,
    ASTCognitiveComplexityVisitor,
)


class TestCodeHealthAnalyzer(unittest.TestCase):
    def test_compute_cognitive_complexity(self):
        # A simple linear function has 0 cognitive complexity
        simple_code = '''
def add(a, b):
    return a + b
'''
        tree_simple = ast.parse(simple_code)
        cog_simple = CodeHealthAnalyzer.compute_cognitive_complexity(tree_simple)
        self.assertEqual(cog_simple, 0)

        # Deeply nested loops and conditions should have higher cognitive complexity
        complex_code = '''
def process(matrix):
    total = 0
    for row in matrix:          # +1 (nesting 0)
        for val in row:         # +2 (nesting 1)
            if val > 0:         # +3 (nesting 2)
                if val % 2 == 0:# +4 (nesting 3)
                    total += val
    return total
'''
        tree_complex = ast.parse(complex_code)
        cog_complex = CodeHealthAnalyzer.compute_cognitive_complexity(tree_complex)
        # 1 + 2 + 3 + 4 = 10
        self.assertEqual(cog_complex, 10)

    def test_compute_cyclomatic_complexity(self):
        code = '''
def evaluate(x):
    if x > 10:
        return 1
    elif x > 5:
        return 2
    else:
        return 3
'''
        tree = ast.parse(code)
        cc = CodeHealthAnalyzer.compute_cyclomatic_complexity(tree)
        # Decision points: if (1) + elif (1) + 1 = 3
        self.assertEqual(cc, 3)

    def test_maintainability_index(self):
        code = '''
def hello():
    print("world")
'''
        mi = CodeHealthAnalyzer.compute_maintainability_index(code, cyclomatic=1)
        self.assertGreaterEqual(mi, 70.0)
        self.assertLessEqual(mi, 100.0)

    def test_extract_debt_markers(self):
        code = '''
# TODO: Optimize database query
x = 10
# FIXME: Handle None pointer
y = 20
# HACK: Workaround for legacy API
'''
        markers = CodeHealthAnalyzer.extract_debt_markers(code)
        self.assertEqual(len(markers), 3)
        tags = [m["tag"] for m in markers]
        self.assertIn("TODO", tags)
        self.assertIn("FIXME", tags)
        self.assertIn("HACK", tags)

    def test_analyze_file_and_god_class(self):
        code = '''
class MegaGodManager:
    """Class with too many methods."""
    def m1(self): pass
    def m2(self): pass
    def m3(self): pass
    def m4(self): pass
    def m5(self): pass
    def m6(self): pass
    def m7(self): pass
    def m8(self): pass
    def m9(self): pass
    def m10(self): pass
    def m11(self): pass
    def m12(self): pass
    def m13(self): pass

# TODO: Refactor god class
'''
        rep = CodeHealthAnalyzer.analyze_file("mega.py", code=code)
        self.assertIn(rep.rating, ["A", "B", "C", "D"])
        self.assertEqual(len(rep.classes), 1)
        self.assertTrue(rep.classes[0].is_god_class)
        self.assertGreater(rep.debt_hours, 0.0)
        self.assertEqual(rep.todo_count, 1)

    def test_analyze_workspace_and_markdown(self):
        ws_rep = CodeHealthAnalyzer.analyze_workspace(".", max_files=10)
        self.assertGreaterEqual(ws_rep.total_files, 1)
        self.assertGreaterEqual(ws_rep.average_maintainability_index, 0.0)
        self.assertIn(ws_rep.overall_rating, ["A", "B", "C", "D"])

        md = CodeHealthAnalyzer.format_markdown_report(ws_rep)
        self.assertIn("T-Zero Code Health & Technical Debt Index", md)
        self.assertIn("Executive Summary Metrics", md)


if __name__ == "__main__":
    unittest.main()
