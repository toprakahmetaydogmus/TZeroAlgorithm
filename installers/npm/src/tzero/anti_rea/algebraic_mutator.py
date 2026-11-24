# -*- coding: utf-8 -*-
"""Tier 17: AST Algebraic Identity & Polymorphic Mutator.

Transforms elementary arithmetic expressions (+, -, *, <<) into complex
Boolean Ring identities (Mixed Boolean-Arithmetic / MBA). 

For example:
    x + y  ==>  (x ^ y) + 2 * (x & y)
    x - y  ==>  (x ^ y) - 2 * ((~x) & y)
    x * 2  ==>  (x << 1)
    x * 4  ==>  (x << 2)

This destroys pattern-matching heuristics in decompilers (Ghidra, IDA, pycdc)
and forces LLMs to solve exponential symbolic constraint systems to infer
the original business equations.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

import ast
from typing import Optional


class AlgebraicIdentityTransformer(ast.NodeTransformer):
    """AST transformer converting elementary arithmetic into MBA representations."""

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        self.generic_visit(node)

        # 1. Transform addition: x + y  ==>  (x ^ y) + 2 * (x & y)
        if isinstance(node.op, ast.Add):
            # Only transform if operands are variables or integers (avoid string concatenation)
            if self._is_numeric_or_variable(node.left) and self._is_numeric_or_variable(node.right):
                xor_part = ast.BinOp(left=node.left, op=ast.BitXor(), right=node.right)
                and_part = ast.BinOp(left=node.left, op=ast.BitAnd(), right=node.right)
                two_times_and = ast.BinOp(left=ast.Constant(value=2), op=ast.Mult(), right=and_part)
                return ast.BinOp(left=xor_part, op=ast.Add(), right=two_times_and)

        # 2. Transform subtraction: x - y  ==>  (x ^ y) - 2 * ((~x) & y)
        elif isinstance(node.op, ast.Sub):
            if self._is_numeric_or_variable(node.left) and self._is_numeric_or_variable(node.right):
                xor_part = ast.BinOp(left=node.left, op=ast.BitXor(), right=node.right)
                inv_left = ast.UnaryOp(op=ast.Invert(), operand=node.left)
                and_part = ast.BinOp(left=inv_left, op=ast.BitAnd(), right=node.right)
                two_times = ast.BinOp(left=ast.Constant(value=2), op=ast.Mult(), right=and_part)
                return ast.BinOp(left=xor_part, op=ast.Sub(), right=two_times)

        # 3. Transform multiplication by 2, 4, 8: x * 2  ==>  x << 1
        elif isinstance(node.op, ast.Mult):
            if isinstance(node.right, ast.Constant) and node.right.value in (2, 4, 8):
                shift = {2: 1, 4: 2, 8: 3}[node.right.value]
                return ast.BinOp(left=node.left, op=ast.LShift(), right=ast.Constant(value=shift))
            elif isinstance(node.left, ast.Constant) and node.left.value in (2, 4, 8):
                shift = {2: 1, 4: 2, 8: 3}[node.left.value]
                return ast.BinOp(left=node.right, op=ast.LShift(), right=ast.Constant(value=shift))

        return node

    def _is_numeric_or_variable(self, node: ast.AST) -> bool:
        """Determines if node is suitable for MBA arithmetic mutation."""
        if isinstance(node, ast.Name):
            return True
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return True
        if isinstance(node, ast.BinOp):
            return True
        return False


class AlgebraicMutator:
    """Public interface for applying Mixed Boolean-Arithmetic (MBA) AST mutations."""

    @classmethod
    def mutate_source_code(cls, source_code: str) -> str:
        """Applies algebraic identity mutation across all functions in source code."""
        try:
            tree = ast.parse(source_code)
            transformer = AlgebraicIdentityTransformer()
            mutated_tree = transformer.visit(tree)
            ast.fix_missing_locations(mutated_tree)
            return ast.unparse(mutated_tree)
        except Exception:
            # Fallback to unmodified code on unparseable edge cases
            return source_code
