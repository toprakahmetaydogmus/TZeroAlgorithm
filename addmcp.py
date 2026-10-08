# -*- coding: utf-8 -*-
"""Install the bundled T-Zero MCP server into detected IDE configurations.

Supports both a clean Dark GUI and a headless CLI (--all, --list, --targets).
Automatically copies the standalone TZeroMCP runtime or configures the Python script,
guaranteeing zero configuration headaches on any computer.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple


APP_VERSION = "3.0.7"
SERVER_NAME = "tzero"
SERVER_FILENAME = "TZeroMCP.exe"


def _attach_windows_console() -> None:
    """If run from CMD or PowerShell on Windows with --noconsole, attach parent console."""
    if os.name == "nt":
        try:
            import ctypes
            if ctypes.windll.kernel32.AttachConsole(-1):
                if sys.stdout is None or getattr(sys.stdout, "closed", True):
                    sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
                if sys.stderr is None or getattr(sys.stderr, "closed", True):
                    sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")
        except Exception:
            pass


@dataclass(frozen=True)
class ClientTarget:
    key: str
    name: str
    config_path: Path
    root_key: str
    detected: bool


def _get_antigravity_config_path(home: Path) -> Path:
    """Resolves primary Google Antigravity MCP config path."""
    config_in_config = home / ".gemini" / "config" / "mcp_config.json"
    if config_in_config.exists() or (home / ".gemini" / "config").exists():
        return config_in_config
    return home / ".gemini" / "antigravity" / "mcp_config.json"


def _get_claude_desktop_config_path(app_data: Path, local_app_data: Path) -> Tuple[Path, bool]:
    """Resolves Claude Desktop configuration path, handling both MSIX packages and standard AppData."""
    # 1. Standard AppData Roaming
    standard_cfg = app_data / "Claude" / "claude_desktop_config.json"
    if standard_cfg.exists():
        return standard_cfg, True

    # 2. Windows Store / MSIX Package sandboxed Roaming
    packages_dir = local_app_data / "Packages"
    if packages_dir.is_dir():
        for claude_pkg in packages_dir.glob("Claude_*"):
            candidate = claude_pkg / "LocalCache" / "Roaming" / "Claude" / "claude_desktop_config.json"
            if candidate.exists() or (claude_pkg / "LocalCache" / "Roaming" / "Claude").is_dir():
                return candidate, True

    detected = any([
        (app_data / "Claude").exists(),
        (local_app_data / "Programs" / "Claude" / "Claude.exe").exists(),
        bool(list(packages_dir.glob("Claude_*"))) if packages_dir.is_dir() else False,
    ])
    return standard_cfg, detected


def build_client_targets(
    home: Optional[Path] = None,
    app_data: Optional[Path] = None,
    local_app_data: Optional[Path] = None,
    which: Callable[[str], Optional[str]] = shutil.which,
) -> List[ClientTarget]:
    """Return known per-user MCP configs and whether their client is installed."""
    home = Path(home or Path.home())
    app_data = Path(app_data or os.environ.get("APPDATA", home / "AppData/Roaming"))
    local_app_data = Path(
        local_app_data or os.environ.get("LOCALAPPDATA", home / "AppData/Local")
    )
    vscode_user = app_data / "Code" / "User"
    vscode_extensions = home / ".vscode" / "extensions"

    def any_path_exists(*paths: Path) -> bool:
        return any(path.exists() for path in paths)

    def extension_installed(prefix: str) -> bool:
        return bool(list(vscode_extensions.glob(f"{prefix}-*")))

    antigravity_config = _get_antigravity_config_path(home)
    claude_config, claude_detected = _get_claude_desktop_config_path(app_data, local_app_data)

    return [
        ClientTarget(
            "cursor",
            "Cursor",
            home / ".cursor" / "mcp.json",
            "mcpServers",
            any_path_exists(
                home / ".cursor",
                app_data / "Cursor",
                local_app_data / "Programs" / "Cursor" / "Cursor.exe",
            ),
        ),
        ClientTarget(
            "vscode",
            "Visual Studio Code / Copilot",
            home / ".copilot" / "mcp-config.json",
            "mcpServers",
            any_path_exists(
                app_data / "Code",
                local_app_data / "Programs" / "Microsoft VS Code" / "Code.exe",
            )
            or which("code") is not None,
        ),
        ClientTarget(
            "claude-desktop",
            "Claude Desktop",
            claude_config,
            "mcpServers",
            claude_detected,
        ),
        ClientTarget(
            "antigravity",
            "Google Antigravity",
            antigravity_config,
            "mcpServers",
            any_path_exists(
                home / ".gemini" / "config",
                home / ".gemini" / "antigravity",
                local_app_data / "Programs" / "Antigravity" / "Antigravity.exe",
            ),
        ),
        ClientTarget(
            "claude-code",
            "Claude Code",
            home / ".claude.json",
            "mcpServers",
            home.joinpath(".claude.json").exists() or which("claude") is not None,
        ),
        ClientTarget(
            "cline",
            "Cline",
            vscode_user
            / "globalStorage"
            / "saoudrizwan.claude-dev"
            / "settings"
            / "cline_mcp_settings.json",
            "mcpServers",
            (vscode_user / "globalStorage" / "saoudrizwan.claude-dev").exists()
            or extension_installed("saoudrizwan.claude-dev"),
        ),
        ClientTarget(
            "roo-code",
            "Roo Code",
            vscode_user
            / "globalStorage"
            / "rooveterinaryinc.roo-cline"
            / "settings"
            / "mcp_settings.json",
            "mcpServers",
            (vscode_user / "globalStorage" / "rooveterinaryinc.roo-cline").exists()
            or extension_installed("rooveterinaryinc.roo-cline"),
        ),
        ClientTarget(
            "windsurf",
            "Windsurf",
            home / ".codeium" / "windsurf" / "mcp_config.json",
            "mcpServers",
            any_path_exists(
                home / ".codeium" / "windsurf",
                app_data / "Windsurf",
                local_app_data / "Programs" / "Windsurf" / "Windsurf.exe",
            )
            or which("windsurf") is not None,
        ),
        ClientTarget(
            "gemini-cli",
            "Gemini CLI",
            home / ".gemini" / "settings.json",
            "mcpServers",
            home.joinpath(".gemini", "settings.json").exists()
            or which("gemini") is not None,
        ),
    ]


def server_entry(target: ClientTarget, server_path: Path) -> Dict[str, object]:
    """Generates the MCP configuration dictionary block for the target."""
    if server_path.suffix.lower() == ".py":
        entry: Dict[str, object] = {
            "command": sys.executable,
            "args": [str(server_path.resolve())],
        }
    else:
        entry: Dict[str, object] = {
            "command": str(server_path.resolve()),
            "args": [],
        }
    if target.root_key == "servers":
        entry["type"] = "stdio"
    return entry


def _backup_path(path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    return path.with_name(f"{path.name}.backup-{timestamp}")


def merge_server_config(
    target: ClientTarget, server_path: Path, server_name: str = SERVER_NAME
) -> Dict[str, object]:
    """Safely merge one server entry, keeping the rest of the client's config."""
    config: Dict[str, object] = {}
    if target.config_path.exists():
        with target.config_path.open("r", encoding="utf-8-sig") as config_file:
            loaded = json.load(config_file)
        if not isinstance(loaded, dict):
            raise ValueError("Configuration root must be a JSON object")
        config = loaded

    servers = config.get(target.root_key, {})
    if not isinstance(servers, dict):
        raise ValueError(f"'{target.root_key}' must be a JSON object")

    entry = server_entry(target, server_path)
    if servers.get(server_name) == entry:
        if target.key == "antigravity":
            _sync_alternate_antigravity_config(target, server_path, server_name)
        elif target.key == "claude-desktop":
            _sync_alternate_claude_desktop_config(target, server_path, server_name)
        return {"status": "unchanged", "backup": None}

    backup = None
    if target.config_path.exists():
        backup = _backup_path(target.config_path)
        shutil.copy2(target.config_path, backup)

    updated_servers = dict(servers)
    updated_servers[server_name] = entry
    config[target.root_key] = updated_servers
    target.config_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=str(target.config_path.parent),
            prefix=f".{target.config_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            json.dump(config, temporary_file, indent=2, ensure_ascii=False)
            temporary_file.write("\n")
            temporary_path = Path(temporary_file.name)
        os.replace(temporary_path, target.config_path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

    # If this is Google Antigravity or Claude Desktop, sync alternate config paths if present
    if target.key == "antigravity":
        _sync_alternate_antigravity_config(target, server_path, server_name)
    elif target.key == "claude-desktop":
        _sync_alternate_claude_desktop_config(target, server_path, server_name)

    return {"status": "installed", "backup": backup}


def _sync_alternate_antigravity_config(
    target: ClientTarget, server_path: Path, server_name: str
) -> None:
    """Keep ~/.gemini/config/mcp_config.json and ~/.gemini/antigravity/mcp_config.json in sync."""
    try:
        home = Path.home()
        alt_paths = [
            home / ".gemini" / "config" / "mcp_config.json",
            home / ".gemini" / "antigravity" / "mcp_config.json",
        ]
        entry = server_entry(target, server_path)
        for alt_path in alt_paths:
            if alt_path.resolve() == target.config_path.resolve():
                continue
            if alt_path.parent.exists():
                cfg: Dict[str, object] = {}
                if alt_path.exists():
                    try:
                        with alt_path.open("r", encoding="utf-8-sig") as fp:
                            cfg = json.load(fp)
                    except Exception:
                        continue
                if not isinstance(cfg, dict):
                    cfg = {}
                servers = cfg.setdefault("mcpServers", {})
                if isinstance(servers, dict) and servers.get(server_name) != entry:
                    servers[server_name] = entry
                    alt_path.parent.mkdir(parents=True, exist_ok=True)
                    with alt_path.open("w", encoding="utf-8") as fp:
                        json.dump(cfg, fp, indent=2, ensure_ascii=False)
                        fp.write("\n")
        # Also install the /tzero slash skills, plugin, and instructions into Antigravity
        _install_antigravity_skill(server_path)
    except Exception:
        pass


def _install_antigravity_skill(server_path: Optional[Path] = None) -> None:
    """Installs the /tzero slash skills, Antigravity plugin, and MCP instructions."""
    try:
        home = Path.home()
        # 1. Global skills directories
        skills_targets = [
            home / ".gemini" / "config" / "skills",
            home / ".gemini" / "skills",
        ]

        # If running within a git or project workspace, also install workspace skill
        cwd = Path.cwd()
        if (cwd / ".git").is_dir() or (cwd / ".agents").is_dir():
            skills_targets.append(cwd / ".agents" / "skills")

        all_skills = {
            "tzero": _ANTIGRAVITY_SKILL_CONTENT,
            "tzero-tree": _ANTIGRAVITY_TREE_SKILL_CONTENT,
            "tzero-audit": _ANTIGRAVITY_AUDIT_SKILL_CONTENT,
            "tzero-arch": _ANTIGRAVITY_ARCH_SKILL_CONTENT,
        }

        for tool_name, (desc, action) in _MCP_TOOLS_SPEC.items():
            all_skills[tool_name] = f"""---
name: {tool_name}
description: >-
  {desc}
  Activate when the user types "/{tool_name}" or asks to run {tool_name}.
---

# /{tool_name} — T-Zero MCP Tool

{desc}

## Execution
{action}
"""

        for target_base in skills_targets:
            for skill_name, content in all_skills.items():
                s_dir = target_base / skill_name
                s_dir.mkdir(parents=True, exist_ok=True)
                (s_dir / "SKILL.md").write_text(content, encoding="utf-8")

        # 2. Antigravity Plugin (~/.gemini/config/plugins/tzero)
        plugin_dir = home / ".gemini" / "config" / "plugins" / "tzero"
        plugin_dir.mkdir(parents=True, exist_ok=True)
        (plugin_dir / "plugin.json").write_text(_ANTIGRAVITY_PLUGIN_JSON, encoding="utf-8")
        (plugin_dir / "installed_version.json").write_text('{"version": "3.0.7"}\n', encoding="utf-8")

        # Plugin skills
        for skill_name, content in all_skills.items():
            p_skill_dir = plugin_dir / "skills" / skill_name
            p_skill_dir.mkdir(parents=True, exist_ok=True)
            (p_skill_dir / "SKILL.md").write_text(content, encoding="utf-8")

        # Plugin rules
        p_rules_dir = plugin_dir / "rules"
        p_rules_dir.mkdir(parents=True, exist_ok=True)
        (p_rules_dir / "tzero-token-optimization.md").write_text(_ANTIGRAVITY_RULE_CONTENT, encoding="utf-8")

        # Plugin mcp_config.json
        cmd = str(server_path.resolve()) if server_path else str(home / "AppData" / "Local" / "TZeroAlgorithm" / SERVER_FILENAME)
        plugin_mcp = {
            "mcpServers": {
                SERVER_NAME: {
                    "command": cmd,
                    "args": []
                }
            }
        }
        (plugin_dir / "mcp_config.json").write_text(json.dumps(plugin_mcp, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        # 3. Enable plugin in ~/.gemini/config/config.json
        cfg_file = home / ".gemini" / "config" / "config.json"
        if cfg_file.exists():
            try:
                cfg_data = json.loads(cfg_file.read_text(encoding="utf-8-sig"))
                if isinstance(cfg_data, dict):
                    plugins_dict = cfg_data.setdefault("plugins", {})
                    if isinstance(plugins_dict, dict) and "tzero" not in plugins_dict:
                        plugins_dict["tzero"] = {"enabled": True}
                        cfg_file.write_text(json.dumps(cfg_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            except Exception:
                pass

        # 4. MCP instructions in ~/.gemini/antigravity-ide/mcp/tzero/instructions.md
        ide_mcp_dir = home / ".gemini" / "antigravity-ide" / "mcp" / SERVER_NAME
        if ide_mcp_dir.is_dir():
            (ide_mcp_dir / "instructions.md").write_text(_ANTIGRAVITY_MCP_INSTRUCTIONS, encoding="utf-8")

    except Exception:
        pass


_ANTIGRAVITY_SKILL_CONTENT = """---
name: tzero
description: >-
  Enterprise-Grade Codebase Context Architect, AST Signatures Analyzer, & Token Reducer.
  Activate when the user types "/tzero", asks to reduce tokens, scan codebase architecture,
  audit code smells, analyze change impact, enforce architectural boundaries, or optimize prompt context for LLMs.
---

# /tzero — Siber Akademi T-Zero Context Engine

Enterprise-Grade Codebase Context Architect, AST Signatures Analyzer, and Token Reducer.
Cuts LLM context ingestion overhead by up to 95% while preserving structural fidelity for AI agents.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Repository: https://github.com/toprakahmetaydogmus/TZeroAlgorithm

## Slash Command Modes

When the user enters `/tzero [subcommand]` or asks for T-Zero assistance, dispatch to the matching capability:

| Subcommand | Description | Action / Tool |
|:---|:---|:---|
| `/tzero` or `/tzero tree` | Builds full multi-tier hierarchical context tree (T-1 to T-4) with ultra token pruning. | Call `get_project_context_tree` MCP tool |
| `/tzero audit` | Runs AST static code smell check and checks for 100% Zero-Leak security (hardcoded secrets). | Call `audit_codebase_quality` MCP tool |
| `/tzero arch` | Generates system architecture specification (`ARCHITECTURE.md`) with live Mermaid diagrams. | Call `generate_architecture_blueprint` MCP tool |
| `/tzero deps [file]` | Traces internal & external module import topology and dependency graphs. | Call `query_module_dependencies` MCP tool |
| `/tzero impact <symbol>` | Analyzes change impact and blast radius (0-100 score) before modifying a class/function. | Call `analyze_change_impact` MCP tool |
| `/tzero rules` | Generates AI agent instruction files (`.cursorrules`, `.cursor/rules/*.mdc`, `.clinerules`). | Call `export_agent_rules` MCP tool |
| `/tzero search <query>` | Performs 100% private local BM25 hybrid semantic code search without cloud embedding APIs. | Call `search_codebase_semantic` MCP tool |
| `/tzero savings` | Computes quantitative token reduction metrics and team financial ROI savings (USD/month). | Call `get_token_savings_metrics` MCP tool |
| `/tzero boundaries` | Enforces T-4 architectural boundaries defined in `tzero.rules.json` to prevent architectural erosion. | Call `enforce_architecture_boundaries` MCP tool |
| `/tzero repomap` | Generates ultra-compact AST symbol token map for chat context windows. | Call `generate_repo_map` MCP tool |
| `/tzero duplicity` | Scans workspace for duplicate or copy-pasted code blocks (6+ lines) across modules. | Call `find_code_duplicity` MCP tool |
| `/tzero doctor` | Inspects environment, Python runtime, and dependencies. | Run `python -m tzero_deps` or CLI `--doctor` |

## Execution Guidelines

1. **Prefer Native MCP Tools:** When the `tzero` MCP server is registered, invoke the corresponding MCP tool directly (`get_project_context_tree`, `audit_codebase_quality`, etc.).
2. **Fallback to CLI/Engine:** If MCP is temporarily unavailable, use the local CLI `tzero_v3.py` or `TZeroAlgorithm.exe` with matching flags (`--scan`, `--audit`, `--export-arch`, etc.).
3. **100% Zero-Leak Guarantee:** Never output, log, or commit sensitive API keys or user credentials.
4. **Summary & Presentation:** Format the output with clear GitHub-style Markdown, tables, and alerts (`> [!TIP]`, `> [!IMPORTANT]`).
"""

_ANTIGRAVITY_TREE_SKILL_CONTENT = """---
name: tzero-tree
description: >-
  Generate multi-tier hierarchical AST context tree with up to 95% token reduction for AI context ingestion.
  Activate when the user types "/tzero-tree" or asks to build a code tree.
---

# /tzero-tree — AST Hierarchical Context Tree Generator

Generate a multi-tier pruned AST context tree to provide AI agents with full architectural understanding at up to 95% lower token cost.

## Modes & Tiers
- **Tier 1 (T-1):** High-level architectural map & entry points.
- **Tier 2 (T-2):** Public API & class/function signatures with types.
- **Tier 3 (T-3):** Full signatures, method contracts, and docstrings.
- **Tier 4 (T-4):** Full AST graph with import dependencies.

## Execution
Call the `get_project_context_tree` MCP tool with the target path (default: current workspace) and desired tier (default: `T-2`).
"""

_ANTIGRAVITY_AUDIT_SKILL_CONTENT = """---
name: tzero-audit
description: >-
  Run AST static code analysis, code smells check, cyclomatic complexity report, and 100% Zero-Leak security audit for hardcoded secrets.
  Activate when the user types "/tzero-audit" or asks to audit code quality.
---

# /tzero-audit — AST Code Quality & Zero-Leak Security Audit

Perform a comprehensive AST quality audit and verify 100% Zero-Leak security:
1. **Code Smells:** Functions >50 lines, classes >300 lines, high complexity.
2. **Dead Code:** Unused imports and unreferenced private functions.
3. **Security (Zero-Leak):** High-entropy strings, hardcoded API keys, tokens, and credentials.

## Execution
Call the `audit_codebase_quality` MCP tool on the target path (default: `.`).
"""

_ANTIGRAVITY_ARCH_SKILL_CONTENT = """---
name: tzero-arch
description: >-
  Generate complete system architecture specification (ARCHITECTURE.md) with live Mermaid component diagrams.
  Activate when the user types "/tzero-arch" or asks for system architecture blueprint.
---

# /tzero-arch — System Architecture Blueprint Generator

Generate an enterprise-grade architectural specification:
1. Module decomposition and layer boundaries.
2. Inter-module import topology.
3. Interactive Mermaid diagram showing system component relationships.
4. Auto-exports or updates `ARCHITECTURE.md`.

## Execution
Call the `generate_architecture_blueprint` MCP tool on the target path (default: `.`).
"""

_MCP_TOOLS_SPEC = {
    "get_project_context_tree": (
        "Scans target project directory and builds an enterprise-grade multi-tier T-Zero hierarchical context tree (T-1 to T-4) with up to 95% token reduction.",
        "Invoke the `get_project_context_tree` MCP tool with arguments `{\"project_root\": \".\", \"reduction_mode\": \"ultra\"}`."
    ),
    "query_module_dependencies": (
        "Analyzes import/export dependencies, module relationships, and internal vs external package dependencies across codebase or for a specific file.",
        "Invoke the `query_module_dependencies` MCP tool."
    ),
    "query_architecture_boundaries": (
        "Retrieves active T-4 architectural boundaries, operational constraints, and 100% Zero-Leak security rules.",
        "Invoke the `query_architecture_boundaries` MCP tool."
    ),
    "generate_architecture_blueprint": (
        "Generates a complete system architecture specification (ARCHITECTURE.md) including auto-generated Mermaid topology diagrams.",
        "Invoke the `generate_architecture_blueprint` MCP tool."
    ),
    "generate_repo_map": (
        "Generates an ultra-compact AST symbol token map for chat context windows.",
        "Invoke the `generate_repo_map` MCP tool."
    ),
    "audit_codebase_quality": (
        "Performs an AST static code smell audit and 100% Zero-Leak security check for hardcoded secret leaks across workspace files.",
        "Invoke the `audit_codebase_quality` MCP tool."
    ),
    "find_code_duplicity": (
        "Scans workspace for duplicate or copy-pasted code blocks (6+ lines) across modules.",
        "Invoke the `find_code_duplicity` MCP tool."
    ),
    "estimate_token_cost": (
        "Calculates exact token cost comparison across OpenAI, Anthropic, Gemini, DeepSeek models.",
        "Invoke the `estimate_token_cost` MCP tool."
    ),
    "analyze_change_impact": (
        "Analyzes change blast radius (0-100 score) and downstream dependents before modifying a class/function.",
        "Invoke the `analyze_change_impact` MCP tool."
    ),
    "enforce_architecture_boundaries": (
        "Enforces architectural boundary rules defined in tzero.rules.json to prevent architectural erosion.",
        "Invoke the `enforce_architecture_boundaries` MCP tool."
    ),
    "search_codebase_semantic": (
        "Performs 100% private local BM25 hybrid semantic code search across codebase without cloud embedding APIs.",
        "Invoke the `search_codebase_semantic` MCP tool."
    ),
    "export_agent_rules": (
        "Exports AI agent rule specifications (.cursorrules, .clinerules, .cursor/rules/*.mdc).",
        "Invoke the `export_agent_rules` MCP tool."
    ),
    "get_token_savings_metrics": (
        "Computes quantitative token reduction metrics and monthly team financial ROI savings.",
        "Invoke the `get_token_savings_metrics` MCP tool."
    ),
}

_ANTIGRAVITY_PLUGIN_JSON = """{
  "name": "tzero",
  "displayName": "Siber Akademi T-Zero Context Engine",
  "version": "3.0.7",
  "description": "Enterprise-Grade Codebase Context Architect, AST Signatures Analyzer, and Token Reducer. Cuts LLM prompt context by up to 95%, audits code smells & security, enforces architecture boundaries, and traces module dependencies.",
  "suggestedPrompts": [
    "/tzero tree - Build multi-tier AST hierarchical context tree with 95% token savings",
    "/tzero audit - Run AST code quality and 100% Zero-Leak security leak audit",
    "/tzero arch - Generate system architecture specification (ARCHITECTURE.md) with Mermaid diagrams",
    "/tzero impact <symbol> - Analyze blast radius and change impact before editing code",
    "/tzero savings - Compute token reduction metrics and financial ROI"
  ],
  "author": {
    "name": "Toprak Ahmet Aydoğmuş (Siber Akademi)",
    "url": "https://github.com/toprakahmetaydogmus/TZeroAlgorithm"
  },
  "keywords": [
    "tzero",
    "token-reduction",
    "ast",
    "codebase-context",
    "mcp",
    "architecture",
    "security-audit"
  ],
  "homepage": "https://github.com/toprakahmetaydogmus/TZeroAlgorithm",
  "repository": "https://github.com/toprakahmetaydogmus/TZeroAlgorithm",
  "license": "MIT"
}
"""

_ANTIGRAVITY_RULE_CONTENT = """---
description: Suggest using T-Zero MCP tools for token pruning and AST architecture mapping on codebases.
trigger: model_decision
---

# T-Zero Token Efficiency & Architecture Rule

When exploring large repositories or analyzing multi-file impact:
1. Prefer `tzero` MCP tools (`get_project_context_tree`, `analyze_change_impact`, `audit_codebase_quality`) to drastically reduce token usage and preserve context window limit.
2. Ensure Zero-Leak safety before committing or suggesting code with credentials or secrets.
"""

_ANTIGRAVITY_MCP_INSTRUCTIONS = """# T-Zero MCP Server Instructions & Best Practices

T-Zero is an Enterprise-Grade Codebase Context Architect and Token Reduction Engine.
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Repository: https://github.com/toprakahmetaydogmus/TZeroAlgorithm

## When to Use T-Zero MCP Tools:
1. **Large Codebases or Deep Trees:** Before reading massive directories or hundreds of files into prompt context, invoke `get_project_context_tree` with `tier="T-2"` or `tier="T-3"`. This reduces token consumption by up to 95% while keeping all class/function AST signatures and types.
2. **Refactoring & Symbol Edits:** Before modifying, deleting, or renaming functions/classes, call `analyze_change_impact` to assess the blast radius and downstream dependents across the workspace.
3. **Architecture Mapping:** Use `generate_architecture_blueprint` to produce comprehensive `ARCHITECTURE.md` and live Mermaid dependency diagrams.
4. **Code Quality & Security:** Use `audit_codebase_quality` to scan for code smells, cyclomatic complexity, dead code, and hardcoded secrets (100% Zero-Leak check).
5. **Architectural Guardrails:** Enforce boundary rules in `tzero.rules.json` using `enforce_architecture_boundaries` to prevent architectural erosion.
"""


def _sync_alternate_claude_desktop_config(
    target: ClientTarget, server_path: Path, server_name: str
) -> None:
    """Keep standard AppData and Windows Store / MSIX Claude configs in sync."""
    try:
        home = Path.home()
        app_data = Path(os.environ.get("APPDATA", home / "AppData/Roaming"))
        local_app_data = Path(os.environ.get("LOCALAPPDATA", home / "AppData/Local"))
        entry = server_entry(target, server_path)
        candidates = [app_data / "Claude" / "claude_desktop_config.json"]
        packages_dir = local_app_data / "Packages"
        if packages_dir.is_dir():
            for claude_pkg in packages_dir.glob("Claude_*"):
                candidates.append(
                    claude_pkg / "LocalCache" / "Roaming" / "Claude" / "claude_desktop_config.json"
                )
        for alt_path in candidates:
            if alt_path.resolve() == target.config_path.resolve():
                continue
            if alt_path.exists() or alt_path.parent.is_dir():
                cfg: Dict[str, object] = {}
                if alt_path.exists():
                    try:
                        with alt_path.open("r", encoding="utf-8-sig") as fp:
                            cfg = json.load(fp)
                    except Exception:
                        continue
                if not isinstance(cfg, dict):
                    cfg = {}
                servers = cfg.setdefault("mcpServers", {})
                if isinstance(servers, dict) and servers.get(server_name) != entry:
                    servers[server_name] = entry
                    alt_path.parent.mkdir(parents=True, exist_ok=True)
                    with alt_path.open("w", encoding="utf-8") as fp:
                        json.dump(cfg, fp, indent=2, ensure_ascii=False)
                        fp.write("\n")
    except Exception:
        pass


def _resource_path(filename: str) -> Path:
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    path = bundle_root / filename
    if path.is_file():
        return path
    for cand in [
        bundle_root / "dist" / filename,
        Path.cwd() / "dist" / filename,
        Path.cwd() / filename,
        Path(__file__).resolve().parent / "dist" / filename,
    ]:
        if cand.is_file():
            return cand
    return path


def _install_server_binary(
    source: Path, local_app_data: Optional[Path] = None
) -> Path:
    if not source.is_file():
        raise FileNotFoundError(f"Bundled MCP server not found: {source}")

    local_app_data = Path(
        local_app_data or os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")
    )
    destination = local_app_data / "TZeroAlgorithm" / SERVER_FILENAME
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists() and _sha256(source) == _sha256(destination):
        return destination

    if destination.exists():
        shutil.copy2(destination, _backup_path(destination))

    temporary_path = destination.with_name(f".{destination.name}.tmp")
    try:
        shutil.copy2(source, temporary_path)
        os.replace(temporary_path, destination)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    return destination


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_and_install_server() -> Path:
    """Finds TZeroMCP binary or falls back to tzero_mcp.py script."""
    # 1. Check for bundled or built binary
    primary = _resource_path(SERVER_FILENAME)
    if primary.is_file():
        try:
            return _install_server_binary(primary)
        except Exception:
            return primary

    # 2. Candidate folders
    root = Path(__file__).resolve().parent
    for cand in [
        root / "dist" / SERVER_FILENAME,
        Path.cwd() / "dist" / SERVER_FILENAME,
        Path.cwd() / SERVER_FILENAME,
        root / SERVER_FILENAME,
    ]:
        if cand.is_file():
            try:
                return _install_server_binary(cand)
            except Exception:
                return cand

    # 3. Python script fallback
    for script_cand in [
        root / "tzero_mcp.py",
        Path.cwd() / "tzero_mcp.py",
    ]:
        if script_cand.is_file():
            return script_cand.resolve()

    raise FileNotFoundError(
        f"Neither '{SERVER_FILENAME}' nor 'tzero_mcp.py' could be found."
    )


def install_targets(
    targets: List[ClientTarget],
    log_fn: Optional[Callable[[str], None]] = None,
    server_path: Optional[Path] = None,
) -> Tuple[int, int]:
    """Installs server to specified client targets, returning (successes, failures)."""
    if log_fn is None:
        log_fn = lambda msg: print(f"[T-Zero MCP] {msg}")

    if server_path is None:
        server_path = resolve_and_install_server()

    log_fn(f"Runtime resolved: {server_path}")
    successes = 0
    failures = 0
    for target in targets:
        try:
            result = merge_server_config(target, server_path)
            status = str(result["status"]).capitalize()
            log_fn(f"{status}: {target.name} -> {target.config_path}")
            if result.get("backup"):
                log_fn(f"Backup created: {result['backup']}")
            successes += 1
        except Exception as error:
            failures += 1
            log_fn(f"Failed for {target.name}: {error}")

    return successes, failures


class AddMCPApp:
    def __init__(self, root: object):
        import tkinter as tk
        from tkinter import ttk
        self.root = root  # type: ignore
        self.targets = build_client_targets()
        self.check_vars: Dict[str, tk.BooleanVar] = {}
        self.root.title("T-Zero MCP Installer")
        self.root.geometry("720x650")
        self.root.minsize(600, 540)
        self.root.configure(bg="#11151c")

        icon_path = _resource_path("siber_akademi.ico")
        if icon_path.is_file():
            try:
                self.root.iconbitmap(str(icon_path))
            except Exception:
                pass

        self._create_widgets()

    def _create_widgets(self) -> None:
        import tkinter as tk
        from tkinter import ttk

        container = tk.Frame(self.root, bg="#11151c", padx=24, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="SIBER AKADEMI  /  T-ZERO MCP",
            bg="#11151c",
            fg="#22d3ee",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")
        tk.Label(
            container,
            text="Install the bundled local MCP server in supported IDE configurations.",
            bg="#11151c",
            fg="#cbd5e1",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(5, 14))

        self.detected_label = tk.Label(
            container,
            text="Detected clients are selected by default. Existing config files are backed up before changes.",
            bg="#11151c",
            fg="#94a3b8",
            font=("Segoe UI", 9),
            wraplength=660,
            justify="left",
        )
        self.detected_label.pack(anchor="w", pady=(0, 8))

        list_frame = tk.Frame(container, bg="#1a202b", padx=12, pady=8)
        list_frame.pack(fill=tk.BOTH, expand=True)
        for target in self.targets:
            state = "Detected" if target.detected else "Not detected"
            variable = tk.BooleanVar(value=target.detected)
            self.check_vars[target.key] = variable
            row = tk.Frame(list_frame, bg="#1a202b")
            row.pack(fill=tk.X, pady=2)
            tk.Checkbutton(
                row,
                text=target.name,
                variable=variable,
                bg="#1a202b",
                fg="#f1f5f9",
                activebackground="#1a202b",
                activeforeground="#f1f5f9",
                selectcolor="#0f172a",
                font=("Segoe UI", 10),
            ).pack(side=tk.LEFT)
            tk.Label(
                row,
                text=state,
                bg="#1a202b",
                fg="#4ade80" if target.detected else "#64748b",
                font=("Segoe UI", 9),
            ).pack(side=tk.RIGHT, padx=6)

        self.log_text = tk.Text(
            container,
            height=7,
            bg="#080b10",
            fg="#a5f3fc",
            insertbackground="#f8fafc",
            relief=tk.FLAT,
            font=("Consolas", 9),
            state=tk.DISABLED,
        )
        self.log_text.pack(fill=tk.BOTH, expand=False, pady=(12, 8))

        buttons = tk.Frame(container, bg="#11151c")
        buttons.pack(fill=tk.X)
        ttk.Button(buttons, text="Select all", command=self._select_all).pack(side=tk.LEFT)
        self.install_button = ttk.Button(
            buttons, text="Install to selected IDEs", command=self.install_selected
        )
        self.install_button.pack(side=tk.RIGHT)

        tk.Label(
            container,
            text="Zero configuration required. Restart IDEs after installation.",
            bg="#11151c",
            fg="#94a3b8",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(10, 0))

    def _select_all(self) -> None:
        for variable in self.check_vars.values():
            variable.set(True)

    def _log(self, message: str) -> None:
        import tkinter as tk
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def install_selected(self) -> None:
        import tkinter as tk
        from tkinter import messagebox

        selected = [
            target for target in self.targets if self.check_vars[target.key].get()
        ]
        if not selected:
            messagebox.showwarning("T-Zero MCP Installer", "Select at least one client.")
            return

        self.install_button.configure(state=tk.DISABLED)
        try:
            successes, failures = install_targets(selected, log_fn=self._log)
            message = f"Configured {successes} client(s)."
            if failures:
                message += f" {failures} client(s) were skipped; see log."
            messagebox.showinfo("T-Zero MCP Installer", message)
        except Exception as error:
            self._log(f"Installer failed: {error}")
            messagebox.showerror("T-Zero MCP Installer", f"Installer failed: {error}")
        finally:
            self.install_button.configure(state=tk.NORMAL)


def run_cli() -> int:
    """Executes the CLI interface when called from command line or with flags."""
    _attach_windows_console()

    parser = argparse.ArgumentParser(
        prog="addmcp",
        description="T-Zero MCP 1-Click Installer for Cursor, Claude Desktop, Antigravity, VS Code, Windsurf, etc."
    )
    parser.add_argument(
        "--all", "-a", action="store_true",
        help="Install into all detected IDEs without GUI."
    )
    parser.add_argument(
        "--targets", "-t", metavar="KEYS",
        help="Comma-separated list of target keys to install to (e.g. cursor,claude-desktop,antigravity)."
    )
    parser.add_argument(
        "--list", "-l", action="store_true",
        help="List all supported and detected IDE targets."
    )
    parser.add_argument(
        "--gui", "-g", action="store_true",
        help="Explicitly launch the GUI installer window."
    )
    parser.add_argument(
        "--version", "-v", action="version",
        version=f"T-Zero MCP Installer {APP_VERSION}"
    )

    args, unknown = parser.parse_known_args()
    all_targets = build_client_targets()

    if args.list:
        print(f"\n[T-Zero MCP Installer v{APP_VERSION}] Available IDE Targets:\n")
        for t in all_targets:
            state = "DETECTED" if t.detected else "not found"
            print(f"  [{state:^9}] {t.key:<15} : {t.name} ({t.config_path})")
        print()
        return 0

    if args.all or args.targets:
        if args.all:
            selected = [t for t in all_targets if t.detected]
            if not selected:
                print("[T-Zero MCP] No installed IDE clients detected automatically.")
                selected = all_targets
        else:
            keys = [k.strip().lower() for k in args.targets.split(",")]
            selected = [t for t in all_targets if t.key.lower() in keys]

        if not selected:
            print("[T-Zero MCP] No valid targets matched.")
            return 1

        print(f"\n[T-Zero MCP Installer v{APP_VERSION}] Installing to {len(selected)} target(s)...")
        successes, failures = install_targets(selected, log_fn=lambda m: print(f"  -> {m}"))
        print(f"[T-Zero MCP] Completed: {successes} configured, {failures} failed.\n")
        return 0 if failures == 0 else 1

    # Default action: launch GUI if display available, otherwise list targets
    try:
        import tkinter as tk
        root = tk.Tk()
        AddMCPApp(root)
        root.mainloop()
        return 0
    except Exception as e:
        print(f"[T-Zero MCP] GUI unavailable ({e}). Defaulting to automatic CLI install:")
        selected = [t for t in all_targets if t.detected]
        if not selected:
            selected = all_targets
        successes, failures = install_targets(selected, log_fn=lambda m: print(f"  -> {m}"))
        return 0 if failures == 0 else 1


def main() -> None:
    sys.exit(run_cli())


if __name__ == "__main__":
    main()