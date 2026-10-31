# -*- coding: utf-8 -*-
"""
Siber Akademi — T-Zero Smart Micro-Patch & AST-Tolerant Fuzzy Patcher.
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: MIT

1. SmartMicroPatcher: Compresses standard git diffs and unified diffs into ultra-dense
   semantic AST micro-patches, reducing token payload by 80% to 90% for LLM workflows.
2. ASTFuzzyPatcher: Applies AI/LLM diffs and patches to codebase files with multi-tier
   tolerance against line-drift, whitespace discrepancies, indentation mismatches,
   AST symbol boundary shifts, and sliding-window fuzzy similarity.
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import ast
import difflib
import os
import re
from dataclasses import dataclass, field
from typing import Tuple, List, Dict, Any, Optional


# ==============================================================================
# 1. SMART MICRO-PATCH COMPRESSOR
# ==============================================================================

class SmartMicroPatcher:
    """Condenses Git diffs and file deltas into semantic AST micro-patches."""

    @staticmethod
    def compress_diff(raw_diff: str, max_context_lines: int = 1) -> Tuple[str, float]:
        """Compresses unified git diff into a compact semantic patch.
        
        Args:
            raw_diff: Standard output from 'git diff' or unified diff.
            max_context_lines: Maximum surrounding context lines to retain per hunk (default 1).
        
        Returns:
            (compact_micro_patch, token_savings_percentage)
        """
        orig_len = len(raw_diff)
        if orig_len < 40:
            return raw_diff, 0.0

        lines = raw_diff.splitlines()
        output = []
        current_file = ""
        in_hunk = False
        hunk_changes = []
        trailing_context = []

        def flush_hunk():
            nonlocal hunk_changes, trailing_context, in_hunk
            if hunk_changes:
                trimmed_trailing = trailing_context[:max_context_lines]
                output.extend(hunk_changes + trimmed_trailing)
            hunk_changes = []
            trailing_context = []
            in_hunk = False

        for line in lines:
            if line.startswith("diff --git "):
                flush_hunk()
                m = re.search(r"b/(.*)$", line)
                current_file = m.group(1) if m else line[11:]
                output.append(f"\n📁 [{current_file}]")
                continue

            if line.startswith(("index ", "--- ", "+++ ", "new file mode ", "deleted file mode ")):
                continue

            if line.startswith("@@"):
                flush_hunk()
                hunk_match = re.match(r"@@\s+-\d+(?:,\d+)?\s+\+(\d+)(?:,\d+)?\s+@@(.*)", line)
                if hunk_match:
                    start_line = hunk_match.group(1)
                    symbol_scope = hunk_match.group(2).strip()
                    scope_tag = f" :: {symbol_scope}" if symbol_scope else ""
                    output.append(f"  ⚡ L{start_line}{scope_tag}")
                else:
                    output.append(f"  ⚡ {line.strip()}")
                in_hunk = True
                continue

            if in_hunk:
                if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
                    flush_trailing = trailing_context[:max_context_lines]
                    if flush_trailing:
                        hunk_changes.extend(flush_trailing)
                        trailing_context = []
                    hunk_changes.append(f"    {line}")
                elif line.startswith(" "):
                    if not hunk_changes:
                        if len(trailing_context) < max_context_lines:
                            trailing_context.append(f"    {line}")
                        else:
                            trailing_context = [f"    {line}"]
                    else:
                        if len(trailing_context) < max_context_lines:
                            trailing_context.append(f"    {line}")
                else:
                    flush_hunk()

        flush_hunk()
        compact_res = "\n".join(output).strip()
        savings = max(0.0, ((orig_len - len(compact_res)) / max(orig_len, 1)) * 100.0)
        return compact_res, savings

    @staticmethod
    def format_micro_patch_report(raw_diff: str, max_context_lines: int = 1) -> str:
        """Formats an AI-ready Markdown report containing the micro-patch."""
        compact, savings = SmartMicroPatcher.compress_diff(raw_diff, max_context_lines=max_context_lines)
        approx_orig_tokens = max(1, int(len(raw_diff) / 3.8))
        approx_compact_tokens = max(1, int(len(compact) / 3.8))

        return (
            f"# 🧩 T-Zero AST Smart Micro-Patch\n"
            f"- **Raw Diff Tokens:** ~{approx_orig_tokens:,} tokens\n"
            f"- **Compressed Patch Tokens:** ~{approx_compact_tokens:,} tokens\n"
            f"- **Payload Compression:** **-{savings:.1f}% savings**\n\n"
            f"```patch\n{compact}\n```"
        )


# ==============================================================================
# 2. AST-TOLERANT FUZZY PATCHER
# ==============================================================================

@dataclass
class PatchHunk:
    """Represents a parsed diff hunk with context, removals, and additions."""
    old_start: int
    old_length: int
    new_start: int
    new_length: int
    symbol_scope: str = ""
    lines: List[str] = field(default_factory=list)
    old_lines: List[str] = field(default_factory=list)
    new_lines: List[str] = field(default_factory=list)
    hunk_index: int = 0


@dataclass
class FilePatch:
    """Represents hunks targeting a specific file path."""
    source_file: Optional[str] = None
    target_file: Optional[str] = None
    hunks: List[PatchHunk] = field(default_factory=list)


class ASTFuzzyPatcher:
    """Multi-tier AST-Tolerant and Whitespace-Agnostic Fuzzy Patcher.
    
    Tiers of tolerance:
      1. exact: Line-exact match at hunk header coordinates.
      2. line_drift: Content-exact match across entire file regardless of line offset.
      3. whitespace_normalized: Strips leading/trailing spaces and adapts indentation.
      4. ast_symbol_boundary: Bounded search within enclosing function/class/method AST scope.
      5. fuzzy_similarity: Sliding-window Levenshtein / SequenceMatcher match (ratio >= tolerance).
    """

    @classmethod
    def parse_patch(cls, patch_text: str) -> List[FilePatch]:
        """Parses unified diff, git diff, or raw hunks into FilePatch structures."""
        lines = patch_text.splitlines()
        file_patches: List[FilePatch] = []
        current_file_patch = FilePatch()
        current_hunk: Optional[PatchHunk] = None
        hunk_idx = 0

        hunk_header_re = re.compile(r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@(.*)$")

        for line in lines:
            # Git file header: diff --git a/foo.py b/foo.py
            if line.startswith("diff --git "):
                if current_hunk:
                    current_file_patch.hunks.append(current_hunk)
                    current_hunk = None
                if current_file_patch.hunks or current_file_patch.target_file:
                    file_patches.append(current_file_patch)
                m = re.search(r"b/(.*)$", line)
                target = m.group(1).strip() if m else None
                current_file_patch = FilePatch(target_file=target)
                continue

            # Standard diff headers: --- a/foo.py, +++ b/foo.py
            if line.startswith("--- ") and not line.startswith("--- /dev/null"):
                m = re.search(r"(?:a/|\b)(.+?)(?:\t.*|$)", line[4:].strip())
                if m:
                    current_file_patch.source_file = m.group(1).strip()
                continue

            if line.startswith("+++ ") and not line.startswith("+++ /dev/null"):
                m = re.search(r"(?:b/|\b)(.+?)(?:\t.*|$)", line[4:].strip())
                if m:
                    current_file_patch.target_file = m.group(1).strip()
                continue

            # Hunk header: @@ -10,5 +10,6 @@ def my_func():
            m_hunk = hunk_header_re.match(line)
            if m_hunk:
                if current_hunk:
                    current_file_patch.hunks.append(current_hunk)
                hunk_idx += 1
                old_s = int(m_hunk.group(1))
                old_l = int(m_hunk.group(2)) if m_hunk.group(2) is not None else 1
                new_s = int(m_hunk.group(3))
                new_l = int(m_hunk.group(4)) if m_hunk.group(4) is not None else 1
                scope = m_hunk.group(5).strip()

                current_hunk = PatchHunk(
                    old_start=old_s,
                    old_length=old_l,
                    new_start=new_s,
                    new_length=new_l,
                    symbol_scope=scope,
                    hunk_index=hunk_idx
                )
                continue

            # Hunk body lines
            if current_hunk is not None:
                if line.startswith("+"):
                    current_hunk.lines.append(line)
                    current_hunk.new_lines.append(line[1:])
                elif line.startswith("-"):
                    current_hunk.lines.append(line)
                    current_hunk.old_lines.append(line[1:])
                elif line.startswith(" "):
                    current_hunk.lines.append(line)
                    current_hunk.old_lines.append(line[1:])
                    current_hunk.new_lines.append(line[1:])
                elif line == "":
                    # Empty context line
                    current_hunk.lines.append(" ")
                    current_hunk.old_lines.append("")
                    current_hunk.new_lines.append("")
                elif line.startswith("\\"):
                    # \ No newline at end of file
                    continue

        if current_hunk:
            current_file_patch.hunks.append(current_hunk)
        if current_file_patch.hunks or current_file_patch.target_file:
            file_patches.append(current_file_patch)

        if not file_patches and current_hunk is not None:
            file_patches.append(FilePatch(hunks=[current_hunk]))

        return file_patches

    @classmethod
    def extract_symbol_name(cls, scope_hint: str) -> Optional[str]:
        """Extracts identifier name from hunk symbol scope header (e.g., 'def charge(x):')."""
        if not scope_hint:
            return None
        m = re.search(r"(?:def|class|func|fn|function|struct|impl)\s+([A-Za-z0-9_]+)", scope_hint)
        if m:
            return m.group(1)
        # Fallback: look for identifier followed by parens
        m2 = re.search(r"([A-Za-z0-9_]{3,})\s*\(", scope_hint)
        return m2.group(1) if m2 else None

    @classmethod
    def find_symbol_range(cls, lines: List[str], symbol_name: str) -> Optional[Tuple[int, int]]:
        """Finds line range [start, end] for a symbol in lines using AST or polyglot indentation."""
        if not symbol_name:
            return None

        # 1. Try Python AST if file is Python
        code_str = "\n".join(lines)
        try:
            tree = ast.parse(code_str)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if node.name == symbol_name:
                        start_line = max(0, node.lineno - 1)
                        end_line = getattr(node, "end_lineno", len(lines))
                        return (start_line, min(len(lines), end_line))
        except Exception:
            pass

        # 2. Universal Polyglot Fallback: Regex + Indentation Scope
        sym_pattern = re.compile(r"(?:def|class|func|fn|function|struct|impl|pub fn)\s+" + re.escape(symbol_name) + r"\b")
        for i, line in enumerate(lines):
            if sym_pattern.search(line):
                # Found symbol definition start
                base_indent = len(line) - len(line.lstrip())
                end_i = len(lines)
                for j in range(i + 1, len(lines)):
                    cur_line = lines[j]
                    if not cur_line.strip():
                        continue
                    cur_indent = len(cur_line) - len(cur_line.lstrip())
                    if cur_indent <= base_indent:
                        end_i = j
                        break
                return (i, end_i)

        return None

    @classmethod
    def adjust_indentation(cls, target_lines: List[str], match_idx: int, old_lines: List[str], new_lines: List[str]) -> List[str]:
        """Adjusts leading indentation of new_lines to match target_lines at match_idx."""
        if not new_lines or not old_lines or match_idx >= len(target_lines):
            return list(new_lines)

        # Detect target indentation
        target_line = target_lines[match_idx] if match_idx < len(target_lines) else ""
        target_indent_len = len(target_line) - len(target_line.lstrip())
        target_indent_str = target_line[:target_indent_len]

        # Detect old hunk indentation
        first_old = old_lines[0] if old_lines else ""
        old_indent_len = len(first_old) - len(first_old.lstrip())
        old_indent_str = first_old[:old_indent_len]

        if target_indent_str == old_indent_str:
            return list(new_lines)

        adjusted: List[str] = []
        for line in new_lines:
            if not line.strip():
                adjusted.append("")
                continue
            cur_indent_len = len(line) - len(line.lstrip())
            rel_diff = cur_indent_len - old_indent_len
            if rel_diff >= 0:
                adjusted.append(target_indent_str + (" " * rel_diff) + line.lstrip())
            else:
                cut = max(0, len(target_indent_str) + rel_diff)
                adjusted.append(target_indent_str[:cut] + line.lstrip())

        return adjusted

    @classmethod
    def match_hunk(
        cls,
        target_lines: List[str],
        hunk: PatchHunk,
        fuzzy: bool = True,
        tolerance: float = 0.75
    ) -> Tuple[bool, int, int, str, float, List[str]]:
        """Finds match slice [start_idx : end_idx] for hunk with multi-tier tolerance.
        
        Returns:
            (matched, start_idx, end_idx, strategy, confidence, adjusted_new_lines)
        """
        k = len(hunk.old_lines)

        # Handle pure addition hunk (no old lines to replace)
        if k == 0:
            exp_pos = max(0, min(len(target_lines), hunk.old_start - 1))
            return True, exp_pos, exp_pos, "exact_insertion", 1.0, list(hunk.new_lines)

        expected_start = max(0, min(len(target_lines), hunk.old_start - 1))
        norm_old = [line.strip() for line in hunk.old_lines]

        # Extract symbol scope range if present in hunk header
        symbol_name = cls.extract_symbol_name(hunk.symbol_scope)
        sym_range = cls.find_symbol_range(target_lines, symbol_name) if symbol_name else None

        # ----------------------------------------------------------------------
        # Tier 1: Exact coordinates & content
        # ----------------------------------------------------------------------
        # Only accept exact match if expected_start is not outside a specified symbol scope
        if expected_start + k <= len(target_lines):
            if target_lines[expected_start : expected_start + k] == hunk.old_lines:
                if not sym_range or (sym_range[0] <= expected_start < sym_range[1]):
                    return True, expected_start, expected_start + k, "exact", 1.0, list(hunk.new_lines)

        # ----------------------------------------------------------------------
        # Tier 2: Line drift search across entire file (exact content)
        # ----------------------------------------------------------------------
        exact_matches = []
        for i in range(len(target_lines) - k + 1):
            if target_lines[i : i + k] == hunk.old_lines:
                exact_matches.append(i)

        if exact_matches:
            if sym_range:
                sym_matches = [idx for idx in exact_matches if sym_range[0] <= idx < sym_range[1]]
                if sym_matches:
                    best_idx = min(sym_matches, key=lambda idx: abs(idx - expected_start))
                    strat = "ast_symbol_boundary" if len(exact_matches) > 1 else "line_drift"
                    return True, best_idx, best_idx + k, strat, 1.0, list(hunk.new_lines)
            best_idx = min(exact_matches, key=lambda idx: abs(idx - expected_start))
            return True, best_idx, best_idx + k, "line_drift", 1.0, list(hunk.new_lines)

        if not fuzzy:
            return False, -1, -1, "none", 0.0, []

        # ----------------------------------------------------------------------
        # Tier 3: Whitespace & Indentation Normalized Search
        # ----------------------------------------------------------------------
        ws_matches = []
        for i in range(len(target_lines) - k + 1):
            candidate = [target_lines[i + j].strip() for j in range(k)]
            if candidate == norm_old:
                ws_matches.append(i)

        if ws_matches:
            if sym_range:
                sym_ws_matches = [idx for idx in ws_matches if sym_range[0] <= idx < sym_range[1]]
                if sym_ws_matches:
                    best_idx = min(sym_ws_matches, key=lambda idx: abs(idx - expected_start))
                    strat = "ast_symbol_boundary" if len(ws_matches) > 1 else "whitespace_normalized"
                    adjusted = cls.adjust_indentation(target_lines, best_idx, hunk.old_lines, hunk.new_lines)
                    return True, best_idx, best_idx + k, strat, 0.95, adjusted
            best_idx = min(ws_matches, key=lambda idx: abs(idx - expected_start))
            adjusted = cls.adjust_indentation(target_lines, best_idx, hunk.old_lines, hunk.new_lines)
            return True, best_idx, best_idx + k, "whitespace_normalized", 0.95, adjusted

        # ----------------------------------------------------------------------
        # Tier 5: Sliding-Window Fuzzy Similarity (Levenshtein / SequenceMatcher)
        # ----------------------------------------------------------------------
        search_range = range(sym_range[0], max(sym_range[0], sym_range[1] - k + 1)) if sym_range else range(len(target_lines) - k + 1)
        old_block = "\n".join(norm_old)
        best_ratio = 0.0
        best_idx = -1

        for i in search_range:
            candidate_block = "\n".join(target_lines[i + j].strip() for j in range(k))
            ratio = difflib.SequenceMatcher(None, candidate_block, old_block).ratio()
            distance_penalty = min(0.12, abs(i - expected_start) * 0.0003)
            effective_score = ratio - distance_penalty
            if effective_score > best_ratio:
                best_ratio = effective_score
                best_idx = i

        if best_idx != -1 and best_ratio >= tolerance:
            strat = "fuzzy_similarity"
            adjusted = cls.adjust_indentation(target_lines, best_idx, hunk.old_lines, hunk.new_lines)
            return True, best_idx, best_idx + k, strat, round(best_ratio, 3), adjusted

        return False, -1, -1, "none", 0.0, []

    @classmethod
    def apply_fuzzy_patch(
        cls,
        source_content: str,
        patch_content: str,
        fuzzy: bool = True,
        tolerance: float = 0.75,
        dry_run: bool = False,
        reverse: bool = False
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Applies patch to source_content with multi-tier tolerance.
        
        Args:
            source_content: Original file source code.
            patch_content: Unified diff, git diff, or hunk text.
            fuzzy: Enable whitespace, AST, and similarity tolerance (default: True).
            tolerance: Minimum similarity ratio for Tier 5 fuzzy match (default: 0.75).
            dry_run: Validate applicability without returning mutated code.
            reverse: Un-apply patch (swaps old_lines and new_lines).
        
        Returns:
            (success, patched_content, metadata_report)
        """
        file_patches = cls.parse_patch(patch_content)
        all_hunks: List[PatchHunk] = []
        for fp in file_patches:
            all_hunks.extend(fp.hunks)

        if not all_hunks:
            return False, source_content, {
                "success": False,
                "error": "No valid diff hunks detected in patch content",
                "applied_hunks": 0,
                "total_hunks": 0
            }

        # Handle reverse patch mode
        if reverse:
            for h in all_hunks:
                h.old_lines, h.new_lines = h.new_lines, h.old_lines
                h.old_start, h.new_start = h.new_start, h.old_start
                h.old_length, h.new_length = h.new_length, h.old_length

        target_lines = source_content.splitlines()
        hunk_results: List[Dict[str, Any]] = []

        # Step 1: Match each hunk against target lines
        # To avoid offset collisions, find match positions first or apply bottom-to-top
        matches = []
        for h in all_hunks:
            matched, start_idx, end_idx, strategy, conf, adj_lines = cls.match_hunk(
                target_lines, h, fuzzy=fuzzy, tolerance=tolerance
            )
            matches.append({
                "hunk": h,
                "matched": matched,
                "start_idx": start_idx,
                "end_idx": end_idx,
                "strategy": strategy,
                "confidence": conf,
                "adjusted_lines": adj_lines
            })

        # Check if all hunks were matched
        all_matched = all(m["matched"] for m in matches)

        # Sort matches in descending order of start_idx to apply bottom-to-top safely
        sorted_matches = sorted(
            [m for m in matches if m["matched"]],
            key=lambda m: m["start_idx"],
            reverse=True
        )

        if all_matched and not dry_run:
            for m in sorted_matches:
                s, e = m["start_idx"], m["end_idx"]
                target_lines[s:e] = m["adjusted_lines"]

        for m in matches:
            h = m["hunk"]
            hunk_results.append({
                "hunk_index": h.hunk_index,
                "status": "applied" if m["matched"] else "rejected",
                "strategy": m["strategy"],
                "confidence": m["confidence"],
                "old_start": h.old_start,
                "matched_line": (m["start_idx"] + 1) if m["matched"] else None,
                "scope_symbol": h.symbol_scope
            })

        applied_count = sum(1 for m in matches if m["matched"])
        patched_text = "\n".join(target_lines)
        if source_content.endswith("\n") and not patched_text.endswith("\n"):
            patched_text += "\n"

        meta = {
            "success": all_matched,
            "total_hunks": len(all_hunks),
            "applied_hunks": applied_count,
            "failed_hunks": len(all_hunks) - applied_count,
            "strategies_used": list({m["strategy"] for m in matches if m["matched"]}),
            "hunk_results": hunk_results,
            "dry_run": dry_run,
            "reverse": reverse,
            "original_lines": len(source_content.splitlines()),
            "patched_lines": len(patched_text.splitlines())
        }

        return all_matched, (patched_text if all_matched and not dry_run else source_content), meta

    @classmethod
    def patch_file(
        cls,
        target_file_path: str,
        patch_text_or_path: str,
        in_place: bool = True,
        fuzzy: bool = True,
        tolerance: float = 0.75,
        dry_run: bool = False,
        backup: bool = False
    ) -> Dict[str, Any]:
        """Patches a file on disk using AST-tolerant fuzzy matching.
        
        Args:
            target_file_path: Absolute or relative path to target file.
            patch_text_or_path: Diff string or path to .diff/.patch file.
            in_place: Write changes directly to target_file_path (default: True).
            fuzzy: Enable fuzzy and AST matching (default: True).
            tolerance: Fuzzy matching threshold (default: 0.75).
            dry_run: Verify patch applicability without writing to disk.
            backup: Create .bak file before modifying (default: False).
        
        Returns:
            Dictionary with operation status and hunk metrics.
        """
        if not os.path.exists(target_file_path):
            return {
                "success": False,
                "error": f"Target file not found: {target_file_path}",
                "target_file": target_file_path
            }

        # Resolve patch content
        if os.path.isfile(patch_text_or_path):
            with open(patch_text_or_path, "r", encoding="utf-8", errors="replace") as pf:
                patch_content = pf.read()
        else:
            patch_content = patch_text_or_path

        with open(target_file_path, "r", encoding="utf-8", errors="replace") as tf:
            original_code = tf.read()

        success, patched_code, meta = cls.apply_fuzzy_patch(
            original_code,
            patch_content,
            fuzzy=fuzzy,
            tolerance=tolerance,
            dry_run=dry_run
        )

        meta["target_file"] = target_file_path

        if success and in_place and not dry_run:
            if backup:
                bak_path = f"{target_file_path}.bak"
                with open(bak_path, "w", encoding="utf-8") as bf:
                    bf.write(original_code)
                meta["backup_created"] = bak_path

            with open(target_file_path, "w", encoding="utf-8") as out_f:
                out_f.write(patched_code)
            meta["file_written"] = True

        return meta


# Global convenience aliases
apply_fuzzy_patch = ASTFuzzyPatcher.apply_fuzzy_patch
patch_file = ASTFuzzyPatcher.patch_file

