# -*- coding: utf-8 -*-
"""Siber Akademi & T-Zero Brand Icon Generator & Asset Synchronizer.

Converts source brand assets (PNG / SVG) into high-DPI multi-resolution Windows
.ico bundles (16, 24, 32, 48, 64, 128, 256 px) with PNG-compression for modern
Windows 10/11 taskbars, Alt-Tab previews, and executable bundling.
Automatically synchronizes the base64 fallback in siber_akademi_icon.py.
"""

import argparse
import base64
import io
import os
import pathlib
import sys
from PIL import Image

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent

DEFAULT_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
SOURCE_PNG = PROJECT_ROOT / "assets" / "siber_akademi_logo.png"

TARGET_ICO_PATHS = [
    PROJECT_ROOT / "tzero" / "siber_akademi.ico",
    PROJECT_ROOT / "installers" / "npm" / "src" / "tzero" / "siber_akademi.ico",
    PROJECT_ROOT / "benchmark-site" / "favicon.ico",
]

TARGET_PYTHON_MODULES = [
    PROJECT_ROOT / "tzero" / "siber_akademi_icon.py",
    PROJECT_ROOT / "installers" / "npm" / "src" / "tzero" / "siber_akademi_icon.py",
]


def generate_ico_bytes(source_path: pathlib.Path, sizes=DEFAULT_SIZES) -> bytes:
    """Read source image and compile into multi-resolution ICO bytes."""
    with Image.open(source_path) as src:
        # Convert to RGBA for clean transparency / anti-aliasing
        img = src.convert("RGBA")

        # Create multi-size icon buffer
        buf = io.BytesIO()
        img.save(buf, format="ICO", sizes=sizes)
        return buf.getvalue()


def update_python_base64_constant(module_path: pathlib.Path, b64_str: str) -> bool:
    """Update SIBER_AKADEMI_ICO_BASE64 in the target python module."""
    if not module_path.is_file():
        return False

    content = module_path.read_text(encoding="utf-8")
    marker = 'SIBER_AKADEMI_ICO_BASE64 = "'
    if marker not in content:
        return False

    start = content.index(marker) + len(marker)
    end = content.index('"', start)

    new_content = content[:start] + b64_str + content[end:]
    if new_content != content:
        module_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Generate and synchronize Siber Akademi .ico brand assets.")
    parser.add_argument("--source", type=pathlib.Path, default=SOURCE_PNG, help="Source PNG logo file")
    parser.add_argument("--check", action="store_true", help="Check if generated .ico and base64 constants are in sync")
    args = parser.parse_args()

    if not args.source.is_file():
        print(f"[ERROR] Source image not found: {args.source}", file=sys.stderr)
        sys.exit(1)

    ico_bytes = generate_ico_bytes(args.source)
    b64_str = base64.b64encode(ico_bytes).decode("ascii")

    if args.check:
        out_of_sync = False
        for ico_path in TARGET_ICO_PATHS:
            if not ico_path.is_file() or ico_path.read_bytes() != ico_bytes:
                print(f"[OUT OF SYNC] {ico_path}")
                out_of_sync = True
            else:
                print(f"[OK] {ico_path}")

        for py_path in TARGET_PYTHON_MODULES:
            if py_path.is_file():
                content = py_path.read_text(encoding="utf-8")
                if b64_str not in content:
                    print(f"[OUT OF SYNC] {py_path} (base64 mismatch)")
                    out_of_sync = True
                else:
                    print(f"[OK] {py_path} (base64 matches)")

        sys.exit(1 if out_of_sync else 0)

    # Write target ICO files
    for ico_path in TARGET_ICO_PATHS:
        ico_path.parent.mkdir(parents=True, exist_ok=True)
        ico_path.write_bytes(ico_bytes)
        print(f"[WROTE] {ico_path} ({len(ico_bytes)} bytes, {len(DEFAULT_SIZES)} resolutions)")

    # Update Python modules
    for py_path in TARGET_PYTHON_MODULES:
        updated = update_python_base64_constant(py_path, b64_str)
        status = "UPDATED" if updated else "UP-TO-DATE"
        print(f"[{status}] {py_path}")

    print("\n[SUCCESS] Siber Akademi high-DPI icon assets successfully generated and synchronized!")


if __name__ == "__main__":
    main()
