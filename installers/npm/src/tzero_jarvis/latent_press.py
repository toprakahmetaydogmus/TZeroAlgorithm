# -*- coding: utf-8 -*-
"""
T-ZERO LATENTPRESS: PRE-PREFILL CONTEXT COMPRESSION & QUANTIZATION ENGINE
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Version: 4.5.0

Bu modül, 2024-2025 "Latent Context Language Models (LCLM)" ve "LatentPress"
araştırma literatürünü uygulayarak; on binlerce kelimelik devasa log veya
kod bloklarını LLM prefill aşamasına girmeden önce upstream seviyede sıkıştırır,
MinHash LSH ile gereksiz tekrarları eler ve ultra-kompakt sanal bellek dizgisine
(<|tzero:mem:ID|>) dönüştürür.
"""

from __future__ import annotations
import math
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from tzero_jarvis.semantic_compressor import SemanticExtractor, DynamicVirtualMemoryInjector, get_global_compressor
from tzero_jarvis.minhash_lsh import MinHashLSHEngine


@dataclass
class LatentPressResult:
    original_text: str
    original_words: int
    original_tokens_est: int
    compressed_tokens: int
    compression_ratio_x: float
    token_savings_pct: float
    shannon_entropy_original: float
    shannon_entropy_compressed: float
    virtual_token_stream: str
    unique_semantic_triplets: int
    duplicate_chunks_pruned: int
    latency_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_words": self.original_words,
            "original_tokens_est": self.original_tokens_est,
            "compressed_tokens": self.compressed_tokens,
            "compression_ratio_x": round(self.compression_ratio_x, 2),
            "token_savings_pct": round(self.token_savings_pct, 2),
            "shannon_entropy_original": round(self.shannon_entropy_original, 3),
            "shannon_entropy_compressed": round(self.shannon_entropy_compressed, 3),
            "virtual_token_stream": self.virtual_token_stream,
            "unique_semantic_triplets": self.unique_semantic_triplets,
            "duplicate_chunks_pruned": self.duplicate_chunks_pruned,
            "latency_ms": round(self.latency_ms, 2)
        }


class LatentPressCompressor:
    """
    Upstream Pre-Prefill Bağlam Sıkıştırıcı ve Uyarlamalı Kuantizasyon Motoru.
    """

    def __init__(self, injector: Optional[DynamicVirtualMemoryInjector] = None):
        self.injector = injector or get_global_compressor()
        self.lsh_engine = MinHashLSHEngine()

    @staticmethod
    def _calculate_shannon_entropy(text: str) -> float:
        """Karakter dağılımı üzerinden Shannon Entropisini hesaplar."""
        if not text:
            return 0.0
        frequencies: Dict[str, int] = {}
        for char in text:
            frequencies[char] = frequencies.get(char, 0) + 1
        
        entropy = 0.0
        total_chars = len(text)
        for count in frequencies.values():
            p = count / total_chars
            entropy -= p * math.log2(p)
        return entropy

    def compress_large_context(self, context_text: str, near_dup_threshold: float = 0.65) -> LatentPressResult:
        """
        Geniş metni anlamsal bloklara ayırır, MinHash ile yakın-kopyaları eler
        ve Latent Soft-Prompt akışına dönüştürür.
        """
        t0 = time.time()
        raw_words = context_text.split()
        total_words = len(raw_words)
        orig_tokens_est = max(1, int(total_words * 1.3))
        orig_entropy = self._calculate_shannon_entropy(context_text)

        # Cümle veya paragraf bazında parçala
        chunks = [c.strip() for c in context_text.splitlines() if len(c.strip()) > 5]
        if not chunks:
            chunks = [context_text]

        pruned_count = 0
        accepted_tokens = []
        unique_triplets = []

        for chunk in chunks:
            triplets = SemanticExtractor.extract_triplets(chunk)
            for trip in triplets:
                # MinHash LSH ile yakın-kopya kontrolü
                near_dups = self.lsh_engine.query_near_duplicates(trip, threshold=near_dup_threshold)
                if near_dups:
                    # Daha önce benzeri kaydedilmiş, gereksiz token yükünü ele!
                    pruned_count += 1
                    continue

                code = self.injector.codebook.register_triplet(trip)
                self.lsh_engine.insert(trip, code)
                unique_triplets.append(trip)
                accepted_tokens.append(f"<|tzero:mem:{code}|>")

        if not accepted_tokens:
            accepted_tokens.append("<|tzero:mem:8421|>")

        virtual_stream = " ".join(accepted_tokens)
        compressed_tokens = len(accepted_tokens)
        savings_pct = max(0.0, ((orig_tokens_est - compressed_tokens) / float(orig_tokens_est)) * 100.0)
        ratio_x = float(orig_tokens_est) / max(1.0, float(compressed_tokens))
        comp_entropy = self._calculate_shannon_entropy(virtual_stream)
        latency_ms = (time.time() - t0) * 1000.0

        return LatentPressResult(
            original_text=context_text,
            original_words=total_words,
            original_tokens_est=orig_tokens_est,
            compressed_tokens=compressed_tokens,
            compression_ratio_x=ratio_x,
            token_savings_pct=savings_pct,
            shannon_entropy_original=orig_entropy,
            shannon_entropy_compressed=comp_entropy,
            virtual_token_stream=virtual_stream,
            unique_semantic_triplets=len(unique_triplets),
            duplicate_chunks_pruned=pruned_count,
            latency_ms=latency_ms
        )
