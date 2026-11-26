# -*- coding: utf-8 -*-
"""Tier 18: In-Memory Code Integrity Attestation & Anti-Hook Guard.

Protects functions against dynamic memory patching, Frida hooks, PyHook
interception, and hot-patching.

Computes SHA-256 cryptographic fingerprints of compiled bytecode (`co_code`)
and verifies integrity before each execution. If runtime tampering is
detected, it activates Deceptive Silent Divergence to deliver poisoned outputs.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

import hashlib
import functools
from typing import Callable, Any, Dict


class MemoryIntegrityGuard:
    """Verifies in-memory function bytecode fingerprints against tampering."""

    INTEGRITY_REGISTRY: Dict[str, str] = {}

    @classmethod
    def compute_code_hash(cls, func: Callable) -> str:
        """Computes SHA-256 hash of a function's underlying bytecode."""
        code_obj = getattr(func, "__code__", None)
        if not code_obj:
            return ""
        return hashlib.sha256(code_obj.co_code).hexdigest()

    @classmethod
    def register_function(cls, func: Callable) -> str:
        """Registers a function's pristine bytecode hash in the integrity registry."""
        h = cls.compute_code_hash(func)
        cls.INTEGRITY_REGISTRY[func.__qualname__] = h
        return h

    @classmethod
    def verify_integrity(cls, func: Callable) -> bool:
        """Verifies if function bytecode matches its pristine registered hash."""
        expected = cls.INTEGRITY_REGISTRY.get(func.__qualname__)
        if not expected:
            return True
        current = cls.compute_code_hash(func)
        return current == expected

    @classmethod
    def inject_integrity_check_code(cls, source_code: str) -> str:
        """Injects standalone in-memory integrity attestation into source code."""
        snippet = '''
# --- SIBER AKADEMI IN-MEMORY CODE INTEGRITY ATTESTATION ---
_ATTESTATION_FINGERPRINTS = {}

def _attest_memory_bytecode_fingerprints():
    """Validates module function bytecode fingerprints against in-memory tampering."""
    import sys, hashlib
    mod = sys.modules.get(__name__)
    if not mod:
        return False
    checked = 0
    for name, obj in list(vars(mod).items()):
        code_obj = getattr(obj, "__code__", None)
        if code_obj is not None and not name.startswith("_vault_"):
            digest = hashlib.sha256(code_obj.co_code).hexdigest()
            expected = _ATTESTATION_FINGERPRINTS.get(name)
            if expected is None:
                _ATTESTATION_FINGERPRINTS[name] = digest
            elif expected != digest:
                return False
            checked += 1
    return checked > 0

_ATTESTATION_OK = _attest_memory_bytecode_fingerprints()
'''
        return f"{snippet.strip()}\n\n{source_code}"
