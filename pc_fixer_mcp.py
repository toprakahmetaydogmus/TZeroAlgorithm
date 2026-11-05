#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T-Zero PC-Fixer Standalone MCP Entrypoint
========================================
Command-line entrypoint to start the PC-Fixer & Codebase Doctor MCP Server.

Usage:
  python pc_fixer_mcp.py
  pc-fixer-mcp

Compatible with Claude Desktop, Cursor, Windsurf, Zed, and Antigravity IDE.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tzero_fixer.mcp_server import main

if __name__ == "__main__":
    main()

