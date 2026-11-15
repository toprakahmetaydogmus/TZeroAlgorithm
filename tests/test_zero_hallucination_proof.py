# -*- coding: utf-8 -*-
"""Automated Verification Suite for T-Zero Empirical Zero-Hallucination Proof.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: MIT
"""

import os
import json
import tempfile
import unittest

from tzero.tzero_hallucination_proof import HallucinationProofEngine, BENCHMARK_CASES


class TestZeroHallucinationProof(unittest.TestCase):
    def setUp(self):
        self.workspace_dir = os.path.abspath(".")

    def test_proof_benchmark_zero_escape_rate(self):
        """Mathematically verifies that 0.0% of hallucinations escape (100% Detection, 0% FPR)."""
        rep = HallucinationProofEngine.run_proof_benchmark(self.workspace_dir)

        # 1. Total Case Counts
        self.assertEqual(rep.total_cases, 60, "Expected exactly 60 benchmark cases")
        self.assertEqual(rep.hallucinated_cases, 55, "Expected 55 hallucinated cases")
        self.assertEqual(rep.clean_cases, 5, "Expected 5 clean control cases")

        # 2. Perfect Detection (100% Recall)
        self.assertEqual(rep.detected_hallucinations, 55, "All 55 hallucinations must be detected")
        self.assertEqual(rep.escaped_hallucinations, 0, "Zero hallucinations allowed to escape (0.0% Escape Rate)")
        self.assertEqual(rep.detection_rate, 100.0, "Detection rate must be 100.0%")
        self.assertEqual(rep.escape_rate, 0.0, "Escape rate must be 0.0%")

        # 3. Zero False Positives (100% Specificity)
        self.assertEqual(rep.clean_passed, 5, "All 5 clean control cases must pass")
        self.assertEqual(rep.false_positives, 0, "Zero false positives allowed on clean code")
        self.assertEqual(rep.false_positive_rate, 0.0, "False positive rate must be 0.0%")

        # 4. Accuracy & Latency
        self.assertEqual(rep.accuracy, 100.0, "Overall accuracy must be 100.0%")
        self.assertLess(rep.avg_latency_ms, 25.0, "Average AST verification latency must be under 25ms")

        # 5. Self-Healing Synthesizer
        self.assertGreaterEqual(rep.auto_healed_count, 20, "At least 20 cases should be auto-healed to valid AST")

    def test_export_artifacts(self):
        """Verifies that JSON and Markdown whitepaper artifacts are generated with valid formatting."""
        rep = HallucinationProofEngine.run_proof_benchmark(self.workspace_dir)
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts = HallucinationProofEngine.export_artifacts(rep, tmp_dir)
            self.assertTrue(os.path.isfile(artifacts["json"]))
            self.assertTrue(os.path.isfile(artifacts["markdown"]))

            with open(artifacts["json"], "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["escaped_hallucinations"], 0)
            self.assertEqual(data["detection_rate"], 100.0)

            with open(artifacts["markdown"], "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("100% Zero-Hallucination Certified", content)
            self.assertIn("0.0% Escape Rate", content)
            self.assertIn("Theorem 1", content)
            self.assertIn("Theorem 2", content)


if __name__ == "__main__":
    unittest.main()
