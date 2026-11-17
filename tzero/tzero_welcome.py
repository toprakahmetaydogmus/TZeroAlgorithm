# -*- coding: utf-8 -*-
"""T-Zero Community Welcome & GitHub Star Prompt Module.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: MIT
Repository: https://github.com/toprakahmetaydogmus/TZeroAlgorithm
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional

REPO_URL = "https://github.com/toprakahmetaydogmus/TZeroAlgorithm"
VERSION = "11.15.0"
_BANNER_PRINTED = False


def find_git_root(start_dir: Optional[Path] = None) -> Optional[Path]:
    """Recursively locates .git root directory starting from start_dir or cwd."""
    curr = (start_dir or Path.cwd()).resolve()
    for p in [curr] + list(curr.parents):
        if (p / ".git").is_dir():
            return p
    return None


def get_welcome_banner(version: str = VERSION) -> str:
    """Returns the ANSI styled welcome banner asking developers to star the project."""
    return f"""\033[1;36m
┌──────────────────────────────────────────────────────────────────────────────┐
│  ⭐ WELCOME TO T-ZERO CONTEXT ARCHITECT & MCP SUITE (v{version})               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Hi! I'm Toprak Ahmet Aydoğmuş (independent engineer at Siber Akademi).      │
│  Thank you for cloning & checking out T-Zero!                                │
│                                                                              │
│  T-Zero slashes AI coding prompt tokens by 85–95% using deterministic AST    │
│  signature extraction with 100% Zero-Leak security and 20 MCP tools.         │
│                                                                              │
│  ⭐ \033[1;33mIf this saves your context window, please drop a star on GitHub:\033[1;36m        │
│     \033[1;32m👉 {REPO_URL}\033[1;36m                     │
│                                                                              │
│  💡 Quick Start:                                                             │
│     \033[1;37mtzero install-ide\033[1;36m        1-Click install into Cursor, Claude, Windsurf   │
│     \033[1;37mtzero-mcp\033[1;36m                Start local Model Context Protocol server       │
│     \033[1;37mtzero --benchmark\033[1;36m        Run multi-model token savings benchmark        │
└──────────────────────────────────────────────────────────────────────────────┘\033[0m"""


def print_star_banner(force: bool = False) -> None:
    """Prints the welcome star banner if running interactively in terminal."""
    global _BANNER_PRINTED
    if _BANNER_PRINTED and not force:
        return

    # Skip if running inside CI or user opted out
    if os.environ.get("TZERO_NO_BANNER") == "1" or os.environ.get("CI") == "true":
        return

    if not force:
        # Non-interactive stdout (pipes, subshells, captures) must remain clean
        if not sys.stdout.isatty():
            return

        argv_lower = [a.lower() for a in sys.argv[1:]]
        quiet_flags = {"--json", "--sarif", "--lsp", "--pipe", "--silent", "-q", "--quiet"}
        if any(arg in quiet_flags for arg in argv_lower):
            return
        if any(arg.startswith("--format=json") or arg.startswith("--format=sarif") for arg in argv_lower):
            return
        if "--format" in argv_lower:
            idx = argv_lower.index("--format")
            if idx + 1 < len(argv_lower) and argv_lower[idx + 1] in ("json", "sarif"):
                return

    try:
        print(get_welcome_banner())
        _BANNER_PRINTED = True
        # Silently ensure git hooks are installed if running inside repository
        install_git_star_hooks()
    except Exception:
        pass


def install_git_star_hooks(repo_dir: Optional[Path] = None) -> bool:
    """Configures repository git hooks so developers get a friendly star reminder on checkout/pull."""
    try:
        target_dir = find_git_root(repo_dir)
        if not target_dir:
            return False

        githooks_dir = target_dir / ".githooks"
        githooks_dir.mkdir(parents=True, exist_ok=True)

        hook_content = f"""#!/bin/sh
# T-Zero GitHub Star & Community Reminder
if [ -z "$TZERO_NO_BANNER" ] && [ -z "$CI" ]; then
  printf "\\n\\033[1;33m⭐ Enjoying T-Zero Context Architect?\\033[0m\\n"
  printf "\\033[1;36m👉 Please star the repository on GitHub: {REPO_URL}\\033[0m\\n\\n"
fi
exit 0
"""
        for hook_name in ("post-checkout", "post-merge"):
            hook_file = githooks_dir / hook_name
            hook_file.write_text(hook_content, encoding="utf-8")
            try:
                hook_file.chmod(0o755)
            except Exception:
                pass

        # Set core.hooksPath in git config
        subprocess.run(
            ["git", "config", "core.hooksPath", ".githooks"],
            cwd=target_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
        return True
    except Exception:
        return False


def main():
    """CLI entrypoint for scripts/welcome.py."""
    print_star_banner(force=True)
    if install_git_star_hooks():
        print("\033[32m✔ Git community hooks configured (.githooks)\033[0m")
    print(f"\033[36mFor questions or support, visit:\033[0m {REPO_URL}/discussions\n")


if __name__ == "__main__":
    main()
