#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-Zero Context Architect - Setup & Post-Install / Develop Hook.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Repository: https://github.com/toprakahmetaydogmus/TZeroAlgorithm
"""

from pathlib import Path
from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install


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
        cmdclass={
            "develop": PostDevelopCommand,
            "install": PostInstallCommand,
        }
    )
