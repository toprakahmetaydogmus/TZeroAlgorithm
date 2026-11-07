# -*- coding: utf-8 -*-
"""T-Zero CLI Stdin/Stdout Pipeline & Token Streaming Compressor.

Enables UNIX pipeline integration (e.g. `cat file.py | tzero --pipe` or `git diff | tzero --pipe`)
for instant terminal token compression and optional clipboard copy.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of T-Zero Context Architect v7.0.0 Master Edition.
"""

import sys
import ast
import os
from typing import Optional

from tzero_v3 import TokenReducer


class PipeCompressor:
    """Zero-latency streaming pipe compressor for UNIX pipelines and developer CLI tooling."""

    @classmethod
    def compress_stream(cls, content: str, filename_hint: str = "", tier: str = "T-3") -> str:
        """Compresses streaming code, diff, or schema content using best AST strategy."""
        if not content or not content.strip():
            return ""

        hint = (filename_hint or "").strip()
        stripped = content.strip()

        # Map tier to mode (T-3 / T-4 -> ultra, T-2 -> light, T-1 -> full)
        mode = "ultra" if tier in ("T-3", "T-4", "ultra") else "light"

        # 1. Autodetect unified diffs
        if hint.lower().endswith((".diff", ".patch")) or stripped.startswith(("diff --git", "--- a/", "Index:")):
            reduced, _ = TokenReducer.reduce_content("stream.diff", content, mode=mode)
            return reduced

        # 2. Known filename hint routing
        if hint:
            reduced, _ = TokenReducer.reduce_content(hint, content, mode=mode)
            return reduced

        # 3. Content autodetect: try Python AST
        try:
            ast.parse(content)
            reduced, _ = TokenReducer.reduce_content("stream.py", content, mode=mode)
            return reduced
        except Exception:
            pass

        # 4. Fallback generic token reduction
        reduced, _ = TokenReducer.reduce_content("stream.txt", content, mode=mode)
        return reduced

    @classmethod
    def run_cli_pipe(cls, filename_hint: str = "", tier: str = "T-3", copy_to_clipboard: bool = False):
        """Reads stdin, compresses content, and writes to stdout / clipboard."""
        try:
            # Safe stdin reading
            if sys.stdin.isatty():
                print("[T-Zero Pipe] Waiting for input from stdin (Ctrl+Z then Enter on Windows, Ctrl+D on Unix)...", file=sys.stderr)
            raw_input = sys.stdin.read()
        except Exception as e:
            print(f"[ERROR] Failed to read from stdin: {e}", file=sys.stderr)
            sys.exit(1)

        result = cls.compress_stream(raw_input, filename_hint=filename_hint, tier=tier)

        # Output to stdout
        sys.stdout.write(result)
        sys.stdout.flush()

        # Optional clipboard copy
        if copy_to_clipboard and result:
            cls._copy_clipboard(result)

    @staticmethod
    def _copy_clipboard(text: str):
        """Copies text to system clipboard safely using platform tools."""
        try:
            if sys.platform.startswith("win"):
                import subprocess
                p = subprocess.Popen(["clip"], stdin=subprocess.PIPE, shell=True)
                p.communicate(input=text.encode("utf-8"))
            elif sys.platform == "darwin":
                import subprocess
                p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
                p.communicate(input=text.encode("utf-8"))
            elif sys.platform.startswith("linux"):
                import subprocess
                p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
                p.communicate(input=text.encode("utf-8"))
        except Exception:
            pass
