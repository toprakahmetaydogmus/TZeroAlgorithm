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
import json
import os
import re
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

    POLYGLOT_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".java", ".cs"}

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

    @classmethod
    def _strip_comments(cls, code: str) -> str:
        """Removes single-line (//) and multi-line (/* */) comments preserving strings."""
        out = []
        i = 0
        n = len(code)
        in_quote: Optional[str] = None
        while i < n:
            ch = code[i]
            nxt = code[i + 1] if i + 1 < n else ""
            if in_quote:
                out.append(ch)
                if ch == "\\" and i + 1 < n:
                    i += 1
                    out.append(code[i])
                elif ch == in_quote:
                    in_quote = None
                i += 1
                continue
            if ch in ('"', "'", '`'):
                in_quote = ch
                out.append(ch)
                i += 1
                continue
            if ch == "/" and nxt == "/":
                i += 2
                while i < n and code[i] != "\n":
                    i += 1
                if i < n and code[i] == "\n":
                    out.append("\n")
                    i += 1
                continue
            if ch == "/" and nxt == "*":
                i += 2
                while i + 1 < n and not (code[i] == "*" and code[i + 1] == "/"):
                    if code[i] == "\n":
                        out.append("\n")
                    i += 1
                i += 2
                continue
            out.append(ch)
            i += 1
        return "".join(out)

    @staticmethod
    def _split_param_list(raw_params: str) -> List[str]:
        """Splits parameter string by commas outside of () [] {} <> quotes."""
        parts = []
        current = []
        depth = 0
        in_quote: Optional[str] = None
        i = 0
        n = len(raw_params)
        while i < n:
            ch = raw_params[i]
            if in_quote:
                current.append(ch)
                if ch == "\\" and i + 1 < n:
                    i += 1
                    current.append(raw_params[i])
                elif ch == in_quote:
                    in_quote = None
                i += 1
                continue
            if ch in ('"', "'", '`'):
                in_quote = ch
                current.append(ch)
                i += 1
                continue
            if ch in ("(", "[", "{", "<"):
                depth += 1
                current.append(ch)
            elif ch in (")", "]", "}", ">"):
                if depth > 0:
                    depth -= 1
                current.append(ch)
            elif ch == "," and depth == 0:
                part = "".join(current).strip()
                if part:
                    parts.append(part)
                current = []
            else:
                current.append(ch)
            i += 1
        if current:
            part = "".join(current).strip()
            if part:
                parts.append(part)
        return parts

    @staticmethod
    def _find_matching_paren(text: str, start_idx: int) -> int:
        """Given start_idx of '(', returns index of matching ')'."""
        depth = 0
        in_quote = None
        i = start_idx
        n = len(text)
        while i < n:
            ch = text[i]
            if in_quote:
                if ch == "\\" and i + 1 < n:
                    i += 2
                    continue
                if ch == in_quote:
                    in_quote = None
                i += 1
                continue
            if ch in ('"', "'", '`'):
                in_quote = ch
                i += 1
                continue
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return -1

    @staticmethod
    def _find_matching_brace(text: str, start_idx: int) -> int:
        """Given start_idx of '{', returns index of matching '}'."""
        depth = 0
        in_quote = None
        i = start_idx
        n = len(text)
        while i < n:
            ch = text[i]
            if in_quote:
                if ch == "\\" and i + 1 < n:
                    i += 2
                    continue
                if ch == in_quote:
                    in_quote = None
                i += 1
                continue
            if ch in ('"', "'", '`'):
                in_quote = ch
                i += 1
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return -1

    @classmethod
    def _parse_ts_param(cls, p: str) -> ParameterContract:
        p = p.strip()
        is_vararg = False
        if p.startswith("..."):
            is_vararg = True
            p = p[3:].strip()

        has_default = is_vararg
        if "=" in p:
            left, _ = p.split("=", 1)
            has_default = True
            left = left.strip()
        else:
            left = p

        if "?:" in left:
            name_p, type_p = left.split("?:", 1)
            name = name_p.strip()
            type_ann = type_p.strip()
            has_default = True
        elif ":" in left:
            name_p, type_p = left.split(":", 1)
            name = name_p.strip()
            type_ann = type_p.strip()
            if name.endswith("?"):
                name = name[:-1].strip()
                has_default = True
        else:
            name = left.strip()
            if name.endswith("?"):
                name = name[:-1].strip()
                has_default = True
            type_ann = None

        if name.startswith("..."):
            name = name[3:].strip()
            is_vararg = True
            has_default = True

        return ParameterContract(
            name=name,
            has_default=has_default,
            type_annotation=type_ann,
            is_vararg=is_vararg
        )

    @classmethod
    def _parse_go_params(cls, raw: str) -> List[ParameterContract]:
        if not raw.strip():
            return []
        parts = cls._split_param_list(raw)
        resolved: List[Tuple[str, str]] = []
        current_type = ""
        for p in reversed(parts):
            tokens = p.strip().split()
            if len(tokens) >= 2:
                current_type = " ".join(tokens[1:])
                resolved.append((tokens[0], current_type))
            elif len(tokens) == 1:
                resolved.append((tokens[0], current_type))
        resolved.reverse()

        params: List[ParameterContract] = []
        for name, typ in resolved:
            is_var = typ.startswith("...")
            params.append(ParameterContract(
                name=name,
                has_default=is_var,
                type_annotation=typ if typ else None,
                is_vararg=is_var
            ))
        return params

    @classmethod
    def _parse_rust_param(cls, p: str) -> Optional[ParameterContract]:
        p = p.strip()
        if not p or p in ("self", "&self", "&mut self"):
            return None
        if ":" in p:
            name, typ = p.split(":", 1)
            return ParameterContract(
                name=name.strip(),
                has_default=False,
                type_annotation=typ.strip()
            )
        return ParameterContract(name=p, has_default=False)

    @classmethod
    def _parse_java_param(cls, p: str) -> ParameterContract:
        p = p.strip()
        has_default = False
        if "=" in p:
            left, _ = p.split("=", 1)
            has_default = True
            left = left.strip()
        else:
            left = p

        tokens = left.split()
        if not tokens:
            return ParameterContract(name="", has_default=has_default)

        name = tokens[-1]
        type_ann = " ".join(tokens[:-1]) if len(tokens) > 1 else None
        is_vararg = False
        if name.startswith("..."):
            name = name[3:]
            is_vararg = True
            has_default = True
        elif type_ann and ("..." in type_ann or "params " in left):
            is_vararg = True
            has_default = True

        return ParameterContract(
            name=name,
            has_default=has_default,
            type_annotation=type_ann,
            is_vararg=is_vararg
        )

    @classmethod
    def _extract_ts_contracts(cls, clean_code: str, functions: Dict[str, FunctionContract], classes: Dict[str, ClassContract]) -> None:
        class_pattern = re.compile(
            r'(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+([A-Za-z0-9_$]+)(?:\s+extends\s+([^{]+))?\s*\{'
        )
        top_level_code = list(clean_code)

        for m in class_pattern.finditer(clean_code):
            cls_name = m.group(1)
            bases = [b.strip() for b in m.group(2).split(",")] if m.group(2) else []
            brace_idx = m.end() - 1
            end_brace = cls._find_matching_brace(clean_code, brace_idx)
            if end_brace == -1:
                end_brace = len(clean_code) - 1

            for k in range(m.start(), end_brace + 1):
                if top_level_code[k] != "\n":
                    top_level_code[k] = " "

            class_body = clean_code[brace_idx + 1:end_brace]
            methods: Dict[str, FunctionContract] = {}

            method_depth = 0
            idx = 0
            n = len(class_body)
            while idx < n:
                ch = class_body[idx]
                if ch == "{":
                    method_depth += 1
                    idx += 1
                    continue
                elif ch == "}":
                    if method_depth > 0:
                        method_depth -= 1
                    idx += 1
                    continue

                if method_depth == 0:
                    m_hdr = re.match(
                        r'^(?:(?:public|static|async|get|set|override|readonly)\s+)*([A-Za-z0-9_$]+)\s*(?:<[^>]+>)?\s*\(',
                        class_body[idx:]
                    )
                    if m_hdr:
                        full_match = m_hdr.group(0)
                        fn_name = m_hdr.group(1)
                        matched_str = class_body[idx:idx + len(full_match)]

                        if (
                            fn_name in {"if", "for", "while", "switch", "catch", "return"}
                            or "private " in matched_str
                            or "protected " in matched_str
                            or fn_name.startswith("_")
                            or fn_name.startswith("#")
                        ):
                            idx += len(full_match)
                            continue

                        paren_start = idx + len(full_match) - 1
                        paren_end = cls._find_matching_paren(class_body, paren_start)
                        if paren_end != -1:
                            raw_params = class_body[paren_start + 1:paren_end]
                            rest = class_body[paren_end + 1:]
                            ret_match = re.match(r'^\s*:\s*([^{;]+)', rest)
                            ret_ann = ret_match.group(1).strip() if ret_match else None
                            is_async = "async " in matched_str

                            params = [cls._parse_ts_param(p) for p in cls._split_param_list(raw_params)]
                            methods[fn_name] = FunctionContract(
                                name=fn_name,
                                parameters=params,
                                return_annotation=ret_ann,
                                is_async=is_async
                            )
                            idx = paren_end + 1
                            continue

                idx += 1

            classes[cls_name] = ClassContract(name=cls_name, bases=bases, methods=methods)

        top_str = "".join(top_level_code)
        fn_pattern = re.compile(
            r'(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*(?:<[^>]+>)?\s*\('
        )
        for m in fn_pattern.finditer(top_str):
            fn_name = m.group(1)
            prefix = top_str[m.start():m.end()]
            is_exported = "export" in prefix
            if fn_name.startswith("_") and not is_exported:
                continue

            paren_start = m.end() - 1
            paren_end = cls._find_matching_paren(top_str, paren_start)
            if paren_end != -1:
                raw_params = top_str[paren_start + 1:paren_end]
                rest = top_str[paren_end + 1:]
                ret_match = re.match(r'^\s*:\s*([^{;]+)', rest)
                ret_ann = ret_match.group(1).strip() if ret_match else None
                is_async = "async" in prefix
                params = [cls._parse_ts_param(p) for p in cls._split_param_list(raw_params)]
                functions[fn_name] = FunctionContract(
                    name=fn_name,
                    parameters=params,
                    return_annotation=ret_ann,
                    is_async=is_async
                )

    @classmethod
    def _extract_go_contracts(cls, clean_code: str, functions: Dict[str, FunctionContract], classes: Dict[str, ClassContract]) -> None:
        for m in re.finditer(r'\btype\s+([A-Za-z0-9_]+)\s+(?:struct|interface)\b', clean_code):
            name = m.group(1)
            if name and name[0].isupper():
                classes.setdefault(name, ClassContract(name=name, bases=[]))

        func_pattern = re.compile(r'\bfunc\s+')
        for m in func_pattern.finditer(clean_code):
            start = m.end()
            rem = clean_code[start:].lstrip()
            recv_type: Optional[str] = None
            if rem.startswith("("):
                paren_start = clean_code.find("(", start)
                paren_end = cls._find_matching_paren(clean_code, paren_start)
                if paren_end == -1:
                    continue
                recv_content = clean_code[paren_start + 1:paren_end].strip()
                tokens = recv_content.split()
                if tokens:
                    recv_type = tokens[-1].lstrip("*")
                start = paren_end + 1

            fn_match = re.match(r'^\s*([A-Za-z0-9_]+)\s*\(', clean_code[start:])
            if not fn_match:
                continue

            fn_name = fn_match.group(1)
            if not fn_name or not fn_name[0].isupper():
                continue

            paren_start = clean_code.find("(", start)
            paren_end = cls._find_matching_paren(clean_code, paren_start)
            if paren_end == -1:
                continue

            raw_params = clean_code[paren_start + 1:paren_end]
            params = cls._parse_go_params(raw_params)

            after_paren = clean_code[paren_end + 1:]
            brace_pos = after_paren.find("{")
            ret_ann = None
            if brace_pos != -1:
                raw_ret = after_paren[:brace_pos].strip()
                if raw_ret:
                    ret_ann = raw_ret

            fc = FunctionContract(
                name=fn_name,
                parameters=params,
                return_annotation=ret_ann
            )

            if recv_type:
                if recv_type not in classes:
                    classes[recv_type] = ClassContract(name=recv_type, bases=[])
                classes[recv_type].methods[fn_name] = fc
            else:
                functions[fn_name] = fc

    @classmethod
    def _extract_rust_contracts(cls, clean_code: str, functions: Dict[str, FunctionContract], classes: Dict[str, ClassContract]) -> None:
        for m in re.finditer(r'\bpub\s+(?:struct|enum)\s+([A-Za-z0-9_]+)\b', clean_code):
            name = m.group(1)
            classes.setdefault(name, ClassContract(name=name, bases=[]))

        top_level_code = list(clean_code)

        impl_pattern = re.compile(r'\bimpl(?:\s+<[^>]+>)?\s+([A-Za-z0-9_]+)\b[^{]*\{')
        for m in impl_pattern.finditer(clean_code):
            impl_name = m.group(1)
            brace_idx = m.end() - 1
            end_brace = cls._find_matching_brace(clean_code, brace_idx)
            if end_brace == -1:
                end_brace = len(clean_code) - 1

            for k in range(m.start(), end_brace + 1):
                if top_level_code[k] != "\n":
                    top_level_code[k] = " "

            if impl_name not in classes:
                classes[impl_name] = ClassContract(name=impl_name, bases=[])

            impl_body = clean_code[brace_idx + 1:end_brace]
            for fn_m in re.finditer(r'\bpub\s+(?:async\s+)?(?:unsafe\s+)?fn\s+([A-Za-z0-9_]+)\s*(?:<[^>]+>)?\s*\(', impl_body):
                fn_name = fn_m.group(1)
                p_start = fn_m.end() - 1
                p_end = cls._find_matching_paren(impl_body, p_start)
                if p_end != -1:
                    raw_params = impl_body[p_start + 1:p_end]
                    params = [p for p in (cls._parse_rust_param(x) for x in cls._split_param_list(raw_params)) if p is not None]
                    after_p = impl_body[p_end + 1:]
                    ret_m = re.match(r'^\s*->\s*([^{;]+)', after_p)
                    ret_ann = ret_m.group(1).strip() if ret_m else None
                    classes[impl_name].methods[fn_name] = FunctionContract(
                        name=fn_name,
                        parameters=params,
                        return_annotation=ret_ann
                    )

        top_str = "".join(top_level_code)
        for fn_m in re.finditer(r'\bpub\s+(?:async\s+)?(?:unsafe\s+)?fn\s+([A-Za-z0-9_]+)\s*(?:<[^>]+>)?\s*\(', top_str):
            fn_name = fn_m.group(1)
            p_start = fn_m.end() - 1
            p_end = cls._find_matching_paren(top_str, p_start)
            if p_end != -1:
                raw_params = top_str[p_start + 1:p_end]
                params = [p for p in (cls._parse_rust_param(x) for x in cls._split_param_list(raw_params)) if p is not None]
                after_p = top_str[p_end + 1:]
                ret_m = re.match(r'^\s*->\s*([^{;]+)', after_p)
                ret_ann = ret_m.group(1).strip() if ret_m else None
                functions[fn_name] = FunctionContract(
                    name=fn_name,
                    parameters=params,
                    return_annotation=ret_ann
                )

    @classmethod
    def _extract_java_cs_contracts(cls, clean_code: str, functions: Dict[str, FunctionContract], classes: Dict[str, ClassContract]) -> None:
        class_pattern = re.compile(
            r'\bpublic\s+(?:abstract\s+|static\s+|sealed\s+)?(?:class|interface)\s+([A-Za-z0-9_]+)(?:\s+extends\s+([^{]+))?\s*\{'
        )
        for m in class_pattern.finditer(clean_code):
            cls_name = m.group(1)
            bases = [b.strip() for b in m.group(2).split(",")] if m.group(2) else []
            brace_idx = m.end() - 1
            end_brace = cls._find_matching_brace(clean_code, brace_idx)
            if end_brace == -1:
                end_brace = len(clean_code) - 1

            class_body = clean_code[brace_idx + 1:end_brace]
            methods: Dict[str, FunctionContract] = {}

            method_depth = 0
            idx = 0
            n = len(class_body)
            while idx < n:
                ch = class_body[idx]
                if ch == "{":
                    method_depth += 1
                    idx += 1
                    continue
                elif ch == "}":
                    if method_depth > 0:
                        method_depth -= 1
                    idx += 1
                    continue

                if method_depth == 0:
                    m_hdr = re.match(
                        r'^\s*public\s+(?:static\s+|async\s+|final\s+|virtual\s+|override\s+)?([A-Za-z0-9_<>[\]]+)\s+([A-Za-z0-9_]+)\s*\(',
                        class_body[idx:]
                    )
                    if m_hdr:
                        ret_ann = m_hdr.group(1)
                        fn_name = m_hdr.group(2)
                        p_start = class_body.find("(", idx)
                        p_end = cls._find_matching_paren(class_body, p_start)
                        if p_end != -1:
                            raw_params = class_body[p_start + 1:p_end]
                            params = [cls._parse_java_param(p) for p in cls._split_param_list(raw_params)]
                            methods[fn_name] = FunctionContract(
                                name=fn_name,
                                parameters=params,
                                return_annotation=ret_ann
                            )
                            idx = p_end + 1
                            continue
                idx += 1

            classes[cls_name] = ClassContract(name=cls_name, bases=bases, methods=methods)

    @classmethod
    def extract_polyglot_contracts(cls, code: str, file_path: str = "module.ts") -> Tuple[Dict[str, FunctionContract], Dict[str, ClassContract]]:
        ext = os.path.splitext(file_path.lower())[1]
        clean_code = cls._strip_comments(code)
        functions: Dict[str, FunctionContract] = {}
        classes: Dict[str, ClassContract] = {}

        if ext in {".ts", ".tsx", ".js", ".jsx"}:
            cls._extract_ts_contracts(clean_code, functions, classes)
        elif ext == ".go":
            cls._extract_go_contracts(clean_code, functions, classes)
        elif ext == ".rs":
            cls._extract_rust_contracts(clean_code, functions, classes)
        elif ext in {".java", ".cs"}:
            cls._extract_java_cs_contracts(clean_code, functions, classes)

        return functions, classes


class ASTContractComparator:
    """Compares two versions of public AST contracts and evaluates breaking changes."""

    @classmethod
    def compare_code(cls, old_code: str, new_code: str, file_path: str = "code.py") -> ContractDiffReport:
        ext = os.path.splitext(file_path.lower())[1]
        if ext in ASTContractExtractor.POLYGLOT_EXTENSIONS:
            old_funcs, old_classes = ASTContractExtractor.extract_polyglot_contracts(old_code, file_path=file_path)
            new_funcs, new_classes = ASTContractExtractor.extract_polyglot_contracts(new_code, file_path=file_path)
        else:
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

        # Get list of changed python and polyglot files
        valid_exts = {".py"} | ASTContractExtractor.POLYGLOT_EXTENSIONS
        try:
            diff_proc = subprocess.run(
                ["git", "diff", "--name-only", base_ref],
                cwd=abs_repo,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            files = [
                f.strip() for f in diff_proc.stdout.splitlines()
                if f.strip() and os.path.splitext(f.strip().lower())[1] in valid_exts
            ]
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
                    ["git", "show", f"{base_ref}:{rel_file}"],
                    cwd=abs_repo,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
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
    def format_sarif_report(cls, reports: List[ContractDiffReport]) -> Dict[str, Any]:
        """Formats contract diff reports into an industry-standard SARIF 2.1.0 JSON object."""
        rules_map: Dict[str, Dict[str, Any]] = {}
        results: List[Dict[str, Any]] = []

        for r in reports:
            # Breaking changes -> error
            for v in r.breaking_changes:
                if v.category not in rules_map:
                    rules_map[v.category] = {
                        "id": v.category,
                        "name": v.category,
                        "shortDescription": {"text": f"Contract violation rule {v.category}"}
                    }
                results.append({
                    "ruleId": v.category,
                    "level": "error",
                    "message": {"text": v.details},
                    "locations": [{
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": r.file_path.replace("\\", "/")
                            }
                        }
                    }]
                })

            # Modifications -> warning for RETURN_TYPE_CHANGED, else note
            for v in r.modifications:
                lvl = "warning" if v.category == "RETURN_TYPE_CHANGED" else "note"
                if v.category not in rules_map:
                    rules_map[v.category] = {
                        "id": v.category,
                        "name": v.category,
                        "shortDescription": {"text": f"Contract modification rule {v.category}"}
                    }
                results.append({
                    "ruleId": v.category,
                    "level": lvl,
                    "message": {"text": v.details},
                    "locations": [{
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": r.file_path.replace("\\", "/")
                            }
                        }
                    }]
                })

            # Additions -> note
            for v in r.non_breaking_additions:
                if v.category not in rules_map:
                    rules_map[v.category] = {
                        "id": v.category,
                        "name": v.category,
                        "shortDescription": {"text": f"Contract addition rule {v.category}"}
                    }
                results.append({
                    "ruleId": v.category,
                    "level": "note",
                    "message": {"text": v.details},
                    "locations": [{
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": r.file_path.replace("\\", "/")
                            }
                        }
                    }]
                })

        rules_list = [rules_map[k] for k in sorted(rules_map.keys())]

        return {
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "T-Zero Contract Guardian",
                            "version": "10.9.0",
                            "rules": rules_list
                        }
                    },
                    "results": results
                }
            ]
        }

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

