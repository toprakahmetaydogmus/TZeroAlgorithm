# -*- coding: utf-8 -*-
"""Unit tests for AST static code analyzer and refactoring engine."""

import ast
import unittest

from tzero_v3 import (
    StaticCodeAnalyzer,
    PythonASTParser,
    PythonASTRefactorer,
    WorkspaceDuplicityFinder,
)


class TestStaticCodeAnalyzer(unittest.TestCase):
    def test_missing_docstring_and_too_many_args(self):
        code = "def bad_func(a, b, c, d, e, f, g, h):\n    pass\n"
        analyzer = StaticCodeAnalyzer("sample.py")
        analyzer.analyze_source(code)
        
        issue_refs = [i["ref"] for i in analyzer.issues]
        self.assertIn("NoDocstring", issue_refs)
        self.assertIn("TooManyArguments", issue_refs)

    def test_async_function_support(self):
        code = "async def async_worker(a, b, c, d, e, f, g):\n    pass\n"
        analyzer = StaticCodeAnalyzer("sample_async.py")
        analyzer.analyze_source(code)
        
        issue_refs = [i["ref"] for i in analyzer.issues]
        self.assertIn("NoDocstring", issue_refs)
        self.assertIn("TooManyArguments", issue_refs)

    def test_global_keyword_smell(self):
        code = "global state_var\nstate_var = 1\n"
        analyzer = StaticCodeAnalyzer("globals.py")
        analyzer.analyze_source(code)
        issue_refs = [i["ref"] for i in analyzer.issues]
        self.assertIn("GlobalKeyword", issue_refs)


class TestPythonASTParser(unittest.TestCase):
    def test_class_and_methods_outline(self):
        code = """class Engine:\n    def start(self): pass\n    async def stop(self): pass\n"""
        tree = ast.parse(code)
        parser = PythonASTParser()
        parser.visit(tree)

        self.assertEqual(len(parser.outline), 1)
        cls_info = parser.outline[0]
        self.assertEqual(cls_info["name"], "Engine")
        self.assertEqual(len(cls_info["methods"]), 2)
        method_names = [m["name"] for m in cls_info["methods"]]
        self.assertIn("start", method_names)
        self.assertIn("stop", method_names)


class TestPythonASTRefactorer(unittest.TestCase):
    def test_rename_function(self):
        code = """def old_compute(x):\n    return x + 1\nresult = old_compute(10)\n"""
        tree = ast.parse(code)
        refactorer = PythonASTRefactorer("old_compute", "new_compute")
        new_tree = refactorer.visit(tree)
        new_code = ast.unparse(new_tree)

        self.assertTrue(refactorer.modified)
        self.assertIn("def new_compute(x):", new_code)
        self.assertIn("result = new_compute(10)", new_code)
        self.assertNotIn("old_compute", new_code)


class TestWorkspaceDuplicityFinder(unittest.TestCase):
    def test_duplicate_blocks(self):
        block = "line1\nline2\nline3\nline4\nline5\nline6\nline7\n"
        snippets = {
            "module_a.py": f"header_a\n{block}\nfooter_a",
            "module_b.py": f"header_b\n{block}\nfooter_b",
        }
        finder = WorkspaceDuplicityFinder(snippets)
        dups = finder.find_duplicates(min_lines=6)
        self.assertGreaterEqual(len(dups), 1)
        self.assertEqual(dups[0]["file1"], "module_a.py")
        self.assertEqual(dups[0]["file2"], "module_b.py")


if __name__ == "__main__":
    unittest.main()
