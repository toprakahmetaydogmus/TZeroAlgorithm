# -*- coding: utf-8 -*-
"""Comprehensive Local Build & Packaging Pipeline for T-Zero.

Executes all builds locally on the developer machine:
1. Python Wheel & Sdist (.whl, .tar.gz)
2. Standalone Windows Executables (.exe):
   - TZeroAlgorithm.exe (Cockpit GUI)
   - TZeroCLI.exe (Console CLI)
   - TZeroMCP.exe (Fast MCP Server)
   - AddMCP.exe (1-Click Installer)
3. VS Code / Cursor Extension (.vsix)
4. Master Windows Release Bundle (.zip)
5. Cryptographic SHA-256 Checksums (.sha256)
"""

import argparse
import hashlib
import os
import pathlib
import shutil
import subprocess
import sys
import time

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "dist"


def log(msg: str):
    print(f"\033[36m⚡ [T-ZERO LOCAL BUILD]\033[0m {msg}", flush=True)


def get_project_version() -> str:
    import tomllib
    pyproject = tomllib.loads((ROOT_DIR / "pyproject.toml").read_text(encoding="utf-8"))
    return pyproject["project"]["version"]


def compute_sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def build_python_packages():
    log("Building Python Wheel and Source Distribution (.whl, .tar.gz)...")
    subprocess.run([sys.executable, "-m", "build"], cwd=ROOT_DIR, check=True)
    log("Python packages built successfully.")


def build_vscode_extension():
    log("Packaging VS Code / Cursor Extension (.vsix)...")
    vscode_dir = ROOT_DIR / "extensions" / "vscode"
    shutil.copy2(ROOT_DIR / "LICENSE", vscode_dir / "LICENSE")
    npx_cmd = shutil.which("npx") or "npx"
    subprocess.run(
        [npx_cmd, "--yes", "@vscode/vsce", "package", "--no-dependencies"],
        cwd=vscode_dir,
        check=True,
        shell=os.name == "nt"
    )
    for vsix in vscode_dir.glob("*.vsix"):
        target = DIST_DIR / vsix.name
        shutil.move(str(vsix), str(target))
        log(f"Moved extension package to: {target.name}")


def build_windows_executables():
    log("Compiling Windows Executables (TZeroAlgorithm, TZeroCLI, TZeroMCP, AddMCP)...")
    compile_script = ROOT_DIR / "scripts" / "build" / "compile.py"
    subprocess.run([sys.executable, str(compile_script)], cwd=ROOT_DIR, check=True)
    log("Windows executables built successfully.")


def generate_checksums():
    log("Generating SHA-256 checksums for all dist artifacts...")
    for item in DIST_DIR.iterdir():
        if item.is_file() and not item.name.endswith(".sha256"):
            sha = compute_sha256(item)
            sha_file = item.with_name(f"{item.name}.sha256")
            sha_file.write_text(f"{sha.lower()}  {item.name}\n", encoding="ascii")


def print_dist_summary(version: str):
    print("\n" + "=" * 78)
    print(f"🎉 T-ZERO LOCAL BUILD COMPLETE — VERSION v{version}")
    print("=" * 78)
    print(f"{'Artifact':<45} | {'Size':<10} | {'SHA-256 (first 12)':<12}")
    print("-" * 78)
    for item in sorted(DIST_DIR.iterdir()):
        if item.is_file() and not item.name.endswith(".sha256"):
            size_mb = f"{item.stat().st_size / (1024 * 1024):.2f} MB"
            sha = compute_sha256(item)
            print(f"{item.name:<45} | {size_mb:<10} | {sha[:12]}...")
    print("=" * 78 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Build T-Zero release artifacts locally.")
    parser.add_argument("--skip-exe", action="store_true", help="Skip compiling heavy Windows .exe binaries")
    parser.add_argument("--skip-vsix", action="store_true", help="Skip packaging VS Code .vsix")
    parser.add_argument("--skip-python", action="store_true", help="Skip building Python .whl/.tar.gz")
    parser.add_argument("--upload", action="store_true", help="Upload built artifacts to matching GitHub Release tag")
    args = parser.parse_args()

    os.chdir(ROOT_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    version = get_project_version()
    log(f"Starting local build pipeline for T-Zero v{version}...")

    t0 = time.time()
    if not args.skip_python:
        build_python_packages()

    if not args.skip_vsix:
        build_vscode_extension()

    if not args.skip_exe and os.name == "nt":
        build_windows_executables()

    generate_checksums()
    print_dist_summary(version)

    elapsed = time.time() - t0
    log(f"Total build time: {elapsed:.1f}s")

    if args.upload:
        tag = f"v{version}"
        log(f"Uploading artifacts to GitHub Release {tag}...")
        files = [str(p) for p in DIST_DIR.glob(f"*{version}*")]
        if files:
            subprocess.run(["gh", "release", "upload", tag] + files + ["--clobber"], check=False)
            log("Upload completed.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
