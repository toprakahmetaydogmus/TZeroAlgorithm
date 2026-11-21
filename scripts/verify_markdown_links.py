# -*- coding: utf-8 -*-
"""Markdown Link and Anchor Verifier for T-Zero Documentation.

Validates all internal anchors, cross-document relative links, and anchor tags
across English, Turkish, Japanese, and Chinese documentation suites.
"""

import pathlib
import re
import sys


def extract_anchors(content: str) -> set:
    """Extract all explicit HTML anchors and GitHub slugified markdown header anchors."""
    # 1. Explicit HTML anchors: <a id="..."> or <a name="...">
    explicit_anchors = set(
        re.findall(r'<a\s+[^>]*(?:id|name)=["\']([^"\']+)["\']', content, re.IGNORECASE)
    )

    # 2. Markdown headers (including callout/blockquote headers: > ### ...)
    headers = re.findall(r'^(?:>\s*)?#{1,6}\s+(.+)$', content, re.MULTILINE)
    slugified_headers = set()

    for h in headers:
        # Strip HTML tags
        clean_h = re.sub(r'<[^>]+>', '', h)
        # Strip markdown images and links
        clean_h = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', clean_h)
        clean_h = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_h)
        # Strip formatting marks (bold, italic, backticks)
        clean_h = re.sub(r'[`*_~]', '', clean_h).strip()

        # GitHub slugify: remove punctuation except hyphens/underscores/spaces
        slug = re.sub(r'[^\w\s-]', '', clean_h.lower())
        slug = re.sub(r'[\s_]+', '-', slug).strip('-')
        if slug:
            slugified_headers.add(slug)

    return explicit_anchors | slugified_headers


def extract_links(content: str) -> list:
    """Extract all markdown links (including nested badge image links) and HTML href targets."""
    targets = []

    # 1. Markdown links: [label](target) or [![alt](img)](target)
    md_links = re.findall(r'\[(?:!\[[^\]]*\]\([^)]+\)|[^\]]+)\]\(([^)]+)\)', content)
    for t in md_links:
        targets.append(t.strip())

    # 2. HTML hrefs: <a href="target">
    html_hrefs = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\']', content, re.IGNORECASE)
    for t in html_hrefs:
        targets.append(t.strip())

    return targets


def check_file(path_str: str) -> bool:
    """Verify all internal and relative links in a documentation file."""
    p = pathlib.Path(path_str)
    if not p.is_file():
        print(f"[FAIL] File not found: {path_str}")
        return False

    content = p.read_text(encoding="utf-8")
    base_dir = p.parent
    all_anchors = extract_anchors(content)
    lower_anchors = {a.lower() for a in all_anchors}

    raw_targets = extract_links(content)
    has_errors = False
    checked_count = 0

    print(f"\nVerifying: {path_str}")

    for target in raw_targets:
        # Ignore external web links and non-file schemes
        if target.startswith(('http://', 'https://', 'mailto:', 'tel:', 'data:', 'javascript:')):
            continue

        checked_count += 1

        # Case A: Pure internal anchor link (#anchor)
        if target.startswith('#'):
            anchor = target[1:].split('?')[0]
            if anchor not in all_anchors and anchor.lower() not in lower_anchors:
                print(f"  [BROKEN ANCHOR] #{anchor}")
                has_errors = True
            continue

        # Case B: Relative file path with optional anchor (file.md#anchor)
        file_part = target.split('#')[0].split('?')[0]
        anchor_part = target.split('#')[1].split('?')[0] if '#' in target else None

        if file_part:
            target_path = (base_dir / file_part).resolve()
            if not target_path.exists():
                print(f"  [BROKEN FILE LINK] {target} -> missing: {target_path}")
                has_errors = True
                continue

            if anchor_part and target_path.is_file():
                target_content = target_path.read_text(encoding="utf-8", errors="ignore")
                target_anchors = extract_anchors(target_content)
                target_lower = {a.lower() for a in target_anchors}
                if anchor_part not in target_anchors and anchor_part.lower() not in target_lower:
                    print(f"  [BROKEN REMOTE ANCHOR] {target} -> #{anchor_part} missing in {target_path.name}")
                    has_errors = True

    if not has_errors:
        print(f"  [OK] All {checked_count} internal anchors and relative file links are valid.")
    return not has_errors


if __name__ == "__main__":
    files = ["README.md", "docs/README.tr.md", "docs/README.ja.md", "docs/README.zh.md"]
    all_ok = True
    for f in files:
        if not check_file(f):
            all_ok = False
    sys.exit(0 if all_ok else 1)
