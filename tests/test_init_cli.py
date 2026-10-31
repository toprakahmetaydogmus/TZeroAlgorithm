# -*- coding: utf-8 -*-
"""Unit tests for T-Zero 1-Click Init CLI (Cursor, Claude, Windsurf, VS Code)."""

import io
import sys
import unittest
from unittest.mock import patch

import addmcp
from tzero_polyglot import PolyglotTokenReducer


class TestInitCLI(unittest.TestCase):
    def test_run_init_list(self):
        """Test tzero init --list runs and lists detected targets."""
        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            code = addmcp.run_init(["--list"])
        self.assertEqual(code, 0)
        output = stdout_capture.getvalue()
        self.assertIn("T-ZERO 1-CLICK MCP INITIALIZATION", output)
        self.assertIn("Supported & Detected IDE Environments", output)
        self.assertIn("Cursor", output)
        self.assertIn("Claude Desktop", output)
        self.assertIn("Windsurf", output)

    def test_run_init_invalid_target(self):
        """Test tzero init with invalid target returns error code."""
        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            code = addmcp.run_init(["--nonexistent-ide-xyz"])
        self.assertEqual(code, 1)
        self.assertIn("No matching IDE target found", stdout_capture.getvalue())

    def test_polyglot_ts_interface_preserved(self):
        """Test TypeScript interface fields are preserved while function bodies are pruned."""
        ts_code = """
import { useState } from 'react';

export interface UserConfig {
    id: string;
    apiKey: string;
    active: boolean;
}

export const fetchUser = async (id: string): Promise<UserConfig> => {
    const res = await fetch(`/api/user/${id}`);
    const data = await res.json();
    return data;
};
"""
        reduced = PolyglotTokenReducer.reduce_javascript(ts_code)
        self.assertIn("export interface UserConfig", reduced)
        self.assertIn("id: string;", reduced)
        self.assertIn("apiKey: string;", reduced)
        self.assertIn("export const fetchUser", reduced)
        self.assertNotIn("const res = await fetch", reduced)
        self.assertNotIn("const data = await res.json()", reduced)


if __name__ == "__main__":
    unittest.main()
