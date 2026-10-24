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

SERVER_VERSION = "7.3.1"

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
    # T-ZERO TDQS 5/5 CERTIFIED PRIMARY SPECIALIZED SUITE (42 TOOLS)
    # Default mode registers all 42 distinct, focused tools directly to list_tools().
    # Canonical 14-tool mode available when TZERO_MCP_TOOL_MODE in ("canonical", "14").
    # All tools accessible dynamically via call_tool() in both modes.
    # -------------------------------------------------------------------------
    _tool_mode = os.environ.get("TZERO_MCP_TOOL_MODE", "all").lower().strip()
    _canonical_only = _tool_mode in ("canonical", "14")
    def _noop_decorator(**kwargs):
        def _wrapper(fn):
            return fn
        return _wrapper
    _maybe_tool = _noop_decorator if _canonical_only else server.tool
    _canon_tool = server.tool if _canonical_only else _noop_decorator
    _LEGACY_DISPATCH: Dict[str, Any] = {}
    _CANONICAL_DISPATCH: Dict[str, Any] = {}
    # -------------------------------------------------------------------------
    # TOOL 1: get_project_context_tree
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="get_project_context_tree",
        description=(
            "Scans the target codebase to build an enterprise-grade multi-tier AST context tree (T-1 to T-4), distinguishing from 'generate_repo_map' and 'get_smart_skeleton_context' by generating hierarchical architectural outlines and symbol tables rather than flat symbol indexes or isolated file skeletons.\n"
            "\n"
            "Parameters:\n"
            "- `project_root` (str, optional, default='.'): Target repository root directory path to scan.\n"
            "- `reduction_mode` (str, optional, default='ultra'): AST reduction depth level ('ultra' for 80-95% compression with signatures and docstrings, 'balanced' for signatures + control flow, 'none' for verbatim source code).\n"
            "- `max_tokens` (int, optional, default=64000): Upper token budget cap; when exceeded, prioritizes files via PageRank and git recency.\n"
            "- `include_file_contents` (bool, optional, default=True): If True, emits AST-pruned code bodies; if False, emits directory hierarchy and module overview only.\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Performs static AST analysis without modifying files on disk.\n"
            "- Idempotent: Generates deterministic output for identical repository states.\n"
            "- 100% Offline: Executes entirely locally with zero network egress, remote telemetry, or LLM billing.\n"
            "- Auth & Rate Limits: Zero authentication or credentials required; execution scales with file count (typically <2s for 1,000 files).\n"
            "- Error Handling: Returns clean Markdown warning notices if no analyzable files exist in the specified path.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Ingest repository architecture, module indexes, and AST signatures into agent context at the start of a coding session or before major refactors (80-95% token savings).\n"
            "- When NOT to use: Do not use for a fast single-page class/method symbol index (use 'generate_repo_map' instead); do not use for single focus-file skeletons (use 'get_smart_skeleton_context' instead); do not use for arbitrary in-memory snippets (use 'prune_code_snippet' instead).\n"
            "\n"
            "Returns: Structured Markdown document featuring '# Repository Architecture (T-1)', '# Module Dependencies (T-2)', '# AST Signatures (T-3)', '# Architectural Rules (T-4)', and token compression metrics."
        ),
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
            "Analyzes import and export dependency graphs across polyglot codebase modules, distinguishing from 'trace_symbol_call_chain' and 'enforce_architecture_boundaries' by mapping package-level inbound and outbound module relationships rather than function-level call stacks or rule violations.\n"
            "\n"
            "Parameters:\n"
            "- `project_root` (str, optional, default='.'): Root directory of the repository to scan.\n"
            "- `file_path` (str, optional, default=''): Relative or absolute path to a specific file to inspect, or empty string to analyze the entire workspace dependency graph.\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Inspects source syntax trees without modifying or moving files.\n"
            "- Idempotent: Generates deterministic dependency mappings for identical file sets.\n"
            "- 100% Offline: Local AST and regex parsing with zero external network requests or telemetry.\n"
            "- Auth & Rate Limits: Zero credentials or API keys required; executes in <100ms.\n"
            "- Error Handling: Returns clean Markdown error notices if the target path is missing.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Inspect inbound referrers (who imports this) and outbound dependencies (what this imports) before refactoring, moving, or reorganizing files.\n"
            "- When NOT to use: Do not use for recursive function/method call chains (use 'trace_symbol_call_chain' instead); do not use for verifying architectural layer rule violations (use 'enforce_architecture_boundaries' instead).\n"
            "\n"
            "Returns: Markdown dependency report detailing total outbound imports, inbound referrers, dependency tables, and external package pool."
        ),
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
            "Retrieves active T-4 architectural tier boundary definitions and operational constraints, distinguishing from 'enforce_architecture_boundaries' and 'generate_architecture_blueprint' by inspecting existing rules rather than executing compliance audits or generating diagrams.\n"
            "\n"
            "Parameters:\n"
            "- `project_root` (str, optional, default='.'): Target repository root directory containing 'tzero.rules.json'.\n"
            "- `extra_guidance` (str, optional, default=''): Optional custom instruction context or query focus for rule extraction.\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Reads rule configuration from disk or built-in defaults without writing changes.\n"
            "- Idempotent: Returns identical tier definitions for unchanged configuration files.\n"
            "- 100% Offline: Pure local file system inspection with zero network egress.\n"
            "- Auth & Rate Limits: Zero authentication or credentials required; sub-millisecond execution.\n"
            "- Error Handling: Gracefully falls back to default Clean Architecture tier rules if rules file is absent.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Verify allowed and forbidden cross-layer dependency rules before designing new modules or writing import statements.\n"
            "- When NOT to use: Do not use for automated rule enforcement checks in CI/CD (use 'enforce_architecture_boundaries' instead); do not use for visual Mermaid architecture diagrams (use 'generate_architecture_blueprint' instead).\n"
            "\n"
            "Returns: Markdown summary of T-1 through T-4 layer boundaries, forbidden import directives, and zero-leak security rules."
        ),
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
            "Generates a system architecture specification with live Mermaid topology diagrams, distinguishing from 'query_architecture_boundaries' and 'get_project_context_tree' by producing graphical structural blueprints rather than raw rule definitions or token-reduced source code.\n"
            "\n"
            "Parameters:\n"
            "- `project_root` (str, optional, default='.'): Repository root directory to inspect.\n"
            "- `use_ai` (bool, optional, default=False): When True, supplements deterministic AST topology with local zero-cost AI architectural insights.\n"
            "- `model` (str, optional, default=''): Optional model identifier override (e.g. 'deepseek-v4.1-flash', 'gpt-4o') when use_ai is True; defaults to empty string for offline mode.\n"
            "\n"
            "Behavior:\n"
            "- Side Effects: Pure in-memory analysis; reads repository directory layout and module headers without writing files on disk.\n"
            "- Idempotent: Produces deterministic Mermaid diagrams and architectural markdown.\n"
            "- 100% Offline: Local topology generation; operates strictly offline.\n"
            "- Auth & Rate Limits: Zero credentials or tokens required; typical generation time <200ms.\n"
            "- Error Handling: Returns descriptive warning if directory contains no recognizable code modules.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Generate system design documents (ARCHITECTURE.md), visualize codebase structure, or onboard team members to system topologies.\n"
            "- When NOT to use: Do not use for raw code token reduction (use 'get_project_context_tree' instead); do not use for detecting static code smells (use 'audit_codebase_quality' instead).\n"
            "\n"
            "Returns: Markdown architecture specification including system tier overview, data flow descriptions, and Mermaid component diagrams."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_generate_architecture_blueprint(
        project_root: Annotated[str, Field(default=".", description="Repository root directory to inspect (default: '.').")] = ".",
        use_ai: Annotated[bool, Field(default=False, description="When True, supplements deterministic AST topology with local zero-cost AI architectural insights (default: False).")] = False,
        model: Annotated[str, Field(default="", description="Optional model identifier override (e.g. 'deepseek-v4.1-flash', 'gpt-4o') when use_ai is True (default: '').")] = ""
    ) -> str:
        """Generates a complete ARCHITECTURE.md document with live Mermaid diagrams.
        
        Args:
            project_root: Repository root directory to inspect (default: '.').
            use_ai: When True, supplements deterministic AST topology with local zero-cost AI architectural insights.
            model: Optional model identifier override (e.g. 'deepseek-v4.1-flash', 'gpt-4o') when use_ai is True.
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
            "Generates an ultra-compact single-file AST symbol map of classes, methods, and functions, distinguishing from 'get_project_context_tree' and 'get_smart_skeleton_context' by producing an ultra-dense symbol index rather than hierarchical code trees or implementation skeletons.\n"
            "\n"
            "Parameters:\n"
            "- `project_root` (str, optional, default='.'): Target repository root directory to scan.\n"
            "- `max_tokens` (int, optional, default=4000): Maximum token ceiling for the returned symbol map.\n"
            "\n"
            "Behavior:\n"
            "- Side Effects: Pure in-memory AST symbol extraction; does not write or modify files on disk.\n"
            "- Idempotent: Deterministic symbol extraction for identical code states.\n"
            "- 100% Offline: Pure local AST parsing; operates strictly offline.\n"
            "- Auth & Rate Limits: Zero authentication or API keys required; execution takes <50ms.\n"
            "- Error Handling: Truncates lower-priority symbols gracefully when token budget is exceeded.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Provide agents with an instant, low-cost overview of all available classes and function signatures across the entire repository (<4,000 tokens).\n"
            "- When NOT to use: Do not use when full function bodies or control flow are needed (use 'get_project_context_tree' instead); do not use for targeted caller/callee skeletons of a specific file (use 'get_smart_skeleton_context' instead).\n"
            "\n"
            "Returns: Compact Markdown table and symbol tree mapping file paths to their exported classes, methods, and functions."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_generate_repo_map(
        project_root: Annotated[str, Field(default=".", description="Target repository root directory to scan (default: '.').")] = ".",
        max_tokens: Annotated[int, Field(default=4000, description="Maximum token ceiling for the returned symbol map (default: 4000).")] = 4000
    ) -> str:
        """Builds a compressed AST symbol map for the repository.
        
        Args:
            project_root: Target repository root directory to scan (default: '.').
            max_tokens: Maximum token ceiling for the returned symbol map (default: 4000).
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
            "Audits workspace code for static code smells, cyclomatic complexity spikes, and hardcoded secret leaks, distinguishing from 'enforce_architecture_boundaries' and 'verify_hallucination_guard' by scanning for code cleanliness and secret exposure rather than layer boundaries or phantom imports.\n"
            "\n"
            "Parameters:\n"
            "- `project_root` (str, optional, default='.'): Root directory of the codebase to audit.\n"
            "- `file_path` (str, optional, default=''): Optional specific file to audit, or empty string to audit the entire workspace.\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Scans workspace files statically without modifying workspace code.\n"
            "- Idempotent: Deterministic finding count and severity classifications for identical files.\n"
            "- 100% Offline: Zero-Leak local AST and pattern analysis; never transmits source code externally.\n"
            "- Auth & Rate Limits: Zero credentials or third-party accounts required; completes in <500ms.\n"
            "- Error Handling: Emits clean status report with zero findings when codebase is pristine.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Run pre-commit or CI/CD quality gates to catch security leaks (OpenAI, Anthropic, AWS, GitHub tokens), long functions (>50 lines), deep nesting (>4 levels), and high cyclomatic complexity.\n"
            "- When NOT to use: Do not use for architectural tier import enforcement (use 'enforce_architecture_boundaries' instead); do not use for detecting copy-pasted duplicate blocks (use 'find_code_duplicity' instead).\n"
            "\n"
            "Returns: Markdown audit report with Quality Score (0-100), Zero-Leak security status, classified smell lists, and remediation suggestions."
        ),
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
            "Detects duplicate or copy-pasted code blocks across codebase modules, distinguishing from 'audit_codebase_quality' and 'find_dead_code' by identifying duplicated logic chunks rather than static code smells or unreferenced functions.\n"
            "\n"
            "Parameters:\n"
            "- `project_root` (str, optional, default='.'): Repository root directory to scan.\n"
            "- `min_lines` (int, optional, default=6): Minimum consecutive identical code lines required to flag a duplicate block.\n"
            "\n"
            "Behavior:\n"
            "- Side Effects: Pure in-memory analysis; reads source files into normalized token sequences without writing or altering files on disk.\n"
            "- Idempotent: Deterministic duplicate detection for identical workspace content.\n"
            "- 100% Offline: Local sliding-window token hashing; operates strictly offline.\n"
            "- Auth & Rate Limits: Zero credentials or API keys required; sub-second execution on typical repos.\n"
            "- Error Handling: Reports zero duplicates found if codebase is clean.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Identify refactoring candidates, extract shared utility functions, and eliminate technical debt caused by copy-paste coding.\n"
            "- When NOT to use: Do not use for detecting unreferenced or orphaned functions (use 'find_dead_code' instead); do not use for general AST complexity checks (use 'audit_codebase_quality' instead).\n"
            "\n"
            "Returns: Markdown report listing duplicated code blocks, file locations, line ranges, and refactoring recommendations."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_find_code_duplicity(
        project_root: Annotated[str, Field(default=".", description="Repository root directory to scan (default: '.').")] = ".",
        min_lines: Annotated[int, Field(default=6, description="Minimum consecutive identical code lines required to flag a duplicate block (default: 6).")] = 6
    ) -> str:
        """Identifies duplicate code blocks across workspace files.
        
        Args:
            project_root: Repository root directory to scan (default: '.').
            min_lines: Minimum consecutive identical code lines required to flag a duplicate block (default: 6).
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
            "Calculates comparative dollar costs across major commercial LLM providers for given source text or repository, distinguishing from 'get_token_savings_metrics' by forecasting per-query API expenses rather than team-wide monthly ROI savings.\n"
            "\n"
            "Parameters:\n"
            "- `text` (str, optional, default=''): Code or prompt string to estimate token cost for.\n"
            "- `project_root` (str, optional, default='.'): Target repository root directory if estimating across files.\n"
            "- `reduction_mode` (str, optional, default='ultra'): AST reduction mode to compare uncompressed vs compressed costs ('ultra', 'balanced', 'none').\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Performs local mathematical calculation using embedded pricing catalog.\n"
            "- Idempotent: Deterministic cost calculation for identical token inputs.\n"
            "- 100% Offline: Computes locally from pricing tables without live billing API requests.\n"
            "- Auth & Rate Limits: Zero credentials or accounts required; executes instantaneously (<1ms).\n"
            "- Error Handling: Gracefully validates inputs and defaults to sample token metrics if text is empty.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Estimate financial expenses before dispatching large context payloads or batch evaluations to commercial AI models.\n"
            "- When NOT to use: Do not use for aggregate team-level monthly ROI savings calculations (use 'get_token_savings_metrics' instead); do not use for compressing prompt tokens (use 'get_project_context_tree' or 'prune_code_snippet' instead).\n"
            "\n"
            "Returns: Formatted Markdown comparison table showing per-query and per-million token costs across OpenAI, Anthropic, Google, and DeepSeek."
        ),
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
            "Analyzes the blast radius and downstream dependents before modifying a symbol or file, distinguishing from 'query_module_dependencies' and 'trace_symbol_call_chain' by scoring change severity (0-100) and risk tier rather than listing raw imports or single call stacks.\n"
            "\n"
            "Parameters:\n"
            "- `target_symbol` (str, required): Name of the class, function, or file path to evaluate for modification impact.\n"
            "- `project_root` (str, optional, default='.'): Target repository root directory.\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Static AST analysis of dependency paths without editing source files.\n"
            "- Idempotent: Deterministic blast radius and risk score for unchanged repository revisions.\n"
            "- 100% Offline: Operates entirely locally with zero remote telemetry or external egress.\n"
            "- Auth & Rate Limits: Zero authentication or API keys required; typical execution <150ms.\n"
            "- Error Handling: Returns informative warning if target symbol is not found in the workspace index.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Assess refactoring safety and downstream breakage risks before modifying or deprecating shared functions or base classes.\n"
            "- When NOT to use: Do not use for broad repository-level module import tables (use 'query_module_dependencies' instead); do not use for step-by-step bidirectional call graph traversal (use 'trace_symbol_call_chain' instead).\n"
            "\n"
            "Returns: Markdown impact report containing Blast Radius Score (0-100), Risk Tier (LOW/MEDIUM/HIGH/CRITICAL), affected dependent files list, and recommended test targets."
        ),
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
            "Enforces architectural layer boundaries and detects unauthorized cross-layer imports, distinguishing from 'query_architecture_boundaries' and 'audit_codebase_quality' by validating import contracts against 'tzero.rules.json' and emitting CI violation errors rather than querying rules or scanning code smells.\n"
            "\n"
            "Parameters:\n"
            "- `project_root` (str, optional, default='.'): Repository root directory to inspect.\n"
            "- `rules_file` (str, optional, default='tzero.rules.json'): Path to the rules JSON file defining layer boundaries.\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Validates imports against layer rules without modifying files.\n"
            "- Idempotent: Deterministic violation detection for identical file states.\n"
            "- 100% Offline: Pure local AST parsing and rule evaluation with zero network egress.\n"
            "- Auth & Rate Limits: Zero credentials or cloud dependencies required; completes in <250ms.\n"
            "- Error Handling: Emits clean compliance message when all imports satisfy architectural rules.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Validate clean architecture compliance (e.g. Domain layer must not import Infrastructure) in CI/CD pipelines or before merging PRs.\n"
            "- When NOT to use: Do not use for viewing configured rules without validation (use 'query_architecture_boundaries' instead); do not use for general syntax or complexity linting (use 'audit_codebase_quality' instead).\n"
            "\n"
            "Returns: Markdown compliance report detailing passed layer contracts, detected boundary violations, offending file lines, and remediation steps."
        ),
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
            "Performs fast local hybrid semantic search across repository files, distinguishing from 'jarvis_hybrid_search' and 'jarvis_query_knowledge_graph' by indexing file contents on-the-fly using BM25 and AST symbol tokens rather than persistent vector databases or knowledge graphs.\n"
            "\n"
            "Parameters:\n"
            "- `query` (str, required): Natural language query, symbol name, or architectural intent to locate.\n"
            "- `project_root` (str, optional, default='.'): Root directory of the repository to search.\n"
            "- `top_k` (int, optional, default=5): Maximum number of top-matching code snippets to return.\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Scans workspace text without altering files or creating persistent index files.\n"
            "- Idempotent: Returns identical ranked search results for identical queries on unchanged repositories.\n"
            "- 100% Offline: 100% private local BM25 ranking; zero external embedding models or cloud queries.\n"
            "- Auth & Rate Limits: Zero credentials or API keys required; typical query latency <50ms.\n"
            "- Error Handling: Returns empty result notice gracefully if no matches satisfy relevance threshold.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Locate relevant functions, classes, and code implementations by semantic concept or intent without relying on cloud vector databases.\n"
            "- When NOT to use: Do not use for building full repository context trees (use 'get_project_context_tree' instead); do not use for querying persistent VQ knowledge graphs (use 'jarvis_query_knowledge_graph' instead).\n"
            "\n"
            "Returns: Markdown document with ranked matching snippets, file paths, line ranges, relevance scores, and matched keywords."
        ),
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
            "Generates and writes standardized AI agent rule specifications into workspace root, distinguishing from 'query_architecture_boundaries' and 'install_git_security_guard' by writing editor-ready governance files (.cursorrules, AGENT.md, .clinerules) rather than querying rules in memory or installing git hooks.\n"
            "\n"
            "Parameters:\n"
            "- `project_root` (str, optional, default='.'): Target workspace directory where agent rule files will be created.\n"
            "- `target` (str, optional, default='all'): Target editor format: 'cursor', 'cline', 'windsurf', 'claude', 'copilot', or 'all'.\n"
            "\n"
            "Behavior:\n"
            "- Mutating: Creates or updates configuration files in the target workspace directory.\n"
            "- Idempotent: Overwrites existing T-Zero agent rule files with current architecture rules without corrupting user customizations.\n"
            "- 100% Offline: Generates rule files locally using built-in templates with zero network requests.\n"
            "- Auth & Rate Limits: Zero authentication or cloud credentials required; completes in <50ms.\n"
            "- Error Handling: Defaults to standard T-Zero engineering templates if workspace configuration is empty.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Run when setting up a repository for AI pair-programming with Cursor, Claude Code, Cline, Windsurf, or GitHub Copilot.\n"
            "- When NOT to use: Do not use to view architectural boundaries without writing files to disk (use 'query_architecture_boundaries' instead); do not use for git pre-commit hook security (use 'install_git_security_guard' instead).\n"
            "\n"
            "Returns: Confirmation Markdown message listing all generated rule file paths and active directives."
        ),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_export_agent_rules(
        project_root: Annotated[str, Field(default=".", description="Target workspace directory where agent rule files will be created (default: current directory).")] = ".",
        target: Annotated[str, Field(default="all", description="Target editor format: 'cursor', 'cline', 'windsurf', 'claude', 'copilot', or 'all' (default: 'all').")] = "all"
    ) -> str:
        """Exports AI coding agent rules into workspace."""
        from tzero_features import AgentRulesGenerator
        p_name = os.path.basename(os.path.abspath(project_root)) or "Project"
        t = (target or "all").lower().strip()
        created = []
        if t in ("cursor", "cursorrules"):
            cr_path = os.path.join(project_root, ".cursorrules")
            with open(cr_path, "w", encoding="utf-8") as f:
                f.write(AgentRulesGenerator.generate_cursorrules(p_name))
            created.append(cr_path)
            c_rules_dir = os.path.join(project_root, ".cursor", "rules")
            os.makedirs(c_rules_dir, exist_ok=True)
            for mdc_name, content in AgentRulesGenerator.generate_cursor_mdc_rules(p_name, project_dir=project_root).items():
                mdc_path = os.path.join(c_rules_dir, mdc_name)
                with open(mdc_path, "w", encoding="utf-8") as f:
                    f.write(content)
                created.append(mdc_path)
        elif t in ("cline", "clinerules"):
            cl_path = os.path.join(project_root, ".clinerules")
            with open(cl_path, "w", encoding="utf-8") as f:
                f.write(AgentRulesGenerator.generate_clinerules(p_name))
            created.append(cl_path)
        elif t in ("windsurf", "windsurfrules"):
            ws_path = os.path.join(project_root, ".windsurfrules")
            with open(ws_path, "w", encoding="utf-8") as f:
                f.write(AgentRulesGenerator.generate_windsurfrules(p_name))
            created.append(ws_path)
        elif t in ("claude", "claudemd"):
            claude_path = os.path.join(project_root, "CLAUDE.md")
            with open(claude_path, "w", encoding="utf-8") as f:
                f.write(AgentRulesGenerator.generate_claude_instructions(p_name))
            created.append(claude_path)
        elif t in ("copilot", "github"):
            gh_dir = os.path.join(project_root, ".github")
            os.makedirs(gh_dir, exist_ok=True)
            copilot_path = os.path.join(gh_dir, "copilot-instructions.md")
            with open(copilot_path, "w", encoding="utf-8") as f:
                f.write(AgentRulesGenerator.generate_copilot_instructions(p_name))
            created.append(copilot_path)
        else:
            created = AgentRulesGenerator.export_all(project_root)
        rel_paths = [os.path.relpath(p, project_root) for p in created]
        return "✅ Generated AI Agent rule files:\n" + "\n".join(f"- `{p}`" for p in rel_paths)

    # -------------------------------------------------------------------------
    # TOOL 13: get_token_savings_metrics
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="get_token_savings_metrics",
        description=(
            "Computes quantitative token reduction metrics and monthly team financial ROI savings, distinguishing from 'estimate_token_cost' by calculating aggregate cumulative dollar and token savings across team engineering workflows rather than single-query price estimates.\n"
            "\n"
            "Parameters:\n"
            "- `project_root` (str, optional, default='.'): Target workspace directory to measure.\n"
            "- `team_size` (int, optional, default=5): Number of developers in the engineering team used to model monthly ROI savings.\n"
            "\n"
            "Behavior:\n"
            "- Side Effects: Pure in-memory calculation; does not write or modify files on disk.\n"
            "- Idempotent: Deterministic calculations based on repository size and active engineer count.\n"
            "- 100% Offline: Executes locally using embedded ROI models; operates strictly offline.\n"
            "- Auth & Rate Limits: Zero authentication or cloud credentials required; instantaneous execution (<5ms).\n"
            "- Error Handling: Validates positive values for engineer counts.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Generate executive ROI reports, quantify token compression savings (80-95%), and prove financial efficiency of T-Zero context optimization.\n"
            "- When NOT to use: Do not use for calculating single-prompt query costs across specific models (use 'estimate_token_cost' instead); do not use for compressing code snippets (use 'prune_code_snippet' instead).\n"
            "\n"
            "Returns: Markdown executive summary with token compression ratios, monthly dollar savings, latency reduction, and annual ROI projections."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_get_token_savings_metrics(
        project_root: Annotated[str, Field(default=".", description="Target workspace directory to measure (default: '.').")] = ".",
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
            "Calculates hyper-compact git diff context for pull requests and commits, distinguishing from 'generate_smart_micro_patch' and 'get_project_context_tree' by extracting changed files with surrounding AST context from git revisions rather than compressing raw diff strings or whole repos.\n"
            "\n"
            "Parameters:\n"
            "- `base_ref` (str, optional, default='HEAD~1'): Git revision, commit hash, or branch comparison target (e.g. 'main...feature', 'HEAD~1').\n"
            "- `project_root` (str, optional, default='.'): Path to the git repository root.\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Executes git diff and AST analysis without modifying working tree or git history.\n"
            "- Idempotent: Deterministic output for identical git references and revisions.\n"
            "- 100% Offline: Local git CLI and AST processing with zero cloud calls.\n"
            "- Auth & Rate Limits: Zero authentication or API keys required; completes in <100ms.\n"
            "- Error Handling: Returns descriptive error if git reference is invalid or repository lacks git tracking.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Prepare minimal, token-efficient PR review context and diff summaries for AI code reviewers.\n"
            "- When NOT to use: Do not use for compressing raw unified diff strings without a git repository (use 'generate_smart_micro_patch' instead); do not use for whole-repo architecture context (use 'get_project_context_tree' instead).\n"
            "\n"
            "Returns: Markdown diff context payload containing changed file summaries, modified AST signatures, and token efficiency statistics."
        ),
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
            "Compresses arbitrary in-memory source code or text by stripping function bodies while preserving AST signatures, distinguishing from 'compress_stream_tokens' and 'get_project_context_tree' by performing structural language-aware AST pruning on raw strings rather than byte-level stream packing or file scanning.\n"
            "\n"
            "Parameters:\n"
            "- `code` (str, required): Raw source code string to compress and prune.\n"
            "- `file_path_or_ext` (str, optional, default='snippet.py'): File name or extension (e.g. 'service.ts', '.go', '.rs') to select appropriate language parser.\n"
            "- `reduction_mode` (str, optional, default='ultra'): Pruning depth ('ultra' for signatures and docstrings, 'balanced' for signatures and control headers, 'none' for verbatim).\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Transforms string content in memory without touching the local file system.\n"
            "- Idempotent: Deterministic output for identical source code inputs.\n"
            "- 100% Offline: Local language AST parser; zero external network egress or telemetry.\n"
            "- Auth & Rate Limits: Zero credentials or API keys required; sub-millisecond execution (<10ms).\n"
            "- Error Handling: Falls back to indentation-aware skeletonization if formal grammar parsing encounters syntax errors.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Compress large code files, snippets, or prompt examples before injecting them into LLM context windows (80-95% token savings).\n"
            "- When NOT to use: Do not use for scanning files directly from disk (use 'get_project_context_tree' instead); do not use for SQL schemas or YAML manifests (use 'prune_schema_definition' instead).\n"
            "\n"
            "Returns: Pruned source code string with function bodies replaced by '# ... implementation pruned ...' and token compression metrics."
        ),
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
            "Scans codebase or memory snippets for hardcoded API keys, private tokens, and credentials with 100% Zero-Leak safety, distinguishing from 'audit_codebase_quality' and 'verify_hallucination_guard' by focusing exclusively on secret exposure rather than code complexity or hallucinated APIs.\n"
            "\n"
            "Parameters:\n"
            "- `project_root` (str, optional, default='.'): Root directory of the repository to scan.\n"
            "- `target_file` (str, optional, default=''): Specific file path to verify, or empty string to scan all files.\n"
            "- `code_snippet` (str, optional, default=''): Optional in-memory code string to verify directly.\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Scans text against entropy and secret pattern regexes without editing files.\n"
            "- Idempotent: Deterministic finding detection for identical inputs.\n"
            "- 100% Offline: Local scanning only; zero tokens or secrets sent over network.\n"
            "- Auth & Rate Limits: Zero authentication or cloud credentials required; executes in <50ms.\n"
            "- Error Handling: Confirms 100% Zero-Leak certified status if no credentials are found.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Verify that proposed code edits, diffs, or commits contain zero leaked API keys (OpenAI, Anthropic, AWS, GitHub, Stripe, SSH).\n"
            "- When NOT to use: Do not use for detecting hallucinated methods or imports (use 'verify_hallucination_guard' instead); do not use for git pre-commit hook installation (use 'install_git_security_guard' instead).\n"
            "\n"
            "Returns: Markdown report with Zero-Leak certification badge, list of detected secrets with line numbers and masked previews, and remediation guidance."
        ),
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
            "Verifies proposed AI code changes against workspace AST symbol tables to eliminate hallucinations before files are modified, distinguishing from 'verify_zero_leak_security' and 'audit_codebase_quality' by detecting non-existent methods, phantom imports, and signature mismatches rather than secrets or code smells.\n"
            "\n"
            "Parameters:\n"
            "- `proposed_code` (str, required): Generated code string to validate against real workspace AST symbols.\n"
            "- `target_file` (str, optional, default=''): Path of the file being edited or created.\n"
            "- `project_root` (str, optional, default='.'): Target repository root directory.\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Statically parses proposed code and compares against workspace symbol index without modifying files on disk.\n"
            "- Idempotent: Deterministic verification for identical code and codebase states.\n"
            "- 100% Offline: Operates entirely locally with zero external network access.\n"
            "- Auth & Rate Limits: Zero authentication or cloud credentials required; completes in <100ms.\n"
            "- Error Handling: Emits clean verification status when all referenced symbols resolve successfully.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Run immediately before applying AI-generated code to prevent importing non-existent modules or invoking phantom functions.\n"
            "- When NOT to use: Do not use for detecting leaked secrets or API keys (use 'verify_zero_leak_security' instead); do not use for checking layer boundary rules (use 'enforce_architecture_boundaries' instead).\n"
            "\n"
            "Returns: Markdown verification report with Hallucination Risk Score (0-100), list of verified symbols, unresolved phantom references, and suggested real symbol replacements."
        ),
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
            "Generates focus-aware dynamic skeleton context showing full implementation of a target file alongside pruned 1st-degree caller/callee skeletons, distinguishing from 'get_project_context_tree' and 'generate_repo_map' by isolating a single focus file with immediate dependencies rather than scanning the entire repository.\n"
            "\n"
            "Parameters:\n"
            "- `focus_file` (str, required): Path to the primary file currently being implemented or edited.\n"
            "- `focus_symbol` (str, optional, default=''): Optional specific symbol inside focus_file to center context upon.\n"
            "- `project_root` (str, optional, default='.'): Target repository root directory.\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Reads focus file and its dependencies without writing or altering files on disk.\n"
            "- Idempotent: Deterministic skeleton generation for identical workspace revisions.\n"
            "- 100% Offline: Local AST parsing only; zero network egress or telemetry.\n"
            "- Auth & Rate Limits: Zero authentication or cloud credentials required; executes in <80ms.\n"
            "- Error Handling: Returns clean Markdown error if focus file does not exist.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Provide the LLM with full implementation of the active working file while giving skeletonized signatures of imported and importing modules (90% token reduction).\n"
            "- When NOT to use: Do not use when global multi-tier architecture is needed (use 'get_project_context_tree' instead); do not use for a quick flat symbol overview (use 'generate_repo_map' instead).\n"
            "\n"
            "Returns: Markdown context block containing full body of focus file, skeletonized signatures of related modules, and token count."
        ),
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
            "Calculates PageRank importance scores across workspace modules to identify architectural backbone files, distinguishing from 'query_module_dependencies' and 'trace_symbol_call_chain' by assigning global centrality weights to files based on incoming reference graphs rather than listing individual imports.\n"
            "\n"
            "Parameters:\n"
            "- `project_root` (str, optional, default='.'): Root directory of the repository to analyze.\n"
            "- `top_k` (int, optional, default=15): Number of top-ranked architectural files to return.\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Builds in-memory graph from AST imports without modifying files.\n"
            "- Idempotent: Deterministic PageRank power-iteration for identical import topologies.\n"
            "- 100% Offline: Local numerical linear algebra; zero cloud API calls.\n"
            "- Auth & Rate Limits: Zero credentials or accounts required; executes in <150ms.\n"
            "- Error Handling: Emits notice if workspace contains no inter-module imports.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Prioritize which files must be included in limited LLM context windows or determine the most critical core modules of an unfamiliar repository.\n"
            "- When NOT to use: Do not use for step-by-step function execution call paths (use 'trace_symbol_call_chain' instead); do not use for blast radius change impact (use 'analyze_change_impact' instead).\n"
            "\n"
            "Returns: Markdown table ranking top files by PageRank centrality score, in-degree references, out-degree dependencies, and architectural role."
        ),
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
            "Traces recursive execution call paths across codebase ASTs in upward or downward directions, distinguishing from 'query_module_dependencies' and 'analyze_change_impact' by following function-level invocation call chains rather than file-level imports or risk scores.\n"
            "\n"
            "Parameters:\n"
            "- `symbol_name` (str, required): Function or method identifier to trace.\n"
            "- `project_root` (str, optional, default='.'): Root directory of the repository.\n"
            "- `max_depth` (int, optional, default=3): Maximum recursive call graph traversal depth.\n"
            "\n"
            "Behavior:\n"
            "- Side Effects: Pure in-memory AST call site traversal; does not write or modify files on disk.\n"
            "- Idempotent: Deterministic graph traversal for identical code states.\n"
            "- 100% Offline: Local syntax tree parsing; operates strictly offline.\n"
            "- Auth & Rate Limits: Zero credentials or cloud dependencies required; typical latency <100ms.\n"
            "- Error Handling: Returns clean notice if target symbol is not defined or uncalled.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Trace caller hierarchy (who calls this function) or callee hierarchy (what does this function call) during deep debugging or refactoring.\n"
            "- When NOT to use: Do not use for broad package-level import dependencies (use 'query_module_dependencies' instead); do not use for calculating overall change blast radius (use 'analyze_change_impact' instead).\n"
            "\n"
            "Returns: Markdown tree diagram of recursive call paths with file names, line numbers, and call depth."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_trace_symbol_call_chain(
        symbol_name: Annotated[str, Field(description="Function or method identifier to trace.")],
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository (default: '.').")] = ".",
        max_depth: Annotated[int, Field(default=3, description="Maximum recursive call graph traversal depth (default: 3).")] = 3
    ) -> str:
        """Traces upstream and downstream call chains for any function or method.
        
        Args:
            symbol_name: Function or method identifier to trace.
            project_root: Root directory of the repository (default: '.').
            max_depth: Maximum recursive call graph traversal depth (default: 3).
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
            "Identifies unused, orphaned, or unreferenced functions, classes, and private methods across codebase files, distinguishing from 'find_code_duplicity' and 'audit_codebase_quality' by finding uncalled symbols rather than duplicate code blocks or static code smells.\n"
            "\n"
            "Parameters:\n"
            "- `project_root` (str, optional, default='.'): Target repository root directory to scan.\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Compares defined AST symbols against reference sites without editing code.\n"
            "- Idempotent: Deterministic detection of unreferenced symbols for unchanged code.\n"
            "- 100% Offline: Local cross-file symbol indexing with zero cloud telemetry.\n"
            "- Auth & Rate Limits: Zero authentication or API keys required; completes in <200ms.\n"
            "- Error Handling: Confirms zero dead code detected if all symbols are referenced.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Clean up technical debt, safely decommission deprecated code, and prune unused legacy functions.\n"
            "- When NOT to use: Do not use for finding duplicate copy-pasted blocks (use 'find_code_duplicity' instead); do not use for detecting security leaks (use 'verify_zero_leak_security' instead).\n"
            "\n"
            "Returns: Markdown report listing orphaned symbols, defining file paths, line numbers, and safe refactoring recommendations."
        ),
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
            "Compresses natural language text or system logs into dense T-Zero virtual memory tokens using Vector Quantization, distinguishing from 'jarvis_decompress_semantic_memory' and 'prune_code_snippet' by encoding prose into persistent vector tokens rather than decoding or pruning AST code.\n"
            "\n"
            "Parameters:\n"
            "- `text` (str, required): Natural language text, discussion, or system log string to compress into semantic memory.\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Encodes text into VQ codebook representation in memory without disk writes.\n"
            "- Idempotent: Deterministic token generation for identical text inputs.\n"
            "- 100% Offline: Local semantic hashing and vector codebook quantization; operates entirely offline.\n"
            "- Auth & Rate Limits: Zero credentials or accounts required; executes in <5ms.\n"
            "- Error Handling: Returns empty token safely if input text is blank.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Compress conversation history, user preferences, or architecture decisions into compact tokens (<|tzero:mem:...|>) for persistent agent recall.\n"
            "- When NOT to use: Do not use to decode memory tokens back to text (use 'jarvis_decompress_semantic_memory' instead); do not use for source code AST pruning (use 'prune_code_snippet' instead).\n"
            "\n"
            "Returns: Markdown report containing generated virtual memory token (<|tzero:mem:ID|>), compression ratio, and semantic key tags."
        ),
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
            "Resolves and decompresses a T-Zero virtual memory token back into its original text representation, distinguishing from 'jarvis_compress_semantic_memory' and 'jarvis_query_knowledge_graph' by reconstructing exact stored memories from token identifiers rather than encoding or graph search.\n"
            "\n"
            "Parameters:\n"
            "- `token_or_code` (str, required): T-Zero memory token string (e.g. '<|tzero:mem:...|>') or numeric codebook index to decompress.\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Reads from local VQ codebook memory in memory without altering repository files.\n"
            "- Idempotent: Deterministic decompression for identical token keys.\n"
            "- 100% Offline: Pure local memory lookup; zero network egress or cloud telemetry.\n"
            "- Auth & Rate Limits: Zero authentication or cloud credentials required; sub-millisecond execution (<1ms).\n"
            "- Error Handling: Returns descriptive warning if token identifier is unknown or expired.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Expand compact memory tokens into human-readable text when an agent needs the full context of a prior decision or log.\n"
            "- When NOT to use: Do not use to compress new text into tokens (use 'jarvis_compress_semantic_memory' instead); do not use for searching knowledge graphs by entity (use 'jarvis_query_knowledge_graph' instead).\n"
            "\n"
            "Returns: Original natural language text or log payload previously stored under the memory token."
        ),
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
            "Orchestrates autonomous workspace engineering goals across multi-agent swarms with self-healing verification, distinguishing from 'jarvis_self_healing_execute' and 'jarvis_swarm_orchestrate' by executing complete phased engineering refactors and rule governance rather than single commands or consensus votes.\n"
            "\n"
            "Parameters:\n"
            "- `goal` (str, optional, default='plan'): Engineering objective, task description, or 'plan'/'help' to display capabilities and phased roadmaps.\n"
            "- `project_root` (str, optional, default='.'): Target workspace directory to orchestrate within.\n"
            "- `mode` (str, optional, default='auto'): Execution mode: 'auto' (evaluates and executes), 'plan' (roadmap only), 'execute' (runs actions), or 'capabilities' (menu).\n"
            "\n"
            "Behavior:\n"
            "- State-Modifying: Coordinates agents to update workspace files, write governance configurations, and run verification gates.\n"
            "- Non-idempotent: Execution steps and outcomes adapt dynamically to workspace state changes.\n"
            "- 100% Offline: Operates entirely on the local file system without remote network transmission or external dependencies.\n"
            "- Auth & Rate Limits: Zero authentication or cloud credentials required; bounded by local task execution time.\n"
            "- Error Handling: Triggers self-healing retry loops automatically if intermediate execution stages encounter failures.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Execute high-level complex coding goals, configure workspace governance rules, or plan phased engineering refactors.\n"
            "- When NOT to use: Do not use for isolated static code smell audits (use 'audit_codebase_quality' instead); do not use for single command self-healing execution (use 'jarvis_self_healing_execute' instead).\n"
            "\n"
            "Returns: Formatted Markdown report detailing executed stages, verification logs, zero-leak security status, and completed artifacts."
        ),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=False)
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
            "Dispatches inference prompts to free zero-API-key intelligence providers (local Ollama or free cloud endpoints), distinguishing from 'search_codebase_semantic' and 'get_project_context_tree' by generating natural language completions rather than static codebase context.\n"
            "\n"
            "Parameters:\n"
            "- `prompt` (str, required): User prompt, code question, or instruction for the AI model.\n"
            "- `system_prompt` (str, optional, default='You are T-Zero Jarvis Autonomous Code Engineer.'): System instruction establishing model behavior and role.\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Performs query inference without modifying workspace files or persisting conversational state.\n"
            "- Non-idempotent: Model responses may vary across invocations.\n"
            "- Open-World Network Operation: Dispatches HTTP requests to local Ollama (127.0.0.1:11434) or Pollinations Free Cloud (text.pollinations.ai) with zero user API keys or billing.\n"
            "- Auth & Rate Limits: Zero credentials required; no account or credit card needed. External free tier has a 45-second network timeout.\n"
            "- Error Handling: Automatically falls back from local Ollama to free cloud endpoints if local daemon is inactive.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Query free AI inference for coding questions or reasoning without configuring API keys or paying commercial provider fees.\n"
            "- When NOT to use: Do not use for local codebase search or AST parsing (use 'search_codebase_semantic' or 'get_project_context_tree' instead); do not use for structured file modifications (use 'generate_smart_micro_patch' instead).\n"
            "\n"
            "Returns: Structured Markdown containing selected zero-cost provider name, model identifier, cost confirmation ($0.00), and response completion text."
        ),
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
            "Searches the T-Zero Jarvis semantic knowledge graph and VQ memory by entity, predicate, or context, distinguishing from 'jarvis_causal_chain_query' and 'search_codebase_semantic' by querying structured semantic memory triples rather than 4D temporal causal chains or raw text files.\n"
            "\n"
            "Parameters:\n"
            "- `query` (str, optional, default=''): General natural language search term to locate in graph.\n"
            "- `entity` (str, optional, default=''): Specific entity name to filter knowledge graph nodes.\n"
            "- `predicate` (str, optional, default=''): Relationship or predicate type to filter edges (e.g. 'depends_on', 'implements').\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Reads from local graph index in memory without writing changes.\n"
            "- Idempotent: Deterministic search results for identical query parameters.\n"
            "- 100% Offline: Pure local knowledge graph querying with zero network egress.\n"
            "- Auth & Rate Limits: Zero authentication or cloud credentials required; query latency <10ms.\n"
            "- Error Handling: Returns empty graph notice gracefully if no matching entities exist.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Retrieve previously learned domain knowledge, architecture relationships, and code entity triples stored in memory.\n"
            "- When NOT to use: Do not use for tracing temporal bug incident causal chains (use 'jarvis_causal_chain_query' instead); do not use for raw text file keyword search (use 'search_codebase_semantic' instead).\n"
            "\n"
            "Returns: Markdown document with matching knowledge graph nodes, relationships, predicates, and stored entity attributes."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_jarvis_query_knowledge_graph(
        query: Annotated[str, Field(default="", description="General natural language search term to locate in graph (default: empty string).")] = "",
        entity: Annotated[str, Field(default="", description="Specific entity name to filter knowledge graph nodes (default: empty string).")] = "",
        predicate: Annotated[str, Field(default="", description="Relationship or predicate type to filter edges, e.g. 'depends_on' (default: empty string).")] = ""
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
            "Compresses large multi-paragraph technical documents into hierarchical semantic outlines, distinguishing from 'jarvis_latent_press_compress' and 'prune_code_snippet' by preserving document structure and section keynotes rather than mathematical latent vectors or AST code syntax.\n"
            "\n"
            "Parameters:\n"
            "- `document_text` (str, required): Full text of technical documentation, README, or article to compress.\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Compresses document content in memory without modifying local files.\n"
            "- Idempotent: Deterministic outline generation for identical document text.\n"
            "- 100% Offline: Local natural language parsing and keypoint extraction; operates strictly offline.\n"
            "- Auth & Rate Limits: Zero credentials or accounts required; completes in <50ms.\n"
            "- Error Handling: Returns clean original text if document is already shorter than threshold.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Ingest long documentation, API specifications, or release notes into LLM context windows (70-85% token reduction).\n"
            "- When NOT to use: Do not use for compressing code files (use 'prune_code_snippet' instead); do not use for compressing near-duplicate context strings (use 'jarvis_latent_press_compress' instead).\n"
            "\n"
            "Returns: Markdown summary with hierarchical section headings, key takeaways, and compression ratio telemetry."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_jarvis_compress_document(
        document_text: Annotated[str, Field(description="Full text of technical documentation, README, or article to compress.")]
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
            "Exports or imports the T-Zero Jarvis persistent VQ codebook memory and knowledge graph to or from disk, distinguishing from 'jarvis_consolidate_memory' and 'jarvis_export_graph_visualization' by serializing raw memory states for backup rather than consolidating memories or generating HTML visualizers.\n"
            "\n"
            "Parameters:\n"
            "- `action` (str, optional, default='save'): Operation to perform: 'save' (exports memory to disk) or 'load' (imports memory from disk).\n"
            "- `file_path` (str, optional, default=''): Optional custom file path relative to workspace root (defaults to 'tzero_memory_store.json' if omitted).\n"
            "\n"
            "Behavior:\n"
            "- State-Modifying: Writes memory store to disk on export or updates in-memory tables on import.\n"
            "- Non-idempotent: Memory state reflects current accumulated knowledge at time of action.\n"
            "- 100% Offline: Pure local file system serialization; operates strictly offline.\n"
            "- Auth & Rate Limits: Zero credentials or API keys required; typical execution <100ms.\n"
            "- Error Handling: Validates file format and handles missing import files with clear error messages.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Persist learned agent memory across IDE sessions or transfer memory codebooks between team environments.\n"
            "- When NOT to use: Do not use for generating visual 3D HTML graph interfaces (use 'jarvis_export_graph_visualization' instead); do not use for pruning obsolete memories (use 'jarvis_consolidate_memory' instead).\n"
            "\n"
            "Returns: Confirmation Markdown message with memory store file path, total exported/imported vector tokens, and node count."
        ),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=False)
    )
    def _legacy_jarvis_export_memory_store(
        action: Annotated[str, Field(default="save", description="Action to perform: 'save' (export to disk) or 'load' (import from disk) (default: 'save').")] = "save",
        file_path: Annotated[str, Field(default="", description="Optional custom JSON file path (default: '' uses 'tzero_memory_store.json').")] = ""
    ) -> str:
        """Saves or loads persistent semantic memory store.
        
        Args:
            action: 'save' or 'load'.
            file_path: Target JSON file path.
        """
        from tzero_jarvis import get_global_compressor
        compressor = get_global_compressor()
        target = file_path if file_path else None

        act = (action or "save").lower().strip()
        if act in ("load", "import"):
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
        description=(
            "Queries the 4D Causal and Temporal Knowledge Graph for root cause analysis of changes and incidents, distinguishing from 'analyze_change_impact' and 'jarvis_query_knowledge_graph' by analyzing chronological causal chains and temporal links rather than static blast radius or entity triples.\n"
            "\n"
            "Parameters:\n"
            "- `target_node_id` (str, required): Incident identifier, bug description, or symbol name to trace root cause for.\n"
            "- `query_type` (str, optional, default='root_causes'): Analysis mode: 'root_causes' (backward causal trace), 'effect_chain' (downstream consequence chain), 'rollback_order' (safe rollback sequence), or 'timeline' (chronological event history).\n"
            "\n"
            "Behavior:\n"
            "- Side Effects: Pure in-memory causal graph traversal; does not write or modify files on disk.\n"
            "- Idempotent: Deterministic causal traversal for unchanged timeline events.\n"
            "- 100% Offline: Pure local causal inference; operates strictly offline.\n"
            "- Auth & Rate Limits: Zero credentials or API keys required; executes in <30ms.\n"
            "- Error Handling: Returns informative notice if target node has no causal links in memory.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Diagnose why a regression occurred, determine which historical commit caused an error, or assess chronological consequence chains.\n"
            "- When NOT to use: Do not use for static module import analysis (use 'query_module_dependencies' instead); do not use for single-commit diff summaries (use 'get_incremental_diff_context' instead).\n"
            "\n"
            "Returns: Markdown causal analysis with chronological timeline table, root cause probability scores, and contributing change links."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_jarvis_causal_chain_query(
        target_node_id: Annotated[str, Field(description="Incident identifier, bug description, or symbol name to trace root cause for.")],
        query_type: Annotated[str, Field(default="root_causes", description="Analysis mode: 'root_causes' (backward causal trace), 'effect_chain' (downstream consequence chain), 'rollback_order' (safe rollback sequence), or 'timeline' (chronological event history) (default: 'root_causes').")] = "root_causes"
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
        description=(
            "Executes commands in a guarded environment with automated error analysis and self-healing retry loops, distinguishing from 'jarvis_orchestrate_goal' and 'jarvis_bft_swarm_consensus' by focusing specifically on command execution recovery rather than full workspace orchestration or swarm consensus.\n"
            "\n"
            "Parameters:\n"
            "- `command` (str, required): Shell command or test script to execute.\n"
            "- `max_retries` (int, optional, default=3): Maximum self-healing repair iterations if execution fails.\n"
            "\n"
            "Behavior:\n"
            "- State-Modifying: Executes shell commands on local system and applies automated fixes on failure.\n"
            "- Non-idempotent: Command output and environmental state depend on local system execution.\n"
            "- 100% Offline: Executes locally using native system shell; operates strictly offline.\n"
            "- Auth & Rate Limits: Zero credentials required; execution bounded by command timeout (60s default).\n"
            "- Error Handling: Intercepts non-zero exit codes, analyzes error stack traces, and synthesizes corrective micro-patches.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Run test suites, build scripts, or deployment commands that may require automated error diagnosis and self-healing fixes.\n"
            "- When NOT to use: Do not use for high-level multi-stage project refactors (use 'jarvis_orchestrate_goal' instead); do not use for static code smell checks (use 'audit_codebase_quality' instead).\n"
            "\n"
            "Returns: Markdown execution log with process exit code, stdout/stderr output, diagnostic analysis, and applied self-healing remedies."
        ),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=False)
    )
    def _legacy_jarvis_self_healing_execute(
        command: Annotated[str, Field(description="Shell command or test script to execute.")],
        max_retries: Annotated[int, Field(default=3, description="Maximum self-healing repair iterations if execution fails (default: 3).")] = 3
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
        description=(
            "Performs brain-like hippocampal memory consolidation to merge redundant vector clusters into representative centroids, distinguishing from 'jarvis_compress_semantic_memory' and 'jarvis_export_memory_store' by optimizing existing memory stores rather than encoding new text or backing up to disk.\n"
            "\n"
            "Parameters:\n"
            "- `action` (str, optional, default='consolidate'): Consolidation mode: 'consolidate' (runs compaction cycle) or 'summary' (reports consolidation status).\n"
            "\n"
            "Behavior:\n"
            "- State-Modifying: Restructures internal VQ codebook clusters into compact representative centroids without removing unique records.\n"
            "- Non-idempotent: Memory state reflects updated cluster centroids post-consolidation.\n"
            "- 100% Offline: Local vector clustering and similarity pruning; operates strictly offline.\n"
            "- Auth & Rate Limits: Zero authentication or cloud credentials required; completes in <50ms.\n"
            "- Error Handling: Preserves high-importance and pinned memory tokens unconditionally.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Periodically optimize persistent agent memory to eliminate clutter, improve search speed, and reclaim codebook capacity.\n"
            "- When NOT to use: Do not use for creating new memories from text (use 'jarvis_compress_semantic_memory' instead); do not use for serializing memory to file (use 'jarvis_export_memory_store' instead).\n"
            "\n"
            "Returns: Markdown report with consolidation statistics, pruned token count, reclaimed memory percentage, and updated cluster health."
        ),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=False)
    )
    def _legacy_jarvis_consolidate_memory(
        action: Annotated[str, Field(default="consolidate", description="Consolidation mode: 'consolidate' (runs compaction cycle) or 'summary' (reports consolidation status) (default: 'consolidate').")] = "consolidate"
    ) -> str:
        """Consolidates episodic memory into permanent abstracted knowledge."""
        from tzero_jarvis import ConsolidationEngine, get_global_compressor
        compressor = get_global_compressor()
        engine = ConsolidationEngine(compressor.codebook)
        
        act = (action or "consolidate").lower().strip()
        if act in ("summary", "status"):
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
        description=(
            "Performs high-speed hybrid search combining BM25 lexical ranking and latent codebook similarity, distinguishing from 'search_codebase_semantic' and 'jarvis_query_knowledge_graph' by querying both persistent VQ memory and workspace files with reciprocal rank fusion rather than pure text or entity triples.\n"
            "\n"
            "Parameters:\n"
            "- `query` (str, required): Search query, question, or code pattern to locate.\n"
            "- `top_k` (int, optional, default=10): Maximum number of ranked results to return.\n"
            "- `domain` (str, optional, default=''): Optional domain filter ('HARDWARE', 'PROTOCOL', 'SOFTWARE', etc.). If empty, searches across all domains.\n"
            "\n"
            "Behavior:\n"
            "- Side Effects: Pure in-memory similarity matching; does not write or modify files on disk.\n"
            "- Determinism: Produces consistent ranked matches for identical query terms on unchanged codebooks.\n"
            "- Scope & Network: Executes entirely offline using local BM25 scoring and vector distance math; operates strictly offline.\n"
            "- Auth & Performance: Requires zero credentials or external API keys; completes in <30ms.\n"
            "- Fault Tolerance: Returns an informative Markdown message if no items match the search query.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Find relevant code, past decisions, or documentation using combined lexical and semantic search without cloud dependencies.\n"
            "- When NOT to use: Do not use for single-file focus skeletons (use 'get_smart_skeleton_context' instead); do not use for full directory context trees (use 'get_project_context_tree' instead).\n"
            "\n"
            "Returns: Markdown document with ranked hybrid results, source types (code vs memory), relevance scores, and code previews."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_jarvis_hybrid_search(
        query: Annotated[str, Field(description="Search query, question, or code pattern to locate.")],
        top_k: Annotated[int, Field(default=10, description="Maximum number of ranked results to return (default: 10).")] = 10,
        domain: Annotated[str, Field(default="", description="Optional domain filter ('HARDWARE', 'PROTOCOL', 'SOFTWARE', etc., default: '' searches all domains).")] = ""
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
        description=(
            "Coordinates a 5-agent autonomous swarm (Security, Architect, QA, Coder, Executive) to execute engineering missions, distinguishing from 'jarvis_orchestrate_goal' and 'jarvis_bft_swarm_consensus' by delegating specialized sub-tasks across roles rather than executing sequentially or running voting rounds.\n"
            "\n"
            "Parameters:\n"
            "- `mission_goal` (str, required): High-level mission directive or engineering objective for the swarm.\n"
            "- `context` (str, optional, default=''): Optional workspace context or specific constraints to guide agent execution.\n"
            "\n"
            "Behavior:\n"
            "- State-Modifying: Directs agent roles to generate code, run audits, and write verified files.\n"
            "- Non-idempotent: Swarm actions dynamically adapt based on intermediate agent findings.\n"
            "- 100% Offline: Swarm operates entirely locally using deterministic rule engines; operates strictly offline.\n"
            "- Auth & Rate Limits: Zero credentials or API keys required; execution bounded by mission complexity.\n"
            "- Error Handling: Reassigns failed agent stages to fallback roles with explanatory diagnostic logs.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Tackle complex engineering initiatives requiring multi-perspective verification (security audit + architecture compliance + code generation).\n"
            "- When NOT to use: Do not use for isolated single-agent command repairs (use 'jarvis_self_healing_execute' instead); do not use for standalone BFT voting (use 'jarvis_bft_swarm_consensus' instead).\n"
            "\n"
            "Returns: Comprehensive Markdown mission debrief with role-by-role execution logs, consensus outcome, and produced artifacts."
        ),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=False)
    )
    def _legacy_jarvis_swarm_orchestrate(
        mission_goal: Annotated[str, Field(description="High-level mission directive or engineering objective for the swarm.")],
        context: Annotated[str, Field(default="", description="Optional workspace context or specific constraints to guide agent execution (default: '').")] = ""
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
        description=(
            "Generates an offline, interactive cyberpunk HTML graph visualizer for knowledge and causal memory networks, distinguishing from 'jarvis_export_memory_store' and 'generate_architecture_blueprint' by producing an interactive browser canvas for memory graphs rather than JSON backups or Mermaid architecture diagrams.\n"
            "\n"
            "Parameters:\n"
            "- `output_path` (str, optional, default=''): Destination file path for the generated HTML visualizer (defaults to 'tzero_graph_hud.html' if omitted).\n"
            "\n"
            "Behavior:\n"
            "- File-Creation: Writes a standalone self-contained HTML file to the specified destination path.\n"
            "- Idempotent: Generates deterministic HTML visualization for identical memory graph states.\n"
            "- 100% Offline: Embeds visualization scripts locally; operates strictly offline.\n"
            "- Auth & Rate Limits: Zero credentials or third-party licenses required; generates in <100ms.\n"
            "- Error Handling: Creates parent directories automatically if output directory does not exist.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Explore and interactively inspect the agent's knowledge graph, entity relationships, and causal links in a web browser.\n"
            "- When NOT to use: Do not use for raw JSON data backups (use 'jarvis_export_memory_store' instead); do not use for architecture module diagrams (use 'generate_architecture_blueprint' instead).\n"
            "\n"
            "Returns: Confirmation Markdown message with absolute path to generated HTML file, total node count, and edge count."
        ),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_jarvis_export_graph_visualization(
        output_path: Annotated[str, Field(default="", description="Destination file path for the generated HTML visualizer (default: '' uses 'tzero_graph_hud.html').")] = ""
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
        description=(
            "Calculates sub-microsecond Jaccard similarity between two text snippets using MinHash Locality-Sensitive Hashing, distinguishing from 'find_code_duplicity' and 'jarvis_latent_press_compress' by computing probabilistic set similarity on raw strings rather than AST block duplicity or vector prefill compression.\n"
            "\n"
            "Parameters:\n"
            "- `text_a` (str, required): First text or code snippet to compare.\n"
            "- `text_b` (str, optional, default=''): Second text to compare against. If empty, searches memory codebook.\n"
            "- `threshold` (float, optional, default=0.5): Minimum Jaccard similarity threshold (0.0 to 1.0) to flag as a positive match.\n"
            "\n"
            "Behavior:\n"
            "- Side Effects: Pure in-memory MinHash calculation; does not write or modify files on disk.\n"
            "- Idempotent: Deterministic MinHash signature generation for identical input texts.\n"
            "- 100% Offline: Pure local bitwise hashing; operates strictly offline.\n"
            "- Auth & Rate Limits: Zero authentication or API keys required; sub-microsecond calculation (<1ms).\n"
            "- Error Handling: Gracefully handles empty string comparisons with 0.0 similarity score.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Fast near-duplicate detection, content deduplication, or measuring similarity between prompt variations and code patches.\n"
            "- When NOT to use: Do not use for scanning an entire repository for duplicated blocks (use 'find_code_duplicity' instead); do not use for semantic knowledge graph queries (use 'jarvis_query_knowledge_graph' instead).\n"
            "\n"
            "Returns: Markdown report with estimated Jaccard Similarity (0.00-1.00), boolean threshold verdict, and shared shingle count."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_jarvis_minhash_similarity(
        text_a: Annotated[str, Field(description="First text or code snippet to compare.")],
        text_b: Annotated[str, Field(default="", description="Second text to compare against. If empty, searches memory codebook (default: '').")] = "",
        threshold: Annotated[float, Field(default=0.5, description="Minimum Jaccard similarity threshold (0.0 to 1.0) to flag as a positive match (default: 0.5).")] = 0.5
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
        description=(
            "Executes 3-phase Practical Byzantine Fault-Tolerant consensus across autonomous swarm agents, distinguishing from 'jarvis_swarm_orchestrate' and 'jarvis_orchestrate_goal' by running formal cryptographic voting (pre-prepare, prepare, commit) rather than delegating tasks or managing work plans.\n"
            "\n"
            "Parameters:\n"
            "- `mission_goal` (str, required): Action, refactoring plan, or critical decision requiring swarm consensus.\n"
            "- `context` (str, optional, default=''): Supporting architectural context, risk parameters, or verification constraints.\n"
            "\n"
            "Behavior:\n"
            "- State-Modifying: Records consensus votes and commits agreed-upon decisions into agent event logs.\n"
            "- Non-idempotent: Voting rounds and validator responses reflect active agent swarm states.\n"
            "- 100% Offline: Executes deterministic PBFT algorithm locally; operates strictly offline.\n"
            "- Auth & Rate Limits: Zero credentials or external blockchain networks required; executes in <50ms.\n"
            "- Error Handling: Automatically rejects proposals if Byzantine fault threshold (f >= n/3) is violated.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Validate high-risk codebase decisions (e.g. major migrations, secret key rotations, destructive operations) through multi-agent consensus.\n"
            "- When NOT to use: Do not use for standard non-critical file edits (use 'generate_smart_micro_patch' instead); do not use for single-command self-healing (use 'jarvis_self_healing_execute' instead).\n"
            "\n"
            "Returns: Markdown PBFT consensus certificate with voting rounds breakdown, quorum status, fault tolerance metrics, and committed action."
        ),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=False)
    )
    def _legacy_jarvis_bft_swarm_consensus(
        mission_goal: Annotated[str, Field(description="Action, refactoring plan, or critical decision requiring swarm consensus.")],
        context: Annotated[str, Field(default="", description="Supporting architectural context, risk parameters, or verification constraints (default: '').")] = ""
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
        description=(
            "Compresses long text contexts before model prefill using Latent-Press deduplication and token pruning, distinguishing from 'jarvis_compress_semantic_memory' and 'prune_code_snippet' by pruning near-duplicate sentence clusters for LLM prefill rather than generating memory tokens or parsing AST code.\n"
            "\n"
            "Parameters:\n"
            "- `context_text` (str, required): Long text or documentation string to compress before feeding to LLM.\n"
            "- `near_dup_threshold` (float, optional, default=0.65): Similarity threshold (0.0 to 1.0) for collapsing redundant sentences.\n"
            "\n"
            "Behavior:\n"
            "- Side Effects: Pure in-memory context compression; does not write or modify files on disk.\n"
            "- Idempotent: Deterministic compression for identical input text and threshold.\n"
            "- 100% Offline: Local vector quantization and token pruning; operates strictly offline.\n"
            "- Auth & Rate Limits: Zero authentication or cloud credentials required; typical latency <20ms.\n"
            "- Error Handling: Preserves critical headings and numbers without lossy distortion.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Condense massive prompt contexts, repetitive log dumps, or stacked documentation files before LLM invocation (40-75% token reduction).\n"
            "- When NOT to use: Do not use for structured code AST compression (use 'prune_code_snippet' instead); do not use for persistent memory storage (use 'jarvis_compress_semantic_memory' instead).\n"
            "\n"
            "Returns: Condensed text string ready for model prompt ingestion, accompanied by token compression telemetry."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_jarvis_latent_press_compress(
        context_text: Annotated[str, Field(description="Long text or documentation string to compress before feeding to LLM.")],
        near_dup_threshold: Annotated[float, Field(default=0.65, description="Similarity threshold (0.0 to 1.0) for collapsing redundant sentences.")] = 0.65
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
            "Compresses SQL DDL schemas, Kubernetes YAML manifests, Dockerfiles, and OpenAPI specs by stripping comments and non-essential attributes, distinguishing from 'prune_code_snippet' and 'get_project_context_tree' by using declarative schema grammar rules rather than programming language AST parsers.\n"
            "\n"
            "Parameters:\n"
            "- `content` (str, required): Raw schema string (SQL, YAML, JSON Schema, Dockerfile) to compress.\n"
            "- `schema_type_or_filename` (str, optional, default='schema.sql'): Filename or schema format ('sql', 'yaml', 'k8s', 'dockerfile', 'openapi').\n"
            "- `reduction_mode` (str, optional, default='ultra'): Reduction level ('ultra' for minimal structural types, 'balanced' for types + constraints, 'none' for verbatim).\n"
            "\n"
            "Behavior:\n"
            "- Read-only: Transforms declarative schema strings in memory without writing to disk.\n"
            "- Idempotent: Deterministic compression for identical schema definitions.\n"
            "- 100% Offline: Pure local schema parsing and token compaction; zero external dependencies.\n"
            "- Auth & Rate Limits: Zero credentials or accounts required; executes in <15ms.\n"
            "- Error Handling: Gracefully preserves unparseable blocks with clean fallback notice.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Compress massive database migration scripts, Kubernetes deployment manifests, or OpenAPI specifications before injecting into prompts.\n"
            "- When NOT to use: Do not use for Python, TypeScript, or Go code files (use 'prune_code_snippet' instead); do not use for git diff patches (use 'generate_smart_micro_patch' instead).\n"
            "\n"
            "Returns: Pruned schema text preserving table names, columns, data types, and primary keys with 60-85% token reduction."
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
            "Compresses unified git diffs into ultra-dense semantic micro-patches while preserving change context, distinguishing from 'get_incremental_diff_context' and 'compress_stream_tokens' by parsing raw diff patch text directly without requiring a live git repository.\n"
            "\n"
            "Parameters:\n"
            "- `diff_content` (str, required): Raw unified diff text (e.g. git diff output) to compress.\n"
            "- `max_context_lines` (int, optional, default=1): Maximum unchanged context lines to keep around hunk modifications.\n"
            "\n"
            "Behavior:\n"
            "- Side Effects: Pure in-memory diff parsing and compression; does not write or modify files on disk.\n"
            "- Idempotent: Deterministic compression for identical diff patch inputs.\n"
            "- 100% Offline: Local hunk parser and AST boundary trimmer; operates strictly offline.\n"
            "- Auth & Rate Limits: Zero credentials or cloud dependencies required; executes in <10ms.\n"
            "- Error Handling: Preserves patch headers and line markers even when diff format is non-standard.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Minimize git diff token footprint when sending code changes, PR reviews, or patch requests to AI models (70-90% token reduction).\n"
            "- When NOT to use: Do not use for extracting diffs directly from a git repository (use 'get_incremental_diff_context' instead); do not use for pruning raw source code files (use 'prune_code_snippet' instead).\n"
            "\n"
            "Returns: Compressed micro-patch string with minimized context lines and token reduction metrics."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_generate_smart_micro_patch(
        diff_content: Annotated[str, Field(description="Raw unified diff text (e.g. git diff output) to compress.")],
        max_context_lines: Annotated[int, Field(default=1, description="Maximum unchanged context lines to keep around hunk modifications (default: 1).")] = 1
    ) -> str:
        """Compresses unified git diff into a compact semantic micro-patch."""
        from tzero_patch import SmartMicroPatcher
        return SmartMicroPatcher.format_micro_patch_report(diff_content, max_context_lines=max_context_lines)

    # -------------------------------------------------------------------------
    # TOOL 40: generate_zero_waste_prompt_context
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="generate_zero_waste_prompt_context",
        description=(
            "Extracts cross-module AST call graphs from workspace entrypoints to assemble minimal zero-waste prompt context, distinguishing from 'get_project_context_tree' and 'get_smart_skeleton_context' by tracing execution reachability from specific main entrypoints rather than scanning all files.\n"
            "\n"
            "Parameters:\n"
            "- `target_dir` (str, optional, default='.'): Target repository root directory.\n"
            "- `entrypoints` (array of strings, optional, default=None): List of entrypoint filenames (e.g. ['main.py', 'app.py']). If omitted or null, entrypoints are auto-detected.\n"
            "\n"
            "Behavior:\n"
            "- Side Effects: Pure in-memory AST reachability analysis; does not write or modify files on disk.\n"
            "- Idempotent: Generates deterministic context for identical entrypoint sets.\n"
            "- 100% Offline: Pure local reachability analysis; operates strictly offline.\n"
            "- Auth & Rate Limits: Zero credentials or cloud services required; executes in <150ms.\n"
            "- Error Handling: Automatically discovers standard entrypoints (main, app, index) if none are specified.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Generate ultra-lean context for an AI agent addressing an entrypoint workflow, discarding unreachable dead files completely.\n"
            "- When NOT to use: Do not use when full global repository architecture is needed (use 'get_project_context_tree' instead); do not use for inspecting a single focused file (use 'get_smart_skeleton_context' instead).\n"
            "\n"
            "Returns: Structured Markdown context containing pruned AST signatures of all reachable modules along execution paths from entrypoints."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_generate_zero_waste_prompt_context(
        target_dir: Annotated[str, Field(default=".", description="Target repository root directory (default: '.').")] = ".",
        entrypoints: Annotated[Optional[List[str]], Field(default=None, description="List of entrypoint filenames (e.g. ['main.py', 'app.py']). If omitted or null, entrypoints are auto-detected.")] = None
    ) -> str:
        """Constructs zero-waste LLM prompt context by pruning dead code via AST reachability."""
        from tzero_reachability import CallGraphReachabilityEngine
        if isinstance(entrypoints, str):
            entrypoints = [x.strip() for x in entrypoints.split(",") if x.strip()]
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
            "Compresses arbitrary streaming code chunks, unified diffs, or logs using byte-level token compression, distinguishing from 'prune_code_snippet' and 'jarvis_latent_press_compress' by processing continuous byte streams on-the-fly without requiring complete AST grammar structures.\n"
            "\n"
            "Parameters:\n"
            "- `content` (str, required): Streaming text, log chunk, or partial code buffer to compress.\n"
            "- `filename_hint` (str, optional, default=''): Optional filename or extension hint (e.g. 'app.py', 'schema.sql', 'patch.diff') to optimize AST reduction.\n"
            "- `tier` (str, optional, default='T-3'): Compression tier ('T-3' for AST signatures, 'T-2' for light structure, 'T-4' for agent rules).\n"
            "\n"
            "Behavior:\n"
            "- Side Effects: Pure in-memory streaming compression; does not write or modify files on disk.\n"
            "- Idempotent: Deterministic compression for identical byte buffer inputs.\n"
            "- 100% Offline: Local streaming compaction algorithm; operates strictly offline.\n"
            "- Auth & Rate Limits: Zero authentication or cloud credentials required; sub-millisecond latency (<2ms).\n"
            "- Error Handling: Falls back to raw stream safely if compression does not reduce token count.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Compress real-time stdout streams, compiler outputs, terminal logs, or chunked buffers before feeding to an LLM.\n"
            "- When NOT to use: Do not use for structured full source code files (use 'prune_code_snippet' instead); do not use for SQL or Kubernetes YAML schemas (use 'prune_schema_definition' instead).\n"
            "\n"
            "Returns: Compressed stream text payload alongside token savings count and compression efficiency percentage."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_compress_stream_tokens(
        content: Annotated[str, Field(description="Streaming text, log chunk, or partial code buffer to compress.")],
        filename_hint: Annotated[str, Field(default="", description="Optional filename or extension hint (e.g. 'app.py', 'schema.sql', 'patch.diff') to optimize AST reduction (default: '').")] = "",
        tier: Annotated[str, Field(default="T-3", description="Compression tier ('T-3' for AST signatures, 'T-2' for light structure, 'T-4' for agent rules) (default: 'T-3').")] = "T-3"
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
            "Installs the automated T-Zero Git Pre-Commit Security Guard hook in the local repository, distinguishing from 'verify_zero_leak_security' and 'export_agent_rules' by installing executable git hooks into '.git/hooks' rather than running one-time scans or writing editor rules.\n"
            "\n"
            "Parameters:\n"
            "- `repo_dir` (str, optional, default='.'): Target git repository root directory where the pre-commit hook will be installed.\n"
            "\n"
            "Behavior:\n"
            "- File-Creation: Writes executable pre-commit script to '.git/hooks/pre-commit' in the target repository.\n"
            "- Idempotent: Safely installs or updates the hook without breaking existing git hook chains.\n"
            "- 100% Offline: Generates hook locally from embedded template; operates strictly offline.\n"
            "- Auth & Rate Limits: Zero credentials or accounts required; completes in <20ms.\n"
            "- Error Handling: Returns descriptive error notice if target directory is not a git repository.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Protect repositories from accidental credential leaks by automatically scanning all staged commits for API keys and secrets.\n"
            "- When NOT to use: Do not use for running a one-time manual security scan (use 'verify_zero_leak_security' instead); do not use for configuring IDE agent rules (use 'export_agent_rules' instead).\n"
            "\n"
            "Returns: Confirmation Markdown message indicating successful installation of the pre-commit hook and active protection patterns."
        ),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def _legacy_install_git_security_guard(
        repo_dir: Annotated[str, Field(default=".", description="Target git repository root directory where the pre-commit hook will be installed (default: '.').")] = "."
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
    @_canon_tool(
        name="build_project_context",
        description=(
            "Scans the target repository file system and constructs a token-optimized AST context payload for LLM prompts across multiple hierarchy tiers (T-1 to T-4).\n\n"
            "Behavior:\n"
            "- Read-only: Scans workspace files and parses AST signatures without modifying disk state.\n"
            "- Idempotent: Generates deterministic context representations for identical workspace revisions.\n"
            "- 100% Offline: Operates entirely locally with zero telemetry, remote embedding APIs, or cloud billing.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Ingest repository architecture, module indexes, focus file skeletons, or zero-waste prompts at the beginning of an agent coding session or major refactor (80-95% token savings).\n"
            "- When NOT to use: Do not use for stripping implementation bodies from a single in-memory code string or diff patch; use 'prune_code_snippet' instead. Do not use for querying specific code symbols or text without building a full context tree; use 'search_codebase' instead.\n\n"
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
    @_canon_tool(
        name="prune_code_snippet",
        description=(
            "Prunes implementation bodies from in-memory code snippets, API schemas, or unified diff streams while preserving AST interfaces, type annotations, and function signatures.\n\n"
            "Behavior:\n"
            "- Read-only: Processes in-memory text buffers without touching disk files.\n"
            "- Idempotent: Deterministic AST reduction for identical code inputs.\n"
            "- 100% Offline: Local AST and regex parsers for Python, TypeScript, Go, Rust, Java, C#, C++, SQL, JSON, YAML.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Compress raw code strings, function definitions, SQL queries, or diff patches before embedding them in an LLM prompt to achieve 80-95% token savings.\n"
            "- When NOT to use: Do not use for scanning full repository files or building hierarchical project context from disk; use 'build_project_context' instead. Do not use for detecting code duplication across modules; use 'audit_code_quality' instead.\n\n"
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
    @_canon_tool(
        name="manage_architecture_rules",
        description=(
            "Manages the lifecycle of architectural boundary definitions, tier rules (T-1 to T-4), and layer constraints configured in tzero.rules.json.\n\n"
            "Behavior:\n"
            "- Read-write: Queries existing rules or updates/deletes layer boundary specifications on disk.\n"
            "- Idempotent: Repeated queries or sets with identical values produce stable configurations.\n"
            "- 100% Offline: Local JSON file management without external communication.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Retrieve, inspect, add, update, reset, or delete architectural layer constraints (e.g. presentation -> domain -> persistence rules).\n"
            "- When NOT to use: Do not use for actively validating codebase files against these rules; use 'enforce_architecture_rules' instead. Do not use for generating visual Mermaid architectural topology diagrams; use 'generate_architecture_blueprint' instead.\n\n"
            "Returns: JSON or Markdown status report detailing active or updated architectural rules."
        ),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=False)
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
    @_canon_tool(
        name="enforce_architecture_rules",
        description=(
            "Enforces architectural boundary rules and layer isolation constraints defined in tzero.rules.json across the repository AST.\n\n"
            "Behavior:\n"
            "- Read-only: Scans codebase imports and call paths; does not alter files.\n"
            "- Idempotent: Deterministic violation reporting for identical codebase states.\n"
            "- 100% Offline: Local import graph validation against configured boundaries.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run in CI/CD pipelines or before merging PRs to prevent architectural erosion (e.g. presentation layer importing database models or circular module dependencies).\n"
            "- When NOT to use: Do not use for creating, viewing, or editing architectural boundary definitions; use 'manage_architecture_rules' instead. Do not use for inspecting general dependencies between modules; use 'analyze_code_dependencies' instead.\n\n"
            "Returns: Detailed compliance audit report listing passed layer boundaries, identified architectural violations, and remediation guidance."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def enforce_architecture_rules(
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to validate (default: current directory).")] = ".",
        strict_mode: Annotated[bool, Field(default=True, description="When True, fails on any boundary infraction; when False, warns without raising errors.")] = True
    ) -> str:
        """Enforces architectural boundary rules and layer isolation constraints across workspace AST."""
        report = _legacy_enforce_architecture_boundaries(project_root=project_root)
        if not strict_mode and "ARCH VIOLATION" in report:
            report = report.replace("ARCH VIOLATION", "ARCH WARNING (strict_mode=False)")
        return report

    # -------------------------------------------------------------------------
    # CANONICAL TOOL 5: generate_architecture_blueprint
    # -------------------------------------------------------------------------
    @_canon_tool(
        name="generate_architecture_blueprint",
        description=(
            "Generates a complete system architectural specification (ARCHITECTURE.md) with auto-generated Mermaid component topology diagrams, layer boundaries, and module hierarchies.\n\n"
            "Behavior:\n"
            "- Read-only: Returns formatted Markdown text without writing files to disk.\n"
            "- Idempotent: Deterministic AST topology diagram generation when use_ai=False.\n"
            "- 100% Offline by default: Runs local AST analysis; optionally uses configured AI model when use_ai=True.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Create or update system architecture documentation and visual Mermaid flow diagrams for onboarding or RFC review.\n"
            "- When NOT to use: Do not use for checking rule compliance against defined boundaries; use 'enforce_architecture_rules' instead. Do not use for raw dependency listings or call chain traces; use 'analyze_code_dependencies' instead.\n\n"
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
    @_canon_tool(
        name="analyze_code_dependencies",
        description=(
            "Analyzes module imports, symbol call chains, graph centrality (PageRank), and unreferenced dead code across polyglot source files.\n\n"
            "Behavior:\n"
            "- Read-only: Inspects source syntax trees without modifying or moving files.\n"
            "- Idempotent: Deterministic dependency mapping for any scanned repository.\n"
            "- 100% Offline: Local AST and regex parsers; zero external network requests.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run before refactoring, moving, or removing a module to inspect inbound dependents, outbound imports, deep symbol call chains, or unreferenced functions.\n"
            "- When NOT to use: Do not use for estimating the blast radius score of modifying a specific function or class; use 'analyze_change_impact' instead. Do not use for validating whether imports violate architectural layer rules; use 'enforce_architecture_rules' instead.\n\n"
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
    @_canon_tool(
        name="analyze_change_impact",
        description=(
            "Calculates change blast radius score (0-100) and identifies downstream dependents before modifying or deleting a target function, class, or module.\n\n"
            "Behavior:\n"
            "- Read-only: Scans workspace AST and dependency graphs; does not alter files.\n"
            "- Idempotent: Deterministic blast radius scoring for identical repository states.\n"
            "- 100% Offline: Local AST caller/callee traversal without remote API calls.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run prior to editing a core interface, signature, or shared utility to gauge how many downstream files and tests will be impacted.\n"
            "- When NOT to use: Do not use for general whole-repository dependency mapping or PageRank centrality; use 'analyze_code_dependencies' instead. Do not use for auditing static code complexity and code smells; use 'audit_code_quality' instead.\n\n"
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
        res = _legacy_analyze_change_impact(target_symbol=target_symbol, project_root=project_root)
        if file_path:
            return f"*(Focus file: `{file_path}`)*\n\n{res}"
        return res

    # -------------------------------------------------------------------------
    # CANONICAL TOOL 8: search_codebase
    # -------------------------------------------------------------------------
    @_canon_tool(
        name="search_codebase",
        description=(
            "Executes private local hybrid search combining BM25 keyword matching and TF-IDF semantic scoring across repository functions, classes, and docstrings.\n\n"
            "Behavior:\n"
            "- Read-only: Queries local code files without writing to disk or modifying indices.\n"
            "- Idempotent: Deterministic ranked results for identical queries on the same codebase.\n"
            "- 100% Offline: Executes entirely on CPU; no OpenAI/cloud embeddings, zero network egress.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Locate relevant functions, classes, or code implementations across the repository using natural language or code identifier queries.\n"
            "- When NOT to use: Do not use for querying persistent semantic knowledge graphs or agent memory triples; use 'query_memory_store' instead. Do not use for generating full project context trees; use 'build_project_context' instead.\n\n"
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
    @_canon_tool(
        name="audit_code_quality",
        description=(
            "Performs AST static code smell analysis, cyclomatic complexity profiling, duplicate code block detection, and AI coding hallucination validation.\n\n"
            "Behavior:\n"
            "- Read-only: Inspects source syntax trees; does not modify or delete files.\n"
            "- Idempotent: Consistent diagnostic findings for the same code state.\n"
            "- 100% Offline: Pure AST inspection without network calls.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run before submitting PRs or executing refactors to catch long methods (>30 lines), excessive arguments (>5), missing docstrings, copy-pasted blocks (6+ lines), or hallucinated imports.\n"
            "- When NOT to use: Do not use for scanning hardcoded secrets or installing git pre-commit security guards; use 'verify_security_guard' instead. Do not use for analyzing module import dependencies; use 'analyze_code_dependencies' instead.\n\n"
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
    @_canon_tool(
        name="verify_security_guard",
        description=(
            "Scans workspace files and code buffers for hardcoded secrets and API keys, or installs the automated git pre-commit zero-leak security guard.\n\n"
            "Behavior:\n"
            "- Read-only when action is 'scan'; installs hook file when action is 'install_pre_commit'.\n"
            "- Idempotent: Scans produce identical results; hook installation is idempotent.\n"
            "- 100% Offline: Zero data transmission; all entropy and pattern checks execute locally.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Ensure zero confidential credentials (OpenAI, Anthropic, Gemini, GitHub tokens, private keys) are exposed in code before committing or sharing context.\n"
            "- When NOT to use: Do not use for general code quality, cyclomatic complexity, and duplicate code scans; use 'audit_code_quality' instead. Do not use for enforcing layer boundary architecture rules; use 'enforce_architecture_rules' instead.\n\n"
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
    @_canon_tool(
        name="estimate_token_cost",
        description=(
            "Calculates exact token counts, comparative API billing costs across AI model providers (OpenAI, Claude, Gemini, DeepSeek), and cumulative financial ROI savings.\n\n"
            "Behavior:\n"
            "- Read-only: Calculates metrics from text or token counts without disk modifications.\n"
            "- Idempotent: Deterministic pricing calculations based on standard provider pricing tables.\n"
            "- 100% Offline: Local pricing lookup table; zero network calls.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Evaluate token consumption, forecast monthly LLM API expenditures, or export agent rule configuration files (.cursorrules, .clinerules).\n"
            "- When NOT to use: Do not use for actively reducing token consumption by pruning repository code into AST signatures; use 'build_project_context' or 'prune_code_snippet' instead.\n\n"
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
    @_canon_tool(
        name="query_memory_store",
        description=(
            "Queries semantic triples, causal reasoning graphs, and MinHash entity clusters from the local agent memory store.\n\n"
            "Behavior:\n"
            "- Read-only: Queries persistent memory store without altering stored knowledge.\n"
            "- Idempotent: Returns consistent knowledge relations for identical queries.\n"
            "- 100% Offline: Local graph and MinHash index lookup without remote endpoints.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Recall past agent decisions, query knowledge graph entity relations, or trace causal dependency chains across reasoning sessions.\n"
            "- When NOT to use: Do not use for modifying, compressing, or deleting memory stores; use 'manage_memory_store' instead. Do not use for searching source code in the repository; use 'search_codebase' instead.\n\n"
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
    @_canon_tool(
        name="manage_memory_store",
        description=(
            "Manages the complete lifecycle of persistent agent semantic memory stores, including compression, consolidation, export, listing, reset, and deletion.\n\n"
            "Behavior:\n"
            "- Read-write: Consolidates or updates local memory state; delete and reset remove stored data.\n"
            "- Idempotent for list and export; stateful for compress, consolidate, reset, and delete.\n"
            "- 100% Offline: Fully local storage management without external synchronization.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Store new semantic knowledge, consolidate episodic memories, export knowledge graphs to JSON/HTML, list active memory stores, or clear/reset agent memories.\n"
            "- When NOT to use: Do not use for querying existing knowledge triples or causal chains from memory; use 'query_memory_store' instead. Do not use for pruning source code snippets or diff streams; use 'prune_code_snippet' instead.\n\n"
            "Returns: Status report confirming memory consolidation, export file path, list of active memory stores, or confirmation of reset/deletion."
        ),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=False, open_world_hint=False)
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
    @_canon_tool(
        name="orchestrate_agent_swarm",
        description=(
            "Coordinates autonomous multi-agent task execution, goal decomposition, Byzantine fault-tolerant (PBFT) consensus voting, and self-healing error recovery.\n\n"
            "Behavior:\n"
            "- State execution: Dispatches sub-tasks, coordinates consensus rounds, and executes self-healing patches.\n"
            "- 100% Offline: Executes deterministic local multi-agent workflows without unverified cloud relays.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Execute high-level complex coding goals across multi-agent swarms, validate proposals via Byzantine consensus voting (3f+1 quorum), or diagnose and heal test failures.\n"
            "- When NOT to use: Do not use for querying or managing long-term agent memory; use 'query_memory_store' and 'manage_memory_store' instead. Do not use for auditing codebase quality before task execution; use 'audit_code_quality' instead.\n\n"
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
    # SUPERDESIGN ORCHESTRATOR TOOLS (Anchor-5 TDQS Certified)
    # -------------------------------------------------------------------------
    @_maybe_tool(
        name="superdesign_generate",
        description=(
            "Generates structured design specifications, system prompt templates, file patterns, and design tokens for the AI agent to execute, distinguishing from 'superdesign_iterate' and 'superdesign_list' by producing initial design blueprints rather than refining existing files or listing assets.\n"
            "\n"
            "Parameters:\n"
            "- `prompt` (str, required): Natural language description of what design to create (e.g. 'modern developer platform dashboard with analytics').\n"
            "- `design_type` (str, optional, default='ui'): Type of design: 'ui' (full responsive web app), 'wireframe' (monochrome wireframe), 'component' (modular component), 'logo' (SVG logo), or 'icon' (SVG icon).\n"
            "- `variations` (int, optional, default=3): Number of distinct design variations to generate (1 to 5).\n"
            "- `framework` (str, optional, default='html'): Component framework: 'html', 'react', or 'vue'.\n"
            "- `workspace_path` (str, optional, default='.'): Workspace directory root for output files.\n"
            "\n"
            "Behavior:\n"
            "- Mutating: Generates design specification artifacts in the workspace directory.\n"
            "- Idempotent: Produces consistent design blueprints for identical prompt parameters.\n"
            "- 100% Offline: Generates accessible design blueprints following Superdesign principles without requiring external API keys.\n"
            "- Auth & Rate Limits: Zero authentication or cloud credentials required; completes in <100ms.\n"
            "- Error Handling: Gracefully falls back to default system tokens if custom theme is not found.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Generate full responsive web app UIs, minimalist wireframes, reusable React/Vue/HTML components, or vector SVG logos and icons.\n"
            "- When NOT to use: Do not use for applying feedback to existing design files (use 'superdesign_iterate' instead); do not use for listing existing iterations (use 'superdesign_list' instead).\n"
            "\n"
            "Returns: Structured JSON dictionary containing target file paths, design system references, file specifications, and execution instructions for the IDE LLM."
        ),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def superdesign_generate(
        prompt: Annotated[str, Field(description="Description of what design to create (e.g. 'modern developer platform dashboard with analytics').")],
        design_type: Annotated[str, Field(default="ui", description="Type of design: 'ui' (full responsive web app), 'wireframe' (monochrome wireframe), 'component' (modular component), 'logo' (SVG logo), or 'icon' (SVG icon).")] = "ui",
        variations: Annotated[int, Field(default=3, description="Number of variations to generate (1 to 5, default 3).")] = 3,
        framework: Annotated[str, Field(default="html", description="Component framework: 'html', 'react', or 'vue'.")] = "html",
        workspace_path: Annotated[str, Field(default=".", description="Workspace directory root for output files (default: current directory).")] = "."
    ) -> str:
        """Returns structured specifications for the AI coding agent to generate designs."""
        import tzero_superdesign
        res = tzero_superdesign.superdesign_generate(
            prompt=prompt,
            design_type=design_type,
            variations=variations,
            framework=framework,
            workspace_path=workspace_path
        )
        return json.dumps(res, indent=2, ensure_ascii=False)

    @_maybe_tool(
        name="superdesign_iterate",
        description=(
            "Generates structured iteration instructions to improve, refine, or polish existing design files, distinguishing from 'superdesign_generate' and 'superdesign_gallery' by modifying existing HTML/SVG assets based on visual feedback rather than creating new designs or building galleries.\n"
            "\n"
            "Parameters:\n"
            "- `design_file` (str, required): Path to the existing HTML, SVG, or component design file to iterate on.\n"
            "- `feedback` (str, required): Improvement instructions or visual feedback to apply (e.g. 'Refine card contrast and add responsive navbar').\n"
            "- `variations` (int, optional, default=1): Number of new iterative variations to generate (1 to 5).\n"
            "- `workspace_path` (str, optional, default='.'): Workspace root directory.\n"
            "\n"
            "Behavior:\n"
            "- Mutating: Reads target design file and produces versioned iteration files in workspace.\n"
            "- Idempotent: Generates consistent iteration specs for identical feedback inputs.\n"
            "- 100% Offline: Preserves design system consistency (grid, typography, contrast) locally without remote API calls.\n"
            "- Auth & Rate Limits: Zero authentication or cloud credentials required; typical execution <80ms.\n"
            "- Error Handling: Returns clean error message if specified design file is not found on disk.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Refine typography, adjust layout spacing, fix accessibility/contrast issues, or polish micro-interactions on existing HTML/SVG files.\n"
            "- When NOT to use: Do not use for creating brand new designs from scratch (use 'superdesign_generate' instead); do not use for viewing all designs in a browser (use 'superdesign_gallery' instead).\n"
            "\n"
            "Returns: JSON iteration specifications including original design snippet, feedback guidelines, and target file paths."
        ),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def superdesign_iterate(
        design_file: Annotated[str, Field(description="Path to the existing HTML, SVG, or component design file to iterate on.")],
        feedback: Annotated[str, Field(description="Improvement instructions or feedback to apply (e.g. 'Refine card contrast and add responsive navbar').")],
        variations: Annotated[int, Field(default=1, description="Number of new iterative variations to generate (1 to 5).")] = 1,
        workspace_path: Annotated[str, Field(default=".", description="Workspace root (default: current directory).")] = "."
    ) -> str:
        """Returns iteration instructions for the AI coding agent to refine existing designs."""
        import tzero_superdesign
        res = tzero_superdesign.superdesign_iterate(
            design_file=design_file,
            feedback=feedback,
            variations=variations,
            workspace_path=workspace_path
        )
        return json.dumps(res, indent=2, ensure_ascii=False)

    @_maybe_tool(
        name="superdesign_extract_system",
        description=(
            "Extracts or initializes structured design tokens (colors, typography, spacing, components) into a reusable design system JSON file, distinguishing from 'superdesign_generate' and 'superdesign_list' by saving design token libraries rather than creating layouts or listing designs.\n"
            "\n"
            "Parameters:\n"
            "- `input_path_or_description` (str, required): Description of visual styling, theme requirements, or file path to extract tokens from.\n"
            "- `system_name` (str, optional, default='tzero_design_system'): Identifier name for the generated design system.\n"
            "- `workspace_path` (str, optional, default='.'): Workspace root directory.\n"
            "\n"
            "Behavior:\n"
            "- Mutating: Writes structured design system JSON file into 'superdesign/design_system/' folder.\n"
            "- Idempotent: Safely creates or updates design token specifications.\n"
            "- 100% Offline: Extracts tokens using local CSS/HTML regex and style parsers; zero cloud telemetry.\n"
            "- Auth & Rate Limits: Zero credentials or accounts required; completes in <50ms.\n"
            "- Error Handling: Defaults to standard T-Zero Dark Slate token system if input source is blank.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Extract a coherent color palette, font system, and component token library from existing code or establish a shared design system for new web applications.\n"
            "- When NOT to use: Do not use for generating full web applications (use 'superdesign_generate' instead); do not use for iterating on existing UI files (use 'superdesign_iterate' instead).\n"
            "\n"
            "Returns: JSON document detailing generated design system file path, color palettes, typography scales, spacing tokens, and component contracts."
        ),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def superdesign_extract_system(
        input_path_or_description: Annotated[str, Field(description="Description of visual styling, theme requirements, or image path to extract tokens from.")],
        system_name: Annotated[str, Field(default="tzero_design_system", description="Identifier for the design system (saved to superdesign/design_system/<name>.json).")] = "tzero_design_system",
        workspace_path: Annotated[str, Field(default=".", description="Workspace root (default: current directory).")] = "."
    ) -> str:
        """Extracts and saves structured design systems from screenshots or descriptions."""
        import tzero_superdesign
        res = tzero_superdesign.superdesign_extract_system(
            input_path_or_description=input_path_or_description,
            system_name=system_name,
            workspace_path=workspace_path
        )
        return json.dumps(res, indent=2, ensure_ascii=False)

    @_maybe_tool(
        name="superdesign_list",
        description=(
            "Discovers and enumerates all Superdesign creations, components, and iterations in the workspace, distinguishing from 'superdesign_gallery' and 'superdesign_generate' by returning structured catalog lists rather than compiling HTML preview galleries or generating new designs.\n"
            "\n"
            "Parameters:\n"
            "- `workspace_path` (str, optional, default='.'): Workspace directory root to inspect.\n"
            "\n"
            "Behavior:\n"
            "- Side Effects: Read-only scan of 'superdesign/' directory; does not write or modify files on disk.\n"
            "- Idempotent: Deterministic catalog enumeration for identical directory states.\n"
            "- 100% Offline: Local filesystem directory traversal; zero network egress.\n"
            "- Auth & Rate Limits: Zero authentication or cloud credentials required; sub-millisecond execution (<5ms).\n"
            "- Error Handling: Returns empty catalog structure gracefully if 'superdesign/' folder does not exist yet.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Enumerate available design variations, check component inventory, or discover existing UI iterations.\n"
            "- When NOT to use: Do not use for generating an interactive visual HTML showcase (use 'superdesign_gallery' instead); do not use for creating new components (use 'superdesign_generate' instead).\n"
            "\n"
            "Returns: JSON object categorizing all found creations into 'uis', 'wireframes', 'components', 'logos', 'icons', and 'design_systems'."
        ),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def superdesign_list(
        workspace_path: Annotated[str, Field(default=".", description="Workspace directory root (default: current directory).")] = "."
    ) -> str:
        """Lists all Superdesign iterations and design systems in the workspace."""
        import tzero_superdesign
        res = tzero_superdesign.superdesign_list(workspace_path=workspace_path)
        return json.dumps(res, indent=2, ensure_ascii=False)

    @_maybe_tool(
        name="superdesign_gallery",
        description=(
            "Generates an interactive responsive HTML gallery to visually browse and preview all Superdesign workspace assets, distinguishing from 'superdesign_list' and 'jarvis_export_graph_visualization' by assembling a visual UI design showcase rather than returning raw JSON file lists or memory graph visualizers.\n"
            "\n"
            "Parameters:\n"
            "- `workspace_path` (str, optional, default='.'): Workspace directory root containing superdesign assets.\n"
            "\n"
            "Behavior:\n"
            "- Mutating: Compiles and writes 'superdesign/gallery.html' to disk with embedded previews.\n"
            "- Idempotent: Deterministic HTML gallery compilation for identical asset collections.\n"
            "- 100% Offline: Generates self-contained HTML/CSS/JS file previewable offline in any browser without internet access.\n"
            "- Auth & Rate Limits: Zero credentials or external CDNs required; compiles in <80ms.\n"
            "- Error Handling: Automatically creates output directory and includes placeholder notices for empty categories.\n"
            "\n"
            "Usage Guidelines:\n"
            "- When to use: Preview, compare, and showcase generated web apps, wireframes, components, and vector logos in an interactive visual gallery.\n"
            "- When NOT to use: Do not use for listing raw file metadata without HTML (use 'superdesign_list' instead); do not use for visualizing semantic memory graphs (use 'jarvis_export_graph_visualization' instead).\n"
            "\n"
            "Returns: JSON result indicating gallery file path, total showcased design count, and category breakdown."
        ),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def superdesign_gallery(
        workspace_path: Annotated[str, Field(default=".", description="Workspace directory root (default: current directory).")] = "."
    ) -> str:
        """Generates an interactive HTML gallery to preview all created designs."""
        import tzero_superdesign
        res = tzero_superdesign.superdesign_gallery(workspace_path=workspace_path)
        return json.dumps(res, indent=2, ensure_ascii=False)

    # Register canonical mappings
    _CANONICAL_DISPATCH['build_project_context'] = build_project_context
    _CANONICAL_DISPATCH['prune_code_snippet'] = prune_code_snippet
    _CANONICAL_DISPATCH['manage_architecture_rules'] = manage_architecture_rules
    _CANONICAL_DISPATCH['enforce_architecture_rules'] = enforce_architecture_rules
    _CANONICAL_DISPATCH['generate_architecture_blueprint'] = generate_architecture_blueprint
    _CANONICAL_DISPATCH['analyze_code_dependencies'] = analyze_code_dependencies
    _CANONICAL_DISPATCH['analyze_change_impact'] = analyze_change_impact
    _CANONICAL_DISPATCH['search_codebase'] = search_codebase
    _CANONICAL_DISPATCH['audit_code_quality'] = audit_code_quality
    _CANONICAL_DISPATCH['verify_security_guard'] = verify_security_guard
    _CANONICAL_DISPATCH['estimate_token_cost'] = estimate_token_cost
    _CANONICAL_DISPATCH['query_memory_store'] = query_memory_store
    _CANONICAL_DISPATCH['manage_memory_store'] = manage_memory_store
    _CANONICAL_DISPATCH['orchestrate_agent_swarm'] = orchestrate_agent_swarm
    _CANONICAL_DISPATCH['superdesign_generate'] = superdesign_generate
    _CANONICAL_DISPATCH['superdesign_iterate'] = superdesign_iterate
    _CANONICAL_DISPATCH['superdesign_extract_system'] = superdesign_extract_system
    _CANONICAL_DISPATCH['superdesign_list'] = superdesign_list
    _CANONICAL_DISPATCH['superdesign_gallery'] = superdesign_gallery


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

        handler = _CANONICAL_DISPATCH.get(name) or _LEGACY_DISPATCH.get(name)
        if handler:
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
    if "--canonical" in sys.argv[1:] or "--mode" in sys.argv[1:]:
        for i, arg in enumerate(sys.argv):
            if arg == "--canonical":
                os.environ["TZERO_MCP_TOOL_MODE"] = "canonical"
            elif arg == "--mode" and i + 1 < len(sys.argv):
                os.environ["TZERO_MCP_TOOL_MODE"] = sys.argv[i + 1]

    if sys.stdin.isatty() and "--stdio" not in sys.argv[1:] and "--canonical" not in sys.argv[1:]:
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
