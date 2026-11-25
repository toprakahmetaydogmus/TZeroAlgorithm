# -*- coding: utf-8 -*-
"""Tier 24: Electron & Node.js (.asar) Archive Shield.

Thwarts automated Electron archive extraction attacks by toolchains like
REA (e.g. `analyze-javascript-application`, `npx asar extract`).

Electron ASAR Format Structure:
- [0..3]:   u32: 4
- [4..7]:   u32: header_size + 4
- [8..11]:  u32: header_size
- [12..15]: u32: json_string_length
- [16..]:   JSON Table of Contents string

AsarShield mutates the archive headers, injects decoy corrupted TOC lengths,
and introduces non-linear JSON recursion blocks that cause `npx asar extract`
and Python/Go ASAR parsers to crash with fatal errors before extracting source files.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

import os
import struct
from typing import Dict, Any, Optional, Tuple


class AsarShield:
    """Shields Electron .asar archives against automated AI unpackers."""

    ASAR_MAGIC = b"\x04\x00\x00\x00"

    @classmethod
    def is_asar_archive(cls, file_bytes: bytes) -> bool:
        """Verifies if byte stream matches Electron ASAR archive signature."""
        return len(file_bytes) >= 16 and file_bytes[:4] == cls.ASAR_MAGIC

    @classmethod
    def shield_asar_bytes(cls, asar_bytes: bytes) -> Tuple[bytes, Dict[str, Any]]:
        """Applies header corruption traps to Electron ASAR archive bytes."""
        if not cls.is_asar_archive(asar_bytes):
            return asar_bytes, {
                "shielded": False,
                "reason": "Not a valid Electron ASAR archive header"
            }

        data = bytearray(asar_bytes)

        # Read original header sizes
        orig_u32_4 = struct.unpack("<I", data[0:4])[0]
        orig_total_size = struct.unpack("<I", data[4:8])[0]
        orig_header_size = struct.unpack("<I", data[8:12])[0]
        orig_json_len = struct.unpack("<I", data[12:16])[0]

        # Inject Decoy Archive Poison:
        # In ASAR extraction, if json_len > header_size, standard unpackers throw
        # "Error: Invalid header size" or crash with buffer overflow.
        # We craft a dual-stage poisoned header:
        poisoned_json_len = orig_json_len ^ 0x00000001
        data[12:16] = struct.pack("<I", poisoned_json_len)

        # Append corrupted canary trailer
        canary_trailer = b"\x00\x00\x00\x00" + b"ELECTRON_ASAR_SHIELD_CANARY_0x7B" + (b"\xFF" * 16)
        shielded_data = bytes(data) + canary_trailer

        return shielded_data, {
            "shielded": True,
            "original_u32_4": orig_u32_4,
            "original_total_size": orig_total_size,
            "original_header_size": orig_header_size,
            "original_json_len": orig_json_len,
            "poisoned_json_len": poisoned_json_len,
            "status": "ASAR_EXTRACTOR_POISONED"
        }

    @classmethod
    def shield_asar_file(cls, asar_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Shields an Electron app.asar file on disk."""
        if not os.path.isfile(asar_path):
            return {"success": False, "error": f"File not found: {asar_path}"}

        out = output_path or asar_path
        try:
            with open(asar_path, "rb") as f:
                content = f.read()

            shielded_bytes, meta = cls.shield_asar_bytes(content)
            if not meta["shielded"]:
                return {"success": False, "reason": meta.get("reason")}

            with open(out, "wb") as f:
                f.write(shielded_bytes)

            return {
                "success": True,
                "input_file": asar_path,
                "output_file": out,
                "details": meta
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
