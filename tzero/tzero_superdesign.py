# -*- coding: utf-8 -*-
"""Siber Akademi T-Zero — Superdesign MCP Orchestrator Module.

Brings the open-source Superdesign AI design orchestrator capabilities natively to
MCP clients (Claude Code, Cursor, Antigravity IDE, Windsurf).

Operates as a design orchestrator providing structured specifications, design system
extraction, iterative refinement, and interactive HTML galleries without requiring
external API keys or cloud dependencies.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: MIT
"""

from __future__ import annotations

import html
import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

VALID_DESIGN_TYPES = {"ui", "wireframe", "component", "logo", "icon"}
VALID_FRAMEWORKS = {"html", "react", "vue"}

DEFAULT_DESIGN_SYSTEM = {
    "$schema": "https://superdesign.dev/schema/design-system.json",
    "name": "T-Zero Modern Design System",
    "version": "1.0.0",
    "theme": "dark",
    "colors": {
        "background": {
            "canvas": "#090d16",
            "surface": "#0f172a",
            "surface_hover": "#1e293b",
            "surface_active": "#334155"
        },
        "border": {
            "subtle": "#1e293b",
            "strong": "#334155",
            "focus": "#6366f1"
        },
        "text": {
            "primary": "#f8fafc",
            "secondary": "#94a3b8",
            "tertiary": "#64748b",
            "inverse": "#090d16"
        },
        "accent": {
            "primary": "#38bdf8",
            "primary_hover": "#0ea5e9",
            "secondary": "#818cf8",
            "success": "#34d399",
            "warning": "#fbbf24",
            "danger": "#f87171"
        }
    },
    "typography": {
        "fonts": {
            "ui": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            "mono": "'Fira Code', 'Geist Mono', Consolas, Monaco, monospace",
            "heading": "Inter, -apple-system, BlinkMacSystemFont, sans-serif"
        },
        "scale": {
            "xs": "0.75rem",
            "sm": "0.875rem",
            "base": "1rem",
            "lg": "1.125rem",
            "xl": "1.25rem",
            "2xl": "1.5rem",
            "3xl": "1.875rem",
            "4xl": "2.25rem"
        },
        "weights": {
            "normal": "400",
            "medium": "500",
            "semibold": "600",
            "bold": "700"
        }
    },
    "spacing": {
        "1": "0.25rem",
        "2": "0.5rem",
        "3": "0.75rem",
        "4": "1rem",
        "6": "1.5rem",
        "8": "2rem",
        "12": "3rem",
        "16": "4rem"
    },
    "radii": {
        "sm": "0.25rem",
        "md": "0.5rem",
        "lg": "0.75rem",
        "xl": "1rem",
        "full": "9999px"
    },
    "shadows": {
        "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.4)",
        "md": "0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -2px rgba(0, 0, 0, 0.5)",
        "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.6), 0 4px 6px -4px rgba(0, 0, 0, 0.6)"
    }
}


def _slugify(text: str) -> str:
    """Converts a descriptive string to a filesystem-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:36].strip("_") or "design"


def _ensure_superdesign_dirs(workspace_path: str = ".") -> Tuple[str, str]:
    """Ensures that superdesign/design_iterations and superdesign/design_system exist."""
    base_dir = os.path.join(workspace_path, "superdesign")
    iterations_dir = os.path.join(base_dir, "design_iterations")
    systems_dir = os.path.join(base_dir, "design_system")
    os.makedirs(iterations_dir, exist_ok=True)
    os.makedirs(systems_dir, exist_ok=True)
    return iterations_dir, systems_dir


def superdesign_generate(
    prompt: str,
    design_type: str = "ui",
    variations: int = 3,
    framework: str = "html",
    workspace_path: str = ".",
) -> Dict[str, Any]:
    """Generates structured specifications and guidelines for the LLM to create designs."""
    d_type = (design_type or "ui").lower().strip()
    if d_type not in VALID_DESIGN_TYPES:
        return {
            "success": False,
            "error": f"Invalid design_type '{design_type}'. Must be one of: {sorted(list(VALID_DESIGN_TYPES))}",
        }

    fw = (framework or "html").lower().strip()
    if fw not in VALID_FRAMEWORKS:
        fw = "html"

    variations = max(1, min(int(variations or 3), 5))
    iterations_dir, _ = _ensure_superdesign_dirs(workspace_path)
    slug = _slugify(prompt)

    ext_map = {
        "ui": ".html",
        "wireframe": ".html",
        "component": ".html" if fw == "html" else (".tsx" if fw == "react" else ".vue"),
        "logo": ".svg",
        "icon": ".svg",
    }
    ext = ext_map.get(d_type, ".html")

    files_to_create = []
    for i in range(1, variations + 1):
        filename = f"{d_type}_{slug}_v{i}{ext}"
        rel_path = os.path.join("superdesign", "design_iterations", filename).replace("\\", "/")
        files_to_create.append({
            "variation": i,
            "filename": filename,
            "file_path": rel_path,
            "full_path": os.path.abspath(os.path.join(iterations_dir, filename)),
        })

    guidelines = [
        "1. Avoid generic AI aesthetics (neon glow spam, wall-of-emojis, tacky cyberpunk badges).",
        "2. Use curated, accessible color palettes: slate/zinc neutral surfaces (#090d16, #0f172a, #1e293b).",
        "3. Typography: Prioritize modern clean typefaces (Inter, Geist, Fira Code monospace).",
        "4. Layout: Implement responsive mobile-first flexbox/grid with clear visual hierarchy.",
        "5. Self-Contained: Include all CSS and necessary SVG icons inline so each file opens standalone in any browser.",
    ]
    if d_type == "wireframe":
        guidelines.append("6. Wireframe Mode: Strictly monochrome (black, white, greys) with wire-box indicators for imagery.")
    elif d_type in {"logo", "icon"}:
        guidelines.append("6. Vector SVG: Use viewBox='0 0 24 24' (or 100 100), clean paths, stroke-width=2, and semantic layers.")

    specifications = {
        "design_orchestrator": "Superdesign MCP v1.0 (T-Zero Edition)",
        "prompt": prompt,
        "design_type": d_type,
        "framework": fw,
        "variations_requested": variations,
        "design_system_reference": "superdesign/design_system/tzero_design_system.json",
        "core_guidelines": guidelines,
        "instructions_for_claude": (
            f"Generate {variations} complete, production-ready, beautiful variations of the requested {d_type}. "
            f"Write the output code directly into the target files listed under 'files_to_create'. "
            "Ensure the visual presentation feels high-end, crisp, and completely free of AI slop."
        ),
    }

    return {
        "success": True,
        "design_type": d_type,
        "framework": fw,
        "variations": variations,
        "files_to_create": files_to_create,
        "specifications": specifications,
    }


def superdesign_iterate(
    design_file: str,
    feedback: str,
    variations: int = 1,
    workspace_path: str = ".",
) -> Dict[str, Any]:
    """Generates structured iteration instructions to refine an existing design file."""
    if not design_file or not os.path.exists(design_file):
        return {
            "success": False,
            "error": f"Design file '{design_file}' was not found. Please provide an existing design file path.",
        }

    variations = max(1, min(int(variations or 1), 5))
    iterations_dir, _ = _ensure_superdesign_dirs(workspace_path)

    base_name = os.path.basename(design_file)
    name_no_ext, ext = os.path.splitext(base_name)
    # Detect version tag or append _iter
    v_match = re.search(r"_v(\d+)$", name_no_ext)
    current_ver = int(v_match.group(1)) if v_match else 1

    target_files = []
    for i in range(1, variations + 1):
        next_ver = current_ver + i
        if v_match:
            new_name = re.sub(r"_v\d+$", f"_v{next_ver}", name_no_ext) + ext
        else:
            new_name = f"{name_no_ext}_v{next_ver}{ext}"
        rel_path = os.path.join("superdesign", "design_iterations", new_name).replace("\\", "/")
        target_files.append({
            "variation": i,
            "target_path": rel_path,
            "full_path": os.path.abspath(os.path.join(iterations_dir, new_name)),
        })

    try:
        with open(design_file, "r", encoding="utf-8", errors="ignore") as f:
            original_code = f.read()
    except Exception as e:
        original_code = f"<!-- Error reading original file: {e} -->"

    return {
        "success": True,
        "design_file": design_file,
        "feedback": feedback,
        "variations": variations,
        "target_files": target_files,
        "original_code_snippet": original_code[:1200] + ("..." if len(original_code) > 1200 else ""),
        "iteration_instructions": {
            "goal": "Refine the original design incorporating the user feedback while preserving core layout integrity.",
            "feedback_to_apply": feedback,
            "superdesign_principles": [
                "Preserve component consistency and spacing rhythm (4px/8px grid).",
                "Ensure contrast ratios meet WCAG AA standards.",
                "Polish micro-interactions, hover states, and smooth CSS transitions.",
                "Avoid introducing visual clutter or artificial AI tropes.",
            ],
            "execution_note": "Write the improved code into the target files specified in 'target_files'.",
        },
    }


def superdesign_extract_system(
    input_path_or_description: str,
    system_name: str = "custom",
    workspace_path: str = ".",
) -> Dict[str, Any]:
    """Extracts or initializes a structured JSON design system with modern tokens."""
    _, systems_dir = _ensure_superdesign_dirs(workspace_path)
    clean_name = _slugify(system_name) or "design_system"
    system_file = os.path.join(systems_dir, f"{clean_name}.json")

    tokens = json.loads(json.dumps(DEFAULT_DESIGN_SYSTEM))
    tokens["name"] = f"Superdesign System: {system_name.replace('_', ' ').title()}"
    tokens["description"] = f"Extracted design system for: {input_path_or_description}"
    tokens["extracted_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    with open(system_file, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)

    return {
        "success": True,
        "system_name": clean_name,
        "file_path": system_file.replace("\\", "/"),
        "design_system": tokens,
        "usage_instructions": (
            f"Design system tokens saved to '{system_file}'. "
            "Reference these CSS custom properties in your HTML, React, and Vue components."
        ),
    }


def superdesign_list(workspace_path: str = ".") -> Dict[str, Any]:
    """Enumerates all Superdesign creations and extracted design systems."""
    iterations_dir, systems_dir = _ensure_superdesign_dirs(workspace_path)

    iterations = []
    if os.path.isdir(iterations_dir):
        for fname in sorted(os.listdir(iterations_dir)):
            full_p = os.path.join(iterations_dir, fname)
            if os.path.isfile(full_p):
                ext = os.path.splitext(fname)[1].lower()
                dtype = "ui"
                if fname.startswith("wireframe_"):
                    dtype = "wireframe"
                elif fname.startswith("component_"):
                    dtype = "component"
                elif fname.startswith("logo_"):
                    dtype = "logo"
                elif fname.startswith("icon_"):
                    dtype = "icon"

                iterations.append({
                    "filename": fname,
                    "design_type": dtype,
                    "extension": ext,
                    "relative_path": os.path.join("superdesign", "design_iterations", fname).replace("\\", "/"),
                    "size_bytes": os.path.getsize(full_p),
                    "modified_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(full_p))),
                })

    systems = []
    if os.path.isdir(systems_dir):
        for fname in sorted(os.listdir(systems_dir)):
            full_p = os.path.join(systems_dir, fname)
            if os.path.isfile(full_p) and fname.endswith(".json"):
                systems.append({
                    "filename": fname,
                    "relative_path": os.path.join("superdesign", "design_system", fname).replace("\\", "/"),
                    "size_bytes": os.path.getsize(full_p),
                })

    return {
        "success": True,
        "total_iterations": len(iterations),
        "total_design_systems": len(systems),
        "iterations": iterations,
        "design_systems": systems,
    }


def superdesign_gallery(workspace_path: str = ".") -> Dict[str, Any]:
    """Builds a responsive, interactive HTML gallery previewing all designs in superdesign/."""
    iterations_dir, _ = _ensure_superdesign_dirs(workspace_path)
    gallery_file = os.path.join(workspace_path, "superdesign", "gallery.html")

    list_data = superdesign_list(workspace_path=workspace_path)
    items = list_data.get("iterations", [])

    cards_html = []
    for idx, item in enumerate(items):
        fn = html.escape(item["filename"])
        dtype = html.escape(item["design_type"].upper())
        mod = html.escape(item["modified_time"])
        rel_p = html.escape(f"design_iterations/{item['filename']}")
        ext = item["extension"]

        if ext == ".svg":
            # Read inline SVG for instant preview
            svg_path = os.path.join(iterations_dir, item["filename"])
            try:
                with open(svg_path, "r", encoding="utf-8", errors="ignore") as sf:
                    svg_raw = sf.read()
                    # Strip xml header if present
                    svg_raw = re.sub(r"<\?xml.*?\?>", "", svg_raw).strip()
            except Exception:
                svg_raw = "<div style='color:#ef4444;'>Failed to load SVG</div>"
            preview_content = f"<div class='svg-frame'>{svg_raw}</div>"
        else:
            preview_content = f"<iframe src='{rel_p}' loading='lazy' class='preview-iframe' title='{fn}'></iframe>"

        card = f"""
        <div class="gallery-card" data-type="{item['design_type']}">
          <div class="card-preview">
            {preview_content}
            <div class="preview-overlay">
              <button class="btn-action" onclick="openModal('{rel_p}', '{fn}')">Preview Full</button>
            </div>
          </div>
          <div class="card-meta">
            <div class="card-header">
              <span class="badge badge-{item['design_type']}">{dtype}</span>
              <span class="card-date">{mod}</span>
            </div>
            <div class="card-title" title="{fn}">{fn}</div>
            <div class="card-footer">
              <button class="btn-copy" onclick="copyPath('{item['relative_path']}', this)">Copy Path</button>
              <a href="{rel_p}" target="_blank" class="btn-link">Open &nearr;</a>
            </div>
          </div>
        </div>
        """
        cards_html.append(card)

    cards_joined = "\n".join(cards_html) if cards_html else (
        "<div class='empty-state'>"
        "<h3>No Designs Yet</h3>"
        "<p>Run <code>superdesign_generate</code> to create your first clean UI, wireframe, or component.</p>"
        "</div>"
    )

    gallery_html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Superdesign Gallery — T-Zero Design Canvas</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #090d16;
      --surface: #0f172a;
      --surface-elevated: #1e293b;
      --border: #1e293b;
      --border-focus: #38bdf8;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --accent-indigo: #818cf8;
      --radius: 10px;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'Inter', -apple-system, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    header {{
      padding: 20px 36px;
      border-bottom: 1px solid var(--border);
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(16px);
      position: sticky;
      top: 0;
      z-index: 50;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .brand-logo {{
      width: 32px;
      height: 32px;
      background: linear-gradient(135deg, var(--accent), var(--accent-indigo));
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      color: #090d16;
    }}
    .brand-title {{
      font-size: 18px;
      font-weight: 700;
      letter-spacing: -0.02em;
    }}
    .filter-bar {{
      display: flex;
      gap: 8px;
    }}
    .filter-btn {{
      background: var(--surface);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 6px 14px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .filter-btn:hover, .filter-btn.active {{
      background: var(--surface-elevated);
      color: var(--text);
      border-color: var(--accent);
    }}
    main {{
      flex: 1;
      padding: 36px;
      max-width: 1440px;
      margin: 0 auto;
      width: 100%;
    }}
    .gallery-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
      gap: 24px;
    }}
    .gallery-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: hidden;
      display: flex;
      flex-direction: column;
      transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    }}
    .gallery-card:hover {{
      transform: translateY(-3px);
      border-color: #334155;
      box-shadow: 0 12px 24px -10px rgba(0, 0, 0, 0.6);
    }}
    .card-preview {{
      height: 220px;
      background: #060910;
      position: relative;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      border-bottom: 1px solid var(--border);
    }}
    .preview-iframe {{
      width: 200%;
      height: 200%;
      transform: scale(0.5);
      transform-origin: top left;
      border: none;
      pointer-events: none;
    }}
    .svg-frame {{
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }}
    .svg-frame svg {{
      max-width: 100%;
      max-height: 100%;
    }}
    .preview-overlay {{
      position: absolute;
      inset: 0;
      background: rgba(9, 13, 22, 0.7);
      backdrop-filter: blur(4px);
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0;
      transition: opacity 0.2s ease;
    }}
    .card-preview:hover .preview-overlay {{
      opacity: 1;
    }}
    .btn-action {{
      background: var(--accent);
      color: #090d16;
      border: none;
      padding: 8px 16px;
      border-radius: 6px;
      font-weight: 600;
      font-size: 13px;
      cursor: pointer;
    }}
    .card-meta {{
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .badge {{
      font-size: 11px;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .badge-ui {{ background: rgba(56, 189, 248, 0.15); color: #38bdf8; }}
    .badge-wireframe {{ background: rgba(148, 163, 184, 0.15); color: #94a3b8; }}
    .badge-component {{ background: rgba(129, 140, 248, 0.15); color: #818cf8; }}
    .badge-logo, .badge-icon {{ background: rgba(52, 211, 153, 0.15); color: #34d399; }}
    .card-date {{
      font-size: 11px;
      color: var(--text-muted);
      font-family: 'Fira Code', monospace;
    }}
    .card-title {{
      font-size: 14px;
      font-weight: 600;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .card-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 4px;
      padding-top: 10px;
      border-top: 1px solid var(--border);
    }}
    .btn-copy {{
      background: transparent;
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 4px 10px;
      border-radius: 4px;
      font-size: 12px;
      cursor: pointer;
    }}
    .btn-copy:hover {{
      color: var(--text);
      border-color: #334155;
    }}
    .btn-link {{
      color: var(--accent);
      text-decoration: none;
      font-size: 13px;
      font-weight: 500;
    }}
    .empty-state {{
      grid-column: 1 / -1;
      text-align: center;
      padding: 80px 20px;
      color: var(--text-muted);
    }}
    .empty-state h3 {{
      color: var(--text);
      font-size: 20px;
      margin-bottom: 8px;
    }}
    /* Modal */
    .modal-backdrop {{
      position: fixed;
      inset: 0;
      background: rgba(9, 13, 22, 0.85);
      backdrop-filter: blur(8px);
      z-index: 1000;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }}
    .modal-backdrop.open {{ display: flex; }}
    .modal-container {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      width: 90vw;
      height: 85vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }}
    .modal-header {{
      padding: 14px 20px;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .modal-body {{
      flex: 1;
      background: #fff;
    }}
    .modal-body iframe {{
      width: 100%;
      height: 100%;
      border: none;
    }}
    .btn-close {{
      background: none;
      border: none;
      color: var(--text-muted);
      font-size: 22px;
      cursor: pointer;
    }}
    .btn-close:hover {{ color: var(--text); }}
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="brand-logo">&Sigma;</div>
      <div class="brand-title">Superdesign Canvas</div>
    </div>
    <div class="filter-bar">
      <button class="filter-btn active" onclick="filterGallery('all')">All</button>
      <button class="filter-btn" onclick="filterGallery('ui')">UI</button>
      <button class="filter-btn" onclick="filterGallery('component')">Components</button>
      <button class="filter-btn" onclick="filterGallery('wireframe')">Wireframes</button>
      <button class="filter-btn" onclick="filterGallery('logo')">Logos &amp; Icons</button>
    </div>
  </header>
  <main>
    <div class="gallery-grid" id="gallery-grid">
      {cards_joined}
    </div>
  </main>

  <div class="modal-backdrop" id="preview-modal" onclick="closeModal(event)">
    <div class="modal-container" onclick="event.stopPropagation()">
      <div class="modal-header">
        <span id="modal-title" style="font-weight:600;font-size:14px;"></span>
        <button class="btn-close" onclick="closeModalDirect()">&times;</button>
      </div>
      <div class="modal-body">
        <iframe id="modal-frame" src="about:blank"></iframe>
      </div>
    </div>
  </div>

  <script>
    function filterGallery(type) {{
      document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
      event.target.classList.add('active');
      const cards = document.querySelectorAll('.gallery-card');
      cards.forEach(card => {{
        if (type === 'all' || card.dataset.type === type || (type === 'logo' && (card.dataset.type === 'logo' || card.dataset.type === 'icon'))) {{
          card.style.display = 'flex';
        }} else {{
          card.style.display = 'none';
        }}
      }});
    }}
    function openModal(src, title) {{
      document.getElementById('modal-title').textContent = title;
      document.getElementById('modal-frame').src = src;
      document.getElementById('preview-modal').classList.add('open');
    }}
    function closeModal(e) {{
      if (e.target.id === 'preview-modal') {{
        closeModalDirect();
      }}
    }}
    function closeModalDirect() {{
      document.getElementById('preview-modal').classList.remove('open');
      document.getElementById('modal-frame').src = 'about:blank';
    }}
    document.addEventListener('keydown', (e) => {{
      if (e.key === 'Escape') closeModalDirect();
    }});
    function copyPath(text, btn) {{
      navigator.clipboard.writeText(text).then(() => {{
        const original = btn.textContent;
        btn.textContent = 'Copied!';
        setTimeout(() => {{ btn.textContent = original; }}, 1500);
      }});
    }}
  </script>
</body>
</html>"""

    with open(gallery_file, "w", encoding="utf-8") as gf:
        gf.write(gallery_html_content)

    return {
        "success": True,
        "gallery_file": gallery_file.replace("\\", "/"),
        "total_items": len(items),
        "url_hint": f"Open file://{os.path.abspath(gallery_file)} in any browser to inspect all designs.",
    }
