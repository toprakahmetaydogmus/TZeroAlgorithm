# -*- coding: utf-8 -*-
"""T-Zero Explain: Ultra-Dense AST Architectural Passport Generator.

Generates high-density, prompt-ready architectural passports for codebases and files,
delivering maximum semantic grounding to LLMs (Claude, GPT, Gemini, DeepSeek) with
up to 95% token savings compared to raw file ingestion.

Author: Toprak Ahmet Aydogmus (Siber Akademi)
Version: 10.5.0
"""

import ast
import os
import sys

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class SymbolPassport:
    name: str
    kind: str          # 'class', 'function', 'async_function'
    lineno: int
    docstring: Optional[str]
    signatures: List[str] = field(default_factory=list)
    complexity: int = 1


@dataclass
class ModulePassport:
    file_path: str
    module_name: str
    docstring: Optional[str]
    raw_lines: int
    raw_tokens: int
    passport_tokens: int
    token_savings_pct: float
    role: str          # 'presentation', 'business_service', 'data_model', 'utility'
    symbols: List[SymbolPassport] = field(default_factory=list)
    dependencies_internal: List[str] = field(default_factory=list)
    dependencies_external: List[str] = field(default_factory=list)
    markdown_passport: str = ""


class ArchitecturalPassportGenerator:
    """Extracts ultra-dense AST architecture passports for LLM prompts."""

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, int(len(text) / 3.8))

    @classmethod
    def _compute_complexity(cls, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of an AST node."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                 ast.With, ast.Assert, ast.comprehension)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    @classmethod
    def _classify_role(cls, path_str: str, symbols: List[SymbolPassport]) -> str:
        lower = path_str.lower()
        if "cli" in lower or "ui" in lower or "view" in lower or "api" in lower or "mcp" in lower:
            return "presentation"
        elif "model" in lower or "schema" in lower or "dto" in lower:
            return "data_model"
        elif "util" in lower or "helper" in lower or "common" in lower:
            return "utility"
        elif any(s.name.endswith(("Service", "Engine", "Manager", "Analyzer", "Architect", "Orchestrator")) for s in symbols):
            return "business_service"
        return "business_service"

    @classmethod
    def explain_file(cls, file_path: str) -> ModulePassport:
        """Generate high-density AST passport for a single Python file."""
        p = Path(file_path).resolve()
        if not p.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            raise IOError(f"Cannot read file {file_path}: {e}")

        raw_lines = len(content.splitlines())
        raw_tokens = cls._estimate_tokens(content)

        try:
            tree = ast.parse(content, filename=str(p))
            module_doc = ast.get_docstring(tree)
        except SyntaxError:
            module_doc = None
            tree = None

        symbols: List[SymbolPassport] = []
        internal_deps: Set[str] = set()
        external_deps: Set[str] = set()

        if tree:
            for node in tree.body:
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        base = alias.name.split(".")[0]
                        if base in sys.builtin_module_names or base in ("os", "sys", "json", "re", "math", "typing", "pathlib", "ast", "time", "shutil"):
                            external_deps.add(base)
                        else:
                            internal_deps.add(base)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        base = node.module.split(".")[0]
                        if node.level > 0 or base not in sys.builtin_module_names:
                            internal_deps.add(node.module)
                        else:
                            external_deps.add(base)

                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    fn_doc = ast.get_docstring(node)
                    # build signature
                    args_list = []
                    for a in node.args.args:
                        ann = f": {ast.unparse(a.annotation)}" if a.annotation else ""
                        args_list.append(f"{a.arg}{ann}")
                    ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
                    sig = f"def {node.name}({', '.join(args_list)}){ret}"
                    symbols.append(SymbolPassport(
                        name=node.name,
                        kind="async_function" if isinstance(node, ast.AsyncFunctionDef) else "function",
                        lineno=node.lineno,
                        docstring=fn_doc.split("\n")[0] if fn_doc else None,
                        signatures=[sig],
                        complexity=cls._compute_complexity(node)
                    ))

                elif isinstance(node, ast.ClassDef):
                    cls_doc = ast.get_docstring(node)
                    bases = [ast.unparse(b) for b in node.bases]
                    base_str = f"({', '.join(bases)})" if bases else ""
                    methods_sig = []
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            m_args = []
                            for a in item.args.args:
                                m_ann = f": {ast.unparse(a.annotation)}" if a.annotation else ""
                                m_args.append(f"{a.arg}{m_ann}")
                            m_ret = f" -> {ast.unparse(item.returns)}" if item.returns else ""
                            methods_sig.append(f"    def {item.name}({', '.join(m_args)}){m_ret}")

                    symbols.append(SymbolPassport(
                        name=node.name,
                        kind="class",
                        lineno=node.lineno,
                        docstring=cls_doc.split("\n")[0] if cls_doc else None,
                        signatures=[f"class {node.name}{base_str}:"] + methods_sig[:10],
                        complexity=cls._compute_complexity(node)
                    ))

        role = cls._classify_role(str(p), symbols)

        # Build Markdown Passport
        md_lines = [
            f"### 🏛️ AST Architectural Passport: `{p.name}`",
            f"- **Role:** `{role.upper()}` | **Lines:** {raw_lines} | **Symbols:** {len(symbols)}",
        ]
        if module_doc:
            md_lines.append(f"- **Purpose:** {module_doc.strip().splitlines()[0]}")
        if internal_deps:
            md_lines.append(f"- **Internal Dependencies:** `{', '.join(sorted(internal_deps)[:6])}`")
        if external_deps:
            md_lines.append(f"- **External Dependencies:** `{', '.join(sorted(external_deps)[:6])}`")

        md_lines.append("\n```python")
        for sym in symbols:
            doc_str = f"  # {sym.docstring}" if sym.docstring else ""
            if sym.kind == "class":
                md_lines.append(f"{sym.signatures[0]}{doc_str}")
                for ms in sym.signatures[1:]:
                    md_lines.append(ms)
            else:
                md_lines.append(f"{sym.signatures[0]}: ...{doc_str}")
        md_lines.append("```\n")

        markdown_passport = "\n".join(md_lines)
        passport_tokens = cls._estimate_tokens(markdown_passport)
        savings_pct = round(max(0.0, (1.0 - passport_tokens / max(1, raw_tokens)) * 100), 1)

        return ModulePassport(
            file_path=str(p),
            module_name=p.stem,
            docstring=module_doc,
            raw_lines=raw_lines,
            raw_tokens=raw_tokens,
            passport_tokens=passport_tokens,
            token_savings_pct=savings_pct,
            role=role,
            symbols=symbols,
            dependencies_internal=sorted(internal_deps),
            dependencies_external=sorted(external_deps),
            markdown_passport=markdown_passport
        )

    @classmethod
    def render_cli(cls, passport: ModulePassport):
        """Render passport output to stdout."""
        print("=" * 80)
        print("\033[1;36m🏛️ T-ZERO AST ARCHITECTURAL PASSPORT\033[0m")
        print("=" * 80)
        print(f"File:           \033[33m{passport.file_path}\033[0m")
        print(f"Module:         \033[32m{passport.module_name}\033[0m")
        print(f"Layer Role:     \033[1;35m{passport.role.upper()}\033[0m")
        print(f"Token Economy:  Raw: \033[31m{passport.raw_tokens:,} tokens\033[0m -> "
              f"Passport: \033[32m{passport.passport_tokens:,} tokens\033[0m "
              f"(\033[1;32m-{passport.token_savings_pct}%\033[0m reduction)")
        print("-" * 80)
        print(passport.markdown_passport)
        print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tzero_explain.py <path_to_file.py>")
        sys.exit(1)
    target = sys.argv[1]
    res = ArchitecturalPassportGenerator.explain_file(target)
    ArchitecturalPassportGenerator.render_cli(res)
