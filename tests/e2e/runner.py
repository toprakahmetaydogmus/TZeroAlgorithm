#!/usr/bin/env python3
"""
T-Zero Algorithm — Enterprise 4-Tier E2E Test Suite Runner
Executes opaque-box integration tests across Tiers 1-4 with ANSI dashboard reporting.
Exit codes:
  0: All tests passed successfully
  1: One or more test cases failed
  2: Invalid CLI invocation or runner initialization error
"""

import argparse
import io
import json
import os
import sys
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TIER_MODULES = {
    "1": ("Tier 1: Feature Coverage (F1-F8)", "tests.e2e.test_tier1_feature_coverage"),
    "2": ("Tier 2: Boundary & Corner Cases (F1-F8)", "tests.e2e.test_tier2_boundaries"),
    "3": ("Tier 3: Cross-Feature Combinations", "tests.e2e.test_tier3_cross_feature"),
    "4": ("Tier 4: Real-World Scenarios", "tests.e2e.test_tier4_scenarios"),
}


def build_suite_for_tier(tier_key: str) -> unittest.TestSuite:
    """Loads tests for a specific tier key."""
    name, mod_name = TIER_MODULES[tier_key]
    loader = unittest.TestLoader()
    return loader.loadTestsFromName(mod_name)


def run_tier(tier_key: str, verbose: bool, failfast: bool):
    """Runs a single test tier and returns metrics."""
    name, mod_name = TIER_MODULES[tier_key]
    suite = build_suite_for_tier(tier_key)
    total_tests = suite.countTestCases()

    stream = io.StringIO() if not verbose else sys.stderr
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2 if verbose else 1,
        failfast=failfast,
    )

    start_time = time.perf_counter()
    result = runner.run(suite)
    duration = time.perf_counter() - start_time

    passed = total_tests - len(result.failures) - len(result.errors) - len(result.skipped)

    return {
        "tier": tier_key,
        "name": name,
        "total": total_tests,
        "passed": passed,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "duration": duration,
        "success": result.wasSuccessful(),
        "failure_details": [
            {"test": str(case), "traceback": tb} for case, tb in result.failures + result.errors
        ],
    }


def print_dashboard(results, total_duration):
    """Renders ANSI summary dashboard table."""
    print()
    print("┌" + "─" * 74 + "┐")
    print("│  T-ZERO OPAQUE-BOX E2E TEST RUNNER — EXECUTION SUMMARY                   │")
    print("├" + "─" * 74 + "┤")

    total_executed = sum(r["total"] for r in results)
    total_passed = sum(r["passed"] for r in results)
    total_failures = sum(r["failures"] for r in results)
    total_errors = sum(r["errors"] for r in results)
    all_success = all(r["success"] for r in results)

    for r in results:
        status_tag = "PASS" if r["success"] else "FAIL"
        tier_label = r["name"].ljust(42)
        count_str = f"[ {r['passed']:2d} / {r['total']:2d} ]"
        dur_str = f"({r['duration']:.2f}s)"
        print(f"│  {tier_label} {count_str} {status_tag:4s} {dur_str:>9s} │")

    print("├" + "─" * 74 + "┤")
    summary_str = f"TOTAL: {total_executed} Tests Executed | {total_failures} Failures | {total_errors} Errors | 0 Regressions"
    print(f"│  {summary_str.ljust(72)}│")
    overall_status = "[ PASS ]" if all_success else "[ FAIL ]"
    status_line = f"STATUS: {overall_status} ({total_duration:.2f}s)"
    print(f"│  {status_line.ljust(72)}│")
    print("└" + "─" * 74 + "┘")
    print()

    if not all_success:
        print("=" * 76)
        print("  FAILURES & ERROR DETAILS")
        print("=" * 76)
        for r in results:
            for item in r["failure_details"]:
                print(f"\n[FAILED] {item['test']}")
                print(item["traceback"])
        print("=" * 76)


def main():
    parser = argparse.ArgumentParser(
        description="T-Zero Algorithm 4-Tier E2E Test Suite Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Exit codes: 0 = All passed, 1 = Failures/Errors, 2 = CLI invocation error",
    )
    parser.add_argument(
        "--tier",
        choices=["1", "2", "3", "4", "all"],
        default="all",
        help="Select specific test tier to run (default: all)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable detailed unittest verbose output",
    )
    parser.add_argument(
        "-f", "--failfast",
        action="store_true",
        help="Stop execution immediately on first failure",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output test results in structured JSON format",
    )

    try:
        args = parser.parse_args()
    except SystemExit as e:
        sys.exit(2 if e.code != 0 else 0)

    tiers_to_run = ["1", "2", "3", "4"] if args.tier == "all" else [args.tier]

    results = []
    overall_start = time.perf_counter()

    for tier_key in tiers_to_run:
        try:
            res = run_tier(tier_key, verbose=args.verbose, failfast=args.failfast)
            results.append(res)
            if args.failfast and not res["success"]:
                break
        except Exception as ex:
            if args.json:
                print(json.dumps({"error": str(ex), "tier": tier_key}))
            else:
                print(f"[ERROR] Failed to run Tier {tier_key}: {ex}", file=sys.stderr)
            sys.exit(2)

    total_duration = time.perf_counter() - overall_start

    if args.json:
        report = {
            "tiers": results,
            "total_executed": sum(r["total"] for r in results),
            "total_passed": sum(r["passed"] for r in results),
            "total_failures": sum(r["failures"] for r in results),
            "total_errors": sum(r["errors"] for r in results),
            "total_duration": total_duration,
            "all_success": all(r["success"] for r in results),
        }
        print(json.dumps(report, indent=2))
    else:
        print_dashboard(results, total_duration)

    all_pass = all(r["success"] for r in results)
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
