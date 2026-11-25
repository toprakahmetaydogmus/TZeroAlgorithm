# -*- coding: utf-8 -*-
"""Zero-dependency parallel unittest runner with longest-job-first scheduling."""

import concurrent.futures
import os
import pathlib
import subprocess
import sys
import time
from typing import List, Tuple

HEAVY_FIRST = {
    "test_e2e_full.py": 0,
    "test_cli_comprehensive.py": 1,
    "test_local_ci.py": 2,
    "test_mcp.py": 3,
    "test_fixer_deep.py": 4,
    "test_dashboard.py": 5,
    "test_cli.py": 6,
    "test_tier1_feature_coverage.py": 7,
}


def discover_test_files(targets: List[str]) -> List[pathlib.Path]:
    """Expand file or directory targets into deduplicated test_*.py paths."""
    seen = set()
    files: List[pathlib.Path] = []
    for raw in targets:
        p = pathlib.Path(raw)
        if p.is_file():
            resolved = p.resolve()
            if resolved not in seen:
                seen.add(resolved)
                files.append(p)
        elif p.is_dir():
            for child in sorted(p.rglob("test_*.py")):
                resolved = child.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    files.append(child)
        else:
            raise FileNotFoundError(f"Test target not found: {raw}")

    files.sort(key=lambda item: (HEAVY_FIRST.get(item.name, 99), -item.stat().st_size, str(item)))
    return files


def run_test_file(test_file: pathlib.Path) -> Tuple[pathlib.Path, int, float, str]:
    """Execute one unittest file in an isolated Python subprocess."""
    start = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", str(test_file)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed = time.perf_counter() - start
    output = (proc.stdout + "\n" + proc.stderr).strip()
    return test_file, proc.returncode, elapsed, output


def main(argv: List[str] | None = None) -> int:
    """Run discovered unittest modules in parallel and exit non-zero on failure."""
    targets = argv if argv is not None and len(argv) > 0 else ["tests"]
    files = discover_test_files(targets)
    if not files:
        print("No test files discovered.", file=sys.stderr)
        return 1

    workers = min(len(files), max(2, os.cpu_count() or 4))
    t0 = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(run_test_file, files))

    total_elapsed = time.perf_counter() - t0
    failures = [row for row in results if row[1] != 0]

    print(f"Ran {len(files)} test modules across {workers} workers in {total_elapsed:.2f}s "
          f"(passed={len(files) - len(failures)}, failed={len(failures)})")
    for path, _, dt, _ in sorted(results, key=lambda row: -row[2])[:8]:
        print(f"  {dt:6.2f}s  {path.as_posix()}")

    for path, code, _, out in failures:
        print(f"\n=== FAIL ({code}): {path.as_posix()} ===")
        print(out)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
