"""Compatibility entry point for registries that launch ``tzero_mcp.py``.

The implementation lives in :mod:`tzero.tzero_mcp`; keeping this tiny wrapper
preserves older Glama and desktop-client configurations after the source-layout
cleanup.
"""

import sys


if "--version" in sys.argv[1:]:
    import pathlib
    import tomllib

    metadata = tomllib.loads(
        pathlib.Path(__file__).with_name("pyproject.toml").read_text(encoding="utf-8")
    )
    print(f"T-Zero MCP Server v{metadata['project']['version']}")
    raise SystemExit(0)

from tzero.tzero_mcp import main  # noqa: E402 - fast flags run before heavy imports


if __name__ == "__main__":
    main()
