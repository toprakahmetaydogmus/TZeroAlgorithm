# -*- coding: utf-8 -*-
"""
T-ZERO ZERO-VECTOR-DB HYBRID IN-MEMORY SEARCH ENGINE
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Version: 4.4.0

Bu modül, harici hiçbir ağır Vektör Veritabanına (ChromaDB, Pinecone, FAISS vb.)
ihtiyaç duymadan; saf bellek içi (In-Memory) Ters İndeksleme (Inverted Index),
BM25 Anlamsal Sıralama ve T-Zero Latent Codebook (#code) eşleştirmesini
birleştiren mikro-saniye (<1 ms) hızında hibrit arama motorudur.
"""

from __future__ import annotations
import math
import re
import time
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class SearchDocument:
    doc_id: str
    doc_type: str  # "code_symbol", "triplet", "memory", "causal_event"
    title: str
    content: str
    discrete_code: Optional[int] = None
    domain: str = "GENERIC"
    metadata: Dict[str, Any] = field(default_factory=dict)
    tokens: List[str] = field(default_factory=list)


@dataclass
class SearchResult:
    doc_id: str
    doc_type: str
    title: str
    content: str
    score: float
    discrete_code: Optional[int] = None
    domain: str = "GENERIC"
    match_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "doc_type": self.doc_type,
            "title": self.title,
            "content": self.content,
            "score": round(self.score, 4),
            "discrete_code": self.discrete_code,
            "domain": self.domain,
            "match_reasons": self.match_reasons
        }


class ZeroVectorDBSearchEngine:
    """
    Sıfır Dış Bağımlılıklı, Bellek İçi BM25 + T-Zero Latent Codebook Hibrit Arama Motoru.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: Dict[str, SearchDocument] = {}
        self.inverted_index: Dict[str, Set[str]] = defaultdict(set)
        self.code_index: Dict[int, Set[str]] = defaultdict(set)
        self.domain_index: Dict[str, Set[str]] = defaultdict(set)
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_len: float = 0.0

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Gelişmiş regex tabanlı küçük harfe dönüştürücü ve temizleyici tokenizer.
        """
        words = re.findall(r'[a-zA-ZçğıöşüÇĞİÖŞÜ0-9_#]+', text.lower())
        return [w for w in words if len(w) > 1]

    def add_document(self, doc_id: str, doc_type: str, title: str, content: str,
                     discrete_code: Optional[int] = None, domain: str = "GENERIC",
                     metadata: Optional[Dict[str, Any]] = None) -> SearchDocument:
        tokens = self.tokenize(f"{title} {content} {domain}")
        doc = SearchDocument(
            doc_id=doc_id,
            doc_type=doc_type,
            title=title,
            content=content,
            discrete_code=discrete_code,
            domain=domain.upper(),
            metadata=metadata or {},
            tokens=tokens
        )
        self.documents[doc_id] = doc
        self.doc_lengths[doc_id] = len(tokens)

        # Ters indekse ekle
        for tok in set(tokens):
            self.inverted_index[tok].add(doc_id)

        # Codebook indeksine ekle
        if discrete_code is not None:
            self.code_index[discrete_code].add(doc_id)

        # Domain indeksine ekle
        self.domain_index[doc.domain].add(doc_id)

        # Ortalama doküman uzunluğunu güncelle
        total_len = sum(self.doc_lengths.values())
        self.avg_doc_len = total_len / max(1, len(self.documents))
        return doc

    def search(self, query: str, top_k: int = 10, target_domain: Optional[str] = None) -> List[SearchResult]:
        """
        Hibrit BM25 + Latent Codebook Arama Algoritması.
        """
        if not self.documents:
            return []

        start_time = time.time()
        query_tokens = self.tokenize(query)
        
        # Query içinde discrete code (#8421 veya 8421) var mı?
        code_matches = re.findall(r'#?(\d{4,5})', query)
        queried_codes = {int(c) for c in code_matches}

        n_docs = len(self.documents)
        scores: Dict[str, float] = defaultdict(float)
        reasons: Dict[str, List[str]] = defaultdict(list)

        # 1. BM25 Skorlama
        for tok in query_tokens:
            posting_list = self.inverted_index.get(tok, set())
            if not posting_list:
                continue

            df = len(posting_list)
            # Standart Lucene/Robertson IDF
            idf = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))

            for doc_id in posting_list:
                doc = self.documents[doc_id]
                tf = doc.tokens.count(tok)
                doc_len = self.doc_lengths.get(doc_id, 1)
                
                denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / max(1.0, self.avg_doc_len)))
                bm25_part = idf * ((tf * (self.k1 + 1.0)) / max(1e-5, denom))
                scores[doc_id] += bm25_part
                if len(reasons[doc_id]) < 3:
                    reasons[doc_id].append(f"token:{tok}")

        # 2. Discrete Code (#8421) Eşleşme Güçlendirmesi (10x Boost)
        for code in queried_codes:
            for doc_id in self.code_index.get(code, set()):
                scores[doc_id] += 15.0
                reasons[doc_id].append(f"code_exact_match:#{code}")

        # 3. Domain Hedefleme Güçlendirmesi
        if target_domain:
            target_domain_upper = target_domain.upper()
            for doc_id in self.domain_index.get(target_domain_upper, set()):
                scores[doc_id] += 5.0
                reasons[doc_id].append(f"domain_match:{target_domain_upper}")

        # Sırala ve formatla
        ranked_doc_ids = sorted(scores.keys(), key=lambda did: scores[did], reverse=True)[:top_k]
        
        results = []
        for did in ranked_doc_ids:
            doc = self.documents[did]
            results.append(SearchResult(
                doc_id=doc.doc_id,
                doc_type=doc.doc_type,
                title=doc.title,
                content=doc.content,
                score=scores[did],
                discrete_code=doc.discrete_code,
                domain=doc.domain,
                match_reasons=reasons[did]
            ))

        return results

    def index_codebase_scanner_results(self, scanner_report: Dict[str, Any]) -> int:
        """
        T-Zero CodebaseScanner (AST) sonuçlarını anında arama indeksine katar.
        """
        count = 0
        symbols = scanner_report.get("symbols", {})
        for sym_name, sym_info in symbols.items():
            doc_id = f"sym_{sym_name}_{count}"
            doc_type = "code_symbol"
            title = f"{sym_info.get('type', 'symbol')}: {sym_name}"
            content = f"File: {sym_info.get('file', '')} Lines: {sym_info.get('lines', '')} Doc: {sym_info.get('docstring', '')}"
            self.add_document(
                doc_id=doc_id,
                doc_type=doc_type,
                title=title,
                content=content,
                domain="SOFTWARE",
                metadata=sym_info
            )
            count += 1
        return count

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_documents": len(self.documents),
            "total_vocabulary": len(self.inverted_index),
            "total_discrete_codes_indexed": len(self.code_index),
            "domains_covered": list(self.domain_index.keys()),
            "avg_doc_length": round(self.avg_doc_len, 2)
        }
