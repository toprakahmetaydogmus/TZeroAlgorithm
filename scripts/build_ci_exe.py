# -*- coding: utf-8 -*-
"""Standalone compiler for TZeroCI.exe.

Compiles `tzero/tzero_ci.py` into `dist/TZeroCI.exe` with PyInstaller.
"""

import os
import sys
import time
import shutil
import hashlib
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build" / "TZeroCI"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def build_tzero_ci():
    print("⚡ [T-ZERO COMPILER] Compiling standalone TZeroCI.exe...", flush=True)
    os.makedirs(DIST_DIR, exist_ok=True)

    # Kill any running instance
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/F", "/IM", "TZeroCI.exe", "/T"], capture_output=True, text=True)
        except Exception:
            pass

    target_exe = DIST_DIR / ("TZeroCI.exe" if os.name == "nt" else "TZeroCI")
    if target_exe.exists():
        try:
            target_exe.unlink()
        except Exception:
            target_exe.rename(DIST_DIR / f"TZeroCI.exe.old_{int(time.time())}")

    icon_path = ROOT_DIR / "tzero" / "siber_akademi.ico"
    args = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--clean",
        "--noconfirm",
        "--name=TZeroCI",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        f"--specpath={ROOT_DIR / 'build' / 'specs'}",
        "--collect-all=tzero",
        "--collect-all=keyring",
        "--collect-all=requests",
        "--copy-metadata=keyring",
        "--copy-metadata=requests",
    ]
    if icon_path.exists():
        args.append(f"--icon={icon_path}")

    args.extend(["--paths=.", str(ROOT_DIR / "tzero" / "tzero_ci.py")])

    print(f"Executing: {' '.join(args)}", flush=True)
    subprocess.run(args, cwd=ROOT_DIR, check=True)

    if target_exe.exists():
        size_mb = target_exe.stat().st_size / (1024 * 1024)
        sha = compute_sha256(target_exe)
        sha_file = DIST_DIR / f"{target_exe.name}.sha256"
        sha_file.write_text(f"{sha}  {target_exe.name}\n", encoding="utf-8")
        print(f"✔ [SUCCESS] {target_exe.name} successfully created ({size_mb:.2f} MB)", flush=True)
        print(f"  SHA-256: {sha}", flush=True)
        return True
    else:
        print(f"❌ [FAILED] {target_exe.name} was not found after compilation.", flush=True)
        return False


if __name__ == "__main__":
    success = build_tzero_ci()
    sys.exit(0 if success else 1)
