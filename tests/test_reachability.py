# -*- coding: utf-8 -*-
"""Unit tests for T-Zero Cross-Module AST Reachability & Dead-Code Pruning Engine."""

import os
import sys
import tempfile
import unittest
import shutil

from tzero.tzero_reachability import CallGraphReachabilityEngine


class TestCallGraphReachability(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="tzero_reach_test_")
        
        # Create a mock project structure with 2 modules:
        # module_a.py has main() which calls helper_used(), but NOT dead_func_a()
        # module_b.py has helper_used() which calls service_active(), but NOT dead_func_b()
        self.file_a = os.path.join(self.test_dir, "module_a.py")
        with open(self.file_a, "w", encoding="utf-8") as f:
            f.write('''
from module_b import helper_used

def dead_func_a():
    return "I am never called"

def main():
    val = helper_used()
    print("Result:", val)

if __name__ == "__main__":
    main()
''')

        self.file_b = os.path.join(self.test_dir, "module_b.py")
        with open(self.file_b, "w", encoding="utf-8") as f:
            f.write('''
def service_active():
    return 42

def helper_used():
    return service_active()

def dead_func_b():
    return "Dead code in module B"
''')

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_reachability_graph_and_pruning(self):
        engine = CallGraphReachabilityEngine(self.test_dir)
        report = engine.generate_zero_waste_prompt(entrypoints=["module_a.py"])
        
        self.assertIn("reachable_symbols", report)
        self.assertIn("dead_symbols", report)
        self.assertIn("zero_waste_prompt", report)
        
        reachable_names = [s["name"] for s in report["reachable_symbols"]]
        dead_names = [s["name"] for s in report["dead_symbols"]]
        
        self.assertIn("main", reachable_names)
        self.assertIn("helper_used", reachable_names)
        self.assertIn("service_active", reachable_names)
        
        self.assertIn("dead_func_a", dead_names)
        self.assertIn("dead_func_b", dead_names)
        
        # Zero-waste prompt must contain active code and omit dead code
        prompt_text = report["zero_waste_prompt"]
        self.assertIn("def service_active():", prompt_text)
        self.assertNotIn("dead_func_a", prompt_text)
        self.assertNotIn("dead_func_b", prompt_text)
        
        # Verify stats
        self.assertGreaterEqual(report["pruned_dead_count"], 2)
        self.assertGreater(report["token_reduction_pct"], 0)

    def test_circular_call_cycle_safety(self):
        # Create circular reference: func1 calls func2, func2 calls func1
        cycle_file = os.path.join(self.test_dir, "cycle.py")
        with open(cycle_file, "w", encoding="utf-8") as f:
            f.write('''
def func1():
    return func2()

def func2():
    return func1()

def main():
    return func1()
''')
        engine = CallGraphReachabilityEngine(self.test_dir)
        report = engine.generate_zero_waste_prompt(entrypoints=["cycle.py"])
        reachable_names = [s["name"] for s in report["reachable_symbols"]]
        self.assertIn("func1", reachable_names)
        self.assertIn("func2", reachable_names)
        self.assertIn("main", reachable_names)


if __name__ == "__main__":
    unittest.main()
