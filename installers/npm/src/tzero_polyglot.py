# -*- coding: utf-8 -*-
"""Siber Akademi T-Zero — Universal Polyglot AST Engine.

Provides zero-dependency, deterministic structural parsing and signature extraction
for Python, TypeScript/JavaScript, Rust, Go, C/C++, Java/C#, and Solidity.
Prunes function/method bodies, loops, and implementation details down to signatures,
interfaces, structs, and declarations with up to 95% context token reduction.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: MIT
"""

import re
from typing import Any, Dict, List, Tuple, Optional


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
        reduced = reducer(content, mode)
        if mode == "light" and lang != "python":
            return cls._attach_light_doc_comments(content, reduced)
        return reduced

    @staticmethod
    def reduce_python(content: str, mode: str = "ultra") -> str:
        """Reduces Python source to imports, class/func headers, and ellipses."""
        lines = content.splitlines()
        pruned: List[str] = []
        in_docstring = False
        keep_docstrings = mode == "light"

        for line in lines:
            stripped = line.strip()
            # Handle multiline docstrings
            if stripped.startswith('"""') or stripped.startswith("'''"):
                delim = '"""' if stripped.startswith('"""') else "'''"
                if stripped.count(delim) == 1:
                    in_docstring = not in_docstring
                if keep_docstrings:
                    pruned.append(line)
                continue
            if in_docstring:
                if keep_docstrings:
                    pruned.append(line)
                continue

            if (stripped.startswith("import ") or stripped.startswith("from ") or
                stripped.startswith("def ") or stripped.startswith("async def ") or
                stripped.startswith("class ") or stripped.startswith("@")):
                if (stripped.startswith("def ") or stripped.startswith("async def ")) and not stripped.endswith("..."):
                    if stripped.endswith(":"):
                        pruned.append(f"{line[:-1]}: ...")
                    else:
                        pruned.append(f"{line} ...")
                else:
                    pruned.append(line)

        return "\n".join(pruned) if pruned else content

    @staticmethod
    def reduce_javascript(content: str, mode: str = "ultra") -> str:
        """Reduces JavaScript/TypeScript source to imports, interfaces, types, and function signatures."""
        lines = content.splitlines()
        pruned: List[str] = []
        in_multiline_import = False
        in_interface_or_type = False
        in_block_comment = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Multi-line comment tracking
            if in_block_comment:
                if "*/" in stripped:
                    in_block_comment = False
                continue
            if stripped.startswith("/*") and not stripped.endswith("*/"):
                in_block_comment = True
                continue
            if stripped.startswith("//"):
                continue

            # Multi-line imports
            if in_multiline_import:
                pruned.append(line)
                if "}" in stripped or ";" in stripped:
                    in_multiline_import = False
                continue

            if stripped.startswith("import ") and "{" in stripped and "}" not in stripped:
                in_multiline_import = True
                pruned.append(line)
                continue

            # Interfaces and Type declarations (keep interface definitions and fields)
            if re.match(r"^(export\s+)?(interface|type)\s+[A-Za-z0-9_]+", stripped):
                pruned.append(line)
                if "{" in stripped and "}" not in stripped:
                    in_interface_or_type = True
                continue

            if in_interface_or_type:
                pruned.append(line)
                if "}" in stripped:
                    in_interface_or_type = False
                continue

            # Function declarations, arrow functions, classes
            if (stripped.startswith("import ") or stripped.startswith("export ") or
                stripped.startswith("class ") or stripped.startswith("function ") or
                stripped.startswith("async function ") or
                (stripped.startswith("const ") and "=>" in stripped) or
                (stripped.startswith("let ") and "=>" in stripped)):
                if "{" in stripped and "}" not in stripped:
                    pruned.append(re.sub(r'\{.*$', '{ ... }', line))
                elif stripped.endswith("{"):
                    pruned.append(f"{line[:-1]}{{ ... }}")
                else:
                    pruned.append(line)
        return "\n".join(pruned) if pruned else content

    @staticmethod
    def reduce_rust(content: str, mode: str = "ultra") -> str:
        """Reduces Rust source code to use statements, traits, structs, enums, and fn signatures."""
        lines = content.splitlines()
        pruned: List[str] = []
        for line in lines:
            stripped = line.strip()
            is_fn = bool(re.match(r'^(pub(\([^)]+\))?\s+)?(async\s+)?(unsafe\s+)?fn\s+', stripped))
            if (stripped.startswith("use ") or stripped.startswith("pub use ") or
                is_fn or
                stripped.startswith("pub struct ") or stripped.startswith("struct ") or
                stripped.startswith("pub enum ") or stripped.startswith("enum ") or
                stripped.startswith("pub trait ") or stripped.startswith("trait ") or
                stripped.startswith("impl ") or stripped.startswith("#[") or
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
        lines = content.splitlines()
        pruned: List[str] = []
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith("#include") or stripped.startswith("#define") or
                stripped.startswith("template") or stripped.startswith("class ") or
                stripped.startswith("struct ") or stripped.startswith("namespace ") or
                stripped.startswith("using ") or stripped.startswith("typedef ") or
                re.match(r'^(?:virtual\s+|static\s+|inline\s+)?[\w:<>]+\s+[\w:]+\s*\([^;]*\)\s*(?:const)?\s*\{?$', stripped)):
                if "{" in stripped:
                    pruned.append(re.sub(r'\{.*$', '{ ... }', line))
                elif not stripped.endswith(";") and not stripped.startswith("#") and not stripped.startswith("namespace"):
                    pruned.append(f"{line};")
                else:
                    pruned.append(line)
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


