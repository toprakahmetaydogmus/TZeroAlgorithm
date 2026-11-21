#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-Zero Context Architect - Setup & Post-Install / Develop Hook.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Repository: https://github.com/toprakahmetaydogmus/TZeroAlgorithm
"""

import sys
from pathlib import Path

VERSION = "12.0.0"

# Fast-path for --version
if len(sys.argv) > 1 and sys.argv[1] in ("--version", "-V"):
    print(VERSION)
    sys.exit(0)

from setuptools import setup  # noqa: E402
from setuptools.command.develop import develop  # noqa: E402
from setuptools.command.install import install  # noqa: E402


def _post_install():
    try:
        from tzero.tzero_welcome import print_star_banner, install_git_star_hooks
        print_star_banner(force=True)
        install_git_star_hooks(Path(__file__).resolve().parent)
    except Exception:
        pass


class PostDevelopCommand(develop):
    """Post-installation for development mode (pip install -e . or setup.py develop)."""
    def run(self):
        super().run()
        _post_install()


class PostInstallCommand(install):
    """Post-installation for standard install mode."""
    def run(self):
        super().run()
        _post_install()


if __name__ == "__main__":
    setup(
        name="tzero-mcp",
        version=VERSION,
        cmdclass={
            "develop": PostDevelopCommand,
            "install": PostInstallCommand,
        }
    )
