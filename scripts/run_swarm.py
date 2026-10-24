# -*- coding: utf-8 -*-
"""
CLI runner for the 5-Agent Autonomous Swarm Orchestrator.
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
"""

import sys
import json
from tzero_jarvis.swarm import SwarmCoordinator

def run_swarm(goal: str = "ESP32 mikrodenetleyici üzerinde nRF24L01 modülünü SPI veriyolu ile güvenli şekilde devreye al"):
    print(f"[*] Hedef Görev: {goal}\n")
    sc = SwarmCoordinator()
    report = sc.coordinate_mission(goal)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report

if __name__ == "__main__":
    mission = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "ESP32 mikrodenetleyici üzerinde nRF24L01 modülünü SPI veriyolu ile güvenli şekilde devreye al"
    run_swarm(mission)
