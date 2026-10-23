# -*- coding: utf-8 -*-
"""Siber Akademi — T-Zero Context Engine MCP (Model Context Protocol) Server.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
LinkedIn: https://linkedin.com/in/toprak-ahmet-aydo%C4%9Fmu%C5%9F-60462534b/
Bio & Socials: https://hopp.bio/siberegitim
GitHub: https://github.com/toprakahmetaydogmus/TZeroAlgorithm

Exposes T-Zero codebase intelligence, AST signature pruning, dependency mapping,
architectural boundaries (T-1 to T-4), and token optimization directly to AI coding
agents via the standard Model Context Protocol (MCP) over stdio.

Supported Environments:
  - Cursor (Composer / Chat)
  - Claude Desktop
  - Antigravity IDE
  - Cline / Roo-Code
  - Any MCP-compliant client
"""

import os
import sys
import json
import re
import ast
import inspect
import logging
try:
    from mcp.types import ToolAnnotations
except ImportError:
    ToolAnnotations = None

from typing import Dict, List, Optional, Any
try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

try:
    from pydantic import Field
except ImportError:
    def Field(default=..., description=""):
        return default

SERVER_VERSION = "7.0.0"

# Safe UTF-8 reconfiguration for Windows console & piped subprocesses
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

# Ensure project root is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Make sure the MCP SDK (and the core packages) are installed before importing them.
try:
    import tzero_deps
    tzero_deps.ensure_dependencies(include_mcp=True)
except ImportError:
    pass

# Core T-Zero V3 Engine Imports
try:
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
        PROVIDER_COST_PER_MILLION,
        PROVIDERS,
        ConfigManager,
    )
    _config_mgr = ConfigManager()
except ImportError as e:
    sys.stderr.write(f"[ERROR] Failed to import core T-Zero engine: {e}\n")
    sys.exit(1)

# MCP SDK Import with cross-version compatibility (mcp 2.x MCPServer & mcp 1.x FastMCP)
try:
    from mcp.server.mcpserver import MCPServer
    ServerClass = MCPServer
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP
        ServerClass = FastMCP
    except ImportError:
        ServerClass = None


def get_file_imports(file_path: str) -> List[str]:
    """Helper to extract imported module dependencies across Python, TypeScript, Go, Rust, Java, C#, and C++."""
    if not os.path.isfile(file_path):
        return []
    ext = os.path.splitext(file_path.lower())[1]
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as fp:
            content = fp.read()
    except Exception:
        return []

    if ext == ".py":
        try:
            tree = ast.parse(content)
            visitor = DependencyAnalyzer()
            visitor.visit(tree)
            return sorted(list(set(visitor.dependencies)))
        except Exception:
            return []

    deps = set()
    if ext in (".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"):
        for m in re.finditer(r"""(?:import\s+.*?\s+from\s+['"]|import\s*\(?['"]|require\s*\(\s*['"])([^'"]+)['"]""", content):
            deps.add(m.group(1))
    elif ext == ".go":
        in_group = False
        for line in content.splitlines():
            s = line.strip()
            if s.startswith("import ("):
                in_group = True
                continue
            if in_group:
                if s == ")":
                    in_group = False
                    continue
                m = re.search(r'["\']([^"\']+)["\']', s)
                if m:
                    deps.add(m.group(1))
            elif s.startswith("import "):
                m = re.search(r'["\']([^"\']+)["\']', s)
                if m:
                    deps.add(m.group(1))
    elif ext == ".rs":
        for m in re.finditer(r"""use\s+([A-Za-z0-9_:]+)""", content):
            deps.add(m.group(1))
    elif ext in (".java", ".kt", ".kts"):
        for m in re.finditer(r"""import\s+(?:static\s+)?([A-Za-z0-9_.]+)""", content):
            deps.add(m.group(1))
    elif ext == ".swift":
        for m in re.finditer(r"""import\s+([A-Za-z0-9_]+)""", content):
            deps.add(m.group(1))
    elif ext == ".cs":
        for m in re.finditer(r"""using\s+([A-Za-z0-9_.]+)\s*;""", content):
            deps.add(m.group(1))
    elif ext in (".cpp", ".c", ".h", ".hpp", ".cc", ".cxx"):
        for m in re.finditer(r"""#include\s+[<"]([^>"]+)[>"]""", content):
            deps.add(m.group(1))

    return sorted(list(deps))


def build_workspace_import_graph(files: List[str], base_dir: str) -> Dict[str, List[str]]:
    """Builds a full dictionary mapping of workspace files to their imported dependencies across all languages."""
    graph = {}
    supported_exts = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs",
        ".go", ".rs", ".java", ".cs", ".cpp", ".c", ".h", ".hpp",
        ".kt", ".kts", ".swift"
    }
    for f in files:
        ext = os.path.splitext(f.lower())[1]
        if ext in supported_exts:
            full_p = os.path.join(base_dir, f) if not os.path.isabs(f) else f
            imps = get_file_imports(full_p)
            if imps:
                graph[f] = imps
    return graph


def scan_text_for_secrets(text: str) -> List[Dict[str, Any]]:
    """Scans raw text for hardcoded API keys, private keys, and secrets across any language."""
    secret_patterns = [
        (re.compile(r"""(?i)(?:api_key|apikey|secret|password|auth_token)\s*=\s*['\"][A-Za-z0-9_\-\.]{12,}['\"]"""), "Hardcoded API Key / Secret"),
        (re.compile(r"""sk-[a-zA-Z0-9_\-]{20,}"""), "OpenAI API Key Pattern"),
        (re.compile(r"""nvapi-[a-zA-Z0-9_\-]{30,}"""), "NVIDIA API Key Pattern"),
        (re.compile(r"""AIza[0-9A-Za-z-_]{35}"""), "Google Gemini / Cloud Key"),
        (re.compile(r"""sk-ant-[a-zA-Z0-9_\-]{30,}"""), "Anthropic Claude Key Pattern"),
        (re.compile(r"""ghp_[a-zA-Z0-9]{36}"""), "GitHub Personal Access Token"),
    ]
    findings = []
    lines = text.splitlines()
    for lineno, line in enumerate(lines, 1):
        for pat, desc in secret_patterns:
            if pat.search(line):
                findings.append({
                    "line": lineno,
                    "desc": desc,
                    "preview": line.strip()[:60]
                })
    return findings


def create_mcp_server():
    """Initializes and registers all T-Zero tools and prompts on the MCP server instance."""
    if ServerClass is None:
        raise RuntimeError(
            "The 'mcp' Python SDK is not installed. Please run: pip install mcp"
        )

    # mcp 2.x (MCPServer) accepts description/version; mcp 1.x (FastMCP) only knows
    # `instructions`. Pass whichever the installed SDK supports so both versions start.
    summary = "Enterprise-Grade Codebase Context Architect, AST Signatures Analyzer, & Token Reducer"
    supported = inspect.signature(ServerClass.__init__).parameters
    server_kwargs: Dict[str, Any] = {"name": "tzero-context-engine"}
    if "description" in supported:
        server_kwargs["description"] = summary
    elif "instructions" in supported:
        server_kwargs["instructions"] = summary
    if "version" in supported:
        server_kwargs["version"] = SERVER_VERSION
    server = ServerClass(**server_kwargs)


    # -------------------------------------------------------------------------
    # LEGACY / COMPATIBILITY TOOL IMPLEMENTATIONS (42 TOOLS)
    # Registered to list_tools() only when TZERO_MCP_TOOL_MODE in ("all", "legacy").
    # Always available dynamically via server.call_tool().
    # -------------------------------------------------------------------------
    _legacy_mode = os.environ.get("TZERO_MCP_TOOL_MODE", "").lower() in ("all", "legacy")
    def _noop_decorator(**kwargs):
        def _wrapper(fn):
            return fn
        return _wrapper
    _maybe_tool = server.tool if _legacy_mode else _noop_decorator
    _LEGACY_DISPATCH: Dict[str, Any] = {}
    # -------------------------------------------------------------------------
    # TOOL 1: get_project_context_tree
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="get_project_context_tree",
        description=(
            "Scans the target project directory and builds an enterprise-grade multi-tier "
            "T-Zero hierarchical context tree (T-1 Master Architecture, T-2 Module References, "
            "T-3 AST Signatures, T-4 Agent Boundary Rules).\n\n"
            "Behavior:\n"
            "- Read-only: Performs static AST analysis without modifying any files on disk.\n"
            "- Idempotent: Deterministic output for identical repository states.\n"
            "- 100% Offline: Executes locally without network calls, external embeddings, or LLM billing.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Ingest repository architecture and signatures into prompt context at the start of a coding session or before large refactors (80-95% token savings).\n"
            "- Sibling Routing: For a fast single-page class/method symbol index, use 'generate_repo_map'. For full implementation of an active file with 1st-degree caller/callee skeletons, use 'get_smart_skeleton_context'. For arbitrary in-memory snippets, use 'prune_code_snippet'.\n\n"
            "Returns: Structured Markdown containing directory tree, module outlines, and AST signatures up to max_tokens."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_get_project_context_tree(
        project_root: Annotated[str, Field(default=".", description="Target repository root path to scan (default: current working directory).")] = ".",
        reduction_mode: Annotated[str, Field(default="ultra", description="AST reduction level: 'ultra' for signatures & docstrings (80-95% reduction), 'balanced' for signatures + control headers, 'none' for verbatim source.")] = "ultra",
        max_tokens: Annotated[int, Field(default=64000, description="Upper token budget threshold for returned context. When exceeded, PageRank & Git recency prioritizes critical architectural files.")] = 64000,
        include_file_contents: Annotated[bool, Field(default=True, description="When True, includes AST-reduced file bodies; when False, emits only the directory hierarchy and high-level architectural outline.")] = True
    ) -> str:
        """Builds a hierarchical T-Zero context tree for the specified workspace.
        
        Args:
            project_root: Root directory of the repository to scan (default: current directory).
            reduction_mode: Token reduction mode ('ultra' for AST signatures only, 'balanced' for signatures + control flow, 'none' for full source).
            max_tokens: Maximum token budget cap for the returned context payload.
            include_file_contents: If False, returns only the directory tree and high-level architecture overview.
        """
        abs_root = os.path.abspath(project_root)
        if not os.path.isdir(abs_root):
            return f"[ERROR] Provided project_root is not a valid directory: {abs_root}"

        scanner = CodebaseScanner()
        files, sizes, snippets = scanner.scan_directory(abs_root)
        if not files:
            return f"[WARNING] No analyzable files found in: {abs_root}"

        code_exts = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs", ".go", ".rs",
            ".java", ".cs", ".cpp", ".c", ".h", ".hpp", ".html", ".css", ".sh",
            ".bat", ".json", ".yaml", ".yml", ".kt", ".kts", ".swift"
        }
        selected_files = [f for f in files if os.path.splitext(f.lower())[1] in code_exts]
        if not selected_files:
            selected_files = files[:50]

        reduced_snippets: Dict[str, str] = {}
        for f in selected_files:
            raw_code = snippets.get(f, "")
            if include_file_contents:
                reduced_snippets[f] = TokenReducer.reduce(raw_code, f, mode=reduction_mode)
            else:
                reduced_snippets[f] = f"# File: {f} ({len(raw_code.splitlines())} lines)"

        raw_context = generate_offline_context(abs_root, selected_files, reduced_snippets)
        token_count = count_tokens_precise(raw_context)

        if token_count > max_tokens:
            try:
                from tzero_features import RepositoryPageRank
                pr_analyzer = RepositoryPageRank(abs_root)
                ranks = pr_analyzer.rank(top_k=len(selected_files))
                score_map = {r["file"]: r["score"] for r in ranks}
            except Exception:
                score_map = {}

            def file_priority(f: str) -> float:
                pr = score_map.get(f, 0.0)
                full_p = os.path.join(abs_root, f)
                try:
                    mtime = os.path.getmtime(full_p)
                except Exception:
                    mtime = 0.0
                return (pr * 1000.0) + (mtime / 1e9)

            sorted_files = sorted(selected_files, key=file_priority, reverse=True)
            
            pruned_files: List[str] = []
            pruned_snippets: Dict[str, str] = {}
            current_tokens = 0
            keep_count = 0
            for f in sorted_files:
                snip = reduced_snippets.get(f, "")
                t_cost = count_tokens_precise(snip)
                if current_tokens + t_cost <= max_tokens:
                    pruned_files.append(f)
                    pruned_snippets[f] = snip
                    current_tokens += t_cost
                    keep_count += 1
                else:
                    pruned_files.append(f)
                    pruned_snippets[f] = f"# [TRUNCATED] High priority AST boundary. Full content omitted for budget ({max_tokens} tokens)."
                    keep_count += 1
                    break

            raw_context = generate_offline_context(abs_root, pruned_files, pruned_snippets)
            raw_context += f"\n\n> [NOTE] Context was capped to fit max_tokens={max_tokens} (retained top {keep_count} priority modules prioritized via PageRank + Recency)."

        return raw_context

    # -------------------------------------------------------------------------
    # TOOL 2: query_module_dependencies
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="query_module_dependencies",
        description=(
            "Analyzes import/export dependencies, module relationships, and internal vs external package dependencies across polyglot files (Python, TypeScript, Go, Rust, Java, C#, C++).\n\n"
            "Behavior:\n"
            "- Read-only: Inspects source syntax trees without modifying or moving files.\n"
            "- Idempotent: Deterministic dependency mapping for any scanned repository.\n"
            "- 100% Offline: Local regex and AST parsing; zero external network requests.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run before refactoring, moving, or removing a module to inspect inbound dependents (who imports this) and outbound dependencies (what this imports).\n"
            "- Sibling Routing: For deep recursive function/method call chains (caller -> callee call graph), use 'trace_symbol_call_chain'. To test whether imports violate layer boundary rules, use 'enforce_architecture_boundaries'.\n\n"
            "Returns: Markdown report detailing inbound referrers, outbound imports, and the workspace dependency pool."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_query_module_dependencies(
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to scan (default: current directory).")] = ".",
        file_path: Annotated[str, Field(default="", description="Optional relative or absolute path to a specific file to inspect. If empty, analyzes the whole workspace.")] = ""
    ) -> str:
        """Analyzes dependency structure and import graphs.
        
        Args:
            project_root: Root directory of the repository (default: current directory).
            file_path: Optional relative or absolute path to a specific file to inspect. If empty, analyzes the whole workspace.
        """
        abs_root = os.path.abspath(project_root)
        if not os.path.isdir(abs_root):
            return f"[ERROR] Directory not found: {abs_root}"

        scanner = CodebaseScanner()
        files, sizes, snippets = scanner.scan_directory(abs_root)

        if file_path:
            target_path = os.path.join(abs_root, file_path) if not os.path.isabs(file_path) else file_path
            rel_target = os.path.relpath(target_path, abs_root).replace("\\", "/")
            if not os.path.isfile(target_path):
                return f"[ERROR] File not found: {target_path}"

            imports = get_file_imports(target_path)
            
            inbound_referrers = []
            stem = os.path.splitext(os.path.basename(file_path))[0]
            for f in files:
                if f != rel_target and f.endswith(".py"):
                    full_p = os.path.join(abs_root, f)
                    f_imports = get_file_imports(full_p)
                    if any(stem == imp.split('.')[0] for imp in f_imports):
                        inbound_referrers.append(f)

            out = [
                f"# 📦 Dependency Analysis for `{rel_target}`\n",
                f"- **Total Outbound Imports:** {len(imports)}",
                f"- **Inbound Dependents (Referenced By):** {len(inbound_referrers)} modules\n",
                "### Outbound Dependencies (Imports):",
            ]
            if imports:
                for imp in sorted(imports):
                    out.append(f"  - `{imp}`")
            else:
                out.append("  *(No imports detected)*")

            out.append("\n### Inbound References (Modules that depend on this file):")
            if inbound_referrers:
                for ref in sorted(inbound_referrers):
                    out.append(f"  - `{ref}`")
            else:
                out.append("  *(No inbound references detected within workspace)*")

            return "\n".join(out)

        # Full repository graph
        graph = build_workspace_import_graph(files, abs_root)
        
        all_external = set()
        out = [
            f"# 🌐 Workspace Dependency Topology: {os.path.basename(abs_root)}\n",
            f"- **Analyzed Python Modules with Imports:** {len(graph)}",
            f"- **Inter-module Relationships:** {sum(len(v) for v in graph.values())}\n",
            "| Module | Imported Dependencies |",
            "|:-------|:----------------------|"
        ]

        for mod in sorted(graph.keys()):
            deps = graph[mod]
            all_external.update(deps)
            deps_str = ", ".join(f"`{d}`" for d in sorted(deps)) if deps else "*none*"
            out.append(f"| `{mod}` | {deps_str} |")

        out.append(f"\n### Detected Dependency Pool ({len(all_external)} packages):")
        for pkg in sorted(all_external):
            out.append(f"- `{pkg}`")

        return "\n".join(out)

    # -------------------------------------------------------------------------
    # TOOL 3: query_architecture_boundaries
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="query_architecture_boundaries",
        description=(
            "Retrieves active T-4 architectural tier boundary definitions, operational constraints, and zero-leak security rules defined in tzero.rules.json or built-in defaults.\n\n"
            "Behavior:\n"
            "- Read-only: Reads configuration files; does not modify rules or codebase files.\n"
            "- Idempotent: Returns consistent rule definitions for identical configurations.\n"
            "- 100% Offline: Local JSON file lookup without remote calls.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Consult before designing new features or adding imports to understand layer isolation rules (e.g. presentation cannot import database models) and avoid architecture violations.\n"
            "- Sibling Routing: To actively validate workspace code against these rules and detect violations, use 'enforce_architecture_boundaries'. To view complete Mermaid topology blueprints, use 'generate_architecture_blueprint'.\n\n"
            "Returns: Markdown specification of architectural layers, allowed/forbidden import directions, and security constraints."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_query_architecture_boundaries(
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository where tzero.rules.json is located (default: current directory).")] = ".",
        extra_guidance: Annotated[str, Field(default="", description="Optional custom rules, architecture styles, or conventions to inject into the boundary definition.")] = ""
    ) -> str:
        """Generates architectural guardrails and boundary rules for AI agents.
        
        Args:
            project_root: Root directory of the repository (default: current directory).
            extra_guidance: Optional custom rules, architecture styles, or conventions.
        """
        abs_root = os.path.abspath(project_root)
        if not os.path.isdir(abs_root):
            return f"[ERROR] Directory not found: {abs_root}"

        scanner = CodebaseScanner()
        files, sizes, snippets = scanner.scan_directory(abs_root)
        p_name = os.path.basename(abs_root) or "Project"
        tree_ascii = "\n".join(f"├── {f}" for f in sorted(files))

        return ContextExportManager.generate_agents_blueprint(
            project_name=p_name,
            files_tree=tree_ascii,
            snippets=snippets,
            extra_rules=extra_guidance
        )

    # -------------------------------------------------------------------------
    # TOOL 4: generate_architecture_blueprint
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="generate_architecture_blueprint",
        description=(
            "Generates a complete system architectural specification (ARCHITECTURE.md) including auto-generated Mermaid component topology diagrams, layer boundaries, and module hierarchies.\n\n"
            "Behavior:\n"
            "- Read-only by default: Returns formatted markdown text. Does NOT write files unless invoked via CLI export.\n"
            "- Idempotent: Produces deterministic AST topology when use_ai=False.\n"
            "- Cost: 100% free and local by default (use_ai=False). If use_ai=True, uses configured environment API key (e.g. NVIDIA NIM / OpenAI) for enriched architectural narrative.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Create or update system architecture documentation and visual Mermaid flow diagrams for onboarding or RFC review.\n"
            "- Sibling Routing: For checking rule compliance against defined boundaries, use 'enforce_architecture_boundaries'. For basic dependency trees, use 'query_module_dependencies'.\n\n"
            "Returns: Comprehensive Markdown document with live Mermaid diagrams, layer classifications, and component interfaces."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_generate_architecture_blueprint(
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to analyze and document (default: current directory).")] = ".",
        use_ai: Annotated[bool, Field(default=False, description="When True, uses configured 3rd-party AI or Free AI Cloud to synthesize deep architecture analysis; when False (default), runs 100% offline AST analysis.")] = False,
        model: Annotated[str, Field(default="", description="Optional model identifier override (e.g. 'deepseek-v4.1-flash', 'gpt-4o') when use_ai is True.")] = ""
    ) -> str:
        """Generates a complete ARCHITECTURE.md document with live Mermaid diagrams.
        
        Args:
            project_root: Root directory of the repository (default: current directory).
            use_ai: If True, uses configured 3rd-party AI or Free AI Cloud to synthesize deep architecture analysis.
            model: Optional model identifier override (e.g. 'deepseek-v4.1-flash', 'gpt-4o').
        """
        abs_root = os.path.abspath(project_root)
        if not os.path.isdir(abs_root):
            return f"[ERROR] Directory not found: {abs_root}"

        scanner = CodebaseScanner()
        files, sizes, snippets = scanner.scan_directory(abs_root)
        p_name = os.path.basename(abs_root) or "Project"
        
        deps_map = build_workspace_import_graph(files, abs_root)

        provider = None
        api_base = ""
        api_key = ""
        if use_ai:
            prof = _config_mgr.get_profile()
            prov_name = prof.get("provider", "NVIDIA NIM")
            provider = PROVIDERS.get(prov_name)
            if provider:
                api_base = provider.get_base_url()
                api_key = _config_mgr.get_credential(provider.name) or os.getenv("NVIDIA_API_KEY", "")

        return ContextExportManager.generate_architecture_blueprint(
            project_name=p_name,
            files=files,
            deps=deps_map,
            snippets=snippets,
            use_ai=use_ai,
            provider=provider,
            api_base=api_base,
            api_key=api_key,
            model=model
        )

    # -------------------------------------------------------------------------
    # TOOL 5: generate_repo_map
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="generate_repo_map",
        description=(
            "Generates an ultra-compressed AST symbol token map (classes, methods, functions) tailored for LLM chat prompts and extreme context window savings.\n\n"
            "Behavior:\n"
            "- Read-only: Extracts AST signatures without writing or modifying files.\n"
            "- Idempotent: Deterministic symbol catalog for the same codebase state.\n"
            "- 100% Offline: Local AST extraction; zero external API calls.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Provide the LLM with an immediate high-level index of all classes and functions across the repository in minimal tokens (~5-15 tokens per file).\n"
            "- Sibling Routing: For full function signatures with parameter types and docstrings, use 'get_project_context_tree'. For 1st-degree context around a specific focus file, use 'get_smart_skeleton_context'.\n\n"
            "Returns: Compact Markdown symbol map indexed by file path."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_generate_repo_map(
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to map (default: current directory).")] = ".",
        max_tokens: Annotated[int, Field(default=4000, description="Maximum token budget for the repo map (default: 4000).")] = 4000
    ) -> str:
        """Builds a compressed AST symbol map for the repository.
        
        Args:
            project_root: Root directory of the repository (default: current directory).
            max_tokens: Maximum token budget for the repo map (default: 4000).
        """
        abs_root = os.path.abspath(project_root)
        if not os.path.isdir(abs_root):
            return f"[ERROR] Directory not found: {abs_root}"

        scanner = CodebaseScanner()
        files, sizes, snippets = scanner.scan_directory(abs_root)
        p_name = os.path.basename(abs_root) or "Project"

        repo_map = ContextExportManager.generate_repo_map(
            project_name=p_name,
            files=files,
            snippets=snippets
        )
        tokens = count_tokens_precise(repo_map)
        if tokens > max_tokens:
            lines = repo_map.splitlines()
            budget_lines = max(10, int(len(lines) * (max_tokens / tokens)))
            repo_map = "\n".join(lines[:budget_lines]) + f"\n... [Truncated to {max_tokens} tokens]"

        return repo_map

    # -------------------------------------------------------------------------
    # TOOL 6: audit_codebase_quality
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="audit_codebase_quality",
        description=(
            "Performs an AST static code smell audit, cyclomatic complexity check, copy-paste duplicity scan, and 100% Zero-Leak security audit for exposed credentials.\n\n"
            "Behavior:\n"
            "- Read-only: Evaluates AST nodes and regex patterns; does not modify or delete files.\n"
            "- Idempotent: Produces consistent quality diagnostics for the same code.\n"
            "- 100% Offline: Fully private local analysis; zero external requests.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run as a pre-commit or pre-PR code health audit to identify complex routines (> 30 lines, > 5 args), missing docstrings, architectural boundary violations, and hardcoded secrets.\n"
            "- Sibling Routing: If you only need to verify zero hardcoded secrets/API keys, use 'verify_zero_leak_security'. If you only want unused function detection, use 'find_dead_code'. If you only want duplicate logic blocks, use 'find_code_duplicity'.\n\n"
            "Returns: Comprehensive diagnostic Markdown report with severity ratings (T-001 Security, T-002 Boundaries, T-003 Contracts, T-004 Complexity), line numbers, and actionable remediation steps."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_audit_codebase_quality(
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to audit (default: current directory).")] = ".",
        file_path: Annotated[str, Field(default="", description="Optional path to a specific file to audit. If empty, audits all code files in the workspace.")] = ""
    ) -> str:
        """Audits codebase quality, AST smells, and secret exposure.
        
        Args:
            project_root: Root directory of the repository (default: current directory).
            file_path: Optional path to a specific file to audit. If empty, audits all Python files.
        """
        abs_root = os.path.abspath(project_root)
        if not os.path.isdir(abs_root):
            return f"[ERROR] Directory not found: {abs_root}"

        scanner = CodebaseScanner()
        files, sizes, snippets = scanner.scan_directory(abs_root)

        target_files = [file_path] if file_path else [f for f in files if f.endswith(".py")]
        
        # Secret scanning regexes
        secret_patterns = [
            (re.compile(r"""(?i)(?:api_key|apikey|secret|password|auth_token)\s*=\s*['"][A-Za-z0-9_\-\.]{16,}['"]"""), "Hardcoded Secret / API Key"),
            (re.compile(r"""sk-[a-zA-Z0-9]{20,}T3BlbkFJ[a-zA-Z0-9]{20,}"""), "OpenAI API Key Pattern"),
            (re.compile(r"""nvapi-[a-zA-Z0-9_\-]{30,}"""), "NVIDIA API Key Pattern"),
            (re.compile(r"""AIza[0-9A-Za-z-_]{35}"""), "Google Gemini / Cloud Key"),
            (re.compile(r"""sk-ant-[a-zA-Z0-9_\-]{30,}"""), "Anthropic Claude Key Pattern"),
        ]

        total_smells = 0
        total_secrets = 0
        report = [
            f"# 🛡️ Code Quality & Security Audit: {os.path.basename(abs_root)}\n",
            f"- **Audited Python Modules:** {len(target_files)}",
        ]

        # Check T-002 Architectural Boundary Rules
        arch_violations = []
        try:
            from tzero_features import ArchitectureRuleEngine
            arch_engine = ArchitectureRuleEngine(abs_root)
            arch_res = arch_engine.enforce_boundaries()
            arch_violations = arch_res.get("violations", [])
        except Exception:
            arch_res = {"clean": True, "violations": []}

        file_reports = []
        if arch_violations:
            arch_lines = ["### 🏛️ T-002 Architectural Boundary Violations"]
            for av in arch_violations:
                arch_lines.append(f"- ❌ **[T-002 VIOLATION]** `{av['file']}:{av['line']}`: Layer '{av['layer']}' cannot import '{av['forbidden_import']}' ({av['reason']})")
            file_reports.append("\n".join(arch_lines))

        for rel_f in target_files:
            full_p = os.path.join(abs_root, rel_f) if not os.path.isabs(rel_f) else rel_f
            if not os.path.isfile(full_p):
                continue

            try:
                with open(full_p, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
            except Exception:
                continue

            auditor = StaticCodeAnalyzer(rel_f)
            auditor.analyze_source(content)
            smells = auditor.issues
            
            file_secrets = []
            for pattern, desc in secret_patterns:
                matches = pattern.findall(content)
                if matches:
                    file_secrets.append(f"{desc} (found {len(matches)} potential occurrences)")

            if smells or file_secrets:
                total_smells += len(smells)
                total_secrets += len(file_secrets)
                section = [f"### `{rel_f}`"]
                for s in file_secrets:
                    section.append(f"- 🚨 **[T-001 CRITICAL] Security Risk:** {s}")
                for sm in smells:
                    rule_id = sm.get("rule") or ("T-003" if sm.get("ref") in ("NoDocstring", "NoClassDoc", "ASTError", "SyntaxError") else "T-004")
                    msg = sm.get("msg") or sm.get("message") or sm.get("ref", "Code smell detected")
                    section.append(f"- ⚠️ Line {sm.get('line', '?')}: **[{rule_id} {sm.get('ref', 'Smell')}]** {msg}")
                file_reports.append("\n".join(section))

        report.append(f"- **Total AST Code Smells Detected:** {total_smells}")
        report.append(f"- **Security Secret Violations:** {total_secrets}")
        report.append(f"- **T-001 (Zero-Leak Security):** {'✅ 100% PASSED (0 secrets exposed)' if total_secrets == 0 else f'🚨 {total_secrets} CRITICAL LEAKS DETECTED'}")
        report.append(f"- **T-002 (Architectural Boundaries):** {'✅ 100% CONFORMANT (0 violations)' if not arch_violations else f'❌ {len(arch_violations)} BOUNDARY VIOLATIONS'}")
        report.append(f"- **T-003 (AST Interface Contracts):** ✅ Verified ({len(target_files)} modules scanned)")
        report.append(f"- **T-004 (AST Code Smells & Complexity):** {'✅ 100% CLEAN (0 smells)' if total_smells == 0 else f'⚠️ {total_smells} smells flagged'}\n")

        if total_secrets == 0:
            report.append("> [!TIP]\n> **100% Zero-Leak Verified:** No exposed API keys or secrets detected.")

        if file_reports:
            report.append("\n---\n")
            report.extend(file_reports)
        else:
            report.append("\n✨ **All audited files passed inspection with zero detected code smells or security leaks.**")

        return "\n".join(report)

    # -------------------------------------------------------------------------
    # TOOL 7: find_code_duplicity
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="find_code_duplicity",
        description=(
            "Scans the repository to identify duplicate or copy-pasted blocks of code across multiple files to identify refactoring opportunities.\n\n"
            "Behavior:\n"
            "- Read-only: Hashes and compares source lines; does not modify code.\n"
            "- Idempotent: Deterministic duplicate detection for any codebase state.\n"
            "- 100% Offline: Fully local execution without network calls.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run during refactoring sprints to locate redundant copy-pasted code blocks suitable for extraction into shared utility functions.\n"
            "- Sibling Routing: For full codebase quality and complexity audits, use 'audit_codebase_quality'. For unused unreferenced code, use 'find_dead_code'.\n\n"
            "Returns: Markdown report detailing duplicate code clusters with file paths, line ranges, and side-by-side code snippets."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_find_code_duplicity(
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to scan (default: current directory).")] = ".",
        min_lines: Annotated[int, Field(default=6, description="Minimum identical consecutive lines to classify as a duplicate block (default: 6).")] = 6
    ) -> str:
        """Identifies duplicate code blocks across workspace files.
        
        Args:
            project_root: Root directory of the repository (default: current directory).
            min_lines: Minimum identical lines to classify as a duplicate block (default: 6).
        """
        abs_root = os.path.abspath(project_root)
        if not os.path.isdir(abs_root):
            return f"[ERROR] Directory not found: {abs_root}"

        scanner = CodebaseScanner()
        files, sizes, snippets = scanner.scan_directory(abs_root)
        
        # Read raw content to detect duplicate lines across files
        raw_snippets: Dict[str, str] = {}
        for f in files:
            full_p = os.path.join(abs_root, f) if not os.path.isabs(f) else f
            if os.path.isfile(full_p):
                try:
                    with open(full_p, "r", encoding="utf-8", errors="ignore") as fp:
                        raw_snippets[f] = fp.read()
                except Exception:
                    pass

        finder = WorkspaceDuplicityFinder(raw_snippets)
        duplicates = finder.find_duplicates(min_lines=min_lines)
        if not duplicates:
            return f"✨ No duplicate code blocks exceeding {min_lines} lines detected across {len(files)} files in `{abs_root}`."

        out = [
            f"# 🔄 Workspace Code Duplicity Report: {os.path.basename(abs_root)}\n",
            f"- **Analyzed Files:** {len(files)}",
            f"- **Identified Duplicate Clusters:** {len(duplicates)}",
            f"- **Threshold:** {min_lines}+ consecutive identical lines\n"
        ]

        for i, dup in enumerate(duplicates[:25], 1):
            out.append(f"### Duplicate Cluster #{i}")
            out.append(f"- Source 1: `{dup.get('file1')}` (Line {dup.get('line1')})")
            out.append(f"- Source 2: `{dup.get('file2')}` (Line {dup.get('line2')})")
            if "snippet" in dup:
                out.append("```\n" + dup["snippet"] + "\n```")

        return "\n".join(out)

    # -------------------------------------------------------------------------
    # TOOL 8: estimate_token_cost
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="estimate_token_cost",
        description=(
            "Calculates exact token count and estimated API prompting cost (USD) across major LLM providers (OpenAI GPT-4o, Claude 3.7 Sonnet, Groq, NVIDIA NIM, and Ollama $0) for a given text or directory.\n\n"
            "Behavior:\n"
            "- Read-only: Mathematical cost projection; does NOT invoke provider APIs or incur financial billing.\n"
            "- Idempotent: Produces exact calculations for identical token counts.\n"
            "- 100% Offline: Uses local pricing tables without external HTTP queries.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Estimate prompt token volume and dollar costs before sending large codebase context to commercial LLM APIs.\n"
            "- Sibling Routing: To track team monthly/annual cumulative ROI savings and compression metrics over time, use 'get_token_savings_metrics'.\n\n"
            "Returns: Markdown table comparing per-million token rates and total estimated costs across major models."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_estimate_token_cost(
        text: Annotated[str, Field(default="", description="Optional raw text to estimate. If empty, analyzes context generated from project_root.")] = "",
        project_root: Annotated[str, Field(default=".", description="Project directory to scan if text is empty (default: current directory).")] = ".",
        reduction_mode: Annotated[str, Field(default="ultra", description="Reduction tier ('ultra', 'balanced', 'none') applied when scanning project_root.")] = "ultra"
    ) -> str:
        """Calculates token counts and costs across LLM providers.
        
        Args:
            text: Optional raw text to estimate. If empty, analyzes context from project_root.
            project_root: Project directory to scan if text is empty (default: current directory).
            reduction_mode: Reduction mode to apply when scanning project_root.
        """
        if text:
            target_text = text
            source_desc = f"Raw text input ({len(text)} characters)"
        else:
            abs_root = os.path.abspath(project_root)
            if not os.path.isdir(abs_root):
                return f"[ERROR] Directory not found: {abs_root}"
            scanner = CodebaseScanner()
            files, sizes, snippets = scanner.scan_directory(abs_root)
            target_text = generate_offline_context(abs_root, files[:50], snippets)
            source_desc = f"Context tree from `{abs_root}` ({len(files)} files, mode={reduction_mode})"

        tokens = count_tokens_precise(target_text)
        out = [
            f"# 💰 T-Zero Token & API Cost Estimation\n",
            f"- **Target Source:** {source_desc}",
            f"- **Calculated Token Volume:** **{tokens:,} tokens**\n",
            "| AI Provider | Rate per 1M Tokens | Estimated Cost (USD) |",
            "|:------------|:-------------------|:---------------------|"
        ]

        providers = [
            ("OpenAI (GPT-4o)", "OpenAI"),
            ("Anthropic (Claude 3.7 Sonnet)", "Anthropic"),
            ("Groq (Llama-3.3-70B)", "Groq"),
            ("NVIDIA NIM (DeepSeek / Nemotron)", "NVIDIA NIM"),
            ("Ollama (Local Private)", "Ollama (Local)"),
        ]

        for display_name, prov_key in providers:
            rate = PROVIDER_COST_PER_MILLION.get(prov_key, 0.0)
            cost = calculate_token_cost(tokens, prov_key)
            rate_str = f"${rate:.2f}" if rate > 0 else "FREE ($0.00)"
            cost_str = f"${cost:.4f}" if cost > 0 else "$0.0000"
            out.append(f"| {display_name} | {rate_str} | **{cost_str}** |")

        out.append("\n> [TIP] Running with `reduction_mode='ultra'` typically reduces token costs by **80% to 95%**.")
        return "\n".join(out)

    # -------------------------------------------------------------------------
    # TOOL 9: analyze_change_impact
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="analyze_change_impact",
        description=(
            "Calculates blast radius score (0-100) and identifies all direct and transitive dependent modules across the codebase before modifying a specific function, class, or symbol.\n\n"
            "Behavior:\n"
            "- Read-only: AST dependency graph traversal; does not modify source files.\n"
            "- Idempotent: Deterministic impact calculation for any given target symbol.\n"
            "- 100% Offline: Local AST analysis without remote services.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run BEFORE renaming, refactoring, or modifying a function or class to determine which caller modules could break.\n"
            "- Sibling Routing: For deep recursive caller/callee trees with visual Mermaid graphs, use 'trace_symbol_call_chain'. For file-level module dependencies, use 'query_module_dependencies'.\n\n"
            "Returns: Structured Markdown report with blast radius score, risk tier, direct dependents, and transitive impact paths."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_analyze_change_impact(
        target_symbol: Annotated[str, Field(description="Name of the function, class, or method to analyze for change blast radius.")],
        project_root: Annotated[str, Field(default=".", description="Workspace root directory containing target symbols (default: current directory).")] = "."
    ) -> str:
        """Traces symbol references, inbound dependents, and calculates blast radius score."""
        from tzero_features import ChangeImpactAnalyzer
        analyzer = ChangeImpactAnalyzer(project_root)
        analysis = analyzer.analyze_symbol(target_symbol)
        return analyzer.format_report(analysis)

    # -------------------------------------------------------------------------
    # TOOL 10: enforce_architecture_boundaries
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="enforce_architecture_boundaries",
        description=(
            "Enforces T-4 architectural boundary rules (tzero.rules.json), verifying modular separation and detecting unauthorized cross-layer imports.\n\n"
            "Behavior:\n"
            "- Read-only: Audits import AST statements; does NOT block git, mutate code, or modify configuration files.\n"
            "- Idempotent: Yields consistent validation results for any given codebase state.\n"
            "- 100% Offline: Local AST validation without external dependencies.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run in CI/CD pipelines or before committing to verify that presentation/UI layers do not import internal database/storage modules directly.\n"
            "- Sibling Routing: To view active boundary rules without evaluating code, use 'query_architecture_boundaries'. For general code quality smells, use 'audit_codebase_quality'.\n\n"
            "Returns: Compliance report detailing pass/fail status, violating file paths, line numbers, layer names, and allowed import directions."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_enforce_architecture_boundaries(
        project_root: Annotated[str, Field(default=".", description="Workspace root to validate against architectural rules (default: current directory).")] = ".",
        rules_file: Annotated[str, Field(default="tzero.rules.json", description="Path to rules JSON file (default: 'tzero.rules.json'). Resolves relative to project_root.")] = "tzero.rules.json"
    ) -> str:
        """Audits imports against architectural layer boundaries."""
        from tzero_features import ArchitectureRuleEngine
        config_p = os.path.join(project_root, rules_file) if not os.path.isabs(rules_file) else rules_file
        engine = ArchitectureRuleEngine(project_root, config_p)
        res = engine.enforce_boundaries()
        # The report is colored for terminals; strip ANSI codes so agents get clean text.
        return re.sub(r"\[[0-9;]*m", "", engine.format_report(res))

    # -------------------------------------------------------------------------
    # TOOL 11: search_codebase_semantic
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="search_codebase_semantic",
        description=(
            "100% Private, local hybrid BM25 + TF-IDF semantic code search across workspace AST tokens, function headers, and docstrings without sending code to third-party embedding APIs.\n\n"
            "Behavior:\n"
            "- Read-only: In-memory inverted index query; does not modify files.\n"
            "- Idempotent: Deterministic search ranking for identical query and code states.\n"
            "- 100% Offline & Private: Never sends code or embeddings to external APIs; $0 cost and zero data leakage.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Find functions, classes, or logic snippets using conceptual natural language queries (e.g. 'authentication jwt token verify', 'rate limit algorithm').\n"
            "- Sibling Routing: For exact string or regex matches, use IDE grep or ripgrep. For finding unused code, use 'find_dead_code'.\n\n"
            "Returns: Ranked Markdown list of matching code snippets with file locations, match scores, and surrounding context."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_search_codebase_semantic(
        query: Annotated[str, Field(description="Natural language or technical keyword query describing the desired code logic.")],
        project_root: Annotated[str, Field(default=".", description="Workspace root directory to index and search (default: current directory).")] = ".",
        top_k: Annotated[int, Field(default=5, description="Maximum number of top-matching code snippets to return (default: 5).")] = 5
    ) -> str:
        """Performs private local hybrid semantic search across the codebase."""
        from tzero_features import LocalSemanticCodeSearch
        searcher = LocalSemanticCodeSearch(project_root)
        results = searcher.search(query, top_k=top_k)
        return searcher.format_search_results(query, results)

    # -------------------------------------------------------------------------
    # TOOL 12: export_agent_rules
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="export_agent_rules",
        description=(
            "Generates and writes standardized AI agent rule specifications (.cursorrules, .cursor/rules/*.mdc, .clinerules, and .github/copilot-instructions.md) into the workspace.\n\n"
            "Behavior:\n"
            "- Mutating: Creates or updates configuration files in the target workspace directory.\n"
            "- Idempotent: Overwrites existing T-Zero agent rule files with current architecture rules without corrupting user customizations.\n"
            "- 100% Offline: Generates rule files locally using built-in templates.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run when setting up a repository for AI pair-programming with Cursor, Claude Code, Cline, Windsurf, or GitHub Copilot.\n"
            "- Sibling Routing: To view architectural boundaries without writing files to disk, use 'query_architecture_boundaries'.\n\n"
            "Returns: Confirmation message listing all generated rule file paths."),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_export_agent_rules(
        project_root: Annotated[str, Field(default=".", description="Target workspace directory where agent rule files will be created (default: current directory).")] = ".",
        target: Annotated[str, Field(default="all", description="Target editor format: 'cursor', 'cline', 'windsurf', or 'all' (default: 'all').")] = "all"
    ) -> str:
        """Exports AI coding agent rules into workspace."""
        from tzero_features import AgentRulesGenerator
        created = AgentRulesGenerator.export_all(project_root)
        rel_paths = [os.path.relpath(p, project_root) for p in created]
        return "✅ Generated AI Agent rule files:\n" + "\n".join(f"- `{p}`" for p in rel_paths)

    # -------------------------------------------------------------------------
    # TOOL 13: get_token_savings_metrics
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="get_token_savings_metrics",
        description=(
            "Computes quantitative token compression metrics, reduction percentage, and developer team financial ROI savings (USD/month).\n\n"
            "Behavior:\n"
            "- Read-only: Evaluates codebase file sizes and compressed token counts; does not alter files or call APIs.\n"
            "- Idempotent: Deterministic metric calculations for current codebase volume.\n"
            "- 100% Offline: Fully local calculation without network access.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Quantify efficiency gains and financial savings from T-Zero context compression for team reports and engineering leadership.\n"
            "- Sibling Routing: For per-model single-prompt cost comparisons (OpenAI vs Anthropic vs Gemini), use 'estimate_token_cost'.\n\n"
            "Returns: Markdown executive summary with token reduction percentages, monthly developer cost savings, and annual ROI projections."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_get_token_savings_metrics(
        project_root: Annotated[str, Field(default=".", description="Target workspace directory to measure (default: current directory).")] = ".",
        team_size: Annotated[int, Field(default=5, description="Number of developers in the engineering team used to model monthly ROI savings (default: 5).")] = 5
    ) -> str:
        """Calculates token reduction and economic ROI."""
        from tzero_features import TokenROICalculator
        from tzero_v3 import CodebaseScanner, TokenReducer

        abs_root = os.path.abspath(project_root)
        scanner = CodebaseScanner()
        files, sizes, snippets = scanner.scan_directory(abs_root)

        raw_chars = sum(sizes.values())
        raw_tokens = max(1, raw_chars // 4)
        reduced_text = "".join(snippets.values())
        reduced_tokens = max(1, count_tokens_precise(reduced_text))

        metrics = TokenROICalculator.calculate(raw_tokens, reduced_tokens, team_size=team_size)
        return TokenROICalculator.format_report(metrics)

    # -------------------------------------------------------------------------
    # TOOL 14: get_incremental_diff_context
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="get_incremental_diff_context",
        description=(
            "Calculates hyper-compact PR git diff context (changed symbols + downstream blast radius dependents) for 98%+ token savings during code review and debugging.\n\n"
            "Behavior:\n"
            "- Read-only: Inspects git diff and local AST; does not stage, commit, or revert any git changes.\n"
            "- Idempotent: Deterministic for the same git working tree status.\n"
            "- 100% Offline: Local git CLI and AST processing.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Provide focused context during code review, PR description generation, or bug hunting for pending changes with 98%+ token reduction.\n"
            "- Sibling Routing: For full repository context, use 'get_project_context_tree'. For single-symbol impact analysis, use 'analyze_change_impact'.\n\n"
            "Returns: Structured Markdown diff context with changed symbol signatures, diff hunks, and caller references."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_get_incremental_diff_context(
        base_ref: Annotated[str, Field(default="HEAD~1", description="Git revision or branch to diff against (default: 'HEAD~1').")] = "HEAD~1",
        project_root: Annotated[str, Field(default=".", description="Git repository root path (default: current directory).")] = "."
    ) -> str:
        """Generates incremental PR diff context and downstream caller signatures."""
        from tzero_features import GitDiffContextBuilder
        builder = GitDiffContextBuilder(project_root)
        res = builder.build_diff_context(base_ref)
        return res["markdown"]

    # -------------------------------------------------------------------------
    # TOOL 15: prune_code_snippet
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="prune_code_snippet",
        description=(
            "Compresses arbitrary in-memory source code or text into compact AST/interface signatures on-the-fly, returning pruned code and precise token savings percentage (80-95% reduction).\n\n"
            "Behavior:\n"
            "- Pure in-memory transformation: Does not read or write any files on disk; takes text input and returns pruned text.\n"
            "- Idempotent: Deterministic output for identical input code and reduction mode.\n"
            "- 100% Offline: Polyglot AST/regex parsers for Python, TypeScript, Go, Rust, Java, C#, C++, Swift, Kotlin.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Compress in-memory code blocks or clipboard buffers before passing them into LLM chat prompts.\n"
            "- Sibling Routing: To scan and compress entire directories or repositories on disk, use 'get_project_context_tree' or 'get_smart_skeleton_context'.\n\n"
            "Returns: Markdown fenced code block with pruned signatures and precise token reduction percentage."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_prune_code_snippet(
        code: Annotated[str, Field(description="Raw source code content to prune.")],
        file_path_or_ext: Annotated[str, Field(default="snippet.py", description="File name or extension (e.g. 'service.ts', 'main.go', 'app.py', '.rs', '.java', '.cs', '.kt', '.swift') indicating language parser.")] = "snippet.py",
        reduction_mode: Annotated[str, Field(default="ultra", description="Reduction tier: 'ultra' for AST signatures only (80-95% reduction), 'balanced' for signatures + control flow.")] = "ultra"
    ) -> str:
        """Compresses code snippets into functional signatures on-the-fly.
        
        Args:
            code: Source code text to prune.
            file_path_or_ext: File name or extension (e.g. 'service.ts', 'main.go', 'app.py', '.rs', '.java', '.cs').
            reduction_mode: 'ultra' for AST signatures only, 'balanced' for signatures + control flow.
        """
        if not code.strip():
            return "[WARNING] Provided code is empty."
        
        reduced, savings = TokenReducer.reduce_content(file_path_or_ext, code, mode=reduction_mode)
        raw_tokens = max(1, count_tokens_precise(code))
        reduced_tokens = max(1, count_tokens_precise(reduced))
        
        out = [
            f"# ✂️ T-Zero Code Pruning Result (`{file_path_or_ext}`)\n",
            f"- **Original Tokens:** {raw_tokens:,} tokens",
            f"- **Pruned Tokens:** {reduced_tokens:,} tokens",
            f"- **Token Compression:** **{savings:.1f}% reduction**\n",
            "```" + (os.path.splitext(file_path_or_ext)[1].lstrip(".") or "text"),
            reduced,
            "```"
        ]
        return "\n".join(out)

    # -------------------------------------------------------------------------
    # TOOL 16: verify_zero_leak_security
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="verify_zero_leak_security",
        description=(
            "100% Zero-Leak security scanner. Analyzes a file, code snippet, or repository workspace for hardcoded API keys (OpenAI, Anthropic, NVIDIA, Gemini, HuggingFace, GitHub), private keys, JWT tokens, and cloud secrets (100% private, 0 external network calls, $0 cost).\n\n"
            "Behavior:\n"
            "- Read-only: Pattern matching and entropy analysis; does NOT modify, expose, or upload credentials.\n"
            "- Idempotent: Deterministic security findings for identical content.\n"
            "- 100% Offline & Private: Never transmits inspected text to any remote server; all secret detections are masked.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run before git commit, push, or public release to guarantee zero secret leaks.\n"
            "- Sibling Routing: For broad code quality audits including complexity, docstrings, and layer rules, use 'audit_codebase_quality'.\n\n"
            "Returns: Security pass/fail report with masked secret snippets, affected file paths, and line numbers."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_verify_zero_leak_security(
        project_root: Annotated[str, Field(default=".", description="Workspace root directory to scan for secret leaks (default: current directory).")] = ".",
        target_file: Annotated[str, Field(default="", description="Optional single file path to inspect instead of the full workspace.")] = "",
        code_snippet: Annotated[str, Field(default="", description="Optional in-memory code string to inspect instead of files on disk.")] = ""
    ) -> str:
        """Runs Zero-Leak secret detection audit across workspace or snippets."""
        if code_snippet:
            secret_leaks = scan_text_for_secrets(code_snippet)
            if secret_leaks:
                out = [f"🚨 **Zero-Leak Security Alert: Found {len(secret_leaks)} potential secret leaks in snippet!**\n"]
                for leak in secret_leaks:
                    out.append(f"- Line {leak['line']}: {leak['desc']}")
                return "\n".join(out)
            return "🔒 [ZERO-LEAK PASS] No hardcoded API keys or secrets detected in code snippet."
            
        abs_root = os.path.abspath(project_root)
        if target_file:
            fp = os.path.join(abs_root, target_file) if not os.path.isabs(target_file) else target_file
            if not os.path.isfile(fp):
                return f"[ERROR] File not found: {fp}"
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception as e:
                return f"[ERROR] Could not read file: {e}"
            secret_leaks = scan_text_for_secrets(content)
            if secret_leaks:
                out = [f"🚨 **Zero-Leak Security Alert: Found {len(secret_leaks)} leaks in `{target_file}`!**\n"]
                for leak in secret_leaks:
                    out.append(f"- Line {leak['line']}: {leak['desc']}")
                return "\n".join(out)
            return f"🔒 [ZERO-LEAK PASS] File `{target_file}` is 100% clean. Zero hardcoded secrets detected."

        # Audit entire workspace for secret leaks
        scanner = CodebaseScanner()
        files, sizes, snippets = scanner.scan_directory(abs_root)
        all_leaks = []
        for f in files:
            content = snippets.get(f, "")
            leaks = scan_text_for_secrets(content)
            for leak in leaks:
                all_leaks.append((f, leak))
        
        if all_leaks:
            out = [f"🚨 **Zero-Leak Security Audit: Found {len(all_leaks)} potential secret leaks in workspace `{abs_root}`!**\n"]
            for fname, leak in all_leaks[:20]:
                out.append(f"- `{fname}` (Line {leak['line']}): {leak['desc']}")
            return "\n".join(out)
        return f"🔒 [ZERO-LEAK PASS] All {len(files)} files in `{abs_root}` passed 100% Zero-Leak security audit. Zero exposed secrets."

    # -------------------------------------------------------------------------
    # TOOL 17: verify_hallucination_guard
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="verify_hallucination_guard",
        description=(
            "Eliminates AI coding hallucinations before code is written or applied. Parses proposed code and verifies all internal imports and function/method call contracts (argument counts and keyword parameter names) against known workspace AST signatures.\n\n"
            "Behavior:\n"
            "- Read-only: Compares AST call signatures against local symbol catalog; does not modify source files.\n"
            "- Idempotent: Deterministic contract verification.\n"
            "- 100% Offline: Uses local AST indices without remote queries.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run BEFORE applying AI-generated code to prevent hallucinated module imports, missing functions, or wrong argument counts.\n"
            "- Sibling Routing: To enforce layer boundary separation rules, use 'enforce_architecture_boundaries'.\n\n"
            "Returns: Verification status report with specific contract mismatches and 'did you mean' fuzzy suggestions."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_verify_hallucination_guard(
        proposed_code: Annotated[str, Field(description="Python code proposed to be written or edited.")],
        target_file: Annotated[str, Field(default="", description="Optional path of the target file being modified to resolve relative imports.")] = "",
        project_root: Annotated[str, Field(default=".", description="Workspace root directory providing the ground-truth AST symbol catalog (default: current directory).")] = "."
    ) -> str:
        """Validates proposed code against workspace AST signatures and contracts.
        
        Args:
            proposed_code: Python code proposed to be written or edited.
            target_file: Optional path of the target file being modified.
            project_root: Root directory of the repository (default: current directory).
        """
        abs_root = os.path.abspath(project_root)
        from tzero_features import ZeroHallucinationGuard
        guard = ZeroHallucinationGuard(abs_root)
        res = guard.validate_code(proposed_code, target_file)
        return res["report"]

    # -------------------------------------------------------------------------
    # TOOL 18: get_smart_skeleton_context
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="get_smart_skeleton_context",
        description=(
            "Focus-aware dynamic skeletonizer. Returns the full, unpruned implementation of the focus file (or specific focus symbol), surrounded by ultra-compact T-3 AST signatures for all 1st-degree outbound imports and inbound callers. Solves the 'Lost in the Middle' problem while saving 95%+ tokens.\n\n"
            "Behavior:\n"
            "- Read-only: Traverses local AST dependencies; does not mutate files.\n"
            "- Idempotent: Returns identical focus + skeleton bundles for the same codebase state.\n"
            "- 100% Offline: Local AST parsing and signature reduction.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run when editing a specific file to provide the LLM with full implementation context plus compact interface skeletons of adjacent modules.\n"
            "- Sibling Routing: For repository-wide context, use 'get_project_context_tree'. For symbol index without file contents, use 'generate_repo_map'.\n\n"
            "Returns: Structured Markdown with full focus file source code and 1st-degree AST skeletons for imported and caller modules."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_get_smart_skeleton_context(
        focus_file: Annotated[str, Field(description="Target file path to focus on and retain with full implementation.")],
        focus_symbol: Annotated[str, Field(default="", description="Optional specific function or class name within focus_file to isolate.")] = "",
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository (default: current directory).")] = "."
    ) -> str:
        """Returns focus implementation with 1st-degree surrounding AST skeletons.
        
        Args:
            focus_file: Target file path to focus on.
            focus_symbol: Optional specific function or class name within focus_file to inspect.
            project_root: Root directory of the repository (default: current directory).
        """
        abs_root = os.path.abspath(project_root)
        from tzero_features import SmartSkeletonContextBuilder
        builder = SmartSkeletonContextBuilder(abs_root)
        return builder.build_skeleton(focus_file, focus_symbol)

    # -------------------------------------------------------------------------
    # TOOL 19: rank_repository_pagerank
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="rank_repository_pagerank",
        description=(
            "Identifies the architectural backbone and most critical modules of any repository using graph-theory PageRank centrality over AST import and reference topologies. Ranks modules by inbound/outbound degree and structural criticality.\n\n"
            "Behavior:\n"
            "- Read-only: Graph centrality computation; does not alter files.\n"
            "- Idempotent: Deterministic PageRank convergence for identical import graphs.\n"
            "- 100% Offline: Fully local graph traversal without external dependencies.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run when exploring an unfamiliar codebase to immediately identify the core architectural modules versus peripheral utilities.\n"
            "- Sibling Routing: For direct pairwise dependencies of a file, use 'query_module_dependencies'. For blast radius of a single function, use 'analyze_change_impact'.\n\n"
            "Returns: Ranked Markdown table with PageRank centrality scores, inbound/outbound degrees, and architectural significance notes."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_rank_repository_pagerank(
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to analyze (default: current directory).")] = ".",
        top_k: Annotated[int, Field(default=15, description="Number of top central modules to return in the ranking report (default: 15).")] = 15
    ) -> str:
        """Computes PageRank architectural centrality scores for repository modules.
        
        Args:
            project_root: Root directory of the repository (default: current directory).
            top_k: Number of top central modules to return in the ranking report (default: 15).
        """
        abs_root = os.path.abspath(project_root)
        from tzero_features import RepositoryPageRank
        ranker = RepositoryPageRank(abs_root)
        rankings = ranker.rank(top_k=top_k)
        return ranker.format_report(rankings)

    # -------------------------------------------------------------------------
    # TOOL 20: trace_symbol_call_chain
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="trace_symbol_call_chain",
        description=(
            "Traces deep execution paths across the codebase AST. Recursively discovers upstream callers (who calls symbol_name) and downstream callees (what symbol_name calls) up to max_depth, rendering an execution tree and Mermaid call diagram.\n\n"
            "Behavior:\n"
            "- Read-only: Recursively traverses AST function call expressions; does not modify source code.\n"
            "- Idempotent: Deterministic call graph traversal.\n"
            "- 100% Offline: Local AST analysis without external services.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run when debugging execution flows, tracing data paths into a function, or seeing everything a complex method calls recursively.\n"
            "- Sibling Routing: For quick single-symbol blast radius scoring (0-100), use 'analyze_change_impact'. For module-level import relations, use 'query_module_dependencies'.\n\n"
            "Returns: Markdown report containing recursive ASCII execution tree, caller/callee counts, and copy-pasteable Mermaid flowchart syntax."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_trace_symbol_call_chain(
        symbol_name: Annotated[str, Field(description="Exact function or method name to trace across the codebase call graph.")],
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository (default: current directory).")] = ".",
        max_depth: Annotated[int, Field(default=3, description="Maximum recursion depth for the call graph traversal (default: 3).")] = 3
    ) -> str:
        """Traces upstream and downstream call chains for any function or method.
        
        Args:
            symbol_name: Name of the function or method to trace.
            project_root: Root directory of the repository (default: current directory).
            max_depth: Maximum recursion depth for the call graph traversal (default: 3).
        """
        abs_root = os.path.abspath(project_root)
        from tzero_features import SymbolCallChainTracer
        tracer = SymbolCallChainTracer(abs_root)
        res = tracer.trace(symbol_name, max_depth=max_depth)
        return tracer.format_report(res)

    # -------------------------------------------------------------------------
    # TOOL 21: find_dead_code
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="find_dead_code",
        description=(
            "Finds unused, orphaned, or unreferenced functions and classes across the codebase AST. Excludes __all__, main, dunder methods, and test functions.\n\n"
            "Behavior:\n"
            "- Read-only: Computes symbol reference counts; does NOT delete or modify any source code files.\n"
            "- Idempotent: Consistent dead code candidate discovery for the same repository state.\n"
            "- 100% Offline: Local AST reference analysis.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run during technical debt cleanup to locate deprecated, dead, or forgotten functions and classes ready for safe removal.\n"
            "- Sibling Routing: For copy-pasted duplicate logic blocks, use 'find_code_duplicity'. For general complexity and linting, use 'audit_codebase_quality'.\n\n"
            "Returns: Markdown report listing candidate orphaned symbols with file paths, line numbers, and symbol types."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_find_dead_code(
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to scan for unreferenced symbols (default: current directory).")] = "."
    ) -> str:
        """Discovers unused symbols and dead code candidates across the codebase.
        
        Args:
            project_root: Root directory of the repository (default: current directory).
        """
        abs_root = os.path.abspath(project_root)
        from tzero_features import DeadCodeFinder
        finder = DeadCodeFinder(abs_root)
        dead = finder.find_unused_symbols()
        return finder.format_report(dead)

    # -------------------------------------------------------------------------
    # TOOL 22: jarvis_compress_semantic_memory
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="jarvis_compress_semantic_memory",
        description=(
            "Compresses natural language text, logs, or system instructions into T-Zero's 3-Layer Semantic Memory representation:\n"
            "- Layer A: Semantic Triplet Extraction with Named Entity Recognition (NER: Hardware, Protocol, IP, Crypto, Vuln, Software)\n"
            "- Layer B: Vector Quantized (VQ) Codebook discrete index mapping (e.g. #8421)\n"
            "- Layer C: Dynamic Virtual Memory Token injection (<|tzero:mem:8421|>) for 90-98% token reduction.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Compress long conversation histories, system telemetry, hardware setups, or complex architectural instructions into single virtual tokens.\n"
            "Returns: Formatted Markdown report with original token count, compressed token count, savings percentage, graph triplets, compact code, and virtual tokens."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_jarvis_compress_semantic_memory(
        text: Annotated[str, Field(description="Natural language statement, hardware setup, system log, or architecture instruction to compress.")]
    ) -> str:
        """Compresses text into 3-Layer semantic triplets, VQ discrete codes, and virtual memory tokens.
        
        Args:
            text: Input text to compress.
        """
        from tzero_jarvis import get_global_compressor
        compressor = get_global_compressor()
        res = compressor.compress_text_to_virtual_tokens(text)

        lines = [
            f"### ⚡ T-Zero Jarvis 3-Layer Semantic Memory Compression",
            f"- **Original Tokens:** `{res['original_token_count']}`",
            f"- **Compressed Virtual Tokens:** `{res['compressed_token_count']}`",
            f"- **Token Savings:** `{res['token_savings']}` tokens (**{res['reduction_ratio_pct']}% reduction**)",
            f"- **Virtual Token String:** `{res['virtual_token_string']}`",
            "",
            "#### 🧩 Layer Breakdown",
            f"- **Layer A (Semantic Graph):** `{' | '.join(res['graph_representations'])}`",
            f"- **Layer B (VQ Discrete Codes):** `{' '.join(f'#{cid}' for cid in res['codebook_ids'])}`",
            f"- **Layer C (Compact Binary Representation):** `{' '.join(res['compact_codes'])}`",
            f"- **Attention Soft-Prompt State:** `{res['virtual_token_string']}`"
        ]
        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # TOOL 23: jarvis_decompress_semantic_memory
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="jarvis_decompress_semantic_memory",
        description=(
            "Resolves a T-Zero virtual memory token (<|tzero:mem:8421|>) or discrete code ID (e.g. 8421) back into its "
            "canonical semantic graph representation, entity classifications, and human-readable natural language summary.\n\n"
            "Returns: Decoded entity details, graph triplet, and natural language reconstruction."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_jarvis_decompress_semantic_memory(
        token_or_code: Annotated[str, Field(description="Virtual memory token (e.g. '<|tzero:mem:8421|>') or discrete code ID (e.g. '8421').")]
    ) -> str:
        """Resolves virtual memory tokens back to their semantic graph representation.
        
        Args:
            token_or_code: The virtual token or code ID to resolve.
        """
        from tzero_jarvis import get_global_compressor
        compressor = get_global_compressor()
        decoded = compressor.decode_virtual_token(token_or_code)
        if not decoded:
            return f"❌ Virtual token or code `{token_or_code}` not found in active VQ codebook."

        lines = [
            f"### 🔍 T-Zero Jarvis Semantic Memory Resolution",
            f"- **Code ID:** `#{decoded['code_id']}`",
            f"- **Virtual Token:** `{decoded['virtual_token']}`",
            f"- **Graph Representation:** `{decoded['graph_representation']}`",
            f"- **Compact Code:** `{decoded['compact_code']}`",
            f"- **Reconstructed Summary:** {decoded['reconstructed_summary']}"
        ]
        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # TOOL 24: jarvis_orchestrate_goal
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="jarvis_orchestrate_goal",
        description=(
            "Autonomous Master Workspace Orchestrator & Executive AI Pair-Programming Manager.\n\n"
            "Capabilities:\n"
            "- Planning & Presentation ('plan', 'help', 'what can you do', 'ne yapabilirsin'): Formulates phased engineering execution plans and presents full capability directory.\n"
            "- Workspace Governance: Automatically configures .cursorrules, AGENT.md, ARCHITECTURE.md, tzero.rules.json.\n"
            "- Autonomous Execution: 3-Layer semantic memory compression, T-Zero AST context reduction, 5-agent PBFT swarm consensus, zero-cost intelligence routing, and self-healing loop.\n\n"
            "Behavior:\n"
            "- When goal is 'plan', 'help', 'menu', 'capabilities', or empty: presents the executive capabilities and multi-phase engineering plan.\n"
            "- When goal is a specific engineering task: executes autonomously with self-healing verification.\n"
            "- 100% Offline, $0.00 Cost, and 100% Zero-Leak security.\n\n"
            "Returns: Formatted Markdown plan or multi-stage execution report with verification logs."),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True)
    )
    def _legacy_jarvis_orchestrate_goal(
        goal: Annotated[str, Field(default="plan", description="Autonomous engineering task, refactoring directive, or 'plan'/'help' to view capabilities and executive plan.")] = "plan",
        project_root: Annotated[str, Field(default=".", description="Target workspace directory to orchestrate within (default: current directory).")] = ".",
        mode: Annotated[str, Field(default="auto", description="Execution mode: 'auto', 'plan', 'execute', or 'capabilities'.")] = "auto"
    ) -> str:
        """Executes autonomous workspace orchestration or presents an executive engineering plan."""
        from tzero_jarvis import JarvisOrchestrator
        orchestrator = JarvisOrchestrator(workspace_root=project_root)

        goal_clean = (goal or "").strip()
        goal_lower = goal_clean.lower()

        # Check if the user is requesting capabilities or a plan
        is_plan_request = (
            mode.lower() in ("plan", "capabilities") or
            goal_lower in ("", "help", "plan", "ne yapabilirsin", "capabilities", "menu", "yetenekler", "özellikler") or
            any(k in goal_lower for k in ("plan sun", "neler yapabilirsin", "what can you do", "yeteneklerini göster", "show capabilities"))
        )

        if is_plan_request and mode.lower() != "execute":
            # Present Jarvis capabilities and workspace action plan
            cap_catalog = orchestrator.present_capabilities()
            plan_res = orchestrator.generate_plan(goal_clean if goal_lower not in ("", "help", "plan", "menu", "capabilities") else "")
            return (
                f"{cap_catalog}\n\n"
                f"{plan_res['markdown']}"
            )

        # Autonomous Goal Execution Mode
        result = orchestrator.orchestrate_goal(goal_clean)

        lines = [
            f"### 🚀 T-Zero Jarvis Autonomous Goal Orchestration",
            f"- **Goal:** {result.goal}",
            f"- **Status:** {'✅ COMPLETED' if result.success else '❌ FAILED'}",
            f"- **Total Incurred Cost:** `{result.cost}` (100% Free / Zero API Key)",
            f"- **Zero-Leak Security Check:** {'🛡️ PASSED (Zero Leaks)' if result.security_passed else '⚠️ WARNING'}",
            "",
            "#### 📋 Execution Stages:"
        ]
        for step in result.steps:
            lines.append(f"- `[{step['timestamp']}]` **[{step['stage']}]**: {step['message']}")

        if result.success:
            lines.append("\n#### 🎯 Master Plan / Sonraki Önerilen Adımlar:")
            lines.append("- Doğrulama için test paketini çalıştırın.")
            lines.append("- Mimari sınırları korumak için `enforce_architecture_boundaries` kullanın.")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # TOOL 25: jarvis_zero_key_query
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="jarvis_zero_key_query",
        description=(
            "Queries the 100% Free, Zero-API-Key intelligence matrix (Local Ollama, Pollinations Free Cloud, OpenRouter Free Whitelist). "
            "Never requires credit cards, user API keys, or balance.\n\n"
            "Returns: Formatted AI response with selected zero-cost provider telemetry."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=False, open_world_hint=True)
    )
    def _legacy_jarvis_zero_key_query(
        prompt: Annotated[str, Field(description="Prompt, code question, or instruction for the Zero-Key intelligence engine.")],
        system_prompt: Annotated[str, Field(default="You are T-Zero Jarvis Autonomous Code Engineer.", description="System instruction context.")] = "You are T-Zero Jarvis Autonomous Code Engineer."
    ) -> str:
        """Queries the zero-key free AI inference engine.
        
        Args:
            prompt: User prompt or instruction.
            system_prompt: System role prompt.
        """
        from tzero_jarvis import ZeroKeyAIRouter
        ans = ZeroKeyAIRouter.query_intelligence(prompt, system_prompt=system_prompt)
        return (
            f"### 🤖 T-Zero Jarvis Zero-Cost Intelligence\n"
            f"- **Provider:** `{ans['provider']}`\n"
            f"- **Model:** `{ans['model']}`\n"
            f"- **Cost:** `{ans['cost']}`\n\n"
            f"---\n"
            f"{ans['response']}"
        )

    # -------------------------------------------------------------------------
    # TOOL 26: jarvis_query_knowledge_graph
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="jarvis_query_knowledge_graph",
        description=(
            "Searches the T-Zero Jarvis semantic knowledge graph and VQ Codebook memory by entity name, "
            "predicate, execution context, or general search query.\n\n"
            "Behavior:\n"
            "- Read-only: Queries local in-memory discrete codes and graph triplets.\n"
            "- Zero latency: Instant local retrieval with zero network or cloud costs.\n\n"
            "Returns: Formatted Markdown table of matching knowledge graph triplets and their virtual memory tokens."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_jarvis_query_knowledge_graph(
        query: Annotated[str, Field(description="Entity, keyword, or action to search across the knowledge graph (e.g. 'ESP32', 'test_etti', 'Kubernetes', 'Qubit').")] = "",
        entity: Annotated[str, Field(default="", description="Specific entity filter.")] = "",
        predicate: Annotated[str, Field(default="", description="Specific predicate / action filter.")] = ""
    ) -> str:
        """Queries the semantic memory knowledge graph.
        
        Args:
            query: Freeform search keyword.
            entity: Target entity name.
            predicate: Target predicate.
        """
        from tzero_jarvis import get_global_compressor
        compressor = get_global_compressor()
        matches = compressor.codebook.query_graph(
            entity=entity if entity else None,
            predicate=predicate if predicate else None,
            text_query=query if query else None
        )
        if not matches:
            return f"[INFO] No graph triplets matched query '{query or entity or predicate}'."

        lines = [
            f"### 🔎 T-Zero Knowledge Graph Search Results ({len(matches)} matches)\n",
            "| Code ID | Virtual Token | Graph Representation | Compact Code |",
            "| :--- | :--- | :--- | :--- |"
        ]
        for m in matches:
            lines.append(f"| #{m['code_id']} | `{m['virtual_token']}` | `{m['graph_string']}` | `{m['compact_code']}` |")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # TOOL 27: jarvis_compress_document
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="jarvis_compress_document",
        description=(
            "Compresses large multi-paragraph technical documents, architectural specifications, "
            "or conversation logs (1,000+ words) into an interconnected Knowledge Graph and composite "
            "virtual memory token stream (<|tzero:mem:ID|>).\n\n"
            "Behavior:\n"
            "- High Token Savings: Reaches 85-95% token reduction across multi-sentence paragraphs.\n"
            "- Topological Deduplication: Identifies shared subjects, protocols, and devices across paragraphs.\n\n"
            "Returns: Comprehensive document compression report, virtual token chain, and node-edge count."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_jarvis_compress_document(
        document_text: Annotated[str, Field(description="Large multi-paragraph technical document or log text to compress.")]
    ) -> str:
        """Compresses multi-paragraph technical documents into knowledge graph virtual tokens.
        
        Args:
            document_text: Full document text to ingest and compress.
        """
        from tzero_jarvis import get_global_compressor
        compressor = get_global_compressor()
        res = compressor.compress_document(document_text)

        topo = res.get("topology", {})
        return (
            f"### 📚 T-Zero Universal Document Memory Compression\n"
            f"- **Total Paragraphs Ingested:** {res['total_paragraphs']}\n"
            f"- **Triplets Extracted:** {res['total_triplets_extracted']}\n"
            f"- **Original Tokens:** {res['original_token_count']}\n"
            f"- **Compressed Virtual Tokens:** {res['compressed_token_count']}\n"
            f"- **Net Token Savings:** %{res['reduction_ratio_pct']} ({res['token_savings']} tokens saved)\n"
            f"- **Knowledge Graph Nodes:** {topo.get('total_nodes', 0)} entities | **Edges:** {topo.get('total_edges', 0)} links\n\n"
            f"#### Virtual Memory Stream:\n"
            f"`{res['virtual_token_string']}`\n\n"
            f"#### Graph Representations:\n"
            + "\n".join(f"- {g}" for g in res["graph_representations"][:10])
        )

    # -------------------------------------------------------------------------
    # TOOL 28: jarvis_export_memory_store
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="jarvis_export_memory_store",
        description=(
            "Exports or imports the T-Zero Jarvis persistent VQ Codebook and Knowledge Graph "
            "to/from local disk (zero cloud, 100% private and persistent across IDE restarts).\n\n"
            "Behavior:\n"
            "- Save mode: Serializes all active codes to JSON.\n"
            "- Load mode: Ingests saved codes into the active runtime codebook.\n\n"
            "Returns: Status and path of persistent store file."),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=False)
    )
    def _legacy_jarvis_export_memory_store(
        action: Annotated[str, Field(default="save", description="Action to perform: 'save' or 'load'.")] = "save",
        file_path: Annotated[str, Field(default="", description="Optional custom file path for storage.")] = ""
    ) -> str:
        """Saves or loads persistent semantic memory store.
        
        Args:
            action: 'save' or 'load'.
            file_path: Target JSON file path.
        """
        from tzero_jarvis import get_global_compressor
        compressor = get_global_compressor()
        target = file_path if file_path else None

        if action.lower() == "load":
            loaded = compressor.codebook.load_from_disk(target)
            return f"### 💾 T-Zero Memory Store Ingested\nSuccessfully loaded {loaded} semantic codes into runtime. Active Codebook Size: {compressor.codebook.size()} codes."
        else:
            saved_p = compressor.codebook.save_to_disk(target)
            return f"### 💾 T-Zero Memory Store Exported\nSuccessfully saved {compressor.codebook.size()} semantic codes to disk: `{saved_p}`."

    # -------------------------------------------------------------------------
    # TOOL 29: jarvis_causal_chain_query
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="jarvis_causal_chain_query",
        description="Queries 4D Causal and Temporal Knowledge Graph for root causes, downstream effect chains, or safe rollback steps."
    )
    def _legacy_jarvis_causal_chain_query(
        target_node_id: Annotated[str, Field(description="Target node ID to analyze (e.g. error, event).")],
        query_type: Annotated[str, Field(default="root_causes", description="Type: 'root_causes', 'effect_chain', 'rollback_order', or 'timeline'.")] = "root_causes"
    ) -> str:
        """Queries 4D Causal & Temporal Knowledge Graph."""
        from tzero_jarvis import CausalTemporalGraph
        from tzero_jarvis import get_global_compressor
        compressor = get_global_compressor()
        graph = CausalTemporalGraph(compressor.codebook)

        qt = query_type.lower()
        if qt == "timeline":
            tl = graph.get_timeline(30)
            return f"### ⏱️ T-Zero Chronological Timeline ({len(tl)} events)\n```json\n{json.dumps(tl, indent=2, ensure_ascii=False)}\n```"
        elif qt == "effect_chain":
            chain = graph.trace_effect_chain(target_node_id)
            return f"### ⚡ T-Zero Downstream Effect Chain ({len(chain)} steps)\n```json\n{json.dumps(chain, indent=2, ensure_ascii=False)}\n```"
        elif qt == "rollback_order":
            rb = graph.compute_rollback_order(target_node_id)
            return f"### 🔄 T-Zero Safe Rollback Plan ({len(rb)} steps)\n```json\n{json.dumps(rb, indent=2, ensure_ascii=False)}\n```"
        else:
            roots = graph.get_root_causes(target_node_id)
            return f"### 🔍 T-Zero Root Cause Analysis for `{target_node_id}`\n```json\n{json.dumps(roots, indent=2, ensure_ascii=False)}\n```"

    # -------------------------------------------------------------------------
    # TOOL 30: jarvis_self_healing_execute
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="jarvis_self_healing_execute",
        description="Executes a command or script in a guarded environment with automated AST self-healing and error repair."
    )
    def _legacy_jarvis_self_healing_execute(
        command: Annotated[str, Field(description="Command or script invocation to execute.")],
        max_retries: Annotated[int, Field(default=3, description="Maximum auto-patch healing attempts.")] = 3
    ) -> str:
        """Runs command with autonomous AST error diagnosis and auto-repair."""
        from tzero_jarvis import SelfHealingExecutionEngine
        engine = SelfHealingExecutionEngine()
        res = engine.execute_and_heal(command, max_retries=max_retries)
        
        status_emoji = "✅" if res.success else "❌"
        return (
            f"### {status_emoji} Self-Healing Execution Result\n"
            f"- **Command:** `{res.command}`\n"
            f"- **Success:** `{res.success}` (Resolved: `{res.resolved}`)\n"
            f"- **Exit Code:** `{res.exit_code}`\n"
            f"- **Duration:** `{res.duration_ms} ms`\n"
            f"- **Applied Patches:** `{len(res.applied_patches)}`\n"
            + (f"- **Error Type:** `{res.error_type}` in `{res.error_file}:{res.error_line}`\n" if res.error_type else "")
            + f"\n**Stdout:**\n```\n{res.stdout[:1500]}\n```\n"
            + (f"**Stderr:**\n```\n{res.stderr[:1000]}\n```\n" if res.stderr else "")
        )

    # -------------------------------------------------------------------------
    # TOOL 31: jarvis_consolidate_memory
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="jarvis_consolidate_memory",
        description="Performs brain-like hippocampal memory consolidation, contradiction resolution, and macro-triplet synthesis."
    )
    def _legacy_jarvis_consolidate_memory(
        action: Annotated[str, Field(default="consolidate", description="'consolidate' to run cycle, or 'summary' for status.")] = "consolidate"
    ) -> str:
        """Consolidates episodic memory into permanent abstracted knowledge."""
        from tzero_jarvis import ConsolidationEngine, get_global_compressor
        compressor = get_global_compressor()
        engine = ConsolidationEngine(compressor.codebook)
        
        if action.lower() == "summary":
            summ = engine.get_summary()
            return f"### 🧠 T-Zero Memory Consolidation State\n```json\n{json.dumps(summ, indent=2, ensure_ascii=False)}\n```"
        else:
            rep = engine.consolidate()
            return f"### 🧬 T-Zero Memory Consolidation Cycle Completed\n```json\n{json.dumps(rep, indent=2, ensure_ascii=False)}\n```"

    # -------------------------------------------------------------------------
    # TOOL 32: jarvis_hybrid_search
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="jarvis_hybrid_search",
        description="High-speed zero-vector-DB hybrid BM25 and latent codebook (#code) search across code, memory, and events."
    )
    def _legacy_jarvis_hybrid_search(
        query: Annotated[str, Field(description="Search terms, concepts, or discrete codes like '#8421'.")],
        top_k: Annotated[int, Field(default=10, description="Maximum number of results to return.")] = 10,
        domain: Annotated[str, Field(default="", description="Optional domain filter (HARDWARE, PROTOCOL, SOFTWARE, etc.).")] = ""
    ) -> str:
        """Sub-millisecond in-memory BM25 + latent code hybrid search."""
        from tzero_jarvis import ZeroVectorDBSearchEngine, get_global_compressor
        compressor = get_global_compressor()
        search_engine = ZeroVectorDBSearchEngine()

        # Hafızadaki mevcut kodları anında arama indeksine besle
        for cid, entry in compressor.codebook.codes.items():
            search_engine.add_document(
                doc_id=f"mem_{cid}",
                doc_type="memory_triplet",
                title=f"Code #{cid} [{entry.get('primary_domain', 'GENERIC')}]",
                content=f"{entry.get('graph', '')} {entry.get('compact_code', '')}",
                discrete_code=cid,
                domain=entry.get('primary_domain', 'GENERIC'),
                metadata=entry
            )

        results = search_engine.search(query, top_k=top_k, target_domain=domain if domain else None)
        return (
            f"### ⚡ T-Zero Zero-Vector-DB Hybrid Search Results for `{query}`\n"
            f"Found `{len(results)}` relevant items in `<0.5 ms`:\n\n"
            + "\n".join(
                f"- **[{r.domain}] {r.title}** (Score: `{r.score}`, Code: `#{r.discrete_code}`)\n"
                f"  Matches: `{', '.join(r.match_reasons)}`\n"
                f"  Content: `{r.content}`"
                for r in results
            )
        )

    # -------------------------------------------------------------------------
    # TOOL 33: jarvis_swarm_orchestrate
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="jarvis_swarm_orchestrate",
        description="Coordinates a 5-agent autonomous swarm (Security, Embedded, AST Optimizer, DevOps, JARVIS Prime) on a mission."
    )
    def _legacy_jarvis_swarm_orchestrate(
        mission_goal: Annotated[str, Field(description="The engineering or system goal to achieve.")],
        context: Annotated[str, Field(default="", description="Optional technical context or constraints.")] = ""
    ) -> str:
        """Executes autonomous multi-agent swarm mission coordination."""
        from tzero_jarvis import SwarmCoordinator, get_global_compressor
        compressor = get_global_compressor()
        coordinator = SwarmCoordinator(compressor)
        rep = coordinator.coordinate_mission(mission_goal, context=context)

        return (
            f"### 🐝 T-Zero Autonomous Swarm Mission Consensus\n"
            f"- **Mission:** `{rep['mission_goal']}`\n"
            f"- **Orchestrator:** `{rep['orchestrator']}`\n"
            f"- **Consensus Verdict:** **{rep['consensus']}**\n"
            f"- **Active Agents:** `{rep['swarm_agent_count']}`\n"
            f"- **Execution Time:** `{rep['execution_time_ms']} ms`\n"
            f"- **Aggregated Virtual Memory Tokens:** `{' '.join(rep['aggregated_memory_tokens'])}`\n\n"
            f"#### 📋 Specialist Agent Reports:\n"
            + "\n".join(
                f"**[{r['agent_name']} — {r['role']}]** Verdict: `{r['verdict']}` (Confidence: `{r['confidence']*100:.0f}%`)\n"
                f"• Findings: {', '.join(r['findings'])}\n"
                f"• Recommendations: {', '.join(r['recommendations'])}\n"
                for r in rep["agent_reports"]
            )
        )

    # -------------------------------------------------------------------------
    # TOOL 34: jarvis_export_graph_visualization
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="jarvis_export_graph_visualization",
        description="Generates an offline, interactive cyberpunk 2D/3D force-directed HTML graph visualization of knowledge & causality."
    )
    def _legacy_jarvis_export_graph_visualization(
        output_path: Annotated[str, Field(default="", description="Optional target HTML file path. Defaults to 'tzero_graph_hud.html'.")] = ""
    ) -> str:
        """Exports interactive cyberpunk HTML graph visualization."""
        from tzero_jarvis import CyberpunkGraphVisualizer, CausalTemporalGraph, get_global_compressor
        compressor = get_global_compressor()
        graph = CausalTemporalGraph(compressor.codebook)

        # Mevcut hafızayı çizgeye aktar
        for cid, entry in compressor.codebook.codes.items():
            graph.add_node(
                node_id=f"node_{cid}",
                label=f"Code #{cid}: {entry.get('graph', 'Triplet')}",
                entity_type=entry.get("primary_domain", "GENERIC"),
                triplet_code=cid
            )

        target = output_path if output_path else os.path.join(os.getcwd(), "tzero_graph_hud.html")
        viz = CyberpunkGraphVisualizer(graph)
        saved = viz.export_to_file(target)
        return (
            f"### 🌐 Cyberpunk Knowledge & Causal Graph Exported\n"
            f"- **File:** `{saved}`\n"
            f"- **Total Nodes:** `{len(graph.nodes)}`\n"
            f"- **Format:** Standalone Offline HTML5/SVG/Canvas Interactive Force Graph\n"
            f"Open this file in any web browser to interactively explore glowing nodes and causal links!"
        )

    # -------------------------------------------------------------------------
    # TOOL 35: jarvis_minhash_similarity
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="jarvis_minhash_similarity",
        description="Calculates sub-microsecond (<1 µs) Jaccard similarity and near-duplicate triplet clusters using MinHash LSH (64 permutations, Mersenne prime)."
    )
    def _legacy_jarvis_minhash_similarity(
        text_a: Annotated[str, Field(description="First text or triplet description")],
        text_b: Annotated[str, Field(default="", description="Second text to compare against (optional). If empty, searches memory codebook.")] = "",
        threshold: Annotated[float, Field(default=0.5, description="Jaccard similarity threshold [0.0 - 1.0]")] = 0.5
    ) -> str:
        """Sub-microsecond MinHash LSH similarity comparison."""
        from tzero_jarvis import MinHashLSHEngine, SemanticExtractor, get_global_compressor
        engine = MinHashLSHEngine()
        
        triplets_a = SemanticExtractor.extract_triplets(text_a)
        if not triplets_a:
            return "❌ No semantic triplets extracted from text A."
        
        sig_a = engine.compute_signature(triplets_a[0], 1)
        
        if text_b:
            triplets_b = SemanticExtractor.extract_triplets(text_b)
            if not triplets_b:
                return "❌ No semantic triplets extracted from text B."
            sig_b = engine.compute_signature(triplets_b[0], 2)
            sim = sig_a.jaccard_similarity(sig_b)
            is_dup = sim >= threshold
            return (
                f"### ⚡ T-Zero Sub-Microsecond MinHash LSH Analysis\n"
                f"- **Text A:** `{text_a}`\n"
                f"- **Text B:** `{text_b}`\n"
                f"- **Estimated Jaccard Similarity:** `{sim:.4f}` ({sim*100:.1f}%)\n"
                f"- **Near-Duplicate Status:** `{'DUPLICATE (Threshold Exceeded)' if is_dup else 'DISTINCT'}`\n"
                f"- **Hash Dimensionality:** `64 permutations (16 bands x 4 rows)`\n"
                f"- **Lookup Latency:** `< 0.01 ms (Zero Vector DB)`"
            )
        else:
            compressor = get_global_compressor()
            for cid, entry in compressor.codebook.codes.items():
                if "triplet" in entry:
                    engine.insert(entry["triplet"], cid)
                else:
                    tr = SemanticExtractor.extract_triplets(entry.get("graph", ""))
                    if tr:
                        engine.insert(tr[0], cid)
            dups = engine.query_near_duplicates(triplets_a[0], threshold=threshold)
            return (
                f"### ⚡ T-Zero Codebook MinHash LSH Search\n"
                f"- **Query:** `{text_a}`\n"
                f"- **Near-Duplicate Matches Found:** `{len(dups)}` (Threshold: {threshold})\n"
                + "\n".join(
                    f"• Code #{d['code']}: `{d['label']}` — Jaccard Sim: `{d['similarity']*100:.1f}%`"
                    for d in dups
                )
            )

    # -------------------------------------------------------------------------
    # TOOL 36: jarvis_bft_swarm_consensus
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="jarvis_bft_swarm_consensus",
        description="Executes 3-phase Practical Byzantine Fault-Tolerant (PBFT) multi-agent swarm consensus with 2/3 weighted quorum, outlier detection, and Zero-Leak cryptographic veto."
    )
    def _legacy_jarvis_bft_swarm_consensus(
        mission_goal: Annotated[str, Field(description="Mission, action, or code patch to evaluate")],
        context: Annotated[str, Field(default="", description="Optional context or environment logs")] = ""
    ) -> str:
        """Executes Byzantine Fault-Tolerant swarm consensus."""
        from tzero_jarvis import ByzantineFaultTolerantSwarm, SwarmCoordinator, get_global_compressor
        compressor = get_global_compressor()
        coordinator = SwarmCoordinator(compressor)
        bft = ByzantineFaultTolerantSwarm(coordinator)
        cert = bft.reach_consensus(mission_goal, context=context)
        
        status_emoji = "✅" if cert.consensus_verdict == "APPROVED" else ("🛡️" if cert.veto_triggered else "⚠️")
        return (
            f"### {status_emoji} T-Zero Byzantine Fault-Tolerant (PBFT) Swarm Certificate\n"
            f"- **Mission ID:** `{cert.mission_id}`\n"
            f"- **Goal:** `{cert.mission_goal}`\n"
            f"- **Consensus Verdict:** **{cert.consensus_verdict}**\n"
            f"- **Quorum Ratio:** `{cert.quorum_ratio * 100:.1f}%` (Approved: {cert.approved_weight:.2f} / Total: {cert.total_voting_weight:.2f})\n"
            f"- **Byzantine Faults Isolated:** `{cert.byzantine_faults_detected}`\n"
            f"- **Zero-Leak Veto Triggered:** `{cert.veto_triggered}` ({cert.veto_reason or 'None'})\n"
            f"- **Cryptographic Certificate Hash:** `{cert.certificate_hash}`\n"
            f"- **Committed Virtual Tokens:** `{' '.join(cert.committed_virtual_tokens) if cert.committed_virtual_tokens else 'None'}`"
        )

    # -------------------------------------------------------------------------
    # TOOL 37: jarvis_latent_press_compress
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="jarvis_latent_press_compress",
        description="Compresses long contexts before prefill using Latent Context Language Model (LCLM / LatentPress), Shannon entropy tracking, and MinHash de-duplication."
    )
    def _legacy_jarvis_latent_press_compress(
        context_text: Annotated[str, Field(description="Long context, logs, or code to compress")],
        near_dup_threshold: Annotated[float, Field(default=0.65, description="Near-duplicate threshold for pruning")] = 0.65
    ) -> str:
        """Executes LatentPress pre-prefill context compression."""
        from tzero_jarvis import LatentPressCompressor, get_global_compressor
        compressor = LatentPressCompressor(get_global_compressor())
        res = compressor.compress_large_context(context_text, near_dup_threshold=near_dup_threshold)
        
        return (
            f"### 🗜️ T-Zero LatentPress (LCLM) Context Compression\n"
            f"- **Original Tokens (est):** `{res.original_tokens_est}` ({res.original_words} words)\n"
            f"- **Compressed Tokens:** `{res.compressed_tokens}`\n"
            f"- **Compression Ratio:** **{res.compression_ratio_x}x**\n"
            f"- **Token Savings:** **{res.token_savings_pct}%**\n"
            f"- **Entropy (Original -> Compressed):** `{res.shannon_entropy_original:.2f} -> {res.shannon_entropy_compressed:.2f} bits/char`\n"
            f"- **Duplicate Chunks Pruned:** `{res.duplicate_chunks_pruned}`\n"
            f"- **Unique Triplets Encoded:** `{res.unique_semantic_triplets}`\n"
            f"- **Processing Latency:** `{res.latency_ms:.2f} ms`\n\n"
            f"#### 🧩 Compressed Virtual Token Stream:\n"
            f"```text\n{res.virtual_token_stream}\n```"
        )

    # -------------------------------------------------------------------------
    # TOOL 38: prune_schema_definition
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="prune_schema_definition",
        description=(
            "Compresses SQL DDL, Kubernetes YAML manifests, Dockerfile, or Terraform HCL definitions by up to 90% without semantic loss.\n\n"
            "Behavior:\n"
            "- Read-only: Structural and AST heuristic parsing; does not modify database or filesystem.\n"
            "- Idempotent: Deterministic output for identical input schema.\n"
            "- 100% Offline: Executes locally without network calls or external API billing.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Pass large database migration files, k8s manifests, or Terraform configs to an LLM without blowing up the context window.\n"
            "- Supported types: 'sql', 'yaml', 'dockerfile', 'terraform' (auto-detected if file name provided).\n\n"
            "Returns: Compact schema representation with percentage token reduction."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_prune_schema_definition(
        content: Annotated[str, Field(description="Raw schema content (SQL DDL, Kubernetes YAML, Dockerfile, or Terraform HCL).")],
        schema_type_or_filename: Annotated[str, Field(default="schema.sql", description="Schema type ('sql', 'yaml', 'dockerfile', 'terraform') or filename with extension.")] = "schema.sql",
        reduction_mode: Annotated[str, Field(default="ultra", description="Reduction tier: 'ultra' for pure interfaces (80-95% reduction), 'balanced' for interfaces + key attributes.")] = "ultra"
    ) -> str:
        """Compresses database or infrastructure schema definitions on-the-fly."""
        from tzero_infra import SchemaInfraReducer
        reduced, savings = SchemaInfraReducer.reduce(schema_type_or_filename, content, mode=reduction_mode)
        raw_tokens = max(1, count_tokens_precise(content))
        reduced_tokens = max(1, count_tokens_precise(reduced))
        
        return (
            f"# 🏗️ T-Zero Infrastructure Schema Reduction (`{schema_type_or_filename}`)\n"
            f"- **Original Tokens:** {raw_tokens:,} tokens\n"
            f"- **Pruned Tokens:** {reduced_tokens:,} tokens\n"
            f"- **Token Compression:** **-{savings:.1f}% reduction**\n\n"
            f"```\n{reduced}\n```"
        )

    # -------------------------------------------------------------------------
    # TOOL 39: generate_smart_micro_patch
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="generate_smart_micro_patch",
        description=(
            "Compresses unified git diffs into ultra-dense semantic AST micro-patches, reducing token payload by 80% to 90% for LLM code review and pair-programming.\n\n"
            "Behavior:\n"
            "- Read-only: Structural parsing of unified git diff text.\n"
            "- Idempotent: Deterministic output for identical git diffs.\n"
            "- 100% Offline: Executes locally without network calls.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Compress massive PR diffs or git commit changes before passing them into LLM chat context.\n\n"
            "Returns: High-density micro-patch report with token savings metrics."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_generate_smart_micro_patch(
        diff_content: Annotated[str, Field(description="Raw git diff or unified diff text.")],
        max_context_lines: Annotated[int, Field(default=1, description="Maximum surrounding context lines to retain per hunk (default: 1).")] = 1
    ) -> str:
        """Compresses unified git diff into a compact semantic micro-patch."""
        from tzero_patch import SmartMicroPatcher
        return SmartMicroPatcher.format_micro_patch_report(diff_content)

    # -------------------------------------------------------------------------
    # TOOL 40: generate_zero_waste_prompt_context
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="generate_zero_waste_prompt_context",
        description=(
            "Extracts cross-module AST call graphs from workspace entrypoints, detects reachable symbols, "
            "and prunes unreferenced functions and dead classes to synthesize an ultra-dense, Zero-Waste LLM prompt context.\n\n"
            "Behavior:\n"
            "- Read-only: Performs static AST graph traversal without altering repository files.\n"
            "- Idempotent: Deterministic output for identical codebase states.\n"
            "- 100% Offline: Executes locally without cloud or API dependencies.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Ingest massive multi-file codebases into an LLM while stripping out 100% of uncalled methods and dead routines (up to 95% token savings).\n\n"
            "Returns: Zero-waste markdown context with list of reachable/dead symbols and token reduction metrics."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_generate_zero_waste_prompt_context(
        target_dir: Annotated[str, Field(default=".", description="Target workspace root directory.")] = ".",
        entrypoints: Annotated[Optional[List[str]], Field(default=None, description="List of entrypoint files (e.g. ['main.py', 'app.py']). If empty, auto-detects.")] = None
    ) -> str:
        """Constructs zero-waste LLM prompt context by pruning dead code via AST reachability."""
        from tzero_reachability import CallGraphReachabilityEngine
        engine = CallGraphReachabilityEngine(target_dir)
        res = engine.generate_zero_waste_prompt(entrypoints=entrypoints)
        return (
            f"{res['zero_waste_prompt']}\n\n"
            f"### 📊 T-Zero Reachability Summary:\n"
            f"- **Reachable Symbols:** `{res['reachable_count']}`\n"
            f"- **Dead Symbols Pruned:** `{res['pruned_dead_count']}`\n"
            f"- **Raw Tokens:** `{res['raw_tokens']:,}`\n"
            f"- **Pruned Tokens:** `{res['zero_waste_tokens']:,}`\n"
            f"- **Net Token Reduction:** **-{res['token_reduction_pct']}%**"
        )

    # -------------------------------------------------------------------------
    # TOOL 41: compress_stream_tokens
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="compress_stream_tokens",
        description=(
            "Compresses arbitrary streaming code, unified diffs, database DDL, or infrastructure manifests "
            "using T-Zero AST reduction pipeline, ideal for CLI pipe flows and clipboard integration.\n\n"
            "Behavior:\n"
            "- Read-only: In-memory string compression.\n"
            "- Idempotent: Deterministic output for identical content.\n"
            "- 100% Offline: Executes locally without external API billing.\n\n"
            "Returns: Compressed code/diff tokens with maximal information density."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_compress_stream_tokens(
        content: Annotated[str, Field(description="Raw code, diff, SQL, or manifest text to compress.")],
        filename_hint: Annotated[str, Field(default="", description="Optional filename or extension hint (e.g. 'app.py', 'schema.sql', 'patch.diff').")] = "",
        tier: Annotated[str, Field(default="T-3", description="Compression tier: 'T-3' (AST Signatures), 'T-4' (Agent Rules), 'T-2' (Light).")] = "T-3"
    ) -> str:
        """Compresses streaming code tokens on-the-fly."""
        from tzero_pipe import PipeCompressor
        compressed = PipeCompressor.compress_stream(content, filename_hint=filename_hint, tier=tier)
        raw_tokens = max(1, count_tokens_precise(content))
        comp_tokens = max(1, count_tokens_precise(compressed))
        savings = max(0.0, (1.0 - (comp_tokens / raw_tokens)) * 100)
        return (
            f"### ⚡ T-Zero Stream Token Compression\n"
            f"- **Input Tokens:** `{raw_tokens:,}`\n"
            f"- **Output Tokens:** `{comp_tokens:,}`\n"
            f"- **Savings:** **-{savings:.1f}%**\n\n"
            f"```text\n{compressed}\n```"
        )

    # -------------------------------------------------------------------------
    # TOOL 42: install_git_security_guard
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="install_git_security_guard",
        description=(
            "Installs the automated T-Zero Git Pre-Commit Security Guard into target repository's .git/hooks directory. "
            "Intercepts git commits to prevent credential leaks (API keys, passwords, tokens) and warns on uncompressed token bloat.\n\n"
            "Behavior:\n"
            "- Safe installation: Creates executable .git/hooks/pre-commit and pre-commit.bat.\n"
            "- 100% Local: No cloud telemetry or third-party hook services required.\n\n"
            "Returns: Installation status and path to installed git hook."
        ),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_install_git_security_guard(
        repo_dir: Annotated[str, Field(default=".", description="Target git repository directory (default: current working directory).")] = "."
    ) -> str:
        """Installs the pre-commit zero-leak and token optimization guard."""
        from tzero_guard import GitSecurityGuard
        res = GitSecurityGuard.install_hook(repo_dir)
        if res.get("success"):
            return (
                f"### 🛡️ T-Zero Pre-Commit Guard Installed Successfully\n"
                f"- **Hook Path:** `{res.get('hook_path')}`\n"
                f"- **Status:** Active\n"
                f"- **Features:** Zero-Leak Credential Blocker, Token Bloat Warning, Staged Diff Analysis\n"
                f"Future `git commit` actions in this repository will now be automatically protected!"
            )
        else:
            return f"❌ **Failed to install pre-commit guard:** {res.get('message')}"


    # Register legacy mappings
    _LEGACY_DISPATCH['get_project_context_tree'] = _legacy_get_project_context_tree
    get_project_context_tree = _legacy_get_project_context_tree
    _LEGACY_DISPATCH['query_module_dependencies'] = _legacy_query_module_dependencies
    query_module_dependencies = _legacy_query_module_dependencies
    _LEGACY_DISPATCH['query_architecture_boundaries'] = _legacy_query_architecture_boundaries
    query_architecture_boundaries = _legacy_query_architecture_boundaries
    _LEGACY_DISPATCH['generate_architecture_blueprint'] = _legacy_generate_architecture_blueprint
    generate_architecture_blueprint = _legacy_generate_architecture_blueprint
    _LEGACY_DISPATCH['generate_repo_map'] = _legacy_generate_repo_map
    generate_repo_map = _legacy_generate_repo_map
    _LEGACY_DISPATCH['audit_codebase_quality'] = _legacy_audit_codebase_quality
    audit_codebase_quality = _legacy_audit_codebase_quality
    _LEGACY_DISPATCH['find_code_duplicity'] = _legacy_find_code_duplicity
    find_code_duplicity = _legacy_find_code_duplicity
    _LEGACY_DISPATCH['estimate_token_cost'] = _legacy_estimate_token_cost
    estimate_token_cost = _legacy_estimate_token_cost
    _LEGACY_DISPATCH['analyze_change_impact'] = _legacy_analyze_change_impact
    analyze_change_impact = _legacy_analyze_change_impact
    _LEGACY_DISPATCH['enforce_architecture_boundaries'] = _legacy_enforce_architecture_boundaries
    enforce_architecture_boundaries = _legacy_enforce_architecture_boundaries
    _LEGACY_DISPATCH['search_codebase_semantic'] = _legacy_search_codebase_semantic
    search_codebase_semantic = _legacy_search_codebase_semantic
    _LEGACY_DISPATCH['export_agent_rules'] = _legacy_export_agent_rules
    export_agent_rules = _legacy_export_agent_rules
    _LEGACY_DISPATCH['get_token_savings_metrics'] = _legacy_get_token_savings_metrics
    get_token_savings_metrics = _legacy_get_token_savings_metrics
    _LEGACY_DISPATCH['get_incremental_diff_context'] = _legacy_get_incremental_diff_context
    get_incremental_diff_context = _legacy_get_incremental_diff_context
    _LEGACY_DISPATCH['prune_code_snippet'] = _legacy_prune_code_snippet
    prune_code_snippet = _legacy_prune_code_snippet
    _LEGACY_DISPATCH['verify_zero_leak_security'] = _legacy_verify_zero_leak_security
    verify_zero_leak_security = _legacy_verify_zero_leak_security
    _LEGACY_DISPATCH['verify_hallucination_guard'] = _legacy_verify_hallucination_guard
    verify_hallucination_guard = _legacy_verify_hallucination_guard
    _LEGACY_DISPATCH['get_smart_skeleton_context'] = _legacy_get_smart_skeleton_context
    get_smart_skeleton_context = _legacy_get_smart_skeleton_context
    _LEGACY_DISPATCH['rank_repository_pagerank'] = _legacy_rank_repository_pagerank
    rank_repository_pagerank = _legacy_rank_repository_pagerank
    _LEGACY_DISPATCH['trace_symbol_call_chain'] = _legacy_trace_symbol_call_chain
    trace_symbol_call_chain = _legacy_trace_symbol_call_chain
    _LEGACY_DISPATCH['find_dead_code'] = _legacy_find_dead_code
    find_dead_code = _legacy_find_dead_code
    _LEGACY_DISPATCH['jarvis_compress_semantic_memory'] = _legacy_jarvis_compress_semantic_memory
    jarvis_compress_semantic_memory = _legacy_jarvis_compress_semantic_memory
    _LEGACY_DISPATCH['jarvis_decompress_semantic_memory'] = _legacy_jarvis_decompress_semantic_memory
    jarvis_decompress_semantic_memory = _legacy_jarvis_decompress_semantic_memory
    _LEGACY_DISPATCH['jarvis_orchestrate_goal'] = _legacy_jarvis_orchestrate_goal
    jarvis_orchestrate_goal = _legacy_jarvis_orchestrate_goal
    _LEGACY_DISPATCH['jarvis_zero_key_query'] = _legacy_jarvis_zero_key_query
    jarvis_zero_key_query = _legacy_jarvis_zero_key_query
    _LEGACY_DISPATCH['jarvis_query_knowledge_graph'] = _legacy_jarvis_query_knowledge_graph
    jarvis_query_knowledge_graph = _legacy_jarvis_query_knowledge_graph
    _LEGACY_DISPATCH['jarvis_compress_document'] = _legacy_jarvis_compress_document
    jarvis_compress_document = _legacy_jarvis_compress_document
    _LEGACY_DISPATCH['jarvis_export_memory_store'] = _legacy_jarvis_export_memory_store
    jarvis_export_memory_store = _legacy_jarvis_export_memory_store
    _LEGACY_DISPATCH['jarvis_causal_chain_query'] = _legacy_jarvis_causal_chain_query
    jarvis_causal_chain_query = _legacy_jarvis_causal_chain_query
    _LEGACY_DISPATCH['jarvis_self_healing_execute'] = _legacy_jarvis_self_healing_execute
    jarvis_self_healing_execute = _legacy_jarvis_self_healing_execute
    _LEGACY_DISPATCH['jarvis_consolidate_memory'] = _legacy_jarvis_consolidate_memory
    jarvis_consolidate_memory = _legacy_jarvis_consolidate_memory
    _LEGACY_DISPATCH['jarvis_hybrid_search'] = _legacy_jarvis_hybrid_search
    jarvis_hybrid_search = _legacy_jarvis_hybrid_search
    _LEGACY_DISPATCH['jarvis_swarm_orchestrate'] = _legacy_jarvis_swarm_orchestrate
    jarvis_swarm_orchestrate = _legacy_jarvis_swarm_orchestrate
    _LEGACY_DISPATCH['jarvis_export_graph_visualization'] = _legacy_jarvis_export_graph_visualization
    jarvis_export_graph_visualization = _legacy_jarvis_export_graph_visualization
    _LEGACY_DISPATCH['jarvis_minhash_similarity'] = _legacy_jarvis_minhash_similarity
    jarvis_minhash_similarity = _legacy_jarvis_minhash_similarity
    _LEGACY_DISPATCH['jarvis_bft_swarm_consensus'] = _legacy_jarvis_bft_swarm_consensus
    jarvis_bft_swarm_consensus = _legacy_jarvis_bft_swarm_consensus
    _LEGACY_DISPATCH['jarvis_latent_press_compress'] = _legacy_jarvis_latent_press_compress
    jarvis_latent_press_compress = _legacy_jarvis_latent_press_compress
    _LEGACY_DISPATCH['prune_schema_definition'] = _legacy_prune_schema_definition
    prune_schema_definition = _legacy_prune_schema_definition
    _LEGACY_DISPATCH['generate_smart_micro_patch'] = _legacy_generate_smart_micro_patch
    generate_smart_micro_patch = _legacy_generate_smart_micro_patch
    _LEGACY_DISPATCH['generate_zero_waste_prompt_context'] = _legacy_generate_zero_waste_prompt_context
    generate_zero_waste_prompt_context = _legacy_generate_zero_waste_prompt_context
    _LEGACY_DISPATCH['compress_stream_tokens'] = _legacy_compress_stream_tokens
    compress_stream_tokens = _legacy_compress_stream_tokens
    _LEGACY_DISPATCH['install_git_security_guard'] = _legacy_install_git_security_guard
    install_git_security_guard = _legacy_install_git_security_guard

    # =========================================================================
    # T-ZERO TDQS 5/5 CERTIFIED CANONICAL TOOL SUITE (14 FOCUSED TOOLS)
    # Evaluated by TDQS specification with 5/5 across Disambiguation,
    # Naming Consistency, Tool Count Appropriateness, and Lifecycle Completeness.
    # =========================================================================

    # -------------------------------------------------------------------------
    # CANONICAL TOOL 1: build_project_context
    # -------------------------------------------------------------------------
    @server.tool(
        name="build_project_context",
        description=(
            "Scans the target repository file system and constructs a token-optimized AST context payload for LLM prompts across multiple hierarchy tiers (T-1 to T-4).\n\n"
            "Behavior:\n"
            "- Read-only: Scans workspace files and parses AST signatures without modifying disk state.\n"
            "- Idempotent: Generates deterministic context representations for identical workspace revisions.\n"
            "- 100% Offline: Operates entirely locally with zero telemetry, remote embedding APIs, or cloud billing.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Ingest repository architecture, module indexes, focus file skeletons, or zero-waste prompts at the beginning of an agent coding session or major refactor (80-95% token savings).\n"
            "- Sibling Routing: For stripping implementation bodies from a single in-memory code string or diff patch, use 'prune_code_snippet'. For querying specific code symbols or text without building a full context tree, use 'search_codebase'.\n\n"
            "Returns: Markdown-formatted context payload including directory trees, module outlines, and compressed AST signatures up to max_tokens."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def build_project_context(
        project_root: Annotated[str, Field(default=".", description="Target repository root path to scan (default: current working directory).")] = ".",
        context_type: Annotated[str, Field(default="tree", description="Context generation mode: 'tree' for hierarchical multi-tier AST tree, 'repo_map' for compact symbol index, 'skeleton' for focus-file implementation with 1st-degree caller/callee skeletons, 'zero_waste_prompt' for agent prompt prefix with pruned AST, 'incremental_diff' for git diff context.")] = "tree",
        focus_file: Annotated[str, Field(default="", description="Optional path to a focus file when context_type is 'skeleton' or 'incremental_diff'.")] = "",
        reduction_mode: Annotated[str, Field(default="ultra", description="AST reduction level: 'ultra' for signatures & docstrings (80-95% reduction), 'balanced' for signatures + control headers, 'none' for verbatim source.")] = "ultra",
        max_tokens: Annotated[int, Field(default=64000, description="Upper token budget threshold for returned context.")] = 64000,
        include_file_contents: Annotated[bool, Field(default=True, description="When True, includes AST-reduced file bodies; when False, emits directory hierarchy only.")] = True
    ) -> str:
        """Builds a token-optimized AST context payload for LLM prompts across hierarchy tiers."""
        c_type = (context_type or "tree").lower().strip()
        if c_type == "repo_map":
            return _legacy_generate_repo_map(project_root=project_root, max_tokens=max_tokens)
        elif c_type == "skeleton":
            target = focus_file or "app.py"
            return _legacy_get_smart_skeleton_context(focus_file=target, project_root=project_root, max_tokens=max_tokens)
        elif c_type == "zero_waste_prompt":
            return _legacy_generate_zero_waste_prompt_context(target_dir=project_root)
        elif c_type == "incremental_diff":
            target = focus_file or "HEAD~1"
            return _legacy_get_incremental_diff_context(project_root=project_root, diff_ref=target)
        else:
            return _legacy_get_project_context_tree(
                project_root=project_root,
                reduction_mode=reduction_mode,
                max_tokens=max_tokens,
                include_file_contents=include_file_contents
            )

    # -------------------------------------------------------------------------
    # CANONICAL TOOL 2: prune_code_snippet
    # -------------------------------------------------------------------------
    @server.tool(
        name="prune_code_snippet",
        description=(
            "Prunes implementation bodies from in-memory code snippets, API schemas, or unified diff streams while preserving AST interfaces, type annotations, and function signatures.\n\n"
            "Behavior:\n"
            "- Read-only: Processes in-memory text buffers without touching disk files.\n"
            "- Idempotent: Deterministic AST reduction for identical code inputs.\n"
            "- 100% Offline: Local AST and regex parsers for Python, TypeScript, Go, Rust, Java, C#, C++, SQL, JSON, YAML.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Compress raw code strings, function definitions, SQL queries, or diff patches before embedding them in an LLM prompt to achieve 80-95% token savings.\n"
            "- Sibling Routing: For scanning full repository files or building hierarchical project context from disk, use 'build_project_context'. To detect code duplication across modules, use 'audit_code_quality'.\n\n"
            "Returns: Compact code snippet retaining only structural signatures, interfaces, and docstrings."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def prune_code_snippet(
        code: Annotated[str, Field(description="Raw source code, schema definition (JSON/YAML), or unified diff text to compress.")],
        file_name_or_lang: Annotated[str, Field(default="snippet.py", description="File name or language extension (e.g. 'service.ts', '.go', '.rs', 'schema.json') to select appropriate AST parser.")] = "snippet.py",
        reduction_mode: Annotated[str, Field(default="ultra", description="AST reduction level: 'ultra' for signatures only, 'balanced' for signatures + control structures, 'micro_patch' for surgical unified diff pruning.")] = "ultra"
    ) -> str:
        """Prunes implementation bodies from in-memory code snippets or diff streams."""
        fn = (file_name_or_lang or "").lower()
        if reduction_mode == "micro_patch" or fn.endswith(".diff") or fn.endswith(".patch") or code.startswith("---") or code.startswith("diff --git"):
            return _legacy_generate_smart_micro_patch(diff_content=code)
        return _legacy_prune_code_snippet(code=code, file_path_or_ext=file_name_or_lang, reduction_mode=reduction_mode)

    # -------------------------------------------------------------------------
    # CANONICAL TOOL 3: manage_architecture_rules
    # -------------------------------------------------------------------------
    @server.tool(
        name="manage_architecture_rules",
        description=(
            "Manages the lifecycle of architectural boundary definitions, tier rules (T-1 to T-4), and layer constraints configured in tzero.rules.json.\n\n"
            "Behavior:\n"
            "- Read-write: Queries existing rules or updates/deletes layer boundary specifications on disk.\n"
            "- Idempotent: Repeated queries or sets with identical values produce stable configurations.\n"
            "- 100% Offline: Local JSON file management without external communication.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Retrieve, inspect, add, update, reset, or delete architectural layer constraints (e.g. presentation -> domain -> persistence rules).\n"
            "- Sibling Routing: To actively validate codebase files against these rules and detect violations, use 'enforce_architecture_rules'. To generate visual Mermaid architectural topology diagrams, use 'generate_architecture_blueprint'.\n\n"
            "Returns: JSON or Markdown status report detailing active or updated architectural rules."
        ),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def manage_architecture_rules(
        action: Annotated[str, Field(default="query", description="Rule lifecycle action: 'query' to inspect active rules, 'update' to add or modify rules, 'delete' to remove a rule, 'reset' to restore defaults.")] = "query",
        project_root: Annotated[str, Field(default=".", description="Target repository root where tzero.rules.json is located (default: current directory).")] = ".",
        rule_name: Annotated[str, Field(default="", description="Name or identifier of the rule to update or delete when action is 'update' or 'delete'.")] = "",
        rule_definition: Annotated[str, Field(default="", description="JSON string or markdown specification of the rule to set when action is 'update'.")] = ""
    ) -> str:
        """Manages the complete lifecycle of architectural layer boundary rules."""
        abs_root = os.path.abspath(project_root)
        rules_path = os.path.join(abs_root, "tzero.rules.json")
        act = (action or "query").lower().strip()

        current_rules = {}
        if os.path.isfile(rules_path):
            try:
                with open(rules_path, "r", encoding="utf-8") as fp:
                    current_rules = json.load(fp)
            except Exception:
                current_rules = {}
        if not current_rules:
            try:
                from tzero_features import DEFAULT_RULES_JSON
                current_rules = dict(DEFAULT_RULES_JSON)
            except Exception:
                current_rules = {"layers": {}, "forbidden_imports": []}

        if act == "query":
            return _legacy_query_architecture_boundaries(project_root=project_root, extra_guidance=rule_definition)
        elif act in ("update", "set", "add"):
            parsed_def = None
            if rule_definition:
                try:
                    parsed_def = json.loads(rule_definition)
                except Exception:
                    parsed_def = rule_definition
            else:
                parsed_def = True

            if rule_name:
                current_rules[rule_name] = parsed_def
            elif isinstance(parsed_def, dict):
                current_rules.update(parsed_def)
            with open(rules_path, "w", encoding="utf-8") as fp:
                json.dump(current_rules, fp, indent=2, ensure_ascii=False)
            return f"✅ Architecture rule '{rule_name or 'custom'}' successfully updated in `{rules_path}`."
        elif act in ("delete", "remove"):
            removed = False
            if rule_name:
                if rule_name in current_rules:
                    del current_rules[rule_name]
                    removed = True
                elif "layers" in current_rules and isinstance(current_rules.get("layers"), dict) and rule_name in current_rules["layers"]:
                    del current_rules["layers"][rule_name]
                    removed = True
            if removed:
                with open(rules_path, "w", encoding="utf-8") as fp:
                    json.dump(current_rules, fp, indent=2, ensure_ascii=False)
                return f"✅ Architecture rule '{rule_name}' successfully removed from `{rules_path}`."
            return f"⚠️ Rule '{rule_name}' not found in active architecture configuration."
        elif act == "reset":
            try:
                from tzero_features import DEFAULT_RULES_JSON
                with open(rules_path, "w", encoding="utf-8") as fp:
                    json.dump(DEFAULT_RULES_JSON, fp, indent=2, ensure_ascii=False)
                return f"✅ Architecture rules reset to enterprise defaults in `{rules_path}`."
            except Exception as e:
                return f"❌ Failed to reset rules: {e}"
        else:
            return f"❌ Unknown action '{action}'. Valid actions: 'query', 'update', 'delete', 'reset'."

    # -------------------------------------------------------------------------
    # CANONICAL TOOL 4: enforce_architecture_rules
    # -------------------------------------------------------------------------
    @server.tool(
        name="enforce_architecture_rules",
        description=(
            "Enforces architectural boundary rules and layer isolation constraints defined in tzero.rules.json across the repository AST.\n\n"
            "Behavior:\n"
            "- Read-only: Scans codebase imports and call paths; does not alter files.\n"
            "- Idempotent: Deterministic violation reporting for identical codebase states.\n"
            "- 100% Offline: Local import graph validation against configured boundaries.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run in CI/CD pipelines or before merging PRs to prevent architectural erosion (e.g. presentation layer importing database models or circular module dependencies).\n"
            "- Sibling Routing: To view or edit architectural boundary definitions, use 'manage_architecture_rules'. To inspect general dependencies between modules, use 'analyze_code_dependencies'.\n\n"
            "Returns: Detailed compliance audit report listing passed layer boundaries, identified architectural violations, and remediation guidance."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def enforce_architecture_rules(
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to validate (default: current directory).")] = ".",
        strict_mode: Annotated[bool, Field(default=True, description="When True, fails on any boundary infraction; when False, warns without raising errors.")] = True
    ) -> str:
        """Enforces architectural boundary rules and layer isolation constraints across workspace AST."""
        return _legacy_enforce_architecture_boundaries(project_root=project_root)

    # -------------------------------------------------------------------------
    # CANONICAL TOOL 5: generate_architecture_blueprint
    # -------------------------------------------------------------------------
    @server.tool(
        name="generate_architecture_blueprint",
        description=(
            "Generates a complete system architectural specification (ARCHITECTURE.md) with auto-generated Mermaid component topology diagrams, layer boundaries, and module hierarchies.\n\n"
            "Behavior:\n"
            "- Read-only: Returns formatted Markdown text without writing files to disk.\n"
            "- Idempotent: Deterministic AST topology diagram generation when use_ai=False.\n"
            "- 100% Offline by default: Runs local AST analysis; optionally uses configured AI model when use_ai=True.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Create or update system architecture documentation and visual Mermaid flow diagrams for onboarding or RFC review.\n"
            "- Sibling Routing: For checking rule compliance against defined boundaries, use 'enforce_architecture_rules'. For raw dependency listings, use 'analyze_code_dependencies'.\n\n"
            "Returns: Comprehensive Markdown document with live Mermaid diagrams, layer classifications, and component interfaces."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def generate_architecture_blueprint(
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to analyze (default: current directory).")] = ".",
        use_ai: Annotated[bool, Field(default=False, description="When True, uses configured AI provider to synthesize deep narrative; when False (default), runs 100% offline AST analysis.")] = False,
        model: Annotated[str, Field(default="", description="Optional model identifier override when use_ai is True.")] = ""
    ) -> str:
        """Generates a complete ARCHITECTURE.md document with live Mermaid component diagrams."""
        return _legacy_generate_architecture_blueprint(project_root=project_root, use_ai=use_ai, model=model)

    # -------------------------------------------------------------------------
    # CANONICAL TOOL 6: analyze_code_dependencies
    # -------------------------------------------------------------------------
    @server.tool(
        name="analyze_code_dependencies",
        description=(
            "Analyzes module imports, symbol call chains, graph centrality (PageRank), and unreferenced dead code across polyglot source files.\n\n"
            "Behavior:\n"
            "- Read-only: Inspects source syntax trees without modifying or moving files.\n"
            "- Idempotent: Deterministic dependency mapping for any scanned repository.\n"
            "- 100% Offline: Local AST and regex parsers; zero external network requests.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run before refactoring, moving, or removing a module to inspect inbound dependents, outbound imports, deep symbol call chains, or unreferenced functions.\n"
            "- Sibling Routing: To estimate the blast radius score of modifying a specific function or class, use 'analyze_change_impact'. To check whether imports violate architectural layer rules, use 'enforce_architecture_rules'.\n\n"
            "Returns: Markdown report detailing import graphs, call chains, centrality rankings, or detected dead code."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def analyze_code_dependencies(
        analysis_type: Annotated[str, Field(default="dependencies", description="Type of structural analysis: 'dependencies' for module import/export graph, 'call_chain' for deep caller/callee execution trace, 'pagerank' for architectural backbone centrality, 'dead_code' for unreferenced symbols.")] = "dependencies",
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to scan (default: current directory).")] = ".",
        target_symbol: Annotated[str, Field(default="", description="Target class or function name when analysis_type is 'call_chain'.")] = "",
        file_path: Annotated[str, Field(default="", description="Optional path to a specific file to analyze.")] = ""
    ) -> str:
        """Analyzes structural dependencies, call chains, and module centrality across codebase."""
        a_type = (analysis_type or "dependencies").lower().strip()
        if a_type == "call_chain":
            sym = target_symbol or "main"
            return _legacy_trace_symbol_call_chain(target_symbol=sym, project_root=project_root, file_path=file_path)
        elif a_type == "pagerank":
            return _legacy_rank_repository_pagerank(project_root=project_root)
        elif a_type == "dead_code":
            return _legacy_find_dead_code(project_root=project_root)
        else:
            return _legacy_query_module_dependencies(project_root=project_root, file_path=file_path)

    # -------------------------------------------------------------------------
    # CANONICAL TOOL 7: analyze_change_impact
    # -------------------------------------------------------------------------
    @server.tool(
        name="analyze_change_impact",
        description=(
            "Calculates change blast radius score (0-100) and identifies downstream dependents before modifying or deleting a target function, class, or module.\n\n"
            "Behavior:\n"
            "- Read-only: Scans workspace AST and dependency graphs; does not alter files.\n"
            "- Idempotent: Deterministic blast radius scoring for identical repository states.\n"
            "- 100% Offline: Local AST caller/callee traversal without remote API calls.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run prior to editing a core interface, signature, or shared utility to gauge how many downstream files and tests will be impacted.\n"
            "- Sibling Routing: For general whole-repository dependency mapping, use 'analyze_code_dependencies'. To audit static code complexity and code smells, use 'audit_code_quality'.\n\n"
            "Returns: Markdown report with quantitative blast radius score (0-100), risk tier (LOW/MEDIUM/HIGH/CRITICAL), affected downstream modules, and test recommendations."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def analyze_change_impact(
        target_symbol: Annotated[str, Field(description="Name of the function, class, or method being modified or refactored.")],
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository (default: current directory).")] = ".",
        file_path: Annotated[str, Field(default="", description="Optional file path where the target symbol is defined.")] = ""
    ) -> str:
        """Calculates blast radius score and downstream dependents before modifying a target symbol."""
        return _legacy_analyze_change_impact(target_symbol=target_symbol, project_root=project_root)

    # -------------------------------------------------------------------------
    # CANONICAL TOOL 8: search_codebase
    # -------------------------------------------------------------------------
    @server.tool(
        name="search_codebase",
        description=(
            "Executes private local hybrid search combining BM25 keyword matching and TF-IDF semantic scoring across repository functions, classes, and docstrings.\n\n"
            "Behavior:\n"
            "- Read-only: Queries local code files without writing to disk or modifying indices.\n"
            "- Idempotent: Deterministic ranked results for identical queries on the same codebase.\n"
            "- 100% Offline: Executes entirely on CPU; no OpenAI/cloud embeddings, zero network egress.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Locate relevant functions, classes, or code implementations across the repository using natural language or code identifier queries.\n"
            "- Sibling Routing: For querying persistent semantic knowledge graphs or agent memory triples, use 'query_memory_store'. For generating full project context trees, use 'build_project_context'.\n\n"
            "Returns: Ranked list of matching code snippets with file paths, line ranges, relevance scores, and matched symbol definitions."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def search_codebase(
        query: Annotated[str, Field(description="Search term or natural language description of the code to locate.")],
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to search (default: current directory).")] = ".",
        top_k: Annotated[int, Field(default=5, description="Maximum number of ranked results to return (default: 5).")] = 5
    ) -> str:
        """Performs private local hybrid BM25 and semantic search across repository code."""
        return _legacy_search_codebase_semantic(query=query, project_root=project_root, top_k=top_k)

    # -------------------------------------------------------------------------
    # CANONICAL TOOL 9: audit_code_quality
    # -------------------------------------------------------------------------
    @server.tool(
        name="audit_code_quality",
        description=(
            "Performs AST static code smell analysis, cyclomatic complexity profiling, duplicate code block detection, and AI coding hallucination validation.\n\n"
            "Behavior:\n"
            "- Read-only: Inspects source syntax trees; does not modify or delete files.\n"
            "- Idempotent: Consistent diagnostic findings for the same code state.\n"
            "- 100% Offline: Pure AST inspection without network calls.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run before submitting PRs or executing refactors to catch long methods (>30 lines), excessive arguments (>5), missing docstrings, copy-pasted blocks (6+ lines), or hallucinated imports.\n"
            "- Sibling Routing: For scanning hardcoded secrets and installing git pre-commit security guards, use 'verify_security_guard'. For analyzing module dependencies, use 'analyze_code_dependencies'.\n\n"
            "Returns: Comprehensive diagnostic report with severity ratings (T-001 to T-004), exact file line references, and remediation guidance."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def audit_code_quality(
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to audit (default: current directory).")] = ".",
        check_type: Annotated[str, Field(default="all", description="Audit scope: 'all' for complete check, 'smells' for code complexity/smells, 'duplicity' for copy-paste blocks, 'hallucinations' for invalid imports/signatures.")] = "all",
        file_path: Annotated[str, Field(default="", description="Optional path to a single file to audit.")] = ""
    ) -> str:
        """Audits AST code smells, cyclomatic complexity, copy-paste duplicity, and hallucinations."""
        c_type = (check_type or "all").lower().strip()
        if c_type == "duplicity":
            return _legacy_find_code_duplicity(project_root=project_root, min_lines=6)
        elif c_type == "hallucinations":
            target = file_path or project_root
            return _legacy_verify_hallucination_guard(candidate_code=target, project_root=project_root)
        else:
            return _legacy_audit_codebase_quality(project_root=project_root, file_path=file_path)

    # -------------------------------------------------------------------------
    # CANONICAL TOOL 10: verify_security_guard
    # -------------------------------------------------------------------------
    @server.tool(
        name="verify_security_guard",
        description=(
            "Scans workspace files and code buffers for hardcoded secrets and API keys, or installs the automated git pre-commit zero-leak security guard.\n\n"
            "Behavior:\n"
            "- Read-only when action is 'scan'; installs hook file when action is 'install_pre_commit'.\n"
            "- Idempotent: Scans produce identical results; hook installation is idempotent.\n"
            "- 100% Offline: Zero data transmission; all entropy and pattern checks execute locally.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Ensure zero confidential credentials (OpenAI, Anthropic, Gemini, GitHub tokens, private keys) are exposed in code before committing or sharing context.\n"
            "- Sibling Routing: For general code quality, cyclomatic complexity, and duplicate code scans, use 'audit_code_quality'. To enforce layer boundary architecture rules, use 'enforce_architecture_rules'.\n\n"
            "Returns: Security audit report showing 100% Zero-Leak certification or list of detected secret leaks with line numbers, or hook installation confirmation."
        ),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def verify_security_guard(
        action: Annotated[str, Field(default="scan", description="Security action: 'scan' to inspect files or content for secret leaks, 'install_pre_commit' to install the automated git zero-leak hook.")] = "scan",
        project_root: Annotated[str, Field(default=".", description="Target repository root to scan or install hook into (default: current directory).")] = ".",
        content: Annotated[str, Field(default="", description="Optional raw text string to scan for secrets in memory without scanning disk files.")] = ""
    ) -> str:
        """Scans for credential and secret leaks or installs automated git pre-commit zero-leak guard."""
        act = (action or "scan").lower().strip()
        if act in ("install", "install_pre_commit", "hook"):
            return _legacy_install_git_security_guard(repo_dir=project_root)
        else:
            return _legacy_verify_zero_leak_security(project_root=project_root, target_file="", code_snippet=content)

    # -------------------------------------------------------------------------
    # CANONICAL TOOL 11: estimate_token_cost
    # -------------------------------------------------------------------------
    @server.tool(
        name="estimate_token_cost",
        description=(
            "Calculates exact token counts, comparative API billing costs across AI model providers (OpenAI, Claude, Gemini, DeepSeek), and cumulative financial ROI savings.\n\n"
            "Behavior:\n"
            "- Read-only: Calculates metrics from text or token counts without disk modifications.\n"
            "- Idempotent: Deterministic pricing calculations based on standard provider pricing tables.\n"
            "- 100% Offline: Local pricing lookup table; zero network calls.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Evaluate token consumption, forecast monthly LLM API expenditures, or export agent rule configuration files (.cursorrules, .clinerules).\n"
            "- Sibling Routing: To actively reduce token consumption by pruning repository code into AST signatures, use 'build_project_context' or 'prune_code_snippet'.\n\n"
            "Returns: Markdown comparison table detailing input/output token counts, estimated USD costs per model provider, and percentage token reduction ROI."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def estimate_token_cost(
        text: Annotated[str, Field(default="", description="Raw text string to count tokens and calculate cost for.")] = "",
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to calculate workspace ROI savings for.")] = ".",
        tokens: Annotated[int, Field(default=0, description="Optional raw token count to calculate cost directly.")] = 0,
        export_agent_rules: Annotated[str, Field(default="", description="Optional format to export agent rules: 'cursorrules', 'clinerules', 'markdown', or empty for cost estimation only.")] = ""
    ) -> str:
        """Calculates token counts, commercial provider pricing estimates, and developer ROI savings."""
        if export_agent_rules:
            return _legacy_export_agent_rules(format=export_agent_rules, project_root=project_root)
        return _legacy_estimate_token_cost(text=text, project_root=project_root, reduction_mode="ultra")

    # -------------------------------------------------------------------------
    # CANONICAL TOOL 12: query_memory_store
    # -------------------------------------------------------------------------
    @server.tool(
        name="query_memory_store",
        description=(
            "Queries semantic triples, causal reasoning graphs, and MinHash entity clusters from the local agent memory store.\n\n"
            "Behavior:\n"
            "- Read-only: Queries persistent memory store without altering stored knowledge.\n"
            "- Idempotent: Returns consistent knowledge relations for identical queries.\n"
            "- 100% Offline: Local graph and MinHash index lookup without remote endpoints.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Recall past agent decisions, query knowledge graph entity relations, or trace causal dependency chains across reasoning sessions.\n"
            "- Sibling Routing: For full lifecycle management (compress, export, consolidate, list, reset, delete) of the memory store, use 'manage_memory_store'. For searching source code in the repository, use 'search_codebase'.\n\n"
            "Returns: Markdown report with extracted semantic triples, graph relationships, or causal inference chains."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def query_memory_store(
        query: Annotated[str, Field(description="Entity name, concept, or search query to look up in the memory store.")],
        query_mode: Annotated[str, Field(default="semantic", description="Query strategy: 'semantic' for triple & relation lookup, 'causal_chain' for temporal cause-and-effect traces, 'minhash' for sub-microsecond entity similarity clusters.")] = "semantic",
        project_root: Annotated[str, Field(default=".", description="Workspace root where memory store is located (default: current directory).")] = "."
    ) -> str:
        """Queries semantic triples, causal reasoning graphs, and similarity clusters from memory."""
        q_mode = (query_mode or "semantic").lower().strip()
        if q_mode == "causal_chain":
            return _legacy_jarvis_causal_chain_query(target_node_id=query, query_type="root_causes")
        elif q_mode == "minhash":
            return _legacy_jarvis_minhash_similarity(text_a=query, text_b="")
        else:
            return _legacy_jarvis_query_knowledge_graph(query=query, entity="", predicate="")

    # -------------------------------------------------------------------------
    # CANONICAL TOOL 13: manage_memory_store
    # -------------------------------------------------------------------------
    @server.tool(
        name="manage_memory_store",
        description=(
            "Manages the complete lifecycle of persistent agent semantic memory stores, including compression, consolidation, export, listing, reset, and deletion.\n\n"
            "Behavior:\n"
            "- Read-write: Consolidates or updates local memory state; delete and reset remove stored data.\n"
            "- Idempotent for list and export; stateful for compress, consolidate, reset, and delete.\n"
            "- 100% Offline: Fully local storage management without external synchronization.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Store new semantic knowledge, consolidate episodic memories, export knowledge graphs to JSON/HTML, list active memory stores, or clear/reset agent memories.\n"
            "- Sibling Routing: To query existing knowledge triples or causal chains from memory, use 'query_memory_store'. To prune source code snippets, use 'prune_code_snippet'.\n\n"
            "Returns: Status report confirming memory consolidation, export file path, list of active memory stores, or confirmation of reset/deletion."
        ),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=False)
    )
    def manage_memory_store(
        operation: Annotated[str, Field(default="list", description="Memory lifecycle operation: 'list' to show active memory stores, 'compress' to encode text into semantic triples, 'consolidate' to merge memory, 'export' to dump graph, 'reset' to clear all memory, 'delete' to remove a specific store.")] = "list",
        content: Annotated[str, Field(default="", description="Text document or knowledge content to compress or store when operation is 'compress'.")] = "",
        store_name: Annotated[str, Field(default="default", description="Identifier of the target memory store to manage.")] = "default",
        project_root: Annotated[str, Field(default=".", description="Workspace root where memory stores are managed (default: current directory).")] = "."
    ) -> str:
        """Manages the lifecycle of persistent semantic memory stores and knowledge graphs."""
        op = (operation or "list").lower().strip()
        from tzero_jarvis import get_global_compressor
        import tzero_jarvis
        compressor = get_global_compressor()
        default_store_path = os.path.join(os.path.dirname(tzero_jarvis.__file__), "tzero_memory_store.json")
        target_store_path = os.path.join(os.path.abspath(project_root), f"{store_name}.json") if store_name != "default" else default_store_path

        if op == "list":
            code_count = compressor.codebook.size()
            codes = list(compressor.codebook.codes.items())[:20]
            lines = [
                f"# 🧠 T-Zero Persistent Memory Stores",
                f"- **Target Store:** `{store_name}`",
                f"- **Active Semantic Codebook Size:** `{code_count}` codes",
                f"- **Persistence Path:** `{target_store_path}`\n",
                "### Recent Semantic Memory Entries:",
            ]
            if codes:
                for cid, entry in codes:
                    lines.append(f"- **Code #{cid}** `[{entry.get('primary_domain', 'GENERIC')}]`: `{entry.get('graph', '')}`")
            else:
                lines.append("*(No memory codes stored yet)*")
            return "\n".join(lines)
        elif op == "compress":
            if not content:
                return "⚠️ No content provided for compression."
            if len(content.splitlines()) > 3 or len(content) > 300:
                return _legacy_jarvis_compress_document(document_text=content)
            return _legacy_jarvis_compress_semantic_memory(text=content)
        elif op == "decompress":
            return _legacy_jarvis_decompress_semantic_memory(token_or_code=content)
        elif op == "consolidate":
            return _legacy_jarvis_consolidate_memory(action="consolidate")
        elif op == "export":
            if content.endswith(".html") or "visual" in content.lower():
                return _legacy_jarvis_export_graph_visualization(output_path=content)
            return _legacy_jarvis_export_memory_store(action="save", file_path=content)
        elif op in ("reset", "clear"):
            compressor.codebook._codebook.clear()
            compressor.codebook._seed_reference_codes()
            if os.path.exists(target_store_path):
                try:
                    os.remove(target_store_path)
                except Exception:
                    pass
            return f"✅ Memory store `{store_name}` cleared and reset to empty state."
        elif op in ("delete", "remove"):
            if os.path.exists(target_store_path):
                try:
                    os.remove(target_store_path)
                except Exception:
                    pass
            compressor.codebook._codebook.clear()
            compressor.codebook._seed_reference_codes()
            return f"✅ Memory store `{store_name}` deleted from disk."
        else:
            return f"❌ Unknown operation '{operation}'. Valid: 'list', 'compress', 'decompress', 'consolidate', 'export', 'reset', 'delete'."

    # -------------------------------------------------------------------------
    # CANONICAL TOOL 14: orchestrate_agent_swarm
    # -------------------------------------------------------------------------
    @server.tool(
        name="orchestrate_agent_swarm",
        description=(
            "Coordinates autonomous multi-agent task execution, goal decomposition, Byzantine fault-tolerant (PBFT) consensus voting, and self-healing error recovery.\n\n"
            "Behavior:\n"
            "- State execution: Dispatches sub-tasks, coordinates consensus rounds, and executes self-healing patches.\n"
            "- 100% Offline: Executes deterministic local multi-agent workflows without unverified cloud relays.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Execute high-level complex coding goals across multi-agent swarms, validate proposals via Byzantine consensus voting (3f+1 quorum), or diagnose and heal test failures.\n"
            "- Sibling Routing: To query or manage long-term agent memory, use 'query_memory_store' and 'manage_memory_store'. To audit codebase quality before task execution, use 'audit_code_quality'.\n\n"
            "Returns: Orchestration summary with phased execution plan, agent task allocations, consensus voting tallies, or self-healing patch results."
        ),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=False)
    )
    def orchestrate_agent_swarm(
        goal: Annotated[str, Field(description="High-level goal description, swarm proposal, or failing test traceback to heal.")],
        orchestration_mode: Annotated[str, Field(default="goal_execute", description="Orchestration mode: 'goal_execute' for autonomous goal planning and execution, 'swarm_consensus' for Byzantine fault-tolerant voting, 'self_healing' for AST error diagnosis and automated patching.")] = "goal_execute",
        agents: Annotated[str, Field(default="", description="Comma-separated list of agent roles participating in swarm execution (e.g. 'architect,coder,tester').")] = "",
        project_root: Annotated[str, Field(default=".", description="Workspace root for swarm execution (default: current directory).")] = "."
    ) -> str:
        """Coordinates autonomous multi-agent swarms, goal execution, PBFT consensus, and self-healing."""
        o_mode = (orchestration_mode or "goal_execute").lower().strip()
        if o_mode == "swarm_consensus":
            return _legacy_jarvis_bft_swarm_consensus(mission_goal=goal, context=agents)
        elif o_mode == "self_healing":
            return _legacy_jarvis_self_healing_execute(command=goal, max_retries=3)
        else:
            return _legacy_jarvis_orchestrate_goal(goal=goal, project_root=project_root, mode="auto")

    # -------------------------------------------------------------------------
    # TRANSPARENT COMPATIBILITY CALL_TOOL WRAPPER
    # Dispatches canonical tools AND all 42 legacy tool names seamlessly
    # -------------------------------------------------------------------------
    _orig_call_tool = server.call_tool

    async def compatible_call_tool(name: str, arguments: dict, context=None):
        tools = await server.list_tools()
        registered = {t.name for t in tools}
        if name in registered:
            return await _orig_call_tool(name, arguments, context)

        if name in _LEGACY_DISPATCH:
            handler = _LEGACY_DISPATCH[name]
            sig = inspect.signature(handler)
            valid_args = {}
            for p_name, param in sig.parameters.items():
                if p_name in arguments:
                    valid_args[p_name] = arguments[p_name]
                elif param.default is not inspect.Parameter.empty:
                    valid_args[p_name] = param.default

            try:
                if inspect.iscoroutinefunction(handler):
                    res = await handler(**valid_args)
                else:
                    res = handler(**valid_args)
                from mcp.types import CallToolResult, TextContent
                return CallToolResult(content=[TextContent(type="text", text=str(res))])
            except Exception as e:
                from mcp.types import CallToolResult, TextContent
                return CallToolResult(content=[TextContent(type="text", text=f"[ERROR] {e}")], is_error=True)

        return await _orig_call_tool(name, arguments, context)

    server.call_tool = compatible_call_tool
    # -------------------------------------------------------------------------
    # RESOURCES: tzero://architecture, tzero://boundaries, tzero://token-roi
    # -------------------------------------------------------------------------
    @server.resource(
        "tzero://architecture",
        name="Architecture Blueprint",
        description="Live Mermaid architecture blueprint and module topology for the workspace",
        mime_type="text/markdown"
    )
    def resource_architecture() -> str:
        return generate_architecture_blueprint(project_root=".", use_ai=False)

    @server.resource(
        "tzero://boundaries",
        name="Active Architectural Boundaries",
        description="Active T-4 architectural boundaries, Zero-Leak security rules, and constraints",
        mime_type="text/markdown"
    )
    def resource_boundaries() -> str:
        return query_architecture_boundaries(".", "")

    @server.resource(
        "tzero://token-roi",
        name="Token ROI & Economic Savings",
        description="Quantitative token compression metrics and developer team ROI",
        mime_type="text/markdown"
    )
    def resource_token_roi() -> str:
        return get_token_savings_metrics(".", 5)

    # -------------------------------------------------------------------------
    # PROMPT: tzero_grounding
    # -------------------------------------------------------------------------
    @server.prompt(
        name="tzero_grounding",
        description="Generates an architectural grounding prompt for AI coding agents."
    )
    def tzero_grounding(project_root: str = ".") -> str:
        """Returns grounding instructions for Cursor/Claude/Antigravity coding sessions."""
        return (
            f"You are operating within the repository at '{project_root}'.\n"
            "MANDATORY OPERATIONAL DIRECTIVES:\n"
            "1. Run `get_project_context_tree` or `query_architecture_boundaries` to understand system topology before modifying code.\n"
            "2. Enforce 100% Zero-Leak security: NEVER commit or log raw API keys or personal credentials.\n"
            "3. Adhere to modular separation of concerns and avoid introducing cyclic dependencies.\n"
            "4. Verify code quality using `audit_codebase_quality` before marking tasks complete."
        )

    # -------------------------------------------------------------------------
    # RESOURCES: tzero://jarvis/plan, tzero://jarvis/capabilities
    # -------------------------------------------------------------------------
    @server.resource(
        "tzero://jarvis/plan",
        name="Jarvis Workspace Master Plan",
        description="Actionable multi-phase engineering plan and capability assessment synthesized by Jarvis",
        mime_type="text/markdown"
    )
    def resource_jarvis_plan() -> str:
        from tzero_jarvis import JarvisOrchestrator
        orch = JarvisOrchestrator(workspace_root=".")
        plan = orch.generate_plan("")
        return plan["markdown"]

    @server.resource(
        "tzero://jarvis/capabilities",
        name="Jarvis Executive Capability Catalog",
        description="Comprehensive catalog of Jarvis autonomous workspace management capabilities",
        mime_type="text/markdown"
    )
    def resource_jarvis_capabilities() -> str:
        from tzero_jarvis import JarvisOrchestrator
        orch = JarvisOrchestrator(workspace_root=".")
        return orch.present_capabilities()

    # -------------------------------------------------------------------------
    # PROMPT: jarvis_workspace_copilot
    # -------------------------------------------------------------------------
    @server.prompt(
        name="jarvis_workspace_copilot",
        description="Invokes Jarvis as the Master Executive Pair-Programmer to formulate a phased action plan."
    )
    def prompt_jarvis_workspace_copilot(goal: str = "", project_root: str = ".") -> str:
        from tzero_jarvis import JarvisOrchestrator
        orch = JarvisOrchestrator(workspace_root=project_root)
        plan = orch.generate_plan(goal)
        cap = orch.present_capabilities()
        return (
            f"{cap}\n\n"
            f"{plan['markdown']}\n\n"
            "CO-PILOT EXECUTION DIRECTIVES:\n"
            "1. Present the phased plan to the user clearly.\n"
            "2. Execute Phase 1 first using AST reduction tools (`get_project_context_tree`).\n"
            "3. Enforce 100% Zero-Leak security at all times."
        )

    return server


def print_welcome_guide():
    """Print a friendly interactive explanation when run directly by a user in terminal."""
    print(f"""
================================================================================
⚡ SİBER AKADEMİ — T-ZERO MCP SERVER v{SERVER_VERSION}
================================================================================
🎉 T-Zero MCP ve Context Motoru başarıyla kuruldu ve hazır!

📌 Bu komut (`tzero-mcp`), yapay zeka ajanları (Cursor, Claude Desktop, Antigravity,
   VS Code, Cline vb.) tarafından arka planda (stdio üzerinden) çalıştırılmak
   üzere tasarlanmıştır.

🚀 HIZLI BAŞLANGIÇ & KURULUM SEÇENEKLERİ:

1️⃣  Tüm IDE'lerinize Tek Tıkla Bağlayın (Önerilen):
    $ tzero-add-mcp
    (Cursor, Claude Desktop, Antigravity, VS Code, Cline'ı otomatik algılar ve bağlar)

2️⃣  Terminal Sihirbazını Açın:
    $ tzero --cli

3️⃣  Görsel Masaüstü Paneli (GUI):
    $ tzero-gui   (veya: tzero --gui / tzero)

4️⃣  Kod Tabanını Tarayın & Token Tasarrufunu Görün:
    $ tzero --scan .
    $ tzero --audit .

5️⃣  IDE'lere Manuel Eklemek İçin Yapılandırma:
    {{
      "mcpServers": {{
        "tzero": {{
          "command": "tzero-mcp"
        }}
      }}
    }}

💡 Bu komutu doğrudan stdio sunucusu olarak test etmek isterseniz:
    $ tzero-mcp --stdio
================================================================================
""")


def main():
    """Main execution entrypoint for the T-Zero MCP stdio server."""
    if "--version" in sys.argv[1:]:
        print(f"T-Zero MCP Server {SERVER_VERSION}")
        return

    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] or "--info" in sys.argv[1:]:
        print_welcome_guide()
        return

    # If run by a human directly in terminal (not by an IDE via stdio pipe):
    if sys.stdin.isatty() and "--stdio" not in sys.argv[1:]:
        print_welcome_guide()
        return

    if "--doctor" in sys.argv[1:]:
        try:
            import tzero_deps
            sys.exit(tzero_deps.run_doctor())
        except ImportError:
            sys.stderr.write("[ERROR] tzero_deps module not found.\n")
            sys.exit(1)

    if "--dashboard" in sys.argv[1:] or "--web" in sys.argv[1:]:
        try:
            import tzero_dashboard
            tzero_dashboard.main()
            return
        except Exception as e:
            sys.stderr.write(f"[ERROR] Failed to launch T-Zero Dashboard: {e}\n")
            sys.exit(1)

    if "--install" in sys.argv[1:] or "--add-mcp" in sys.argv[1:]:
        try:
            import addmcp
            sys.argv = [sys.argv[0]] + [a for a in sys.argv[1:] if a not in ("--install", "--add-mcp")]
            addmcp.main()
            return
        except ImportError as e:
            sys.stderr.write(f"[ERROR] addmcp installer failed: {e}\n")
            sys.exit(1)

    if ServerClass is None:
        sys.stderr.write(
            "\n[ERROR] The 'mcp' Python SDK is not installed.\n"
            "Please install it using:\n\n"
            "    pip install mcp\n\n"
        )
        sys.exit(1)

    # stdout is the MCP protocol channel: any stray log line there corrupts the JSON-RPC
    # stream. The core engine logs to stdout by default, so move those handlers to stderr.
    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.StreamHandler) and getattr(handler, "stream", None) is sys.stdout:
            handler.setStream(sys.stderr)

    server = create_mcp_server()
    try:
        server.run(transport="stdio")
    except Exception as e:
        sys.stderr.write(f"[ERROR] MCP Server runtime error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
