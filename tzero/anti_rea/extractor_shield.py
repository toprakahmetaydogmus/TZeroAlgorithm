# -*- coding: utf-8 -*-
"""Tier 1: Extractor & Archive Poisoning (Anti-pyinstxtractor).

Target: Automated PyInstaller archive extractors used by REA and AI agents.
PyInstaller archives contain a table of contents (TOC) and magic cookie
('MEI\\014\\013\\012\\013\\016'). While standard extractors read sequentially
from the cookie forward, the native C bootloader reads archive offsets
from the End of File (EOF) trailer struct.

This module mutates non-essential archive header bytes and injects decoy
cookies so that pyinstxtractor raises IndexError or ValueError while the
executable runs without issue.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
"""

import os
import struct
from typing import Dict, Any, List, Tuple, Optional


PYINSTALLER_COOKIE = b"MEI\014\013\012\013\016"
PYINSTALLER_COOKIE_LEN = len(PYINSTALLER_COOKIE)


class ExtractorShield:
    """Hardens executables against automated PyInstaller extraction scripts."""

    @classmethod
    def scan_cookie(cls, binary_data: bytes) -> List[int]:
        """Locates all occurrences of PyInstaller cookie in binary data."""
        offsets = []
        pos = 0
        while True:
            idx = binary_data.find(PYINSTALLER_COOKIE, pos)
            if idx == -1:
                break
            offsets.append(idx)
            pos = idx + 1
        return offsets

    @classmethod
    def _find_pe_slack_offset(cls, data_array: bytearray, max_offset: int) -> int:
        """Locates an unused all-zero PE section alignment cave before the CArchive overlay."""
        if len(data_array) < 0x100 or data_array[:2] != b"MZ":
            return -1
        try:
            e_lfanew = struct.unpack_from("<I", data_array, 0x3C)[0]
            if e_lfanew + 24 > len(data_array) or data_array[e_lfanew:e_lfanew + 4] != b"PE\x00\x00":
                return -1
            num_sec = struct.unpack_from("<H", data_array, e_lfanew + 6)[0]
            opt_size = struct.unpack_from("<H", data_array, e_lfanew + 20)[0]
            sec_off = e_lfanew + 24 + opt_size
            if sec_off + num_sec * 40 > len(data_array):
                return -1
            preferred = (".rdata", ".rsrc", ".pdata", ".fptable")
            candidates = []
            for i in range(num_sec):
                s = sec_off + i * 40
                name = data_array[s:s + 8].rstrip(b"\x00").decode("ascii", errors="ignore")
                vsize, _vaddr, rsize, rptr = struct.unpack_from("<IIII", data_array, s + 8)
                if name in preferred and rsize > vsize + 32:
                    slack_start = rptr + ((vsize + 15) & ~15)
                    slack_end = min(rptr + rsize, max_offset)
                    if slack_end - slack_start >= 32:
                        candidates.append((slack_start, slack_end))
            for slack_start, slack_end in candidates:
                zero_idx = data_array[slack_start:slack_end].find(b"\x00" * 32)
                if zero_idx != -1:
                    return slack_start + zero_idx
        except Exception:
            return -1
        return -1

    @classmethod
    def shield_binary_bytes(cls, binary_data: bytes) -> Tuple[bytes, Dict[str, Any]]:
        """Applies non-destructive decoy cookie injection strictly into null-byte caves."""
        offsets = cls.scan_cookie(binary_data)
        if not offsets:
            return binary_data, {
                "shielded": False,
                "reason": "PyInstaller cookie not found (pure native or already shielded)"
            }

        data_array = bytearray(binary_data)
        mutations_applied = 0

        for cookie_offset in offsets:
            padding_start = max(0, cookie_offset - 128)
            padding_chunk = data_array[padding_start:cookie_offset]

            # 1. Inject only if a genuine 32-byte null region exists before the cookie (e.g. mock/aligned cave)
            zero_idx = padding_chunk.find(b"\x00" * 32)
            decoy_offset = padding_start + zero_idx if zero_idx != -1 else -1

            # 2. For real PyInstaller PE executables, use unmapped .rdata/.rsrc section alignment slack
            if decoy_offset == -1 and len(data_array) >= 0x100 and data_array[:2] == b"MZ":
                pkg_start = cookie_offset
                if cookie_offset + 12 <= len(data_array):
                    try:
                        pkg_len = struct.unpack_from(">I", data_array, cookie_offset + 8)[0]
                        trailer_end = min(len(data_array), cookie_offset + 88)
                        if 0 < pkg_len <= trailer_end:
                            pkg_start = trailer_end - pkg_len
                    except Exception:
                        pass
                decoy_offset = cls._find_pe_slack_offset(data_array, min(cookie_offset, pkg_start))

            if decoy_offset != -1 and decoy_offset + PYINSTALLER_COOKIE_LEN + 8 <= cookie_offset:
                data_array[decoy_offset:decoy_offset + PYINSTALLER_COOKIE_LEN] = PYINSTALLER_COOKIE
                corrupted_header = struct.pack(">II", 0xFFFFFFFF, 0x00000000)
                data_array[decoy_offset + PYINSTALLER_COOKIE_LEN:decoy_offset + PYINSTALLER_COOKIE_LEN + 8] = corrupted_header
                mutations_applied += 1

        return bytes(data_array), {
            "shielded": mutations_applied > 0,
            "cookies_found": len(offsets),
            "decoy_traps_injected": mutations_applied,
            "status": "EXTRACTOR_POISONED" if mutations_applied > 0 else "SKIPPED"
        }

    @classmethod
    def shield_file(cls, file_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Shields a compiled executable file on disk against pyinstxtractor."""
        if not os.path.isfile(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        with open(file_path, "rb") as f:
            content = f.read()

        shielded_content, meta = cls.shield_binary_bytes(content)
        target_path = output_path or file_path

        if meta.get("shielded"):
            with open(target_path, "wb") as f:
                f.write(shielded_content)
            meta["output_path"] = target_path
            meta["success"] = True
            return meta

        return {"success": False, "reason": meta.get("reason", "No mutations applied")}


# Type alias helper
List_Int = list
