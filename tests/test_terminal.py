# -*- coding: utf-8 -*-
"""Unit tests for tzero.tzero_terminal module."""

import io
import os
import unittest
from unittest.mock import MagicMock, patch

from tzero.tzero_terminal import (
    SMP_EMOJI_FALLBACKS,
    TZeroTerminalStream,
    enable_windows_vt100,
    init_terminal,
    sanitize_terminal_text,
    strip_ansi,
    supports_ansi,
    supports_emojis,
    tzero_print,
)


class TestTZeroTerminal(unittest.TestCase):
    """Verifies ANSI escape handling, Windows VT100, and SMP emoji fallback."""

    def test_strip_ansi(self):
        colored = "\033[1;36mHello \033[32mWorld\033[0m!"
        plain = strip_ansi(colored)
        self.assertEqual(plain, "Hello World!")

    def test_sanitize_terminal_text_no_ansi(self):
        text = "\033[1;33mImportant\033[0m"
        clean = sanitize_terminal_text(text, allow_ansi=False)
        self.assertEqual(clean, "Important")

    def test_sanitize_terminal_text_with_ansi(self):
        text = "\033[1;33mImportant\033[0m"
        clean = sanitize_terminal_text(text, allow_ansi=True)
        self.assertEqual(clean, text)

    def test_sanitize_terminal_text_smp_emoji_fallbacks(self):
        # When emojis are disabled (legacy CMD mode), all SMP emojis must be replaced
        raw = "👉 https://github.com 💡 Tip: 🚀 Fast 🐦 Twitter 🔴 Reddit"
        clean = sanitize_terminal_text(raw, allow_emojis=False)

        # Ensure no characters above U+FFFF remain
        smp_chars = [c for c in clean if ord(c) > 0xFFFF]
        self.assertEqual(len(smp_chars), 0)
        self.assertIn("►", clean)
        self.assertIn("•", clean)
        self.assertIn("[T-Zero]", clean)
        self.assertIn("[X]", clean)
        self.assertIn("[Reddit]", clean)

    def test_bmp_symbols_preserved(self):
        # Characters like ★ (U+2605), ✔ (U+2714), ─ (U+2500) are BMP and should not be replaced
        raw = "★ Rating: 5/5 ✔ Success ┌───┐"
        clean = sanitize_terminal_text(raw, allow_emojis=False)
        self.assertIn("★", clean)
        self.assertIn("✔", clean)
        self.assertIn("┌───┐", clean)

    def test_terminal_stream_wrapper(self):
        buf = io.StringIO()
        stream = TZeroTerminalStream(buf)
        stream.write("👉 Hello \033[1;32mGreen\033[0m")
        stream.flush()
        out = buf.getvalue()
        # Verify write succeeded
        self.assertTrue(len(out) > 0)
        self.assertEqual(stream.encoding, "utf-8")

    def test_tzero_print(self):
        buf = io.StringIO()
        tzero_print("★", "Hello", file=buf)
        self.assertIn("★ Hello", buf.getvalue())

    def test_supports_ansi_env_override(self):
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            self.assertFalse(supports_ansi())
        with patch.dict(os.environ, {"FORCE_COLOR": "1"}):
            self.assertTrue(supports_ansi())

    def test_supports_emojis_env_override(self):
        with patch.dict(os.environ, {"TZERO_NO_EMOJI": "1"}):
            self.assertFalse(supports_emojis())

    def test_enable_windows_vt100_safe(self):
        # Must not raise an exception even in mocked or headless environments
        res = enable_windows_vt100()
        self.assertIsInstance(res, bool)


if __name__ == "__main__":
    unittest.main()
