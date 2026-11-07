# -*- coding: utf-8 -*-
"""
T-ZERO BYZANTINE FAULT-TOLERANT (BFT) MULTI-AGENT CONSENSUS PROTOCOL
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Version: 4.5.0

Bu modül, dağıtık sistemlerdeki PBFT (Practical Byzantine Fault Tolerance)
ve Raft konsensüs mekanizmalarını otonom AI ajan sürüsüne uyarlar:
1. Dinamik Ajan İtibar & Güven Ağırlıkları (w_i in [0.1, 1.0])
2. Halüsinasyon ve Aykırı Değer (Outlier) İzolasyonu
3. Güvenlik Muhafızı Mutlak Veto Yetkisi (Zero-Leak Veto Protection)
4. 3-Aşamalı BFT Oylama: Pre-Prepare -> Prepare -> Commit (2/3 Ağırlıklı Quorum)
"""

from __future__ import annotations
import time
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from tzero_jarvis.swarm import SwarmCoordinator, SwarmAgentReport


@dataclass
class BFTConsensusCertificate:
    mission_id: str
    mission_goal: str
    consensus_verdict: str  # "APPROVED", "REJECTED_BY_VETO", "QUORUM_NOT_MET"
    quorum_ratio: float
    total_voting_weight: float
    approved_weight: float
    byzantine_faults_detected: int
    veto_triggered: bool
    veto_reason: Optional[str]
    committed_virtual_tokens: List[str]
    certificate_hash: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "mission_goal": self.mission_goal,
            "consensus_verdict": self.consensus_verdict,
            "quorum_ratio": round(self.quorum_ratio, 4),
            "total_voting_weight": round(self.total_voting_weight, 2),
            "approved_weight": round(self.approved_weight, 2),
            "byzantine_faults_detected": self.byzantine_faults_detected,
            "veto_triggered": self.veto_triggered,
            "veto_reason": self.veto_reason,
            "committed_virtual_tokens": self.committed_virtual_tokens,
            "certificate_hash": self.certificate_hash,
            "timestamp": self.timestamp
        }


class ByzantineFaultTolerantSwarm:
    """
    PBFT / Raft Tabanlı Otonom Ajan Konsensüs Yöneticisi.
    """

    DEFAULT_WEIGHTS = {
        "SecuritySentinel": 1.0,     # En yüksek güvenlik ağırlığı & Veto
        "EmbeddedHardware": 0.95,    # Donanım doğrulaması
        "ASTOptimizer": 0.90,       # AST ve token tasarrufu
        "AutonomousDevOps": 0.90,   # Build ve ortam
        "JARVIS Prime": 1.0         # Lider koordinatör
    }

    def __init__(self, coordinator: Optional[SwarmCoordinator] = None):
        self.coordinator = coordinator or SwarmCoordinator()
        self.agent_weights: Dict[str, float] = dict(self.DEFAULT_WEIGHTS)
        self.reputation_history: Dict[str, List[float]] = {k: [1.0] for k in self.DEFAULT_WEIGHTS}

    def reach_consensus(self, mission_goal: str, context: str = "") -> BFTConsensusCertificate:
        """
        3 Aşamalı BFT Konsensüs Protokolünü çalıştırır.
        """
        mission_id = f"bft_{int(time.time()*1000)%100000}"
        
        # 1. Aşama: Sürü Görev Raporlarını Topla (Prepare Phase)
        raw_result = self.coordinator.coordinate_mission(mission_goal, context)
        agent_reports = raw_result.get("agent_reports", [])

        total_weight = 0.0
        approved_weight = 0.0
        byzantine_faults = 0
        veto_triggered = False
        veto_reason = None
        all_tokens = []

        # 2. Aşama: Oyların Denetimi ve Ağırlıklı Sentez
        for rep in agent_reports:
            agent_name = rep.get("agent_name", "Unknown")
            verdict = rep.get("verdict", "REJECTED")
            weight = self.agent_weights.get(agent_name, 0.5)
            confidence = rep.get("confidence", 0.5)
            effective_weight = weight * confidence
            total_weight += effective_weight

            # Zero-Leak Veto Denetimi
            if agent_name == "SecuritySentinel" and verdict != "APPROVED":
                findings_str = " ".join(rep.get("findings", []))
                if any(kw in findings_str.lower() for kw in ("leak", "secret", "critical", "zafiyet", "risk")):
                    veto_triggered = True
                    veto_reason = f"SecuritySentinel Veto: {findings_str[:120]}"

            # Anomali / Halüsinasyon Kontrolü
            # Örn: Ajan aşırı düşük güvenle çelişkili karar verirse
            if confidence < 0.4:
                byzantine_faults += 1
                self.agent_weights[agent_name] = max(0.2, self.agent_weights[agent_name] - 0.05)
            else:
                self.agent_weights[agent_name] = min(1.0, self.agent_weights[agent_name] + 0.01)

            if verdict == "APPROVED":
                approved_weight += effective_weight
                all_tokens.extend(rep.get("memory_tokens", []))

        # 3. Aşama: Commit (2/3 Quorum Barajı)
        quorum_ratio = (approved_weight / max(0.001, total_weight))
        
        if veto_triggered:
            final_verdict = "REJECTED_BY_VETO"
        elif quorum_ratio >= (2.0 / 3.0):
            final_verdict = "APPROVED"
        else:
            final_verdict = "QUORUM_NOT_MET"

        # Kriptografik İmza Üret
        cert_data = f"{mission_id}:{mission_goal}:{final_verdict}:{quorum_ratio}:{approved_weight}"
        cert_hash = hashlib.sha256(cert_data.encode("utf-8")).hexdigest()

        return BFTConsensusCertificate(
            mission_id=mission_id,
            mission_goal=mission_goal,
            consensus_verdict=final_verdict,
            quorum_ratio=quorum_ratio,
            total_voting_weight=total_weight,
            approved_weight=approved_weight,
            byzantine_faults_detected=byzantine_faults,
            veto_triggered=veto_triggered,
            veto_reason=veto_reason,
            committed_virtual_tokens=list(dict.fromkeys(all_tokens)),
            certificate_hash=cert_hash
        )
