# -*- coding: utf-8 -*-
"""T-Zero Cryptographic Multi-Repo AST Federation Sync (tzero_federation.py).

Exports signed, Zero-Leak sanitized AST interface contracts (no function bodies,
no secrets) for safe peer-repository sharing, verification, and cross-repo impact lookup.

100% Free, Local, Offline, Zero-Leak Certified.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional

from tzero_features import should_skip_dir, should_skip_file
from tzero_polyglot import PolyglotTokenReducer, count_bpe_tokens
from tzero_security import ZeroLeakEngine


SCHEMA_VERSION = "1.0"
FEDERATION_DIR = os.path.join(".tzero", "federation")


class FederationSyncEngine:
    """Exports, cryptographically verifies, and imports cross-repo AST interface contracts."""

    @staticmethod
    def _canonical_digest(payload: Dict[str, Any]) -> str:
        body = {
            "schema_version": payload.get("schema_version", SCHEMA_VERSION),
            "repo_name": payload.get("repo_name", ""),
            "modules": payload.get("modules", []),
        }
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @classmethod
    def export_manifest(
        cls,
        workspace_dir: str = ".",
        repo_name: Optional[str] = None,
        out_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        abs_ws = os.path.abspath(workspace_dir)
        name = repo_name or os.path.basename(abs_ws) or "repository"
        modules: List[Dict[str, Any]] = []

        for root, dirs, files in os.walk(abs_ws):
            dirs[:] = sorted(d for d in dirs if not should_skip_dir(os.path.join(root, d), abs_ws))
            for fname in sorted(files):
                fpath = os.path.join(root, fname)
                if should_skip_file(fpath, abs_ws):
                    continue
                lang = PolyglotTokenReducer.detect_language(fname)
                if not lang:
                    continue
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        raw_code = f.read()
                except OSError:
                    continue

                reduced = PolyglotTokenReducer.reduce_code(raw_code, filename=fname, mode="ultra")
                if ZeroLeakEngine.scan_text(reduced):
                    reduced = ZeroLeakEngine.sanitize_text(reduced)
                rel = os.path.relpath(fpath, abs_ws).replace("\\", "/")
                modules.append({
                    "rel_path": rel,
                    "lang": lang,
                    "skeleton_tokens": count_bpe_tokens(reduced),
                    "skeleton": reduced,
                })

        manifest: Dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "repo_name": name,
            "exported_at": round(time.time(), 3),
            "module_count": len(modules),
            "modules": modules,
        }
        manifest["sha256"] = cls._canonical_digest(manifest)

        if out_file:
            out_abs = os.path.abspath(out_file)
            os.makedirs(os.path.dirname(out_abs), exist_ok=True)
            with open(out_abs, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

        return manifest

    @classmethod
    def verify_manifest(cls, manifest: Dict[str, Any]) -> bool:
        expected = str(manifest.get("sha256") or "")
        if len(expected) != 64:
            return False
        actual = cls._canonical_digest(manifest)
        return hmac.compare_digest(actual, expected)

    @classmethod
    def import_manifest(cls, workspace_dir: str, manifest_path: str) -> Dict[str, Any]:
        abs_ws = os.path.abspath(workspace_dir)
        with open(manifest_path, "r", encoding="utf-8", errors="replace") as f:
            manifest = json.load(f)

        verified = cls.verify_manifest(manifest)
        if not verified:
            raise ValueError(f"Federation manifest failed SHA-256 verification: {manifest_path}")

        raw_name = str(manifest.get("repo_name") or "peer")
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", raw_name).strip("._") or "peer"
        store_dir = os.path.join(abs_ws, FEDERATION_DIR)
        os.makedirs(store_dir, exist_ok=True)
        dst = os.path.join(store_dir, f"{safe_name}.json")
        with open(dst, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return {
            "verified": True,
            "repo_name": raw_name,
            "module_count": manifest.get("module_count", len(manifest.get("modules", []))),
            "stored_path": dst,
        }

    @classmethod
    def list_peers(cls, workspace_dir: str = ".") -> List[Dict[str, Any]]:
        store_dir = os.path.join(os.path.abspath(workspace_dir), FEDERATION_DIR)
        if not os.path.isdir(store_dir):
            return []
        peers: List[Dict[str, Any]] = []
        for fname in sorted(os.listdir(store_dir)):
            if not fname.endswith(".json"):
                continue
            try:
                with open(os.path.join(store_dir, fname), "r", encoding="utf-8", errors="replace") as f:
                    data = json.load(f)
                peers.append({
                    "repo_name": data.get("repo_name", fname[:-5]),
                    "module_count": data.get("module_count", 0),
                    "verified": cls.verify_manifest(data),
                    "sha256": data.get("sha256", ""),
                })
            except Exception:
                pass
        return peers

    @classmethod
    def analyze_cross_repo_impact(
        cls,
        workspace_dir: str,
        symbol_name: str,
        scip_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not symbol_name or not str(symbol_name).strip():
            raise ValueError("symbol_name must be a non-empty string")

        sym = str(symbol_name).strip()
        pattern = re.compile(rf"\b{re.escape(sym)}\b")
        abs_ws = os.path.abspath(workspace_dir)
        local_hits: List[Dict[str, Any]] = []

        # 1. Local workspace scan
        scip_abs = os.path.abspath(scip_path) if scip_path else None
        for root, dirs, files in os.walk(abs_ws):
            dirs[:] = sorted(d for d in dirs if not should_skip_dir(os.path.join(root, d), abs_ws))
            for fname in sorted(files):
                fpath = os.path.join(root, fname)
                if should_skip_file(fpath, abs_ws):
                    continue
                if scip_abs and os.path.abspath(fpath) == scip_abs:
                    continue
                lang = PolyglotTokenReducer.detect_language(fname)
                if not lang:
                    continue
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                except OSError:
                    continue

                matched_lines: List[int] = []
                total_matches = 0
                for idx, line in enumerate(lines, 1):
                    m_count = len(pattern.findall(line))
                    if m_count > 0:
                        matched_lines.append(idx)
                        total_matches += m_count

                if total_matches > 0:
                    rel = os.path.relpath(fpath, abs_ws).replace("\\", "/")
                    local_hits.append({
                        "file": rel,
                        "matches": total_matches,
                        "lines": matched_lines,
                    })

        # 2. Peer federations scan
        store_dir = os.path.join(abs_ws, FEDERATION_DIR)
        impacted_peers: List[Dict[str, Any]] = []
        unverified_peers: List[str] = []

        if os.path.isdir(store_dir):
            for fname in sorted(os.listdir(store_dir)):
                if not fname.endswith(".json"):
                    continue
                peer_p = os.path.join(store_dir, fname)
                try:
                    with open(peer_p, "r", encoding="utf-8", errors="replace") as f:
                        data = json.load(f)
                except Exception:
                    unverified_peers.append(fname[:-5])
                    continue

                if not isinstance(data, dict) or not cls.verify_manifest(data):
                    peer_id = (data.get("repo_name") if isinstance(data, dict) else None) or fname[:-5]
                    unverified_peers.append(str(peer_id))
                    continue

                repo_name = str(data.get("repo_name") or fname[:-5])
                for mod in data.get("modules", []):
                    skel = str(mod.get("skeleton") or "")
                    m_count = len(pattern.findall(skel))
                    if m_count > 0:
                        impacted_peers.append({
                            "repo_name": repo_name,
                            "rel_path": str(mod.get("rel_path") or ""),
                            "lang": str(mod.get("lang") or ""),
                            "matches": m_count,
                        })

        # 3. Optional SCIP trace
        scip_trace: Optional[Dict[str, Any]] = None
        if scip_path and os.path.isfile(scip_path):
            try:
                from tzero_scip import ScipIndexImporter
                scip_trace = ScipIndexImporter.load(scip_path).trace_symbol(sym)
            except Exception as e:
                scip_trace = {"error": str(e)}

        return {
            "symbol": sym,
            "local_hits": local_hits,
            "impacted_peers": impacted_peers,
            "unverified_peers": unverified_peers,
            "scip_trace": scip_trace,
            "total_impacted_files": len(local_hits) + len(impacted_peers),
        }


def run_federation_cli(
    action: str = "list",
    workspace_dir: str = ".",
    target_file: Optional[str] = None,
    repo_name: Optional[str] = None,
    symbol_name: Optional[str] = None,
    scip_path: Optional[str] = None,
) -> int:
    act = (action or "list").strip().lower()
    if act == "impact":
        if not symbol_name or not str(symbol_name).strip():
            print(
                json.dumps({"error": "Symbol name required for 'impact' (pass --federation-symbol <symbol>)"}, indent=2),
                file=sys.stderr,
            )
            return 1
        res = FederationSyncEngine.analyze_cross_repo_impact(workspace_dir, str(symbol_name).strip(), scip_path=scip_path)
        print(json.dumps(res, indent=2))
        return 0
    if act in ("import", "verify") and not target_file:
        print(
            json.dumps({"error": f"Target manifest file required for '{act}' (pass --federation-out <file>)"}, indent=2),
            file=sys.stderr,
        )
        return 1
    if act == "export":
        out_p = target_file or os.path.join(workspace_dir, FEDERATION_DIR, f"{repo_name or 'self'}.json")
        res = FederationSyncEngine.export_manifest(workspace_dir=workspace_dir, repo_name=repo_name, out_file=out_p)
        print(json.dumps({"action": "export", "repo_name": res["repo_name"], "module_count": res["module_count"], "sha256": res["sha256"], "out_file": out_p}, indent=2))
        return 0
    if act == "import" and target_file:
        res = FederationSyncEngine.import_manifest(workspace_dir=workspace_dir, manifest_path=target_file)
        print(json.dumps(res, indent=2))
        return 0
    if act == "verify" and target_file:
        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        ok = FederationSyncEngine.verify_manifest(data)
        print(json.dumps({"verified": ok, "repo_name": data.get("repo_name", "")}, indent=2))
        return 0 if ok else 1

    peers = FederationSyncEngine.list_peers(workspace_dir=workspace_dir)
    print(json.dumps({"peers": peers}, indent=2))
    return 0

