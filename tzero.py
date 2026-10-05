# -*- coding: utf-8 -*-
"""T-Zero Context Architect V3 - Backward Compatibility & API Wrapper.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Websites: https://utspro.co | https://hopp.bio/siberegitim

Provides seamless backward compatibility for legacy invocations of `tzero.py`,
delegating directly to the V3 engine and exporting core analysis tools and MCP utilities.
"""

from tzero_v3 import (
    CodebaseScanner,
    TokenReducer,
    generate_offline_context,
    DependencyAnalyzer,
    StaticCodeAnalyzer,
    WorkspaceDuplicityFinder,
    ContextExportManager,
    calculate_token_cost,
    count_tokens_precise,
    main,
)

try:
    from tzero_mcp import create_mcp_server
except ImportError:
    create_mcp_server = None

if __name__ == "__main__":
    main()
