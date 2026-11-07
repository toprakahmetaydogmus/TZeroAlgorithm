# -*- coding: utf-8 -*-
"""
T-ZERO AUTONOMOUS SELF-HEALING EXECUTION ENGINE
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Version: 4.4.0

Bu modül, kodları ve terminal komutlarını izole bir şekilde yürüten,
oluşan hataları (SyntaxError, NameError, ImportError, runtime panic vb.)
AST ve kural tabanlı cerrahi yamalarla otomatik olarak onaran (Auto-Patch)
ve çözümü nedensellik çizgesine kaydeden otonom onarım motorudur.
"""

from __future__ import annotations
import os
import sys
import re
import ast
import time
import subprocess
import traceback
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from tzero_jarvis.causal_graph import CausalTemporalGraph, CausalRelationType


@dataclass
class ExecutionResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    success: bool
    error_type: Optional[str] = None
    error_line: Optional[int] = None
    error_file: Optional[str] = None
    applied_patches: List[str] = field(default_factory=list)
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error_type": self.error_type,
            "error_line": self.error_line,
            "error_file": self.error_file,
            "applied_patches": self.applied_patches,
            "resolved": self.resolved
        }


class SelfHealingExecutionEngine:
    """
    Otonom Hata Yakalama, Teşhis ve AST Tabanlı Otomatik Onarım Motoru.
    """

    def __init__(self, causal_graph: Optional[CausalTemporalGraph] = None, work_dir: Optional[str] = None):
        self.causal_graph = causal_graph or CausalTemporalGraph()
        self.work_dir = work_dir or os.getcwd()

    def run_command(self, command: str, timeout: int = 30) -> ExecutionResult:
        """
        Komutu çalıştırır, süreyi ve çıktıları ölçer.
        """
        start_time = time.time()
        try:
            res = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.work_dir
            )
            duration_ms = (time.time() - start_time) * 1000.0
            success = (res.returncode == 0)
            
            error_type, error_file, error_line = None, None, None
            if not success:
                error_type, error_file, error_line = self.diagnose_error(res.stderr or res.stdout)

            return ExecutionResult(
                command=command,
                exit_code=res.returncode,
                stdout=res.stdout,
                stderr=res.stderr,
                duration_ms=round(duration_ms, 2),
                success=success,
                error_type=error_type,
                error_file=error_file,
                error_line=error_line,
                resolved=success
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"TimeoutExpired after {timeout} seconds",
                duration_ms=timeout * 1000.0,
                success=False,
                error_type="TimeoutExpired",
                resolved=False
            )
        except Exception as e:
            return ExecutionResult(
                command=command,
                exit_code=-2,
                stdout="",
                stderr=str(e),
                duration_ms=(time.time() - start_time) * 1000.0,
                success=False,
                error_type=type(e).__name__,
                resolved=False
            )

    def diagnose_error(self, error_text: str) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        """
        Stderr ve stacktrace içinden hata türünü, dosya yolunu ve satır numarasını ayıklar.
        """
        if not error_text:
            return None, None, None

        # 1. Python Traceback: File "...", line X, in ...
        py_tb_match = re.findall(r'File "([^"]+)", line (\d+)', error_text)
        error_file, error_line = None, None
        if py_tb_match:
            error_file, line_str = py_tb_match[-1]
            try:
                error_line = int(line_str)
            except ValueError:
                pass

        # 2. Rust/Cargo Error: --> src/main.rs:12:5
        rust_match = re.search(r'-->\s+([^:]+):(\d+):(\d+)', error_text)
        if rust_match:
            error_file = rust_match.group(1)
            try:
                error_line = int(rust_match.group(2))
            except ValueError:
                pass

        # 3. Hata Tipi Tespiti
        err_type = "GenericExecutionError"
        for line in reversed(error_text.strip().splitlines()):
            line_str = line.strip()
            # Örn: NameError: name 'foo' is not defined
            # SyntaxError: invalid syntax
            # ModuleNotFoundError: No module named '...'
            match = re.match(r'^([A-Z][a-zA-Z0-9_]+Error|Exception|Panic|error\[E\d+\]):\s*(.*)', line_str)
            if match:
                err_type = match.group(1)
                break
            if "panic" in line_str.lower():
                err_type = "RustPanic"
                break
            if "syntax error" in line_str.lower():
                err_type = "SyntaxError"
                break

        return err_type, error_file, error_line

    def auto_repair_python_file(self, file_path: str, error_type: str, error_line: Optional[int], stderr: str) -> bool:
        """
        Belirtilen Python dosyasındaki yaygın hataları AST ve kural tabanlı olarak otomatik onarır.
        """
        if not os.path.exists(file_path):
            return False

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return False

        lines = content.splitlines(keepends=True)
        modified = False
        patch_note = ""

        # Hata 1: ModuleNotFoundError / ImportError: No module named 'xxx'
        mod_match = re.search(r"No module named ['\"]([^'\"]+)['\"]", stderr)
        if mod_match:
            missing_mod = mod_match.group(1)
            # Eğer dahili bir alt paket veya standart kütüphane eksikliği ise sys.path ekle
            if missing_mod in ("tzero_jarvis", "tzero", "crates"):
                sys_path_inject = f"import sys, os\nsys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))\n"
                if sys_path_inject not in content:
                    lines.insert(0, sys_path_inject)
                    modified = True
                    patch_note = f"Injected sys.path for missing internal module {missing_mod}"

        # Hata 2: NameError: name 'X' is not defined (Yaygın: os, sys, json, time, re, math)
        name_match = re.search(r"name ['\"]([^'\"]+)['\"] is not defined", stderr)
        if name_match:
            missing_name = name_match.group(1)
            common_std_libs = {
                "os": "import os\n",
                "sys": "import sys\n",
                "json": "import json\n",
                "time": "import time\n",
                "re": "import re\n",
                "math": "import math\n",
                "Path": "from pathlib import Path\n",
                "Optional": "from typing import Optional\n",
                "List": "from typing import List\n",
                "Dict": "from typing import Dict\n",
                "Tuple": "from typing import Tuple\n",
                "Any": "from typing import Any\n",
            }
            if missing_name in common_std_libs:
                lines.insert(0, common_std_libs[missing_name])
                modified = True
                patch_note = f"Imported missing name '{missing_name}'"

        # Hata 3: SyntaxError / IndentationError satır sonu eksik parantez veya iki nokta ':'
        if error_type in ("SyntaxError", "IndentationError") and error_line and 1 <= error_line <= len(lines):
            idx = error_line - 1
            bad_line = lines[idx]
            stripped = bad_line.strip()
            # if, for, while, def, class sonuna ':' ekleme
            for kw in ("if ", "for ", "while ", "def ", "class ", "elif ", "else:", "except"):
                if stripped.startswith(kw) and not stripped.endswith(":"):
                    lines[idx] = bad_line.rstrip() + ":\n"
                    modified = True
                    patch_note = f"Added missing colon ':' on line {error_line}"
                    break

        if modified:
            try:
                # AST syntax kontrolü yap, eğer geçerliyse kaydet
                ast.parse("".join(lines))
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                return True
            except SyntaxError:
                # AST yine geçmediyse geri al
                return False

        return False

    def execute_and_heal(self, command: str, max_retries: int = 3) -> ExecutionResult:
        """
        Komutu çalıştırır. Hata olursa teşhis eder, otomatik onarım uygular
        ve başarıya ulaşana kadar (veya max_retries dolana kadar) döngüyü sürdürür.
        Sonucu Causal Graph'a kaydeder.
        """
        attempt = 0
        current_res = self.run_command(command)
        applied_patches = []

        while not current_res.success and attempt < max_retries:
            attempt += 1
            error_type = current_res.error_type or "UnknownError"
            error_file = current_res.error_file

            # Causal Graph'a hatayı düğüm olarak ekle
            err_node_id = f"err_{int(time.time()*1000)%100000}"
            self.causal_graph.add_node(
                node_id=err_node_id,
                label=f"Failure: {error_type} in {error_file or 'command'}",
                entity_type="VULN",
                attributes={"stderr": current_res.stderr[:200]}
            )

            repaired = False
            if error_file and error_file.endswith(".py") and os.path.isabs(error_file):
                repaired = self.auto_repair_python_file(
                    error_file,
                    error_type,
                    current_res.error_line,
                    current_res.stderr
                )
            elif error_file and error_file.endswith(".py"):
                # Göreceli yol ise work_dir ile birleştir
                full_path = os.path.join(self.work_dir, error_file)
                if os.path.exists(full_path):
                    repaired = self.auto_repair_python_file(
                        full_path,
                        error_type,
                        current_res.error_line,
                        current_res.stderr
                    )

            if repaired:
                patch_id = f"patch_{int(time.time()*1000)%100000}"
                self.causal_graph.add_node(
                    node_id=patch_id,
                    label=f"AutoPatch applied to {error_file}",
                    entity_type="SOFTWARE"
                )
                self.causal_graph.add_edge(patch_id, err_node_id, relation=CausalRelationType.FIXES)
                applied_patches.append(f"Auto-patched {error_file} on line {current_res.error_line}")
                
                # Tekrar dene
                current_res = self.run_command(command)
                if current_res.success:
                    current_res.resolved = True
                    break
            else:
                # Otomatik kural bulunamadı, döngüden çık
                break

        current_res.applied_patches = applied_patches
        return current_res
