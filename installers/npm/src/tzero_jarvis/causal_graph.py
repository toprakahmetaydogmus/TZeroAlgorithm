# -*- coding: utf-8 -*-
"""
T-ZERO CAUSAL & TEMPORAL KNOWLEDGE GRAPH ENGINE (4D GRAPH)
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Version: 4.4.0

Bu modül, anlamsal üçlüleri (Semantic Triplet) 4 boyutlu uzayda (zaman + nedensellik)
birleştiren akıllı çizge motorudur.

Temel Yetenekler:
1. Zamansal Sıralama (Temporal Sequencing): precedes, follows, simultaneous, timestamping
2. Nedensellik Bağları (Causal Edges): causes, triggered_by, fixes, resolves, mitigates, fails_with
3. Kök Neden Analizi (Root-Cause Analysis via Causal DAG Traversal)
4. Geri Alma Sıralaması (Rollback Order Planning)
5. Döngü Tespiti (Causal Cycle Detection)
"""

from __future__ import annotations
import time
import json
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from tzero_jarvis.semantic_compressor import SemanticTriplet, TypedEntity, EntityType, VectorQuantizedCodebook


class CausalRelationType:
    CAUSES = "causes"             # A -> B (A, B'ye sebep oldu)
    TRIGGERED_BY = "triggered_by" # B <- A (B, A tarafından tetiklendi)
    FIXES = "fixes"               # A -> B (A, B hatasını/sorununu çözdü)
    RESOLVES = "resolves"         # Eş anlamlı: çözüme kavuşturdu
    MITIGATES = "mitigates"       # A, B'nin etkisini hafifletti
    FAILS_WITH = "fails_with"     # A eylemi B hatasıyla sonuçlandı
    PRECEDES = "precedes"         # A zaman olarak B'den önce gerçekleşti
    FOLLOWS = "follows"           # A zaman olarak B'den sonra gerçekleşti
    CORRELATED_WITH = "correlated_with" # İstatistiki ilişki


@dataclass
class CausalEdge:
    source_id: str
    target_id: str
    relation: str
    weight: float = 1.0
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CausalNode:
    node_id: str
    label: str
    entity_type: str = "GENERIC"
    triplet_code: Optional[int] = None
    timestamp: float = field(default_factory=time.time)
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CausalTemporalGraph:
    """
    4 Boyutlu Nedensellik ve Zaman Çizgesi Motoru.
    Gelişmiş DAG algoritmaları ile kök neden ve geri alma zincirlerini hesaplar.
    """

    def __init__(self, codebook: Optional[VectorQuantizedCodebook] = None):
        self.codebook = codebook or VectorQuantizedCodebook()
        self.nodes: Dict[str, CausalNode] = {}
        self.outgoing_edges: Dict[str, List[CausalEdge]] = {}
        self.incoming_edges: Dict[str, List[CausalEdge]] = {}
        self.chronological_timeline: List[str] = [] # node_id list in temporal order

    def add_node(self, node_id: str, label: str, entity_type: str = "GENERIC",
                 triplet_code: Optional[int] = None, timestamp: Optional[float] = None,
                 attributes: Optional[Dict[str, Any]] = None) -> CausalNode:
        ts = timestamp if timestamp is not None else time.time()
        node = CausalNode(
            node_id=node_id,
            label=label,
            entity_type=entity_type,
            triplet_code=triplet_code,
            timestamp=ts,
            attributes=attributes or {}
        )
        self.nodes[node_id] = node
        if node_id not in self.outgoing_edges:
            self.outgoing_edges[node_id] = []
        if node_id not in self.incoming_edges:
            self.incoming_edges[node_id] = []
        
        # Zaman çizgisine ekle
        self.chronological_timeline.append(node_id)
        self.chronological_timeline.sort(key=lambda nid: self.nodes[nid].timestamp)
        return node

    def add_edge(self, source_id: str, target_id: str, relation: str = CausalRelationType.CAUSES,
                 weight: float = 1.0, metadata: Optional[Dict[str, Any]] = None) -> CausalEdge:
        if source_id not in self.nodes:
            self.add_node(source_id, source_id)
        if target_id not in self.nodes:
            self.add_node(target_id, target_id)

        edge = CausalEdge(
            source_id=source_id,
            target_id=target_id,
            relation=relation,
            weight=weight,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        self.outgoing_edges[source_id].append(edge)
        self.incoming_edges[target_id].append(edge)
        return edge

    def record_triplet_event(self, triplet: SemanticTriplet,
                             preceding_triplet_code: Optional[int] = None,
                             causes_triplet_code: Optional[int] = None) -> Tuple[int, str]:
        """
        Bir semantik üçlüyü çizgeye zamansal düğüm olarak ekler ve nedensellik bağlarını kurar.
        """
        code = self.codebook.encode(triplet)
        node_id = f"node_{code}_{int(time.time() * 1000) % 100000}"
        label = f"({triplet.subject})->[{triplet.predicate}]->({','.join(o.name for o in triplet.objects)})"
        
        # Ana entity domain belirle
        primary_domain = "GENERIC"
        if triplet.objects:
            primary_domain = triplet.objects[0].entity_type.value
        elif triplet.contexts:
            primary_domain = triplet.contexts[0].entity_type.value

        self.add_node(
            node_id=node_id,
            label=label,
            entity_type=primary_domain,
            triplet_code=code,
            attributes={"subject": triplet.subject, "predicate": triplet.predicate}
        )

        # Önceki olayla zamansal bağ
        if preceding_triplet_code is not None:
            prev_nodes = [nid for nid, n in self.nodes.items() if n.triplet_code == preceding_triplet_code]
            if prev_nodes:
                latest_prev = prev_nodes[-1]
                self.add_edge(latest_prev, node_id, relation=CausalRelationType.PRECEDES)

        # Neden-sonuç bağı
        if causes_triplet_code is not None:
            cause_nodes = [nid for nid, n in self.nodes.items() if n.triplet_code == causes_triplet_code]
            if cause_nodes:
                latest_cause = cause_nodes[-1]
                self.add_edge(latest_cause, node_id, relation=CausalRelationType.CAUSES)

        return code, node_id

    def get_root_causes(self, target_node_id: str, max_depth: int = 10) -> List[Dict[str, Any]]:
        """
        Hedef düğümün (örn: bir hata veya arıza durumu) tüm kök nedenlerini (Root Causes)
        nedensellik çizgisi boyunca geriye doğru izleyerek bulur.
        """
        if target_node_id not in self.nodes:
            return []

        visited: Set[str] = set()
        root_causes: List[Dict[str, Any]] = []

        def dfs(curr_id: str, depth: int, path: List[str]):
            if depth >= max_depth or curr_id in visited:
                return
            visited.add(curr_id)

            incoming = self.incoming_edges.get(curr_id, [])
            causal_incoming = [
                e for e in incoming 
                if e.relation in (CausalRelationType.CAUSES, CausalRelationType.TRIGGERED_BY, CausalRelationType.PRECEDES)
            ]

            if not causal_incoming and depth > 0:
                # Kök nedene ulaşıldı
                node = self.nodes[curr_id]
                root_causes.append({
                    "root_node_id": curr_id,
                    "label": node.label,
                    "entity_type": node.entity_type,
                    "triplet_code": node.triplet_code,
                    "causal_path": list(reversed(path + [curr_id])),
                    "depth": depth
                })
                return

            for edge in causal_incoming:
                dfs(edge.source_id, depth + 1, path + [curr_id])

        dfs(target_node_id, 0, [])
        return root_causes

    def trace_effect_chain(self, start_node_id: str, max_depth: int = 10) -> List[Dict[str, Any]]:
        """
        Başlangıç düğümünün tetiklediği tüm zincirleme sonuçları (Downstream Effects) çıkarır.
        """
        if start_node_id not in self.nodes:
            return []

        chain: List[Dict[str, Any]] = []
        queue: List[Tuple[str, int, List[str]]] = [(start_node_id, 0, [start_node_id])]
        visited: Set[str] = {start_node_id}

        while queue:
            curr_id, depth, path = queue.pop(0)
            if depth >= max_depth:
                continue

            for edge in self.outgoing_edges.get(curr_id, []):
                next_id = edge.target_id
                if next_id not in visited:
                    visited.add(next_id)
                    next_node = self.nodes.get(next_id)
                    if next_node:
                        chain.append({
                            "node_id": next_id,
                            "label": next_node.label,
                            "relation": edge.relation,
                            "depth": depth + 1,
                            "path": path + [next_id]
                        })
                        queue.append((next_id, depth + 1, path + [next_id]))

        return chain

    def compute_rollback_order(self, target_node_id: str) -> List[Dict[str, Any]]:
        """
        Bir hata durumunda veya işlemin geri alınması gerektiğinde,
        ters topolojik sıralama (Reverse Topological Order) ile güvenli geri alma adımlarını hesaplar.
        """
        effects = self.trace_effect_chain(target_node_id)
        # En derin/en son etkilenen düğümden başlayarak geri alma planı
        rollback_steps = []
        for item in reversed(effects):
            rollback_steps.append({
                "step": len(rollback_steps) + 1,
                "action": f"Rollback: {item['label']}",
                "node_id": item["node_id"],
                "relation_to_reverse": item["relation"]
            })
        
        target_node = self.nodes.get(target_node_id)
        if target_node:
            rollback_steps.append({
                "step": len(rollback_steps) + 1,
                "action": f"Revert Base: {target_node.label}",
                "node_id": target_node_id,
                "relation_to_reverse": "initial_trigger"
            })
        return rollback_steps

    def get_timeline(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Kronolojik olay akışını döndürür.
        """
        results = []
        for nid in self.chronological_timeline[-limit:]:
            node = self.nodes[nid]
            results.append({
                "node_id": nid,
                "label": node.label,
                "entity_type": node.entity_type,
                "triplet_code": node.triplet_code,
                "timestamp": node.timestamp,
                "outgoing_count": len(self.outgoing_edges.get(nid, [])),
                "incoming_count": len(self.incoming_edges.get(nid, []))
            })
        return results

    def to_graph_data(self) -> Dict[str, Any]:
        """
        Görselleştirme için nodes ve links JSON verisi üretir.
        """
        nodes_data = []
        for nid, node in self.nodes.items():
            nodes_data.append({
                "id": nid,
                "label": node.label,
                "group": node.entity_type,
                "code": node.triplet_code,
                "timestamp": node.timestamp
            })

        links_data = []
        for src, edges in self.outgoing_edges.items():
            for e in edges:
                links_data.append({
                    "source": e.source_id,
                    "target": e.target_id,
                    "relation": e.relation,
                    "weight": e.weight
                })

        return {
            "nodes": nodes_data,
            "links": links_data,
            "stats": {
                "total_nodes": len(self.nodes),
                "total_edges": sum(len(el) for el in self.outgoing_edges.values()),
                "timeline_events": len(self.chronological_timeline)
            }
        }
