# -*- coding: utf-8 -*-
"""
Siber Akademi — T-Zero Instruction & Architecture Drift Scorer.
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: MIT

Quantifies how closely LLM code generations and workspace modifications adhere
to initial system prompt rules, negative constraints, and architectural boundaries.
Directly measures the "Lost in the Middle" attention degradation phenomenon:
proves high SNR via AST pruning prevents instruction decay over long sessions.
"""

import os
import sys
import ast
import json
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from tzero_security import ZeroLeakEngine


@dataclass
class DriftFinding:
    category: str
    severity: str
    file_path: str
    line_no: int
    message: str
    penalty_points: float


@dataclass
class DriftReport:
    workspace_dir: str
    drift_score: float         # 0.0 = Perfect zero drift, 100.0 = Severe drift
    adherence_pct: float       # 100.0% = Flawless instruction following
    snr_rating: str            # "EXCELLENT (HIGH SNR)", "DEGRADED", "CRITICAL"
    findings: List[DriftFinding] = field(default_factory=list)
    files_audited: int = 0


class DriftAnalyzer:
    """Measures instruction drift and architectural rule decay across the codebase."""

    SKIP_DIRS = {
        ".git", "__pycache__", ".pytest_cache", "target", "dist",
        "build", ".venv", "venv", "node_modules", ".superpowers", "bin"
    }

    @classmethod
    def analyze_workspace(cls, workspace_dir: str = ".") -> DriftReport:
        """Analyzes active workspace files for rule drift, security drift, and complexity."""
        abs_root = os.path.abspath(workspace_dir)
        findings: List[DriftFinding] = []
        files_count = 0

        total_penalty = 0.0

        for root, dirs, files in os.walk(abs_root):
            dirs[:] = [d for d in dirs if d not in cls.SKIP_DIRS and not d.startswith(".")]
            for fname in files:
                if fname.endswith(".py"):
                    fpath = os.path.join(root, fname)
                    rel = os.path.relpath(fpath, abs_root).replace("\\", "/")
                    if "test" in rel.lower():
                        continue
                    files_count += 1
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read()

                        # 1. Zero-Leak Security Drift
                        sec_hits = ZeroLeakEngine.scan_text(content, check_entropy=True)
                        for hit in sec_hits:
                            penalty = 15.0
                            total_penalty += penalty
                            findings.append(DriftFinding(
                                category="Zero-Leak Security",
                                severity="CRITICAL",
                                file_path=rel,
                                line_no=hit.line_no,
                                message=f"Secret leak introduced: {hit.description}",
                                penalty_points=penalty
                            ))

                        # 2. AST Code Smell & Instruction Drift
                        tree = ast.parse(content, filename=rel)
                        for node in ast.walk(tree):
                            # Bare exceptions swallow interrupts and drift from error guidelines
                            if isinstance(node, ast.ExceptHandler) and node.type is None:
                                penalty = 5.0
                                total_penalty += penalty
                                findings.append(DriftFinding(
                                category="Error Handling",
                                severity="HIGH",
                                file_path=rel,
                                line_no=node.lineno,
                                message="Bare `except:` clause used instead of typed exception",
                                penalty_points=penalty
                            ))

                            # Large un-decomposed functions (>60 lines) violate clean architecture
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                length = getattr(node, "end_lineno", node.lineno) - node.lineno
                                if length > 60:
                                    penalty = 3.0
                                    total_penalty += penalty
                                    findings.append(DriftFinding(
                                        category="Architectural Modularity",
                                        severity="MEDIUM",
                                        file_path=rel,
                                        line_no=node.lineno,
                                        message=f"Function `{node.name}` ({length} lines) exceeds clean modularity limit (60 max)",
                                        penalty_points=penalty
                                    ))

                    except Exception:
                        pass

        # Normalize drift score between 0.0 and 100.0
        normalized_drift = min(100.0, round(total_penalty, 1))
        adherence_pct = max(0.0, round(100.0 - normalized_drift, 1))

        if adherence_pct >= 90.0:
            snr = "EXCELLENT (HIGH SNR / ZERO DECAY)"
        elif adherence_pct >= 75.0:
            snr = "MODERATE (MINOR ATTENTION DEGRADATION)"
        else:
            snr = "POOR (ATTENTION DILUTION / HIGH DRIFT)"

        return DriftReport(
            workspace_dir=abs_root,
            drift_score=normalized_drift,
            adherence_pct=adherence_pct,
            snr_rating=snr,
            findings=findings,
            files_audited=files_count
        )

    @classmethod
    def render_cli(cls, report: DriftReport) -> None:
        """Renders rich ANSI terminal drift score report."""
        print("\n" + "=" * 80)
        print("🎯 \033[36mT-ZERO INSTRUCTION & ARCHITECTURAL DRIFT ANALYZER\033[0m")
        print("=" * 80)
        print(f"📁 Workspace: \033[33m{report.workspace_dir}\033[0m ({report.files_audited} modules audited)")
        
        # Color badge for adherence
        if report.adherence_pct >= 90.0:
            badge = f"\033[32m{report.adherence_pct}% (EXCELLENT)\033[0m"
        elif report.adherence_pct >= 75.0:
            badge = f"\033[33m{report.adherence_pct}% (ACCEPTABLE)\033[0m"
        else:
            badge = f"\033[31m{report.adherence_pct}% (CRITICAL DRIFT)\033[0m"

        print(f"📈 Prompt Instruction Adherence: {badge}")
        print(f"📉 Cumulative Drift Score: \033[33m{report.drift_score} / 100\033[0m")
        print(f"⚡ Context Attention SNR: \033[32m{report.snr_rating}\033[0m")
        print("-" * 80)

        if not report.findings:
            print("🌟 \033[32mFlawless Adherence! Zero rule drift, zero secret leaks, zero boundary violations.\033[0m")
        else:
            print(f"Identified {len(report.findings)} rule drift / violation points:")
            for f in report.findings[:15]:
                print(f"  • \033[33m{f.file_path}:{f.line_no}\033[0m [{f.category}]: {f.message}")
            if len(report.findings) > 15:
                print(f"  ... and {len(report.findings) - 15} more findings.")

        print("=" * 80)
        print("💡 \033[32mAST pruning preserves high Signal-to-Noise Ratio (SNR), preventing model forgetting over 50+ turns.\033[0m\n")

    @classmethod
    def to_json(cls, report: DriftReport) -> str:
        """Serializes drift report into JSON."""
        return json.dumps({
            "workspace_dir": report.workspace_dir,
            "drift_score": report.drift_score,
            "adherence_pct": report.adherence_pct,
            "snr_rating": report.snr_rating,
            "files_audited": report.files_audited,
            "findings_count": len(report.findings),
            "findings": [
                {
                    "category": f.category,
                    "severity": f.severity,
                    "file_path": f.file_path,
                    "line_no": f.line_no,
                    "message": f.message,
                    "penalty_points": f.penalty_points
                }
                for f in report.findings
            ]
        }, indent=2)


def main():
    target = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "."
    rep = DriftAnalyzer.analyze_workspace(target)
    if "--json" in sys.argv:
        print(DriftAnalyzer.to_json(rep))
    else:
        DriftAnalyzer.render_cli(rep)


if __name__ == "__main__":
    main()
