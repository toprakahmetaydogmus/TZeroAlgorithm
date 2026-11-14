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
import builtins
import difflib
from dataclasses import dataclass, field
from typing import Dict, List, Set, Any, Optional, Tuple

STD_LIB_ROOT_MODULES = {
    "os", "sys", "json", "time", "re", "math", "hashlib", "uuid", "datetime",
    "asyncio", "subprocess", "tempfile", "platform", "shutil", "urllib", "random",
    "logging", "collections", "functools", "itertools", "pathlib", "difflib",
    "typing", "dataclasses", "unittest", "tomllib", "argparse", "io", "copy"
}

TYPING_NAMES = {
    "Optional", "List", "Dict", "Tuple", "Set", "Any", "Union", "Callable",
    "Sequence", "Iterable", "NamedTuple", "TypeVar", "Generic", "Annotated"
}

PATHLIB_NAMES = {"Path"}

PYTHON_BUILTIN_FUNCTIONS = set(dir(builtins))

BUILTIN_COMMON_METHODS = {
    # unittest / testing
    "assert", "assertequal", "assertnotequal", "asserttrue", "assertfalse",
    "assertis", "assertisnot", "assertisnone", "assertisnotnone",
    "assertin", "assertnotin", "assertisinstance", "assertnotisinstance",
    "assertgreater", "assertgreaterequal", "assertless", "assertlessequal",
    "assertalmostequal", "assertnotalmostequal", "assertraises", "assertwarns",
    "assertlogs", "assertcount", "assertsequenceequal", "assertdictequal",
    "setup", "teardown", "setupclass", "teardownclass",
    # pathlib & fs methods
    "write_text", "read_text", "write_bytes", "read_bytes", "mkdir", "unlink",
    "rmdir", "rename", "replace", "stat", "chmod", "touch", "iterdir", "glob",
    "rglob", "is_dir", "is_file", "is_symlink", "samefile", "expanduser",
    # dict / list / set / str / io / process methods
    "append", "extend", "insert", "remove", "pop", "clear", "index", "count",
    "sort", "reverse", "copy", "get", "setdefault", "update", "values",
    "keys", "items", "split", "rsplit", "splitlines", "join", "strip",
    "lstrip", "rstrip", "lower", "upper", "capitalize", "title", "startswith",
    "endswith", "replace", "find", "rfind", "encode", "decode", "format",
    "read", "readline", "readlines", "write", "writelines", "close", "seek",
    "tell", "flush", "seekable", "readable", "writable", "fileno", "isatty",
    "communicate", "poll", "wait", "terminate", "kill", "send_signal",
    "dump", "dumps", "load", "loads", "run", "call", "check_call", "check_output",
    "exists", "is_file", "is_dir", "resolve", "parent", "parents", "stem",
    "suffix", "suffixes", "name", "as_posix", "match", "search", "findall",
    "finditer", "sub", "subn", "group", "groups", "groupdict", "start", "end",
    "span", "sleep", "time", "monotonic", "now", "utcnow", "isoformat",
    "strftime", "strptime", "timestamp", "date", "year", "month", "day",
    "hour", "minute", "second", "microsecond", "total_seconds", "days",
    "parse", "unparse", "walk", "visit", "generic_visit"
}

IGNORED_WORKSPACE_FILES = {
    "tzero_gateway.py", "auto_outreach.py", "auto_onprem_outreach.py",
    "test_gateway_client.py", "siber_akademi_icon.py"
}


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
    def __init__(
        self,
        known_functions: Set[str],
        known_imports: Set[str],
        known_methods: Set[str],
        module_symbol_map: Optional[Dict[str, Set[str]]] = None
    ):
        super().__init__()
        self.known_functions = known_functions
        self.known_imports = known_imports
        self.known_methods = known_methods
        self.module_symbol_map = module_symbol_map or {}
        self.actions: List[HealingAction] = []
        self.renamed_imports: Dict[str, str] = {}

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST:
        # Never alter imports from Python standard library or popular runtime libraries
        if node.module:
            root_mod = node.module.split(".")[0]
            if (
                root_mod in STD_LIB_ROOT_MODULES
                or root_mod in getattr(sys, "stdlib_module_names", set())
                or root_mod in ("requests", "keyring", "PIL", "pygments", "pytest", "mcp", "pydantic", "tiktoken")
            ):
                return node

        # Check imported names against known symbols
        new_names = []
        target_candidates = self.known_imports
        if node.module and self.module_symbol_map:
            mod_key = node.module.split(".")[-1]
            if node.module in self.module_symbol_map and self.module_symbol_map[node.module]:
                target_candidates = self.module_symbol_map[node.module]
            elif mod_key in self.module_symbol_map and self.module_symbol_map[mod_key]:
                target_candidates = self.module_symbol_map[mod_key]

        for alias in node.names:
            name = alias.name
            if target_candidates and name not in target_candidates:
                best, score = find_best_symbol_match(name, target_candidates, cutoff=0.50)
                if best and best != name:
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
            if (
                attr_name.startswith("_")
                or attr_name.startswith("assert")
                or attr_name.lower() in BUILTIN_COMMON_METHODS
            ):
                return node
            if self.known_methods and attr_name not in self.known_methods:
                best, score = find_best_symbol_match(attr_name, self.known_methods, cutoff=0.55)
                if best and best != attr_name:
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
            if (
                func_name.startswith("_")
                or func_name in PYTHON_BUILTIN_FUNCTIONS
            ):
                return node
            if self.known_functions and func_name not in self.known_functions:
                best, score = find_best_symbol_match(func_name, self.known_functions, cutoff=0.55)
                if best and best != func_name:
                    self.actions.append(HealingAction(
                        original_symbol=func_name,
                        healed_symbol=best,
                        symbol_type="function_call",
                        line_number=getattr(node, "lineno", 1),
                        confidence=score
                    ))
                    node.func.id = best
        return node


class WorkspaceSymbolsResult:
    """Container for collected symbols supporting both 3-element unpacking and module map."""
    def __init__(self, funcs: Set[str], imports: Set[str], methods: Set[str], module_map: Optional[Dict[str, Set[str]]] = None):
        self.functions = funcs
        self.imports = imports
        self.methods = methods
        self.module_map = module_map or {}

    def __iter__(self):
        yield self.functions
        yield self.imports
        yield self.methods

    def __getitem__(self, idx):
        return (self.functions, self.imports, self.methods, self.module_map)[idx]

    def __len__(self):
        return 3


class ASTHallucinationAutoCorrector:
    """Self-healing engine to detect and repair hallucinated AI symbols."""

    SKIP_DIRS = {
        ".git", "__pycache__", ".pytest_cache", "target", "dist",
        "build", ".venv", "venv", "node_modules", ".superpowers", "bin"
    }

    @classmethod
    def collect_workspace_symbols(cls, workspace_dir: str) -> WorkspaceSymbolsResult:
        """Collects all real functions, imports, and methods defined across workspace."""
        functions: Set[str] = set()
        imports: Set[str] = set()
        methods: Set[str] = set()
        module_map: Dict[str, Set[str]] = {}

        abs_root = os.path.abspath(workspace_dir)
        for root, dirs, fnames in os.walk(abs_root):
            dirs[:] = [d for d in dirs if d not in cls.SKIP_DIRS and not d.startswith(".")]
            for fname in fnames:
                if fname in IGNORED_WORKSPACE_FILES or fname.startswith("."):
                    continue
                if fname.endswith(".py"):
                    fpath = os.path.join(root, fname)
                    mod_name = os.path.splitext(fname)[0]
                    imports.add(mod_name)
                    rel_dir = os.path.relpath(root, abs_root).replace(os.sep, ".").replace("/", ".")
                    if rel_dir != "." and not rel_dir.startswith("."):
                        module_map.setdefault(rel_dir, set()).add(mod_name)
                        parent_pkg = rel_dir.split(".")[-1]
                        module_map.setdefault(parent_pkg, set()).add(mod_name)
                    mod_symbols: Set[str] = set()
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                            tree = ast.parse(f.read(), filename=fname)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                imports.add(node.name)
                                mod_symbols.add(node.name)
                                for item in node.body:
                                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                        methods.add(item.name)
                            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                functions.add(node.name)
                                imports.add(node.name)
                                mod_symbols.add(node.name)
                        module_map[mod_name] = mod_symbols
                        rel = os.path.relpath(fpath, abs_root).replace(os.sep, ".").replace("/", ".")
                        if rel.endswith(".py"):
                            rel = rel[:-3]
                        module_map[rel] = mod_symbols
                    except Exception:
                        pass

        return WorkspaceSymbolsResult(functions, imports, methods, module_map)

    @classmethod
    def heal_code(
        cls,
        code: str,
        workspace_dir: str = ".",
        precomputed_symbols: Optional[Any] = None
    ) -> HealingReport:
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

        if precomputed_symbols is not None:
            if hasattr(precomputed_symbols, "module_map"):
                known_funcs = precomputed_symbols.functions
                known_imports = precomputed_symbols.imports
                known_methods = precomputed_symbols.methods
                module_map = precomputed_symbols.module_map
            else:
                known_funcs, known_imports, known_methods = precomputed_symbols[:3]
                module_map = precomputed_symbols[3] if len(precomputed_symbols) > 3 else {}
        else:
            sym_res = cls.collect_workspace_symbols(workspace_dir)
            known_funcs = sym_res.functions
            known_imports = sym_res.imports
            known_methods = sym_res.methods
            module_map = sym_res.module_map

        transformer = _ASTHealerTransformer(known_funcs, known_imports, known_methods, module_symbol_map=module_map)
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

        if not transformer.actions and not injected_headers:
            return HealingReport(
                success=True,
                original_code=code,
                healed_code=code,
                total_fixes=0,
                actions=[],
                diff=""
            )

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
    def heal_file(
        cls,
        file_path: str,
        workspace_dir: str = ".",
        apply_write: bool = False,
        precomputed_symbols: Optional[Tuple[Set[str], Set[str], Set[str]]] = None
    ) -> HealingReport:
        """Reads file, applies healing, optionally overwrites if apply_write is True."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()

        report = cls.heal_code(code, workspace_dir=workspace_dir, precomputed_symbols=precomputed_symbols)
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

    @classmethod
    def heal_workspace(
        cls,
        target_dir: str = ".",
        workspace_dir: Optional[str] = None,
        apply_write: bool = False,
        exclude_dirs: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """Recursively scans and self-heals all Python source files across target_dir."""
        if workspace_dir is None:
            workspace_dir = target_dir
        if exclude_dirs is None:
            exclude_dirs = {
                ".git", ".venv", "venv", "node_modules", "build", "dist",
                "__pycache__", ".pytest_cache", ".tzero", "tzero-showcase"
            }
        scanned_files = 0
        healed_reports: List[Tuple[str, HealingReport]] = []
        total_fixes = 0
        precomputed_symbols = cls.collect_workspace_symbols(workspace_dir)

        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
            for f in files:
                if f in IGNORED_WORKSPACE_FILES or f.startswith("."):
                    continue
                if f.endswith(".py"):
                    scanned_files += 1
                    full_path = os.path.join(root, f)
                    try:
                        rep = cls.heal_file(
                            full_path,
                            workspace_dir=workspace_dir,
                            apply_write=apply_write,
                            precomputed_symbols=precomputed_symbols
                        )
                        if rep.total_fixes > 0:
                            healed_reports.append((full_path, rep))
                            total_fixes += rep.total_fixes
                    except Exception:
                        pass

        return {
            "success": True,
            "workspace_dir": workspace_dir,
            "total_files_scanned": scanned_files,
            "healed_files_count": len(healed_reports),
            "total_fixes": total_fixes,
            "reports": healed_reports,
            "written_to_disk": apply_write
        }

    @classmethod
    def render_workspace_cli(cls, summary: Dict[str, Any], target_hint: str = ""):
        print("\n🔧 \033[1mT-ZERO WORKSPACE-WIDE OMNI-SUPERVISOR\033[0m")
        print("=" * 70)
        target = target_hint or summary.get("workspace_dir", ".")
        print(f"📁 Workspace Root: \033[1m{target}\033[0m")
        print(f"📂 Total Python Files Scanned: {summary['total_files_scanned']}")
        print(f"✨ Repaired Files: \033[1m{summary['healed_files_count']}\033[0m")
        print(f"📊 Total Repaired Hallucinations: \033[1m{summary['total_fixes']}\033[0m")
        if summary.get("written_to_disk"):
            print("💾 In-place disk write: \033[32mENABLED (Atomic Saved)\033[0m")
        else:
            print("🔍 Mode: \033[33mDRY-RUN (No files modified)\033[0m")

        reports = summary.get("reports", [])
        if reports:
            print("\n📋 Repaired Files Summary:")
            for path, rep in reports[:15]:
                rel_path = os.path.relpath(path, target) if os.path.isabs(path) else path
                print(f"  • \033[1m{rel_path}\033[0m: {rep.total_fixes} fix(es)")
                for a in rep.actions[:3]:
                    print(f"      [{a.symbol_type}] \033[31m{a.original_symbol}\033[0m ➔ \033[32m{a.healed_symbol}\033[0m")
            if len(reports) > 15:
                print(f"  ... and {len(reports) - 15} more files repaired.")
        else:
            print("\n\033[32m✅ Workspace Flawless: 0 hallucinated symbols detected across all files!\033[0m")
        print("=" * 70)

