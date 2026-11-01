# -*- coding: utf-8 -*-
import os
import re

PATTERNS = [
    r"sk-[a-zA-Z0-9]{20,}",
    r"nvapi-[a-zA-Z0-9_-]{20,}",
    r"ghp_[a-zA-Z0-9]{20,}",
    r"AIza[0-9A-Za-z-_]{35}",
    r"xox[baprs]-[0-9a-zA-Z]{10,48}",
    r"(?i)api[_-]?key\s*[:=]\s*['\"][a-zA-Z0-9_-]{16,}['\"]",
    r"(?i)secret\s*[:=]\s*['\"][a-zA-Z0-9_-]{16,}['\"]",
    r"(?i)password\s*[:=]\s*['\"][a-zA-Z0-9_-]{8,}['\"]",
]

# Patterns that are allowed / test fixtures
FALSE_POSITIVES = [
    "YOUR_KEY_HERE",
    "ENTER_YOUR_KEY",
    "password_example",
    "test_password",
    "invalid passphrase or corrupted backup",
    "sha256",
    "tzero_seed_",
    "mock",
    "placeholder",
    "example",
]

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
root_dirs = [repo_root]

found = []
for rdir in root_dirs:
    for root, dirs, files in os.walk(rdir):
        if any(d in root for d in [".git", "__pycache__", ".pytest_cache", "target", "dist", "build", ".venv", "venv", ".egg-info", "node_modules", "tests"]):
            continue
        for f in files:
            if f.endswith((".py", ".rs", ".json", ".toml", ".bat", ".md", ".txt", ".html", ".js", ".css")):
                fpath = os.path.join(root, f)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                        content = fp.read()
                        for p in PATTERNS:
                            matches = re.findall(p, content)
                            filtered = [m for m in matches if not any(fp in str(m) for fp in FALSE_POSITIVES)]
                            if filtered:
                                found.append((fpath, p, filtered[:3]))
                except Exception as e:
                    pass

print(f"Total secret audit findings: {len(found)}")
for fpath, p, m in found:
    print(f"File: {fpath} | Pattern: {p} | Matches: {m}")
