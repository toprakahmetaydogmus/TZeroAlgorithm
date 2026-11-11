# -*- coding: utf-8 -*-
"""Unit tests for AST Smart Micro-Patch Compressor."""

import unittest
from tzero.tzero_patch import SmartMicroPatcher


class TestSmartMicroPatcher(unittest.TestCase):
    def test_compress_unified_diff(self):
        raw_diff = """
diff --git a/services/payment.py b/services/payment.py
index 4b825dc..91a72fb 100644
--- a/services/payment.py
+++ b/services/payment.py
@@ -20,7 +20,7 @@ class PaymentProcessor:
     def __init__(self, gateway_url: str):
         self.gateway_url = gateway_url
         self.timeout = 30
-        self.sandbox = True
+        self.sandbox = False
         self.retry_limit = 3
 
     def charge(self, amount: int) -> bool:
"""
        compact, savings = SmartMicroPatcher.compress_diff(raw_diff)
        self.assertGreater(savings, 30.0)
        self.assertIn("[services/payment.py]", compact)
        self.assertIn("class PaymentProcessor:", compact)
        self.assertIn("-        self.sandbox = True", compact)
        self.assertIn("+        self.sandbox = False", compact)
        self.assertNotIn("index 4b825dc", compact)

    def test_format_micro_patch_report(self):
        raw_diff = """
diff --git a/main.go b/main.go
--- a/main.go
+++ b/main.go
@@ -5,3 +5,3 @@ func Start() {
-	port := ":8080"
+	port := ":9000"
 }
"""
        report = SmartMicroPatcher.format_micro_patch_report(raw_diff)
        self.assertIn("# 🧩 T-Zero AST Smart Micro-Patch", report)
        self.assertIn("```patch", report)
        self.assertIn("port := \":9000\"", report)


class TestASTFuzzyPatcher(unittest.TestCase):
    """Thorough tests for ASTFuzzyPatcher across all 5 tiers of tolerance."""

    def test_tier1_exact_patch(self):
        from tzero.tzero_patch import apply_fuzzy_patch
        source = (
            "def add(a, b):\n"
            "    # old comment\n"
            "    return a + b\n"
        )
        patch = (
            "@@ -1,3 +1,3 @@ def add(a, b):\n"
            " def add(a, b):\n"
            "-    # old comment\n"
            "+    # new comment\n"
            "     return a + b\n"
        )
        ok, res, meta = apply_fuzzy_patch(source, patch)
        self.assertTrue(ok)
        self.assertEqual(meta["applied_hunks"], 1)
        self.assertEqual(meta["hunk_results"][0]["strategy"], "exact")
        self.assertIn("# new comment", res)

    def test_tier2_line_drift_patch(self):
        from tzero.tzero_patch import apply_fuzzy_patch
        # Function has drifted 20 lines down because other functions were added
        source = "\n" * 20 + (
            "def multiply(x, y):\n"
            "    result = x * y\n"
            "    return result\n"
        )
        # Patch thinks it is at line 1
        patch = (
            "@@ -1,3 +1,3 @@ def multiply(x, y):\n"
            " def multiply(x, y):\n"
            "-    result = x * y\n"
            "+    result = x * y * 1.0\n"
            "     return result\n"
        )
        ok, res, meta = apply_fuzzy_patch(source, patch)
        self.assertTrue(ok)
        self.assertEqual(meta["hunk_results"][0]["strategy"], "line_drift")
        self.assertIn("result = x * y * 1.0", res)

    def test_tier3_whitespace_and_indentation_adaptation(self):
        from tzero.tzero_patch import apply_fuzzy_patch
        # Source has 8-space indentation
        source = (
            "class Engine:\n"
            "    def run(self):\n"
            "        timeout = 30\n"
            "        return timeout\n"
        )
        # Patch was generated with 2-space indentation by an LLM
        patch = (
            "@@ -3,2 +3,2 @@ def run(self):\n"
            "-  timeout = 30\n"
            "+  timeout = 60\n"
            "   return timeout\n"
        )
        ok, res, meta = apply_fuzzy_patch(source, patch)
        self.assertTrue(ok)
        self.assertEqual(meta["hunk_results"][0]["strategy"], "whitespace_normalized")
        # Ensure 8-space indentation was applied to preserve target code structure
        self.assertIn("        timeout = 60\n", res)

    def test_tier4_ast_symbol_boundary(self):
        from tzero.tzero_patch import apply_fuzzy_patch
        # Target file has multiple similar lines, but hunk targets specific function
        source = (
            "def worker_a():\n"
            "    val = 10\n"
            "    return val\n\n"
            "def worker_b():\n"
            "    val = 10\n"
            "    return val\n"
        )
        patch = (
            "@@ -2,2 +2,2 @@ def worker_b():\n"
            "-    val = 10\n"
            "+    val = 999\n"
            "     return val\n"
        )
        ok, res, meta = apply_fuzzy_patch(source, patch)
        self.assertTrue(ok)
        # worker_a should be untouched
        self.assertIn("def worker_a():\n    val = 10", res)
        # worker_b should be updated
        self.assertIn("def worker_b():\n    val = 999", res)

    def test_tier5_fuzzy_similarity_patch(self):
        from tzero.tzero_patch import apply_fuzzy_patch
        # Context line in target differs slightly (comment was tweaked)
        source = (
            "def calculate_total(items):\n"
            "    # calculate sum of items array\n"
            "    total = 0\n"
            "    for i in items: total += i\n"
            "    return total\n"
        )
        # Patch has slightly different context comment
        patch = (
            "@@ -2,4 +2,4 @@ def calculate_total(items):\n"
            "     # calculate sum of items list\n"
            "-    total = 0\n"
            "+    total = 100\n"
            "     for i in items: total += i\n"
        )
        ok, res, meta = apply_fuzzy_patch(source, patch, tolerance=0.70)
        self.assertTrue(ok)
        self.assertIn("total = 100", res)
        self.assertIn(meta["hunk_results"][0]["strategy"], ("fuzzy_similarity", "whitespace_normalized"))

    def test_multi_hunk_bottom_to_top(self):
        from tzero.tzero_patch import apply_fuzzy_patch
        source = (
            "line_one = 1\n"
            "line_two = 2\n"
            "line_three = 3\n"
            "line_four = 4\n"
        )
        patch = (
            "@@ -1,2 +1,2 @@\n"
            "-line_one = 1\n"
            "+line_one = 100\n"
            " line_two = 2\n"
            "@@ -3,2 +3,2 @@\n"
            "-line_three = 3\n"
            "+line_three = 300\n"
            " line_four = 4\n"
        )
        ok, res, meta = apply_fuzzy_patch(source, patch)
        self.assertTrue(ok)
        self.assertEqual(meta["applied_hunks"], 2)
        self.assertIn("line_one = 100", res)
        self.assertIn("line_three = 300", res)

    def test_reverse_patch_unapply(self):
        from tzero.tzero_patch import apply_fuzzy_patch
        source = "value = 42\n"
        patch = (
            "@@ -1,1 +1,1 @@\n"
            "-value = 10\n"
            "+value = 42\n"
        )
        # Reverse apply should take value 42 back to 10
        ok, res, meta = apply_fuzzy_patch(source, patch, reverse=True)
        self.assertTrue(ok)
        self.assertEqual(res.strip(), "value = 10")

    def test_patch_file_with_backup(self):
        import tempfile
        import os
        from tzero.tzero_patch import patch_file

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".py") as tf:
            tf.write("x = 1\ny = 2\n")
            target_path = tf.name

        try:
            patch = "@@ -1,2 +1,2 @@\n-x = 1\n+x = 99\n y = 2\n"
            res = patch_file(target_path, patch, in_place=True, backup=True)
            self.assertTrue(res["success"])
            self.assertTrue(res.get("file_written"))
            self.assertTrue(os.path.exists(res.get("backup_created")))

            # Verify contents
            with open(target_path, "r", encoding="utf-8") as f:
                self.assertIn("x = 99", f.read())
            with open(res.get("backup_created"), "r", encoding="utf-8") as f:
                self.assertIn("x = 1", f.read())
        finally:
            if os.path.exists(target_path):
                os.remove(target_path)
            if os.path.exists(f"{target_path}.bak"):
                os.remove(f"{target_path}.bak")


if __name__ == "__main__":
    unittest.main()

