# -*- coding: utf-8 -*-
"""Tier 20: Native Machine Code Stripped Compiler & Binary Bridge.

The ultimate defense tier against Python decompilation: eliminates Python
bytecode altogether by compiling performance-critical and sensitive logic
into native C / Rust machine code extensions (.pyd / .so / .dll).

When compiled as stripped machine code with Link-Time Optimization (LTO):
- Zero Python bytecode exists for pycdc or uncompyle6.
- Decompilers see only stripped x86_64/ARM64 assembly instructions.
- AI reverse-engineering agents (REA, Ghidra MCP) face an exponentially
  harder decompilation problem.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

import os
import re
import shutil
import sys
import sysconfig
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional


class NativeBridge:
    """Manages compilation of sensitive Python logic into stripped machine code."""

    @classmethod
    def generate_c_wrapper_template(cls, func_name: str, logic_c: str) -> str:
        """Generates a self-contained ANSI C extension source file."""
        return f"""/*
 * Siber Akademi Anti-REA Native Machine Code Shield
 * Stripped C Kernel — Zero Python Bytecode Footprint
 */
#define PY_SSIZE_T_CLEAN
#include <Python.h>

static PyObject* method_{func_name}(PyObject* self, PyObject* args) {{
    long x, y, result;
    if (!PyArg_ParseTuple(args, "ll", &x, &y)) {{
        return NULL;
    }}
    
    /* Native execution logic */
    {logic_c}
    
    return PyLong_FromLong(result);
}}

static PyMethodDef NativeMethods[] = {{
    {{"{func_name}", method_{func_name}, METH_VARARGS, "Native Stripped Execution Kernel"}},
    {{NULL, NULL, 0, NULL}}
}};

static struct PyModuleDef nativemodule = {{
    PyModuleDef_HEAD_INIT,
    "native_armor_core",
    "Anti-REA Native Shield Core",
    -1,
    NativeMethods
}};

PyMODINIT_FUNC PyInit_native_armor_core(void) {{
    return PyModule_Create(&nativemodule);
}}
"""

    @classmethod
    def audit_native_coverage(cls, target_path: str) -> Dict[str, Any]:
        """Audits target codebase or directory for native binary compiled shield coverage."""
        p = Path(target_path)
        if not p.exists():
            return {"error": "Path not found", "native_files": 0}

        native_extensions = {".pyd", ".so", ".dll", ".dylib"}
        if p.is_file():
            is_native = p.suffix.lower() in native_extensions
            return {
                "target": str(p),
                "is_native_binary": is_native,
                "rating": "NATIVE_STRIPPED_MACHINE_CODE" if is_native else "INTERPRETED_BYTECODE"
            }

        native_files = [f for f in p.rglob("*") if f.suffix.lower() in native_extensions]
        py_files = [f for f in p.rglob("*.py") if "__pycache__" not in str(f)]

        ratio = len(native_files) / max(1, len(native_files) + len(py_files))
        return {
            "directory": str(p),
            "native_binaries": len(native_files),
            "python_sources": len(py_files),
            "native_shield_ratio": round(ratio, 2),
            "status": "HYBRID_HARDENED" if native_files else "BYTECODE_ONLY"
        }

    @classmethod
    def compile_native_extension(
        cls,
        func_name: str,
        logic_c: str,
        output_dir: str,
    ) -> Dict[str, Any]:
        """Generates C extension source and compiles a stripped shared library when a compiler is available."""
        safe_fn = re.sub(r"[^A-Za-z0-9_]", "_", func_name or "kernel")
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        c_src_path = out_path / f"{safe_fn}_native.c"
        c_code = cls.generate_c_wrapper_template(safe_fn, logic_c)
        c_src_path.write_text(c_code, encoding="utf-8")

        ext_suffix = sysconfig.get_config_var("EXT_SUFFIX") or (".pyd" if os.name == "nt" else ".so")
        binary_path = out_path / f"native_armor_core{ext_suffix}"
        include_dir = sysconfig.get_path("include")
        compiler = shutil.which("gcc") or shutil.which("clang")

        if not compiler or not include_dir:
            return {
                "compiled": False,
                "compiler": None,
                "source_file": str(c_src_path),
                "binary_file": None,
                "fallback": "C_SOURCE_EMITTED",
                "reason": "Native C compiler (gcc/clang) or Python headers unavailable.",
            }

        cmd = [
            compiler,
            "-O3",
            "-shared",
            "-s",
            f"-I{include_dir}",
            str(c_src_path),
            "-o",
            str(binary_path),
        ]
        if os.name != "nt":
            cmd.insert(2, "-fPIC")

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if proc.returncode == 0 and binary_path.is_file():
                return {
                    "compiled": True,
                    "compiler": compiler,
                    "source_file": str(c_src_path),
                    "binary_file": str(binary_path),
                    "fallback": None,
                }
            return {
                "compiled": False,
                "compiler": compiler,
                "source_file": str(c_src_path),
                "binary_file": None,
                "fallback": "C_SOURCE_EMITTED",
                "reason": (proc.stderr or proc.stdout or "Compiler exited non-zero")[:300],
            }
        except Exception as exc:
            return {
                "compiled": False,
                "compiler": compiler,
                "source_file": str(c_src_path),
                "binary_file": None,
                "fallback": "C_SOURCE_EMITTED",
                "reason": str(exc),
            }
