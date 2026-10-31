# -*- coding: utf-8 -*-
"""Unit tests for Local Semantic Commit Synthesizer and CI Generator."""

import os
import tempfile
import unittest

from tzero_commit import LocalSemanticCommitSynthesizer
from tzero_ci import CIPipelineGenerator


class TestCommitAndCI(unittest.TestCase):
    def test_analyze_diff_feat(self):
        sample_diff = """
diff --git a/services/payment.py b/services/payment.py
--- a/services/payment.py
+++ b/services/payment.py
@@ -10,2 +10,6 @@ class PaymentProcessor:
+    def process_charge(self, amount: int) -> bool:
+        return True
"""
        sem = LocalSemanticCommitSynthesizer.analyze_diff(sample_diff)
        self.assertEqual(sem.commit_type, "feat")
        self.assertIn("PaymentProcessor", sem.headline)
        self.assertTrue(len(sem.bullets) > 0)

    def test_analyze_diff_test(self):
        sample_diff = """
diff --git a/tests/test_payment.py b/tests/test_payment.py
--- a/tests/test_payment.py
+++ b/tests/test_payment.py
@@ -1,2 +1,5 @@
+def test_charge():
+    assert True
"""
        sem = LocalSemanticCommitSynthesizer.analyze_diff(sample_diff)
        self.assertEqual(sem.commit_type, "test")

    def test_generate_commit_message_format(self):
        sample_diff = """
diff --git a/tzero_patch.py b/tzero_patch.py
--- a/tzero_patch.py
+++ b/tzero_patch.py
@@ -1,2 +1,4 @@
+def apply_fuzzy_patch():
+    pass
"""
        msg = LocalSemanticCommitSynthesizer.generate_commit_message(diff_override=sample_diff)
        self.assertTrue(msg.startswith("feat(patcher):"))
        self.assertIn("Signed-off-by:", msg)
        self.assertIn("apply_fuzzy_patch", msg)

    def test_generate_changelog_entry(self):
        entry = LocalSemanticCommitSynthesizer.generate_changelog_entry(version="v8.2.0")
        self.assertIn("## [v8.2.0]", entry)

    def test_install_ci_templates(self):
        with tempfile.TemporaryDirectory() as td:
            ok_gh, gh_path = CIPipelineGenerator.install_github_workflow(td)
            self.assertTrue(ok_gh)
            self.assertTrue(os.path.exists(gh_path))
            with open(gh_path, "r", encoding="utf-8") as f:
                self.assertIn("T-Zero Autonomous Quality & Zero-Leak Gate", f.read())

            ok_gl, gl_path = CIPipelineGenerator.install_gitlab_ci(td)
            self.assertTrue(ok_gl)
            self.assertTrue(os.path.exists(gl_path))

            ok_pc, pc_path = CIPipelineGenerator.install_pre_commit(td)
            self.assertTrue(ok_pc)
            self.assertTrue(os.path.exists(pc_path))


if __name__ == "__main__":
    unittest.main()
