# -*- coding: utf-8 -*-
"""T-Zero SCIP / LSIF Cross-Language Index Importer.

Loads compiler-exact SCIP JSON and LSIF NDJSON symbol indexes into a unified
cross-file definition/reference call graph without running external paid services.

100% Free, Local, Offline, Zero-Leak Certified.
"""

from __future__ import annotations

import json
import os
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set


@dataclass
class SymbolLocation:
    symbol: str
    file: str
    line: int
    column: int = 0
    role: str = "reference"


@dataclass
class ScipIndexGraph:
    format_name: str
    document_count: int
    definitions: Dict[str, List[SymbolLocation]] = field(default_factory=dict)
    references: Dict[str, List[SymbolLocation]] = field(default_factory=dict)
    call_edges: Dict[str, Set[str]] = field(default_factory=dict)

    def trace_symbol(self, symbol_query: str) -> Dict[str, Any]:
        q = (symbol_query or "").strip().lower()
        matched_defs: List[Dict[str, Any]] = []
        matched_refs: List[Dict[str, Any]] = []

        for sym, locs in self.definitions.items():
            if not q or q in sym.lower():
                for loc in locs:
                    matched_defs.append({
                        "symbol": sym,
                        "file": loc.file,
                        "line": loc.line,
                        "column": loc.column,
                    })
        for sym, locs in self.references.items():
            if not q or q in sym.lower():
                for loc in locs:
                    matched_refs.append({
                        "symbol": sym,
                        "file": loc.file,
                        "line": loc.line,
                        "column": loc.column,
                    })

        return {
            "query": symbol_query,
            "format": self.format_name,
            "document_count": self.document_count,
            "definitions": matched_defs,
            "references": matched_refs,
        }

    def export_tzero_graph(self) -> Dict[str, Any]:
        return {
            "format": self.format_name,
            "documents": self.document_count,
            "symbols_indexed": len(self.definitions) + len(self.references),
            "edges": {src: sorted(dsts) for src, dsts in self.call_edges.items() if dsts},
        }


class ScipIndexImporter:
    """Loads SCIP JSON or LSIF NDJSON indexes into ScipIndexGraph."""

    @classmethod
    def _uri_to_rel(cls, uri: str) -> str:
        if not uri:
            return ""
        if uri.startswith("file://"):
            p = urllib.parse.unquote(urllib.parse.urlparse(uri).path)
            return p.lstrip("/").replace("\\", "/")
        return uri.replace("\\", "/")

    @classmethod
    def from_scip_dict(cls, payload: Dict[str, Any]) -> ScipIndexGraph:
        defs: Dict[str, List[SymbolLocation]] = {}
        refs: Dict[str, List[SymbolLocation]] = {}
        docs = payload.get("documents") or []
        edges: Dict[str, Set[str]] = {}

        for doc in docs:
            rel_path = str(doc.get("relative_path") or "").replace("\\", "/")
            for occ in doc.get("occurrences") or []:
                sym = str(occ.get("symbol") or "")
                if not sym:
                    continue
                rng = occ.get("range") or [0, 0]
                ln = int(rng[0]) if len(rng) > 0 else 0
                col = int(rng[1]) if len(rng) > 1 else 0
                roles = int(occ.get("symbol_roles", 0))
                is_def = bool(roles & 1)
                loc = SymbolLocation(
                    symbol=sym,
                    file=rel_path,
                    line=ln,
                    column=col,
                    role="definition" if is_def else "reference",
                )
                if is_def:
                    defs.setdefault(sym, []).append(loc)
                else:
                    refs.setdefault(sym, []).append(loc)

        for sym, ref_locs in refs.items():
            def_files = {d.file for d in defs.get(sym, [])}
            for rloc in ref_locs:
                for df in def_files:
                    if df != rloc.file:
                        edges.setdefault(rloc.file, set()).add(df)

        return ScipIndexGraph(
            format_name="scip",
            document_count=len(docs),
            definitions=defs,
            references=refs,
            call_edges=edges,
        )

    @classmethod
    def from_lsif_lines(cls, lines: List[str]) -> ScipIndexGraph:
        vertices: Dict[Any, Dict[str, Any]] = {}
        doc_by_range: Dict[Any, str] = {}
        moniker_by_range: Dict[Any, str] = {}
        def_result_targets: Dict[Any, List[Any]] = {}
        ref_result_targets: Dict[Any, List[Any]] = {}
        range_to_def_result: Dict[Any, Any] = {}
        range_to_ref_result: Dict[Any, Any] = {}
        docs_seen: Set[str] = set()

        for raw in lines:
            s = raw.strip()
            if not s:
                continue
            item = json.loads(s)
            if item.get("type") == "vertex":
                vid = item.get("id")
                vertices[vid] = item
                if item.get("label") == "document":
                    docs_seen.add(cls._uri_to_rel(str(item.get("uri") or "")))
            elif item.get("type") == "edge":
                label = item.get("label", "")
                out_v = item.get("outV")
                in_vs = item.get("inVs") or ([item.get("inV")] if "inV" in item else [])
                if label == "contains":
                    doc_uri = cls._uri_to_rel(str(vertices.get(out_v, {}).get("uri") or ""))
                    for rv in in_vs:
                        doc_by_range[rv] = doc_uri
                elif label == "moniker":
                    for mv in in_vs:
                        ident = str(vertices.get(mv, {}).get("identifier") or "")
                        if ident:
                            moniker_by_range[out_v] = ident
                elif label == "textDocument/definition" and in_vs:
                    range_to_def_result[out_v] = in_vs[0]
                elif label == "textDocument/references" and in_vs:
                    range_to_ref_result[out_v] = in_vs[0]
                elif label == "item":
                    out_label = vertices.get(out_v, {}).get("label", "")
                    if out_label == "definitionResult":
                        def_result_targets.setdefault(out_v, []).extend(in_vs)
                    elif out_label == "referenceResult":
                        ref_result_targets.setdefault(out_v, []).extend(in_vs)

        defs: Dict[str, List[SymbolLocation]] = {}
        refs: Dict[str, List[SymbolLocation]] = {}
        edges: Dict[str, Set[str]] = {}

        def _range_loc(rv: Any, sym: str, role: str) -> SymbolLocation:
            v = vertices.get(rv, {})
            start = v.get("start") or {}
            return SymbolLocation(
                symbol=sym,
                file=doc_by_range.get(rv, ""),
                line=int(start.get("line", 0)),
                column=int(start.get("character", 0)),
                role=role,
            )

        for src_r, res_id in range_to_def_result.items():
            sym = moniker_by_range.get(src_r) or f"lsif_sym_{src_r}"
            for def_r in def_result_targets.get(res_id, [src_r]):
                defs.setdefault(sym, []).append(_range_loc(def_r, sym, "definition"))

        for src_r, res_id in range_to_ref_result.items():
            sym = moniker_by_range.get(src_r) or f"lsif_sym_{src_r}"
            src_doc = doc_by_range.get(src_r, "")
            for ref_r in ref_result_targets.get(res_id, []):
                loc = _range_loc(ref_r, sym, "reference")
                refs.setdefault(sym, []).append(loc)
                if src_doc and loc.file and loc.file != src_doc:
                    edges.setdefault(loc.file, set()).add(src_doc)

        return ScipIndexGraph(
            format_name="lsif",
            document_count=len(docs_seen),
            definitions=defs,
            references=refs,
            call_edges=edges,
        )

    @classmethod
    def load(cls, path: str) -> ScipIndexGraph:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"SCIP/LSIF index file not found: {path}")
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read().strip()
        if not text:
            return ScipIndexGraph(format_name="empty", document_count=0)
        try:
            data = json.loads(text)
            if isinstance(data, dict) and "documents" in data:
                return cls.from_scip_dict(data)
        except json.JSONDecodeError:
            pass
        return cls.from_lsif_lines(text.splitlines())


def run_scip_import_cli(path: str, symbol: Optional[str] = None) -> int:
    graph = ScipIndexImporter.load(path)
    out = graph.trace_symbol(symbol) if symbol else graph.export_tzero_graph()
    print(json.dumps(out, indent=2))
    return 0
