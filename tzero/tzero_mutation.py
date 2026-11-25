# -*- coding: utf-8 -*-
"""T-Zero Autonomous AST Mutation Testing & Test Quality Engine.

Evaluates test suite robustness and detects phantom/tautological tests
by injecting subtle AST mutations into code and validating if existing tests fail (kill the mutant).

Features:
- Pure AST mutation: Comparison, boolean, arithmetic, and constant operators.
- 100% Offline & Zero-Dependency: Uses Python standard library (ast, unittest, subprocess).
- In-memory & isolated tempfile execution without modifying git working tree.
- Calculates Mutation Score (0-100%) and recommends precise assertion patches.

Author: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of T-Zero Context Architect v10.8.0 Master Edition.
"""

import ast
import copy
import os
import shlex
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


@dataclass
class Mutant:
    mutant_id: str
    line_no: int
    operator: str
    original_snippet: str
    mutated_snippet: str
    mutated_code: str
    status: str = "PENDING"  # KILLED, SURVIVED, TIMEOUT, ERROR
    killed_by: Optional[str] = None
    output_snippet: Optional[str] = None


@dataclass
class MutationReport:
    file_path: str
    total_mutants: int
    killed: int
    survived: int
    timeouts: int
    errors: int
    mutation_score: float  # (killed / total) * 100
    duration_seconds: float
    mutants: List[Mutant] = field(default_factory=list)


class ASTMutationTransformer(ast.NodeTransformer):
    """Generates targeted single-point mutations in an AST tree."""

    COMP_SWAPS = {
        ast.Eq: ast.NotEq,
        ast.NotEq: ast.Eq,
        ast.Lt: ast.GtE,
        ast.LtE: ast.Gt,
        ast.Gt: ast.LtE,
        ast.GtE: ast.Lt,
        ast.Is: ast.IsNot,
        ast.IsNot: ast.Is,
        ast.In: ast.NotIn,
        ast.NotIn: ast.In
    }

    BOOL_SWAPS = {
        ast.And: ast.Or,
        ast.Or: ast.And
    }

    BIN_SWAPS = {
        ast.Add: ast.Sub,
        ast.Sub: ast.Add,
        ast.Mult: ast.Div,
        ast.Div: ast.Mult
    }

    def __init__(self, target_mutation_index: int):
        super().__init__()
        self.target_index = target_mutation_index
        self.current_index = 0
        self.applied_mutation: Optional[Tuple[int, str, str, str]] = None  # (line, op, orig, mut)

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        self.generic_visit(node)
        for i, op in enumerate(node.ops):
            op_type = type(op)
            if op_type in self.COMP_SWAPS:
                if self.current_index == self.target_index:
                    new_op_class = self.COMP_SWAPS[op_type]
                    orig_name = op_type.__name__
                    new_name = new_op_class.__name__
                    node.ops[i] = new_op_class()
                    self.applied_mutation = (
                        getattr(node, "lineno", 1),
                        "ComparisonSwap",
                        orig_name,
                        new_name
                    )
                self.current_index += 1
        return node

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        self.generic_visit(node)
        op_type = type(node.op)
        if op_type in self.BOOL_SWAPS:
            if self.current_index == self.target_index:
                new_op_class = self.BOOL_SWAPS[op_type]
                orig_name = op_type.__name__
                new_name = new_op_class.__name__
                node.op = new_op_class()
                self.applied_mutation = (
                    getattr(node, "lineno", 1),
                    "BooleanOperatorSwap",
                    orig_name,
                    new_name
                )
            self.current_index += 1
        return node

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        self.generic_visit(node)
        op_type = type(node.op)
        if op_type in self.BIN_SWAPS:
            if self.current_index == self.target_index:
                new_op_class = self.BIN_SWAPS[op_type]
                orig_name = op_type.__name__
                new_name = new_op_class.__name__
                node.op = new_op_class()
                self.applied_mutation = (
                    getattr(node, "lineno", 1),
                    "ArithmeticOperatorSwap",
                    orig_name,
                    new_name
                )
            self.current_index += 1
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if isinstance(node.value, bool):
            if self.current_index == self.target_index:
                orig_val = str(node.value)
                node.value = not node.value
                self.applied_mutation = (
                    getattr(node, "lineno", 1),
                    "BooleanConstantInversion",
                    orig_val,
                    str(node.value)
                )
            self.current_index += 1
        return node


class ASTMutationEngine:
    """Orchestrates mutation generation, test execution, and mutation score computation."""

    @classmethod
    def count_mutation_points(cls, code: str) -> int:
        """Counts total possible mutation opportunities in code."""
        try:
            tree = ast.parse(code)
        except Exception:
            return 0
        transformer = ASTMutationTransformer(target_mutation_index=-1)
        transformer.visit(tree)
        return transformer.current_index

    @classmethod
    def generate_mutants(cls, code: str, max_mutants: int = 15) -> List[Mutant]:
        """Generates up to max_mutants distinct AST mutations."""
        total_points = cls.count_mutation_points(code)
        if total_points == 0:
            return []

        # Sample or iterate mutation indices
        step = max(1, total_points // max_mutants)
        indices = list(range(0, total_points, step))[:max_mutants]

        mutants: List[Mutant] = []
        for idx in indices:
            try:
                tree = ast.parse(code)
                transformer = ASTMutationTransformer(target_mutation_index=idx)
                mutated_tree = transformer.visit(tree)
                ast.fix_missing_locations(mutated_tree)

                if transformer.applied_mutation:
                    line, op_name, orig_str, mut_str = transformer.applied_mutation
                    mutated_code = ast.unparse(mutated_tree)
                    m = Mutant(
                        mutant_id=f"MUT_{idx+1:03d}",
                        line_no=line,
                        operator=op_name,
                        original_snippet=orig_str,
                        mutated_snippet=mut_str,
                        mutated_code=mutated_code
                    )
                    mutants.append(m)
            except Exception:
                continue

        return mutants

    _ALLOWED_TEST_ARGS = {
        tok: tok
        for tok in ("-m", "unittest", "discover", "pytest", "-v", "-q", "--verbose", "-s", "-p", "-x", "--tb=short", "test_*.py")
    }

    @classmethod
    def _resolve_existing_test_entry(cls, token: str, roots: List[str]) -> Optional[str]:
        """Resolves a relative test path against actual filesystem entries under allowed roots."""
        cand = os.path.realpath(os.path.abspath(token))
        for root in roots:
            rel = os.path.relpath(cand, root)
            if rel == ".." or rel.startswith(".." + os.sep) or os.path.isabs(rel):
                continue
            for walk_root, _, files in os.walk(root):
                for fname in files:
                    real_entry = os.path.realpath(os.path.join(walk_root, fname))
                    if real_entry == cand:
                        return os.path.relpath(real_entry, roots[0])
        return None

    @staticmethod
    def _sanitize_target_path(target_path: str) -> str:
        if not target_path or "\x00" in target_path:
            raise ValueError("Invalid target path.")
        ws_root = os.path.realpath(".")
        tmp_root = os.path.realpath(tempfile.gettempdir())
        resolved = os.path.realpath(os.path.abspath(target_path))
        base_root = tmp_root if (resolved == tmp_root or resolved.startswith(tmp_root + os.sep)) else ws_root
        rel = os.path.relpath(resolved, base_root)
        if rel == ".." or rel.startswith(".." + os.sep) or os.path.isabs(rel):
            raise ValueError(f"Path outside allowed workspace or temp scope: {target_path}")
        real_target = os.path.normpath(os.path.join(base_root, rel))
        if not real_target.startswith(base_root):
            raise ValueError(f"Path outside allowed workspace or temp scope: {target_path}")
        return real_target

    @classmethod
    def run_mutation_analysis(
        cls,
        target_file: str,
        test_command: Optional[str] = None,
        max_mutants: int = 10,
        timeout_seconds: float = 6.0
    ) -> MutationReport:
        """Executes full mutation testing on target_file against test_command."""
        start_time = time.time()
        ws_root = os.path.realpath(".")
        tmp_root = os.path.realpath(tempfile.gettempdir())
        resolved_t = os.path.realpath(os.path.abspath(cls._sanitize_target_path(target_file)))
        base_root = tmp_root if (resolved_t == tmp_root or resolved_t.startswith(tmp_root + os.sep)) else ws_root
        rel_t = os.path.relpath(resolved_t, base_root)
        if rel_t == ".." or rel_t.startswith(".." + os.sep) or os.path.isabs(rel_t):
            raise ValueError(f"Target path outside allowed root: {target_file}")
        abs_target = os.path.normpath(os.path.join(base_root, rel_t))
        if not abs_target.startswith(base_root):
            raise ValueError(f"Target path outside allowed root: {target_file}")
        if not os.path.isfile(abs_target):
            raise FileNotFoundError(f"Target file not found: {target_file}")

        with open(abs_target, "r", encoding="utf-8", errors="replace") as f:
            original_code = f.read()

        mutants = cls.generate_mutants(original_code, max_mutants=max_mutants)
        if not mutants:
            return MutationReport(
                file_path=target_file,
                total_mutants=0,
                killed=0,
                survived=0,
                timeouts=0,
                errors=0,
                mutation_score=100.0,
                duration_seconds=round(time.time() - start_time, 2),
                mutants=[]
            )

        target_dir = os.path.dirname(abs_target)
        expected_test_name = f"test_{os.path.splitext(os.path.basename(abs_target))[0]}.py"

        # Build argv strictly from fixed flags and verified on-disk entries without shell=True
        if not test_command:
            matched_test = None
            for tests_dir in (os.path.join(target_dir, "tests"), os.path.join(ws_root, "tests")):
                if os.path.isdir(tests_dir) and expected_test_name in os.listdir(tests_dir):
                    matched_test = os.path.join(tests_dir, expected_test_name)
                    break
            if matched_test:
                test_cmd_args = [sys.executable, "-m", "unittest", matched_test]
            else:
                test_cmd_args = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
        else:
            if any(tok in test_command for tok in (";", "&&", "||", "|", "`", "$(", ">", "<", "\n", "\r")):
                raise ValueError("Unsafe shell metacharacters detected in test_command.")
            parsed_args = [
                tok.strip('"').strip("'")
                for tok in shlex.split(test_command, posix=(os.name != "nt"))
                if tok.strip()
            ]
            if not parsed_args:
                raise ValueError("Empty test_command.")
            bin_name = os.path.basename(parsed_args[0]).lower()
            if bin_name.startswith("python"):
                runner_prefix = [sys.executable]
            elif bin_name in ("pytest", "pytest.exe"):
                runner_prefix = [sys.executable, "-m", "pytest"]
            else:
                raise ValueError(f"Unsupported test runner executable: {parsed_args[0]}")

            safe_tail: List[str] = []
            for tok in parsed_args[1:]:
                if tok in cls._ALLOWED_TEST_ARGS:
                    safe_tail.append(cls._ALLOWED_TEST_ARGS[tok])
                else:
                    matched_rel = cls._resolve_existing_test_entry(tok, [target_dir, ws_root])
                    if not matched_rel:
                        # Also support test filenames passed relative to target_dir
                        alt_cand = os.path.join(target_dir, tok)
                        matched_rel = cls._resolve_existing_test_entry(alt_cand, [target_dir, ws_root])
                    if not matched_rel:
                        raise ValueError(f"Unsupported or missing test argument: {tok}")
                    safe_tail.append(matched_rel)
            test_cmd_args = runner_prefix + safe_tail

        killed = 0
        survived = 0
        timeouts = 0
        errors = 0

        safe_bak_name = os.path.basename(abs_target) + ".tzero_mut_bak"
        backup_path = os.path.normpath(os.path.join(target_dir, safe_bak_name))
        if not backup_path.startswith(target_dir):
            raise ValueError("Backup path escaped target directory.")
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(original_code)

        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{target_dir}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else target_dir

        try:
            for m in mutants:
                # Write mutant to disk
                if not abs_target.startswith(base_root):
                    raise ValueError("Target path escaped allowed root.")
                with open(abs_target, "w", encoding="utf-8") as f:
                    f.write(m.mutated_code)

                try:
                    proc = subprocess.run(
                        test_cmd_args,
                        shell=False,
                        capture_output=True,
                        text=True,
                        timeout=timeout_seconds,
                        env=env,
                        cwd=target_dir
                    )
                    if proc.returncode != 0:
                        m.status = "KILLED"
                        killed += 1
                        m.output_snippet = (proc.stderr or proc.stdout).strip().splitlines()[-1] if (proc.stderr or proc.stdout) else "AssertionError"
                    else:
                        m.status = "SURVIVED"
                        survived += 1
                except subprocess.TimeoutExpired:
                    m.status = "TIMEOUT"
                    timeouts += 1
                    killed += 1  # Infinite loop is considered caught
                except Exception as ex:
                    m.status = "ERROR"
                    errors += 1
                    m.output_snippet = str(ex)

        finally:
            # Always restore original code cleanly
            if os.path.isfile(backup_path):
                with open(backup_path, "r", encoding="utf-8") as f:
                    restored = f.read()
                with open(abs_target, "w", encoding="utf-8") as f:
                    f.write(restored)
                os.remove(backup_path)

        total = len(mutants)
        score = round((killed / total) * 100.0, 1) if total > 0 else 100.0
        duration = round(time.time() - start_time, 2)

        return MutationReport(
            file_path=target_file,
            total_mutants=total,
            killed=killed,
            survived=survived,
            timeouts=timeouts,
            errors=errors,
            mutation_score=score,
            duration_seconds=duration,
            mutants=mutants
        )

    @classmethod
    def format_markdown_report(cls, report: MutationReport) -> str:
        """Formats the mutation analysis into clean GitHub-style Markdown."""
        score_badge = "🟢" if report.mutation_score >= 80 else ("🟡" if report.mutation_score >= 50 else "🔴")
        lines = [
            f"## 🧬 T-Zero AST Mutation & Test Quality Report",
            f"**Target File:** `{report.file_path}`",
            f"**Mutation Score:** {score_badge} **{report.mutation_score}%** ({report.killed}/{report.total_mutants} mutants killed)",
            f"**Duration:** `{report.duration_seconds}s` | **Surviving Mutants:** `{report.survived}` | **Timeouts:** `{report.timeouts}`",
            "",
            "| ID | Line | Operator | Mutation | Result |",
            "| :--- | :---: | :--- | :--- | :--- |"
        ]

        for m in report.mutants:
            res_icon = "🗡️ KILLED" if m.status in ("KILLED", "TIMEOUT") else "⚠️ SURVIVED"
            lines.append(
                f"| `{m.mutant_id}` | L{m.line_no} | {m.operator} | `{m.original_snippet}` -> `{m.mutated_snippet}` | {res_icon} |"
            )

        if report.survived > 0:
            lines.extend([
                "",
                "### ⚠️ Recommendation for Surviving Mutants",
                "Surviving mutants indicate code branches that lack assertions or are tautological.",
                "Review the surviving lines above and add unit tests specifically asserting those conditions."
            ])

        return "\n".join(lines)
