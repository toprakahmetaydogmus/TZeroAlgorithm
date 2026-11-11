# -*- coding: utf-8 -*-
"""Single-source release metadata and package synchronizer for T-Zero."""

import argparse
import json
import pathlib
import re
import shutil
import tomllib
from typing import Dict, List

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent


def _update_json_version(path: pathlib.Path, version: str, keys: List[str], check_only: bool) -> bool:
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for key in keys:
        if key == "packages[0].version":
            if data["packages"][0]["version"] != version:
                data["packages"][0]["version"] = version
                changed = True
        elif data.get(key) != version:
            data[key] = version
            changed = True
    if changed and not check_only:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changed


def _regex_replace(path: pathlib.Path, pattern: str, repl: str, check_only: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    new_text, count = re.subn(pattern, repl, text)
    changed = count > 0 and new_text != text
    if changed and not check_only:
        path.write_text(new_text, encoding="utf-8")
    return changed


def sync_release_metadata(target_version: str, check_only: bool = False) -> Dict[str, bool]:
    """Synchronizes release versions across Python, MCP, npm, Brew, and VS Code manifests."""
    results: Dict[str, bool] = {}

    results["pyproject.toml"] = _regex_replace(
        ROOT_DIR / "pyproject.toml",
        r'(?m)^(version\s*=\s*)"[^"]+"',
        rf'\1"{target_version}"',
        check_only,
    )
    results["server.json"] = _update_json_version(
        ROOT_DIR / "server.json", target_version, ["version", "packages[0].version"], check_only
    )
    results["smithery.json"] = _update_json_version(
        ROOT_DIR / "smithery.json", target_version, ["version"], check_only
    )
    results["glama.json"] = _update_json_version(
        ROOT_DIR / "glama.json", target_version, ["version"], check_only
    )
    results["installers/npm/package.json"] = _update_json_version(
        ROOT_DIR / "installers" / "npm" / "package.json", target_version, ["version"], check_only
    )
    results["extensions/vscode/package.json"] = _update_json_version(
        ROOT_DIR / "extensions" / "vscode" / "package.json", target_version, ["version"], check_only
    )

    for rel in ("Formula/tzero.rb", "installers/brew/tzero.rb"):
        p = ROOT_DIR / rel
        c1 = _regex_replace(p, r'refs/tags/v[0-9]+\.[0-9]+\.[0-9]+\.tar\.gz', f"refs/tags/v{target_version}.tar.gz", check_only)
        c2 = _regex_replace(p, r'(?m)^(\s*version\s+)"[^"]+"', rf'\1"{target_version}"', check_only)
        results[rel] = c1 or c2

    results["tzero_mcp.py"] = _regex_replace(
        ROOT_DIR / "tzero" / "tzero_mcp.py",
        r'(?m)^(SERVER_VERSION\s*=\s*)"[^"]+"',
        rf'\1"{target_version}"',
        check_only,
    )

    addmcp_p = ROOT_DIR / "addmcp.py"
    c_app = _regex_replace(addmcp_p, r'(?m)^(APP_VERSION\s*=\s*)"[^"]+"', rf'\1"{target_version}"', check_only)
    c_ban = _regex_replace(addmcp_p, r'1-CLICK MCP INITIALIZATION \(v[0-9]+\.[0-9]+\.[0-9]+\)', f"1-CLICK MCP INITIALIZATION (v{target_version})", check_only)
    results["addmcp.py"] = c_app or c_ban

    tb_p = ROOT_DIR / "tzero" / "tzero_task_benchmark.py"
    c_tb1 = _regex_replace(tb_p, r'(?m)^(\s*version:\s*str\s*=\s*)"[^"]+"', rf'\1"{target_version}"', check_only)
    c_tb2 = _regex_replace(tb_p, r'BENCHMARK REPORT \(v[0-9]+\.[0-9]+\.[0-9]+\)', f"BENCHMARK REPORT (v{target_version})", check_only)
    results["tzero_task_benchmark.py"] = c_tb1 or c_tb2

    v3_p = ROOT_DIR / "tzero" / "tzero_v3.py"
    c_v1 = _regex_replace(v3_p, r'(T-Zero (?:Developer Console & Context Architect|Geliştirici Konsolu & Bağlam Mimarı) )v[0-9]+\.[0-9]+\.[0-9]+', rf'\1v{target_version}', check_only)
    c_v2 = _regex_replace(v3_p, r'(parser\.add_argument\("--changelog"[^\n]*const=)"v[^"]+"', rf'\1"v{target_version}"', check_only)
    c_v3 = _regex_replace(v3_p, r'(Context Architect )v[0-9]+\.[0-9]+\.[0-9]+( Master Edition)', rf'\1v{target_version}\2', check_only)
    c_v4 = _regex_replace(v3_p, r'(CONTEXT ARCHITECT & MCP )v[0-9]+\.[0-9]+\.[0-9]+( MASTER)', rf'\1v{target_version}\2', check_only)
    c_v5 = _regex_replace(v3_p, r'(GRADIO COCKPIT \()v[0-9]+\.[0-9]+\.[0-9]+(\))', rf'\1v{target_version}\2', check_only)
    results["tzero_v3.py"] = any((c_v1, c_v2, c_v3, c_v4, c_v5))

    tui_p = ROOT_DIR / "tzero" / "tzero_tui.py"
    c_t1 = _regex_replace(tui_p, r'(LIVE COCKPIT )v[0-9]+\.[0-9]+\.[0-9]+', rf'\1v{target_version}', check_only)
    c_t2 = _regex_replace(tui_p, r'(generate_changelog_entry\(version=)"v[0-9]+\.[0-9]+\.[0-9]+"', rf'\1"v{target_version}"', check_only)
    results["tzero_tui.py"] = c_t1 or c_t2

    return results


def sync_npm_sources() -> int:
    """Synchronizes non-private Python modules and packages into installers/npm/src/."""
    npm_src = ROOT_DIR / "installers" / "npm" / "src"
    npm_src.mkdir(parents=True, exist_ok=True)
    pyproject = tomllib.loads((ROOT_DIR / "pyproject.toml").read_text(encoding="utf-8"))
    config = pyproject["tool"]["setuptools"]
    paths = {pathlib.Path(f"{name}.py") for name in config["py-modules"]}
    paths.add(pathlib.Path("tzero.py"))
    for package in config["packages"]:
        package_dir = ROOT_DIR.joinpath(*package.split("."))
        paths.update(path.relative_to(ROOT_DIR) for path in package_dir.glob("*.py"))
    paths.add(pathlib.Path("tzero/tzero_graph_hud.html"))
    paths.add(pathlib.Path("tzero/siber_akademi.ico"))

    for existing in npm_src.rglob("*"):
        if existing.is_file() and existing.suffix in {".py", ".html", ".ico"}:
            if existing.relative_to(npm_src) not in paths:
                existing.unlink()

    for relative_path in sorted(paths):
        target = npm_src / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT_DIR / relative_path, target)
    return len(paths)


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize T-Zero release metadata.")
    parser.add_argument("--version", default="10.9.0", help="Canonical target version")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if any manifest drifts")
    parser.add_argument("--sync-npm", action="store_true", help="Copy Python package files into installers/npm/src/")
    args = parser.parse_args()

    if args.sync_npm:
        count = sync_npm_sources()
        print(f"[SYNC-NPM] Synchronized {count} Python files into installers/npm/src/")
        if args.check:
            return 0

    res = sync_release_metadata(args.version, check_only=args.check)
    drifted = [k for k, v in res.items() if v]
    if args.check:
        if drifted:
            print(f"[DRIFT] Out-of-sync manifests: {', '.join(drifted)}")
            return 1
        print(f"[OK] All manifests match {args.version}")
        return 0

    print(f"[SYNC] Updated {len(drifted)} manifest(s) to {args.version}: {', '.join(drifted) if drifted else 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
