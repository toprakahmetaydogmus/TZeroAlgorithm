import concurrent.futures
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from tzero.tzero_packer import pack_python_symbols
from tzero.tzero_security import ZeroLeakEngine

path = "tzero/tzero_snapshot.py"
source = subprocess.check_output(["git", "show", f"HEAD:{path}"]).decode("utf-8")
if ZeroLeakEngine.scan_text(source):
    raise SystemExit("Tracked source flagged by secret scan. No payload sent.")
symbols = ["SnapshotEngine.get_cache_path", "SnapshotEngine.get_sqlite_path"]
packed = pack_python_symbols(source, symbols, min_reduction=95)
prompt = """Use only the supplied Python code. Do not run tools, inspect files, or edit anything.
Return exactly three letters separated by spaces. If the code doesn't answer a question, use X.
1. When get_cache_path receives a nonempty custom_path, what does it return? A) os.path.abspath(custom_path) B) custom_path unchanged C) a path under workspace_dir
2. Without custom_path, which class attribute supplies the filename in get_sqlite_path? A) SNAPSHOT_FILENAME B) CACHE_DIR C) SQLITE_FILENAME
3. Without custom_path, how is workspace_dir normalized for get_cache_path? A) os.path.abspath B) os.path.realpath C) os.path.expanduser

Python code:
"""
cli = shutil.which("agy.exe")
if not cli:
    raise SystemExit("Antigravity CLI is unavailable.")
model = "gemini-3.8-flash-low"


def run(condition, code, trial, workspace, settings):
    cmd = [cli, "--model", model, "--effort", "low", "--sandbox", "--mode", "plan",
           "--settings", str(settings), "--print-timeout", "35s", "--output-format", "json",
           "--print", prompt + code]
    proc = subprocess.run(cmd, cwd=workspace, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=50)
    if proc.returncode:
        return {"condition": condition, "trial": trial, "error": f"CLI exit {proc.returncode}"}
    reply = json.loads(proc.stdout)
    answer = " ".join(reply.get("response", "").strip().upper().split())
    return {"condition": condition, "trial": trial, "answer": answer,
            "correct": answer == "A C A", "usage": reply.get("usage"),
            "status": reply.get("status"), "seconds": reply.get("duration_seconds")}


with tempfile.TemporaryDirectory(prefix="tzero-flash-ab-") as folder:
    settings = Path(folder) / "settings.json"
    settings.write_text('{"useG1Credits": false}', encoding="utf-8")
    conditions = [("full", source), ("targeted", packed.text)]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for trial in range(1, 4):
            order = conditions if trial % 2 else conditions[::-1]
            jobs = [pool.submit(run, label, code, trial, folder, settings) for label, code in order]
            results.extend(j.result() for j in jobs)
            if any("error" in row for row in results):
                break
    report = {
        "model": model, "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"],text=True).strip(),
        "source_path": path, "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "symbols": symbols, "tokenizer": packed.encoding, "source_tokens": packed.source_tokens,
        "targeted_tokens": packed.context_tokens, "source_reduction_pct": packed.reduction_pct,
        "expected": "A C A", "ai_credit_overages": False, "trials": results,
    }
    print(json.dumps(report, indent=2))
