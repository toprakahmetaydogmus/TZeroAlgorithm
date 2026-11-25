# -*- coding: utf-8 -*-
"""Zero-dependency parallel unittest runner with longest-job-first scheduling."""

import concurrent.futures
import os
import pathlib
import subprocess
import sys
import time
import unittest
from typing import List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

HEAVY_FILES = {
    "test_e2e_full.py",
    "test_cli_comprehensive.py",
    "test_local_ci.py",
    "test_mcp.py",
}

TARGET_PRIORITY = {
    "test_tool_01_to_10": 0,
    "test_execute_codebase_workflow_actions": 1,
    "test_tool_11_to_20": 2,
    "test_tool_21_to_37": 3,
    "test_cli_local_ci_flags": 4,
    "test_full_pipeline_run_quick": 5,
    "test_terminal_report_rendering": 6,
    "test_mcp_local_ci_tool_routing": 7,
    "test_tool_sync_cost_drift": 8,
    "test_fixer_deep.py": 9,
    "test_cli.py": 10,
}


def _collect_suite_targets(suite: unittest.TestSuite, keep_class_whole: set) -> List[str]:
    targets: List[str] = []
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            targets.extend(_collect_suite_targets(item, keep_class_whole))
        else:
            test_id = item.id()
            parts = test_id.rsplit(".", 1)
            if len(parts) == 2 and parts[0].rsplit(".", 1)[-1] in keep_class_whole:
                if parts[0] not in targets:
                    targets.append(parts[0])
            else:
                targets.append(test_id)
    return targets


def _expand_heavy_file(path: pathlib.Path) -> List[str]:
    module_name = ".".join(path.with_suffix("").parts)
    suite = unittest.defaultTestLoader.loadTestsFromName(module_name)
    return _collect_suite_targets(suite, {"TestDashboardServerLive"})


def discover_test_targets(targets: List[str]) -> List[Tuple[str, int]]:
    """Expand file/directory targets into runnable unittest target strings with priorities."""
    seen_files = set()
    files: List[pathlib.Path] = []
    for raw in targets:
        p = pathlib.Path(raw)
        if p.is_file():
            resolved = p.resolve()
            if resolved not in seen_files:
                seen_files.add(resolved)
                files.append(p)
        elif p.is_dir():
            for child in sorted(p.rglob("test_*.py")):
                resolved = child.resolve()
                if resolved not in seen_files:
                    seen_files.add(resolved)
                    files.append(child)
        else:
            raise FileNotFoundError(f"Test target not found: {raw}")

    run_items: List[Tuple[str, int, int]] = []
    for path in files:
        if path.name in HEAVY_FILES:
            for dotted in _expand_heavy_file(path):
                leaf = dotted.rsplit(".", 1)[-1]
                prio = TARGET_PRIORITY.get(leaf, 15)
                run_items.append((dotted, prio, 0))
        else:
            prio = TARGET_PRIORITY.get(path.name, 50)
            run_items.append((str(path), prio, -path.stat().st_size))

    run_items.sort(key=lambda item: (item[1], item[2], item[0]))
    return [(target, prio) for target, prio, _ in run_items]


def run_target(target: str) -> Tuple[str, int, float, str]:
    """Execute one unittest module, class, or method in an isolated subprocess."""
    start = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", target],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed = time.perf_counter() - start
    output = (proc.stdout + "\n" + proc.stderr).strip()
    return target, proc.returncode, elapsed, output


def main(argv: Optional[List[str]] = None) -> int:
    """Run discovered unittest targets in parallel and exit non-zero on failure."""
    raw_targets = argv if argv is not None and len(argv) > 0 else ["tests"]
    items = discover_test_targets(raw_targets)
    if not items:
        print("No test targets discovered.", file=sys.stderr)
        return 1

    targets = [target for target, _ in items]
    workers = min(len(targets), max(4, (os.cpu_count() or 4) + 2))
    t0 = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(run_target, targets))

    total_elapsed = time.perf_counter() - t0
    failures = [row for row in results if row[1] != 0]

    print(f"Ran {len(targets)} test targets across {workers} workers in {total_elapsed:.2f}s "
          f"(passed={len(targets) - len(failures)}, failed={len(failures)})")
    for target, _, dt, _ in sorted(results, key=lambda row: -row[2])[:8]:
        print(f"  {dt:6.2f}s  {target}")

    for target, code, _, out in failures:
        print(f"\n=== FAIL ({code}): {target} ===")
        print(out)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
