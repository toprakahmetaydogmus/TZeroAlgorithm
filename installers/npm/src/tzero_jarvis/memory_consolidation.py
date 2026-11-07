# -*- coding: utf-8 -*-
"""
T-ZERO DUAL-MEMORY CONSOLIDATION ENGINE (HIPPOCAMPAL REPLAY)
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Version: 4.4.0

Bu modül, insan beynindeki hipokampus-neokorteks bellek konsolidasyonunu taklit eder:
1. EpisodicMemory (Kısa süreli epizodik tampon bellek)
2. Semantic Consolidation (Derin konsolidasyon / Gece rüyası döngüsü):
   - Benzer epizotları kümeleme (Clustering)
   - Çoklu adımlardan Makro-Üçlü (Macro-Triplet) sentezleme
   - Çelişki Çözümleme (Contradiction Resolution & Temporal Superseding)
   - Kalıcı Latent Codebook'a terfi ettirme (Promotion)
"""

from __future__ import annotations
import time
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from tzero_jarvis.semantic_compressor import SemanticTriplet, TypedEntity, EntityType, VectorQuantizedCodebook, SemanticExtractor


@dataclass
class Episode:
    episode_id: str
    content: str
    timestamp: float = field(default_factory=time.time)
    source: str = "user"  # "user", "agent", "execution", "sensor"
    triplets: List[SemanticTriplet] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    superseded: bool = False
    superseded_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "content": self.content,
            "timestamp": self.timestamp,
            "source": self.source,
            "triplet_count": len(self.triplets),
            "tags": self.tags,
            "superseded": self.superseded,
            "superseded_by": self.superseded_by
        }


@dataclass
class MacroTriplet:
    macro_id: str
    subject: str
    predicate: str
    objects: List[str]
    context: str
    derived_from_episodes: List[str]
    discrete_code: int
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EpisodicMemoryBuffer:
    """
    Kısa süreli epizodik bellek tamponu (Rolling Ring-Buffer).
    """

    def __init__(self, max_capacity: int = 1000):
        self.max_capacity = max_capacity
        self.episodes: List[Episode] = []

    def record_episode(self, content: str, source: str = "user", tags: Optional[List[str]] = None) -> Episode:
        ep_id = f"ep_{int(time.time()*1000)%100000}_{len(self.episodes)+1}"
        triplets = SemanticExtractor.extract_triplets(content)
        episode = Episode(
            episode_id=ep_id,
            content=content,
            timestamp=time.time(),
            source=source,
            triplets=triplets,
            tags=tags or []
        )
        self.episodes.append(episode)
        if len(self.episodes) > self.max_capacity:
            self.episodes.pop(0)
        return episode

    def get_active_episodes(self) -> List[Episode]:
        return [ep for ep in self.episodes if not ep.superseded]


class ConsolidationEngine:
    """
    Derin Bellek Konsolidasyonu ve Çelişki Giderme Motoru.
    """

    def __init__(self, codebook: Optional[VectorQuantizedCodebook] = None):
        self.codebook = codebook or VectorQuantizedCodebook()
        self.episodic_buffer = EpisodicMemoryBuffer()
        self.macro_triplets: List[MacroTriplet] = []

    def consolidate(self) -> Dict[str, Any]:
        """
        Konsolidasyon Döngüsünü (Replay Cycle) çalıştırır.
        1. Çelişki ve durum güncellemelerini yakalar (Örn: hata -> başarı).
        2. Varlık kümeleri üzerinden makro kavramlar türetir.
        3. Codebook'a deterministik hashlerle ekler.
        """
        active_episodes = self.episodic_buffer.get_active_episodes()
        if not active_episodes:
            return {
                "status": "idle",
                "consolidated_episodes": 0,
                "macro_triplets_created": 0,
                "contradictions_resolved": 0
            }

        # 1. Çelişki ve Durum Geçersiz Kılma (Superseding)
        contradictions_resolved = self._resolve_contradictions(active_episodes)

        # 2. Varlık Kümeleri Oluşturma (Entity-Based Clustering)
        entity_clusters: Dict[str, List[Episode]] = defaultdict(list)
        for ep in self.episodic_buffer.get_active_episodes():
            for t in ep.triplets:
                for obj in t.objects:
                    entity_clusters[obj.name.lower()].append(ep)
                for ctx in t.contexts:
                    entity_clusters[ctx.name.lower()].append(ep)

        # 3. Makro-Üçlü Sentezleme
        macro_count = 0
        for entity_key, eps in entity_clusters.items():
            if len(eps) >= 2: # En az iki kez etkileşime girilen varlık
                # Ortak özne ve eylemleri topla
                all_triplets = [t for ep in eps for t in ep.triplets]
                subjects = list({t.subject for t in all_triplets})
                subj = subjects[0] if subjects else "Sistem"
                
                # Nesneleri birleştir
                obj_names = sorted(list({o.name for t in all_triplets for o in t.objects}))
                ctx_names = sorted(list({c.name for t in all_triplets for c in t.contexts}))

                # Sentezlenmiş makro üçlü
                macro_triplet = SemanticTriplet(
                    subject=subj,
                    predicate="entegre_etti_ve_doğruladı",
                    objects=[TypedEntity(name=name, entity_type=EntityType.Generic) for name in obj_names[:4]],
                    contexts=[TypedEntity(name=name, entity_type=EntityType.Generic) for name in ctx_names[:2]]
                )
                
                code = self.codebook.encode(macro_triplet)
                macro_id = f"macro_{entity_key}_{code}"
                
                if not any(m.macro_id == macro_id for m in self.macro_triplets):
                    macro_entry = MacroTriplet(
                        macro_id=macro_id,
                        subject=subj,
                        predicate=macro_triplet.predicate,
                        objects=obj_names[:4],
                        context=" | ".join(ctx_names[:2]),
                        derived_from_episodes=[ep.episode_id for ep in eps],
                        discrete_code=code,
                        confidence=0.95
                    )
                    self.macro_triplets.append(macro_entry)
                    macro_count += 1

        return {
            "status": "success",
            "total_episodes_processed": len(active_episodes),
            "macro_triplets_created": macro_count,
            "contradictions_resolved": contradictions_resolved,
            "total_active_macros": len(self.macro_triplets)
        }

    def _resolve_contradictions(self, episodes: List[Episode]) -> int:
        """
        Zaman içindeki zıtlıkları tespit eder ve eskiyen bilgileri geçersiz (superseded) kılar.
        """
        resolved_count = 0
        # Basit durum çiftleri: (hata/ariza/başarısız) vs (düzeltildi/başarılı/çözüldü)
        failure_terms = {"hata", "arıza", "başarısız", "failed", "error", "bozuldu", "çöktü"}
        success_terms = {"başarılı", "düzeltildi", "çözüldü", "success", "fixed", "tamamlandı", "çalıştı"}

        for i, ep_earlier in enumerate(episodes):
            earlier_text = ep_earlier.content.lower()
            if any(term in earlier_text for term in failure_terms):
                # Sonraki epizotlarda aynı varlık için düzeltme var mı?
                for ep_later in episodes[i+1:]:
                    later_text = ep_later.content.lower()
                    if any(term in later_text for term in success_terms):
                        # Varlık örtüşmesi kontrolü
                        earlier_words = set(earlier_text.split())
                        later_words = set(later_text.split())
                        common_nouns = earlier_words.intersection(later_words)
                        if len(common_nouns) >= 2:
                            ep_earlier.superseded = True
                            ep_earlier.superseded_by = ep_later.episode_id
                            resolved_count += 1
                            break
        return resolved_count

    def get_summary(self) -> Dict[str, Any]:
        """
        Konsolide edilmiş bellek özetini döndürür.
        """
        return {
            "total_episodes": len(self.episodic_buffer.episodes),
            "active_episodes": len(self.episodic_buffer.get_active_episodes()),
            "total_macros": len(self.macro_triplets),
            "macros": [m.to_dict() for m in self.macro_triplets[-10:]]
        }
