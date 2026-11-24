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
    def shield_binary_bytes(cls, binary_data: bytes) -> Tuple[bytes, Dict[str, Any]]:
        """Applies header mutation and decoy cookie injection to raw binary bytes."""
        offsets = cls.scan_cookie(binary_data)
        if not offsets:
            return binary_data, {
                "shielded": False,
                "reason": "PyInstaller cookie not found (pure native or already shielded)"
            }

        data_array = bytearray(binary_data)
        mutations_applied = 0

        # For each cookie found, inject a decoy cookie with corrupted TOC length earlier in padding
        for cookie_offset in offsets:
            # Check if there is space in preceding padding (at least 64 bytes)
            padding_start = max(0, cookie_offset - 128)
            padding_chunk = data_array[padding_start:cookie_offset]
            
            # If there's an all-zero null padding region, insert decoy corrupted cookie
            zero_idx = padding_chunk.find(b"\x00" * 32)
            decoy_offset = padding_start + zero_idx if zero_idx != -1 else (padding_start if len(padding_chunk) >= 32 else -1)
            if decoy_offset != -1:
                # Write decoy cookie
                data_array[decoy_offset:decoy_offset + PYINSTALLER_COOKIE_LEN] = PYINSTALLER_COOKIE
                # Write a corrupted TOC length (0xFFFFFFFF) and negative package count immediately following
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
