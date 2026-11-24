# -*- coding: utf-8 -*-
"""PyPI Distribution Publisher for Anti-REA.

Validates and uploads anti-rea wheel and source distributions to PyPI using twine.

Usage:
  python scripts/publish_anti_rea.py --check
  python scripts/publish_anti_rea.py --token <pypi-token>
"""

import argparse
import os
import pathlib
import subprocess
import sys

PACKAGE_DIR = pathlib.Path(__file__).resolve().parent.parent / "packages" / "anti_rea"
DIST_DIR = PACKAGE_DIR / "dist"


def main():
    parser = argparse.ArgumentParser(description="Publish anti-rea to PyPI.")
    parser.add_argument("--check", action="store_true", help="Run twine check on built artifacts")
    parser.add_argument("--token", help="PyPI API token (pypi-...)")
    parser.add_argument("--test", action="store_true", help="Upload to TestPyPI instead of production PyPI")
    args = parser.parse_args()

    files = list(DIST_DIR.glob("anti_rea-4.1.0*"))
    if not files:
        print("[!] No built artifacts found in packages/anti_rea/dist/.")
        print("[*] Building now...")
        subprocess.run([sys.executable, "-m", "build", str(PACKAGE_DIR)], check=True)
        files = list(DIST_DIR.glob("anti_rea-4.1.0*"))

    print(f"[*] Found {len(files)} artifact(s):")
    for f in files:
        print(f"    - {f.name} ({f.stat().st_size / 1024:.1f} KB)")

    print("[*] Running twine check...")
    check_cmd = [sys.executable, "-m", "twine", "check"] + [str(f) for f in files]
    res = subprocess.run(check_cmd)
    if res.returncode != 0:
        print("[!] Twine check failed.")
        return 1

    print("[+] Twine check PASSED. Artifacts are valid for PyPI!")

    if args.check:
        print("[+] Check only requested. To upload, provide --token or set TWINE_PASSWORD.")
        return 0

    token = args.token or os.environ.get("TWINE_PASSWORD") or os.environ.get("PYPI_API_TOKEN")
    if not token:
        print("\n[i] To publish to PyPI, run:")
        print("    python scripts/publish_anti_rea.py --token pypi-AgEIcHlwaS5vcmc...")
        return 0

    upload_cmd = [
        sys.executable,
        "-m",
        "twine",
        "upload",
        "--username",
        "__token__",
        "--password",
        token,
    ]
    if args.test:
        upload_cmd += ["--repository", "testpypi"]
    upload_cmd += [str(f) for f in files]

    print("[*] Uploading to PyPI...")
    return subprocess.run(upload_cmd).returncode


if __name__ == "__main__":
    sys.exit(main())
