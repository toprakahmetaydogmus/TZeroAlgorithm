"""Run an unguided pytest diagnosis A/B with Antigravity and local T-Zero."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from scripts.benchmark_pytest_logs_cli import MODEL, SOURCE, SUITE, clean, pytest_run

REVISION = "25fed66b07ba32b4edab18af1e7446ca81a7e2f5"
TOOLS = ["search_codebase", "build_project_context"]
SERVER = "tzero_benchmark"
PROMPT = (
    "A pytest regression was reported. Diagnose it using the workspace and its "
    "pytest.log. Choose what to inspect using the available local tools. Stay inside "
    "the workspace. Do not use the internet, read environment variables, edit files, "
    "or run shell commands. Report the exact root cause, the source evidence, and "
    "the smallest fix. Do not implement the fix."
)


def prepare(repo, root):
    archive = root / "source.zip"
    fixture = root / "fixture"
    subprocess.run(
        ["git", "archive", "--format=zip", f"--output={archive}", REVISION, "tzero", "tests", "pyproject.toml"],
        cwd=repo,
        check=True,
    )
    shutil.unpack_archive(archive, fixture)
    status, _ = pytest_run(fixture, ["-q", "--tb=short"])
    if status:
        raise RuntimeError("Fixture baseline failed")
    target = fixture / SOURCE
    source = target.read_text(encoding="utf-8")
    old = "cls.CACHE_DIR, cls.SQLITE_FILENAME)"
    if source.count(old) != 1:
        raise RuntimeError("Regression could not be seeded")
    target.write_text(source.replace(old, "cls.CACHE_DIR, cls.SNAPSHOT_FILENAME)"), encoding="utf-8")
    status, log = pytest_run(fixture, ["-vv", "--tb=long", "--color=no"])
    if status != 1 or "4 failed, 22 passed" not in log:
        raise RuntimeError("Fixture did not reproduce the expected four failures")
    (fixture / "pytest.log").write_text(clean(log, fixture), encoding="utf-8")
    return fixture


def run(cli, config, fixture, workspace, settings, enabled):
    shutil.copytree(fixture, workspace, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".tzero"))
    mcp = {
        SERVER: {
            "command": sys.executable,
            "args": ["-m", "tzero.tzero_mcp", "--canonical"],
            "env": {"PYTHONPATH": str(workspace)},
            "enabledTools": TOOLS,
            "timeoutSeconds": 20,
        },
    } if enabled else {}
    temporary_config = json.dumps({"mcpServers": mcp}).encode()
    original_config = config.read_bytes() if config.exists() else None
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_bytes(temporary_config)
    try:
        listing = subprocess.check_output([cli, "mcp", "list"], cwd=workspace, encoding="utf-8")
        if bool(re.search(rf"(?m)^{SERVER}\s+stdio\s+enabled\b", listing)) != enabled:
            raise RuntimeError("Antigravity MCP configuration did not take effect")
        proc = subprocess.run(
            [cli, "--model", MODEL, "--effort", "low", "--sandbox", "--mode", "plan",
             "--settings", str(settings), "--print-timeout", "120s", "--output-format", "stream-json",
             "--print", PROMPT],
            cwd=workspace, env={**os.environ, "PYTHONPATH": str(workspace)}, stdin=subprocess.DEVNULL,
            capture_output=True, encoding="utf-8", errors="replace", timeout=135,
        )
    finally:
        if config.read_bytes() == temporary_config:
            if original_config is None:
                config.unlink()
            else:
                config.write_bytes(original_config)
    events = [json.loads(line) for line in proc.stdout.splitlines() if line.startswith("{")]
    init = next((event["init"] for event in events if "init" in event), {})
    result = next((event["result"] for event in reversed(events) if "result" in event), {})
    steps = [event.get("step_update", {}) for event in events if event.get("event") == "step_update"]
    calls = [
        {"tool": step["tool_name"], "failed": bool(step.get("tool_info", {}).get("error"))}
        for step in steps
        if step.get("state") == "DONE" and step.get("tool_name")
    ]
    return {
        "condition": "tzero_available" if enabled else "baseline",
        "status": result.get("status", "NO_RESULT"),
        "exit_code": proc.returncode,
        "usage": result.get("usage"),
        "seconds": result.get("duration_seconds"),
        "available_tools": init.get("tools", []),
        "tool_calls": calls,
        "answer": clean(result.get("response") or "", workspace),
        "error": clean((result.get("error") or proc.stderr)[-1200:] if proc.returncode else "", workspace),
    }


def benchmark(cli, args):
    config = Path.home() / ".gemini/config/mcp_config.json"
    with tempfile.TemporaryDirectory(prefix="tzero-autonomous-") as temp:
        root = Path(temp)
        fixture = prepare(Path.cwd(), root)
        settings = root / "settings.json"
        settings.write_text(json.dumps({
            "useG1Credits": False,
            "allowNonWorkspaceAccess": False,
            "permissions": {
                "allow": [f"mcp({SERVER}/*)"],
                "deny": ["command(*)", "write_file(*)", "read_url(*)", "execute_url(*)", "download_url(*)"],
            },
        }), encoding="utf-8")
        report = {"model": MODEL, "source_commit": REVISION, "prompt": PROMPT,
                  "suite": SUITE, "mcp_server": SERVER, "mcp_tools": TOOLS,
                  "ai_credit_overages": False, "trials": []}
        for trial in range(1, args.pairs + 1):
            for enabled in ((False, True) if trial % 2 else (True, False)):
                workspace = root / f"workspace-{trial}-{int(enabled)}"
                record = run(cli, config, fixture, workspace, settings, enabled)
                record["trial"] = trial
                report["trials"].append(record)
                path = args.output / "results.json"
                path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
                print(record["condition"], trial, record["status"], record["usage"], flush=True)
                if record["status"] != "SUCCESS":
                    raise RuntimeError("CLI trial failed. Check the recorded result.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--pairs", type=int, choices=(1, 2, 3), default=3)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cli = shutil.which("agy.exe")
    if not cli:
        raise RuntimeError("Antigravity CLI not found")
    lock = Path.home() / ".gemini/tzero-autonomous-benchmark.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("x", encoding="utf-8") as handle:
        handle.write(str(os.getpid()))
    try:
        plugins = json.loads(subprocess.check_output([cli, "plugin", "list", "--json"], encoding="utf-8"))
        installed_tzero = any(plugin["name"] == "tzero" and plugin["enabled"] for plugin in plugins)
        if installed_tzero:
            subprocess.run([cli, "plugin", "disable", "tzero"], check=True)
        try:
            benchmark(cli, args)
        finally:
            if installed_tzero:
                subprocess.run([cli, "plugin", "enable", "tzero"], check=True)
    finally:
        lock.unlink()


if __name__ == "__main__":
    main()
