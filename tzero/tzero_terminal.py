# -*- coding: utf-8 -*-
"""T-Zero Universal Terminal & Console Output Manager.

Ensures crystal-clear console rendering across Windows CMD (cmd.exe),
PowerShell, Windows Terminal, macOS Terminal, Linux VT100/xterm, and IDE consoles.

Key Capabilities:
1. Enables VT100 Virtual Terminal Processing (ENABLE_VIRTUAL_TERMINAL_PROCESSING)
   on Windows conhost so ANSI escape sequences render colors rather than raw '←[1;36m'.
2. Sets console code pages to UTF-8 (65001) on Windows.
3. Transparently sanitizes Supplementary Multilingual Plane (SMP) emojis
   (> U+FFFF, such as 👉, 💡, 🚀, 🐦, 🔴, etc.) into clean, beautiful BMP
   or ASCII equivalents when running in legacy Windows CMD where standard fonts
   fail to render them and show ''.
4. Strips ANSI escape sequences cleanly when stdout is redirected to a pipe/file
   or when ANSI color is not supported by the environment.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: AGPL-3.0-only
Repository: https://github.com/toprakahmetaydogmus/TZeroAlgorithm
"""

import io
import os
import re
import sys
from typing import Any, Dict, Optional, TextIO

# ANSI escape sequence regex (colors, formatting, cursor movements)
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\033\[[0-9;]*[a-zA-Z]")

# Supplementary Multilingual Plane (SMP) regex (characters above U+FFFF)
SMP_CHAR_RE = re.compile(r"[\U00010000-\U0010ffff]")

# High-fidelity replacement dictionary for SMP emojis when console cannot render them
SMP_EMOJI_FALLBACKS: Dict[str, str] = {
    # Hand pointers
    "👉": "►",
    "👈": "◄",
    "👆": "▲",
    "👇": "▼",
    "👋": "*",
    # Icons & Indicators
    "💡": "•",
    "🚀": "[T-Zero]",
    "⭐": "★",
    "🌟": "★",
    "🎉": "★",
    "✨": "*",
    "🔥": "*",
    "⚡": "*",
    "🎯": "[Target]",
    "📊": "[Stats]",
    "📈": "[+]",
    "📉": "[-]",
    "📁": "[Dir]",
    "📂": "[Dir]",
    "📄": "[Doc]",
    "📝": "[Note]",
    "📋": "[List]",
    "📌": "[Pin]",
    "📚": "[Docs]",
    "💾": "[Save]",
    "🔒": "[Lock]",
    "🛡": "[Shield]",
    "🚨": "[Alert]",
    "💉": "[Fix]",
    "🩺": "[Doctor]",
    "🩹": "[Patch]",
    "🤖": "[AI]",
    "🏆": "[Top]",
    "🔍": "[Search]",
    "🔧": "[Tool]",
    "🛠": "[Tools]",
    "📦": "[Pkg]",
    "🌐": "[Web]",
    "🏛": "[Arch]",
    "🐝": "[Swarm]",
    "👑": "[Master]",
    "💸": "[$]",
    "💰": "[$]",
    "🏦": "[Bank]",
    "🧬": "[AST]",
    "🧠": "[Brain]",
    "🕒": "[Time]",
    "🚪": "[Exit]",
    "🍎": "[Apple]",
    "🐍": "[Py]",
    "🐹": "[Go]",
    "🌙": "[Night]",
    "🏠": "[Home]",
    "🏢": "[Work]",
    "🏥": "[Health]",
    "🎨": "[Art]",
    "🎬": "[Media]",
    "🎥": "[Video]",
    "📢": "[Notice]",
    "🔁": "[Loop]",
    "🔗": "[Link]",
    "💥": "[!]",
    "🧩": "[Module]",
    "🔌": "[Plugin]",
    "🧹": "[Clean]",
    "🗡": "[Test]",
    # Social Platforms
    "🐦": "[X]",
    "🔴": "[Reddit]",
    "🟠": "[HN]",
    "💼": "[LinkedIn]",
    "💬": "[WhatsApp]",
    # Color indicators
    "🟢": "(+)",
    "🟡": "(!)",
    "🔵": "(i)",
    "🟣": "(*)",
    "🔷": "[*]",
    "🟨": "[!]",
}

_INITIALIZED = False
_VT100_ENABLED = False


def enable_windows_vt100() -> bool:
    """Enables Virtual Terminal Processing (VT100) on Windows console handles."""
    global _VT100_ENABLED
    if not sys.platform.startswith("win"):
        _VT100_ENABLED = True
        return True

    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32

        # 1. Enable on standard output and error handles
        # STD_OUTPUT_HANDLE = -11, STD_ERROR_HANDLE = -12
        for handle_id in (-11, -12):
            h = kernel32.GetStdHandle(handle_id)
            if h and h != -1:
                mode = ctypes.c_ulong()
                if kernel32.GetConsoleMode(h, ctypes.byref(mode)):
                    # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
                    # DISABLE_NEWLINE_AUTO_RETURN = 0x0008
                    kernel32.SetConsoleMode(h, mode.value | 0x0004 | 0x0008)
                    _VT100_ENABLED = True

        # 2. Also attempt directly on CONOUT$ (works even when stdout is redirected)
        try:
            GENERIC_READ = 0x80000000
            GENERIC_WRITE = 0x40000000
            FILE_SHARE_READ = 1
            FILE_SHARE_WRITE = 2
            OPEN_EXISTING = 3
            h_con = kernel32.CreateFileW(
                "CONOUT$",
                GENERIC_READ | GENERIC_WRITE,
                FILE_SHARE_READ | FILE_SHARE_WRITE,
                None,
                OPEN_EXISTING,
                0,
                0,
            )
            if h_con != -1 and h_con != 0:
                mode = ctypes.c_ulong()
                if kernel32.GetConsoleMode(h_con, ctypes.byref(mode)):
                    kernel32.SetConsoleMode(h_con, mode.value | 0x0004 | 0x0008)
                    _VT100_ENABLED = True
                kernel32.CloseHandle(h_con)
        except Exception:
            pass

        # 3. Set Windows Console CodePage to UTF-8 (65001)
        try:
            kernel32.SetConsoleOutputCP(65001)
            kernel32.SetConsoleCP(65001)
        except Exception:
            pass

        return _VT100_ENABLED
    except Exception:
        return False


def supports_ansi(stream: Optional[TextIO] = None) -> bool:
    """Determines whether the given stream supports ANSI escape sequences."""
    target_stream = stream or sys.stdout

    # Honor NO_COLOR standard (https://no-color.org)
    if os.environ.get("NO_COLOR") is not None:
        return False

    # Force color if explicitly requested
    if os.environ.get("FORCE_COLOR") in ("1", "true", "TRUE"):
        return True

    # If stdout is redirected / pipe, disable ANSI by default unless forced
    is_tty = hasattr(target_stream, "isatty") and target_stream.isatty()
    if not is_tty:
        return False

    if sys.platform.startswith("win"):
        # Check for modern Windows terminals
        if os.environ.get("WT_SESSION") or os.environ.get("VSCODE_PID"):
            return True
        if os.environ.get("TERM_PROGRAM") in ("vscode", "hyper", "warp", "mintty"):
            return True
        if os.environ.get("ConEmuANSI") == "ON" or "ANSICON" in os.environ:
            return True
        return _VT100_ENABLED

    # Unix / Linux / macOS
    term = os.environ.get("TERM", "")
    if term == "dumb":
        return False
    return True


def supports_emojis() -> bool:
    """Determines whether the active terminal can properly render SMP 4-byte emojis."""
    if os.environ.get("TZERO_NO_EMOJI") in ("1", "true", "TRUE"):
        return False

    if sys.platform.startswith("win"):
        # Windows Terminal, VS Code, Hyper, ConEmu have full SMP font fallbacks
        if os.environ.get("WT_SESSION") or os.environ.get("VSCODE_PID"):
            return True
        if os.environ.get("TERM_PROGRAM") in ("vscode", "hyper", "warp", "mintty"):
            return True
        if os.environ.get("ConEmuANSI") == "ON":
            return True
        # Classic Windows cmd.exe / powershell.exe with standard fonts fails on SMP emojis
        return False

    # Unix/macOS: terminal encoding UTF-8 usually renders emojis fine
    return True


def strip_ansi(text: str) -> str:
    """Removes all ANSI escape codes from string."""
    return ANSI_ESCAPE_RE.sub("", text)


def sanitize_terminal_text(
    text: str,
    allow_ansi: Optional[bool] = None,
    allow_emojis: Optional[bool] = None,
) -> str:
    """Formats text for terminal display, falling back gracefully where unsupported."""
    if not isinstance(text, str):
        text = str(text)

    check_ansi = supports_ansi() if allow_ansi is None else allow_ansi
    if not check_ansi:
        text = strip_ansi(text)

    check_emojis = supports_emojis() if allow_emojis is None else allow_emojis
    if not check_emojis:
        # Replace known SMP emojis with clean BMP / ASCII representations
        for emoji_char, fallback in SMP_EMOJI_FALLBACKS.items():
            if emoji_char in text:
                text = text.replace(emoji_char, fallback)
        # Fall back any remaining SMP characters (above U+FFFF) to a clean bullet
        text = SMP_CHAR_RE.sub("•", text)

    return text


class TZeroTerminalStream(io.TextIOBase):
    """Transparent TextIO proxy that filters ANSI sequences and SMP emojis on the fly."""

    def __init__(self, wrapped_stream: TextIO, is_stderr: bool = False):
        self._stream = wrapped_stream
        self._is_stderr = is_stderr

    def write(self, s: Any) -> int:
        if not isinstance(s, str):
            s = str(s)
        clean_s = sanitize_terminal_text(s)
        try:
            return self._stream.write(clean_s)
        except UnicodeEncodeError:
            # Absolute fallback: encode with ascii replace
            safe_ascii = clean_s.encode("ascii", errors="replace").decode("ascii")
            return self._stream.write(safe_ascii)

    def flush(self) -> None:
        try:
            self._stream.flush()
        except Exception:
            pass

    def isatty(self) -> bool:
        return hasattr(self._stream, "isatty") and self._stream.isatty()

    def fileno(self) -> int:
        return self._stream.fileno()

    @property
    def encoding(self) -> str:
        return getattr(self._stream, "encoding", "utf-8") or "utf-8"

    @property
    def errors(self) -> str:
        return getattr(self._stream, "errors", "replace") or "replace"

    @property
    def buffer(self) -> Any:
        return getattr(self._stream, "buffer", self._stream)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._stream, name)


def init_terminal(wrap_streams: bool = True) -> None:
    """Initializes Windows VT100 mode and installs transparent terminal stream wrappers."""
    global _INITIALIZED
    if _INITIALIZED:
        return

    # Enable Windows VT100 Virtual Terminal Processing
    if sys.platform.startswith("win"):
        enable_windows_vt100()

    # Reconfigure stdout/stderr with utf-8 if available
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # Wrap sys.stdout and sys.stderr with TZeroTerminalStream if requested
    if wrap_streams:
        # Check if running as JSON-RPC MCP server: don't alter stdout in MCP mode!
        is_mcp = (
            any("mcp" in a.lower() for a in sys.argv)
            or os.environ.get("TZERO_MCP_ACTIVE") == "1"
        )
        if not is_mcp:
            if sys.stdout and not isinstance(sys.stdout, TZeroTerminalStream):
                sys.stdout = TZeroTerminalStream(sys.stdout, is_stderr=False)  # type: ignore
            if sys.stderr and not isinstance(sys.stderr, TZeroTerminalStream):
                sys.stderr = TZeroTerminalStream(sys.stderr, is_stderr=True)  # type: ignore

    _INITIALIZED = True


def tzero_print(*args: Any, **kwargs: Any) -> None:
    """Safe print helper that automatically formats text for the current terminal."""
    file = kwargs.get("file", sys.stdout)
    sep = kwargs.get("sep", " ")
    end = kwargs.get("end", "\n")

    text = sep.join(str(a) for a in args)
    formatted = sanitize_terminal_text(text)
    file.write(formatted + end)
    file.flush()


# Auto-initialize terminal capabilities on module load
init_terminal(wrap_streams=True)
