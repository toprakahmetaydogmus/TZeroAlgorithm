# -*- coding: utf-8 -*-
"""Markdown Link and Anchor Verifier for T-Zero Documentation."""

import re
import pathlib
import sys

def check_file(path_str):
    p = pathlib.Path(path_str)
    if not p.is_file():
        print(f"File not found: {path_str}")
        return False

    content = p.read_text(encoding="utf-8")
    base_dir = p.parent

    # 1. Collect HTML anchors: <a id="..."></a> or <a name="..."></a>
    explicit_anchors = set(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)["\']', content, re.IGNORECASE))

    # 2. Collect Markdown headers: # Header Name
    headers = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
    # GitHub markdown slugification rule:
    # lowercase, remove punctuation except hyphens, spaces to hyphens
    slugified_headers = set()
    for h in headers:
        clean_h = re.sub(r'<[^>]+>', '', h).strip()
        slug = re.sub(r'[^\w\s-]', '', clean_h.lower())
        slug = re.sub(r'[\s_]+', '-', slug).strip('-')
        slugified_headers.add(slug)

    all_anchors = explicit_anchors | slugified_headers

    has_errors = False
    print(f"\nVerifying: {path_str}")

    # Check internal anchor links: [label](#anchor)
    internal_links = re.findall(r'\[([^\]]+)\]\(#([^\)]+)\)', content)
    for label, anchor in internal_links:
        # Also clean any query params if present
        clean_anchor = anchor.split('?')[0].lower()
        if anchor not in all_anchors and clean_anchor not in {a.lower() for a in all_anchors}:
            print(f"  [BROKEN ANCHOR] [{label}](#{anchor})")
            has_errors = True

    # Check file links: [label](path)
    # Match markdown links that do not start with http, mailto, tel, #
    raw_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
    for label, url in raw_links:
        if url.startswith(('http://', 'https://', 'mailto:', '#', 'tel:', 'data:')):
            continue
        file_part = url.split('#')[0].split('?')[0]
        anchor_part = url.split('#')[1] if '#' in url else None
        if file_part:
            target_path = (base_dir / file_part).resolve()
            if not target_path.exists():
                print(f"  [BROKEN FILE LINK] [{label}]({url}) -> missing file: {target_path}")
                has_errors = True
            elif anchor_part and target_path.is_file():
                # check anchor in target file
                target_content = target_path.read_text(encoding="utf-8", errors="ignore")
                target_explicit = set(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)["\']', target_content, re.IGNORECASE))
                target_headers = re.findall(r'^#{1,6}\s+(.+)$', target_content, re.MULTILINE)
                target_slugs = set()
                for th in target_headers:
                    cth = re.sub(r'<[^>]+>', '', th).strip()
                    tslug = re.sub(r'[^\w\s-]', '', cth.lower())
                    tslug = re.sub(r'[\s_]+', '-', tslug).strip('-')
                    target_slugs.add(tslug)
                target_all = target_explicit | target_slugs
                if anchor_part not in target_all and anchor_part.lower() not in {a.lower() for a in target_all}:
                    print(f"  [BROKEN REMOTE ANCHOR] [{label}]({url}) -> anchor #{anchor_part} not in {target_path.name}")
                    has_errors = True

    if not has_errors:
        print("  [OK] All internal anchors and relative file links are valid.")
    return not has_errors

if __name__ == "__main__":
    files = ["README.md", "docs/README.tr.md", "docs/README.ja.md", "docs/README.zh.md"]
    all_ok = True
    for f in files:
        if not check_file(f):
            all_ok = False
    sys.exit(0 if all_ok else 1)
