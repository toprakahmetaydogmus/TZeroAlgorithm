# -*- coding: utf-8 -*-
"""T-Zero Vectorless Semantic Graph & Local Code-RAG Engine (100% Offline, Zero-Cost).

Combines lexical BM25 token relevance, AST structural symbols, and PageRank
graph centrality into a unified hybrid retrieval pipeline without external embeddings.
"""

from __future__ import annotations

import collections
import dataclasses
import math
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclasses.dataclass
class GraphRagChunk:
    chunk_id: str
    file_path: str
    name: str
    kind: str  # function, class, interface, module
    signature: str
    content: str
    docstring: str
    line_start: int
    line_end: int
    dependencies: List[str] = dataclasses.field(default_factory=list)
    tokens: List[str] = dataclasses.field(default_factory=list)
    bm25_score: float = 0.0
    graph_centrality: float = 0.0
    hybrid_score: float = 0.0


class VectorlessGraphRAG:
    """100% Offline, private Graph RAG combining BM25, AST Call Graph, and Centrality."""

    def __init__(self, workspace_dir: str):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.chunks: List[GraphRagChunk] = []
        self.doc_freqs: Dict[str, int] = collections.defaultdict(int)
        self.total_docs: int = 0
        self.avg_doc_len: float = 0.0
        self.call_graph: Dict[str, Set[str]] = collections.defaultdict(set)
        self.reverse_call_graph: Dict[str, Set[str]] = collections.defaultdict(set)
        self.centrality_scores: Dict[str, float] = {}

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Sub-word aware identifier tokenization."""
        if not text:
            return []
        raw_words = re.findall(r"[A-Za-z0-9_]+", text)
        tokens: List[str] = []
        for word in raw_words:
            tokens.append(word.lower())
            # split camelCase and PascalCase
            parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+", word)
            if len(parts) > 1:
                for p in parts:
                    clean = p.lower().strip("_")
                    if len(clean) >= 2:
                        tokens.append(clean)
            # split snake_case
            if "_" in word:
                for sub in word.split("_"):
                    clean = sub.lower()
                    if len(clean) >= 2:
                        tokens.append(clean)
        return [t for t in tokens if len(t) >= 2]

    def index_workspace(self, file_limit: int = 500) -> int:
        """Scan workspace and index code structures into graph RAG nodes."""
        from tzero.tzero_snapshot import SnapshotEngine

        snap = SnapshotEngine.create_snapshot(self.workspace_dir)
        self.chunks.clear()
        self.doc_freqs.clear()
        self.call_graph.clear()
        self.reverse_call_graph.clear()

        total_tokens = 0
        file_count = 0

        for rel_path, file_snap in sorted(snap.files.items()):
            file_count += 1
            if file_count > file_limit:
                break

            full_path = os.path.join(self.workspace_dir, rel_path)
            # 1. Module chunk
            mod_text = f"{rel_path} " + " ".join(file_snap.imports)
            mod_tokens = self.tokenize(mod_text)
            mod_chunk = GraphRagChunk(
                chunk_id=f"mod::{rel_path}",
                file_path=rel_path,
                name=os.path.basename(rel_path),
                kind="module",
                signature=f"module {rel_path}",
                content=mod_text,
                docstring="",
                line_start=1,
                line_end=1,
                dependencies=list(file_snap.imports),
                tokens=mod_tokens,
            )
            self.chunks.append(mod_chunk)
            total_tokens += len(mod_tokens)

            # Record dependency edges
            for imp in file_snap.imports:
                imp_stem = os.path.splitext(os.path.basename(imp))[0]
                self.call_graph[rel_path].add(imp_stem)
                self.reverse_call_graph[imp_stem].add(rel_path)

            # 2. Function / Class chunks
            for fn_name in file_snap.functions:
                sig_text = f"def {fn_name}() in {rel_path}"
                fn_tokens = self.tokenize(f"{fn_name} {rel_path}")
                fn_chunk = GraphRagChunk(
                    chunk_id=f"fn::{rel_path}::{fn_name}",
                    file_path=rel_path,
                    name=fn_name,
                    kind="function",
                    signature=sig_text,
                    content=sig_text,
                    docstring="",
                    line_start=1,
                    line_end=1,
                    dependencies=list(file_snap.imports),
                    tokens=fn_tokens,
                )
                self.chunks.append(fn_chunk)
                total_tokens += len(fn_tokens)

            for cls_name in file_snap.classes:
                sig_text = f"class {cls_name} in {rel_path}"
                cls_tokens = self.tokenize(f"{cls_name} {rel_path}")
                cls_chunk = GraphRagChunk(
                    chunk_id=f"cls::{rel_path}::{cls_name}",
                    file_path=rel_path,
                    name=cls_name,
                    kind="class",
                    signature=sig_text,
                    content=sig_text,
                    docstring="",
                    line_start=1,
                    line_end=1,
                    dependencies=list(file_snap.imports),
                    tokens=cls_tokens,
                )
                self.chunks.append(cls_chunk)
                total_tokens += len(cls_tokens)

        self.total_docs = len(self.chunks)
        self.avg_doc_len = (total_tokens / self.total_docs) if self.total_docs > 0 else 1.0

        # Build Document Frequency
        for chunk in self.chunks:
            seen_terms = set(chunk.tokens)
            for term in seen_terms:
                self.doc_freqs[term] += 1

        # Compute PageRank Centrality across nodes
        self._compute_graph_centrality()
        return self.total_docs

    def _compute_graph_centrality(self, damping: float = 0.85, iterations: int = 25) -> None:
        """Compute node centrality for connected files."""
        nodes = list(self.call_graph.keys() | self.reverse_call_graph.keys())
        if not nodes:
            return
        n = len(nodes)
        scores = {node: 1.0 / n for node in nodes}

        for _ in range(iterations):
            new_scores = {}
            for node in nodes:
                incoming_sum = 0.0
                for pred in self.reverse_call_graph.get(node, set()):
                    out_deg = len(self.call_graph.get(pred, set()))
                    if out_deg > 0:
                        incoming_sum += scores.get(pred, 0.0) / out_deg
                new_scores[node] = (1.0 - damping) / n + damping * incoming_sum
            scores = new_scores

        self.centrality_scores = scores
        for chunk in self.chunks:
            stem = os.path.splitext(os.path.basename(chunk.file_path))[0]
            chunk.graph_centrality = self.centrality_scores.get(stem, self.centrality_scores.get(chunk.file_path, 0.05))

    def _score_bm25(self, query_tokens: List[str], chunk_tokens: List[str], k1: float = 1.2, b: float = 0.75) -> float:
        """Standard BM25 scoring for query tokens against chunk tokens."""
        if not query_tokens or not chunk_tokens:
            return 0.0
        doc_len = len(chunk_tokens)
        counts = collections.Counter(chunk_tokens)
        score = 0.0

        for q in query_tokens:
            if q not in counts:
                continue
            df = self.doc_freqs.get(q, 0)
            idf = math.log(1.0 + (self.total_docs - df + 0.5) / (df + 0.5))
            tf = counts[q]
            denom = tf + k1 * (1.0 - b + b * (doc_len / (self.avg_doc_len or 1.0)))
            score += idf * (tf * (k1 + 1.0)) / denom
        return max(0.0, score)

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        graph_weight: float = 0.35,
        bm25_weight: float = 0.65,
    ) -> List[Dict[str, Any]]:
        """Execute hybrid search combining BM25 and graph centrality ranking."""
        if not self.chunks:
            self.index_workspace()

        q_tokens = self.tokenize(query_text)
        if not q_tokens:
            return []

        scored_chunks: List[GraphRagChunk] = []
        max_bm25 = 0.0001
        for chunk in self.chunks:
            b_score = self._score_bm25(q_tokens, chunk.tokens)
            chunk.bm25_score = b_score
            if b_score > max_bm25:
                max_bm25 = b_score

        # Normalize and blend
        for chunk in self.chunks:
            norm_bm25 = chunk.bm25_score / max_bm25
            # Graph centrality boost
            hybrid = (norm_bm25 * bm25_weight) + (chunk.graph_centrality * graph_weight)
            # Exact symbol name match boost
            if any(q == chunk.name.lower() for q in q_tokens):
                hybrid += 0.5
            chunk.hybrid_score = hybrid
            if chunk.bm25_score > 0.0 or chunk.hybrid_score > 0.2:
                scored_chunks.append(chunk)

        scored_chunks.sort(key=lambda c: c.hybrid_score, reverse=True)
        top = scored_chunks[:top_k]

        return [
            {
                "chunk_id": c.chunk_id,
                "file_path": c.file_path,
                "name": c.name,
                "kind": c.kind,
                "signature": c.signature,
                "hybrid_score": round(c.hybrid_score, 4),
                "bm25_score": round(c.bm25_score, 4),
                "centrality": round(c.graph_centrality, 4),
                "dependencies": c.dependencies[:5],
            }
            for c in top
        ]

