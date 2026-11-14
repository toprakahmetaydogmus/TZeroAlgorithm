# -*- coding: utf-8 -*-
"""
Siber Akademi — T-Zero Self-Healing AST Hallucination Auto-Corrector.
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: MIT

Statically inspects candidate code against verified workspace AST symbol tables.
Detects phantom imports, misspelled identifiers, and hallucinated method calls,
and automatically rewrites the AST to the correct valid local identifier.
"""

import os
import sys
import re
import ast
import difflib
from dataclasses import dataclass, field
from typing import Dict, List, Set, Any, Optional, Tuple

STD_LIB_ROOT_MODULES = {
    "os", "sys", "json", "time", "re", "math", "hashlib", "uuid", "datetime",
    "asyncio", "subprocess", "tempfile", "platform", "shutil", "urllib", "random",
    "logging", "collections", "functools", "itertools", "pathlib", "difflib"
}

TYPING_NAMES = {
    "Optional", "List", "Dict", "Tuple", "Set", "Any", "Union", "Callable",
    "Sequence", "Iterable", "NamedTuple", "TypeVar", "Generic", "Annotated"
}

PATHLIB_NAMES = {"Path"}


def find_best_symbol_match(target: str, candidates: Set[str], cutoff: float = 0.50) -> Tuple[Optional[str], float]:
    """Hybrid symbol matcher combining token-level Jaccard overlap, prefix boost, and SequenceMatcher."""
    if not candidates or not target:
        return None, 0.0
    t_lower = target.lower()
    for c in candidates:
        if c.lower() == t_lower:
            return c, 0.99

    best_cand: Optional[str] = None
    best_score: float = 0.0
    t_words = set(re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+', target))
    t_words = {w.lower() for w in t_words}

    for c in candidates:
        c_words = set(re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+', c))
        c_words = {w.lower() for w in c_words}
        word_overlap = len(t_words & c_words) / max(1, len(t_words | c_words)) if (t_words or c_words) else 0.0
        seq_ratio = difflib.SequenceMatcher(None, target, c).ratio()
        prefix_boost = 0.15 if (c.lower().startswith(target[:4].lower()) and len(target) >= 4) else 0.0
        score = (0.5 * seq_ratio) + (0.5 * word_overlap) + prefix_boost
        if score > best_score and score >= cutoff:
            best_score = score
            best_cand = c

    return best_cand, round(best_score, 2)


@dataclass
class HealingAction:
    original_symbol: str
    healed_symbol: str
    symbol_type: str  # "import", "method_call", "function_call"
    line_number: int
    confidence: float
    context_hint: str = ""


@dataclass
class HealingReport:
    success: bool
    original_code: str
    healed_code: str
    total_fixes: int
    actions: List[HealingAction] = field(default_factory=list)
    diff: str = ""


class _ASTHealerTransformer(ast.NodeTransformer):
    def __init__(self, known_functions: Set[str], known_imports: Set[str], known_methods: Set[str]):
        super().__init__()
        self.known_functions = known_functions
        self.known_imports = known_imports
        self.known_methods = known_methods
        self.actions: List[HealingAction] = []
        self.renamed_imports: Dict[str, str] = {}

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST:
        # Check imported names against known symbols
        new_names = []
        for alias in node.names:
            name = alias.name
            if self.known_imports and name not in self.known_imports:
                best, score = find_best_symbol_match(name, self.known_imports, cutoff=0.50)
                if best:
                    self.actions.append(HealingAction(
                        original_symbol=name,
                        healed_symbol=best,
                        symbol_type="import",
                        line_number=getattr(node, "lineno", 1),
                        confidence=score,
                        context_hint=f"Module: {node.module or ''}"
                    ))
                    self.renamed_imports[name] = best
                    new_names.append(ast.alias(name=best, asname=alias.asname))
                    continue
            new_names.append(alias)
        node.names = new_names
        return node

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if node.id in self.renamed_imports:
            node.id = self.renamed_imports[node.id]
        return node

    def visit_Call(self, node: ast.Call) -> ast.AST:
        self.generic_visit(node)
        # Check attribute calls (e.g. obj.calc_cost())
        if isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            if self.known_methods and attr_name not in self.known_methods:
                best, score = find_best_symbol_match(attr_name, self.known_methods, cutoff=0.50)
                if best:
                    self.actions.append(HealingAction(
                        original_symbol=attr_name,
                        healed_symbol=best,
                        symbol_type="method_call",
                        line_number=getattr(node, "lineno", 1),
                        confidence=score
                    ))
                    node.func.attr = best
        # Check standalone function calls (e.g. calculate_tokens())
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
            if self.known_functions and func_name not in self.known_functions:
                best, score = find_best_symbol_match(func_name, self.known_functions, cutoff=0.50)
                if best:
                    self.actions.append(HealingAction(
                        original_symbol=func_name,
                        healed_symbol=best,
                        symbol_type="function_call",
                        line_number=getattr(node, "lineno", 1),
                        confidence=score
                    ))
                    node.func.id = best
        return node


class ASTHallucinationAutoCorrector:
    """Self-healing engine to detect and repair hallucinated AI symbols."""

    SKIP_DIRS = {
        ".git", "__pycache__", ".pytest_cache", "target", "dist",
        "build", ".venv", "venv", "node_modules", ".superpowers", "bin"
    }

    @classmethod
    def collect_workspace_symbols(cls, workspace_dir: str) -> Tuple[Set[str], Set[str], Set[str]]:
        """Collects all real functions, imports, and methods defined across workspace."""
        functions: Set[str] = set()
        imports: Set[str] = set()
        methods: Set[str] = set()

        abs_root = os.path.abspath(workspace_dir)
        for root, dirs, fnames in os.walk(abs_root):
            dirs[:] = [d for d in dirs if d not in cls.SKIP_DIRS and not d.startswith(".")]
            for fname in fnames:
                if fname.endswith(".py"):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                            tree = ast.parse(f.read(), filename=fname)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                imports.add(node.name)
                                for item in node.body:
                                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                        methods.add(item.name)
                            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                functions.add(node.name)
                                imports.add(node.name)
                    except Exception:
                        pass

        return functions, imports, methods

    @classmethod
    def heal_code(cls, code: str, workspace_dir: str = ".") -> HealingReport:
        """Parses candidate code, fixes hallucinated symbols, and returns report."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return HealingReport(
                success=False,
                original_code=code,
                healed_code=code,
                total_fixes=0,
                diff=f"SyntaxError in code: {e}"
            )

        known_funcs, known_imports, known_methods = cls.collect_workspace_symbols(workspace_dir)
        transformer = _ASTHealerTransformer(known_funcs, known_imports, known_methods)
        healed_tree = transformer.visit(tree)
        ast.fix_missing_locations(healed_tree)

        try:
            healed_code = ast.unparse(healed_tree)
        except Exception:
            healed_code = code

        # Check for unimported standard modules & typing names
        declared_or_imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    declared_or_imported.add(a.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                for a in node.names:
                    declared_or_imported.add(a.name)
            elif isinstance(node, ast.FunctionDef):
                declared_or_imported.add(node.name)
            elif isinstance(node, ast.ClassDef):
                declared_or_imported.add(node.name)

        used_names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        missing_root_modules = sorted(list(STD_LIB_ROOT_MODULES & used_names - declared_or_imported))
        missing_typing = sorted(list(TYPING_NAMES & used_names - declared_or_imported))
        missing_path = sorted(list(PATHLIB_NAMES & used_names - declared_or_imported))

        injected_headers = []
        for mod in missing_root_modules:
            injected_headers.append(f"import {mod}")
            transformer.actions.append(HealingAction(
                original_symbol=f"<missing import {mod}>",
                healed_symbol=f"import {mod}",
                symbol_type="auto_import",
                line_number=1,
                confidence=1.0,
                context_hint="Auto-injected standard library import"
            ))
        if missing_typing:
            injected_headers.append(f"from typing import {', '.join(missing_typing)}")
            for t_name in missing_typing:
                transformer.actions.append(HealingAction(
                    original_symbol=f"<missing typing {t_name}>",
                    healed_symbol=f"from typing import {t_name}",
                    symbol_type="auto_import",
                    line_number=1,
                    confidence=1.0,
                    context_hint="Auto-injected typing annotation import"
                ))
        if missing_path:
            injected_headers.append("from pathlib import Path")
            transformer.actions.append(HealingAction(
                original_symbol="<missing pathlib Path>",
                healed_symbol="from pathlib import Path",
                symbol_type="auto_import",
                line_number=1,
                confidence=1.0,
                context_hint="Auto-injected pathlib import"
            ))

        if injected_headers:
            header_str = "\n".join(injected_headers) + "\n\n"
            healed_code = header_str + healed_code

        # Generate diff
        orig_lines = code.splitlines(keepends=True)
        healed_lines = healed_code.splitlines(keepends=True)
        diff_lines = list(difflib.unified_diff(
            orig_lines, healed_lines, fromfile="candidate.py (ai_generated)", tofile="healed.py (ast_corrected)"
        ))
        diff_str = "".join(diff_lines)

        return HealingReport(
            success=True,
            original_code=code,
            healed_code=healed_code,
            total_fixes=len(transformer.actions),
            actions=transformer.actions,
            diff=diff_str
        )

    @classmethod
    def heal_file(cls, file_path: str, workspace_dir: str = ".", apply_write: bool = False) -> HealingReport:
        """Reads file, applies healing, optionally overwrites if apply_write is True."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()

        report = cls.heal_code(code, workspace_dir=workspace_dir)
        if apply_write and report.total_fixes > 0:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report.healed_code)

        return report

    @classmethod
    def render_cli(cls, rep: HealingReport, target_hint: str = ""):
        print("\n🔧 \033[1mT-ZERO SELF-HEALING AST AUTO-CORRECTOR\033[0m")
        print("=" * 70)
        if target_hint:
            print(f"🎯 Target File: {target_hint}")
        print(f"📊 Auto-Repaired Hallucinations: \033[1m{rep.total_fixes}\033[0m")

        if rep.actions:
            print("\n📋 Detected & Repaired Symbols:")
            for a in rep.actions:
                conf_pct = int(a.confidence * 100)
                print(f"  • Line {a.line_number} [{a.symbol_type}]: \033[31m{a.original_symbol}\033[0m ➔ \033[32m{a.healed_symbol}\033[0m (Confidence: {conf_pct}%)")

            if rep.diff:
                print("\n🔍 AST Unified Diff:")
                for line in rep.diff.splitlines()[:20]:
                    if line.startswith("+"):
                        print(f"\033[32m{line}\033[0m")
                    elif line.startswith("-"):
                        print(f"\033[31m{line}\033[0m")
                    else:
                        print(line)
        else:
            print("\033[32m✅ Flawless Code: 0 hallucinated symbols detected! AST matches workspace.\033[0m")
        print("=" * 70)

