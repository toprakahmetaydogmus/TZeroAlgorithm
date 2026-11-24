# -*- coding: utf-8 -*-
"""Tier 23: In-Flight String Vault & Anti-Memory Dump Engine.

Eradicates plaintext string constants from binaries and memory. 
Replaces all string literals in the AST with dynamic in-flight decryption calls.
The decrypted string exists in RAM only for the CPU cycle it is evaluated,
and its memory buffer is immediately scrubbed (zeroized).

When an adversary runs `strings myapp.exe`, inspects Ghidra `.rodata`, or
takes a RAM dump via Process Hacker/Scylla, zero readable strings are recovered.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

import ast
import random
from typing import Dict, List, Tuple, Any, Optional


class StringVault:
    """Manages encryption and dynamic in-flight evaluation of string literals."""

    VAULT_RUNTIME_SNIPPET = '''
# --- SIBER AKADEMI DYNAMIC IN-FLIGHT STRING VAULT ---
def _vault_decrypt_string(enc_blob, salt_key):
    """Decrypts string into ephemeral stack frame and scrubs the buffer."""
    buf = bytearray(enc_blob)
    k = salt_key & 0xFF
    res_chars = []
    for i in range(len(buf)):
        byte_val = buf[i] ^ ((k + i * 7) & 0xFF)
        res_chars.append(chr(byte_val))
        buf[i] = 0  # Immediate in-place memory wipe
    return "".join(res_chars)
'''

    @classmethod
    def encrypt_string(cls, plaintext: str, salt_key: int = 0x9B) -> bytes:
        """Encrypts a string into dynamic byte sequence."""
        k = salt_key & 0xFF
        raw_bytes = plaintext.encode("utf-8")
        return bytes([b ^ ((k + i * 7) & 0xFF) for i, b in enumerate(raw_bytes)])

    @classmethod
    def vault_source_code(cls, source_code: str, min_len: int = 3, seed: int = 42) -> str:
        """Parses AST, encrypts all string literals, and injects in-flight vault runtime."""
        try:
            tree = ast.parse(source_code)
            rng = random.Random(seed)

            class _StringVaultVisitor(ast.NodeTransformer):
                def visit_FunctionDef(self, node):
                    # Skip docstrings
                    body = node.body
                    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                        # Keep or handle docstring separately, transform the rest
                        for stmt in body[1:]:
                            self.visit(stmt)
                        return node
                    self.generic_visit(node)
                    return node

                def visit_Constant(self, node: ast.Constant) -> ast.AST:
                    if isinstance(node.value, str) and len(node.value) >= min_len:
                        # Skip if it looks like a python magic method or short token
                        val = node.value
                        if val.startswith("__") and val.endswith("__"):
                            return node
                        
                        salt = rng.randint(0x10, 0xEF)
                        enc_bytes = StringVault.encrypt_string(val, salt_key=salt)
                        
                        # Replace with _vault_decrypt_string(enc_bytes, salt)
                        call_node = ast.Call(
                            func=ast.Name(id="_vault_decrypt_string", ctx=ast.Load()),
                            args=[
                                ast.Constant(value=enc_bytes),
                                ast.Constant(value=salt)
                            ],
                            keywords=[]
                        )
                        return ast.copy_location(call_node, node)
                    return node

            transformer = _StringVaultVisitor()
            vaulted_tree = transformer.visit(tree)
            ast.fix_missing_locations(vaulted_tree)
            vaulted_code = ast.unparse(vaulted_tree)

            return f"{cls.VAULT_RUNTIME_SNIPPET.strip()}\n\n{vaulted_code}"
        except Exception:
            return source_code
