# -*- coding: utf-8 -*-
"""
Siber Akademi — T-Zero Universal Polyglot Type & Schema Transpiler.
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: MIT

Transpiles Python @dataclass and Pydantic data models into TypeScript interfaces,
Rust structs, and Go structs deterministically via AST.
"""

import os
import sys
import ast
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple


@dataclass
class ModelField:
    name: str
    py_type: str
    is_optional: bool = False
    doc: str = ""


@dataclass
class TranspiledModel:
    class_name: str
    fields: List[ModelField] = field(default_factory=list)
    docstring: str = ""
    typescript: str = ""
    rust: str = ""
    golang: str = ""
    kotlin: str = ""
    swift: str = ""


class PolyglotTypeBridge:
    """Deterministic Polyglot Type & Schema Transpiler."""

    # Type Mapping Tables
    TYPE_MAP_TS = {
        "str": "string",
        "int": "number",
        "float": "number",
        "bool": "boolean",
        "bytes": "Uint8Array",
        "dict": "Record<string, any>",
        "list": "any[]",
        "set": "Set<any>",
        "tuple": "[any]",
        "Any": "any",
        "datetime": "string",
        "date": "string",
        "UUID": "string",
    }

    TYPE_MAP_RUST = {
        "str": "String",
        "int": "i64",
        "float": "f64",
        "bool": "bool",
        "bytes": "Vec<u8>",
        "dict": "std::collections::HashMap<String, serde_json::Value>",
        "list": "Vec<serde_json::Value>",
        "set": "std::collections::HashSet<String>",
        "Any": "serde_json::Value",
        "datetime": "chrono::DateTime<chrono::Utc>",
        "date": "chrono::NaiveDate",
        "UUID": "uuid::Uuid",
    }

    TYPE_MAP_GO = {
        "str": "string",
        "int": "int64",
        "float": "float64",
        "bool": "bool",
        "bytes": "[]byte",
        "dict": "map[string]interface{}",
        "list": "[]interface{}",
        "set": "[]string",
        "Any": "interface{}",
        "datetime": "time.Time",
        "date": "time.Time",
        "UUID": "string",
    }

    TYPE_MAP_KOTLIN = {
        "str": "String",
        "int": "Long",
        "float": "Double",
        "bool": "Boolean",
        "bytes": "ByteArray",
        "dict": "Map<String, Any>",
        "list": "List<Any>",
        "set": "Set<String>",
        "Any": "Any",
        "datetime": "java.time.Instant",
        "date": "java.time.LocalDate",
        "UUID": "java.util.UUID",
    }

    TYPE_MAP_SWIFT = {
        "str": "String",
        "int": "Int",
        "float": "Double",
        "bool": "Bool",
        "bytes": "Data",
        "dict": "[String: Any]",
        "list": "[Any]",
        "set": "Set<String>",
        "Any": "Any",
        "datetime": "Date",
        "date": "Date",
        "UUID": "UUID",
    }

    @classmethod
    def _parse_py_type(cls, node: ast.AST) -> Tuple[str, bool]:
        """Returns (base_type_str, is_optional)."""
        if node is None:
            return "Any", False

        # e.g. Optional[T] or Union[T, None]
        if isinstance(node, ast.Subscript):
            val_name = getattr(node.value, "id", "")
            if val_name == "Optional":
                inner, _ = cls._parse_py_type(node.slice)
                return inner, True
            elif val_name in ("List", "list"):
                inner, _ = cls._parse_py_type(node.slice)
                return f"List[{inner}]", False
            elif val_name in ("Dict", "dict"):
                if isinstance(node.slice, ast.Tuple) and len(node.slice.elts) == 2:
                    k, _ = cls._parse_py_type(node.slice.elts[0])
                    v, _ = cls._parse_py_type(node.slice.elts[1])
                    return f"Dict[{k}, {v}]", False
                return "Dict[str, Any]", False
            elif val_name == "Union":
                # Check if None is in union
                elts = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
                non_none = [e for e in elts if not (isinstance(e, ast.Constant) and e.value is None) and getattr(e, "id", "") != "None"]
                if len(non_none) == 1:
                    inner, _ = cls._parse_py_type(non_none[0])
                    return inner, True
                return "Any", True
            return "Any", False
        elif isinstance(node, ast.Name):
            return node.id, False
        elif isinstance(node, ast.Constant):
            return str(node.value), False

        return "Any", False

    @classmethod
    def _to_ts_type(cls, py_type: str, is_optional: bool) -> str:
        if py_type.startswith("List["):
            inner = py_type[5:-1]
            ts_inner = cls._to_ts_type(inner, False)
            res = f"{ts_inner}[]"
        elif py_type.startswith("Dict["):
            parts = py_type[5:-1].split(",", 1)
            k = cls._to_ts_type(parts[0].strip(), False) if len(parts) > 0 else "string"
            v = cls._to_ts_type(parts[1].strip(), False) if len(parts) > 1 else "any"
            res = f"Record<{k}, {v}>"
        else:
            res = cls.TYPE_MAP_TS.get(py_type, py_type)

        return f"{res} | null" if is_optional else res

    @classmethod
    def _to_rust_type(cls, py_type: str, is_optional: bool) -> str:
        if py_type.startswith("List["):
            inner = py_type[5:-1]
            rust_inner = cls._to_rust_type(inner, False)
            res = f"Vec<{rust_inner}>"
        elif py_type.startswith("Dict["):
            parts = py_type[5:-1].split(",", 1)
            k = cls._to_rust_type(parts[0].strip(), False) if len(parts) > 0 else "String"
            v = cls._to_rust_type(parts[1].strip(), False) if len(parts) > 1 else "serde_json::Value"
            res = f"std::collections::HashMap<{k}, {v}>"
        else:
            res = cls.TYPE_MAP_RUST.get(py_type, py_type)

        return f"Option<{res}>" if is_optional else res

    @classmethod
    def _to_go_type(cls, py_type: str, is_optional: bool) -> str:
        if py_type.startswith("List["):
            inner = py_type[5:-1]
            go_inner = cls._to_go_type(inner, False)
            res = f"[]{go_inner}"
        elif py_type.startswith("Dict["):
            parts = py_type[5:-1].split(",", 1)
            k = cls._to_go_type(parts[0].strip(), False) if len(parts) > 0 else "string"
            v = cls._to_go_type(parts[1].strip(), False) if len(parts) > 1 else "interface{}"
            res = f"map[{k}]{v}"
        else:
            res = cls.TYPE_MAP_GO.get(py_type, py_type)

        return f"*{res}" if is_optional else res

    @classmethod
    def _to_kotlin_type(cls, py_type: str, is_optional: bool) -> str:
        if py_type.startswith("List["):
            inner = py_type[5:-1]
            kt_inner = cls._to_kotlin_type(inner, False)
            res = f"List<{kt_inner}>"
        elif py_type.startswith("Dict["):
            parts = py_type[5:-1].split(",", 1)
            k = cls._to_kotlin_type(parts[0].strip(), False) if len(parts) > 0 else "String"
            v = cls._to_kotlin_type(parts[1].strip(), False) if len(parts) > 1 else "Any"
            res = f"Map<{k}, {v}>"
        else:
            res = cls.TYPE_MAP_KOTLIN.get(py_type, py_type)

        return f"{res}?" if is_optional else res

    @classmethod
    def _to_swift_type(cls, py_type: str, is_optional: bool) -> str:
        if py_type.startswith("List["):
            inner = py_type[5:-1]
            swift_inner = cls._to_swift_type(inner, False)
            res = f"[{swift_inner}]"
        elif py_type.startswith("Dict["):
            parts = py_type[5:-1].split(",", 1)
            k = cls._to_swift_type(parts[0].strip(), False) if len(parts) > 0 else "String"
            v = cls._to_swift_type(parts[1].strip(), False) if len(parts) > 1 else "Any"
            res = f"[{k}: {v}]"
        else:
            res = cls.TYPE_MAP_SWIFT.get(py_type, py_type)

        return f"{res}?" if is_optional else res

    @classmethod
    def parse_python_models(cls, py_code: str) -> List[TranspiledModel]:
        """Parses Python classes and generates TypeScript, Rust, and Go interfaces."""
        try:
            tree = ast.parse(py_code)
        except Exception:
            return []

        models: List[TranspiledModel] = []

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                fields: List[ModelField] = []
                doc = ast.get_docstring(node) or ""

                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        fname = item.target.id
                        ptype, opt = cls._parse_py_type(item.annotation)
                        fields.append(ModelField(name=fname, py_type=ptype, is_optional=opt))

                if not fields:
                    continue

                # Generate TS
                ts_lines = [f"export interface {node.name} {{"]
                for f in fields:
                    opt_mark = "?" if f.is_optional else ""
                    ts_t = cls._to_ts_type(f.py_type, f.is_optional)
                    ts_lines.append(f"  {f.name}{opt_mark}: {ts_t};")
                ts_lines.append("}")
                ts_str = "\n".join(ts_lines)

                # Generate Rust
                rust_lines = [
                    "#[derive(Debug, Clone, Serialize, Deserialize)]",
                    f"pub struct {node.name} {{"
                ]
                for f in fields:
                    r_type = cls._to_rust_type(f.py_type, f.is_optional)
                    rust_lines.append(f"    pub {f.name}: {r_type},")
                rust_lines.append("}")
                rust_str = "\n".join(rust_lines)

                # Generate Go
                go_lines = [f"type {node.name} struct {{"]
                for f in fields:
                    g_type = cls._to_go_type(f.py_type, f.is_optional)
                    pascal_name = "".join(p.capitalize() for p in f.name.split("_"))
                    go_lines.append(f'\t{pascal_name} {g_type} `json:"{f.name}"`')
                go_lines.append("}")
                go_str = "\n".join(go_lines)

                # Generate Kotlin
                kt_lines = [f"data class {node.name}("]
                for idx, f in enumerate(fields):
                    kt_type = cls._to_kotlin_type(f.py_type, f.is_optional)
                    parts = f.name.split("_")
                    camel_name = parts[0] + "".join(p.capitalize() for p in parts[1:]) if len(parts) > 1 else f.name
                    default_suffix = " = null" if f.is_optional else ""
                    comma = "," if idx < len(fields) - 1 else ""
                    kt_lines.append(f"    val {camel_name}: {kt_type}{default_suffix}{comma}")
                kt_lines.append(")")
                kt_str = "\n".join(kt_lines)

                # Generate Swift
                swift_lines = [
                    f"public struct {node.name}: Codable, Equatable {{",
                ]
                for f in fields:
                    swift_type = cls._to_swift_type(f.py_type, f.is_optional)
                    parts = f.name.split("_")
                    camel_name = parts[0] + "".join(p.capitalize() for p in parts[1:]) if len(parts) > 1 else f.name
                    swift_lines.append(f"    public let {camel_name}: {swift_type}")
                swift_lines.append("}")
                swift_str = "\n".join(swift_lines)

                models.append(TranspiledModel(
                    class_name=node.name,
                    fields=fields,
                    docstring=doc,
                    typescript=ts_str,
                    rust=rust_str,
                    golang=go_str,
                    kotlin=kt_str,
                    swift=swift_str
                ))

        return models

    @classmethod
    def transpile_file(cls, py_file_path: str, target_lang: str = "ts") -> str:
        """Reads Python file and returns transpiled definitions in requested language."""
        with open(py_file_path, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()

        models = cls.parse_python_models(code)
        if not models:
            return f"// No typed models or dataclasses detected in {os.path.basename(py_file_path)}"

        target = target_lang.lower().strip()
        if target in ("ts", "typescript"):
            return "\n\n".join(m.typescript for m in models)
        elif target in ("rust", "rs"):
            return "\n\n".join(m.rust for m in models)
        elif target in ("go", "golang"):
            return "\n\n".join(m.golang for m in models)
        elif target in ("kt", "kotlin"):
            return "\n\n".join(m.kotlin for m in models)
        elif target in ("swift", "ios"):
            return "\n\n".join(m.swift for m in models)
        else:
            return "\n\n".join(
                f"// --- {m.class_name} ---\n// TypeScript:\n{m.typescript}\n\n// Rust:\n{m.rust}\n\n// Go:\n{m.golang}\n\n// Kotlin:\n{m.kotlin}\n\n// Swift:\n{m.swift}"
                for m in models
            )

    @classmethod
    def render_cli(cls, py_file: str, lang: str):
        print(f"\n🌉 \033[1mT-ZERO POLYGLOT TYPE & SCHEMA TRANSPILER\033[0m")
        print("=" * 70)
        print(f"📄 Source Python Model: {py_file}")
        print(f"🎯 Target Language:     \033[36m{lang.upper()}\033[0m")
        print("=" * 70)
        out = cls.transpile_file(py_file, target_lang=lang)
        print(out)
        print("=" * 70)

