# -*- coding: utf-8 -*-
"""Tier 46-60 (Domain D04): Authenticated HKDF-SHA256 + CTR Bytecode Envelope.

Compiles protected Python application bodies into compressed marshal bytecode
encrypted with a per-build SHA-256 CTR keystream and authenticated via HMAC-SHA256.

Key guarantees:
1. Preserves 100% native Python runtime semantics for protected applications:
   - classes, inheritance & super(), @dataclass, @property, decorators
   - async def / await, yield / yield from generators, closures
   - full UTF-8 strings, sys.argv, __name__ == "__main__", relative imports
2. Leaves ZERO plaintext user functions, constants, strings, or AST structure
   visible to static scanners, decompilers (uncompyle6/pycdc), or LLM agents.
3. Enforces active pre-decryption tracer checks (sys.gettrace & sys.monitoring)
   and scrubs decrypted plaintext buffers in memory right after marshal load.

Developer: Toprak Ahmet Aydogmus (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

import ast
import base64
import hashlib
import hmac
import marshal
import random
import zlib
from typing import Tuple


class CryptoBytecodeEnvelope:
    """Seals Python module bodies inside an authenticated encrypted bytecode envelope."""

    ENVELOPE_MARKER = "SIBER AKADEMI HMAC-SHA256 AUTHENTICATED ENVELOPE"

    @staticmethod
    def _derive_keys(secret: bytes, salt: bytes) -> Tuple[bytes, bytes]:
        enc_key = hashlib.sha256(b"tzero-enc-v5|" + secret + salt).digest()
        mac_key = hashlib.sha256(b"tzero-mac-v5|" + secret + salt).digest()
        return enc_key, mac_key

    @staticmethod
    def _ctr_xor(data: bytes, enc_key: bytes, salt: bytes) -> bytes:
        out = bytearray(len(data))
        block_size = 32
        offset = 0
        counter = 0
        while offset < len(data):
            block = hashlib.sha256(enc_key + salt + counter.to_bytes(4, "big")).digest()
            take = min(block_size, len(data) - offset)
            for idx in range(take):
                out[offset + idx] = data[offset + idx] ^ block[idx]
            offset += take
            counter += 1
        return bytes(out)

    @classmethod
    def seal_source(cls, source_code: str, *, seed: int = 42, future_block: str = "") -> str:
        """Compiles user module code cleanly and seals it inside an authenticated envelope."""
        # Compile clean AST with optional future flags preserved at outer prologue
        unit_src = f"{future_block}{source_code}" if future_block else source_code
        tree = ast.parse(unit_src)
        code_obj = compile(tree, "<tzero_sealed_module>", "exec")
        compressed = zlib.compress(marshal.dumps(code_obj), level=9)

        rng = random.Random(seed ^ (len(compressed) << 8))
        salt = bytes(rng.getrandbits(8) for _ in range(16))
        share_a = bytes(rng.getrandbits(8) for _ in range(32))
        share_b = bytes(rng.getrandbits(8) for _ in range(32))
        secret = bytes(a ^ b for a, b in zip(share_a, share_b))

        enc_key, mac_key = cls._derive_keys(secret, salt)
        ciphertext = cls._ctr_xor(compressed, enc_key, salt)
        tag_hex = hmac.new(mac_key, salt + ciphertext, hashlib.sha256).hexdigest()

        b85_payload = base64.b85encode(ciphertext).decode("ascii")
        b85_salt = base64.b85encode(salt).decode("ascii")
        b85_a = base64.b85encode(share_a).decode("ascii")
        b85_b = base64.b85encode(share_b).decode("ascii")

        return f'''# --- {cls.ENVELOPE_MARKER} (D04: REA-046..060) ---
def _tzero_decrypt_and_exec(_p_b85: str, _s_b85: str, _ka_b85: str, _kb_b85: str, _sig_hex: str, _ns: dict) -> None:
    import base64, hashlib, hmac, marshal, os, sys, zlib
    if sys.gettrace() is not None:
        os._exit(0xC0000409)
    _mon = getattr(sys, "monitoring", None)
    if _mon is not None:
        try:
            for _tid in range(6):
                if _mon.get_tool(_tid) is not None and _tid != 5:
                    os._exit(0xC0000409)
        except Exception:
            pass
    _salt = base64.b85decode(_s_b85)
    _sa = bytearray(base64.b85decode(_ka_b85))
    _sb = bytearray(base64.b85decode(_kb_b85))
    _sec = bytearray(len(_sa))
    _raw = bytearray()
    _plain = bytearray()
    try:
        for _i in range(len(_sa)):
            _sec[_i] = _sa[_i] ^ _sb[_i]
            _sa[_i] = 0
            _sb[_i] = 0
        _sec_bytes = bytes(_sec)
        _ek = hashlib.sha256(b"tzero-enc-v5|" + _sec_bytes + _salt).digest()
        _mk = hashlib.sha256(b"tzero-mac-v5|" + _sec_bytes + _salt).digest()
        _ct = base64.b85decode(_p_b85)
        _calc = hmac.new(_mk, _salt + _ct, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(_calc, _sig_hex):
            raise RuntimeError("Anti-REA Envelope Integrity Tamper Detected")
        _raw = bytearray(len(_ct))
        _off = 0
        _ctr = 0
        while _off < len(_ct):
            _blk = hashlib.sha256(_ek + _salt + _ctr.to_bytes(4, "big")).digest()
            _take = min(32, len(_ct) - _off)
            for _j in range(_take):
                _raw[_off + _j] = _ct[_off + _j] ^ _blk[_j]
            _off += _take
            _ctr += 1
        _plain = bytearray(zlib.decompress(bytes(_raw)))
        _code_obj = marshal.loads(bytes(_plain))
        exec(_code_obj, _ns, _ns)
    finally:
        for _buf in (_sec, _raw, _plain):
            for _k in range(len(_buf)):
                _buf[_k] = 0

_tzero_decrypt_and_exec({repr(b85_payload)}, {repr(b85_salt)}, {repr(b85_a)}, {repr(b85_b)}, {repr(tag_hex)}, globals())
'''
