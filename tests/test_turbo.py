# -*- coding: utf-8 -*-
"""
Tests for Siber Akademi T-Zero Turbo Overdrive & Adaptive Burst Accelerator ("Kamçılama Modu").
"""

import os
import sys
import tempfile
import unittest
import subprocess
from tzero.tzero_turbo import get_turbo_accelerator, TurboOverdriveAccelerator


class TestTurboAccelerator(unittest.TestCase):

    def setUp(self):
        self.turbo = get_turbo_accelerator()
        self.turbo.clear_cache()

    def test_singleton(self):
        t1 = get_turbo_accelerator()
        t2 = TurboOverdriveAccelerator.get_instance()
        self.assertIs(t1, t2)

    def test_cache_hit_and_invalidation(self):
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write("def calculate_total(price: float, tax: float) -> float:\n    return price * (1 + tax)\n")
            tf_path = tf.name

        try:
            def dummy_reducer(code, path, mode):
                return "def calculate_total(...): ..."

            # 1st call: Cache miss
            reduced, was_cached = self.turbo.fast_reduce_file(tf_path, dummy_reducer, mode="ultra")
            self.assertEqual(reduced, "def calculate_total(...): ...")
            self.assertFalse(was_cached)
            self.assertEqual(self.turbo.get_cache_size(), 1)

            # 2nd call: Cache hit
            reduced_2, was_cached_2 = self.turbo.fast_reduce_file(tf_path, dummy_reducer, mode="ultra")
            self.assertEqual(reduced_2, "def calculate_total(...): ...")
            self.assertTrue(was_cached_2)

            # Modify file: cache should invalidate
            with open(tf_path, "a", encoding="utf-8") as f:
                f.write("\n# extra line\n")

            reduced_3, was_cached_3 = self.turbo.fast_reduce_file(tf_path, dummy_reducer, mode="ultra")
            self.assertEqual(reduced_3, "def calculate_total(...): ...")
            self.assertFalse(was_cached_3)
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_parallel_reduce_batch(self):
        temp_files = []
        try:
            for i in range(5):
                tf = tempfile.NamedTemporaryFile("w", suffix=f"_{i}.py", delete=False)
                tf.write(f"def func_{i}(x: int) -> int:\n    return x + {i}\n")
                tf.close()
                temp_files.append(tf.name)

            def mock_reducer(code, path, mode):
                fn_name = os.path.basename(path).replace(".py", "")
                return f"def {fn_name}(...): pass"

            # Run parallel reduce batch
            res = self.turbo.parallel_reduce_batch(temp_files, mock_reducer, mode="ultra")
            self.assertEqual(len(res), 5)
            for p in temp_files:
                self.assertIn(p, res)
                self.assertIn("def ", res[p])
        finally:
            for p in temp_files:
                if os.path.exists(p):
                    os.remove(p)

    def test_parallel_map(self):
        items = list(range(20))
        squares = self.turbo.parallel_map(lambda x: x * x, items)
        self.assertEqual(squares, [x * x for x in items])

    def test_sense_latency_and_whip(self):
        initial_triggers = self.turbo.metrics.overdrive_triggers
        # Simulate an operation that takes slightly over threshold
        with self.turbo.sense_latency("Test Latency Event"):
            import time
            time.sleep(0.16)

        self.assertGreater(self.turbo.metrics.overdrive_triggers, initial_triggers)
        self.assertTrue(any("Test Latency Event" in op for op in self.turbo.metrics.whipped_operations))

    def test_status_report(self):
        report = self.turbo.format_status_report()
        self.assertIn("TURBO OVERDRIVE", report)
        self.assertIn("BURST ACCELERATOR", report)
        self.assertIn("Worker Threads Pool", report)
        self.assertIn("Fast-Path In-Memory", report)

    def test_cli_turbo(self):
        # Test CLI --turbo status
        proc = subprocess.run(
            [sys.executable, "tzero/tzero_v3.py", "--turbo"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("TURBO OVERDRIVE", proc.stdout)
        self.assertIn("BURST ACCELERATOR", proc.stdout)

    def test_cli_kamcilama_alias(self):
        # Test CLI --kamcilama alias
        proc = subprocess.run(
            [sys.executable, "tzero/tzero_v3.py", "--kamcilama"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("TURBO OVERDRIVE", proc.stdout)
        self.assertIn("BURST ACCELERATOR", proc.stdout)


if __name__ == "__main__":
    unittest.main()
