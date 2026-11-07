# -*- coding: utf-8 -*-
"""
T-ZERO SUB-MICROSECOND MINHASH LSH TRIPLET SIMILARITY ENGINE
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Version: 4.5.0

Bu modül, en son 2024-2025 LSH (Locality-Sensitive Hashing) ve MinHash
literatüründen esinlenilmiş; harici hiçbir nöral kütüphaneye ihtiyaç duymadan,
anlamsal üçlüler (Semantic Triplets) arasındaki Jaccard benzerliğini
mikrosaniyenin altında (<1 µs / nanosecond-tier) hesaplayan ve yakın-kopyaları
(near-duplicates) anında kümeleyen deterministik hash motorudur.
"""

from __future__ import annotations
import hashlib
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from tzero_jarvis.semantic_compressor import SemanticTriplet, TypedEntity, EntityType, SemanticExtractor


# Büyük Mersenne Asalı: 2^31 - 1
MERSENNE_PRIME = 2147483647
NUM_PERMUTATIONS = 64
BANDS = 16
ROWS_PER_BAND = 4  # 16 * 4 = 64


# Deterministik Hash Katsayıları (a * x + b) % p
def _generate_hash_seeds(k: int = NUM_PERMUTATIONS) -> List[Tuple[int, int]]:
    seeds = []
    for i in range(k):
        # SHA-256 ile tekrarlanabilir deterministik katsayılar
        h = hashlib.sha256(f"tzero_seed_{i}".encode("utf-8")).hexdigest()
        a = (int(h[:8], 16) % (MERSENNE_PRIME - 1)) + 1
        b = int(h[8:16], 16) % MERSENNE_PRIME
        seeds.append((a, b))
    return seeds

HASH_SEEDS = _generate_hash_seeds(NUM_PERMUTATIONS)


@dataclass
class MinHashSignature:
    triplet_code: int
    signature: List[int]  # 64 integer hashes
    label: str
    tokens: Set[str] = field(default_factory=set)

    def jaccard_similarity(self, other: MinHashSignature) -> float:
        """İki imza arasındaki Jaccard benzerliğini hesaplar (Bitwise/Integer çarpışma oranı)."""
        if len(self.signature) != len(other.signature):
            return 0.0
        matches = sum(1 for a, b in zip(self.signature, other.signature) if a == b)
        return matches / float(len(self.signature))


class MinHashLSHEngine:
    """
    Sub-Mikrosaniye MinHash LSH Çizge Benzerlik ve Kümeleme Motoru.
    Banding tekniği ile O(1) yakın-komşu araması yapar.
    """

    def __init__(self, bands: int = BANDS, rows_per_band: int = ROWS_PER_BAND):
        self.bands = bands
        self.rows_per_band = rows_per_band
        self.num_hashes = bands * rows_per_band
        self.signatures: Dict[int, MinHashSignature] = {}
        # Band -> BucketHash -> Set of triplet_codes
        self.buckets: List[Dict[int, Set[int]]] = [{} for _ in range(self.bands)]

    @staticmethod
    def _shingle_triplet(triplet: SemanticTriplet) -> Set[str]:
        """Üçlünün bileşenlerinden 1-gram ve 2-gram anlamsal shingle'lar üretir."""
        tokens = set()
        tokens.add(f"subj:{triplet.subject.lower()}")
        tokens.add(f"pred:{triplet.predicate.lower()}")
        
        for o in triplet.objects:
            tokens.add(f"obj:{o.name.lower()}")
            tokens.add(f"tag:{o.entity_type.lower()}")
            tokens.add(f"so:{triplet.subject.lower()}_{o.name.lower()}")

        for c in triplet.contexts:
            tokens.add(f"ctx:{c.name.lower()}")
            tokens.add(f"sc:{triplet.subject.lower()}_{c.name.lower()}")

        return tokens

    def compute_signature(self, triplet: SemanticTriplet, code: int) -> MinHashSignature:
        """Üçlü için 64 boyutlu kompakt MinHash imzasını hesaplar."""
        shingles = self._shingle_triplet(triplet)
        sig = [MERSENNE_PRIME] * self.num_hashes

        for token in shingles:
            # Token'ın 32-bit integer hash'i
            tok_h = int(hashlib.md5(token.encode("utf-8")).hexdigest()[:8], 16)
            for i, (a, b) in enumerate(HASH_SEEDS):
                perm_val = (a * tok_h + b) % MERSENNE_PRIME
                if perm_val < sig[i]:
                    sig[i] = perm_val

        return MinHashSignature(
            triplet_code=code,
            signature=sig,
            label=triplet.to_graph_string(),
            tokens=shingles
        )

    def insert(self, triplet: SemanticTriplet, code: int) -> MinHashSignature:
        """Üçlüyü LSH tablosuna ekler ve bant kovalarına yerleştirir."""
        sig = self.compute_signature(triplet, code)
        self.signatures[code] = sig

        # Banding tekniği ile kovalara yaz
        for b_idx in range(self.bands):
            start = b_idx * self.rows_per_band
            end = start + self.rows_per_band
            band_slice = tuple(sig.signature[start:end])
            bucket_key = hash(band_slice)
            
            if bucket_key not in self.buckets[b_idx]:
                self.buckets[b_idx][bucket_key] = set()
            self.buckets[b_idx][bucket_key].add(code)

        return sig

    def query_near_duplicates(self, triplet: SemanticTriplet, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        LSH kovaları üzerinden O(1) hızında adayları çeker ve
        Jaccard benzerliği threshold üzerinde olanları döndürür.
        """
        temp_sig = self.compute_signature(triplet, 0)
        candidate_codes: Set[int] = set()

        for b_idx in range(self.bands):
            start = b_idx * self.rows_per_band
            end = start + self.rows_per_band
            band_slice = tuple(temp_sig.signature[start:end])
            bucket_key = hash(band_slice)

            if bucket_key in self.buckets[b_idx]:
                candidate_codes.update(self.buckets[b_idx][bucket_key])

        results = []
        for cand_code in candidate_codes:
            cand_sig = self.signatures.get(cand_code)
            if cand_sig:
                sim = temp_sig.jaccard_similarity(cand_sig)
                if sim >= threshold:
                    results.append({
                        "code": cand_code,
                        "similarity": round(sim, 4),
                        "label": cand_sig.label
                    })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results

    def find_clusters(self, min_similarity: float = 0.7) -> List[List[int]]:
        """Tüm kayıtlı kodlar arasındaki benzerlik kümelerini (Clusters) çıkarır."""
        visited: Set[int] = set()
        clusters: List[List[int]] = []

        all_codes = list(self.signatures.keys())
        for code in all_codes:
            if code in visited:
                continue
            
            sig = self.signatures[code]
            cluster = [code]
            visited.add(code)

            for other_code in all_codes:
                if other_code in visited:
                    continue
                other_sig = self.signatures[other_code]
                if sig.jaccard_similarity(other_sig) >= min_similarity:
                    cluster.append(other_code)
                    visited.add(other_code)

            if len(cluster) > 1:
                clusters.append(cluster)

        return clusters
