# -*- coding: utf-8 -*-
"""Deterministic Emoji Scrubber for Markdown & HTML Headings.

Removes leading emojis and pictographs from headings (#, ##, ###, <h2>, etc.)
and code-block sub-section headers while preserving all text, code, formatting,
HTML IDs, and internal link anchors.
"""

import re
import pathlib

# Matches Unicode emoji ranges, dingbats, miscellaneous symbols, pictographs, variation selectors
EMOJI_CHARS = (
    r"[\U00010000-\U0010ffff"
    r"\u2600-\u27bf"
    r"\u2300-\u23ff"
    r"\u2b50\u2b55\u200d\ufe0f\u20e3"
    r"\u2190-\u21ff\u2900-\u297f\u3030\u303d\u3297\u3299"
    r"\U0001f300-\U0001f5ff"
    r"\U0001f600-\U0001f64f"
    r"\U0001f680-\U0001f6ff"
    r"\U0001f700-\U0001f77f"
    r"\U0001f780-\U0001f7ff"
    r"\U0001f800-\U0001f8ff"
    r"\U0001f900-\U0001f9ff"
    r"\U0001fa00-\U0001fa6f"
    r"\U0001fa70-\U0001faff]"
)

# 1. Markdown heading pattern: ^(>*\s*#{1,6}\s+)(emojis...)\s*(.*)$
MD_HEADING_RE = re.compile(
    rf"^(>*\s*#{{1,6}}\s+)(?:{EMOJI_CHARS}+\s*)+(.*)$"
)

# 2. Code comment header pattern: ^(\s*#\s+)(emojis...)\s*(Option [A-Z]|1-Click|Download|Install|Run|Output|Seçenek [A-Z]|Tek Tıkla|选项 [A-Z]|一键|启动|選択肢 [A-Z])(.*)$
CODE_COMMENT_HEADING_RE = re.compile(
    rf"^(\s*#\s+)(?:{EMOJI_CHARS}+\s*)+(.*)$"
)

# 3. HTML heading pattern: (<h[1-6][^>]*>)(emojis...)\s*(.*</h[1-6]>)
HTML_HEADING_RE = re.compile(
    rf"(<h[1-6][^>]*>)\s*(?:{EMOJI_CHARS}+\s*)+(.*?</h[1-6]>)",
    re.IGNORECASE
)


def clean_markdown_content(text: str) -> tuple[str, int]:
    lines = text.splitlines(keepends=True)
    out = []
    count = 0
    in_code_block = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            out.append(line)
            continue

        if not in_code_block:
            # Check markdown heading
            m = MD_HEADING_RE.match(line)
            if m:
                prefix = m.group(1)
                rest = m.group(2).strip()
                newline = "\n" if line.endswith("\n") else ""
                out.append(f"{prefix}{rest}{newline}")
                count += 1
                continue
        else:
            # Inside code block, clean comments that have emojis followed by text like Option A, 1-Click, etc.
            m = CODE_COMMENT_HEADING_RE.match(line)
            if m:
                prefix = m.group(1)
                rest = m.group(2).strip()
                newline = "\n" if line.endswith("\n") else ""
                out.append(f"{prefix}{rest}{newline}")
                count += 1
                continue

        out.append(line)

    return "".join(out), count


def clean_html_content(text: str) -> tuple[str, int]:
    count = 0

    def repl(m):
        nonlocal count
        count += 1
        return f"{m.group(1)}{m.group(2)}"

    new_text, n = HTML_HEADING_RE.subn(repl, text)
    return new_text, n


def process_file(path: pathlib.Path) -> int:
    content = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".html":
        new_content, count = clean_html_content(content)
    else:
        new_content, count = clean_markdown_content(content)

    if count > 0:
        path.write_text(new_content, encoding="utf-8")
        print(f"[CLEANED] {path} ({count} headings stripped)")
    else:
        print(f"[UNCHANGED] {path}")
    return count


def discover_target_files(root: pathlib.Path) -> list[pathlib.Path]:
    ignored_dirs = {".git", ".venv", "venv", "node_modules", "build", "dist", "__pycache__"}
    targets = []
    for p in root.rglob("*"):
        if any(part in ignored_dirs for part in p.parts):
            continue
        if p.is_file() and p.suffix.lower() in {".md", ".html"}:
            targets.append(p)
    return sorted(targets)


if __name__ == "__main__":
    import sys
    check_mode = "--check" in sys.argv
    root = pathlib.Path(__file__).resolve().parent.parent

    target_files = discover_target_files(root)
    total_cleaned = 0
    violations = []

    for p in target_files:
        content = p.read_text(encoding="utf-8", errors="ignore")
        if check_mode:
            in_code = False
            for line_no, line in enumerate(content.splitlines(), start=1):
                if line.strip().startswith("```"):
                    in_code = not in_code
                    continue
                if not in_code and re.match(r"^\s*#{1,6}\s+", line):
                    if MD_HEADING_RE.match(line):
                        violations.append(f"{p.relative_to(root)}:{line_no} -> {line.strip()}")
        else:
            total_cleaned += process_file(p)

    if check_mode:
        if violations:
            print(f"Found {len(violations)} headings starting with emojis:")
            for v in violations:
                print(f"  {v}")
            sys.exit(1)
        else:
            print("Check passed: 0 headings start with emojis.")
            sys.exit(0)
    else:
        print(f"\nCompleted! Total headings cleaned: {total_cleaned}")
