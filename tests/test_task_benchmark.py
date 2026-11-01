# -*- coding: utf-8 -*-
"""
Tests for T-Zero Task-Completion & Real Tokenizer Benchmark Engine.
"""

import unittest
from tzero_task_benchmark import TaskCompletionBenchmark, TaskBenchmarkReport, count_bpe_tokens


class TestTaskBenchmark(unittest.TestCase):
    def test_bpe_token_counter(self):
        text = "def hello_world(name: str) -> str:\n    return f'Hello, {name}'\n"
        tokens = count_bpe_tokens(text)
        self.assertGreater(tokens, 0)
        self.assertLess(tokens, 50)

    def test_prune_to_ast_skeleton(self):
        code = '''
def complex_algorithm(a: int, b: int) -> int:
    """Computes gcd with euclidean method."""
    while b:
        a, b = b, a % b
    return a
'''
        pruned = TaskCompletionBenchmark.prune_to_ast_skeleton(code)
        self.assertIn("def complex_algorithm(a: int, b: int) -> int:", pruned)
        self.assertIn("Computes gcd with euclidean method", pruned)
        self.assertIn("...", pruned)
        self.assertNotIn("while b:", pruned)

    def test_evaluate_all_tasks(self):
        report = TaskCompletionBenchmark.evaluate_all()
        self.assertIsInstance(report, TaskBenchmarkReport)
        self.assertEqual(report.total_tasks, 3)
        self.assertEqual(report.passed_tasks, 3)
        self.assertEqual(report.success_rate_pct, 100.0)
        self.assertGreater(report.total_raw_tokens, report.total_tzero_tokens)
        self.assertGreater(report.average_token_reduction_pct, 10.0)

    def test_terminal_summary_format(self):
        report = TaskCompletionBenchmark.evaluate_all()
        summary = TaskCompletionBenchmark.format_terminal_summary(report)
        self.assertIn("TASK-01", summary)
        self.assertIn("PASS (0 Halluc)", summary)
        self.assertIn("OVERALL TASK SUCCESS RATE: 100.0%", summary)


if __name__ == "__main__":
    unittest.main()
