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
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple


def _read_varint(raw: bytes, offset: int = 0) -> Tuple[int, int]:
    """Reads a varint from raw bytes starting at offset. Returns (value, new_offset)."""
    val = 0
    shift = 0
    length = len(raw)
    while offset < length:
        b = raw[offset]
        offset += 1
        val |= (b & 0x7F) << shift
        if not (b & 0x80):
            return val, offset
        shift += 7
        if shift > 64:
            break
    return val, offset


def _iter_wire_fields(raw: bytes) -> Iterator[Tuple[int, int, Any]]:
    """Iterates (tag, wire_type, value) tuples from protobuf binary wire bytes."""
    offset = 0
    length = len(raw)
    while offset < length:
        key, offset = _read_varint(raw, offset)
        wire_type = key & 0x07
        tag = key >> 3
        if tag == 0:
            break
        if wire_type == 0:
            val, offset = _read_varint(raw, offset)
            yield tag, wire_type, val
        elif wire_type == 1:
            val = raw[offset:offset + 8]
            offset += 8
            yield tag, wire_type, val
        elif wire_type == 2:
            length_delim, offset = _read_varint(raw, offset)
            val = raw[offset:offset + length_delim]
            offset += length_delim
            yield tag, wire_type, val
        elif wire_type == 5:
            val = raw[offset:offset + 4]
            offset += 4
            yield tag, wire_type, val
        else:
            break


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
    def from_scip_protobuf_bytes(cls, raw: bytes) -> ScipIndexGraph:
        if not raw:
            return ScipIndexGraph(format_name="empty", document_count=0)

        defs: Dict[str, List[SymbolLocation]] = {}
        refs: Dict[str, List[SymbolLocation]] = {}
        edges: Dict[str, Set[str]] = {}
        doc_count = 0

        # Top-level Index: tag 2 = Document (wire type 2)
        for tag, wtype, doc_data in _iter_wire_fields(raw):
            if tag != 2 or wtype != 2:
                continue
            doc_count += 1
            rel_path = ""
            raw_occurrences: List[bytes] = []

            # Document fields: tag 1 = relative_path (str), tag 2 = Occurrence
            for d_tag, d_wtype, d_val in _iter_wire_fields(doc_data):
                if d_tag == 1 and d_wtype == 2:
                    rel_path = d_val.decode("utf-8", errors="replace").replace("\\", "/")
                elif d_tag == 2 and d_wtype == 2:
                    raw_occurrences.append(d_val)

            for occ_bytes in raw_occurrences:
                occ_range: List[int] = []
                sym = ""
                roles = 0
                for o_tag, o_wtype, o_val in _iter_wire_fields(occ_bytes):
                    if o_tag == 1:
                        if o_wtype == 2:
                            off = 0
                            while off < len(o_val):
                                n, off = _read_varint(o_val, off)
                                occ_range.append(n)
                        elif o_wtype == 0:
                            occ_range.append(int(o_val))
                    elif o_tag == 2 and o_wtype == 2:
                        sym = o_val.decode("utf-8", errors="replace")
                    elif o_tag == 3 and o_wtype == 0:
                        roles = int(o_val)

                if not sym:
                    continue

                ln = int(occ_range[0]) if len(occ_range) > 0 else 0
                col = int(occ_range[1]) if len(occ_range) > 1 else 0
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
            format_name="scip-protobuf",
            document_count=doc_count,
            definitions=defs,
            references=refs,
            call_edges=edges,
        )

    @classmethod
    def load(cls, path: str) -> ScipIndexGraph:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"SCIP/LSIF index file not found: {path}")
        with open(path, "rb") as f:
            raw = f.read()
        if not raw.strip():
            return ScipIndexGraph(format_name="empty", document_count=0)

        if path.lower().endswith(".scip") or b"\x00" in raw:
            return cls.from_scip_protobuf_bytes(raw)

        try:
            text = raw.decode("utf-8")
            try:
                data = json.loads(text)
                if isinstance(data, dict) and "documents" in data:
                    return cls.from_scip_dict(data)
            except json.JSONDecodeError:
                pass
            return cls.from_lsif_lines(text.splitlines())
        except Exception:
            return cls.from_scip_protobuf_bytes(raw)


def run_scip_import_cli(path: str, symbol: Optional[str] = None) -> int:
    graph = ScipIndexImporter.load(path)
    out = graph.trace_symbol(symbol) if symbol else graph.export_tzero_graph()
    print(json.dumps(out, indent=2))
    return 0
