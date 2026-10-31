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
from typing import Dict, List, Tuple, Optional


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
        "solidity": [".sol"]
    }

    @classmethod
    def detect_language(cls, filename: str) -> Optional[str]:
        """Detect language from filename extension."""
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        for lang, exts in cls.SUPPORTED_LANGUAGES.items():
            if ext in exts:
                return lang
        return None

    @classmethod
    def reduce_code(cls, content: str, filename: str = "", mode: str = "ultra") -> str:
        """Prunes code content to its structural signatures based on detected language."""
        lang = cls.detect_language(filename)
        if not lang or mode == "none":
            return content

        if lang == "python":
            return cls.reduce_python(content, mode)
        elif lang in ("javascript", "typescript"):
            return cls.reduce_javascript(content, mode)
        elif lang == "rust":
            return cls.reduce_rust(content, mode)
        elif lang == "go":
            return cls.reduce_go(content, mode)
        elif lang == "cpp":
            return cls.reduce_cpp(content, mode)
        elif lang == "java":
            return cls.reduce_java(content, mode)
        elif lang == "solidity":
            return cls.reduce_solidity(content, mode)
        return content

    @staticmethod
    def reduce_python(content: str, mode: str = "ultra") -> str:
        """Reduces Python source to imports, class/func headers, and ellipses."""
        lines = content.splitlines()
        pruned: List[str] = []
        in_docstring = False

        for line in lines:
            stripped = line.strip()
            # Handle multiline docstrings
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if stripped.count('"""') == 1 or stripped.count("'''") == 1:
                    in_docstring = not in_docstring
                continue
            if in_docstring:
                continue

            if (stripped.startswith("import ") or stripped.startswith("from ") or
                stripped.startswith("def ") or stripped.startswith("async def ") or
                stripped.startswith("class ") or stripped.startswith("@")):
                indent = len(line) - len(line.lstrip())
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
                    pruned.append(f"{line} { ... }")
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
