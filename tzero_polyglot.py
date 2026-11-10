# -*- coding: utf-8 -*-
"""Siber Akademi T-Zero — Universal Polyglot AST Engine.

Provides zero-dependency, deterministic structural parsing and signature extraction
for Python, TypeScript/JavaScript, Rust, Go, C/C++, Java/C#, and Solidity.
Prunes function/method bodies, loops, and implementation details down to signatures,
interfaces, structs, and declarations with up to 95% context token reduction.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: MIT
"""

import ast
import re
from typing import Any, Callable, Dict, List, Tuple, Optional


_BPE_ENCODING_CACHE: Dict[str, Any] = {}


def count_bpe_tokens(text: str, model_name: str = "gpt-4o", fallback_divisor: float = 4.0) -> int:
    """Count tokens using cached local tiktoken BPE encodings with deterministic fallback."""
    if not text:
        return 0
    try:
        import tiktoken
        lower_m = (model_name or "gpt-4o").lower()
        if any(k in lower_m for k in ("gpt-4o", "o1", "o3", "o4", "gpt-5", "gemini", "deepseek")):
            enc_name = "o200k_base"
        elif any(k in lower_m for k in ("claude", "gpt-4", "gpt-3.5", "llama", "mistral", "qwen")):
            enc_name = "cl100k_base"
        else:
            enc_name = "o200k_base"
        enc = _BPE_ENCODING_CACHE.get(enc_name)
        if enc is None:
            enc = tiktoken.get_encoding(enc_name)
            _BPE_ENCODING_CACHE[enc_name] = enc
        return max(1, len(enc.encode(text, disallowed_special=())))
    except Exception:
        return max(1, int(len(text) / fallback_divisor))


class PolyglotTokenReducer:
    """Universal multi-language structural signature extractor."""

    SUPPORTED_LANGUAGES = {
        "python": [".py", ".pyw"],
        "javascript": [".js", ".jsx", ".mjs", ".cjs"],
        "typescript": [".ts", ".tsx"],
        "rust": [".rs"],
        "go": [".go"],
        "cpp": [".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hxx"],
        "java": [".java", ".cs"],
        "solidity": [".sol"],
        "ruby": [".rb", ".rake", ".gemspec"],
        "php": [".php", ".phtml"],
        "swift": [".swift"],
        "kotlin": [".kt", ".kts"],
        "dart": [".dart"],
        "scala": [".scala", ".sc"],
        "elixir": [".ex", ".exs"]
    }

    _TREE_SITTER_ADAPTERS: Dict[str, Callable[[str, str, str], str]] = {}

    @classmethod
    def has_tree_sitter(cls) -> bool:
        """Returns True if optional tree-sitter library or any custom adapter is registered."""
        if cls._TREE_SITTER_ADAPTERS:
            return True
        try:
            import importlib.util
            return importlib.util.find_spec("tree_sitter") is not None
        except Exception:
            return False

    @classmethod
    def register_tree_sitter_adapter(
        cls,
        lang: str,
        adapter: Optional[Callable[[str, str, str], str]],
    ) -> None:
        """Registers or clears an optional tree-sitter reducer adapter for a language."""
        key = (lang or "").lower()
        if adapter is None:
            cls._TREE_SITTER_ADAPTERS.pop(key, None)
        else:
            cls._TREE_SITTER_ADAPTERS[key] = adapter

    @staticmethod
    def _lexical_scan_lines(content: str) -> List[Tuple[str, int, int, int, int, bool]]:
        """Scans lines ignoring strings (' \" `) and comments (// /* */) for brace/paren counts."""
        lines = content.splitlines()
        results: List[Tuple[str, int, int, int, int, bool]] = []
        in_block_comment = False

        for line in lines:
            open_b = 0
            close_b = 0
            open_p = 0
            close_p = 0
            has_code_token = False
            quote_char: Optional[str] = None
            i = 0
            n = len(line)

            while i < n:
                ch = line[i]
                nxt = line[i + 1] if i + 1 < n else ""

                if in_block_comment:
                    if ch == "*" and nxt == "/":
                        in_block_comment = False
                        i += 2
                        continue
                    i += 1
                    continue

                if quote_char:
                    has_code_token = True
                    if ch == "\\":
                        i += 2
                        continue
                    if ch == quote_char:
                        quote_char = None
                    i += 1
                    continue

                if ch == "/" and nxt == "/":
                    break
                if ch == "/" and nxt == "*":
                    in_block_comment = True
                    i += 2
                    continue
                if ch in ('"', "'", "`"):
                    has_code_token = True
                    quote_char = ch
                    i += 1
                    continue

                if not ch.isspace():
                    has_code_token = True
                if ch == "{":
                    open_b += 1
                elif ch == "}":
                    close_b += 1
                elif ch == "(":
                    open_p += 1
                elif ch == ")":
                    close_p += 1
                i += 1

            results.append((line, open_b, close_b, open_p, close_p, not has_code_token))
        return results

    @classmethod
    def chunk_code(
        cls,
        content: str,
        filename: str = "",
        max_chunk_tokens: int = 400,
    ) -> List[str]:
        """cAST-style semantic boundary chunker splitting only along AST/block boundaries."""
        if not content or not content.strip():
            return []
        lang = cls.detect_language(filename) or ""
        blocks: List[str] = []

        if lang == "python":
            try:
                tree = ast.parse(content)
                lines = content.splitlines()
                prev_end = 0
                for node in tree.body:
                    start = max(prev_end, getattr(node, "lineno", 1) - 1)
                    end = getattr(node, "end_lineno", start + 1)
                    if start > prev_end:
                        gap = "\n".join(lines[prev_end:start]).strip()
                        if gap:
                            blocks.append(gap)
                    blocks.append("\n".join(lines[start:end]))
                    prev_end = end
                if prev_end < len(lines):
                    tail = "\n".join(lines[prev_end:]).strip()
                    if tail:
                        blocks.append(tail)
            except SyntaxError:
                blocks = []

        if not blocks:
            scanned = cls._lexical_scan_lines(content)
            cur_lines: List[str] = []
            depth = 0
            for raw_line, ob, cb, _, _, _ in scanned:
                cur_lines.append(raw_line)
                depth = max(0, depth + ob - cb)
                if depth == 0 and raw_line.strip():
                    if ob > 0 or cb > 0 or raw_line.strip().endswith(";"):
                        blocks.append("\n".join(cur_lines))
                        cur_lines = []
            if cur_lines:
                tail_blk = "\n".join(cur_lines).strip()
                if tail_blk:
                    blocks.append(tail_blk)

        if not blocks:
            return [content]

        chunks: List[str] = []
        active: List[str] = []
        active_tokens = 0
        for blk in blocks:
            blk_tok = count_bpe_tokens(blk)
            if active and active_tokens + blk_tok > max_chunk_tokens:
                chunks.append("\n\n".join(active))
                active = [blk]
                active_tokens = blk_tok
            else:
                active.append(blk)
                active_tokens += blk_tok
        if active:
            chunks.append("\n\n".join(active))
        return chunks

    @classmethod
    def detect_language(cls, filename: str) -> Optional[str]:
        """Detect language from filename extension."""
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        for lang, exts in cls.SUPPORTED_LANGUAGES.items():
            if ext in exts:
                return lang
        return None

    @staticmethod
    def _attach_light_doc_comments(content: str, reduced: str) -> str:
        """Preserves preceding doc-comments (/**, ///, #!) alongside declarations for T-2 light mode."""
        src_lines = content.splitlines()
        doc_by_decl: Dict[str, List[str]] = {}
        pending_docs: List[str] = []
        in_doc_block = False

        for line in src_lines:
            s = line.strip()
            if not s:
                if not in_doc_block:
                    pending_docs = []
                continue
            if s.startswith("/**") or s.startswith("/*"):
                pending_docs.append(line)
                if "*/" not in s[2:]:
                    in_doc_block = True
                continue
            if in_doc_block:
                pending_docs.append(line)
                if "*/" in s:
                    in_doc_block = False
                continue
            if s.startswith("///") or s.startswith("//!"):
                pending_docs.append(line)
                continue
            if pending_docs:
                doc_by_decl.setdefault(s, list(pending_docs))
                pending_docs = []

        if not doc_by_decl:
            return reduced

        out: List[str] = []
        for r_line in reduced.splitlines():
            r_stripped = r_line.strip()
            # Match declarations even when { ... } suffix was collapsed
            matched_docs = doc_by_decl.get(r_stripped)
            if not matched_docs:
                prefix_sig = r_stripped.split("{", 1)[0].strip()
                if prefix_sig:
                    for decl_k, d_lines in doc_by_decl.items():
                        if decl_k.startswith(prefix_sig):
                            matched_docs = d_lines
                            break
            if matched_docs:
                out.extend(matched_docs)
            out.append(r_line)
        return "\n".join(out)

    @classmethod
    def reduce_code(cls, content: str, filename: str = "", mode: str = "ultra") -> str:
        """Prunes code content to its structural signatures based on detected language."""
        lang = cls.detect_language(filename)
        if not lang or mode == "none":
            return content

        adapter = cls._TREE_SITTER_ADAPTERS.get(lang)
        if adapter is not None:
            try:
                return adapter(content, filename, mode)
            except Exception:
                pass

        norm_mode = "light" if str(mode).lower() in ("light", "balanced") else "ultra"

        dispatch = {
            "python": cls.reduce_python,
            "javascript": cls.reduce_javascript,
            "typescript": cls.reduce_javascript,
            "rust": cls.reduce_rust,
            "go": cls.reduce_go,
            "cpp": cls.reduce_cpp,
            "java": cls.reduce_java,
            "solidity": cls.reduce_solidity,
            "ruby": cls.reduce_ruby,
            "php": cls.reduce_php,
            "swift": cls.reduce_swift,
            "kotlin": cls.reduce_kotlin,
            "dart": cls.reduce_dart,
            "scala": cls.reduce_scala,
            "elixir": cls.reduce_elixir,
        }
        reducer = dispatch.get(lang)
        if not reducer:
            return content
        reduced = reducer(content, norm_mode)
        if norm_mode == "light" and lang != "python":
            return cls._attach_light_doc_comments(content, reduced)
        return reduced

    @staticmethod
    def reduce_python(content: str, mode: str = "ultra") -> str:
        """Reduces Python source via ast.parse (multiline-safe) with line fallback on SyntaxError."""
        lines = content.splitlines()
        keep_docstrings = mode == "light"
        try:
            tree = ast.parse(content)
            pruned: List[str] = []

            def _emit_func(fn_node: ast.AST, indent_prefix: str = "") -> None:
                for dec in getattr(fn_node, "decorator_list", []):
                    d_end = getattr(dec, "end_lineno", dec.lineno)
                    for ln in range(dec.lineno, d_end + 1):
                        pruned.append(lines[ln - 1])
                body = getattr(fn_node, "body", [])
                sig_start = fn_node.lineno
                if body:
                    first_stmt = body[0]
                    if first_stmt.lineno == sig_start:
                        hdr = lines[sig_start - 1].split(":", 1)[0]
                        pruned.append(f"{hdr}: ...")
                        return
                    sig_end = max(sig_start, first_stmt.lineno - 1)
                    while sig_end > sig_start and not lines[sig_end - 1].strip():
                        sig_end -= 1
                else:
                    sig_end = getattr(fn_node, "end_lineno", sig_start)
                for ln in range(sig_start, sig_end):
                    pruned.append(lines[ln - 1])
                last_hdr = lines[sig_end - 1].rstrip()
                if not last_hdr.endswith("..."):
                    pruned.append(f"{last_hdr} ..." if last_hdr.endswith(":") else f"{last_hdr}: ...")
                if keep_docstrings and body:
                    doc = ast.get_docstring(fn_node)
                    if doc:
                        pruned.append(f'{indent_prefix}    """{doc.splitlines()[0]}"""')

            for node in tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    end_l = getattr(node, "end_lineno", node.lineno)
                    for ln in range(node.lineno, end_l + 1):
                        pruned.append(lines[ln - 1])
                elif (
                    keep_docstrings
                    and isinstance(node, ast.Expr)
                    and isinstance(getattr(node, "value", None), ast.Constant)
                    and isinstance(node.value.value, str)
                ):
                    end_l = getattr(node, "end_lineno", node.lineno)
                    for ln in range(node.lineno, end_l + 1):
                        pruned.append(lines[ln - 1])
                elif isinstance(node, ast.ClassDef):
                    for dec in node.decorator_list:
                        d_end = getattr(dec, "end_lineno", dec.lineno)
                        for ln in range(dec.lineno, d_end + 1):
                            pruned.append(lines[ln - 1])
                    if node.body and node.body[0].lineno == node.lineno:
                        pruned.append(lines[node.lineno - 1].split(":", 1)[0] + ":")
                    else:
                        cls_end_hdr = max(node.lineno, (node.body[0].lineno - 1) if node.body else node.lineno)
                        while cls_end_hdr > node.lineno and not lines[cls_end_hdr - 1].strip():
                            cls_end_hdr -= 1
                        for ln in range(node.lineno, cls_end_hdr + 1):
                            pruned.append(lines[ln - 1])
                    if keep_docstrings:
                        cdoc = ast.get_docstring(node)
                        if cdoc:
                            pruned.append(f'    """{cdoc.splitlines()[0]}"""')
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            _emit_func(item, indent_prefix="    ")
                        elif isinstance(item, ast.AnnAssign) and hasattr(ast, "unparse"):
                            pruned.append(f"    {ast.unparse(item)}")
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    _emit_func(node, indent_prefix="")
            return "\n".join(pruned) if pruned else content
        except SyntaxError:
            pruned_fallback: List[str] = []
            for line in lines:
                stripped = line.strip()
                if (stripped.startswith("import ") or stripped.startswith("from ") or
                    stripped.startswith("def ") or stripped.startswith("async def ") or
                    stripped.startswith("class ") or stripped.startswith("@")):
                    if (stripped.startswith("def ") or stripped.startswith("async def ")) and not stripped.endswith("..."):
                        if stripped.endswith(":"):
                            pruned_fallback.append(f"{line[:-1]}: ...")
                        else:
                            pruned_fallback.append(f"{line} ...")
                    else:
                        pruned_fallback.append(line)
            return "\n".join(pruned_fallback) if pruned_fallback else content

    @staticmethod
    def reduce_javascript(content: str, mode: str = "ultra") -> str:
        """Reduces JavaScript/TypeScript source with string/comment-aware brace & multiline signature tracking."""
        scanned = PolyglotTokenReducer._lexical_scan_lines(content)
        pruned: List[str] = []
        in_multiline_import = False
        keep_block_until_depth: Optional[int] = None
        skip_body_until_depth: Optional[int] = None
        pending_sig: List[str] = []
        pending_paren = 0
        brace_depth = 0

        ctrl_re = re.compile(r'^(?:else\s+)?(?:if|for|while|switch|catch|try|finally|return|throw|break|continue)\b')
        iface_re = re.compile(r'^(?:export\s+)?(?:declare\s+)?(?:interface|type|enum)\s+[A-Za-z0-9_]+')
        class_re = re.compile(r'^(?:export\s+)?(?:abstract\s+)?(?:default\s+)?class\s+[A-Za-z0-9_]+')
        func_re = re.compile(
            r'^(?:export\s+(?:default\s+)?)?(?:async\s+)?function\b'
            r'|^(?:export\s+)?(?:const|let|var)\s+[A-Za-z0-9_$]+\s*(?::[^=]+)?=\s*(?:async\s+)?(?:\([^)]*\)|[A-Za-z0-9_$]+)\s*=>'
            r'|^(?:(?:public|private|protected|static|async|get|set|override|readonly)\s+)*(?:constructor|[A-Za-z0-9_$]+)\s*(?:<[^>]+>)?\s*\('
        )

        for raw_line, ob, cb, op, cp, is_comment_only in scanned:
            stripped = raw_line.strip()
            if not stripped or is_comment_only:
                continue

            if in_multiline_import:
                pruned.append(raw_line)
                brace_depth = max(0, brace_depth + ob - cb)
                if "}" in stripped or ";" in stripped:
                    in_multiline_import = False
                continue

            if keep_block_until_depth is not None:
                pruned.append(raw_line)
                brace_depth = max(0, brace_depth + ob - cb)
                if brace_depth < keep_block_until_depth:
                    keep_block_until_depth = None
                continue

            if skip_body_until_depth is not None:
                brace_depth = max(0, brace_depth + ob - cb)
                if brace_depth < skip_body_until_depth:
                    skip_body_until_depth = None
                continue

            if pending_sig:
                pending_sig.append(raw_line)
                pending_paren += op - cp
                prev_depth = brace_depth
                brace_depth = max(0, brace_depth + ob - cb)
                if pending_paren <= 0 and (ob > 0 or stripped.endswith(";") or stripped.endswith(")")):
                    if ob > cb:
                        for sline in pending_sig[:-1]:
                            pruned.append(sline)
                        pruned.append(re.sub(r'\{.*$', '{ ... }', pending_sig[-1]))
                        skip_body_until_depth = prev_depth + 1
                    else:
                        pruned.extend(pending_sig)
                    pending_sig = []
                    pending_paren = 0
                continue

            prev_depth = brace_depth
            brace_depth = max(0, brace_depth + ob - cb)

            if stripped.startswith("import ") and ob > cb:
                in_multiline_import = True
                pruned.append(raw_line)
                continue

            if stripped.startswith(("import ", "require(")) or stripped.startswith("@"):
                pruned.append(raw_line)
                continue

            if iface_re.match(stripped):
                pruned.append(raw_line)
                if ob > cb:
                    keep_block_until_depth = prev_depth + 1
                continue

            if class_re.match(stripped):
                pruned.append(raw_line)
                continue

            if ctrl_re.match(stripped):
                if ob > cb:
                    skip_body_until_depth = prev_depth + 1
                continue

            is_export_const_or_decl = stripped.startswith(("export ", "declare "))
            if func_re.match(stripped) or is_export_const_or_decl:
                if op > cp and ob == 0:
                    pending_sig = [raw_line]
                    pending_paren = op - cp
                    continue
                if ob > cb:
                    pruned.append(re.sub(r'\{.*$', '{ ... }', raw_line))
                    skip_body_until_depth = prev_depth + 1
                elif stripped.endswith("{"):
                    pruned.append(f"{raw_line[:-1]}{{ ... }}")
                    skip_body_until_depth = prev_depth + 1
                else:
                    pruned.append(raw_line)

        return "\n".join(pruned) if pruned else content

    @staticmethod
    def reduce_rust(content: str, mode: str = "ultra") -> str:
        """Reduces Rust source code to use statements, traits, structs, enums, impls, and fn signatures."""
        lines = content.splitlines()
        pruned: List[str] = []
        for line in lines:
            stripped = line.strip()
            is_fn = bool(re.match(r'^(pub(\([^)]+\))?\s+)?(async\s+)?(unsafe\s+)?fn\s+', stripped))
            is_impl = bool(re.match(r'^impl\b', stripped))
            if (stripped.startswith("use ") or stripped.startswith("pub use ") or
                is_fn or is_impl or
                stripped.startswith("pub struct ") or stripped.startswith("struct ") or
                stripped.startswith("pub enum ") or stripped.startswith("enum ") or
                stripped.startswith("pub trait ") or stripped.startswith("trait ") or
                stripped.startswith("#[") or
                stripped.startswith("pub const ") or stripped.startswith("pub type ") or
                stripped.startswith("const ") or stripped.startswith("type ")):
                if "{" in stripped and not stripped.endswith("}"):
                    pruned.append(re.sub(r'\{.*$', '{ ... }', line))
                elif stripped.endswith(";"):
                    pruned.append(line)
                elif stripped.endswith("{"):
                    pruned.append(f"{line[:-1]}{{ ... }}")
                else:
                    pruned.append(line)
        return "\n".join(pruned) if pruned else content

    @staticmethod
    def reduce_go(content: str, mode: str = "ultra") -> str:
        """Reduces Go source code to package, imports, types, interfaces, and func signatures."""
        lines = content.splitlines()
        pruned: List[str] = []
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith("package ") or stripped.startswith("import ") or
                stripped.startswith("type ") or stripped.startswith("func ") or
                stripped.startswith("var ") or stripped.startswith("const ")):
                if stripped.startswith("func ") and "{" in stripped:
                    pruned.append(re.sub(r'\{.*$', '{ ... }', line))
                else:
                    pruned.append(line)
        return "\n".join(pruned) if pruned else content

    @staticmethod
    def reduce_cpp(content: str, mode: str = "ultra") -> str:
        """Reduces C/C++ source code to headers, classes, structs, templates, and prototypes."""
        scanned = PolyglotTokenReducer._lexical_scan_lines(content)
        pruned: List[str] = []
        brace_depth = 0
        skip_body_until_depth: Optional[int] = None
        fn_re = re.compile(
            r'^(?:(?:virtual|static|inline|explicit|constexpr)\s+)?'
            r'(?:[\w:<>&*\s]+\s+)?~?[\w:]+\s*\([^;]*\)\s*(?:const)?\s*(?:override|noexcept|final)?\s*(?:\{|;)?$'
        )
        ctrl_re = re.compile(r'^(?:if|for|while|switch|catch|return|else)\b')

        for raw_line, ob, cb, _, _, is_comment_only in scanned:
            stripped = raw_line.strip()
            if not stripped or is_comment_only:
                continue

            if skip_body_until_depth is not None:
                brace_depth = max(0, brace_depth + ob - cb)
                if brace_depth < skip_body_until_depth:
                    skip_body_until_depth = None
                continue

            prev_depth = brace_depth
            brace_depth = max(0, brace_depth + ob - cb)
            if ctrl_re.match(stripped):
                if ob > cb:
                    skip_body_until_depth = prev_depth + 1
                continue

            is_container = stripped.startswith((
                "#include", "#define", "template", "class ", "struct ", "namespace ", "using ", "typedef "
            ))
            is_fn = bool(fn_re.match(stripped))
            if is_container or is_fn:
                if "{" in stripped:
                    pruned.append(re.sub(r'\{.*$', '{ ... }', raw_line))
                    if is_fn and ob > cb:
                        skip_body_until_depth = prev_depth + 1
                elif not stripped.endswith(";") and not stripped.startswith("#") and not stripped.startswith("namespace"):
                    pruned.append(f"{raw_line};")
                else:
                    pruned.append(raw_line)
        return "\n".join(pruned) if pruned else content

    @staticmethod
    def reduce_java(content: str, mode: str = "ultra") -> str:
        """Reduces Java/C# source code to packages, imports, classes, interfaces, records, and method signatures."""
        lines = content.splitlines()
        pruned: List[str] = []
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith("package ") or stripped.startswith("import ") or
                stripped.startswith("using ") or stripped.startswith("namespace ") or
                "class " in stripped or "interface " in stripped or "record " in stripped or
                "enum " in stripped or re.match(r'^\s*(?:public|private|protected|static|final|abstract|async)\s+.*\(.*\)', stripped)):
                if "{" in stripped:
                    pruned.append(re.sub(r'\{.*$', '{ ... }', line))
                elif not stripped.endswith(";") and not stripped.startswith("package") and not stripped.startswith("import"):
                    pruned.append(f"{line} {{ ... }}")
                else:
                    pruned.append(line)
        return "\n".join(pruned) if pruned else content

    @staticmethod
    def reduce_solidity(content: str, mode: str = "ultra") -> str:
        """Reduces Solidity smart contracts to pragma, interfaces, contracts, structs, events, and function headers."""
        lines = content.splitlines()
        pruned: List[str] = []
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith("pragma ") or stripped.startswith("import ") or
                stripped.startswith("contract ") or stripped.startswith("interface ") or
                stripped.startswith("library ") or stripped.startswith("struct ") or
                stripped.startswith("event ") or stripped.startswith("modifier ") or
                stripped.startswith("function ") or stripped.startswith("mapping(")):
                if "{" in stripped and not stripped.endswith("}"):
                    pruned.append(re.sub(r'\{.*$', '{ ... }', line))
                elif stripped.startswith("function ") and not stripped.endswith(";"):
                    pruned.append(f"{line};")
                else:
                    pruned.append(line)
        return "\n".join(pruned) if pruned else content

    @staticmethod
    def reduce_ruby(content: str, mode: str = "ultra") -> str:
        """Reduces Ruby source code to module/class declarations, requires, mixins, and method signatures."""
        lines = content.splitlines()
        pruned: List[str] = []
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith("require ") or stripped.startswith("require_relative ") or
                stripped.startswith("module ") or stripped.startswith("class ") or
                stripped.startswith("def ") or stripped.startswith("attr_") or
                stripped.startswith("include ") or stripped.startswith("extend ") or
                stripped.startswith("has_many ") or stripped.startswith("belongs_to ") or
                stripped in ("private", "protected", "public")):
                if stripped.startswith("def ") and not stripped.endswith("end"):
                    pruned.append(f"{line}; ...; end")
                else:
                    pruned.append(line)
        return "\n".join(pruned) if pruned else content

    @staticmethod
    def reduce_php(content: str, mode: str = "ultra") -> str:
        """Reduces PHP source code to namespace, imports, classes, interfaces, traits, and method signatures."""
        lines = content.splitlines()
        pruned: List[str] = []
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith("<?php") or stripped.startswith("namespace ") or
                stripped.startswith("use ") or "class " in stripped or
                "interface " in stripped or "trait " in stripped or "enum " in stripped or
                "function " in stripped):
                if "{" in stripped:
                    pruned.append(re.sub(r'\{.*$', '{ ... }', line))
                elif "function " in stripped and not stripped.endswith(";"):
                    pruned.append(f"{line} {{ ... }}")
                else:
                    pruned.append(line)
        return "\n".join(pruned) if pruned else content

    @staticmethod
    def reduce_swift(content: str, mode: str = "ultra") -> str:
        """Reduces Swift source code to imports, protocols, classes, structs, enums, extensions, and func signatures."""
        lines = content.splitlines()
        pruned: List[str] = []
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith("import ") or stripped.startswith("protocol ") or
                "class " in stripped or "struct " in stripped or "enum " in stripped or
                "extension " in stripped or "func " in stripped or stripped.startswith("init(")):
                if "{" in stripped:
                    pruned.append(re.sub(r'\{.*$', '{ ... }', line))
                elif not stripped.endswith(";"):
                    pruned.append(f"{line} {{ ... }}")
                else:
                    pruned.append(line)
        return "\n".join(pruned) if pruned else content

    @staticmethod
    def reduce_kotlin(content: str, mode: str = "ultra") -> str:
        """Reduces Kotlin source code to package, imports, classes, interfaces, objects, and function headers."""
        lines = content.splitlines()
        pruned: List[str] = []
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith("package ") or stripped.startswith("import ") or
                "class " in stripped or "interface " in stripped or "object " in stripped or
                stripped.startswith("fun ") or " fun " in stripped):
                if "{" in stripped:
                    pruned.append(re.sub(r'\{.*$', '{ ... }', line))
                elif not stripped.endswith(";"):
                    pruned.append(f"{line} {{ ... }}")
                else:
                    pruned.append(line)
        return "\n".join(pruned) if pruned else content

    @staticmethod
    def reduce_dart(content: str, mode: str = "ultra") -> str:
        """Reduces Dart source code to imports, exports, classes, mixins, enums, and method signatures."""
        lines = content.splitlines()
        pruned: List[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("//") or stripped.startswith("/*"):
                continue
            if stripped.startswith(("return ", "return;", "if ", "if(", "for ", "for(", "while ", "while(", "switch ", "throw ", "print(")):
                continue
            if (stripped.startswith("import ") or stripped.startswith("export ") or
                stripped.startswith("part ") or "class " in stripped or
                "mixin " in stripped or "enum " in stripped or "extension " in stripped or
                re.match(r'^\s*(?:@\w+\s+)*(?:static\s+|async\s+)?[\w<>,]+\s+\w+\s*\(.*?\)', stripped)):
                if "{" in stripped and not ("class " in stripped or "mixin " in stripped):
                    pruned.append(re.sub(r'\{.*$', '{ ... }', line))
                elif not stripped.endswith(";") and not stripped.endswith("{"):
                    pruned.append(f"{line} {{ ... }}")
                else:
                    pruned.append(line)
        return "\n".join(pruned) if pruned else content

    @staticmethod
    def reduce_scala(content: str, mode: str = "ultra") -> str:
        """Reduces Scala source code to packages, imports, traits, objects, classes, and def headers."""
        lines = content.splitlines()
        pruned: List[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("//") or stripped.startswith("/*"):
                continue
            if (stripped.startswith("package ") or stripped.startswith("import ") or
                "class " in stripped or "trait " in stripped or "object " in stripped or
                "enum " in stripped or stripped.startswith("def ") or " def " in stripped):
                if "{" in stripped and not ("class " in stripped or "trait " in stripped or "object " in stripped):
                    pruned.append(re.sub(r'\{.*$', '{ ... }', line))
                elif not stripped.endswith(";") and not stripped.endswith("{"):
                    pruned.append(f"{line} {{ ... }}")
                else:
                    pruned.append(line)
        return "\n".join(pruned) if pruned else content

    @staticmethod
    def reduce_elixir(content: str, mode: str = "ultra") -> str:
        """Reduces Elixir source code to module headers, structs, specs, and function signatures."""
        lines = content.splitlines()
        pruned: List[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if (stripped.startswith("defmodule ") or stripped.startswith("defstruct ") or
                stripped.startswith("alias ") or stripped.startswith("import ") or
                stripped.startswith("require ") or stripped.startswith("use ") or
                stripped.startswith("@type ") or stripped.startswith("@spec ") or
                stripped.startswith("def ") or stripped.startswith("defp ") or
                stripped.startswith("defmacro ")):
                if stripped.startswith("defmodule "):
                    pruned.append(line)
                elif ", do:" in stripped:
                    pruned.append(re.sub(r', do:.*$', ', do: ...', line))
                elif stripped.endswith(" do"):
                    pruned.append(re.sub(r'\s+do$', ', do: ...', line))
                else:
                    pruned.append(line)
        return "\n".join(pruned) if pruned else content


