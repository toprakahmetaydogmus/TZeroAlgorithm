# -*- coding: utf-8 -*-
"""T-Zero Context Architect v7.3.2 - Backward Compatibility & API Wrapper.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
LinkedIn: https://linkedin.com/in/toprak-ahmet-aydo%C4%9Fmu%C5%9F-60462534b/
Bio & Socials: https://hopp.bio/siberegitim
GitHub: https://github.com/toprakahmetaydogmus/TZeroAlgorithm

Provides seamless backward compatibility for legacy invocations of `tzero.py`,
delegating directly to the V3/V4 engine and exporting core analysis tools,
Superdesign orchestrator tools, and MCP utilities.
"""

from tzero_v3 import (
    CodebaseScanner,
    TokenReducer,
    PolyglotSignatureExtractor,
    generate_offline_context,
    DependencyAnalyzer,
    StaticCodeAnalyzer,
    WorkspaceDuplicityFinder,
    ContextExportManager,
    calculate_token_cost,
    count_tokens_precise,
    launch_gui,
    main,
)
from tzero_features import (
    ChangeImpactAnalyzer,
    ArchitectureRuleEngine,
    AgentRulesGenerator,
    LocalSemanticCodeSearch,
    TokenROICalculator,
    GitDiffContextBuilder,
)

try:
    from tzero_superdesign import (
        superdesign_generate,
        superdesign_iterate,
        superdesign_extract_system,
        superdesign_list,
        superdesign_gallery,
    )
except ImportError:
    superdesign_generate = None
    superdesign_iterate = None
    superdesign_extract_system = None
    superdesign_list = None
    superdesign_gallery = None

try:
    from tzero_mcp import create_mcp_server
except ImportError:
    create_mcp_server = None

if __name__ == "__main__":
    main()
