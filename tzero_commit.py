# -*- coding: utf-8 -*-
"""
Siber Akademi — T-Zero Local Semantic Git Commit & Changelog Synthesizer.
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: MIT

Analyzes staged or unstaged AST git diffs locally (100% offline, $0 cost) to
synthesize Conventional Commit messages and structured CHANGELOG entries
without transmitting code to cloud LLMs.
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
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from tzero_patch import ASTFuzzyPatcher


@dataclass
class DiffSemantics:
    """Analyzed semantics of a git diff."""
    commit_type: str
    scope: str
    headline: str
    bullets: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    symbols_modified: List[str] = field(default_factory=list)
    raw_diff_tokens: int = 0


class LocalSemanticCommitSynthesizer:
    """Zero-cost local synthesizer for Conventional Commits and release notes."""

    @classmethod
    def get_git_diff(cls, repo_dir: str = ".", staged: bool = True) -> str:
        """Retrieves staged or unstaged git diff."""
        cmd = ["git", "diff", "--staged"] if staged else ["git", "diff"]
        try:
            res = subprocess.run(cmd, cwd=repo_dir, capture_output=True, text=True, encoding="utf-8", errors="replace")
            output = res.stdout
            if not output.strip() and staged:
                # Fallback to unstaged or HEAD~1 if staged is empty
                res2 = subprocess.run(["git", "diff", "HEAD~1"], cwd=repo_dir, capture_output=True, text=True, encoding="utf-8", errors="replace")
                output = res2.stdout
            return output
        except Exception:
            return ""

    @classmethod
    def analyze_diff(cls, diff_text: str) -> DiffSemantics:
        """Parses diff hunks and infers conventional commit type, scope, and bullets."""
        if not diff_text or not diff_text.strip():
            return DiffSemantics(
                commit_type="chore",
                scope="repo",
                headline="update codebase files",
                bullets=["general maintenance updates"]
            )

        file_patches = ASTFuzzyPatcher.parse_patch(diff_text)
        files = [fp.target_file or fp.source_file or "unknown" for fp in file_patches if fp.target_file or fp.source_file]

        # Extract symbols touched from hunk scopes and newly added definitions
        symbols = []
        for fp in file_patches:
            for h in fp.hunks:
                sym = ASTFuzzyPatcher.extract_symbol_name(h.symbol_scope)
                if sym and sym not in symbols:
                    symbols.append(sym)
                for nl in h.new_lines:
                    trimmed_nl = nl.strip()
                    m_def = re.match(r"^(?:async\s+)?(?:def|class|pub\s+fn|func|fn|struct|interface)\s+([A-Za-z0-9_]+)", trimmed_nl)
                    if m_def:
                        s_name = m_def.group(1)
                        if s_name not in symbols:
                            symbols.append(s_name)

        # Inferred scope
        scope = "core"
        if files:
            first = files[0].lower().replace("\\", "/")
            if "test" in first:
                scope = "tests"
            elif "benchmark" in first or "dashboard" in first:
                scope = "dashboard"
            elif "patch" in first:
                scope = "patcher"
            elif "polyglot" in first:
                scope = "polyglot"
            elif "packer" in first:
                scope = "packer"
            elif "features" in first:
                scope = "features"
            elif "mcp" in first:
                scope = "mcp"
            elif "vscode" in first or "extension" in first:
                scope = "vscode"
            else:
                base = os.path.basename(first).split(".")[0]
                scope = base.replace("tzero_", "").replace("_", "-")

        # Inferred type
        all_tests = all("test" in f.lower() for f in files) if files else False
        all_docs = all(f.lower().endswith((".md", ".rst", ".txt")) for f in files) if files else False

        diff_lower = diff_text.lower()
        has_fixes = any(w in diff_lower for w in ("fix", "bug", "error", "traceback", "exception", "failed", "crash"))
        has_tests = any("def test_" in diff_text or "class Test" in diff_text for _ in [1])
        has_new_defs = bool(re.search(r"^\+\s*(?:def|class|pub fn|func|struct)\s+[A-Za-z0-9_]+", diff_text, re.MULTILINE))

        if all_tests:
            commit_type = "test"
        elif all_docs:
            commit_type = "docs"
        elif has_new_defs:
            commit_type = "feat"
        elif has_fixes:
            commit_type = "fix"
        elif has_tests:
            commit_type = "test"
        else:
            commit_type = "refactor"

        # Generate descriptive bullets
        bullets = []
        for fp in file_patches:
            fname = fp.target_file or fp.source_file or "file"
            bname = os.path.basename(fname)
            hunk_count = len(fp.hunks)
            fp_syms = [ASTFuzzyPatcher.extract_symbol_name(h.symbol_scope) for h in fp.hunks]
            valid_syms = [s for s in fp_syms if s]
            if valid_syms:
                bullets.append(f"enhance `{bname}` ({', '.join(valid_syms[:3])})")
            else:
                bullets.append(f"update `{bname}` with {hunk_count} hunk{'s' if hunk_count > 1 else ''}")

        # Construct headline
        if symbols:
            top_sym = symbols[0]
            action = "add" if commit_type == "feat" else "update"
            headline = f"{action} {top_sym} and related AST capabilities"
        elif files:
            headline = f"improve {scope} components and workflow definitions"
        else:
            headline = "update workspace components"

        return DiffSemantics(
            commit_type=commit_type,
            scope=scope,
            headline=headline,
            bullets=bullets[:6],
            modified_files=files,
            symbols_modified=symbols,
            raw_diff_tokens=max(1, len(diff_text) // 4)
        )

    @classmethod
    def generate_commit_message(cls, repo_dir: str = ".", staged: bool = True, diff_override: Optional[str] = None) -> str:
        """Generates a Conventional Commit message from local AST git diff."""
        diff_text = diff_override if diff_override is not None else cls.get_git_diff(repo_dir=repo_dir, staged=staged)
        sem = cls.analyze_diff(diff_text)

        subject = f"{sem.commit_type}({sem.scope}): {sem.headline}"
        body_lines = [f"- {b}" for b in sem.bullets]
        body = "\n".join(body_lines)

        msg = f"{subject}\n\n{body}\n\nSigned-off-by: T-Zero Autonomous Local Synthesizer ($0 Local Engine)"
        return msg

    @classmethod
    def generate_changelog_entry(cls, version: str = "v8.1.0", repo_dir: str = ".") -> str:
        """Generates a Markdown release changelog entry from git history."""
        msg = cls.generate_commit_message(repo_dir=repo_dir, staged=True)
        sem = cls.analyze_diff(cls.get_git_diff(repo_dir=repo_dir, staged=True))

        return (
            f"## [{version}] - Local AST Release\n\n"
            f"### 🚀 {sem.commit_type.upper()}: {sem.scope.capitalize()}\n"
            + "\n".join(f"* {b}" for b in sem.bullets)
            + f"\n\n* **Modified Modules:** {len(sem.modified_files)} files\n"
            f"* **AST Symbols Touched:** {', '.join(sem.symbols_modified[:5]) or 'Internal Logic'}\n"
        )
