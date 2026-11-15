# -*- coding: utf-8 -*-
"""T-Zero MCP Installer Bridge Module.

Exposes addmcp functionality within the tzero package namespace.
"""

import sys
from pathlib import Path

try:
    from addmcp import *
    from addmcp import run_cli, run_init, build_client_targets, install_targets
except ImportError:
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from addmcp import *
    from addmcp import run_cli, run_init, build_client_targets, install_targets
