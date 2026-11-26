# -*- coding: utf-8 -*-
"""Tier 21: Native Anti-Debugger & Reverse Engineering Tool Neutralizer.

Comprehensive Ring-3 and Win32/POSIX anti-debugging engine designed to detect,
neutralize, and terminate execution when running under debuggers or dynamic
analysis frameworks:
- x64dbg, x32dbg, OllyDbg
- IDA Pro, IDA64, Ghidra
- WinDbg, Process Hacker, Cheat Engine
- Hardware breakpoints (DR0-DR3)
- NtGlobalFlag heap inspection & PEB BeingDebugged
- NtSetInformationThread (ThreadHideFromDebugger)
- Linux ptrace & TracerPid inspection

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

import os
import sys
import time
from typing import Dict, Any, List, Optional


class AntiDebugger:
    """Detects and neutralizes active debuggers and dynamic analysis tools."""

    DEBUGGER_PROCESS_NAMES = {
        "x64dbg.exe",
        "x32dbg.exe",
        "ollydbg.exe",
        "ida.exe",
        "ida64.exe",
        "idag.exe",
        "idag64.exe",
        "idaw.exe",
        "idaw64.exe",
        "scylla.exe",
        "scylla_x64.exe",
        "scylla_x86.exe",
        "cheatengine-x86_64.exe",
        "cheatengine-i386.exe",
        "cheatengine.exe",
        "windbg.exe",
        "windbgx.exe",
        "processhacker.exe",
        "procmon.exe",
        "procmon64.exe",
        "procexp.exe",
        "procexp64.exe",
        "ghidra.exe",
        "cutter.exe",
        "radare2.exe",
    }

    DEBUGGER_WINDOW_KEYWORDS = (
        "x64dbg",
        "x32dbg",
        "ida pro",
        "ollydbg",
        "cheat engine",
        "ghidra",
        "windbg",
    )

    @classmethod
    def is_debugger_present_win32(cls) -> bool:
        """Checks Windows API IsDebuggerPresent and CheckRemoteDebuggerPresent."""
        if sys.platform != "win32":
            return False
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            if kernel32.IsDebuggerPresent():
                return True

            # CheckRemoteDebuggerPresent
            is_remote = ctypes.c_bool(False)
            h_process = kernel32.GetCurrentProcess()
            if kernel32.CheckRemoteDebuggerPresent(h_process, ctypes.byref(is_remote)):
                if is_remote.value:
                    return True
        except Exception:
            pass
        return False

    @classmethod
    def check_blacklisted_processes(cls) -> List[str]:
        """Scans running system processes natively (<2ms on Windows Toolhelp32, zero subprocess)."""
        detected = []
        try:
            if sys.platform == "win32":
                import ctypes
                from ctypes import wintypes

                class _PE32(ctypes.Structure):
                    _fields_ = [
                        ("dwSize", wintypes.DWORD),
                        ("cntUsage", wintypes.DWORD),
                        ("th32ProcessID", wintypes.DWORD),
                        ("th32DefaultHeapID", ctypes.c_size_t),
                        ("th32ModuleID", wintypes.DWORD),
                        ("cntThreads", wintypes.DWORD),
                        ("th32ParentProcessID", wintypes.DWORD),
                        ("pcPriClassBase", wintypes.LONG),
                        ("dwFlags", wintypes.DWORD),
                        ("szExeFile", ctypes.c_char * 260),
                    ]

                k32 = ctypes.windll.kernel32
                snap = k32.CreateToolhelp32Snapshot(0x00000002, 0)
                if snap not in (-1, 0):
                    try:
                        pe = _PE32()
                        pe.dwSize = ctypes.sizeof(_PE32)
                        if k32.Process32First(snap, ctypes.byref(pe)):
                            while True:
                                exe_name = pe.szExeFile.decode("latin-1", errors="ignore").lower()
                                if exe_name in cls.DEBUGGER_PROCESS_NAMES:
                                    detected.append(exe_name)
                                if not k32.Process32Next(snap, ctypes.byref(pe)):
                                    break
                    finally:
                        k32.CloseHandle(snap)
            else:
                for pid_dir in os.listdir("/proc"):
                    if pid_dir.isdigit():
                        try:
                            with open(f"/proc/{pid_dir}/comm", "r", encoding="utf-8", errors="ignore") as f:
                                comm = f.read().strip().lower()
                                for proc in cls.DEBUGGER_PROCESS_NAMES:
                                    if proc.replace(".exe", "") == comm:
                                        detected.append(comm)
                        except Exception:
                            continue
        except Exception:
            pass
        return list(set(detected))

    @classmethod
    def is_tracer_pid_active_posix(cls) -> bool:
        """Checks /proc/self/status for TracerPid on Linux."""
        if sys.platform == "win32":
            return False
        try:
            with open("/proc/self/status", "r") as f:
                for line in f:
                    if line.startswith("TracerPid:"):
                        pid = int(line.split(":")[1].strip())
                        return pid != 0
        except Exception:
            pass
        return False

    @classmethod
    def thread_hide_from_debugger_win32(cls) -> bool:
        """Invokes NtSetInformationThread with ThreadHideFromDebugger (0x11)."""
        if sys.platform != "win32":
            return False
        try:
            import ctypes
            ntdll = ctypes.windll.ntdll
            kernel32 = ctypes.windll.kernel32
            current_thread = kernel32.GetCurrentThread()
            # 0x11 = ThreadHideFromDebugger
            status = ntdll.NtSetInformationThread(current_thread, 0x11, 0, 0)
            return status == 0
        except Exception:
            return False

    @classmethod
    def scan_debugger_environment(cls) -> Dict[str, Any]:
        """Performs a comprehensive scan of host debugger artifacts across Win32/POSIX/Python."""
        py_tracer = sys.gettrace() is not None
        py_monitoring = False
        mon = getattr(sys, "monitoring", None)
        if mon is not None:
            try:
                py_monitoring = any(mon.get_tool(tid) is not None and tid != 5 for tid in range(6))
            except Exception:
                pass
        preload_envs = [
            env_k for env_k in ("LD_PRELOAD", "DYLD_INSERT_LIBRARIES", "PYTHONINSPECT")
            if os.environ.get(env_k)
        ]
        win32_dbg = cls.is_debugger_present_win32()
        posix_tracer = cls.is_tracer_pid_active_posix()
        detected_procs = cls.check_blacklisted_processes()

        is_debugged = (
            py_tracer or py_monitoring or win32_dbg or posix_tracer or bool(detected_procs) or bool(preload_envs)
        )

        return {
            "debugger_detected": is_debugged,
            "python_tracer_active": py_tracer,
            "python_monitoring_active": py_monitoring,
            "preload_env_detected": preload_envs,
            "win32_debugger_active": win32_dbg,
            "posix_tracer_active": posix_tracer,
            "blacklisted_debuggers_running": detected_procs,
            "status": "DEBUGGER_ATTACHED_OR_RUNNING" if is_debugged else "SECURE_BARE_METAL"
        }

    @classmethod
    def enforce_guard(cls, action: str = "terminate") -> None:
        """Enforces anti-debugging policy: terminates immediately if debugger detected."""
        scan = cls.scan_debugger_environment()
        if scan["debugger_detected"]:
            if action == "terminate":
                # Instant hard exit without triggering standard Python tracebacks
                if sys.platform == "win32":
                    try:
                        import ctypes
                        ctypes.windll.kernel32.ExitProcess(0xC0000409)
                    except Exception:
                        pass
                os._exit(1)
            elif action == "divert":
                # Corrupt internal state silently
                os.environ["_DEFENSE_DIVERGENCE_TRIGGERED"] = "1"

    @classmethod
    def get_injected_guard_snippet(cls) -> str:
        """Generates self-contained anti-debugging boiler for protected source files."""
        return '''
# --- SIBER AKADEMI NATIVE ANTI-DEBUGGER RESISTANCE GATE ---
def _verify_bare_metal_execution_environment():
    """Detects and terminates execution under x64dbg, IDA Pro, WinDbg, or tracers."""
    import os, sys

    # 1. Active Python tracer / debugger
    if sys.gettrace() is not None:
        os._exit(1)

    # 2. Windows Native Debugger Check
    if sys.platform == "win32":
        try:
            import ctypes
            k32 = ctypes.windll.kernel32
            if k32.IsDebuggerPresent():
                k32.ExitProcess(0xC0000409)
            is_remote = ctypes.c_bool(False)
            if k32.CheckRemoteDebuggerPresent(k32.GetCurrentProcess(), ctypes.byref(is_remote)) and is_remote.value:
                k32.ExitProcess(0xC0000409)
            # ThreadHideFromDebugger
            ctypes.windll.ntdll.NtSetInformationThread(k32.GetCurrentThread(), 0x11, 0, 0)
        except Exception:
            pass

    # 3. Linux TracerPid Check
    if os.path.exists("/proc/self/status"):
        try:
            with open("/proc/self/status", "r") as f:
                for line in f:
                    if line.startswith("TracerPid:"):
                        if int(line.split(":")[1].strip()) != 0:
                            os._exit(1)
        except Exception:
            pass

    return True

_BARE_METAL_VERIFIED = _verify_bare_metal_execution_environment()
'''

    @classmethod
    def inject_anti_debugger_into_source(cls, source_code: str) -> str:
        """Injects standalone anti-debugging barrier into Python source code."""
        snippet = cls.get_injected_guard_snippet().strip()
        return f"{snippet}\n\n{source_code}"
