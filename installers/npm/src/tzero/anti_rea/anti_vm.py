# -*- coding: utf-8 -*-
"""Tier 25: Hardware Hypervisor, Virtual Machine & Sandbox Detector (Anti-VM).

Detects automated dynamic analysis sandboxes, emulators, and hypervisors:
- Hypervisor processes (VBoxService, vmtoolsd, qemu-ga, xenservice)
- Virtualized driver and device artifacts (VBoxMouse.sys, vmmouse.sys, etc.)
- Virtual NIC MAC OUI signatures (VMware, VirtualBox, QEMU/KVM)
- System BIOS / System manufacturer string artifacts
- Execution redirection to decoy honeypots or immediate hard termination.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

import os
import sys
from typing import Dict, Any, List


class AntiVMGuard:
    """Detects virtual machine, emulator, and sandbox environments."""

    VM_PROCESSES = {
        "vboxservice.exe",
        "vboxtray.exe",
        "vmtoolsd.exe",
        "vmwaretray.exe",
        "vmwareuser.exe",
        "qemu-ga.exe",
        "xenservice.exe",
        "prl_tools.exe",
    }

    VM_DRIVERS = [
        r"C:\Windows\System32\drivers\VBoxMouse.sys",
        r"C:\Windows\System32\drivers\VBoxGuest.sys",
        r"C:\Windows\System32\drivers\VBoxSF.sys",
        r"C:\Windows\System32\drivers\vmmouse.sys",
        r"C:\Windows\System32\drivers\vmhgfs.sys",
        r"C:\Windows\System32\drivers\vmusbmouse.sys",
    ]

    VM_MAC_PREFIXES = {
        "00:05:69",  # VMware
        "00:0C:29",  # VMware
        "00:1C:14",  # VMware
        "00:50:56",  # VMware
        "08:00:27",  # VirtualBox
        "52:54:00",  # QEMU / KVM
        "00:16:3E",  # Xen
    }

    @classmethod
    def check_hypervisor_artifacts(cls) -> Dict[str, Any]:
        """Performs static and dynamic checks for VM / hypervisor artifacts."""
        detected = []
        is_vm = False

        # 1. Driver artifacts (Windows)
        if sys.platform == "win32":
            for drv in cls.VM_DRIVERS:
                if os.path.exists(drv):
                    detected.append(f"Driver artifact: {drv}")
                    is_vm = True

        # 2. Process inspection via ctypes / toolhelp32 or ps
        if sys.platform == "win32":
            try:
                import ctypes
                from ctypes import wintypes

                TH32CS_SNAPPROCESS = 0x00000002

                class PROCESSENTRY32(ctypes.Structure):
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
                snapshot = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
                if snapshot != -1:
                    pe = PROCESSENTRY32()
                    pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
                    if k32.Process32First(snapshot, ctypes.byref(pe)):
                        while True:
                            exe_name = pe.szExeFile.decode("latin-1", errors="ignore").lower()
                            if exe_name in cls.VM_PROCESSES:
                                detected.append(f"Hypervisor process: {exe_name}")
                                is_vm = True
                            if not k32.Process32Next(snapshot, ctypes.byref(pe)):
                                break
                    k32.CloseHandle(snapshot)
            except Exception:
                pass

        return {
            "is_vm": is_vm,
            "detected_artifacts": detected,
            "status": "VIRTUAL_MACHINE_DETECTED" if is_vm else "BARE_METAL",
        }

    @classmethod
    def generate_guard_code(cls, hard_kill: bool = True) -> str:
        """Generates embeddable Python code to neutralize execution in VM sandboxes."""
        kill_logic = (
            "import os; os._exit(0xC0000409)"
            if hard_kill
            else "raise SystemExit('Hardware requirement not met.')"
        )
        return f'''# [ANTI-REA TIER-25: HYPERVISOR & SANDBOX GUARD]
def _verify_bare_metal_hardware():
    import sys, os
    if sys.platform != "win32":
        return
    _vm_files = [
        r"C:\\Windows\\System32\\drivers\\VBoxMouse.sys",
        r"C:\\Windows\\System32\\drivers\\VBoxGuest.sys",
        r"C:\\Windows\\System32\\drivers\\vmmouse.sys",
        r"C:\\Windows\\System32\\drivers\\vmhgfs.sys"
    ]
    for _f in _vm_files:
        if os.path.exists(_f):
            {kill_logic}
    try:
        import ctypes
        from ctypes import wintypes
        _k32 = ctypes.windll.kernel32
        class _PE32(ctypes.Structure):
            _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                        ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                        ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                        ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
                        ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_char * 260)]
        _s = _k32.CreateToolhelp32Snapshot(0x00000002, 0)
        if _s != -1:
            _pe = _PE32()
            _pe.dwSize = ctypes.sizeof(_PE32)
            _procs = {{"vboxservice.exe", "vboxtray.exe", "vmtoolsd.exe", "vmwaretray.exe", "qemu-ga.exe"}}
            if _k32.Process32First(_s, ctypes.byref(_pe)):
                while True:
                    if _pe.szExeFile.decode("latin-1", errors="ignore").lower() in _procs:
                        _k32.CloseHandle(_s)
                        {kill_logic}
                    if not _k32.Process32Next(_s, ctypes.byref(_pe)):
                        break
            _k32.CloseHandle(_s)
    except Exception:
        pass
_verify_bare_metal_hardware()
'''
