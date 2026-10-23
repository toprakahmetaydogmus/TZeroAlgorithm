# -*- coding: utf-8 -*-
"""T-Zero Cross-Module AST Call-Graph Reachability & Dead-Code Pruning Engine.

Performs static AST call-graph reachability analysis across multi-file codebases,
discovering reachable symbols from specified entrypoints and pruning unreferenced
functions and dead classes to assemble ultra-compact, Zero-Waste LLM prompt contexts.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of T-Zero Context Architect v7.0.0 Master Edition.
"""

import ast
import os
import re
from typing import Dict, List, Set, Any, Optional


class SymbolNode:
    """Represents a callable symbol (function or class) in the codebase AST."""
    def __init__(self, name: str, file_path: str, start_line: int, end_line: int, code: str, is_class: bool = False):
        self.name = name
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.code = code
        self.is_class = is_class
        self.calls: Set[str] = set()

    @property
    def symbol_id(self) -> str:
        return f"{self.file_path}:{self.name}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.symbol_id,
            "name": self.name,
            "file": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "is_class": self.is_class,
            "calls": sorted(list(self.calls))
        }


class CallExtractorVisitor(ast.NodeVisitor):
    """AST Visitor to extract invoked function and class names within a symbol body."""
    def __init__(self):
        self.invoked_names: Set[str] = set()

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            self.invoked_names.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.invoked_names.add(node.func.attr)
        self.generic_visit(node)


class CallGraphReachabilityEngine:
    """Enterprise AST graph reachability engine for zero-waste LLM prompt synthesis."""

    IGNORE_DIRS = {
        ".git", "__pycache__", "venv", ".venv", "env", "node_modules",
        "build", "dist", ".gemini", ".idea", ".vscode", "crates", "assets"
    }

    def __init__(self, workspace_root: str = "."):
        self.workspace_root = os.path.abspath(workspace_root)
        self.symbols: Dict[str, SymbolNode] = {}  # symbol_id -> SymbolNode
        self.name_to_ids: Dict[str, List[str]] = {}  # symbol_name -> list of symbol_ids
        self.file_contents: Dict[str, str] = {}
        self.module_top_level_calls: Dict[str, Set[str]] = {}

    def scan_workspace(self):
        """Discovers and parses all Python files in the workspace root."""
        self.symbols.clear()
        self.name_to_ids.clear()
        self.file_contents.clear()
        self.module_top_level_calls.clear()

        for root, dirs, files in os.walk(self.workspace_root):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            for file in files:
                if file.endswith(".py"):
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, self.workspace_root).replace("\\", "/")
                    try:
                        with open(full_p, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read()
                        self.file_contents[rel_p] = content
                        self._parse_file(rel_p, content)
                    except Exception:
                        continue

    def _parse_file(self, rel_path: str, content: str):
        """Parses a single Python file into AST and indexes classes, functions, and top-level calls."""
        try:
            tree = ast.parse(content)
        except Exception:
            return

        lines = content.splitlines()
        top_calls: Set[str] = set()

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = node.name
                start = getattr(node, "lineno", 1)
                end = getattr(node, "end_lineno", start)
                code_snippet = "\n".join(lines[start - 1:end])
                
                is_cls = isinstance(node, ast.ClassDef)
                sym = SymbolNode(name, rel_path, start, end, code_snippet, is_class=is_cls)
                
                # Extract calls inside this function/class
                extractor = CallExtractorVisitor()
                extractor.visit(node)
                sym.calls = extractor.invoked_names

                self.symbols[sym.symbol_id] = sym
                self.name_to_ids.setdefault(name, []).append(sym.symbol_id)
            elif isinstance(node, ast.If):
                # Check for if __name__ == "__main__":
                if self._is_main_guard(node):
                    extractor = CallExtractorVisitor()
                    extractor.visit(node)
                    top_calls.update(extractor.invoked_names)
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                extractor = CallExtractorVisitor()
                extractor.visit(node)
                top_calls.update(extractor.invoked_names)

        self.module_top_level_calls[rel_path] = top_calls

    @staticmethod
    def _is_main_guard(node: ast.If) -> bool:
        """Checks if an AST If block represents if __name__ == '__main__':."""
        try:
            test = node.test
            if isinstance(test, ast.Compare):
                left = test.left
                if isinstance(left, ast.Name) and left.id == "__name__":
                    for comparator in test.comparators:
                        if isinstance(comparator, ast.Constant) and comparator.value == "__main__":
                            return True
        except Exception:
            pass
        return False

    def build_reachability_graph(self, entrypoints: Optional[List[str]] = None) -> Dict[str, Any]:
        """Calculates reachable vs dead symbols using BFS graph traversal."""
        if not self.symbols:
            self.scan_workspace()

        entry_paths: Set[str] = set()
        if entrypoints:
            for ep in entrypoints:
                clean_ep = os.path.relpath(os.path.join(self.workspace_root, ep), self.workspace_root).replace("\\", "/")
                entry_paths.add(clean_ep)
        else:
            # Default to standard common entrypoints
            candidates = ["main.py", "app.py", "cli.py", "run.py", "tzero_v3.py"]
            for c in candidates:
                if c in self.file_contents:
                    entry_paths.add(c)
            if not entry_paths and self.file_contents:
                # Pick first file
                entry_paths.add(sorted(list(self.file_contents.keys()))[0])

        # Seed queue with entrypoint roots
        queue: List[str] = []
        visited_ids: Set[str] = set()

        # Add top-level called symbols and main functions from entrypoints
        for ep in entry_paths:
            top_calls = self.module_top_level_calls.get(ep, set())
            for call_name in top_calls:
                for target_id in self.name_to_ids.get(call_name, []):
                    if target_id not in visited_ids:
                        visited_ids.add(target_id)
                        queue.append(target_id)

            # Also add any function named 'main', 'run', 'cli' in the entrypoint file
            for sym_id, sym in self.symbols.items():
                if sym.file_path == ep and sym.name in {"main", "run", "cli", "app"}:
                    if sym_id not in visited_ids:
                        visited_ids.add(sym_id)
                        queue.append(sym_id)

        # Fallback if no specific entrypoint call found: mark all top functions in entrypoints
        if not queue:
            for sym_id, sym in self.symbols.items():
                if sym.file_path in entry_paths:
                    if sym_id not in visited_ids:
                        visited_ids.add(sym_id)
                        queue.append(sym_id)

        # Graph BFS traversal
        while queue:
            curr_id = queue.pop(0)
            curr_sym = self.symbols.get(curr_id)
            if not curr_sym:
                continue

            for call_name in curr_sym.calls:
                target_ids = self.name_to_ids.get(call_name, [])
                for t_id in target_ids:
                    if t_id not in visited_ids:
                        visited_ids.add(t_id)
                        queue.append(t_id)

        reachable_symbols = [self.symbols[sid] for sid in visited_ids if sid in self.symbols]
        dead_symbols = [sym for sid, sym in self.symbols.items() if sid not in visited_ids]

        return {
            "entrypoints": sorted(list(entry_paths)),
            "reachable": reachable_symbols,
            "dead": dead_symbols
        }

    def generate_zero_waste_prompt(self, entrypoints: Optional[List[str]] = None) -> Dict[str, Any]:
        """Assembles a streamlined prompt context containing strictly reachable code."""
        graph = self.build_reachability_graph(entrypoints)
        reachable: List[SymbolNode] = graph["reachable"]
        dead: List[SymbolNode] = graph["dead"]

        # Calculate original raw characters vs pruned
        raw_chars = sum(len(c) for c in self.file_contents.values())
        
        # Group reachable symbols by file
        file_to_nodes: Dict[str, List[SymbolNode]] = {}
        for sym in reachable:
            file_to_nodes.setdefault(sym.file_path, []).append(sym)

        # Build clean pruned context
        prompt_lines = [
            "# ===================================================================",
            "# ⚡ T-ZERO ZERO-WASTE PROMPT CONTEXT (PRUNED REACHABILITY GRAPH)",
            f"# Entrypoints: {', '.join(graph['entrypoints'])}",
            f"# Active symbols: {len(reachable)} | Dead symbols pruned: {len(dead)}",
            "# ===================================================================\n"
        ]

        for file_p in sorted(file_to_nodes.keys()):
            nodes = sorted(file_to_nodes[file_p], key=lambda x: x.start_line)
            prompt_lines.append(f"## File: {file_p}")
            prompt_lines.append("```python")
            for node in nodes:
                prompt_lines.append(f"# [{node.file_path}:{node.name} L{node.start_line}-{node.end_line}]")
                prompt_lines.append(node.code)
                prompt_lines.append("")
            prompt_lines.append("```\n")

        zero_waste_prompt = "\n".join(prompt_lines)

        # Calculate code symbol tokens (raw vs pruned)
        raw_code_chars = sum(len(sym.code) for sym in reachable) + sum(len(sym.code) for sym in dead)
        pruned_code_chars = sum(len(sym.code) for sym in reachable)
        raw_tokens = max(1, raw_code_chars // 4)
        pruned_tokens = max(1, pruned_code_chars // 4)
        reduction_pct = round(max(0.0, (1.0 - (pruned_code_chars / max(1, raw_code_chars))) * 100), 2)

        return {
            "entrypoints": graph["entrypoints"],
            "reachable_symbols": [s.to_dict() for s in reachable],
            "dead_symbols": [s.to_dict() for s in dead],
            "reachable_count": len(reachable),
            "pruned_dead_count": len(dead),
            "raw_tokens": raw_tokens,
            "zero_waste_tokens": pruned_tokens,
            "token_reduction_pct": reduction_pct,
            "zero_waste_prompt": zero_waste_prompt
        }
