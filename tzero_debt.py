# -*- coding: utf-8 -*-
"""T-Zero Autonomous AST Code Health, Cognitive Complexity & Technical Debt Index.

Computes exact AST-based cognitive complexity, standard Maintainability Index (MI 0-100),
Halstead volume approximations, and financial technical debt refactoring estimates ($ / hours).

Capabilities:
- Cognitive Complexity analysis (Sonarqube-style nesting & branching weights).
- Cyclomatic Complexity & Maintainability Index (MI 0-100: Green / Yellow / Red).
- God Class & Long Method code smell detection.
- Debt Marker Tracker (TODO, FIXME, HACK, XXX, TEMP).
- Quantitative Refactoring Hours & Financial Debt ROI computation.
- 100% Offline, $0 cost, zero cloud dependencies (Python standard library only).

Author: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of T-Zero Context Architect v10.9.0 Master Edition.
"""

import ast
import json
import math
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


@dataclass
class FunctionHealth:
    name: str
    line_number: int
    lines_of_code: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    debt_hours: float
    issues: List[str] = field(default_factory=list)


@dataclass
class ClassHealth:
    name: str
    line_number: int
    method_count: int
    lines_of_code: int
    total_cognitive_complexity: int
    is_god_class: bool
    issues: List[str] = field(default_factory=list)


@dataclass
class FileHealthReport:
    file_path: str
    lines_of_code: int
    maintainability_index: float  # 0 to 100
    rating: str  # A (Good), B (Fair), C (Warning), D (Critical)
    cyclomatic_complexity: int
    cognitive_complexity: int
    debt_hours: float
    debt_cost_usd: float  # at $75/hr benchmark
    todo_count: int
    functions: List[FunctionHealth] = field(default_factory=list)
    classes: List[ClassHealth] = field(default_factory=list)
    debt_markers: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class WorkspaceHealthReport:
    workspace_root: str
    total_files: int
    total_lines_of_code: int
    average_maintainability_index: float
    overall_rating: str
    total_debt_hours: float
    total_debt_cost_usd: float
    total_todo_markers: int
    top_refactoring_hotspots: List[Dict[str, Any]] = field(default_factory=list)
    file_reports: List[FileHealthReport] = field(default_factory=list)


class ASTCognitiveComplexityVisitor(ast.NodeVisitor):
    """Calculates cognitive complexity based on nesting penalties and structural breaks."""

    def __init__(self):
        self.complexity = 0
        self.nesting_level = 0

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Don't increment nesting level for top-level function itself
        old_nesting = self.nesting_level
        for item in node.body:
            self.visit(item)
        self.nesting_level = old_nesting

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        old_nesting = self.nesting_level
        for item in node.body:
            self.visit(item)
        self.nesting_level = old_nesting

    def visit_If(self, node: ast.If):
        # +1 for if, plus nesting increment
        self.complexity += (1 + self.nesting_level)
        self.nesting_level += 1
        for item in node.body:
            self.visit(item)
        self.nesting_level -= 1

        if node.orelse:
            # If elif, handled by child If; else increment
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                self.visit(node.orelse[0])
            else:
                self.complexity += 1
                self.nesting_level += 1
                for item in node.orelse:
                    self.visit(item)
                self.nesting_level -= 1

    def visit_For(self, node: ast.For):
        self.complexity += (1 + self.nesting_level)
        self.nesting_level += 1
        for item in node.body:
            self.visit(item)
        self.nesting_level -= 1

    def visit_AsyncFor(self, node: ast.AsyncFor):
        self.complexity += (1 + self.nesting_level)
        self.nesting_level += 1
        for item in node.body:
            self.visit(item)
        self.nesting_level -= 1

    def visit_While(self, node: ast.While):
        self.complexity += (1 + self.nesting_level)
        self.nesting_level += 1
        for item in node.body:
            self.visit(item)
        self.nesting_level -= 1

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self.complexity += (1 + self.nesting_level)
        self.nesting_level += 1
        for item in node.body:
            self.visit(item)
        self.nesting_level -= 1

    def visit_BoolOp(self, node: ast.BoolOp):
        # Multiple binary boolean conditions (e.g. a and b and c -> +2)
        if len(node.values) > 1:
            self.complexity += (len(node.values) - 1)
        self.generic_visit(node)


class CodeHealthAnalyzer:
    """Analyzes AST maintainability index, cognitive complexity, and technical debt."""

    HOURLY_DEV_RATE = 75.0  # $75/hr engineering benchmark

    @classmethod
    def compute_cognitive_complexity(cls, node: ast.AST) -> int:
        visitor = ASTCognitiveComplexityVisitor()
        visitor.visit(node)
        return visitor.complexity

    @classmethod
    def compute_cyclomatic_complexity(cls, node: ast.AST) -> int:
        """Computes McCabe cyclomatic complexity: decision points + 1."""
        decisions = 0
        for sub in ast.walk(node):
            if isinstance(sub, (ast.If, ast.For, ast.While, ast.AsyncFor, ast.ExceptHandler, ast.With, ast.Assert)):
                decisions += 1
            elif isinstance(sub, ast.BoolOp):
                decisions += max(1, len(sub.values) - 1)
        return decisions + 1

    @classmethod
    def compute_maintainability_index(cls, code: str, cyclomatic: int) -> float:
        """Computes SEI/Microsoft Maintainability Index normalized to 0-100."""
        lines = [ln.strip() for ln in code.splitlines() if ln.strip() and not ln.strip().startswith("#")]
        loc = max(1, len(lines))
        # Estimate Halstead volume based on tokens and character volume
        halstead_vol = max(1.0, len(code) * math.log2(max(2, len(set(code.split())))))
        
        # Standard formula: 171 - 5.2 * ln(V) - 0.23 * CC - 16.2 * ln(LOC)
        raw_mi = 171.0 - (5.2 * math.log(halstead_vol)) - (0.23 * cyclomatic) - (16.2 * math.log(loc))
        normalized = max(0.0, min(100.0, (raw_mi * 100.0) / 171.0))
        return round(normalized, 1)

    @classmethod
    def extract_debt_markers(cls, code: str) -> List[Dict[str, Any]]:
        """Finds TODO, FIXME, HACK, XXX, TEMP debt comments."""
        markers = []
        pattern = re.compile(r"#\s*(TODO|FIXME|HACK|XXX|TEMP)[:\s]*(.*)", re.IGNORECASE)
        for idx, line in enumerate(code.splitlines(), start=1):
            match = pattern.search(line)
            if match:
                markers.append({
                    "line": idx,
                    "tag": match.group(1).upper(),
                    "text": match.group(2).strip()
                })
        return markers

    @classmethod
    def analyze_file(cls, file_path: str, code: Optional[str] = None) -> FileHealthReport:
        if code is None:
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    code = f.read()
            except Exception as e:
                return FileHealthReport(
                    file_path=file_path,
                    lines_of_code=0,
                    maintainability_index=100.0,
                    rating="A",
                    cyclomatic_complexity=1,
                    cognitive_complexity=0,
                    debt_hours=0.0,
                    debt_cost_usd=0.0,
                    todo_count=0
                )

        try:
            tree = ast.parse(code)
        except Exception:
            return FileHealthReport(
                file_path=file_path,
                lines_of_code=len(code.splitlines()),
                maintainability_index=0.0,
                rating="D",
                cyclomatic_complexity=10,
                cognitive_complexity=10,
                debt_hours=2.0,
                debt_cost_usd=150.0,
                todo_count=0
            )

        total_cc = cls.compute_cyclomatic_complexity(tree)
        total_cog = cls.compute_cognitive_complexity(tree)
        mi = cls.compute_maintainability_index(code, total_cc)
        debt_markers = cls.extract_debt_markers(code)

        fn_reports: List[FunctionHealth] = []
        cls_reports: List[ClassHealth] = []
        total_debt_hours = len(debt_markers) * 0.5  # 30m per TODO/FIXME

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fn_loc = (node.end_lineno - node.lineno + 1) if getattr(node, "end_lineno", None) else 10
                fn_cc = cls.compute_cyclomatic_complexity(node)
                fn_cog = cls.compute_cognitive_complexity(node)
                issues = []
                debt_h = 0.0

                if fn_cog > 15:
                    issues.append(f"High cognitive complexity ({fn_cog} > 15)")
                    debt_h += (fn_cog - 15) * 0.25

                if fn_loc > 50:
                    issues.append(f"Long function ({fn_loc} lines > 50)")
                    debt_h += 1.0

                if fn_cc > 10:
                    issues.append(f"High cyclomatic complexity ({fn_cc} > 10)")
                    debt_h += 0.5

                total_debt_hours += debt_h
                fn_reports.append(FunctionHealth(
                    name=node.name,
                    line_number=node.lineno,
                    lines_of_code=fn_loc,
                    cyclomatic_complexity=fn_cc,
                    cognitive_complexity=fn_cog,
                    debt_hours=round(debt_h, 2),
                    issues=issues
                ))

            elif isinstance(node, ast.ClassDef):
                cls_loc = (node.end_lineno - node.lineno + 1) if getattr(node, "end_lineno", None) else 20
                methods = [item for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))]
                m_count = len(methods)
                is_god = m_count > 12 or cls_loc > 300
                cls_cog = cls.compute_cognitive_complexity(node)
                issues = []
                debt_h = 0.0

                if is_god:
                    issues.append(f"God class detected ({m_count} methods, {cls_loc} lines)")
                    debt_h += 2.5

                total_debt_hours += debt_h
                cls_reports.append(ClassHealth(
                    name=node.name,
                    line_number=node.lineno,
                    method_count=m_count,
                    lines_of_code=cls_loc,
                    total_cognitive_complexity=cls_cog,
                    is_god_class=is_god,
                    issues=issues
                ))

        if mi >= 80:
            rating = "A"
        elif mi >= 65:
            rating = "B"
        elif mi >= 50:
            rating = "C"
        else:
            rating = "D"

        total_debt_hours = round(total_debt_hours, 2)
        debt_cost = round(total_debt_hours * cls.HOURLY_DEV_RATE, 2)

        return FileHealthReport(
            file_path=file_path,
            lines_of_code=len(code.splitlines()),
            maintainability_index=mi,
            rating=rating,
            cyclomatic_complexity=total_cc,
            cognitive_complexity=total_cog,
            debt_hours=total_debt_hours,
            debt_cost_usd=debt_cost,
            todo_count=len(debt_markers),
            functions=fn_reports,
            classes=cls_reports,
            debt_markers=debt_markers
        )

    @classmethod
    def analyze_workspace(cls, workspace_root: str = ".", max_files: int = 250) -> WorkspaceHealthReport:
        abs_root = os.path.abspath(workspace_root)
        reports: List[FileHealthReport] = []

        ignore_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build", ".pytest_cache"}

        for root, dirs, files in os.walk(abs_root):
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
            for f in files:
                if f.endswith(".py"):
                    rel_p = os.path.relpath(os.path.join(root, f), abs_root)
                    rep = cls.analyze_file(os.path.join(root, f))
                    rep.file_path = rel_p.replace("\\", "/")
                    reports.append(rep)
                    if len(reports) >= max_files:
                        break
            if len(reports) >= max_files:
                break

        if not reports:
            return WorkspaceHealthReport(
                workspace_root=workspace_root,
                total_files=0,
                total_lines_of_code=0,
                average_maintainability_index=100.0,
                overall_rating="A",
                total_debt_hours=0.0,
                total_debt_cost_usd=0.0,
                total_todo_markers=0
            )

        total_loc = sum(r.lines_of_code for r in reports)
        avg_mi = round(sum(r.maintainability_index for r in reports) / len(reports), 1)
        tot_hours = round(sum(r.debt_hours for r in reports), 1)
        tot_cost = round(tot_hours * cls.HOURLY_DEV_RATE, 2)
        tot_todos = sum(r.todo_count for r in reports)

        if avg_mi >= 80:
            overall_r = "A"
        elif avg_mi >= 65:
            overall_r = "B"
        elif avg_mi >= 50:
            overall_r = "C"
        else:
            overall_r = "D"

        # Find top 5 hotspots across files
        all_hotspots = []
        for r in reports:
            for fn in r.functions:
                if fn.issues:
                    all_hotspots.append({
                        "file": r.file_path,
                        "symbol": f"{fn.name}()",
                        "line": fn.line_number,
                        "cognitive": fn.cognitive_complexity,
                        "debt_hours": fn.debt_hours,
                        "issues": ", ".join(fn.issues)
                    })
            for cl in r.classes:
                if cl.is_god_class:
                    all_hotspots.append({
                        "file": r.file_path,
                        "symbol": f"class {cl.name}",
                        "line": cl.line_number,
                        "cognitive": cl.total_cognitive_complexity,
                        "debt_hours": 2.5,
                        "issues": ", ".join(cl.issues)
                    })

        all_hotspots.sort(key=lambda x: x["cognitive"], reverse=True)
        top_hotspots = all_hotspots[:5]

        return WorkspaceHealthReport(
            workspace_root=workspace_root,
            total_files=len(reports),
            total_lines_of_code=total_loc,
            average_maintainability_index=avg_mi,
            overall_rating=overall_r,
            total_debt_hours=tot_hours,
            total_debt_cost_usd=tot_cost,
            total_todo_markers=tot_todos,
            top_refactoring_hotspots=top_hotspots,
            file_reports=reports
        )

    @classmethod
    def format_markdown_report(cls, report: WorkspaceHealthReport) -> str:
        """Formats the technical debt index into an executive GitHub Markdown document."""
        badge = "🟢 Grade A (High Maintainability)" if report.overall_rating == "A" else (
            "🟡 Grade B (Moderate Maintainability)" if report.overall_rating == "B" else (
                "🟠 Grade C (Technical Debt Warning)" if report.overall_rating == "C" else "🔴 Grade D (Critical Refactor Required)"
            )
        )

        lines = [
            "# 🏥 T-Zero Code Health & Technical Debt Index",
            f"**Workspace:** `{os.path.abspath(report.workspace_root)}` | **Status:** {badge}",
            "",
            "## 📊 Executive Summary Metrics",
            f"- **Files Analyzed:** `{report.total_files}` modules (`{report.total_lines_of_code}` total lines of code)",
            f"- **Average Maintainability Index (MI):** `{report.average_maintainability_index} / 100` (Grade `{report.overall_rating}`)",
            f"- **Estimated Technical Debt:** `~{report.total_debt_hours} hours` (`${report.total_debt_cost_usd:,.2f}` refactor budget @ ${cls.HOURLY_DEV_RATE:.0f}/hr)",
            f"- **Lingering Debt Markers:** `{report.total_todo_markers}` (TODO / FIXME / HACK comments)",
            ""
        ]

        if report.top_refactoring_hotspots:
            lines.append("## 🎯 Top Priority Refactoring Hotspots")
            lines.append("| File | Symbol | Line | Cognitive Complexity | Debt Est. | Issues |")
            lines.append("| :--- | :--- | :---: | :---: | :---: | :--- |")
            for h in report.top_refactoring_hotspots:
                lines.append(f"| `{h['file']}` | `{h['symbol']}` | `{h['line']}` | `{h['cognitive']}` | `~{h['debt_hours']}h` | {h['issues']} |")
            lines.append("")

        lines.append("## 💡 T-Zero Autonomous Recommendations")
        if report.average_maintainability_index >= 80:
            lines.append("1. ✅ **Outstanding Architecture:** Codebase exhibits high modularity and low cognitive overhead.")
        else:
            lines.append("1. ⚠️ **Decompose God Classes & Functions:** Extract methods with cognitive complexity > 15 into dedicated helper modules.")
        lines.append("2. 🛡️ **Maintain Zero-Leak Security:** Keep all secret keys in environment variables.")
        lines.append("3. ⚡ **Run AST Mutation Tests:** Validate that your test suite actively detects logical mutations (`tzero mutate <file>`).")

        return "\n".join(lines).strip()

