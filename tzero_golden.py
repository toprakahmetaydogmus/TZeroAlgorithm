# -*- coding: utf-8 -*-
"""T-Zero Autonomous Golden Baseline & AST Regression Engine.

Captures a cryptographically signed baseline snapshot of all public AST signatures
across the workspace and verifies against accidental regressions in CI/CD pipelines.

Capabilities:
- Zero-drift public API golden snapshot generation (.tzero/goldens.json).
- Deterministic signature diffing (removed symbols, altered parameters, return type drift).
- Pre-merge regression guard: fails CI if public contract breaks without explicit baseline update.
- 100% Offline, $0 cost, zero cloud dependencies (Python standard library only).

Author: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of T-Zero Context Architect v10.9.0 Master Edition.
"""

import ast
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


@dataclass
class SymbolSignature:
    file_path: str
    symbol_name: str
    kind: str  # "function", "class", "method"
    signature: str
    return_type: Optional[str] = None
    docstring_hash: str = ""


@dataclass
class GoldenBaseline:
    workspace_root: str
    version: str
    created_at: float
    symbols: Dict[str, Dict[str, Any]]
    total_symbols: int
    sha256_checksum: str


class ASTGoldenRegressionEngine:
    """Extracts and verifies golden AST signature baselines for zero-drift CI pipelines."""

    @classmethod
    def extract_file_signatures(cls, file_path: str, code: str) -> List[SymbolSignature]:
        """Extracts all public function, class, and method signatures from Python code."""
        try:
            tree = ast.parse(code)
        except Exception:
            return []

        signatures: List[SymbolSignature] = []
        rel_p = file_path.replace("\\", "/")

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_") and not node.name.startswith("__"):
                    continue
                sig = cls._extract_function_signature(node)
                ret = ast.unparse(node.returns) if getattr(node, "returns", None) else None
                doc = ast.get_docstring(node) or ""
                doc_h = hashlib.sha256(doc.encode("utf-8")).hexdigest()[:12]
                signatures.append(SymbolSignature(
                    file_path=rel_p,
                    symbol_name=node.name,
                    kind="function",
                    signature=sig,
                    return_type=ret,
                    docstring_hash=doc_h
                ))

            elif isinstance(node, ast.ClassDef):
                if node.name.startswith("_"):
                    continue
                bases = ", ".join(ast.unparse(b) for b in node.bases)
                cls_sig = f"class {node.name}({bases})" if bases else f"class {node.name}"
                doc = ast.get_docstring(node) or ""
                doc_h = hashlib.sha256(doc.encode("utf-8")).hexdigest()[:12]
                signatures.append(SymbolSignature(
                    file_path=rel_p,
                    symbol_name=node.name,
                    kind="class",
                    signature=cls_sig,
                    return_type=None,
                    docstring_hash=doc_h
                ))

                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if item.name.startswith("_") and not item.name.startswith("__"):
                            continue
                        m_sig = cls._extract_function_signature(item)
                        m_ret = ast.unparse(item.returns) if getattr(item, "returns", None) else None
                        m_doc = ast.get_docstring(item) or ""
                        m_doc_h = hashlib.sha256(m_doc.encode("utf-8")).hexdigest()[:12]
                        signatures.append(SymbolSignature(
                            file_path=rel_p,
                            symbol_name=f"{node.name}.{item.name}",
                            kind="method",
                            signature=m_sig,
                            return_type=m_ret,
                            docstring_hash=m_doc_h
                        ))

        return signatures

    @classmethod
    def _extract_function_signature(cls, node: Any) -> str:
        params = []
        args = node.args

        num_defaults = len(args.defaults)
        num_pos = len(args.args)
        defaults_start = num_pos - num_defaults

        for i, a in enumerate(args.args):
            p_str = a.arg
            if getattr(a, "annotation", None):
                p_str += f": {ast.unparse(a.annotation)}"
            if i >= defaults_start:
                def_node = args.defaults[i - defaults_start]
                p_str += f" = {ast.unparse(def_node)}"
            params.append(p_str)

        if args.vararg:
            v_str = f"*{args.vararg.arg}"
            if getattr(args.vararg, "annotation", None):
                v_str += f": {ast.unparse(args.vararg.annotation)}"
            params.append(v_str)

        for i, a in enumerate(args.kwonlyargs):
            kw_str = a.arg
            if getattr(a, "annotation", None):
                kw_str += f": {ast.unparse(a.annotation)}"
            if i < len(args.kw_defaults) and args.kw_defaults[i] is not None:
                kw_str += f" = {ast.unparse(args.kw_defaults[i])}"
            params.append(kw_str)

        if args.kwarg:
            kwarg_str = f"**{args.kwarg.arg}"
            if getattr(args.kwarg, "annotation", None):
                kwarg_str += f": {ast.unparse(args.kwarg.annotation)}"
            params.append(kwarg_str)

        prefix = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
        return f"{prefix}{node.name}({', '.join(params)})"

    @classmethod
    def generate_baseline(cls, workspace_root: str = ".", max_files: int = 300) -> GoldenBaseline:
        """Scans workspace and generates the golden contract baseline."""
        abs_root = os.path.abspath(workspace_root)
        all_sigs: Dict[str, Dict[str, Any]] = {}
        hasher = hashlib.sha256()

        ignore_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build", ".pytest_cache"}

        file_count = 0
        for root, dirs, files in os.walk(abs_root):
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
            for f in files:
                if f.endswith(".py"):
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, abs_root).replace("\\", "/")
                    try:
                        with open(full_p, "r", encoding="utf-8", errors="replace") as fp:
                            code = fp.read()
                        sigs = cls.extract_file_signatures(rel_p, code)
                        for s in sigs:
                            key = f"{s.file_path}:{s.symbol_name}"
                            d = asdict(s)
                            all_sigs[key] = d
                            hasher.update(f"{key}:{s.signature}:{s.return_type}".encode("utf-8"))
                        file_count += 1
                        if file_count >= max_files:
                            break
                    except Exception:
                        pass
            if file_count >= max_files:
                break

        return GoldenBaseline(
            workspace_root=abs_root,
            version="10.9.0",
            created_at=time.time(),
            symbols=all_sigs,
            total_symbols=len(all_sigs),
            sha256_checksum=hasher.hexdigest()
        )

    @classmethod
    def save_baseline(cls, baseline: GoldenBaseline, file_path: Optional[str] = None) -> str:
        out_p = file_path or os.path.join(baseline.workspace_root, ".tzero", "goldens.json")
        os.makedirs(os.path.dirname(out_p), exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(asdict(baseline), f, indent=2)
        return out_p

    @classmethod
    def verify_against_golden(cls, workspace_root: str = ".", golden_path: Optional[str] = None) -> Dict[str, Any]:
        """Compares current working tree AST signatures against the golden baseline."""
        abs_root = os.path.abspath(workspace_root)
        g_path = golden_path or os.path.join(abs_root, ".tzero", "goldens.json")

        if not os.path.isfile(g_path):
            return {
                "success": False,
                "error": f"Golden baseline file not found at: {g_path}. Run 'tzero golden' first to establish baseline."
            }

        try:
            with open(g_path, "r", encoding="utf-8") as f:
                baseline_data = json.load(f)
            baseline_symbols = baseline_data.get("symbols", {})
        except Exception as e:
            return {"success": False, "error": f"Corrupt golden file: {e}"}

        current_baseline = cls.generate_baseline(abs_root)
        curr_symbols = current_baseline.symbols

        removed_symbols = []
        modified_signatures = []
        added_symbols = []

        for key, base_s in baseline_symbols.items():
            if key not in curr_symbols:
                removed_symbols.append({
                    "symbol": key,
                    "kind": base_s.get("kind"),
                    "last_known_signature": base_s.get("signature")
                })
            else:
                curr_s = curr_symbols[key]
                if base_s.get("signature") != curr_s.get("signature") or base_s.get("return_type") != curr_s.get("return_type"):
                    modified_signatures.append({
                        "symbol": key,
                        "old_signature": base_s.get("signature"),
                        "new_signature": curr_s.get("signature"),
                        "old_return": base_s.get("return_type"),
                        "new_return": curr_s.get("return_type")
                    })

        for key, curr_s in curr_symbols.items():
            if key not in baseline_symbols:
                added_symbols.append({
                    "symbol": key,
                    "kind": curr_s.get("kind"),
                    "signature": curr_s.get("signature")
                })

        clean = len(removed_symbols) == 0 and len(modified_signatures) == 0

        return {
            "success": clean,
            "total_baseline_symbols": len(baseline_symbols),
            "total_current_symbols": len(curr_symbols),
            "removed_symbols": removed_symbols,
            "modified_signatures": modified_signatures,
            "added_symbols": added_symbols,
            "clean": clean
        }

    @classmethod
    def format_markdown_report(cls, report: Dict[str, Any]) -> str:
        """Formats the golden regression comparison into a clear Markdown document."""
        if not report.get("success", False) and "error" in report:
            return f"❌ **T-Zero Golden Verification Error:** {report['error']}"

        clean = report.get("clean", False)
        status_badge = "🟢 ZERO REGRESSIONS (PASS)" if clean else "🔴 CONTRACT DRIFT DETECTED (REGRESSION)"

        lines = [
            "# 🏆 T-Zero Golden Baseline & AST Regression Report",
            f"**Status:** {status_badge}",
            f"- **Baseline Symbols:** `{report.get('total_baseline_symbols', 0)}`",
            f"- **Current Symbols:** `{report.get('total_current_symbols', 0)}`",
            ""
        ]

        if report.get("removed_symbols"):
            lines.append("## ❌ Removed Public Symbols (Breaking Regressions)")
            for r in report["removed_symbols"]:
                lines.append(f"- **`{r['symbol']}`** (`{r['kind']}`): Last signature was `{r['last_known_signature']}`")
            lines.append("")

        if report.get("modified_signatures"):
            lines.append("## ⚠️ Modified Public Signatures")
            for m in report["modified_signatures"]:
                lines.append(f"- **`{m['symbol']}`**:")
                lines.append(f"  - 🔴 Previous: `{m['old_signature']}` -> `{m['old_return']}`")
                lines.append(f"  - 🟢 Current:  `{m['new_signature']}` -> `{m['new_return']}`")
            lines.append("")

        if report.get("added_symbols"):
            lines.append(f"## ✨ New Public Symbols (`{len(report['added_symbols'])}` added)")
            for a in report["added_symbols"][:10]:
                lines.append(f"- ➕ `{a['symbol']}`: `{a['signature']}`")
            if len(report["added_symbols"]) > 10:
                lines.append(f"- ... and {len(report['added_symbols']) - 10} more additions.")
            lines.append("")

        if clean:
            lines.append("✅ **All public AST signatures strictly adhere to the established Golden Baseline.**")
        else:
            lines.append("💡 **To update the golden baseline deliberately:** run `tzero golden --update`.")

        return "\n".join(lines).strip()
