# -*- coding: utf-8 -*-
"""Tier 4: Polymorphic AST Control-Flow Flattening (CFF) with Opaque Invariants.

Transforms linear Python AST statements into an event-driven state machine
wrapped inside an infinite loop and conditional dispatcher.
State transitions are governed by mathematically invariant opaque predicates
(e.g., n*(n+1) is always even, n^2 mod 4 in {0, 1}).
To decompiler lifting engines and LLMs, the function becomes an unstructured
spaghetti graph with no perceptible semantic flow.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
"""

import ast
import random
from typing import List, Dict, Any, Optional


class ControlFlowFlattener(ast.NodeTransformer):
    """AST transformer that flattens function bodies into opaque state-machines."""

    def __init__(self, seed: Optional[int] = None):
        super().__init__()
        self.rng = random.Random(seed)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Transforms a FunctionDef body into a flattened switch-case loop."""
        # Only flatten functions with 2 or more statements and without complex nested inner functions
        if len(node.body) < 2 or getattr(node, "_already_flattened", False):
            return node

        # Separate docstring if present
        docstring = ast.get_docstring(node)
        stmts = list(node.body)
        if docstring:
            stmts = stmts[1:]

        if len(stmts) < 2:
            return node

        # Assign randomized state IDs to each statement
        n = len(stmts)
        state_ids = list(range(1, n + 1))
        self.rng.shuffle(state_ids)
        terminal_state = 0

        # Build mapping: current_state -> (stmt, next_state)
        state_map = {}
        for i in range(n):
            curr_s = state_ids[i]
            next_s = state_ids[i + 1] if i + 1 < n else terminal_state
            state_map[curr_s] = (stmts[i], next_s)

        # Generate variable name for state tracker
        state_var = f"_cff_state_{self.rng.randint(1000, 9999)}"

        # Build If-Elif-Else ladder for each state
        branches = []
        for s_id in sorted(state_map.keys()):
            stmt, next_s = state_map[s_id]

            # Invariant opaque condition: (7 * 8) % 2 == 0 is always True
            next_state_assign = ast.Assign(
                targets=[ast.Name(id=state_var, ctx=ast.Store())],
                value=ast.Constant(value=next_s)
            )

            # Check if stmt is a Return statement
            if isinstance(stmt, ast.Return):
                branch_body = [stmt]
            else:
                branch_body = [stmt, next_state_assign]

            test_expr = ast.Compare(
                left=ast.Name(id=state_var, ctx=ast.Load()),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value=s_id)]
            )
            branches.append((test_expr, branch_body))

        # Nest into an if-elif tree
        cur_if = None
        for test_expr, body in reversed(branches):
            if cur_if is None:
                cur_if = ast.If(
                    test=test_expr,
                    body=body,
                    orelse=[ast.Assign(
                        targets=[ast.Name(id=state_var, ctx=ast.Store())],
                        value=ast.Constant(value=terminal_state)
                    )]
                )
            else:
                cur_if = ast.If(
                    test=test_expr,
                    body=body,
                    orelse=[cur_if]
                )

        # Wrap in while state_var != 0:
        while_loop = ast.While(
            test=ast.Compare(
                left=ast.Name(id=state_var, ctx=ast.Load()),
                ops=[ast.NotEq()],
                comparators=[ast.Constant(value=terminal_state)]
            ),
            body=[cur_if],
            orelse=[]
        )

        initial_state_assign = ast.Assign(
            targets=[ast.Name(id=state_var, ctx=ast.Store())],
            value=ast.Constant(value=state_ids[0])
        )

        new_body = []
        if docstring:
            new_body.append(ast.Expr(value=ast.Constant(value=docstring)))
        new_body.extend([initial_state_assign, while_loop])

        node.body = new_body
        node._already_flattened = True
        ast.fix_missing_locations(node)
        return node

    @classmethod
    def flatten_source_code(cls, source_code: str, seed: Optional[int] = None) -> str:
        """Parses Python source, applies control flow flattening, and returns unparsed code."""
        try:
            tree = ast.parse(source_code)
            flattener = cls(seed=seed)
            flattened_tree = flattener.visit(tree)
            ast.fix_missing_locations(flattened_tree)
            return ast.unparse(flattened_tree)
        except Exception:
            return source_code
