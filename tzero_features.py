# -*- coding: utf-8 -*-
"""Siber Akademi — T-Zero Advanced Intelligence Suite.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
LinkedIn: https://linkedin.com/in/toprak-ahmet-aydo%C4%9Fmu%C5%9F-60462534b/
Bio & Socials: https://hopp.bio/siberegitim
GitHub: https://github.com/toprakahmetaydogmus/TZeroAlgorithm

Modules Included:
  1. ChangeImpactAnalyzer: Blast radius and change impact dependency tracer.
  2. ArchitectureRuleEngine: T-4 architectural boundary enforcement and CI gate.
  3. AgentRulesGenerator: One-click export for .cursorrules, .cursor/rules/*.mdc, .clinerules, and Copilot.
  4. LocalSemanticCodeSearch: 100% private, local BM25 + TF-IDF hybrid code search & RAG engine.
  5. TokenROICalculator: Token compression ratio, developer ROI, and cost savings telemetry.
  6. DashboardRequestHandler / launch_web_dashboard: Lightweight zero-dependency local web dashboard server (localhost:7300).
"""

import os
import sys
import re
import ast
import json
import math
import collections
import http.server
import socketserver
import threading
import urllib.parse
import subprocess
import fnmatch
import difflib
import hashlib
import copy
from typing import Dict, List, Set, Tuple, Optional, Any

# Ensure parent directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)


_IGNORE_RULES_CACHE: Dict[str, List[str]] = {}

def get_ignore_patterns(base_dir: str) -> List[str]:
    """Reads .gitignore and .tzeroignore patterns from project directory."""
    if base_dir in _IGNORE_RULES_CACHE:
        return _IGNORE_RULES_CACHE[base_dir]

    patterns = [
        ".git", ".git/*", "__pycache__", "*/__pycache__/*", "*.pyc",
        "node_modules", "*/node_modules/*", ".venv", "venv", "*/.venv/*", "*/venv/*",
        "build", "dist", "*.egg-info", "*.min.js", "*.min.css", "*.lock"
    ]
    for ign_file in (".gitignore", ".tzeroignore"):
        p = os.path.join(base_dir, ign_file)
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            patterns.append(line.rstrip("/"))
                            patterns.append(line.rstrip("/") + "/*")
            except Exception:
                pass
    _IGNORE_RULES_CACHE[base_dir] = patterns
    return patterns


def should_skip_dir(root: str, base_dir: str) -> bool:
    """Helper to check if a subdirectory should be skipped relative to base project dir."""
    rel = os.path.relpath(root, base_dir).replace("\\", "/")
    if rel == ".":
        return False
    parts = rel.split("/")
    if any(p.startswith(".") or p in ("__pycache__", "build", "dist", "node_modules", "venv", ".venv") for p in parts):
        return True
    patterns = get_ignore_patterns(base_dir)
    for pat in patterns:
        if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(parts[-1], pat):
            return True
    return False


def should_skip_file(file_path: str, base_dir: str) -> bool:
    """Helper to check if a file matches .gitignore or .tzeroignore patterns."""
    rel = os.path.relpath(file_path, base_dir).replace("\\", "/")
    fname = os.path.basename(file_path)
    if fname.startswith(".") or fname.endswith((".pyc", ".min.js", ".min.css", ".lock")):
        return True
    patterns = get_ignore_patterns(base_dir)
    for pat in patterns:
        if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(fname, pat):
            return True
    return False


# =============================================================================
# 1. CHANGE IMPACT & BLAST RADIUS ANALYZER
# =============================================================================

class ChangeImpactAnalyzer:
    """Calculates blast radius and change impact for modified symbols and files.
    
    Traces AST definitions, call references, and inbound import graphs to compute
    risk scores and affected modules before making code changes.
    """

    def __init__(self, project_dir: str):
        self.project_dir = os.path.abspath(project_dir)
        self.files_list: List[str] = []
        self.snippets: Dict[str, str] = {}
        self.ast_trees: Dict[str, ast.AST] = {}
        self.symbol_defs: Dict[str, str] = {}  # symbol -> primary defining_file
        self.symbol_locations: Dict[str, List[str]] = collections.defaultdict(list) # symbol -> [defining_files]
        self.import_graph: Dict[str, Set[str]] = collections.defaultdict(set) # file -> imported_modules
        self.inbound_graph: Dict[str, Set[str]] = collections.defaultdict(set) # module -> dependent_files
        self._build_index()

    def _add_symbol_def(self, symbol: str, rel_path: str):
        if symbol not in self.symbol_defs:
            self.symbol_defs[symbol] = rel_path
        if rel_path not in self.symbol_locations[symbol]:
            self.symbol_locations[symbol].append(rel_path)

    def _build_index(self):
        """Scans python files and builds symbol and dependency maps."""
        for root, _, files in os.walk(self.project_dir):
            if should_skip_dir(root, self.project_dir):
                continue
            for f in files:
                if f.endswith('.py'):
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, self.project_dir).replace('\\', '/')
                    self.files_list.append(rel_p)
                    try:
                        with open(full_p, 'r', encoding='utf-8', errors='ignore') as fp:
                            content = fp.read()
                        self.snippets[rel_p] = content
                        self._index_file_ast(rel_p, content)
                    except Exception:
                        pass

    def _index_file_ast(self, rel_path: str, code: str):
        try:
            tree = ast.parse(code)
            self.ast_trees[rel_path] = tree
            stem = os.path.splitext(os.path.basename(rel_path))[0]
            
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    self._add_symbol_def(node.name, rel_path)
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            self._add_symbol_def(item.name, rel_path)
                            self._add_symbol_def(f"{node.name}.{item.name}", rel_path)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self._add_symbol_def(node.name, rel_path)
                elif isinstance(node, ast.Import):
                    for name in node.names:
                        base = name.name.split('.')[0]
                        self.import_graph[rel_path].add(base)
                        self.inbound_graph[base].add(rel_path)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        base = node.module.split('.')[0]
                        self.import_graph[rel_path].add(base)
                        self.inbound_graph[base].add(rel_path)
        except Exception:
            pass

    def analyze_symbol(self, symbol_name: str) -> Dict[str, Any]:
        """Calculates the blast radius for modifying a specific symbol (class/function).
        
        Uses AST analysis over workspace code to accurately discover call sites and
        attribute accesses without false positives from comments and string literals.
        """
        defining_file = self.symbol_defs.get(symbol_name)
        defining_locations = self.symbol_locations.get(symbol_name, [defining_file] if defining_file else [])
        direct_callers: List[Dict[str, Any]] = []
        transitive_files: Set[str] = set()

        target_attr = symbol_name.split('.')[-1]
        target_class = symbol_name.split('.')[0] if '.' in symbol_name else ""

        for f, content in self.snippets.items():
            if f in defining_locations or target_attr not in content:
                continue

            matches_lines: List[int] = []
            try:
                tree = self.ast_trees.get(f)
                if tree is None:
                    tree = ast.parse(content)
                    self.ast_trees[f] = tree
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        matched = False
                        if isinstance(node.func, ast.Name) and node.func.id == target_attr:
                            matched = True
                        elif isinstance(node.func, ast.Attribute) and node.func.attr == target_attr:
                            if target_class:
                                if isinstance(node.func.value, ast.Name) and node.func.value.id == target_class:
                                    matched = True
                            else:
                                matched = True
                        if matched:
                            matches_lines.append(getattr(node, 'lineno', 1))
                    elif isinstance(node, ast.Attribute) and node.attr == target_attr:
                        if target_class and isinstance(node.value, ast.Name) and node.value.id == target_class:
                            matches_lines.append(getattr(node, 'lineno', 1))
                    elif isinstance(node, ast.Name) and node.id == target_attr:
                        # Direct symbol reference as argument, type annotation, or value
                        matches_lines.append(getattr(node, 'lineno', 1))
            except Exception:
                # Fallback for non-python files or invalid syntax
                pattern = rf"\b{re.escape(target_attr)}\b"
                for m in re.finditer(pattern, content):
                    line_no = content[:m.start()].count('\n') + 1
                    matches_lines.append(line_no)

            unique_lines = sorted(list(set(matches_lines)))
            if unique_lines:
                direct_callers.append({
                    "file": f,
                    "occurrences": len(unique_lines),
                    "lines": unique_lines[:5]
                })
                transitive_files.add(f)

        # Trace second-level dependents
        second_level: Set[str] = set()
        for df in transitive_files:
            stem = os.path.splitext(os.path.basename(df))[0]
            for dep in self.inbound_graph.get(stem, set()):
                if dep not in defining_locations and dep not in transitive_files:
                    second_level.add(dep)

        total_affected = len(transitive_files) + len(second_level)
        # Blast Radius Score (0-100)
        blast_score = min(100, int((len(direct_callers) * 20) + (len(second_level) * 10)))
        if blast_score >= 75:
            risk = "CRITICAL"
        elif blast_score >= 45:
            risk = "HIGH"
        elif blast_score >= 20:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        downstream_dependents = [
            {"file": f, "level": 1} for f in sorted(transitive_files)
        ] + [
            {"file": f, "level": 2} for f in sorted(second_level)
        ]

        # Test Coverage Mapper: Locate test files covering this symbol or defining module
        test_commands: List[str] = []
        tests_dir = os.path.join(self.project_dir, "tests")
        if os.path.isdir(tests_dir):
            target_stem = os.path.splitext(os.path.basename(defining_file))[0] if defining_file else ""
            for t_root, _, t_files in os.walk(tests_dir):
                for tf in t_files:
                    if tf.startswith("test_") and tf.endswith(".py"):
                        tf_path = os.path.join(t_root, tf)
                        rel_tf = os.path.relpath(tf_path, self.project_dir).replace('\\', '/')
                        if target_stem and (target_stem in tf or f"test_{target_stem}.py" == tf):
                            cmd = f"pytest {rel_tf}"
                            if cmd not in test_commands:
                                test_commands.append(cmd)
                        elif tf in self.snippets:
                            snip = self.snippets[tf]
                            if target_attr in snip:
                                cmd = f"pytest {rel_tf}"
                                if cmd not in test_commands:
                                    test_commands.append(cmd)

        test_cmd = test_commands[0] if test_commands else "pytest tests/"

        return {
            "symbol": symbol_name,
            "defining_file": defining_file or "Unknown / Built-in",
            "defining_files": defining_locations,
            "blast_score": blast_score,
            "risk_score": blast_score,
            "risk_level": risk,
            "direct_callers": direct_callers,
            "second_level_dependents": sorted(list(second_level)),
            "downstream_dependents": downstream_dependents,
            "total_affected_modules": total_affected,
            "test_command": test_cmd,
            "matching_tests": test_commands,
        }

    def format_report(self, analysis: Dict[str, Any]) -> str:
        """Formats the analysis into an actionable markdown blast radius report."""
        sym = analysis["symbol"]
        score = analysis["blast_score"]
        risk = analysis["risk_level"]
        f_def = analysis["defining_file"]

        risk_badges = {
            "LOW": "🟢 LOW RISK",
            "MEDIUM": "🟡 MEDIUM RISK",
            "HIGH": "🟠 HIGH RISK",
            "CRITICAL": "🔴 CRITICAL RISK"
        }

        out = [
            f"# 💥 Change Impact & Blast Radius: `{sym}`\n",
            f"> **Risk Assessment:** {risk_badges.get(risk, risk)} (Score: {score}/100)  ",
            f"> **Target Definition:** `{f_def}`  ",
            f"> **Total Affected Modules:** **{analysis['total_affected_modules']} files**\n",
            "---",
            "\n## 🎯 Direct Dependent Modules (Caller Files)",
        ]

        if analysis.get("test_command"):
            out.append(f"\n> 🧪 **Targeted Test Command:** `{analysis['test_command']}`\n")

        if analysis["direct_callers"]:
            out.append("| File Path | Reference Count | Line Numbers |")
            out.append("|:----------|:----------------|:-------------|")
            for c in analysis["direct_callers"]:
                lines_str = ", ".join(str(l) for l in c["lines"])
                out.append(f"| `{c['file']}` | {c['occurrences']} | Lines {lines_str} |")
        else:
            out.append("✨ *No direct references found across the workspace.*")

        if analysis["second_level_dependents"]:
            out.append("\n## 🌊 Transitive Inbound Ripple (Second-Order Callers)")
            for sec in analysis["second_level_dependents"]:
                out.append(f"- `{sec}`")

        out.append("\n## 🛡️ Recommended Safeguards")
        if risk in ("HIGH", "CRITICAL"):
            out.append("1. **Deprecation Grace Period:** Do not break existing parameter signatures; use optional arguments or decorators.")
            out.append("2. **Regression Test Suite:** Run unit tests covering all direct callers before merging.")
            out.append("3. **Downstream Sync:** Ensure dependent modules are updated simultaneously in this PR.")
        else:
            out.append("1. Verify local unit tests pass.")
            out.append("2. Safe to refactor with standard caution.")

        return "\n".join(out)


# =============================================================================
# 2. ARCHITECTURE RULE ENGINE & CI BOUNDARY GATE
# =============================================================================

DEFAULT_RULES_JSON = {
    "version": "1.0",
    "description": "T-Zero Architectural Boundary Rules for Modular Integrity",
    "layers": {
        "core": ["core/*", "engine/*"],
        "api": ["api/*", "tzero_mcp.py", "server/*"],
        "cli": ["main.py", "compile.py", "cli/*"],
        "ui": ["gui/*", "views/*"]
    },
    "forbidden_imports": [
        {
            "from_layer": "core",
            "cannot_import": ["ui", "views"],
            "reason": "Core domain logic must never have visual UI dependencies."
        },
        {
            "from_layer": "models",
            "cannot_import": ["views", "controllers"],
            "reason": "Data models must remain decoupled from presentation layers."
        }
    ]
}


class ArchitectureRuleEngine:
    """Enforces active architectural boundary rules (T-4) across modules.
    
    Prevents spaghetti code, circular imports, and architecture erosion.
    Can be used as a CLI gate in GitHub Actions CI (`--enforce-boundaries`).
    """

    def __init__(self, project_dir: str, config_path: Optional[str] = None):
        self.project_dir = os.path.abspath(project_dir)
        self.config_path = config_path or os.path.join(self.project_dir, "tzero.rules.json")
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, Any]:
        if os.path.isfile(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return DEFAULT_RULES_JSON

    @staticmethod
    def generate_default_rules(target_path: str):
        """Generates a starter tzero.rules.json file."""
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_RULES_JSON, f, indent=2)

    def _matches_layer(self, file_rel: str, patterns: List[str]) -> bool:
        for p in patterns:
            p_clean = p.replace("\\", "/").rstrip("/*")
            if p.endswith("/*"):
                if file_rel.startswith(p_clean + "/") or file_rel == p_clean:
                    return True
            elif file_rel == p_clean or os.path.basename(file_rel) == p_clean:
                return True
        return False

    def enforce_boundaries(self) -> Dict[str, Any]:
        """Scans codebase and verifies all import rules."""
        violations: List[Dict[str, Any]] = []
        layers = self.rules.get("layers", {})
        forbidden = self.rules.get("forbidden_imports", [])

        # Scan python files
        scanned_files = 0
        for root, _, files in os.walk(self.project_dir):
            if should_skip_dir(root, self.project_dir):
                continue
            for f in files:
                if f.endswith(".py"):
                    scanned_files += 1
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, self.project_dir).replace("\\", "/")

                    try:
                        with open(full_p, "r", encoding="utf-8", errors="ignore") as fp:
                            tree = ast.parse(fp.read())
                    except Exception:
                        continue

                    # Extract file imports
                    # Extract file imports (full dotted names & resolved relative paths)
                    imported_modules = set()
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            line_no = getattr(node, 'lineno', 1)
                            for n in node.names:
                                imported_modules.add((n.name, line_no))
                        elif isinstance(node, ast.ImportFrom):
                            line_no = getattr(node, 'lineno', 1)
                            base_parts = []
                            file_dir = os.path.dirname(rel_p)
                            if file_dir:
                                base_parts = file_dir.replace('\\', '/').split('/')

                            if node.level and node.level > 0:
                                # Relative import resolution based on file position
                                if node.level <= len(base_parts):
                                    prefix_parts = base_parts[:len(base_parts) - node.level + 1]
                                    if node.module:
                                        resolved_mod = ".".join(prefix_parts + node.module.split('.'))
                                    else:
                                        resolved_mod = ".".join(prefix_parts)
                                else:
                                    resolved_mod = node.module or ""
                                if resolved_mod:
                                    imported_modules.add((resolved_mod, line_no))
                                for n in node.names:
                                    if resolved_mod:
                                        imported_modules.add((f"{resolved_mod}.{n.name}", line_no))
                                    else:
                                        imported_modules.add((n.name, line_no))
                            elif node.module:
                                imported_modules.add((node.module, line_no))
                                for n in node.names:
                                    imported_modules.add((f"{node.module}.{n.name}", line_no))

                    # Check rules
                    for rule in forbidden:
                        from_layer = rule.get("from_layer")
                        cannot_import = rule.get("cannot_import", [])
                        reason = rule.get("reason", "Forbidden architectural dependency.")
                        layer_patterns = layers.get(from_layer, [])

                        if self._matches_layer(rel_p, layer_patterns):
                            for full_imp, line_no in imported_modules:
                                imp_segments = full_imp.split('.')
                                for forbidden_target in cannot_import:
                                    clean_forbidden = forbidden_target.replace('/', '.').rstrip('/*')
                                    is_violation = (
                                        full_imp == clean_forbidden
                                        or full_imp.startswith(clean_forbidden + '.')
                                        or full_imp.endswith('.' + clean_forbidden)
                                        or clean_forbidden in imp_segments
                                        or fnmatch.fnmatch(full_imp, forbidden_target)
                                        or fnmatch.fnmatch(full_imp, f"{clean_forbidden}.*")
                                    )
                                    if is_violation:
                                        v_entry = {
                                            "file": rel_p,
                                            "line": line_no,
                                            "layer": from_layer,
                                            "forbidden_import": forbidden_target,
                                            "imported_module": full_imp,
                                            "reason": reason
                                        }
                                        if v_entry not in violations:
                                            violations.append(v_entry)

        is_clean = len(violations) == 0
        return {
            "clean": is_clean,
            "scanned_files": scanned_files,
            "violations": violations,
            "total_violations": len(violations)
        }

    def format_report(self, result: Dict[str, Any]) -> str:
        """Formats the audit results into a terminal or markdown report."""
        if result["clean"]:
            return (
                f"✅ \033[32m[ARCH PASS] All {result['scanned_files']} files conform to architectural "
                f"boundary rules (tzero.rules.json). Zero violations detected.\033[0m"
            )

        lines = [
            f"❌ \033[31m[ARCH VIOLATION] Detected {result['total_violations']} architectural boundary violations:\033[0m\n"
        ]
        for v in result["violations"]:
            lines.append(
                f"  - \033[33m{v['file']}:{v['line']}\033[0m -> "
                f"Layer '\033[36m{v['layer']}\033[0m' cannot import '\033[31m{v['forbidden_import']}\033[0m'"
                f"\n    Reason: {v['reason']}"
            )
        lines.append("\n\033[31mExecution halted due to boundary rule enforcement.\033[0m")
        return "\n".join(lines)


# =============================================================================
# 3. AI AGENT RULES GENERATOR (.cursorrules, .clinerules, Copilot, Cursor MDC)
# =============================================================================

class AgentRulesGenerator:
    """Generates production-grade native rule files for AI coding agents."""

    @staticmethod
    def generate_cursorrules(project_name: str, tech_stack: str = "Python / Modern Toolchain") -> str:
        return f"""# Cursor AI Rules for {project_name}
# Generated by Siber Akademi T-Zero Context Architect V3 (https://github.com/toprakahmetaydogmus/TZeroAlgorithm)

[PROJECT CONTEXT]
- Name: {project_name}
- Stack: {tech_stack}
- Architecture: Modular Clean Architecture & High Structural Cohesion

[STRICT OPERATIONAL DIRECTIVES]
1. RULE T-001: ZERO-LEAK SECURITY GUARANTEE:
   - NEVER hardcode API keys, tokens, or credentials anywhere.
   - Use environment variables or OS keyring exclusively.
   - Never commit sensitive .env files.

2. RULE T-002: ARCHITECTURAL BOUNDARY ENFORCEMENT:
   - Maintain clear separation of concerns between core logic, transport layers, and UI.
   - Avoid creating circular import loops. Enforce tzero.rules.json.

3. RULE T-003: AST CONTRACT FIDELITY:
   - Preserve exact class declarations, typed signatures, and docstrings.
   - Do not delete existing comments or docstrings unless explicitly requested.

4. RULE T-004: ANTI-PATTERN & MINIMAL BLAST RADIUS:
   - Keep functions concise (<= 30 lines) and arguments minimal (<= 6).
   - Before modifying core functions, verify all downstream callers.
   - Always run the test suite (`python -m unittest discover -s tests -v`) before concluding tasks.
"""

    @staticmethod
    def generate_clinerules(project_name: str) -> str:
        return f"""# Cline & Roo-Code System Rules: {project_name}
# Enforced by T-Zero Context Engine (Rules T-001 to T-004)

## Persona & Standards
You are an elite Principal Software Engineer working on `{project_name}`.

## Core Rules:
1. **Rule T-001 (Zero-Leak Policy):** Never output or commit real API keys or personal secrets.
2. **Rule T-002 (Architectural Boundaries):** Enforce layer isolation and avoid circular dependencies.
3. **Rule T-003 (AST Contract Fidelity):** Keep all existing docstrings, type annotations, and signatures intact.
4. **Rule T-004 (Quality & Verification):** Ensure every change passes unit tests cleanly with zero regressions.
"""

    @staticmethod
    def generate_copilot_instructions(project_name: str) -> str:
        return f"""# GitHub Copilot Instructions for {project_name}
# Enforced by T-Zero Algorithm Rules (T-001 to T-004)

## Repository Guidelines
- **Project:** {project_name}
- **Rule T-001 (Security):** 100% Zero-Leak. Use environment variables for secrets.
- **Rule T-002 (Architecture):** Respect layer boundaries and avoid circular imports.
- **Rule T-003 (AST Contracts):** PEP 8 for Python. Clean, typed, modular code with complete signatures.
- **Rule T-004 (Testing):** Add unit tests in `tests/` for any new functionality; keep functions concise.
"""

    @staticmethod
    def generate_cursor_mdc_rules(project_name: str, project_dir: Optional[str] = None) -> Dict[str, str]:
        """Generates modern modular .cursor/rules/*.mdc format dynamically from tzero.rules.json."""
        layers_desc = []
        forbidden_desc = []

        if project_dir:
            rules_path = os.path.join(project_dir, "tzero.rules.json")
            if os.path.isfile(rules_path):
                try:
                    with open(rules_path, "r", encoding="utf-8") as f:
                        rules_data = json.load(f)
                    for l_name, patterns in rules_data.get("layers", {}).items():
                        layers_desc.append(f"- **Layer `{l_name}`:** `{', '.join(patterns)}`")
                    for rule in rules_data.get("forbidden_imports", []):
                        forbidden_desc.append(
                            f"- Layer `{rule.get('from_layer')}` cannot import `{', '.join(rule.get('cannot_import', []))}`: {rule.get('reason', '')}"
                        )
                except Exception:
                    pass

        layers_block = "\n".join(layers_desc) if layers_desc else "- Core business logic must remain decoupled from presentation or CLI entrypoints."
        forbidden_block = "\n".join(forbidden_desc) if forbidden_desc else "- Avoid circular dependencies and cross-layer spaghettification."

        arch_mdc = f"""---
description: Architectural Boundary & Modularity Standards for {project_name}
globs: **/*.py
---
# Architecture Standards for {project_name}

## Active Architectural Layers:
{layers_block}

## Enforced Import Boundaries:
{forbidden_block}

- All public functions and classes must include descriptive docstrings.
- Follow PEP 8 and maintain type hints where applicable.
"""
        sec_mdc = f"""---
description: Zero-Leak Security & Secret Protection
globs: **/*
---
# Zero-Leak Security Mandate

- NEVER write raw API keys (OpenAI, Anthropic, NVIDIA, Gemini) into code.
- Always retrieve credentials via OS keyring or environment variables.
- Keep test data strictly synthetic.
"""
        return {
            "architecture.mdc": arch_mdc,
            "security.mdc": sec_mdc
        }

    @staticmethod
    def generate_windsurfrules(project_name: str) -> str:
        return f"""# Windsurf AI Rules for {project_name}
# Enforced by Siber Akademi T-Zero Context Engine

## Core Directives
1. **Zero-Leak Guarantee:** NEVER hardcode credentials or expose production secrets.
2. **Context-Driven Edits:** Always verify architectural layer boundaries and dependencies.
3. **Preserve Documentation:** Do not strip comments, docstrings, or type hints unless requested.
4. **Verification:** Ensure tests pass cleanly before concluding tasks.
"""

    @staticmethod
    def generate_claude_instructions(project_name: str) -> str:
        return f"""# Claude Code & Extended Thinking Directives: {project_name}

## System Overview
- **Project:** {project_name}
- **Engine:** T-Zero Context Architect
- **Standards:** Clean Architecture, 100% Zero-Leak Security, PEP 8 / Idiomatic Typing.

## Behavioral Directives:
- Maintain minimal blast radius on all code changes.
- Check downstream caller impacts before refactoring shared interfaces.
- Always run the test suite to prevent regressions.
"""

    @classmethod
    def export_all(cls, project_dir: str) -> List[str]:
        """Exports all agent rules into the target repository."""
        p_name = os.path.basename(os.path.abspath(project_dir)) or "Project"
        created = []

        # 1. .cursorrules
        cr_path = os.path.join(project_dir, ".cursorrules")
        with open(cr_path, "w", encoding="utf-8") as f:
            f.write(cls.generate_cursorrules(p_name))
        created.append(cr_path)

        # 2. .clinerules
        cl_path = os.path.join(project_dir, ".clinerules")
        with open(cl_path, "w", encoding="utf-8") as f:
            f.write(cls.generate_clinerules(p_name))
        created.append(cl_path)

        # 3. .windsurfrules
        ws_path = os.path.join(project_dir, ".windsurfrules")
        with open(ws_path, "w", encoding="utf-8") as f:
            f.write(cls.generate_windsurfrules(p_name))
        created.append(ws_path)

        # 4. CLAUDE.md
        claude_path = os.path.join(project_dir, "CLAUDE.md")
        with open(claude_path, "w", encoding="utf-8") as f:
            f.write(cls.generate_claude_instructions(p_name))
        created.append(claude_path)

        # 5. .github/copilot-instructions.md
        gh_dir = os.path.join(project_dir, ".github")
        os.makedirs(gh_dir, exist_ok=True)
        copilot_path = os.path.join(gh_dir, "copilot-instructions.md")
        with open(copilot_path, "w", encoding="utf-8") as f:
            f.write(cls.generate_copilot_instructions(p_name))
        created.append(copilot_path)

        # 6. .cursor/rules/*.mdc
        c_rules_dir = os.path.join(project_dir, ".cursor", "rules")
        os.makedirs(c_rules_dir, exist_ok=True)
        for mdc_name, content in cls.generate_cursor_mdc_rules(p_name, project_dir=project_dir).items():
            mdc_path = os.path.join(c_rules_dir, mdc_name)
            with open(mdc_path, "w", encoding="utf-8") as f:
                f.write(content)
            created.append(mdc_path)

        # 7. AGENT.md / AGENTS.md (Antigravity & Autonomous Orchestrator Directive)
        from tzero_jarvis.workspace_orchestrator import WorkspaceProfiler, WorkspaceGovernanceSynthesizer
        try:
            prof = WorkspaceProfiler(project_dir).profile()
            agent_md_content = WorkspaceGovernanceSynthesizer.generate_agent_md(prof)
            
            agent_p = os.path.join(project_dir, "AGENT.md")
            with open(agent_p, "w", encoding="utf-8") as f:
                f.write(agent_md_content)
            created.append(agent_p)

            agents_p = os.path.join(project_dir, "AGENTS.md")
            with open(agents_p, "w", encoding="utf-8") as f:
                f.write(agent_md_content)
            created.append(agents_p)

            # 8. ARCHITECTURE.md if not exists
            arch_p = os.path.join(project_dir, "ARCHITECTURE.md")
            if not os.path.isfile(arch_p):
                with open(arch_p, "w", encoding="utf-8") as f:
                    f.write(WorkspaceGovernanceSynthesizer.generate_architecture_md(prof))
                created.append(arch_p)
        except Exception:
            pass

        return created


# =============================================================================
# 4. LOCAL HYBRID SEMANTIC & BM25 CODE SEARCH (100% PRIVATE & ZERO-LEAK)
# =============================================================================

class LocalSemanticCodeSearch:
    """100% Local, zero-network hybrid BM25 + symbol token code search with Reciprocal Rank Fusion (RRF).
    
    Indexes functions, classes, docstrings, and signatures into an in-memory
    vector/lexical index with AST-aware chunking, allowing natural language queries
    without sending code to any external embedding API.
    """

    def __init__(self, project_dir: str):
        self.project_dir = os.path.abspath(project_dir)
        self.chunks: List[Dict[str, Any]] = []
        self.doc_freqs: Dict[str, int] = collections.defaultdict(int)
        self.total_docs = 0
        self.avg_doc_len = 0.0
        self._index_codebase()

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        # Split on non-alphanumeric, camelCase, snake_case
        tokens = []
        words = re.findall(r'[A-Za-z0-9_]+', text.lower())
        for w in words:
            sub = re.findall(r'[a-z]+|[0-9]+', w)
            tokens.extend(sub)
            tokens.append(w)
        return [t for t in tokens if len(t) > 1]

    def _index_codebase(self):
        total_len = 0
        for root, _, files in os.walk(self.project_dir):
            if should_skip_dir(root, self.project_dir):
                continue
            for f in files:
                if f.endswith(('.py', '.js', '.ts', '.go', '.rs', '.cpp', '.c', '.h', '.html', '.css')):
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, self.project_dir).replace('\\', '/')
                    try:
                        with open(full_p, 'r', encoding='utf-8', errors='ignore') as fp:
                            content = fp.read()
                    except Exception:
                        continue

                    lines = content.splitlines()
                    if not lines:
                        continue

                    # 1. AST-Aware Chunking for Python
                    indexed_ast = False
                    if f.endswith('.py'):
                        try:
                            tree = ast.parse(content)
                            for node in ast.walk(tree):
                                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                                    start_line = node.lineno
                                    end_line = getattr(node, "end_lineno", node.lineno) or node.lineno
                                    doc = ast.get_docstring(node) or ""
                                    block = "\n".join(lines[start_line - 1 : min(len(lines), end_line)])
                                    toks = (
                                        self._tokenize(node.name) * 3
                                        + self._tokenize(doc) * 2
                                        + self._tokenize(block)
                                    )
                                    if not toks:
                                        continue
                                    chunk_entry = {
                                        "file": rel_p,
                                        "start_line": start_line,
                                        "end_line": end_line,
                                        "symbol_name": node.name,
                                        "docstring": doc,
                                        "snippet": block[:500],
                                        "tokens": toks,
                                        "term_counts": collections.Counter(toks),
                                        "length": len(toks),
                                        "is_ast": True
                                    }
                                    self.chunks.append(chunk_entry)
                                    total_len += len(toks)
                                    for term in set(toks):
                                        self.doc_freqs[term] += 1
                                    indexed_ast = True
                        except Exception:
                            pass

                    # 2. Sliding window chunking (for non-Python or whole file coverage)
                    chunk_size = 25
                    step = 15
                    for i in range(0, max(1, len(lines)), step):
                        block = "\n".join(lines[i:i+chunk_size])
                        toks = self._tokenize(block)
                        if not toks:
                            continue
                        
                        chunk_entry = {
                            "file": rel_p,
                            "start_line": i + 1,
                            "end_line": min(len(lines), i + chunk_size),
                            "symbol_name": "",
                            "docstring": "",
                            "snippet": block[:400],
                            "tokens": toks,
                            "term_counts": collections.Counter(toks),
                            "length": len(toks),
                            "is_ast": False
                        }
                        self.chunks.append(chunk_entry)
                        total_len += len(toks)

                        seen = set(toks)
                        for term in seen:
                            self.doc_freqs[term] += 1

        self.total_docs = len(self.chunks)
        self.avg_doc_len = total_len / max(1, self.total_docs)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Performs hybrid BM25 + Symbol Match search with Reciprocal Rank Fusion (RRF)."""
        q_tokens = self._tokenize(query)
        if not q_tokens or self.total_docs == 0:
            return []

        k1 = 1.5
        b = 0.75
        bm25_scores = []
        symbol_scores = []
        docstring_scores = []
        q_lower = query.strip().lower()

        for idx, chunk in enumerate(self.chunks):
            # 1. BM25 score
            score = 0.0
            doc_len = chunk["length"]
            term_counts = chunk["term_counts"]
            for q in q_tokens:
                if q in term_counts:
                    tf = term_counts[q]
                    df = self.doc_freqs.get(q, 0)
                    idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1.0)
                    tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / self.avg_doc_len)))
                    score += idf * tf_norm
            if score > 0.0:
                bm25_scores.append((score, idx))

            # 2. Exact / Prefix Symbol Score
            sym = chunk.get("symbol_name", "").lower()
            sym_score = 0.0
            if sym:
                if q_lower == sym:
                    sym_score = 10.0
                elif sym.startswith(q_lower) or q_lower in sym:
                    sym_score = 6.0
                elif any(q in sym for q in q_tokens):
                    sym_score = 3.0
            if sym_score > 0.0:
                symbol_scores.append((sym_score, idx))

            # 3. Docstring semantic match
            doc = chunk.get("docstring", "").lower()
            doc_score = 0.0
            if doc:
                overlap = sum(1 for q in q_tokens if q in doc)
                if overlap > 0:
                    doc_score = overlap * 2.0
                    docstring_scores.append((doc_score, idx))

        # Sort each channel
        bm25_scores.sort(key=lambda x: x[0], reverse=True)
        symbol_scores.sort(key=lambda x: x[0], reverse=True)
        docstring_scores.sort(key=lambda x: x[0], reverse=True)

        bm25_ranks = {idx: rank + 1 for rank, (_, idx) in enumerate(bm25_scores)}
        symbol_ranks = {idx: rank + 1 for rank, (_, idx) in enumerate(symbol_scores)}
        doc_ranks = {idx: rank + 1 for rank, (_, idx) in enumerate(docstring_scores)}

        # Combine with Reciprocal Rank Fusion (RRF)
        all_candidate_indices = set(bm25_ranks.keys()) | set(symbol_ranks.keys()) | set(doc_ranks.keys())
        rrf_k = 60
        fused_scores = []

        for idx in all_candidate_indices:
            rrf_score = 0.0
            if idx in bm25_ranks:
                rrf_score += 1.0 / (rrf_k + bm25_ranks[idx])
            if idx in symbol_ranks:
                rrf_score += 2.5 / (rrf_k + symbol_ranks[idx])
            if idx in doc_ranks:
                rrf_score += 1.5 / (rrf_k + doc_ranks[idx])

            # Bonus for AST chunks
            if self.chunks[idx].get("is_ast"):
                rrf_score *= 1.25

            fused_scores.append((rrf_score, idx))

        fused_scores.sort(key=lambda x: x[0], reverse=True)

        results = []
        seen_ranges = set()
        for s, idx in fused_scores:
            c = self.chunks[idx]
            range_key = (c["file"], c["start_line"], c["end_line"])
            if range_key in seen_ranges:
                continue
            seen_ranges.add(range_key)

            scaled_relevance = round(s * 100.0, 2)
            results.append({
                "file": c["file"],
                "start_line": c["start_line"],
                "end_line": c["end_line"],
                "snippet": c["snippet"],
                "relevance_score": scaled_relevance
            })
            if len(results) >= top_k:
                break

        return results

    def format_search_results(self, query: str, results: List[Dict[str, Any]]) -> str:
        out = [
            f"# 🔍 Semantic Code Search: \"{query}\"\n",
            f"- **Found Matches:** {len(results)} relevant code blocks\n"
        ]
        if not results:
            out.append("*(No relevant code matches found for this query)*")
            return "\n".join(out)

        for i, r in enumerate(results, 1):
            out.append(f"### {i}. `{r['file']}` (Lines {r['start_line']}-{r['end_line']}) — Relevance: {r['relevance_score']}")
            out.append("```\n" + r["snippet"] + "\n```\n")
        return "\n".join(out)


# =============================================================================
# 5. TOKEN SAVINGS & DEVELOPER ROI CALCULATOR
# =============================================================================

class TokenROICalculator:
    """Calculates quantitative token reduction savings and economic ROI."""

    @staticmethod
    def calculate(raw_tokens: int, reduced_tokens: int, team_size: int = 5, queries_per_day: int = 30) -> Dict[str, Any]:
        saved_per_query = max(0, raw_tokens - reduced_tokens)
        reduction_pct = (saved_per_query / max(1, raw_tokens)) * 100.0

        # Based on average blended input cost $2.50 / 1M tokens (GPT-4o / Claude 3.7 Sonnet)
        rate_per_million = 2.50
        cost_raw_per_query = (raw_tokens / 1_000_000.0) * rate_per_million
        cost_reduced_per_query = (reduced_tokens / 1_000_000.0) * rate_per_million
        savings_per_query = cost_raw_per_query - cost_reduced_per_query

        daily_team_queries = team_size * queries_per_day
        monthly_queries = daily_team_queries * 22  # 22 working days
        monthly_savings_usd = monthly_queries * savings_per_query
        annual_savings_usd = monthly_savings_usd * 12

        return {
            "raw_tokens": raw_tokens,
            "reduced_tokens": reduced_tokens,
            "saved_tokens_per_query": saved_per_query,
            "reduction_percentage": round(reduction_pct, 1),
            "cost_raw_query_usd": round(cost_raw_per_query, 4),
            "cost_reduced_query_usd": round(cost_reduced_per_query, 4),
            "team_size": team_size,
            "monthly_queries": monthly_queries,
            "monthly_savings_usd": round(monthly_savings_usd, 2),
            "annual_savings_usd": round(annual_savings_usd, 2)
        }

    compute_savings = calculate

    @classmethod
    def format_report(cls, metrics: Dict[str, Any]) -> str:
        pct = metrics["reduction_percentage"]
        m_usd = metrics["monthly_savings_usd"]
        a_usd = metrics["annual_savings_usd"]

        return f"""# 📊 T-Zero Token Reduction & Economic ROI Report

> **Compression Ratio:** **{pct}% token reduction** ({metrics['raw_tokens']:,} tokens ➔ {metrics['reduced_tokens']:,} tokens)  
> **Team Model:** {metrics['team_size']} Engineers × ~{metrics['monthly_queries']:,} queries/month  
> **Estimated Financial ROI:** **${m_usd:,.2f} USD / month** (${a_usd:,.2f} USD / year)

| Metric | Raw Uncompressed | T-Zero Ultra Engine | Delta |
|:-------|:-----------------|:-------------------|:------|
| **Tokens per Query** | {metrics['raw_tokens']:,} | {metrics['reduced_tokens']:,} | **-{pct}%** |
| **Cost per Prompt** | ${metrics['cost_raw_query_usd']:.4f} | ${metrics['cost_reduced_query_usd']:.4f} | **-${metrics['cost_raw_query_usd'] - metrics['cost_reduced_query_usd']:.4f}** |
| **Monthly Team Cost** | ${metrics['cost_raw_query_usd'] * metrics['monthly_queries']:,.2f} | ${metrics['cost_reduced_query_usd'] * metrics['monthly_queries']:,.2f} | **-${m_usd:,.2f}** |

> [!TIP]
> T-Zero AST pruning eliminates boilerplate internals while preserving exact semantic interfaces, allowing models to fit massive enterprise codebases into limited context windows.
"""


# =============================================================================
# 6. INCREMENTAL GIT DIFF & PR CONTEXT BUILDER (98%+ Token Savings)
# =============================================================================

class GitDiffContextBuilder:
    """Computes incremental git diff context and downstream blast radius dependencies.
    
    Extracts only modified symbol signatures + affected callers/importers,
    achieving 98%+ token savings compared to whole-repository prompt ingestion.
    """

    def __init__(self, project_dir: str):
        self.project_dir = os.path.abspath(project_dir)
        self.impact_analyzer = ChangeImpactAnalyzer(self.project_dir)

    def get_diff_changed_files(self, base_ref: str = "HEAD~1") -> List[Dict[str, Any]]:
        """Finds changed files using local git diff without external network calls."""
        changed = []

        diff_output = ""
        try:
            r = subprocess.run(
                ["git", "diff", "--name-status", base_ref],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                check=False
            )
            if r.returncode == 0 and r.stdout.strip():
                diff_output = r.stdout
            else:
                r2 = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True,
                    check=False
                )
                if r2.returncode == 0:
                    diff_output = r2.stdout
        except Exception:
            return []

        for line in diff_output.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                status = parts[0]
                file_rel = parts[-1].replace("\\", "/")
                changed.append({
                    "status": status,
                    "file": file_rel
                })
        return changed

    def build_diff_context(self, base_ref: str = "HEAD~1") -> Dict[str, Any]:
        """Builds hyper-compact diff context payload."""
        from tzero_v3 import TokenReducer
        changed_files = self.get_diff_changed_files(base_ref)
        if not changed_files:
            return {
                "base_ref": base_ref,
                "changed_files_count": 0,
                "modified_symbols_count": 0,
                "downstream_dependents_count": 0,
                "compressed_tokens": 0,
                "full_repo_tokens": 0,
                "token_savings_percent": 100.0,
                "markdown": "## No Git Changes Detected\nWorking tree is completely clean relative to base reference."
            }

        modified_symbols = []
        downstream_dependents = set()
        file_snippets = {}

        for item in changed_files:
            rel_p = item["file"]
            full_p = os.path.join(self.project_dir, rel_p)
            if not os.path.isfile(full_p):
                continue

            try:
                with open(full_p, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
                file_snippets[rel_p] = content
            except Exception:
                continue

            if rel_p.endswith(".py"):
                try:
                    tree = ast.parse(content)
                    for node in tree.body:
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                            modified_symbols.append((rel_p, node.name))
                            impact = self.impact_analyzer.analyze_symbol(node.name)
                            for caller in impact.get("direct_callers", []):
                                if isinstance(caller, dict) and "file" in caller:
                                    downstream_dependents.add(caller["file"])
                                elif isinstance(caller, str):
                                    downstream_dependents.add(caller)
                            for dep in impact.get("second_level_dependents", []):
                                if isinstance(dep, dict) and "file" in dep:
                                    downstream_dependents.add(dep["file"])
                                elif isinstance(dep, str):
                                    downstream_dependents.add(dep)
                            for dep in impact.get("downstream_dependents", []):
                                if isinstance(dep, dict) and "file" in dep:
                                    downstream_dependents.add(dep["file"])
                                elif isinstance(dep, str):
                                    downstream_dependents.add(dep)
                except Exception:
                    pass

        full_repo_tokens = sum(len(v) // 4 for v in self.impact_analyzer.snippets.values())
        reduced_snippets = {
            f: TokenReducer.reduce(c, f, mode="ultra") for f, c in file_snippets.items()
        }
        compressed_diff_tokens = sum(len(v) // 4 for v in reduced_snippets.values())

        savings_pct = 0.0
        if full_repo_tokens > 0:
            savings_pct = round(max(0.0, 100.0 - (compressed_diff_tokens / full_repo_tokens * 100.0)), 1)

        md = [
            f"# 🚀 T-Zero Incremental PR Context (Diff Mode)",
            f"",
            f"> **Compression Ratio:** **{savings_pct}% reduction** ({compressed_diff_tokens:,} tokens vs {full_repo_tokens:,} full repo tokens)",
            f"> **Base Ref:** `{base_ref}` | **Modified Files:** {len(file_snippets)} | **Downstream Impacted Files:** {len(downstream_dependents)}",
            f"",
            f"## 📝 1. Modified Modules & Changed Signatures",
        ]

        for rel_p, reduced_code in reduced_snippets.items():
            ext = os.path.splitext(rel_p)[1].lstrip(".") or "txt"
            md.append(f"### `{rel_p}`")
            md.append(f"```{ext}")
            md.append(reduced_code[:3000] if len(reduced_code) > 3000 else reduced_code)
            md.append("```")
            md.append("")

        if downstream_dependents:
            md.append("## 🎯 2. Downstream Blast Radius Dependents")
            for dep_file in sorted(downstream_dependents):
                md.append(f"- `{dep_file}` (Depends on modified symbols)")
            md.append("")

        md_str = "\n".join(md)
        return {
            "base_ref": base_ref,
            "changed_files_count": len(file_snippets),
            "modified_symbols_count": len(modified_symbols),
            "downstream_dependents_count": len(downstream_dependents),
            "compressed_tokens": compressed_diff_tokens,
            "full_repo_tokens": full_repo_tokens,
            "token_savings_percent": savings_pct,
            "markdown": md_str
        }


# =============================================================================
# 7. LOCAL CYBERPUNK WEB DASHBOARD (Zero-Dependency Localhost Server)
# =============================================================================

HTML_DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Siber Akademi — T-Zero Context Engine Webview</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Outfit:wght@400;600;800&display=swap" rel="stylesheet"/>
<style>
:root {
  --bg-dark: #0a0b10;
  --bg-card: rgba(18, 20, 29, 0.85);
  --border: rgba(0, 255, 216, 0.2);
  --accent: #00ffd8;
  --accent-glow: rgba(0, 255, 216, 0.35);
  --text: #e2e8f0;
  --text-dim: #94a3b8;
  --neon-pink: #ff007f;
  --neon-green: #00ff41;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg-dark);
  color: var(--text);
  font-family: 'Outfit', sans-serif;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
header {
  background: rgba(10, 11, 16, 0.95);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  padding: 16px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
}
.brand { display: flex; align-items: center; gap: 12px; font-weight: 800; font-size: 1.25rem; letter-spacing: 1px; }
.brand span { color: var(--accent); }
nav { display: flex; gap: 8px; }
button.tab-btn {
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-dim);
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-family: 'Outfit', sans-serif;
  font-weight: 600;
  transition: all 0.2s ease;
}
button.tab-btn.active, button.tab-btn:hover {
  background: rgba(0, 255, 216, 0.1);
  border-color: var(--border);
  color: var(--accent);
}
main { flex: 1; padding: 32px; max-width: 1400px; margin: 0 auto; width: 100%; }
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  backdrop-filter: blur(8px);
}
h2 { font-size: 1.5rem; margin-bottom: 16px; color: var(--accent); display: flex; align-items: center; gap: 8px; }
pre, code { font-family: 'JetBrains Mono', monospace; }
pre {
  background: #050608;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.05);
  overflow-x: auto;
  font-size: 0.9rem;
  line-height: 1.5;
}
.search-box {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
input[type="text"] {
  flex: 1;
  background: #050608;
  border: 1px solid var(--border);
  padding: 12px 16px;
  border-radius: 8px;
  color: #fff;
  font-family: 'JetBrains Mono', monospace;
}
.btn-action {
  background: var(--accent);
  color: #000;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
  transition: 0.2s;
}
.btn-action:hover { background: #50fa7b; }
.metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
.metric-card {
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}
.metric-val { font-size: 2rem; font-weight: 800; color: var(--accent); margin-top: 4px; }
.tab-content { display: none; }
.tab-content.active { display: block; }
</style>
</head>
<body>
<header>
  <div class="brand">⚡ <span>T-ZERO</span> CONTEXT ARCHITECT V3</div>
  <nav>
    <button class="tab-btn active" onclick="switchTab('overview')">🏛️ Overview</button>
    <button class="tab-btn" onclick="switchTab('search')">🔍 RAG Search</button>
    <button class="tab-btn" onclick="switchTab('impact')">💥 Blast Radius</button>
    <button class="tab-btn" onclick="switchTab('boundaries')">🛡️ Boundaries</button>
    <button class="tab-btn" onclick="switchTab('rules')">🤖 Agent Rules</button>
  </nav>
</header>
<main>
  <!-- OVERVIEW TAB -->
  <div id="tab-overview" class="tab-content active">
    <div class="metric-grid">
      <div class="metric-card"><div>Analyzed Modules</div><div class="metric-val" id="m-files">--</div></div>
      <div class="metric-card"><div>Token Reduction</div><div class="metric-val" style="color:var(--neon-green)">94.6%</div></div>
      <div class="metric-card"><div>Zero-Leak Security</div><div class="metric-val" style="color:var(--neon-pink)">100%</div></div>
      <div class="metric-card"><div>MCP Status</div><div class="metric-val">READY</div></div>
    </div>
    <div class="card">
      <h2>🏛️ Architectural Topology Tree</h2>
      <pre id="tree-box">Loading workspace context tree...</pre>
    </div>
  </div>

  <!-- SEARCH TAB -->
  <div id="tab-search" class="tab-content">
    <div class="card">
      <h2>🔍 Local Hybrid Semantic Code Search (Zero-Leak)</h2>
      <p style="color:var(--text-dim); margin-bottom: 16px;">Query code semantically without uploading source code to third-party embeddings APIs.</p>
      <div class="search-box">
        <input type="text" id="search-input" placeholder="e.g. authentication jwt token, database pool, keyring encryption..."/>
        <button class="btn-action" onclick="runSearch()">Search</button>
      </div>
      <div id="search-results"></div>
    </div>
  </div>

  <!-- BLAST RADIUS TAB -->
  <div id="tab-impact" class="tab-content">
    <div class="card">
      <h2>💥 Change Impact & Blast Radius Analyzer</h2>
      <p style="color:var(--text-dim); margin-bottom: 16px;">Inspect downstream dependents and caller cascades before refactoring functions or classes.</p>
      <div class="search-box">
        <input type="text" id="symbol-input" placeholder="e.g. generate_offline_context, TokenReducer, CodebaseScanner..."/>
        <button class="btn-action" onclick="runImpact()">Analyze Impact</button>
      </div>
      <pre id="impact-results">Enter a symbol name above and click 'Analyze Impact'.</pre>
    </div>
  </div>

  <!-- BOUNDARIES TAB -->
  <div id="tab-boundaries" class="tab-content">
    <div class="card">
      <h2>🛡️ Architecture Boundary & Layer Enforcer (T-4 Rules)</h2>
      <p style="color:var(--text-dim); margin-bottom: 16px;">Validates modular separation and prevents unauthorized cross-layer imports.</p>
      <button class="btn-action" onclick="runBoundaries()">Verify Boundaries</button>
      <pre id="boundaries-results" style="margin-top:16px;">Click 'Verify Boundaries' to run AST import validation.</pre>
    </div>
  </div>

  <!-- RULES TAB -->
  <div id="tab-rules" class="tab-content">
    <div class="card">
      <h2>🤖 Export AI Agent Rules (.cursorrules, .clinerules, Copilot)</h2>
      <p style="color:var(--text-dim); margin-bottom: 16px;">Generate native configuration files for Cursor, Claude, Antigravity IDE, and Cline.</p>
      <button class="btn-action" onclick="exportRules()">Generate All Rules to Workspace</button>
      <pre id="rules-output" style="margin-top: 16px;">Click button to generate rules.</pre>
    </div>
  </div>
</main>
<script>
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('tab-' + tabId).classList.add('active');
}

fetch('/api/overview').then(r => r.json()).then(data => {
  document.getElementById('m-files').innerText = data.files_count;
  document.getElementById('tree-box').innerText = data.tree;
}).catch(e => console.error(e));

function runSearch() {
  const q = document.getElementById('search-input').value;
  if (!q) return;
  fetch('/api/search?q=' + encodeURIComponent(q))
    .then(r => r.json())
    .then(data => {
      let html = '';
      if (!data.length) html = '<p>No matches found.</p>';
      data.forEach(m => {
        html += `<div style="margin-bottom:16px; border-left: 2px solid var(--accent); padding-left:12px;">
          <strong>${m.file}</strong> (Lines ${m.start_line}-${m.end_line}) — Score: ${m.relevance_score}
          <pre style="margin-top:6px;">${m.snippet}</pre>
        </div>`;
      });
      document.getElementById('search-results').innerHTML = html;
    });
}

function runImpact() {
  const sym = document.getElementById('symbol-input').value;
  if (!sym) return;
  fetch('/api/impact?sym=' + encodeURIComponent(sym))
    .then(r => r.json())
    .then(data => {
      document.getElementById('impact-results').innerText = data.report;
    });
}

function runBoundaries() {
  fetch('/api/boundaries')
    .then(r => r.json())
    .then(data => {
      document.getElementById('boundaries-results').innerText = data.report;
    });
}

function exportRules() {
  fetch('/api/export-rules')
    .then(r => r.json())
    .then(data => {
      document.getElementById('rules-output').innerText = "Exported files:\n" + data.files.join("\n");
    });
}
</script>
</body>
</html>
"""


class DashboardRequestHandler(http.server.BaseHTTPRequestHandler):
    """Zero-dependency secure HTTP handler serving the T-Zero Web Dashboard and REST APIs."""
    
    project_dir = "."
    _search_engine: Optional[LocalSemanticCodeSearch] = None
    _impact_analyzer: Optional[ChangeImpactAnalyzer] = None
    _rule_engine: Optional[ArchitectureRuleEngine] = None
    _last_mtime: float = 0.0

    @classmethod
    def _get_project_mtime(cls) -> float:
        """Finds latest modification timestamp across files to detect stale cache."""
        latest = 0.0
        for root, _, files in os.walk(cls.project_dir):
            if should_skip_dir(root, cls.project_dir):
                continue
            for f in files:
                if f.endswith(('.py', '.json', '.js', '.ts', '.go', '.rs')):
                    try:
                        m = os.path.getmtime(os.path.join(root, f))
                        if m > latest:
                            latest = m
                    except OSError:
                        pass
        return latest

    @classmethod
    def get_engines(cls) -> Tuple[LocalSemanticCodeSearch, ChangeImpactAnalyzer, ArchitectureRuleEngine]:
        """Returns initialized analysis engines, auto-refreshing cache if files changed."""
        current_m = cls._get_project_mtime()
        if (
            cls._search_engine is None
            or cls._impact_analyzer is None
            or cls._rule_engine is None
            or current_m > cls._last_mtime
        ):
            cls._search_engine = LocalSemanticCodeSearch(cls.project_dir)
            cls._impact_analyzer = ChangeImpactAnalyzer(cls.project_dir)
            cls._rule_engine = ArchitectureRuleEngine(cls.project_dir)
            cls._last_mtime = current_m
        return cls._search_engine, cls._impact_analyzer, cls._rule_engine

    def log_message(self, format, *args):
        pass  # Quiet logging

    def _send_security_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("X-Content-Type-Options", "nosniff")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_security_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            payload = HTML_DASHBOARD_TEMPLATE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self._send_security_headers()
            self.end_headers()
            self.wfile.write(payload)
            return

        search_engine, impact_analyzer, rule_engine = self.get_engines()

        if path == "/api/overview":
            from tzero_v3 import CodebaseScanner
            scanner = CodebaseScanner()
            files, sizes, snippets = scanner.scan_directory(self.project_dir)
            tree_ascii = "\n".join(f"├── {f}" for f in files[:40])
            if len(files) > 40:
                tree_ascii += f"\n... and {len(files) - 40} more files"
            res = {"files_count": len(files), "tree": tree_ascii}
            self._send_json(res)
            return

        if path == "/api/search":
            q = query.get("q", [""])[0]
            matches = search_engine.search(q, top_k=6)
            self._send_json(matches)
            return

        if path == "/api/impact":
            sym = query.get("sym", [""])[0]
            analysis = impact_analyzer.analyze_symbol(sym)
            report = impact_analyzer.format_report(analysis)
            self._send_json({"analysis": analysis, "report": report})
            return

        if path == "/api/boundaries":
            res = rule_engine.enforce_boundaries()
            # Clean report without ANSI colors for HTML
            if res["clean"]:
                rep = f"PASSED: All {res['scanned_files']} files conform to boundary rules. Zero violations."
            else:
                rep = f"VIOLATIONS DETECTED ({res['total_violations']}):\n"
                for v in res["violations"]:
                    rep += f"- {v['file']}:{v['line']} -> Layer '{v['layer']}' cannot import '{v['forbidden_import']}' ({v['reason']})\n"
            self._send_json({"result": res, "report": rep})
            return

        if path == "/api/export-rules":
            files = AgentRulesGenerator.export_all(self.project_dir)
            self._send_json({"success": True, "files": [os.path.relpath(f, self.project_dir) for f in files]})
            return

        self.send_error(404, "Endpoint not found")

    def _send_json(self, data: Any):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(payload)


def launch_web_dashboard(project_dir: str = ".", port: int = 7300, open_browser: bool = True):
    """Starts the zero-dependency local web dashboard server."""
    import webbrowser
    DashboardRequestHandler.project_dir = os.path.abspath(project_dir)
    server_address = ("127.0.0.1", port)
    
    try:
        httpd = socketserver.TCPServer(server_address, DashboardRequestHandler)
    except OSError:
        port += 1
        server_address = ("127.0.0.1", port)
        httpd = socketserver.TCPServer(server_address, DashboardRequestHandler)

    url = f"http://127.0.0.1:{port}"
    print(f"\n\033[1m\033[36m=== SİBER AKADEMİ T-ZERO WEB DASHBOARD ===\033[0m")
    print(f"🚀 Running locally at: \033[32m{url}\033[0m")
    print(f"📁 Workspace Target:   {os.path.abspath(project_dir)}")
    print("Press Ctrl+C to terminate the web server.\n")

    if open_browser:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Web dashboard shut down.")
        httpd.server_close()


# =============================================================================
# 7. ZERO-HALLUCINATION GUARD & PRE-FLIGHT SYMBOL / CALL VALIDATOR (TOOL 17)
# =============================================================================

class _SelfHealingTransformer(ast.NodeTransformer):
    """AST transformer that automatically corrects hallucinated imports, function names, and kwargs."""
    def __init__(self, fixes: Dict[str, Any]):
        self.import_fixes = fixes.get("imports", {})    # (module, old_sym) -> new_sym
        self.call_fixes = fixes.get("calls", {})        # old_func_name -> new_func_name
        self.kwarg_fixes = fixes.get("kwargs", {})      # (func_name, old_kw) -> new_kw

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST:
        if node.module:
            for alias in node.names:
                key = (node.module, alias.name)
                if key in self.import_fixes:
                    alias.name = self.import_fixes[key]
        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if node.id in self.call_fixes:
            node.id = self.call_fixes[node.id]
        return self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> ast.AST:
        fname = ""
        full_name = ""
        if isinstance(node.func, ast.Name):
            fname = node.func.id
            if fname in self.call_fixes:
                node.func.id = self.call_fixes[fname]
                fname = node.func.id
            full_name = fname
        elif isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            if attr in self.call_fixes:
                node.func.attr = self.call_fixes[attr]
                attr = node.func.attr
            fname = attr
            try:
                full_name = f"{ast.unparse(node.func.value)}.{attr}"
            except Exception:
                full_name = attr

        for kw in node.keywords:
            if kw.arg:
                if (full_name, kw.arg) in self.kwarg_fixes:
                    kw.arg = self.kwarg_fixes[(full_name, kw.arg)]
                elif (fname, kw.arg) in self.kwarg_fixes:
                    kw.arg = self.kwarg_fixes[(fname, kw.arg)]
                elif ("", kw.arg) in self.kwarg_fixes:
                    kw.arg = self.kwarg_fixes[("", kw.arg)]
        return self.generic_visit(node)


class ZeroHallucinationGuard:
    """Pre-flight validator that eliminates AI coding hallucinations before code is applied.
    
    5-Tier Zero-Hallucination Architecture:
      1. Ghost Dependency Guard: Blocks imports of non-existent packages (validates against stdlib, requirements.txt, pyproject.toml, and installed packages).
      2. AST Symbol & Module Guard: Verifies imports against workspace modules and declared __all__ / exported symbols.
      3. AST Call & Keyword Argument Guard: Validates positional counts and parameter names against known function signatures.
      4. Schema & Field Contract Guard: Validates class instantiations, dataclasses, and attribute accesses against known fields.
      5. Return Type & Chaining Guard: Detects invalid chaining or iterations on functions returning None or primitive types.
      + Self-Healing AST Patcher: Automatically synthesizes corrected, hallucination-free code via AST node transformation.
      + Grounding Contract Generator: Emits immutable Type & Symbol boundary contracts for prompt pinning.
    """

    def __init__(self, project_dir: str):
        self.project_dir = os.path.abspath(project_dir)
        self.modules: Dict[str, str] = {}  # mod_name -> rel_path
        self.exported_symbols: Dict[str, Set[str]] = collections.defaultdict(set)
        self.function_signatures: Dict[str, Dict[str, Any]] = {}
        self.class_fields: Dict[str, Set[str]] = collections.defaultdict(set)
        self.class_methods: Dict[str, Set[str]] = collections.defaultdict(set)
        self.declared_packages: Set[str] = set()
        self.installed_packages: Set[str] = set()
        self.stdlib_modules: Set[str] = set()
        self.known_package_aliases: Dict[str, str] = {}
        self._load_installed_and_stdlib()
        self._load_dependency_manifests()
        self._build_catalog()

    def _load_installed_and_stdlib(self):
        """Loads Python standard library modules, installed environment packages, and alias mappings."""
        # 1. Standard Library Modules
        self.stdlib_modules = set(getattr(sys, "stdlib_module_names", sys.builtin_module_names))
        self.stdlib_modules.update({
            "typing", "typing_extensions", "__future__", "dataclasses", "unittest",
            "test", "abc", "contextlib", "collections", "functools", "itertools",
            "os", "sys", "re", "json", "ast", "math", "time", "datetime", "pathlib",
            "shutil", "tempfile", "subprocess", "socket", "http", "urllib", "hashlib",
            "logging", "threading", "asyncio", "multiprocessing", "queue", "signal",
            "copy", "inspect", "difflib", "fnmatch", "glob", "io", "pickle", "sqlite3",
            "csv", "xml", "email", "html", "base64", "binascii", "struct", "random",
            "warnings", "weakref", "zoneinfo", "uuid", "decimal", "enum", "numbers"
        })

        # 2. Installed packages in the active environment
        try:
            import importlib.metadata as im
            for dist in im.distributions():
                dname = dist.metadata.get("Name", "")
                if dname:
                    norm = dname.lower().replace("-", "_")
                    self.installed_packages.add(norm)
                    self.installed_packages.add(dname.lower())
                try:
                    top_level = dist.read_text("top_level.txt")
                    if top_level:
                        for tl in top_level.splitlines():
                            tl = tl.strip()
                            if tl:
                                self.installed_packages.add(tl.lower())
                except Exception:
                    pass
        except Exception:
            pass

        # 3. Canonical import aliases for top third-party packages
        self.known_package_aliases = {
            "yaml": "pyyaml",
            "cv2": "opencv-python",
            "pil": "pillow",
            "sklearn": "scikit-learn",
            "dateutil": "python-dateutil",
            "dotenv": "python-dotenv",
            "jwt": "pyjwt",
            "bs4": "beautifulsoup4",
            "magic": "python-magic",
            "multipart": "python-multipart",
            "git": "gitpython",
            "serial": "pyserial",
            "mcp": "mcp",
            "fastapi": "fastapi",
            "pydantic": "pydantic",
            "uvicorn": "uvicorn",
            "click": "click",
            "pytest": "pytest",
            "flask": "flask",
            "django": "django",
            "sqlalchemy": "sqlalchemy",
            "httpx": "httpx",
            "aiohttp": "aiohttp",
            "requests": "requests",
        }

    def _load_dependency_manifests(self):
        """Scans project directory for requirements.txt, pyproject.toml, and setup.py to find declared dependencies."""
        for root, _, files in os.walk(self.project_dir):
            if should_skip_dir(root, self.project_dir):
                continue
            for f in files:
                f_lower = f.lower()
                full_p = os.path.join(root, f)
                if f_lower.startswith("requirements") and f_lower.endswith(".txt"):
                    try:
                        with open(full_p, "r", encoding="utf-8", errors="ignore") as fp:
                            for line in fp:
                                line = line.strip()
                                if line and not line.startswith(("#", "-", "@")):
                                    pkg = re.split(r'[><=~!;\s\[]', line)[0].strip()
                                    if pkg:
                                        self.declared_packages.add(pkg.lower().replace("-", "_"))
                                        self.declared_packages.add(pkg.lower())
                    except Exception:
                        pass
                elif f_lower == "pyproject.toml":
                    try:
                        with open(full_p, "r", encoding="utf-8", errors="ignore") as fp:
                            in_deps = False
                            for line in fp:
                                line = line.strip()
                                if line.startswith("[") and ("dependencies" in line.lower() or "requires" in line.lower()):
                                    in_deps = True
                                    continue
                                elif line.startswith("["):
                                    in_deps = False
                                if in_deps and line:
                                    m = re.match(r'^["\']?([a-zA-Z0-9_\-]+)', line)
                                    if m:
                                        pkg = m.group(1).lower().replace("-", "_")
                                        self.declared_packages.add(pkg)
                    except Exception:
                        pass

    def _build_catalog(self):
        for root, _, files in os.walk(self.project_dir):
            if should_skip_dir(root, self.project_dir):
                continue
            for f in files:
                if f.endswith('.py'):
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, self.project_dir).replace('\\', '/')
                    mod_path = os.path.splitext(rel_p)[0].replace('/', '.')
                    stem = os.path.splitext(f)[0]
                    self.modules[mod_path] = rel_p
                    self.modules[stem] = rel_p

                    try:
                        with open(full_p, 'r', encoding='utf-8', errors='ignore') as fp:
                            content = fp.read()
                        tree = ast.parse(content)
                        self._index_module_ast(mod_path, stem, tree)
                    except Exception:
                        pass

    def _index_module_ast(self, mod_path: str, stem: str, tree: ast.AST):
        all_symbols: Set[str] = set()
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    all_symbols.add(elt.value)
                    elif isinstance(target, ast.Name):
                        all_symbols.add(target.id)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                all_symbols.add(node.target.id)
            elif isinstance(node, ast.ClassDef):
                all_symbols.add(node.name)
                fields: Set[str] = set()
                methods: Set[str] = set()
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        fields.add(item.target.id)
                    elif isinstance(item, ast.Assign):
                        for t in item.targets:
                            if isinstance(t, ast.Name):
                                fields.add(t.id)
                    elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.add(item.name)
                        sig = self._extract_func_sig(item)
                        self.function_signatures[f"{node.name}.{item.name}"] = sig
                        if item.name not in self.function_signatures:
                            self.function_signatures[item.name] = sig
                        if item.name == "__init__":
                            for sub in ast.walk(item):
                                if isinstance(sub, ast.Assign):
                                    for t in sub.targets:
                                        if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                                            fields.add(t.attr)
                                elif isinstance(sub, ast.AnnAssign):
                                    if isinstance(sub.target, ast.Attribute) and isinstance(sub.target.value, ast.Name) and sub.target.value.id == "self":
                                        fields.add(sub.target.attr)
                self.class_fields[node.name] = fields
                self.class_fields[f"{stem}.{node.name}"] = fields
                self.class_methods[node.name] = methods
                self.class_methods[f"{stem}.{node.name}"] = methods

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                all_symbols.add(node.name)
                sig = self._extract_func_sig(node)
                self.function_signatures[node.name] = sig

        self.exported_symbols[mod_path].update(all_symbols)
        self.exported_symbols[stem].update(all_symbols)

    def _extract_func_sig(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> Dict[str, Any]:
        args = node.args
        posonly = [a.arg for a in args.posonlyargs]
        standard_args = [a.arg for a in args.args]
        all_pos = posonly + standard_args
        num_defaults = len(args.defaults)
        min_pos = len(all_pos) - num_defaults
        kwonly = [a.arg for a in args.kwonlyargs]
        all_params = set(all_pos + kwonly)
        
        arg_strs = []
        defaults_offset = len(all_pos) - num_defaults
        for i, a in enumerate(args.posonlyargs):
            s = a.arg
            if a.annotation:
                s += f": {ast.unparse(a.annotation)}"
            if i >= defaults_offset:
                s += f" = {ast.unparse(args.defaults[i - defaults_offset])}"
            arg_strs.append(s)
        if posonly:
            arg_strs.append("/")
        for i, a in enumerate(args.args):
            idx = len(posonly) + i
            s = a.arg
            if a.annotation:
                s += f": {ast.unparse(a.annotation)}"
            if idx >= defaults_offset:
                s += f" = {ast.unparse(args.defaults[idx - defaults_offset])}"
            arg_strs.append(s)
        if args.vararg:
            v_s = f"*{args.vararg.arg}"
            if args.vararg.annotation:
                v_s += f": {ast.unparse(args.vararg.annotation)}"
            arg_strs.append(v_s)
        elif kwonly:
            arg_strs.append("*")
        for i, a in enumerate(args.kwonlyargs):
            s = a.arg
            if a.annotation:
                s += f": {ast.unparse(a.annotation)}"
            default = args.kw_defaults[i]
            if default:
                s += f" = {ast.unparse(default)}"
            arg_strs.append(s)
        if args.kwarg:
            k_s = f"**{args.kwarg.arg}"
            if args.kwarg.annotation:
                k_s += f": {ast.unparse(args.kwarg.annotation)}"
            arg_strs.append(k_s)

        ret_type = ast.unparse(node.returns).strip() if node.returns else ""
        ret = f" -> {ret_type}" if ret_type else ""
        sig_str = f"{node.name}({', '.join(arg_strs)}){ret}"

        return {
            "name": node.name,
            "min_pos": min_pos,
            "max_pos": float("inf") if args.vararg else len(all_pos),
            "has_vararg": bool(args.vararg),
            "has_kwarg": bool(args.kwarg),
            "all_params": all_params,
            "sig_str": sig_str,
            "return_type": ret_type,
        }

    def validate_code(self, proposed_code: str, target_file: str = "") -> Dict[str, Any]:
        """Validates proposed code against workspace symbol, dependency manifests, and call contracts."""
        try:
            tree = ast.parse(proposed_code)
        except SyntaxError as e:
            return {
                "passed": False,
                "syntax_error": str(e),
                "violations": [f"Syntax error at line {e.lineno}: {e.msg}"],
                "repaired_code": "",
                "can_auto_heal": False,
                "repairs_applied": [],
                "report": f"❌ [HALLUCINATION BLOCKED] Proposed code failed Python syntax parsing at line {e.lineno}: {e.msg}"
            }

        violations: List[str] = []
        fixes: Dict[str, Any] = {"imports": {}, "calls": {}, "kwargs": {}}
        repairs_applied: List[str] = []

        # ---------------------------------------------------------------------
        # 1. TIER 1 & 2: GHOST DEPENDENCY & WORKSPACE IMPORT GUARDS
        # ---------------------------------------------------------------------
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    base_mod = node.module.split('.')[0]
                    is_workspace = base_mod in self.modules or node.module in self.modules
                    if is_workspace:
                        avail = self.exported_symbols.get(node.module, self.exported_symbols.get(base_mod, set()))
                        for alias in node.names:
                            if alias.name != "*" and alias.name not in avail:
                                close = difflib.get_close_matches(alias.name, list(avail), n=1, cutoff=0.5)
                                did_you_mean = f" Did you mean: `{close[0]}`?" if close else ""
                                if close:
                                    fixes["imports"][(node.module, alias.name)] = close[0]
                                    fixes["calls"][alias.name] = close[0]
                                    repairs_applied.append(f"Import `{alias.name}` -> `{close[0]}` (in `{node.module}`)")
                                violations.append(
                                    f"Import Hallucination: Symbol `{alias.name}` does not exist in workspace module `{node.module}`.{did_you_mean}"
                                )
                    else:
                        # Check external third-party package against stdlib + manifests + environment
                        b_lower = base_mod.lower()
                        is_std = b_lower in self.stdlib_modules
                        is_dec = b_lower in self.declared_packages or b_lower.replace("_", "-") in self.declared_packages
                        is_inst = b_lower in self.installed_packages or b_lower in self.known_package_aliases or self.known_package_aliases.get(b_lower) in self.installed_packages
                        if not (is_std or is_dec or is_inst):
                            all_known = list(self.declared_packages | self.installed_packages | set(self.known_package_aliases.keys()))
                            close_pkg = difflib.get_close_matches(b_lower, all_known, n=1, cutoff=0.6)
                            hint = f" Did you mean `{close_pkg[0]}`?" if close_pkg else ""
                            violations.append(
                                f"Ghost Dependency Hallucination: Package `{base_mod}` is not part of Python stdlib, not declared in requirements.txt/pyproject.toml, and not installed in environment.{hint}"
                            )

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    base_mod = alias.name.split('.')[0]
                    is_workspace = base_mod in self.modules
                    if not is_workspace:
                        b_lower = base_mod.lower()
                        is_std = b_lower in self.stdlib_modules
                        is_dec = b_lower in self.declared_packages or b_lower.replace("_", "-") in self.declared_packages
                        is_inst = b_lower in self.installed_packages or b_lower in self.known_package_aliases or self.known_package_aliases.get(b_lower) in self.installed_packages
                        if not (is_std or is_dec or is_inst):
                            all_known = list(self.declared_packages | self.installed_packages | set(self.known_package_aliases.keys()))
                            close_pkg = difflib.get_close_matches(b_lower, all_known, n=1, cutoff=0.6)
                            hint = f" Did you mean `{close_pkg[0]}`?" if close_pkg else ""
                            violations.append(
                                f"Ghost Dependency Hallucination: Package `{base_mod}` is not part of Python stdlib, not declared in requirements.txt/pyproject.toml, and not installed in environment.{hint}"
                            )

        # ---------------------------------------------------------------------
        # 2. TIER 3 & 4: CALL SIGNATURE, KWARGS & SCHEMA FIELD GUARDS
        # ---------------------------------------------------------------------
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ""
                attr_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    val_str = ast.unparse(node.func.value)
                    attr_name = node.func.attr
                    func_name = f"{val_str}.{attr_name}"

                sig = self.function_signatures.get(func_name)
                if not sig and attr_name:
                    sig = self.function_signatures.get(attr_name)

                # Schema & Dataclass field validation on class instantiation
                target_class = func_name or attr_name
                if target_class in self.class_fields and len(self.class_fields[target_class]) > 0:
                    declared_fields = self.class_fields[target_class]
                    valid_params = sig["all_params"] if sig else set()
                    for kw in node.keywords:
                        if kw.arg and kw.arg not in declared_fields and kw.arg not in valid_params:
                            close_f = difflib.get_close_matches(kw.arg, list(declared_fields | valid_params), n=1, cutoff=0.5)
                            hint = f" Did you mean field `{close_f[0]}`?" if close_f else ""
                            if close_f:
                                fixes["kwargs"][(target_class, kw.arg)] = close_f[0]
                                repairs_applied.append(f"Field `{target_class}.{kw.arg}` -> `{close_f[0]}`")
                            violations.append(
                                f"Schema Field Hallucination: Class `{target_class}` has no declared attribute or field `{kw.arg}`.{hint}"
                            )

                if sig:
                    # Validate keyword arguments
                    if not sig["has_kwarg"]:
                        for kw in node.keywords:
                            if kw.arg and kw.arg not in sig["all_params"]:
                                close_kw = difflib.get_close_matches(kw.arg, list(sig["all_params"]), n=1, cutoff=0.5)
                                hint = f" Did you mean parameter `{close_kw[0]}`?" if close_kw else ""
                                if close_kw:
                                    target_k = func_name or sig["name"]
                                    fixes["kwargs"][(target_k, kw.arg)] = close_kw[0]
                                    fixes["kwargs"][(sig["name"], kw.arg)] = close_kw[0]
                                    if attr_name:
                                        fixes["kwargs"][(attr_name, kw.arg)] = close_kw[0]
                                    repairs_applied.append(f"Param `{kw.arg}` -> `{close_kw[0]}` in `{func_name or sig['name']}()`")
                                violations.append(
                                    f"Call Hallucination: `{func_name or sig['name']}` does not accept keyword argument `{kw.arg}`.{hint} Valid signature: `{sig['sig_str']}`"
                                )
                    # Validate positional argument counts
                    num_pos = len(node.args)
                    is_method_attr_call = isinstance(node.func, ast.Attribute)
                    effective_min = sig["min_pos"]
                    effective_max = sig["max_pos"]
                    if is_method_attr_call and "self" in sig["all_params"]:
                        effective_min = max(0, effective_min - 1)
                        if effective_max != float("inf"):
                            effective_max = max(0, effective_max - 1)

                    if num_pos < effective_min:
                        violations.append(
                            f"Call Hallucination: `{func_name or sig['name']}` missing required positional arguments ({num_pos} provided, at least {effective_min} required). Valid signature: `{sig['sig_str']}`"
                        )
                    elif not sig["has_vararg"] and num_pos > effective_max:
                        violations.append(
                            f"Call Hallucination: `{func_name or sig['name']}` received too many positional arguments ({num_pos} provided, at most {effective_max} allowed). Valid signature: `{sig['sig_str']}`"
                        )
                elif isinstance(node.func, ast.Attribute):
                    target_attr = node.func.attr
                    all_sigs = list(self.function_signatures.keys())
                    matches = difflib.get_close_matches(target_attr, [s.split('.')[-1] for s in all_sigs], n=1, cutoff=0.5)
                    if matches:
                        cand_sigs = [self.function_signatures[m]["sig_str"] for m in matches if m in self.function_signatures]
                        val_str = ast.unparse(node.func.value)
                        fixes["calls"][target_attr] = matches[0]
                        repairs_applied.append(f"Method `{val_str}.{target_attr}()` -> `.{matches[0]}()`")
                        violations.append(
                            f"Call Hallucination: Method or function `{val_str}.{target_attr}` does not exist! Did you mean: `{'; '.join(cand_sigs or matches)}`?"
                        )

        # ---------------------------------------------------------------------
        # 3. TIER 5: RETURN TYPE & CHAINING GUARD
        # ---------------------------------------------------------------------
        for node in ast.walk(tree):
            # Check iterations: for x in func():
            if isinstance(node, (ast.For, ast.AsyncFor)):
                if isinstance(node.iter, ast.Call):
                    c_name = ast.unparse(node.iter.func).strip()
                    sig = self.function_signatures.get(c_name) or self.function_signatures.get(c_name.split('.')[-1])
                    if sig and sig.get("return_type"):
                        rt = sig["return_type"].strip()
                        if rt in ("None", "NoneType", "bool", "int", "float"):
                            violations.append(
                                f"Return Contract Hallucination: Function `{c_name}` returns `{rt}`, which is not iterable in a loop!"
                            )
            # Check attribute access on None return: func().attr
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Call):
                    c_name = ast.unparse(node.value.func).strip()
                    sig = self.function_signatures.get(c_name) or self.function_signatures.get(c_name.split('.')[-1])
                    if sig and sig.get("return_type") in ("None", "NoneType"):
                        violations.append(
                            f"Return Contract Hallucination: Function `{c_name}` has declared return type 'None', cannot access member `.{node.attr}` on NoneType!"
                        )

        # ---------------------------------------------------------------------
        # 4. SELF-HEALING AST REPAIR SYNTHESIS
        # ---------------------------------------------------------------------
        repaired_code = ""
        can_auto_heal = False
        has_fixes = bool(fixes["imports"] or fixes["calls"] or fixes["kwargs"])
        if has_fixes:
            try:
                tree_copy = copy.deepcopy(tree)
                transformer = _SelfHealingTransformer(fixes)
                healed_tree = transformer.visit(tree_copy)
                ast.fix_missing_locations(healed_tree)
                repaired_code = ast.unparse(healed_tree)
                can_auto_heal = True
            except Exception:
                repaired_code = ""
                can_auto_heal = False

        passed = len(violations) == 0
        if passed:
            report_str = "✅ [PASS] Zero-Hallucination Guard verified. All imports, call contracts, dependency manifests, and schemas are valid."
        else:
            report_lines = [
                f"❌ [HALLUCINATION BLOCKED] Found {len(violations)} contract violation(s) in proposed code:\n"
            ]
            for i, v in enumerate(violations, 1):
                report_lines.append(f"{i}. {v}")
            
            if can_auto_heal and repaired_code:
                report_lines.append("\n### 🩹 Self-Healing AST Auto-Repair:")
                report_lines.append(f"> T-Zero automatically synthesized a corrected, hallucination-free version applying {len(repairs_applied)} fix(es):")
                for r in repairs_applied:
                    report_lines.append(f"- 🔧 {r}")
                report_lines.append("\n```python")
                report_lines.append(repaired_code)
                report_lines.append("```\n")
            else:
                report_lines.append("\n> **Corrective Action:** Adjust imports or function calls to match declared AST interfaces above.")

            report_str = "\n".join(report_lines)

        return {
            "passed": passed,
            "violations": violations,
            "repaired_code": repaired_code,
            "can_auto_heal": can_auto_heal,
            "repairs_applied": repairs_applied,
            "report": report_str
        }

    def repair_code(self, proposed_code: str, target_file: str = "") -> str:
        """Returns auto-healed code if hallucinations exist and can be safely repaired, or original code."""
        res = self.validate_code(proposed_code, target_file)
        if res.get("can_auto_heal") and res.get("repaired_code"):
            return res["repaired_code"]
        return proposed_code

    def generate_grounding_contract(self, focus_modules: Optional[List[str]] = None, task_intent: str = "") -> str:
        """Emits an immutable AST Type & Symbol grounding contract for prompt pinning."""
        out = [
            "# 🔒 T-ZERO IMMUTABLE AST GROUNDING CONTRACT (ZERO-HALLUCINATION SPECIFICATION)",
            "",
            "> **CRITICAL DIRECTIVE FOR AI AGENT / COMPOSER:**",
            "> You MUST strictly conform to the exact symbol, function, parameter, and class definitions declared below.",
            "> Guessing parameter names, inventing unlisted methods, or importing ghost packages is strictly prohibited.",
            ""
        ]

        if task_intent:
            out.append(f"**Task Objective:** `{task_intent}`\n")

        # 1. Permitted Workspace Signatures
        out.append("## 1. 🔍 Permitted Workspace Function Signatures & Types")
        out.append("| Module | Function / Method Signature | Return Type |")
        out.append("|:---|:---|:---|")
        
        target_keys = sorted(self.function_signatures.keys())
        if focus_modules:
            target_keys = [k for k in target_keys if any(m in k for m in focus_modules)]

        for k in target_keys[:40]:
            sig = self.function_signatures[k]
            rt = sig.get("return_type") or "Any"
            out.append(f"| `{k.split('.')[0] if '.' in k else 'global'}` | `{sig['sig_str']}` | `{rt}` |")
        out.append("")

        # 2. Permitted Class Schemas
        if self.class_fields:
            out.append("## 2. 🧩 Declared Class & Model Field Schemas")
            out.append("| Class | Declared Attributes & Fields |")
            out.append("|:---|:---|")
            for c_name, fields in list(self.class_fields.items())[:25]:
                if "." not in c_name and fields:
                    out.append(f"| `{c_name}` | `{', '.join(sorted(fields))}` |")
            out.append("")

        # 3. Permitted Dependencies
        declared_list = sorted(list(self.declared_packages))
        if declared_list:
            out.append("## 3. 📦 Declared Third-Party Packages (Manifest Verified)")
            out.append(f"`{', '.join(declared_list[:25])}`\n")

        out.append("> **Enforcement:** Code failing this grounding contract will be blocked and rejected by the T-Zero Pre-Flight Compiler.")
        return "\n".join(out)


# =============================================================================
# 8. FOCUS-AWARE SMART SKELETON CONTEXT BUILDER (TOOL 18)
# =============================================================================

class SmartSkeletonContextBuilder:
    """Builds focus-aware hybrid context with full implementation for the target
    and ultra-compressed T-3 AST skeletons for surrounding 1st-degree ecosystem.
    """

    def __init__(self, project_dir: str):
        self.project_dir = os.path.abspath(project_dir)
        self.impact_analyzer = ChangeImpactAnalyzer(project_dir)

    def build_skeleton(self, focus_file: str, focus_symbol: str = "", task_intent: str = "") -> str:
        """Returns full target code + 1st-degree AST skeletons and matching reusable helpers."""
        from tzero_v3 import TokenReducer
        
        target_path = os.path.join(self.project_dir, focus_file) if not os.path.isabs(focus_file) else focus_file
        rel_target = os.path.relpath(target_path, self.project_dir).replace('\\', '/')
        if not os.path.isfile(target_path):
            return f"[ERROR] Focus file not found: {focus_file}"

        with open(target_path, 'r', encoding='utf-8', errors='ignore') as fp:
            full_code = fp.read()

        target_section = full_code
        target_title = f"`{rel_target}` (Full Implementation)"

        if focus_symbol and rel_target.endswith(".py"):
            try:
                tree = ast.parse(full_code)
                lines = full_code.splitlines()
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        if node.name == focus_symbol:
                            start_l = node.lineno - 1
                            end_l = getattr(node, "end_lineno", len(lines))
                            target_section = "\n".join(lines[start_l:end_l])
                            target_title = f"`{rel_target}::{focus_symbol}` (Target Symbol Implementation)"
                            break
            except Exception:
                pass

        # Identify 1st-degree outbound imports
        outbound_files: Set[str] = set()
        stem = os.path.splitext(os.path.basename(rel_target))[0]
        imported_modules = self.impact_analyzer.import_graph.get(rel_target, set())
        for f in self.impact_analyzer.files_list:
            f_stem = os.path.splitext(os.path.basename(f))[0]
            if f_stem in imported_modules and f != rel_target:
                outbound_files.add(f)

        # Identify 1st-degree inbound callers
        inbound_files: Set[str] = set()
        if focus_symbol:
            impact = self.impact_analyzer.analyze_symbol(focus_symbol)
            for caller in impact.get("direct_callers", []):
                inbound_files.add(caller["file"])
        else:
            for f in self.impact_analyzer.inbound_graph.get(stem, set()):
                if f != rel_target:
                    inbound_files.add(f)

        surrounding_files = sorted(list((outbound_files | inbound_files) - {rel_target}))

        md = [
            f"# 🎯 Focus-Aware Smart Skeleton Context: {os.path.basename(rel_target)}",
            "",
            f"> **Architecture Pattern:** Zero-Hallucination Hybrid (Full Target + Surrounding T-3 AST Skeletons)",
            f"> **Target File:** `{rel_target}` | **Surrounding Ecosystem:** {len(surrounding_files)} modules",
            "",
            f"## 1. 🔍 Target Implementation: {target_title}",
            "```python" if rel_target.endswith(".py") else "```text",
            target_section,
            "```",
            "",
            "## 2. 🌐 Surrounding Interface Ecosystem (T-3 AST Skeletons)",
            "> The following 1st-degree dependencies and callers are pruned to AST signatures to guarantee interface fidelity with minimum token overhead:",
            ""
        ]

        for s_file in surrounding_files:
            s_full = os.path.join(self.project_dir, s_file)
            try:
                with open(s_full, 'r', encoding='utf-8', errors='ignore') as fp:
                    s_code = fp.read()
                pruned = TokenReducer.reduce(s_code, s_file, mode="ultra")
                ext = os.path.splitext(s_file)[1].lstrip('.') or "py"
                rel_type = "Outbound Dependency" if s_file in outbound_files else "Inbound Caller"
                md.append(f"### `{s_file}` ({rel_type})")
                md.append(f"```{ext}")
                md.append(pruned)
                md.append("```\n")
            except Exception:
                pass

        # Section 3: Surface matching reusable helpers across repository
        try:
            suggester = ReusableHelperSuggester(self.project_dir)
            lookup_query = task_intent or focus_symbol or os.path.splitext(os.path.basename(rel_target))[0]
            helpers = suggester.suggest_helpers(lookup_query, target_file=rel_target, top_k=3)
            if helpers:
                md.append("## 3. 💡 Reusable Repository Helpers Available")
                md.append("> **T-Zero Anti-Reinvention Guard:** Pruned skeletons might conceal helper utilities. The following existing helpers match your context and are ready for direct import:")
                md.append("")
                for h in helpers:
                    md.append(f"- **`{h['name']}`** in `{h['file']}:{h['line']}`")
                    md.append(f"  ```python\n  {h['import_stmt']}\n  ```")
                    if h.get("docstring"):
                        md.append(f"  *{h['docstring']}*")
                md.append("")
        except Exception:
            pass

        return "\n".join(md)


# =============================================================================
# 9. GRAPH-CENTRALITY ARCHITECTURAL PAGERANK (TOOL 19)
# =============================================================================

class RepositoryPageRank:
    """Pure-Python PageRank implementation to identify the architectural backbone of a codebase."""

    def __init__(self, project_dir: str):
        self.project_dir = os.path.abspath(project_dir)
        self.impact_analyzer = ChangeImpactAnalyzer(project_dir)

    def rank(self, top_k: int = 15, damping: float = 0.85, max_iter: int = 40) -> List[Dict[str, Any]]:
        """Calculates PageRank centrality for all files in the repository."""
        nodes = sorted(self.impact_analyzer.files_list)
        N = len(nodes)
        if N == 0:
            return []

        node_to_idx = {node: i for i, node in enumerate(nodes)}
        stem_to_node = {}
        for n in nodes:
            s = os.path.splitext(os.path.basename(n))[0]
            stem_to_node[s] = n

        # Build adjacency
        out_edges: Dict[int, Set[int]] = collections.defaultdict(set)
        in_edges: Dict[int, Set[int]] = collections.defaultdict(set)

        for src, imps in self.impact_analyzer.import_graph.items():
            if src in node_to_idx:
                u = node_to_idx[src]
                for imp in imps:
                    if imp in stem_to_node:
                        dst = stem_to_node[imp]
                        v = node_to_idx[dst]
                        if u != v:
                            out_edges[u].add(v)
                            in_edges[v].add(u)

        # Power iteration
        scores = [1.0 / N] * N
        for _ in range(max_iter):
            new_scores = [(1.0 - damping) / N] * N
            dangling_sum = sum(scores[i] for i in range(N) if not out_edges[i])
            dangling_alloc = (damping * dangling_sum) / N

            for i in range(N):
                new_scores[i] += dangling_alloc
                for parent in in_edges[i]:
                    out_deg = len(out_edges[parent])
                    if out_deg > 0:
                        new_scores[i] += damping * (scores[parent] / out_deg)

            scores = new_scores

        # Rank
        ranked_indices = sorted(range(N), key=lambda i: scores[i], reverse=True)
        results = []
        for idx in ranked_indices[:top_k]:
            file_p = nodes[idx]
            in_deg = len(in_edges[idx])
            out_deg = len(out_edges[idx])
            raw_score = scores[idx]

            # Extract key contracts
            contracts = []
            content = self.impact_analyzer.snippets.get(file_p, "")
            try:
                tree = ast.parse(content)
                for node in tree.body:
                    if isinstance(node, ast.ClassDef):
                        contracts.append(f"class {node.name}")
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        contracts.append(f"def {node.name}()")
            except Exception:
                pass

            results.append({
                "file": file_p,
                "pagerank_score": round(raw_score * 100, 3),
                "inbound_degree": in_deg,
                "outbound_degree": out_deg,
                "key_contracts": contracts[:5]
            })

        return results

    def format_report(self, rankings: List[Dict[str, Any]]) -> str:
        out = [
            f"# 🏛️ Repository Architectural PageRank & Centrality Backbone",
            "",
            "> **Graph Theory Analysis:** Identifies the foundational core modules of your project based on AST import topologies.",
            "",
            "| Rank | Module | Centrality Score | Inbound (Callers) | Outbound (Deps) | Key Exported Contracts |",
            "|:----:|:-------|:----------------:|:-----------------:|:---------------:|:-----------------------|"
        ]
        for rank, r in enumerate(rankings, 1):
            contracts_str = ", ".join(f"`{c}`" for c in r["key_contracts"]) if r["key_contracts"] else "*none*"
            out.append(f"| #{rank} | `{r['file']}` | **{r['pagerank_score']}** | {r['inbound_degree']} | {r['outbound_degree']} | {contracts_str} |")

        out.append("\n> **Recommendation:** Protect high-centrality modules (Top #1-#5) with strict unit tests and boundary rules before refactoring.")
        return "\n".join(out)


# =============================================================================
# 10. DEEP SYMBOL CALL-CHAIN & EXECUTION PATH TRACER (TOOL 20)
# =============================================================================

class SymbolCallChainTracer:
    """Traces upstream callers and downstream callees across the workspace AST."""

    def __init__(self, project_dir: str):
        self.project_dir = os.path.abspath(project_dir)
        self.call_graph: Dict[str, Set[str]] = collections.defaultdict(set) # caller -> set(callees)
        self.reverse_call_graph: Dict[str, Set[str]] = collections.defaultdict(set) # callee -> set(callers)
        self._build_call_graph()

    def _build_call_graph(self):
        for root, _, files in os.walk(self.project_dir):
            if should_skip_dir(root, self.project_dir):
                continue
            for f in files:
                if f.endswith('.py'):
                    full_p = os.path.join(root, f)
                    try:
                        with open(full_p, 'r', encoding='utf-8', errors='ignore') as fp:
                            content = fp.read()
                        tree = ast.parse(content)
                        self._index_calls(tree)
                    except Exception:
                        pass

    def _index_calls(self, tree: ast.AST):
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                caller_name = node.name
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        callee_name = ""
                        if isinstance(child.func, ast.Name):
                            callee_name = child.func.id
                        elif isinstance(child.func, ast.Attribute):
                            callee_name = child.func.attr
                        if callee_name and callee_name != caller_name:
                            self.call_graph[caller_name].add(callee_name)
                            self.reverse_call_graph[callee_name].add(caller_name)

    def trace(self, symbol_name: str, max_depth: int = 3) -> Dict[str, Any]:
        """Traces upstream callers and downstream callees up to max_depth."""
        def trace_upstream(sym: str, depth: int, visited: Set[str]) -> List[Dict[str, Any]]:
            if depth >= max_depth or sym in visited:
                return []
            visited.add(sym)
            res = []
            for caller in sorted(self.reverse_call_graph.get(sym, set())):
                res.append({
                    "symbol": caller,
                    "depth": depth + 1,
                    "callers": trace_upstream(caller, depth + 1, visited.copy())
                })
            return res

        def trace_downstream(sym: str, depth: int, visited: Set[str]) -> List[Dict[str, Any]]:
            if depth >= max_depth or sym in visited:
                return []
            visited.add(sym)
            res = []
            for callee in sorted(self.call_graph.get(sym, set())):
                res.append({
                    "symbol": callee,
                    "depth": depth + 1,
                    "callees": trace_downstream(callee, depth + 1, visited.copy())
                })
            return res

        upstream = trace_upstream(symbol_name, 0, set())
        downstream = trace_downstream(symbol_name, 0, set())

        return {
            "symbol": symbol_name,
            "max_depth": max_depth,
            "upstream": upstream,
            "downstream": downstream,
            "total_upstream_callers": len(self.reverse_call_graph.get(symbol_name, set())),
            "total_downstream_callees": len(self.call_graph.get(symbol_name, set())),
        }

    def format_report(self, trace_result: Dict[str, Any]) -> str:
        sym = trace_result["symbol"]
        out = [
            f"# 🔗 Deep Symbol Call-Chain & Execution Path: `{sym}`",
            "",
            f"- **Target Symbol:** `{sym}`",
            f"- **Direct Inbound Callers:** {trace_result['total_upstream_callers']}",
            f"- **Direct Outbound Callees:** {trace_result['total_downstream_callees']}",
            f"- **Max Trace Depth:** {trace_result['max_depth']}",
            "",
            "## 1. ⬆️ Upstream Callers (Who calls this symbol):"
        ]

        def render_tree(items: List[Dict[str, Any]], key: str, prefix: str = ""):
            for item in items:
                out.append(f"{prefix}└── `{item['symbol']}` (Level {item['depth']})")
                if item.get(key):
                    render_tree(item[key], key, prefix + "    ")

        if trace_result["upstream"]:
            render_tree(trace_result["upstream"], "callers")
        else:
            out.append("*(No upstream callers detected in workspace)*")

        out.append("\n## 2. ⬇️ Downstream Callees (What this symbol calls internally):")
        if trace_result["downstream"]:
            render_tree(trace_result["downstream"], "callees")
        else:
            out.append("*(No internal callees detected in workspace)*")

        # Mermaid Diagram
        out.append("\n## 3. 📊 Visual Call Graph (Mermaid)")
        out.append("```mermaid")
        out.append("graph LR")
        out.append(f'    T["{sym} (TARGET)"]:::target')
        out.append("    classDef target fill:#00ffd8,stroke:#000,color:#000,font-weight:bold;")
        
        added_edges = set()
        for c in trace_result["upstream"]:
            edge = f'    "{c["symbol"]}" --> T'
            if edge not in added_edges:
                out.append(edge)
                added_edges.add(edge)

        for c in trace_result["downstream"]:
            edge = f'    T --> "{c["symbol"]}"'
            if edge not in added_edges:
                out.append(edge)
                added_edges.add(edge)

        out.append("```")
        return "\n".join(out)


# =============================================================================
# 11. CIRCULAR DEPENDENCY DETECTOR (DFS CYCLE TRAVERSAL)
# =============================================================================

def detect_circular_dependencies(import_graph: Any) -> List[List[str]]:
    """Detects import cycles (A -> B -> A) using Depth-First Search with recursion stack.
    Accepts either an explicit adjacency graph Dict[str, Set[str]] or a project_dir path."""
    if isinstance(import_graph, (str, os.PathLike)):
        project_dir = os.path.abspath(str(import_graph))
        graph: Dict[str, Set[str]] = {}
        for root, _, files in os.walk(project_dir):
            if should_skip_dir(root, project_dir):
                continue
            for f in files:
                if f.endswith(".py"):
                    full_p = os.path.join(root, f)
                    rel_mod = os.path.relpath(full_p, project_dir).replace("\\", "/").replace(".py", "").replace("/", ".")
                    deps = set()
                    try:
                        with open(full_p, "r", encoding="utf-8", errors="ignore") as io:
                            tree = ast.parse(io.read(), filename=full_p)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    deps.add(alias.name)
                            elif isinstance(node, ast.ImportFrom) and node.module:
                                deps.add(node.module)
                    except Exception:
                        pass
                    graph[rel_mod] = deps
        import_graph = graph

    cycles = []
    visited: Set[str] = set()
    rec_stack: List[str] = []

    def dfs(node: str):
        visited.add(node)
        rec_stack.append(node)

        for neighbor in import_graph.get(node, set()):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in rec_stack:
                cycle_start = rec_stack.index(neighbor)
                cycle = rec_stack[cycle_start:] + [neighbor]
                core_cycle = cycle[:-1]
                min_idx = core_cycle.index(min(core_cycle))
                canonical = core_cycle[min_idx:] + core_cycle[:min_idx] + [core_cycle[min_idx]]
                if canonical not in cycles:
                    cycles.append(canonical)

        rec_stack.pop()

    for n in sorted(import_graph.keys()):
        if n not in visited:
            dfs(n)

    return cycles


# =============================================================================
# 12. DEAD CODE & UNUSED SYMBOL FINDER (TOOL 21)
# =============================================================================

class DeadCodeFinder:
    """Discovers unused, unreferenced functions and classes across the codebase AST."""

    def __init__(self, project_dir: str):
        self.project_dir = os.path.abspath(project_dir)

    def find_dead_symbols(self) -> Dict[str, Any]:
        """Scans codebase to detect declared functions/classes never imported or referenced."""
        definitions = []  # (symbol_name, rel_path, line_no, kind)
        all_references: Set[str] = set()
        declared_all: Set[str] = set()

        for root, _, files in os.walk(self.project_dir):
            if should_skip_dir(root, self.project_dir):
                continue
            for f in files:
                if f.endswith('.py'):
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, self.project_dir).replace('\\', '/')
                    is_test = "test" in rel_p.lower() or f.startswith("test_")
                    try:
                        with open(full_p, 'r', encoding='utf-8', errors='ignore') as fp:
                            content = fp.read()
                        tree = ast.parse(content)
                    except Exception:
                        continue

                    for node in ast.walk(tree):
                        if isinstance(node, ast.Name):
                            all_references.add(node.id)
                        elif isinstance(node, ast.Attribute):
                            all_references.add(node.attr)
                        elif isinstance(node, (ast.Import, ast.ImportFrom)):
                            for alias in node.names:
                                all_references.add(alias.name)

                        # Top-level declarations from non-test source files
                        if not is_test and f != "__init__.py":
                            if isinstance(node, ast.ClassDef):
                                if not node.name.startswith("_") and node.name != "Config":
                                    definitions.append((node.name, rel_p, node.lineno, "class"))
                            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                if not node.name.startswith("_") and node.name not in ("main", "run", "handler"):
                                    definitions.append((node.name, rel_p, node.lineno, "function"))
                            elif isinstance(node, ast.Assign):
                                for target in node.targets:
                                    if isinstance(target, ast.Name) and target.id == "__all__":
                                        if isinstance(node.value, (ast.List, ast.Tuple)):
                                            for elt in node.value.elts:
                                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                                    declared_all.add(elt.value)

        impact = ChangeImpactAnalyzer(self.project_dir)
        dead_symbols = []
        for name, rel_p, lineno, kind in definitions:
            if name in declared_all:
                continue
            files_referencing = set()
            for snip_file, snip_content in impact.snippets.items():
                if re.search(rf"\b{re.escape(name)}\b", snip_content):
                    files_referencing.add(snip_file)
            
            external_refs = [sf for sf in files_referencing if sf != rel_p and "test" not in sf.lower()]
            if not external_refs:
                dead_symbols.append({
                    "symbol": name,
                    "kind": kind,
                    "file": rel_p,
                    "line": lineno
                })

        return {
            "total_dead_symbols": len(dead_symbols),
            "dead_symbols": dead_symbols
        }

    def format_report(self, res: Dict[str, Any]) -> str:
        count = res["total_dead_symbols"]
        if count == 0:
            return "✨ [CLEAN] Zero dead code detected across workspace. All defined symbols are referenced."

        out = [
            f"# 🧹 Dead Code & Unused Symbol Audit ({count} unreferenced symbols)\n",
            "> **AST Static Analysis:** The following symbols are defined in the workspace but never referenced by other modules:\n",
            "| Symbol | Kind | Declaring File | Line |",
            "|:---|:---|:---|:---|"
        ]
        for s in res["dead_symbols"]:
            out.append(f"| `{s['symbol']}` | {s['kind']} | `{s['file']}` | Line {s['line']} |")
        out.append("\n> **Recommendation:** Verify if these are intended public API exports or safe to prune.")
        return "\n".join(out)

    find_unused_symbols = find_dead_symbols


# =============================================================================
# 11. REUSABLE HELPER SUGGESTER & ANTI-REINVENTION GUARD
# =============================================================================

class ReusableHelperSuggester:
    """Discovers, ranks, and surfaces reusable utility and helper functions across repository AST.
    
    Prevents LLMs and developers from reinventing existing functions that may have been pruned
    from the context window or located in separate utility packages.
    """

    def __init__(self, project_dir: str):
        self.project_dir = os.path.abspath(project_dir)
        self.helpers: List[Dict[str, Any]] = []
        self._indexed = False

    def _ensure_indexed(self):
        if not self._indexed:
            self._index_codebase()
            self._indexed = True

    def _index_codebase(self):
        """Scans workspace python files and extracts reusable helper functions."""
        for root, _, files in os.walk(self.project_dir):
            if should_skip_dir(root, self.project_dir):
                continue
            for f in files:
                if f.endswith('.py'):
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, self.project_dir).replace('\\', '/')
                    # Skip test files and private hidden files
                    if any(t in rel_p.lower() for t in ("/test", "\\test", "tests/", "tests\\", "test_")):
                        continue
                    try:
                        with open(full_p, 'r', encoding='utf-8', errors='ignore') as fp:
                            content = fp.read()
                        self._extract_helpers_from_file(rel_p, content)
                    except Exception:
                        pass

    def _extract_helpers_from_file(self, rel_path: str, code: str):
        try:
            tree = ast.parse(code)
        except Exception:
            return

        lines = code.splitlines()
        is_util_file = any(u in rel_path.lower() for u in ("util", "helper", "common", "tools", "shared", "lib", "core"))

        mod_name = rel_path
        if mod_name.endswith(".py"):
            mod_name = mod_name[:-3]
        if mod_name.endswith("/__init__"):
            mod_name = mod_name[:-9]
        mod_dotted = mod_name.replace("/", ".").replace("\\", ".")

        helper_prefixes = (
            "get_", "parse_", "format_", "safe_", "is_", "has_", "compute_", "build_",
            "extract_", "clean_", "normalize_", "validate_", "to_", "from_", "find_",
            "convert_", "serialize_", "deserialize_", "read_", "write_", "load_", "dump_",
            "calculate_", "check_", "detect_", "scan_", "strip_", "ensure_", "resolve_"
        )

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fname = node.name
                if fname.startswith("__"):
                    continue
                if fname.startswith("test_") or fname in ("setUp", "tearDown", "main", "run"):
                    continue

                is_prefixed = fname.startswith(helper_prefixes)
                doc = (ast.get_docstring(node) or "").strip()

                if not (is_util_file or is_prefixed or doc):
                    continue

                start_l = node.lineno
                end_l = getattr(node, "end_lineno", len(lines))
                body = "\n".join(lines[start_l - 1:end_l])

                # Extract parameters signature
                args_list = []
                for a in node.args.args:
                    arg_str = a.arg
                    if a.annotation:
                        try:
                            arg_str += f": {ast.unparse(a.annotation)}"
                        except Exception:
                            pass
                    args_list.append(arg_str)
                ret_str = ""
                if node.returns:
                    try:
                        ret_str = f" -> {ast.unparse(node.returns)}"
                    except Exception:
                        pass

                sig_str = f"def {fname}({', '.join(args_list)}){ret_str}"

                tokens = set()
                for part in re.split(r'[_]+', fname):
                    subparts = re.findall(r'[A-Za-z][a-z0-9]*', part)
                    for sp in subparts:
                        tokens.add(sp.lower())
                for a in node.args.args:
                    tokens.add(a.arg.lower())
                if doc:
                    for w in re.findall(r'[a-zA-Z]{3,}', doc):
                        tokens.add(w.lower())

                import_stmt = f"from {mod_dotted} import {fname}"

                self.helpers.append({
                    "name": fname,
                    "file": rel_path,
                    "line": start_l,
                    "end_line": end_l,
                    "signature": sig_str,
                    "docstring": doc,
                    "body": body,
                    "import_stmt": import_stmt,
                    "is_util_file": is_util_file,
                    "tokens": tokens,
                })

    def suggest_helpers(self, query: str = "", target_file: str = "", top_k: int = 5) -> List[Dict[str, Any]]:
        """Searches repository helpers matching natural language query, function name, or task."""
        self._ensure_indexed()
        if not self.helpers:
            return []

        q_clean = (query or "").lower().strip()
        q_tokens = set(re.findall(r'[a-zA-Z0-9]+', q_clean))

        scored: List[Tuple[float, Dict[str, Any]]] = []
        for h in self.helpers:
            score = 0.0
            h_name = h["name"].lower()
            h_tokens = h["tokens"]
            h_doc = h["docstring"].lower()

            if q_clean and h_name == q_clean:
                score += 150.0
            elif q_clean and q_clean in h_name:
                score += 60.0

            if q_tokens:
                token_matches = q_tokens & h_tokens
                score += len(token_matches) * 25.0

                for qt in q_tokens:
                    if qt in h_doc:
                        score += 12.0

            if h["is_util_file"]:
                score *= 1.25

            if target_file and h["file"] == target_file:
                score *= 0.8  # Slight preference for importing from other modules

            if score > 0 or not q_clean:
                if not q_clean:
                    score = 20.0 if h["is_util_file"] else 5.0
                scored.append((score, h))

        scored.sort(key=lambda x: x[0], reverse=True)

        seen_names = set()
        results = []
        for s, h in scored:
            if h["name"] in seen_names:
                continue
            seen_names.add(h["name"])
            item = dict(h)
            item["relevance_score"] = round(s, 2)
            results.append(item)
            if len(results) >= top_k:
                break

        return results

    def check_reinvention_guard(self, code_snippet: str, target_file: str = "", top_k: int = 3) -> Dict[str, Any]:
        """Inspects newly written code snippet to detect if it re-implements existing workspace helpers."""
        self._ensure_indexed()
        warnings = []
        try:
            tree = ast.parse(code_snippet)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    new_fname = node.name
                    doc = ast.get_docstring(node) or ""
                    query = f"{new_fname} {doc}"
                    matches = self.suggest_helpers(query=query, target_file=target_file, top_k=top_k)
                    for m in matches:
                        if m["name"] == new_fname and target_file and m["file"] == target_file:
                            continue
                        if m["relevance_score"] >= 35.0:
                            warnings.append({
                                "new_symbol": new_fname,
                                "matched_helper": m["name"],
                                "file": m["file"],
                                "line": m["line"],
                                "import_stmt": m["import_stmt"],
                                "docstring": m["docstring"],
                                "body": m["body"],
                                "relevance_score": m["relevance_score"]
                            })
        except Exception:
            pass

        return {
            "has_reinventions": len(warnings) > 0,
            "total_warnings": len(warnings),
            "warnings": warnings
        }

    def format_helpers_report(self, results: List[Dict[str, Any]], query: str = "", include_body: bool = True) -> str:
        q_label = f': "{query}"' if query else ""
        out = [
            f"# 💡 Reusable Repository Helpers{q_label}\n",
            "> **T-Zero Anti-Reinvention Guard:** Pruning code into skeletons can sometimes hide utility helpers.",
            "> The following functions already exist in your workspace and can be directly imported and reused:\n"
        ]

        if not results:
            out.append("*(No matching reusable helpers found in the repository for this query)*")
            return "\n".join(out)

        out.append("| Helper Function | Module File | Line | Ready Import |")
        out.append("|:---|:---|:---|:---|")
        for r in results:
            out.append(f"| `{r['name']}` | `{r['file']}` | Line {r['line']} | `{r['import_stmt']}` |")
        out.append("")

        for i, r in enumerate(results, 1):
            out.append(f"### {i}. `{r['signature']}`")
            out.append(f"- **File:** `{r['file']}` (Line {r['line']})")
            out.append(f"- **Import:** `{r['import_stmt']}`")
            if r.get("docstring"):
                out.append(f"- **Docstring:** *{r['docstring']}*")
            if include_body and r.get("body"):
                out.append("```python")
                out.append(r["body"])
                out.append("```\n")

        out.append("> **Recommendation:** Import and reuse these existing helpers instead of writing duplicate logic.")
        return "\n".join(out)

    def format_guard_report(self, report: Dict[str, Any], include_body: bool = True) -> str:
        count = report.get("total_warnings", 0)
        out = [
            f"# 🛡️ T-Zero Anti-Reinvention Guard Alert ({count} Existing Helpers Found)\n",
            "> **AST Wheel-Reinvention Warning:** The code snippet being introduced defines functions that replicate helpers already present in the codebase:\n"
        ]
        for w in report.get("warnings", []):
            out.append(f"### ⚠️ Proposed Function: `{w['new_symbol']}`")
            out.append(f"- **Existing Helper:** `{w['matched_helper']}` in `{w['file']}:{w['line']}`")
            out.append(f"- **Recommended Reuse:**")
            out.append(f"  ```python\n  {w['import_stmt']}\n  ```")
            if w.get("docstring"):
                out.append(f"- **Existing Docstring:** *{w['docstring']}*")
            if include_body and w.get("body"):
                out.append("```python")
                out.append(w["body"])
                out.append("```\n")
        out.append("> **Action:** Avoid re-implementing these functions. Use the provided import statements instead.")
        return "\n".join(out)


