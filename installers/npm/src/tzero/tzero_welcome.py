# -*- coding: utf-8 -*-
"""T-Zero Community Welcome & GitHub Star Prompt Module.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: AGPL-3.0-only
Repository: https://github.com/toprakahmetaydogmus/TZeroAlgorithm
"""

import argparse
import os
import subprocess
import sys
import warnings
from pathlib import Path
from typing import Optional

try:
    from tzero.tzero_terminal import (
        init_terminal,
        sanitize_terminal_text,
        supports_ansi,
    )
except ImportError:
    try:
        from tzero_terminal import (
            init_terminal,
            sanitize_terminal_text,
            supports_ansi,
        )
    except ImportError:
        def init_terminal(*args, **kwargs):
            pass

        def sanitize_terminal_text(text, *args, **kwargs):
            return text

        def supports_ansi(*args, **kwargs):
            return False

REPO_URL = "https://github.com/toprakahmetaydogmus/TZeroAlgorithm"
VERSION = "12.2.2"
_BANNER_PRINTED = False


def find_git_root(start_dir: Optional[Path] = None) -> Optional[Path]:
    """Recursively locates .git root directory starting from start_dir or cwd."""
    curr = (start_dir or Path.cwd()).resolve()
    for p in [curr] + list(curr.parents):
        if (p / ".git").exists():
            return p
    return None


def get_welcome_banner(version: str = VERSION) -> str:
    """Returns the ANSI styled welcome banner asking developers to star the project."""
    try:
        from tzero.tzero_growth import get_cached_community_stats
        stats = get_cached_community_stats()
    except Exception:
        stats = {"stars": 111, "target_stars": 250, "downloads_label": "22,900+"}
    stars = stats["stars"]
    target = stats["target_stars"]
    dl_label = stats["downloads_label"]
    raw_banner = f"""\033[1;36m
┌──────────────────────────────────────────────────────────────────────────────┐
│  ★ WELCOME TO T-ZERO CONTEXT ARCHITECT & MCP SUITE (v{version})               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Hi! I'm Toprak Ahmet Aydoğmuş (independent engineer at Siber Akademi).      │
│  T-Zero has reached \033[1;32m{dl_label} downloads\033[1;36m across PyPI & npm!                   │
│                                                                              │
│  T-Zero slashes AI coding prompt tokens by 85–95% using deterministic AST    │
│  signature extraction with 100% Zero-Leak security and 21 MCP tools.         │
│                                                                              │
│  ★ \033[1;33mHELP US REACH OUR {target} STARS GOAL (Current: {stars}/{target}):\033[1;36m                     │
│     \033[1;32m► Run 'tzero star' or visit: {REPO_URL}\033[1;36m       │
│                                                                              │
│  💖 \033[1;35mSPONSOR & KEEP T-ZERO 100% FREE:\033[1;36m                                     │
│     \033[1;32m► https://github.com/sponsors/toprakahmetaydogmus\033[1;36m                     │
│                                                                              │
│  • Quick Commands:                                                           │
│     \033[1;37mtzero star\033[1;36m               1-Click open GitHub & star the project          │
│     \033[1;37mtzero install-ide\033[1;36m        1-Click install into Cursor, Claude, Windsurf   │
│     \033[1;37mtzero-mcp\033[1;36m                Start local Model Context Protocol server       │
│     \033[1;37mtzero roi\033[1;36m                View live token & dollar ($) savings dashboard  │
└──────────────────────────────────────────────────────────────────────────────┘\033[0m"""
    return sanitize_terminal_text(raw_banner)


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
        init_terminal()
        print(get_welcome_banner())
        _BANNER_PRINTED = True
        # On first interactive terminal run, open GitHub repository to encourage star
        check_first_launch_repo_open()
    except Exception:
        pass


def check_first_launch_repo_open(force_open: bool = False, state_path: Optional[Path] = None) -> bool:
    """On first interactive launch, opens the GitHub repository in browser and prompts to star."""
    state_file = state_path or (Path.home() / ".tzero" / "welcome_state.json")
    try:
        if state_file.is_file() and not force_open:
            import json
            data = json.loads(state_file.read_text(encoding="utf-8"))
            if data.get("first_launch_repo_opened_v12"):
                return False

        if not force_open:
            if not sys.stdout.isatty():
                return False
            if os.environ.get("CI") == "true" or os.environ.get("TZERO_NO_BANNER") == "1":
                return False

        import webbrowser
        webbrowser.open(REPO_URL)

        state_file.parent.mkdir(parents=True, exist_ok=True)
        import json
        state_file.write_text(json.dumps({"first_launch_repo_opened_v12": True}), encoding="utf-8")
        return True
    except Exception:
        return False


def install_git_star_hooks(repo_dir: Optional[Path] = None) -> bool:
    """Install reminders only when explicitly called; never change Git configuration.

    Refuse configured hook managers and existing active hooks. The default Git
    hooks directory also works for linked worktrees; no core.hooksPath is needed.
    """
    created = []
    try:
        target_dir = find_git_root(repo_dir)
        if not target_dir:
            raise ValueError("not inside a Git repository")

        configured = subprocess.run(
            ["git", "config", "--get", "core.hooksPath"], cwd=target_dir,
            capture_output=True, text=True, check=False,
        )
        if configured.returncode == 0:
            raise ValueError("core.hooksPath is already configured; existing hooks preserved")
        if configured.returncode != 1:
            raise ValueError("could not read Git hook configuration")

        result = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-path", "hooks"],
            cwd=target_dir, capture_output=True, text=True, check=True,
        )
        githooks_dir = Path(result.stdout.strip())
        if not githooks_dir.is_absolute():
            raise ValueError("Git did not return an absolute hooks directory")
        if githooks_dir.exists() and any(
            not entry.name.endswith(".sample") for entry in githooks_dir.iterdir()
        ):
            raise ValueError("existing Git hooks found; no hooks were changed")
        githooks_dir.mkdir(parents=True, exist_ok=True)

        hook_content = f"""#!/bin/sh
# T-Zero GitHub Star & Community Reminder
if [ -z "$TZERO_NO_BANNER" ] && [ -z "$CI" ]; then
  printf "\\n\\033[1;33m★ Enjoying T-Zero Context Architect?\\033[0m\\n"
  printf "\\033[1;36m► Please star the repository on GitHub: {REPO_URL}\\033[0m\\n\\n"
fi
exit 0
"""
        for hook_name in ("post-checkout", "post-merge"):
            hook_file = githooks_dir / hook_name
            # Exclusive creation also protects hooks created after the checks above.
            with hook_file.open("x", encoding="utf-8", newline="\n") as stream:
                created.append(hook_file)
                stream.write(hook_content)
            hook_file.chmod(0o755)
        return True
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        for hook_file in created:
            hook_file.unlink(missing_ok=True)
        warnings.warn(f"Star reminder hooks were not installed: {exc}", stacklevel=2)
        return False


def main(argv=None) -> int:
    """CLI entrypoint for scripts/welcome.py."""
    parser = argparse.ArgumentParser(description="T-Zero community welcome")
    parser.add_argument(
        "--install-star-hooks", action="store_true",
        help="Explicitly install star reminders in an unused default Git hooks directory",
    )
    args = parser.parse_args(argv)
    init_terminal()
    print_star_banner(force=True)
    if args.install_star_hooks:
        if not install_git_star_hooks():
            return 1
        print(sanitize_terminal_text("\033[32m✔ Git community hooks installed\033[0m"))
    info_text = f"\033[36mFor questions or support, visit:\033[0m {REPO_URL}/discussions\n"
    print(sanitize_terminal_text(info_text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
