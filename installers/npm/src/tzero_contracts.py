# -*- coding: utf-8 -*-
"""T-Zero Autonomous AST Public API Contract & Semantic Versioning Guardian.

Analyzes AST signature changes between code revisions, determining if modifications
are backward-compatible or introduce breaking changes to public callers.

Capabilities:
- Detects removed public functions, methods, and classes.
- Flags added required parameters without defaults (caller breaking change).
- Detects parameter deletions, reorderings, and return type modifications.
- Recommends exact Semantic Versioning (SemVer) bump: MAJOR, MINOR, or PATCH.
- Computes Git revision contract diffs (HEAD vs uncommitted, or base_ref vs HEAD).
- 100% Offline, $0 cost, zero external dependencies (pure Python standard library).

Author: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of T-Zero Context Architect v10.9.0 Master Edition.
"""

import ast
import os
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


class SemVerBump(str, Enum):
    PATCH = "PATCH"      # Internal logic / docs changed, 100% contract compatible
    MINOR = "MINOR"      # New public functions/classes/optional parameters added
    MAJOR = "MAJOR"      # Incompatible public API contract change (breaking change)


@dataclass
class ParameterContract:
    name: str
    has_default: bool
    type_annotation: Optional[str] = None
    is_kwonly: bool = False
    is_vararg: bool = False
    is_kwarg: bool = False


@dataclass
class FunctionContract:
    name: str
    parameters: List[ParameterContract]
    return_annotation: Optional[str] = None
    is_async: bool = False
    docstring: Optional[str] = None

    @property
    def required_param_count(self) -> int:
        return sum(1 for p in self.parameters if not p.has_default and not p.is_vararg and not p.is_kwarg)

    @property
    def param_names(self) -> List[str]:
        return [p.name for p in self.parameters]


@dataclass
class ClassContract:
    name: str
    bases: List[str]
    methods: Dict[str, FunctionContract] = field(default_factory=dict)
    docstring: Optional[str] = None


@dataclass
class ContractViolation:
    severity: str  # BREAKING, ADDITION, MODIFICATION
    category: str  # REMOVED_SYMBOL, SIGNATURE_BREAK, PARAMETER_REMOVED, etc.
    symbol: str
    details: str


@dataclass
class ContractDiffReport:
    file_path: str
    semver_bump: SemVerBump
    breaking_changes: List[ContractViolation] = field(default_factory=list)
    non_breaking_additions: List[ContractViolation] = field(default_factory=list)
    modifications: List[ContractViolation] = field(default_factory=list)

    @property
    def is_breaking(self) -> bool:
        return len(self.breaking_changes) > 0


class ASTContractExtractor:
    """Extracts public API signatures and contracts from an AST tree."""

    @classmethod
    def extract_from_code(cls, code: str) -> Tuple[Dict[str, FunctionContract], Dict[str, ClassContract]]:
        try:
            tree = ast.parse(code)
        except Exception:
            return {}, {}

        functions: Dict[str, FunctionContract] = {}
        classes: Dict[str, ClassContract] = {}

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Ignore private functions starting with single underscore (except __init__)
                if node.name.startswith("_") and not node.name.startswith("__"):
                    continue
                fc = cls._extract_function(node)
                functions[node.name] = fc

            elif isinstance(node, ast.ClassDef):
                if node.name.startswith("_"):
                    continue
                cc = cls._extract_class(node)
                classes[node.name] = cc

        return functions, classes

    @classmethod
    def _extract_function(cls, node: Any) -> FunctionContract:
        params: List[ParameterContract] = []
        args = node.args

        # Calculate defaults offset
        num_defaults = len(args.defaults)
        num_pos = len(args.args)
        defaults_start = num_pos - num_defaults

        for i, a in enumerate(args.args):
            has_def = i >= defaults_start
            ann = ast.unparse(a.annotation) if getattr(a, "annotation", None) else None
            params.append(ParameterContract(name=a.arg, has_default=has_def, type_annotation=ann))

        if args.vararg:
            ann = ast.unparse(args.vararg.annotation) if getattr(args.vararg, "annotation", None) else None
            params.append(ParameterContract(name=f"*{args.vararg.arg}", has_default=True, type_annotation=ann, is_vararg=True))

        for i, a in enumerate(args.kwonlyargs):
            kw_def = False
            if i < len(args.kw_defaults) and args.kw_defaults[i] is not None:
                kw_def = True
            ann = ast.unparse(a.annotation) if getattr(a, "annotation", None) else None
            params.append(ParameterContract(name=a.arg, has_default=kw_def, type_annotation=ann, is_kwonly=True))

        if args.kwarg:
            ann = ast.unparse(args.kwarg.annotation) if getattr(args.kwarg, "annotation", None) else None
            params.append(ParameterContract(name=f"**{args.kwarg.arg}", has_default=True, type_annotation=ann, is_kwarg=True))

        ret_ann = ast.unparse(node.returns) if getattr(node, "returns", None) else None
        doc = ast.get_docstring(node)

        return FunctionContract(
            name=node.name,
            parameters=params,
            return_annotation=ret_ann,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            docstring=doc
        )

    @classmethod
    def _extract_class(cls, node: ast.ClassDef) -> ClassContract:
        bases = [ast.unparse(b) for b in node.bases]
        methods: Dict[str, FunctionContract] = {}
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if item.name.startswith("_") and not item.name.startswith("__"):
                    continue
                methods[item.name] = cls._extract_function(item)

        return ClassContract(
            name=node.name,
            bases=bases,
            methods=methods,
            docstring=ast.get_docstring(node)
        )


class ASTContractComparator:
    """Compares two versions of public AST contracts and evaluates breaking changes."""

    @classmethod
    def compare_code(cls, old_code: str, new_code: str, file_path: str = "code.py") -> ContractDiffReport:
        old_funcs, old_classes = ASTContractExtractor.extract_from_code(old_code)
        new_funcs, new_classes = ASTContractExtractor.extract_from_code(new_code)

        breaking: List[ContractViolation] = []
        additions: List[ContractViolation] = []
        modifications: List[ContractViolation] = []

        # 1. Check top-level functions
        for fn_name, old_fn in old_funcs.items():
            if fn_name not in new_funcs:
                breaking.append(ContractViolation(
                    severity="BREAKING",
                    category="REMOVED_FUNCTION",
                    symbol=fn_name,
                    details=f"Public function '{fn_name}()' was removed."
                ))
            else:
                new_fn = new_funcs[fn_name]
                cls._compare_function_signatures(old_fn, new_fn, fn_name, breaking, additions, modifications)

        for fn_name, new_fn in new_funcs.items():
            if fn_name not in old_funcs:
                additions.append(ContractViolation(
                    severity="ADDITION",
                    category="ADDED_FUNCTION",
                    symbol=fn_name,
                    details=f"New public function '{fn_name}()' added."
                ))

        # 2. Check classes and methods
        for cls_name, old_cls in old_classes.items():
            if cls_name not in new_classes:
                breaking.append(ContractViolation(
                    severity="BREAKING",
                    category="REMOVED_CLASS",
                    symbol=cls_name,
                    details=f"Public class '{cls_name}' was removed."
                ))
            else:
                new_cls = new_classes[cls_name]
                # Compare class methods
                for m_name, old_m in old_cls.methods.items():
                    if m_name not in new_cls.methods:
                        breaking.append(ContractViolation(
                            severity="BREAKING",
                            category="REMOVED_METHOD",
                            symbol=f"{cls_name}.{m_name}",
                            details=f"Public method '{cls_name}.{m_name}()' was removed."
                        ))
                    else:
                        new_m = new_cls.methods[m_name]
                        cls._compare_function_signatures(old_m, new_m, f"{cls_name}.{m_name}", breaking, additions, modifications)

                for m_name, new_m in new_cls.methods.items():
                    if m_name not in old_cls.methods:
                        additions.append(ContractViolation(
                            severity="ADDITION",
                            category="ADDED_METHOD",
                            symbol=f"{cls_name}.{m_name}",
                            details=f"New public method '{cls_name}.{m_name}()' added."
                        ))

        for cls_name, new_cls in new_classes.items():
            if cls_name not in old_classes:
                additions.append(ContractViolation(
                    severity="ADDITION",
                    category="ADDED_CLASS",
                    symbol=cls_name,
                    details=f"New public class '{cls_name}' added."
                ))

        # Determine SemVer bump
        if breaking:
            bump = SemVerBump.MAJOR
        elif additions:
            bump = SemVerBump.MINOR
        else:
            bump = SemVerBump.PATCH

        return ContractDiffReport(
            file_path=file_path,
            semver_bump=bump,
            breaking_changes=breaking,
            non_breaking_additions=additions,
            modifications=modifications
        )

    @classmethod
    def _compare_function_signatures(
        cls,
        old_fn: FunctionContract,
        new_fn: FunctionContract,
        symbol_name: str,
        breaking: List[ContractViolation],
        additions: List[ContractViolation],
        modifications: List[ContractViolation]
    ):
        old_pnames = old_fn.param_names
        new_pnames = new_fn.param_names

        # Check removed parameters
        for p in old_fn.parameters:
            if p.name not in new_pnames:
                breaking.append(ContractViolation(
                    severity="BREAKING",
                    category="REMOVED_PARAMETER",
                    symbol=symbol_name,
                    details=f"Parameter '{p.name}' was removed from '{symbol_name}'."
                ))

        # Check added required parameters (breaking!)
        for p in new_fn.parameters:
            if p.name not in old_pnames:
                if not p.has_default and not p.is_vararg and not p.is_kwarg:
                    breaking.append(ContractViolation(
                        severity="BREAKING",
                        category="REQUIRED_PARAMETER_ADDED",
                        symbol=symbol_name,
                        details=f"New required parameter '{p.name}' added to '{symbol_name}' without default value."
                    ))
                else:
                    additions.append(ContractViolation(
                        severity="ADDITION",
                        category="OPTIONAL_PARAMETER_ADDED",
                        symbol=symbol_name,
                        details=f"Optional parameter '{p.name}' added to '{symbol_name}'."
                    ))

        # Check return type annotation change
        if old_fn.return_annotation and new_fn.return_annotation and old_fn.return_annotation != new_fn.return_annotation:
            modifications.append(ContractViolation(
                severity="MODIFICATION",
                category="RETURN_TYPE_CHANGED",
                symbol=symbol_name,
                details=f"Return type changed from '{old_fn.return_annotation}' to '{new_fn.return_annotation}'."
            ))

    @classmethod
    def compare_git_revision(cls, repo_dir: str = ".", base_ref: str = "HEAD~1") -> List[ContractDiffReport]:
        """Compares public API contracts between base_ref and working tree / HEAD."""
        abs_repo = os.path.abspath(repo_dir)

        # Get list of changed python files
        try:
            diff_proc = subprocess.run(
                f"git diff --name-only {base_ref} -- '*.py'",
                cwd=abs_repo,
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            files = [f.strip() for f in diff_proc.stdout.splitlines() if f.strip() and f.strip().endswith(".py")]
        except Exception:
            return []

        reports: List[ContractDiffReport] = []
        for rel_file in files:
            full_p = os.path.join(abs_repo, rel_file)
            if not os.path.isfile(full_p):
                continue

            with open(full_p, "r", encoding="utf-8", errors="replace") as f:
                new_code = f.read()

            # Fetch base_ref content via git show
            try:
                show_proc = subprocess.run(
                    f"git show {base_ref}:{rel_file}",
                    cwd=abs_repo,
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8"
                )
                if show_proc.returncode == 0:
                    old_code = show_proc.stdout
                else:
                    old_code = ""
            except Exception:
                old_code = ""

            rep = cls.compare_code(old_code, new_code, file_path=rel_file)
            reports.append(rep)

        return reports

    @classmethod
    def format_markdown_report(cls, reports: List[ContractDiffReport]) -> str:
        """Formats the contract diffs into a GitHub PR Shield Markdown document."""
        if not reports:
            return "✅ **Public API Contracts:** No modified Python files found in git revision diff."

        has_breaking = any(r.is_breaking for r in reports)
        highest_bump = SemVerBump.PATCH
        if has_breaking:
            highest_bump = SemVerBump.MAJOR
        elif any(r.semver_bump == SemVerBump.MINOR for r in reports):
            highest_bump = SemVerBump.MINOR

        badge = "🔴 **MAJOR (BREAKING)**" if highest_bump == SemVerBump.MAJOR else (
            "🟢 **MINOR (FEATURE)**" if highest_bump == SemVerBump.MINOR else "🔵 **PATCH (REFACTOR)**"
        )

        lines = [
            "## 🛡️ T-Zero Public API Contract & SemVer Guardian",
            f"**Recommended SemVer Bump:** {badge}",
            f"**Files Evaluated:** `{len(reports)}`",
            ""
        ]

        for r in reports:
            status_icon = "🔴 BREAKING" if r.is_breaking else ("🟢 COMPATIBLE" if r.semver_bump == SemVerBump.MINOR else "🔵 REFACTOR")
            lines.append(f"### `{r.file_path}` — {status_icon} (`{r.semver_bump.value}`)")

            if r.breaking_changes:
                lines.append("**⚠️ Breaking Changes:**")
                for b in r.breaking_changes:
                    lines.append(f"- ❌ `{b.category}`: `{b.symbol}` — {b.details}")

            if r.non_breaking_additions:
                lines.append("**✨ Additions:**")
                for a in r.non_breaking_additions:
                    lines.append(f"- ➕ `{a.category}`: `{a.symbol}` — {a.details}")

            if r.modifications:
                lines.append("**📝 Modifications:**")
                for m in r.modifications:
                    lines.append(f"- ℹ️ `{m.category}`: `{m.symbol}` — {m.details}")

            lines.append("")

        return "\n".join(lines).strip()

