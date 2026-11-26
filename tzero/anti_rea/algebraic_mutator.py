# -*- coding: utf-8 -*-
"""Tier 76-90 (Domain D06): Type-Safe AST Algebraic Identity & MBA Mutator.

Transforms integer arithmetic expressions (+, -, *) into Mixed Boolean-Arithmetic
(MBA) equivalents while guaranteeing 100% runtime compatibility for strings, floats,
lists, booleans, and custom objects via strict runtime type guards:
    int + int  ==>  (x ^ y) + ((x & y) << 1)
    int - int  ==>  (x ^ y) - (((~x) & y) << 1)
    int * 2    ==>  (x << 1)

Developer: Toprak Ahmet Aydogmus (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

import ast


_MBA_RUNTIME_HEADER = '''# --- SIBER AKADEMI TYPE-SAFE MBA ARITHMETIC ENGINE (D06: REA-076..090) ---
def _tzero_mba_add(_a, _b):
    if type(_a) is int and type(_b) is int:
        return (_a ^ _b) + ((_a & _b) << 1)
    return _a + _b

def _tzero_mba_sub(_a, _b):
    if type(_a) is int and type(_b) is int:
        return (_a ^ _b) - (((~_a) & _b) << 1)
    return _a - _b
'''


class AlgebraicIdentityTransformer(ast.NodeTransformer):
    """AST transformer converting pure/typed arithmetic into MBA representations safely."""

    @staticmethod
    def _is_pure_int_const(node: ast.AST) -> bool:
        return isinstance(node, ast.Constant) and type(node.value) is int

    @staticmethod
    def _is_eligible_operand(node: ast.AST) -> bool:
        return isinstance(node, (ast.Name, ast.BinOp, ast.Call)) or (
            isinstance(node, ast.Constant) and type(node.value) is int
        )

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        self.generic_visit(node)

        if isinstance(node.op, ast.Add):
            if self._is_pure_int_const(node.left) and self._is_pure_int_const(node.right):
                xor_part = ast.BinOp(left=node.left, op=ast.BitXor(), right=node.right)
                and_part = ast.BinOp(left=node.left, op=ast.BitAnd(), right=node.right)
                shifted = ast.BinOp(left=and_part, op=ast.LShift(), right=ast.Constant(value=1))
                return ast.copy_location(ast.BinOp(left=xor_part, op=ast.Add(), right=shifted), node)
            if self._is_eligible_operand(node.left) and self._is_eligible_operand(node.right):
                return ast.copy_location(
                    ast.Call(
                        func=ast.Name(id="_tzero_mba_add", ctx=ast.Load()),
                        args=[node.left, node.right],
                        keywords=[],
                    ),
                    node,
                )

        elif isinstance(node.op, ast.Sub):
            if self._is_pure_int_const(node.left) and self._is_pure_int_const(node.right):
                xor_part = ast.BinOp(left=node.left, op=ast.BitXor(), right=node.right)
                inv_left = ast.UnaryOp(op=ast.Invert(), operand=node.left)
                and_part = ast.BinOp(left=inv_left, op=ast.BitAnd(), right=node.right)
                shifted = ast.BinOp(left=and_part, op=ast.LShift(), right=ast.Constant(value=1))
                return ast.copy_location(ast.BinOp(left=xor_part, op=ast.Sub(), right=shifted), node)
            if self._is_eligible_operand(node.left) and self._is_eligible_operand(node.right):
                return ast.copy_location(
                    ast.Call(
                        func=ast.Name(id="_tzero_mba_sub", ctx=ast.Load()),
                        args=[node.left, node.right],
                        keywords=[],
                    ),
                    node,
                )

        elif isinstance(node.op, ast.Mult):
            # Shift optimization ONLY when one operand is 2/4/8 AND the other is provably an int literal
            if self._is_pure_int_const(node.right) and node.right.value in (2, 4, 8) and self._is_pure_int_const(node.left):
                shift = {2: 1, 4: 2, 8: 3}[node.right.value]
                return ast.copy_location(ast.BinOp(left=node.left, op=ast.LShift(), right=ast.Constant(value=shift)), node)
            if self._is_pure_int_const(node.left) and node.left.value in (2, 4, 8) and self._is_pure_int_const(node.right):
                shift = {2: 1, 4: 2, 8: 3}[node.left.value]
                return ast.copy_location(ast.BinOp(left=node.right, op=ast.LShift(), right=ast.Constant(value=shift)), node)

        return node


class AlgebraicMutator:
    """Public interface for applying type-safe Mixed Boolean-Arithmetic (MBA) AST mutations."""

    @classmethod
    def mutate_source_code(cls, source_code: str) -> str:
        """Applies type-safe algebraic identity mutation across expressions cleanly."""
        try:
            tree = ast.parse(source_code)
            transformer = AlgebraicIdentityTransformer()
            mutated_tree = transformer.visit(tree)
            ast.fix_missing_locations(mutated_tree)
            mutated = ast.unparse(mutated_tree)
            return f"{_MBA_RUNTIME_HEADER}\n{mutated}"
        except Exception:
            return source_code
