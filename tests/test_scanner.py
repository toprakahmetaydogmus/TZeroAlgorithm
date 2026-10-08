# -*- coding: utf-8 -*-
"""Unit tests for TokenReducer and CodebaseScanner."""

import os
import ast
import tempfile
import unittest

from tzero_v3 import (
    CodebaseScanner,
    DependencyAnalyzer,
    TokenReducer,
    resolve_default_workspace,
)


class TestTokenReducer(unittest.TestCase):
    def test_python_reduction_ultra(self):
        sample_code = '''"""Module docstring."""
import os
import sys

class DataProcessor:
    """Class docstring."""
    def __init__(self, name):
        self.name = name
        # Internal comment
        print("Initializing")
        x = 10 + 20

    def compute(self, val):
        """Docstring."""
        res = val * 42
        return res
'''
        reduced = TokenReducer.reduce(sample_code, "test.py", mode="ultra")
        self.assertIn("import os", reduced)
        self.assertIn("class DataProcessor", reduced)
        self.assertIn("def __init__", reduced)
        self.assertIn("def compute", reduced)
        # Internal expressions should be pruned in ultra mode
        self.assertNotIn('x = 10 + 20', reduced)
        self.assertNotIn('print("Initializing")', reduced)

    def test_python_reduction_ultra_preserves_multiline_headers(self):
        sample_code = '''from collections import (
    defaultdict,
    deque,
)

class DataProcessor(
    BaseProcessor,
    LoggerMixin,
):
    @classmethod
    async def process_data(
        cls,
        data: list[str],
        threshold: float,
        normalize: bool = True,
    ) -> dict:
        return {"data": data}
'''
        reduced = TokenReducer.reduce(sample_code, "test.py", mode="ultra")

        self.assertEqual(
            reduced,
            '''from collections import (
    defaultdict,
    deque,
)
class DataProcessor(
    BaseProcessor,
    LoggerMixin,
):
    @classmethod
    async def process_data(
        cls,
        data: list[str],
        threshold: float,
        normalize: bool = True,
    ) -> dict:''',
        )

    def test_python_reduction_ultra_preserves_multiline_function_signature(self):
        code = '''def process_data(
    data: list[str],
    threshold: float,
    normalize: bool = True,
) -> dict:
    ...
'''

        reduced = TokenReducer.reduce(code, "example.py", mode="ultra")

        self.assertEqual(
            reduced,
            '''def process_data(
    data: list[str],
    threshold: float,
    normalize: bool = True,
) -> dict:''',
        )

    def test_python_reduction_ultra_falls_back_for_invalid_syntax(self):
        code = "from package import (\ndef available():\n    pass\n"

        reduced = TokenReducer.reduce(code, "test.py", mode="ultra")

        self.assertIn("from package import (", reduced)
        self.assertIn("def available():", reduced)
        self.assertNotIn("    pass", reduced)

    def test_javascript_reduction(self):
        sample_js = '''import React from 'react';
// Comment
export function UserProfile({ id }) {
    const [state, setState] = useState(null);
    console.log("Rendering");
    return <div>User</div>;
}
export class MyService {
}
'''
        reduced = TokenReducer.reduce(sample_js, "component.jsx", mode="ultra")
        self.assertIn("export function UserProfile", reduced)
        self.assertIn("export class MyService", reduced)

    def test_none_reduction_mode(self):
        code = "def foo():\n    return 42\n"
        self.assertEqual(TokenReducer.reduce(code, "foo.py", mode="none"), code)


class TestDependencyAnalyzer(unittest.TestCase):
    def test_import_extraction(self):
        code = """import os, sys\nfrom collections import defaultdict\nfrom typing import Dict, Any"""
        tree = ast.parse(code)
        analyzer = DependencyAnalyzer()
        analyzer.visit(tree)
        self.assertIn("os", analyzer.dependencies)
        self.assertIn("sys", analyzer.dependencies)
        self.assertIn("collections", analyzer.dependencies)
        self.assertIn("typing", analyzer.dependencies)


class TestCodebaseScanner(unittest.TestCase):
    def test_scanner_with_temp_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = os.path.join(temp_dir, "a.py")
            file2 = os.path.join(temp_dir, "b.js")
            ignored = os.path.join(temp_dir, ".git", "hidden.py")
            ignored_venv = os.path.join(temp_dir, ".venv-1", "hidden.py")
            os.makedirs(os.path.dirname(ignored), exist_ok=True)
            os.makedirs(os.path.dirname(ignored_venv), exist_ok=True)

            with open(file1, "w") as f:
                f.write("def sample_a(): pass")
            with open(file2, "w") as f:
                f.write("function sampleB() {}")
            with open(ignored, "w") as f:
                f.write("def ignored(): pass")
            with open(ignored_venv, "w") as f:
                f.write("def ignored_venv(): pass")

            scanner = CodebaseScanner()
            files, sizes, snippets = scanner.scan_directory(temp_dir)

            self.assertIn("a.py", files)
            self.assertIn("b.js", files)
            # Ignored folder should not appear
            self.assertFalse(any(".git" in f for f in files))
            self.assertFalse(any(".venv-1" in f for f in files))


class TestDefaultWorkspace(unittest.TestCase):
    def test_resolves_project_root_when_launched_from_dist(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = os.path.join(temp_dir, "project")
            dist_dir = os.path.join(project_root, "dist")
            os.makedirs(dist_dir)
            for filename in ("tzero_v3.py", "pyproject.toml"):
                with open(os.path.join(project_root, filename), "w") as file:
                    file.write("")

            self.assertEqual(
                resolve_default_workspace(dist_dir),
                project_root,
            )

    def test_keeps_explicit_non_build_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = os.path.join(temp_dir, "workspace")
            os.makedirs(workspace)

            self.assertEqual(resolve_default_workspace(workspace), workspace)


if __name__ == "__main__":
    unittest.main()
