# -*- coding: utf-8 -*-
"""
Siber Akademi — T-Zero Dynamic Context Window & Token Budget Packer.
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: MIT

Solves the context window packing problem for LLMs: packs an entire repository or
focused subsystem into an EXACT token budget (e.g. 8k, 16k, 32k, 64k, 128k) using
multi-tier AST representations (T-1 Raw, T-2 Light, T-3 Ultra, T-4 Signature) and
greedy relevance-weighted knapsack optimization.
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import os
import re
import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any, Set

from tzero_polyglot import PolyglotTokenReducer
from tzero_features import should_skip_dir, get_ignore_patterns


@dataclass
class ModuleBudgetEntry:
    """Represents a module with multi-tier representations and token counts."""
    rel_path: str
    abs_path: str
    lang: Optional[str]
    raw_code: str
    raw_tokens: int
    relevance_score: float = 1.0
    tier_versions: Dict[str, str] = field(default_factory=dict)
    tier_tokens: Dict[str, int] = field(default_factory=dict)
    selected_tier: Optional[str] = None


@dataclass
class PackResult:
    """Result of context budget packing."""
    target_budget: int
    total_tokens: int
    utilization_pct: float
    raw_total_tokens: int
    token_savings_pct: float
    focus_target: str
    entries: List[ModuleBudgetEntry] = field(default_factory=list)
    bundle_text: str = ""
    tier_counts: Dict[str, int] = field(default_factory=dict)


class TokenBudgetPacker:
    """Dynamically packs codebase AST tiers to fit an exact LLM token budget."""

    TOKEN_DIVISOR = 3.8  # Fallback ratio when tiktoken is unavailable

    @classmethod
    def estimate_tokens(cls, text: str, model_name: str = "gpt-4o") -> int:
        """Exact cached BPE token counter for source code with deterministic char-ratio fallback."""
        from tzero_polyglot import count_bpe_tokens
        return count_bpe_tokens(text, model_name=model_name, fallback_divisor=cls.TOKEN_DIVISOR)

    @classmethod
    def extract_t4_signatures(cls, code: str, lang: Optional[str]) -> str:
        """Extracts minimal one-line signature repomap (T-4)."""
        lines = code.splitlines()
        sig_lines = []
        for line in lines:
            trimmed = line.strip()
            if not trimmed or trimmed.startswith(("#", "//", "/*", "*")):
                continue
            if re.match(r"^(?:export\s+)?(?:class|interface|type|struct|enum|def|async\s+def|func|fn|pub\s+fn|pub\s+struct)\b", trimmed):
                sig_lines.append(trimmed.split("{")[0].split(":")[0].strip())
        if not sig_lines:
            sig_lines = [l.strip() for l in lines[:5] if l.strip()]
        return "\n".join(sig_lines[:25])

    @classmethod
    def scan_workspace(cls, workspace_dir: str, max_files: int = 150) -> List[ModuleBudgetEntry]:
        """Scans workspace and prepares multi-tier representations for supported files."""
        entries: List[ModuleBudgetEntry] = []
        workspace_dir = os.path.abspath(workspace_dir)

        for root, dirs, files in os.walk(workspace_dir):
            if len(entries) >= max_files:
                dirs[:] = []
                break

            if should_skip_dir(root, workspace_dir):
                dirs[:] = []
                continue

            # Filter out hidden or build directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "dist", "build", "venv", ".venv", "__pycache__")]

            for fname in files:
                if len(entries) >= max_files:
                    dirs[:] = []
                    break
                lang = PolyglotTokenReducer.detect_language(fname)
                if not lang:
                    continue

                abs_p = os.path.join(root, fname)
                rel_p = os.path.relpath(abs_p, workspace_dir).replace("\\", "/")

                try:
                    with open(abs_p, "r", encoding="utf-8", errors="replace") as f:
                        raw_code = f.read()
                except Exception:
                    continue

                if not raw_code.strip():
                    continue

                raw_tok = cls.estimate_tokens(raw_code)

                # Generate 4 Tiers:
                # T-1: Full Raw Implementation
                t1 = raw_code

                # T-2: Light AST Reduction (preserves docstrings/comments)
                t2 = PolyglotTokenReducer.reduce_code(raw_code, fname, mode="light")

                # T-3: Ultra AST Reduction (signatures only)
                t3 = PolyglotTokenReducer.reduce_code(raw_code, fname, mode="ultra")

                # T-4: Minimal One-line Declarations
                t4 = cls.extract_t4_signatures(raw_code, lang)

                tier_versions = {
                    "T-1": t1,
                    "T-2": t2,
                    "T-3": t3,
                    "T-4": t4
                }
                tier_tokens = {
                    "T-1": raw_tok,
                    "T-2": cls.estimate_tokens(t2),
                    "T-3": cls.estimate_tokens(t3),
                    "T-4": cls.estimate_tokens(t4)
                }

                entries.append(ModuleBudgetEntry(
                    rel_path=rel_p,
                    abs_path=abs_p,
                    lang=lang,
                    raw_code=raw_code,
                    raw_tokens=raw_tok,
                    tier_versions=tier_versions,
                    tier_tokens=tier_tokens
                ))

        return entries

    @classmethod
    def score_relevance(cls, entries: List[ModuleBudgetEntry], focus: str = "") -> None:
        """Assigns relevance scores to each file based on focus query and module centrality."""
        focus_clean = (focus or "").strip().lower()
        focus_terms = set(re.findall(r"\w+", focus_clean))

        for entry in entries:
            score = 1.0
            rel_lower = entry.rel_path.lower()

            # Direct file path match
            if focus_clean and (focus_clean == rel_lower or focus_clean in rel_lower):
                score += 100.0
            elif focus_terms:
                # Match terms in filename
                for term in focus_terms:
                    if term in rel_lower:
                        score += 25.0
                # Match terms in code
                for term in focus_terms:
                    matches = len(re.findall(r"\b" + re.escape(term) + r"\b", entry.raw_code.lower()))
                    score += min(matches * 2.0, 20.0)

            # Centrality bonuses
            if any(name in rel_lower for name in ("core", "main", "server", "router", "manager", "engine", "service")):
                score += 5.0
            if any(name in rel_lower for name in ("test", "spec", "mock")):
                score *= 0.5  # Deprioritize tests unless specifically focused

            entry.relevance_score = score

    @classmethod
    def pack(
        cls,
        workspace_dir: str = ".",
        budget_tokens: int = 16000,
        focus: str = "",
        max_files: int = 150
    ) -> PackResult:
        """Packs workspace files to fill budget_tokens with optimal AST tiers.
        
        Args:
            workspace_dir: Target project root.
            budget_tokens: Exact token ceiling (e.g. 8000, 16000, 32000, 64000).
            focus: Optional focus target file or semantic query.
            max_files: Maximum workspace files to inspect.
        
        Returns:
            PackResult with optimal multi-file context bundle.
        """
        entries = cls.scan_workspace(workspace_dir, max_files=max_files)
        if not entries:
            return PackResult(
                target_budget=budget_tokens,
                total_tokens=0,
                utilization_pct=0.0,
                raw_total_tokens=0,
                token_savings_pct=0.0,
                focus_target=focus,
                bundle_text="// No matching source files found in workspace."
            )

        cls.score_relevance(entries, focus=focus)

        # Sort entries by relevance score descending
        entries.sort(key=lambda e: e.relevance_score, reverse=True)

        raw_total = sum(e.raw_tokens for e in entries)

        # Reserved tokens for bundle manifest header (~400 tokens)
        usable_budget = max(500, budget_tokens - 400)
        allocated_tokens = 0
        tier_counts = {"T-1": 0, "T-2": 0, "T-3": 0, "T-4": 0}

        # Step 1: Assign top-priority focus files Tier 1 if possible
        for e in entries:
            if e.relevance_score >= 100.0:  # Direct focus match
                t1_tok = e.tier_tokens["T-1"]
                if allocated_tokens + t1_tok <= usable_budget:
                    e.selected_tier = "T-1"
                    allocated_tokens += t1_tok
                    tier_counts["T-1"] += 1
                elif allocated_tokens + e.tier_tokens["T-2"] <= usable_budget:
                    e.selected_tier = "T-2"
                    allocated_tokens += e.tier_tokens["T-2"]
                    tier_counts["T-2"] += 1

        # Step 2: Try to assign Tier 2 (Light) or Tier 3 (Ultra) to high-relevance modules
        for e in entries:
            if e.selected_tier is not None:
                continue

            if e.relevance_score > 10.0:
                t2_tok = e.tier_tokens["T-2"]
                t3_tok = e.tier_tokens["T-3"]
                if allocated_tokens + t2_tok <= usable_budget:
                    e.selected_tier = "T-2"
                    allocated_tokens += t2_tok
                    tier_counts["T-2"] += 1
                elif allocated_tokens + t3_tok <= usable_budget:
                    e.selected_tier = "T-3"
                    allocated_tokens += t3_tok
                    tier_counts["T-3"] += 1

        # Step 3: Fill remainder with Tier 3 (Ultra) or Tier 4 (Signatures)
        for e in entries:
            if e.selected_tier is not None:
                continue

            t3_tok = e.tier_tokens["T-3"]
            t4_tok = e.tier_tokens["T-4"]

            if allocated_tokens + t3_tok <= usable_budget:
                e.selected_tier = "T-3"
                allocated_tokens += t3_tok
                tier_counts["T-3"] += 1
            elif allocated_tokens + t4_tok <= usable_budget:
                e.selected_tier = "T-4"
                allocated_tokens += t4_tok
                tier_counts["T-4"] += 1
            else:
                # Budget exhausted; this file is omitted from packed context
                e.selected_tier = None

        packed_entries = [e for e in entries if e.selected_tier is not None]

        # Step 4: Render Markdown Context Bundle
        bundle_md = cls.render_bundle_markdown(
            packed_entries=packed_entries,
            budget=budget_tokens,
            allocated_tokens=allocated_tokens,
            raw_total=raw_total,
            focus=focus,
            tier_counts=tier_counts
        )

        final_total = cls.estimate_tokens(bundle_md)
        util_pct = min(100.0, (final_total / budget_tokens) * 100.0)
        savings_pct = max(0.0, ((raw_total - final_total) / max(raw_total, 1)) * 100.0)

        return PackResult(
            target_budget=budget_tokens,
            total_tokens=final_total,
            utilization_pct=round(util_pct, 1),
            raw_total_tokens=raw_total,
            token_savings_pct=round(savings_pct, 1),
            focus_target=focus,
            entries=packed_entries,
            bundle_text=bundle_md,
            tier_counts=tier_counts
        )

    @classmethod
    def render_bundle_markdown(
        cls,
        packed_entries: List[ModuleBudgetEntry],
        budget: int,
        allocated_tokens: int,
        raw_total: int,
        focus: str,
        tier_counts: Dict[str, int]
    ) -> str:
        """Formats the unified AI context pack with manifest table and delimited code sections."""
        out = []
        focus_tag = f" (Focus: `{focus}`)" if focus else ""
        tier_summary = ", ".join(f"{cnt}x {t}" for t, cnt in tier_counts.items() if cnt > 0)

        out.append(f"# 📦 T-ZERO PACKED CONTEXT BUNDLE{focus_tag}")
        out.append(f"- **Target Token Budget:** {budget:,} tokens")
        out.append(f"- **Packed Token Volume:** ~{allocated_tokens:,} tokens ({allocated_tokens/max(budget,1)*100:.1f}% capacity)")
        out.append(f"- **Raw Codebase Tokens:** ~{raw_total:,} tokens (**{max(0.0, (1 - allocated_tokens/max(raw_total,1))*100):.1f}% reduction**)")
        out.append(f"- **Files Included:** {len(packed_entries)} files ({tier_summary})\n")

        # Manifest Table
        out.append("### 📑 Context Manifest")
        out.append("| File | Tier | Language | Tokens | Status |")
        out.append("| :--- | :---: | :---: | :---: | :--- |")
        for e in packed_entries:
            tok = e.tier_tokens.get(e.selected_tier, 0)
            status = "Full Body" if e.selected_tier == "T-1" else "AST Skeleton"
            out.append(f"| `{e.rel_path}` | **{e.selected_tier}** | {e.lang} | ~{tok:,} | {status} |")
        out.append("\n---\n")

        # File Content Blocks
        for e in packed_entries:
            code = e.tier_versions.get(e.selected_tier, "")
            out.append(f"<!-- FILE: {e.rel_path} [TIER: {e.selected_tier} | {e.lang}] -->")
            out.append(f"```{e.lang or 'text'}\n// [T-Zero Context: {e.rel_path} ({e.selected_tier})]")
            out.append(code.strip())
            out.append("```\n")

        return "\n".join(out).strip()


def pack_workspace(
    workspace_dir: str = ".",
    budget_tokens: int = 16000,
    focus: str = "",
    out_file: Optional[str] = None
) -> PackResult:
    """Convenience helper to pack workspace context into a budget and optionally write to disk."""
    res = TokenBudgetPacker.pack(workspace_dir=workspace_dir, budget_tokens=budget_tokens, focus=focus)
    if out_file:
        out_path = os.path.join(workspace_dir, out_file) if not os.path.isabs(out_file) else out_file
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(res.bundle_text)
    return res
