# -*- coding: utf-8 -*-
"""Unit tests for T-Zero CLI Stdin/Stdout Pipe & Streaming Token Compressor."""

import unittest
from tzero.tzero_pipe import PipeCompressor


class TestPipeCompressor(unittest.TestCase):
    def test_compress_python_stream(self):
        code = '''
def calculate_heavy_load(x: int, y: int) -> int:
    """Detailed docstring that takes up tokens."""
    # Internal logic comment
    val = x * 100
    for i in range(10):
        val += i
    return val + y

class AnalyticsEngine:
    def __init__(self):
        self.state = 1
    def run(self):
        print("Running")
'''
        compressed = PipeCompressor.compress_stream(code, filename_hint="service.py", tier="T-3")
        self.assertIn("def calculate_heavy_load", compressed)
        self.assertIn("class AnalyticsEngine", compressed)
        # Detailed comments/bodies should be pruned in T-3 AST mode
        self.assertNotIn("Detailed docstring that takes up tokens", compressed)
        self.assertLess(len(compressed), len(code))

    def test_compress_sql_stream(self):
        sql = '''
CREATE TABLE users (
    id INT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    created_at TIMESTAMP
);

INSERT INTO users (id, username) VALUES (1, 'alice'), (2, 'bob');
'''
        compressed = PipeCompressor.compress_stream(sql, filename_hint="schema.sql", tier="T-3")
        self.assertIn("CREATE TABLE users", compressed)
        self.assertNotIn("INSERT INTO users", compressed)

    def test_compress_diff_stream_autodetect(self):
        diff = '''diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,3 +1,3 @@
 def hello():
-    return 1
+    return 2
'''
        # Even without filename_hint, autodetect git diff
        compressed = PipeCompressor.compress_stream(diff, filename_hint="", tier="T-3")
        self.assertIn("📁 [app.py]", compressed)
        self.assertIn("+    return 2", compressed)

    def test_empty_and_whitespace_stream(self):
        self.assertEqual(PipeCompressor.compress_stream(""), "")
        self.assertEqual(PipeCompressor.compress_stream("   \n\t  "), "")


if __name__ == "__main__":
    unittest.main()
