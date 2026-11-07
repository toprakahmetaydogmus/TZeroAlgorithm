# -*- coding: utf-8 -*-
"""T-Zero Context Architect V4 - Startup Wrapper.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
LinkedIn: https://linkedin.com/in/toprak-ahmet-aydo%C4%9Fmu%C5%9F-60462534b/
Bio & Socials: https://hopp.bio/siberegitim
GitHub: https://github.com/toprakahmetaydogmus/TZeroAlgorithm

Points to unified single-file layout: tzero_v3.py
"""

import os
import sys
import multiprocessing


def _setup_windows_streams():
    """Ensure standard streams are connected or safely redirected on Windows."""
    if sys.platform.startswith("win"):
        if len(sys.argv) > 1:
            try:
                import ctypes
                if ctypes.windll.kernel32.AttachConsole(-1):
                    try:
                        sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
                    except Exception:
                        pass
                    try:
                        sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")
                    except Exception:
                        pass
                    try:
                        sys.stdin = open("CONIN$", "r", encoding="utf-8", errors="replace")
                    except Exception:
                        pass
            except Exception:
                pass
        if sys.stdout is None:
            try:
                sys.stdout = open(os.devnull, "w", encoding="utf-8", errors="replace")
            except Exception:
                import io
                sys.stdout = io.StringIO()
        if sys.stderr is None:
            try:
                import os
                sys.stderr = open(os.devnull, "w", encoding="utf-8", errors="replace")
            except Exception:
                import io
                sys.stderr = io.StringIO()


_setup_windows_streams()

from tzero_v3 import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()

