"""Compare evidence for a pytest regression using Gemini 3.8 Flash Low."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

from tzero.tzero_packer import pack_python_symbols
from tzero.tzero_security import ZeroLeakEngine

MODEL = "gemini-3.8-flash-low"
SOURCE = Path("tzero/tzero_snapshot.py")
FOCUS_SYMBOLS = [
    "SnapshotEngine.get_cache_path",
    "SnapshotEngine.get_sqlite_path",
    "SnapshotEngine._save_snapshot",
]
SUITE = ["tests/test_snapshot_incremental.py", "tests/test_packer.py",
         "tests/test_task_benchmark.py", "tests/test_benchmark.py"]
PROMPT = """Diagnose this pytest run using only the supplied output. Do not inspect any files, use tools, or modify anything. State which test or tests failed, the root cause, and the smallest fix. If the log does not support a conclusion, say what is missing. Keep your answer under 90 words.

PYTEST OUTPUT
"""


def clean(text, checkout):
    # Logs are to be sent to a hosted model. Strip local absolute paths first.
    for path, label in ((checkout, "<repo>"), (Path(tempfile.gettempdir()), "<tmp>"),
                        (Path.home(), "<home>")):
        for variant in (str(path), path.as_posix()):
            text = re.sub(re.escape(variant), lambda _: label, text, flags=re.IGNORECASE)
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)
    if ZeroLeakEngine.scan_text(text):
        raise RuntimeError("Potential secret in pytest output. No benchmark prompt sent.")
    return text


def pytest_run(checkout, flags):
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *flags, *SUITE], cwd=checkout,
        capture_output=True, encoding="utf-8", errors="replace", timeout=120,
    )
    return proc.returncode, proc.stdout + proc.stderr


def report_failures(xml_path):
    root = ET.parse(xml_path).getroot()
    testcases = list(root.iter("testcase"))
    failures = {}
    for test in testcases:
        for tag in ("failure", "error"):
            event = test.find(tag)
            if event is not None:
                name = f"{test.get('classname')}.{test.get('name')}"
                failures[name] = (event.get("message", ""), (event.text or "").strip())
    return len(testcases), failures


def run(cli, condition, evidence, trial, workspace, settings):
    if len(PROMPT + evidence) > 25000:
        raise RuntimeError(f"{condition} exceeds the Windows CLI argument budget")
    proc = subprocess.run(
        [cli, "--model", MODEL, "--effort", "low", "--sandbox", "--mode", "plan",
         "--settings", str(settings), "--print-timeout", "45s", "--output-format",
         "json", "--print", PROMPT + evidence],
        cwd=workspace, capture_output=True, encoding="utf-8", errors="replace", timeout=60,
    )
    if proc.returncode:
        raise RuntimeError(f"{condition} trial {trial}: CLI exit {proc.returncode}")
    response = json.loads(proc.stdout)
    if response.get("status") != "SUCCESS" or not response.get("usage"):
        raise RuntimeError(f"{condition} trial {trial}: no successful usage record")
    return {"condition": condition, "trial": trial,
            "answer": response["response"].strip(), "usage": response["usage"],
            "seconds": response.get("duration_seconds")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--focused-with-source-only", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    cli = shutil.which("agy.exe")
    if not cli:
        raise RuntimeError("Antigravity CLI not found")
    repo = Path.cwd()
    revision = subprocess.check_output(
        ["git", "rev-parse", "--verify", "--end-of-options", f"{args.revision}^{{commit}}"],
        text=True,
    ).strip()
    with tempfile.TemporaryDirectory(prefix="tzero-pytest-ab-") as tmp:
        temp = Path(tmp)
        checkout = temp / "checkout"
        archive = temp / "source.zip"
        subprocess.run(["git", "archive", "--format=zip", f"--output={archive}", revision],
                       cwd=repo, check=True)
        shutil.unpack_archive(archive, checkout)
        status, _ = pytest_run(checkout, ["-q", "--tb=short"])
        if status != 0:
            raise RuntimeError("Baseline suite is not green, so the regression was not introduced")
        target = checkout / SOURCE
        source = target.read_text(encoding="utf-8")
        expression = "cls.CACHE_DIR, cls.SQLITE_FILENAME)"
        if source.count(expression) != 1:
            raise RuntimeError("Expected one SQLite path reference")
        source = source.replace(expression, "cls.CACHE_DIR, cls.SNAPSHOT_FILENAME)")
        target.write_text(source, encoding="utf-8")
        logs = {}
        run_data = {}
        for condition, flags in (("full", ["-vv", "--tb=long"]), ("short", ["-q", "--tb=short"])):
            xml = temp / f"{condition}.xml"
            status, evidence = pytest_run(checkout, [*flags, "--color=no", f"--junitxml={xml}"])
            if status != 1:
                raise RuntimeError(f"Expected test failures in the {condition} run")
            run_data[condition] = report_failures(xml)
            logs[condition] = clean(evidence, checkout)
        count, failures = run_data["short"]
        full_count, full_failures = run_data["full"]
        if not failures or count != full_count or failures.keys() != full_failures.keys():
            raise RuntimeError("Full and short pytest runs did not produce the same failures")
        logs["focused"] = clean(
            f"pytest results: {count} tests, {len(failures)} failures\n\n" + "\n\n".join(
                f"{name}\n{trace or message}" for name, (message, trace) in failures.items()
            ), checkout,
        )
        conditions = ("full", "short", "focused")
        report_name = "results.json"
        if args.focused_with_source_only:
            context = pack_python_symbols(source, FOCUS_SYMBOLS, min_reduction=0)
            logs["focused_plus_source"] = clean(
                f"{logs['focused']}\n\nRELEVANT SOURCE ({SOURCE.as_posix()})\n{context.text}",
                checkout,
            )
            conditions = ("focused_plus_source",)
            report_name = "focused-plus-source.json"
        for condition, log in logs.items():
            (output / f"{condition}.txt").write_text(log + "\n", encoding="utf-8")
        # Use an empty workspace so the CLI cannot see the test checkout.
        session = temp / "agent"
        session.mkdir()
        settings = temp / "settings.json"
        settings.write_text('{"useG1Credits": false}', encoding="utf-8")
        results = []
        with ThreadPoolExecutor(max_workers=3) as pool:
            for trial in range(1, 4):
                offset = (trial - 1) % len(conditions)
                order = conditions[offset:] + conditions[:offset]
                jobs = [pool.submit(run, cli, condition, logs[condition], trial, session, settings)
                        for condition in order]
                results.extend(job.result() for job in jobs)
        report = {"model": MODEL, "source_commit": revision, "suite": SUITE,
                  "fixture": "get_sqlite_path defaults to SNAPSHOT_FILENAME instead of SQLITE_FILENAME",
                  "test_cases": count, "failing_tests": sorted(failures),
                  "ai_credit_overages": False, "prompt": PROMPT,
                  "log_characters": {key: len(value) for key, value in logs.items()}, "trials": results}
        if args.focused_with_source_only:
            report["symbols_selected_in_advance"] = FOCUS_SYMBOLS
        (output / report_name).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
