#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-Zero Context Architect - Package setup without installation side effects.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Repository: https://github.com/toprakahmetaydogmus/TZeroAlgorithm
"""

import sys

VERSION = "12.3.1"

# Fast-path for --version
if len(sys.argv) > 1 and sys.argv[1] in ("--version", "-V"):
    print(VERSION)
    sys.exit(0)

from setuptools import setup  # noqa: E402


if __name__ == "__main__":
    setup(
        name="tzero-mcp",
        version=VERSION,
    )
