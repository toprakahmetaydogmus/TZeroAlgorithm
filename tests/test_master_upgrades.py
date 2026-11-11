# -*- coding: utf-8 -*-
"""
Tests for T-Zero Jarvis Master-Tier Upgrades (v4.4.0)
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
"""

import unittest
import os
import tempfile
from tzero.tzero_jarvis.causal_graph import CausalTemporalGraph, CausalRelationType
from tzero.tzero_jarvis.self_healing import SelfHealingExecutionEngine
from tzero.tzero_jarvis.memory_consolidation import ConsolidationEngine, EpisodicMemoryBuffer
from tzero.tzero_jarvis.hybrid_search import ZeroVectorDBSearchEngine
from tzero.tzero_jarvis.swarm import SwarmCoordinator
from tzero.tzero_jarvis.graph_visualizer import CyberpunkGraphVisualizer
from tzero.tzero_jarvis.semantic_compressor import SemanticTriplet, TypedEntity, EntityType, DynamicVirtualMemoryInjector


class TestMasterUpgrades(unittest.TestCase):

    def setUp(self):
        self.injector = DynamicVirtualMemoryInjector()
        self.causal_graph = CausalTemporalGraph(self.injector.codebook)

    def test_causal_graph_root_causes_and_rollback(self):
        # Olay 1: Toprak SPI veriyolunu yanlış konfigüre etti
        self.causal_graph.add_node("n1", "SPI Hatalı Baudrate", "PROTOCOL")
        # Olay 2: nRF24L01 paket düşmesi yaşandı
        self.causal_graph.add_node("n2", "nRF24L01 Paket Kaybı", "HARDWARE")
        # Olay 3: Veri transferi zaman aşımına uğradı
        self.causal_graph.add_node("n3", "İletişim Zaman Aşımı Hatası", "SOFTWARE")

        self.causal_graph.add_edge("n1", "n2", relation=CausalRelationType.CAUSES)
        self.causal_graph.add_edge("n2", "n3", relation=CausalRelationType.CAUSES)

        # Kök neden analizi
        root_causes = self.causal_graph.get_root_causes("n3")
        self.assertTrue(len(root_causes) >= 1)
        self.assertEqual(root_causes[0]["root_node_id"], "n1")

        # Rollback planı
        rollback = self.causal_graph.compute_rollback_order("n1")
        self.assertTrue(len(rollback) >= 2)

    def test_self_healing_execution(self):
        engine = SelfHealingExecutionEngine(self.causal_graph)
        
        # Test 1: Başarılı komut
        res = engine.run_command("python -c \"print('T-Zero Self-Healing OK')\"")
        self.assertTrue(res.success)
        self.assertIn("T-Zero Self-Healing OK", res.stdout)

        # Test 2: Hata Teşhisi
        sample_tb = """Traceback (most recent call last):
  File "test_script.py", line 42, in <module>
    import unknown_custom_mod
ModuleNotFoundError: No module named 'unknown_custom_mod'"""
        err_type, err_file, err_line = engine.diagnose_error(sample_tb)
        self.assertEqual(err_type, "ModuleNotFoundError")
        self.assertEqual(err_file, "test_script.py")
        self.assertEqual(err_line, 42)

    def test_self_healing_python_auto_repair(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_code_path = os.path.join(tmpdir, "broken.py")
            # Eksik iki nokta ':' olan kod
            with open(bad_code_path, "w", encoding="utf-8") as f:
                f.write("def calculate_crc()\n    return 42\n")

            engine = SelfHealingExecutionEngine(self.causal_graph, work_dir=tmpdir)
            repaired = engine.auto_repair_python_file(
                bad_code_path,
                "SyntaxError",
                1,
                "SyntaxError: expected ':'"
            )
            self.assertTrue(repaired)
            
            with open(bad_code_path, "r", encoding="utf-8") as f:
                fixed_content = f.read()
            self.assertIn("def calculate_crc():", fixed_content)

    def test_memory_consolidation_contradiction_resolution(self):
        engine = ConsolidationEngine(self.injector.codebook)
        
        # Olay 1: Hata bildiren epizot
        engine.episodic_buffer.record_episode("ESP32 SPI haberleşmesi zaman aşımı hatası verdi.", source="sensor")
        # Olay 2: Çözüm bildiren epizot
        engine.episodic_buffer.record_episode("ESP32 SPI bağlantısı düzeltildi ve başarılı oldu.", source="user")

        summary = engine.consolidate()
        self.assertEqual(summary["status"], "success")
        self.assertGreaterEqual(summary["contradictions_resolved"], 1)

        # İlk epizodun superseded olduğunu doğrula
        first_ep = engine.episodic_buffer.episodes[0]
        self.assertTrue(first_ep.superseded)

    def test_hybrid_search_bm25_and_codebook(self):
        engine = ZeroVectorDBSearchEngine()
        
        # ESP32 #8421 Dokümanı
        engine.add_document(
            doc_id="doc_esp",
            doc_type="triplet",
            title="ESP32 nRF24L01 SPI Testi",
            content="Toprak laboratuvarda ESP32 kartına nRF24L01 modülünü bağlayarak SPI üzerinden test etti.",
            discrete_code=8421,
            domain="HARDWARE"
        )
        # STM32 Dokümanı
        engine.add_document(
            doc_id="doc_stm",
            doc_type="triplet",
            title="STM32 CAN Bus Testi",
            content="Mühendis STM32 mikrodenetleyici üzerinde CAN veriyolunu 500kbps hızında denedi.",
            discrete_code=9012,
            domain="HARDWARE"
        )

        # Arama 1: Kelime bazlı
        res1 = engine.search("nRF24L01 SPI", top_k=5)
        self.assertTrue(len(res1) >= 1)
        self.assertEqual(res1[0].doc_id, "doc_esp")

        # Arama 2: Doğrudan #8421 latent code araması (Boost testi)
        res2 = engine.search("#8421", top_k=5)
        self.assertTrue(len(res2) >= 1)
        self.assertEqual(res2[0].discrete_code, 8421)
        self.assertIn("code_exact_match:#8421", res2[0].match_reasons)

    def test_swarm_multi_agent_coordination(self):
        coordinator = SwarmCoordinator(self.injector, self.causal_graph)
        res = coordinator.coordinate_mission(
            mission_goal="ESP32 ile nRF24L01 modülünü SPI portundan güvenli şekilde devreye al",
            context="Laboratuvar donanım testi"
        )
        self.assertIn("consensus", res)
        self.assertEqual(res["orchestrator"], "JARVIS Prime")
        self.assertEqual(res["swarm_agent_count"], 5)
        self.assertTrue(len(res["agent_reports"]) >= 4)
        self.assertTrue(len(res["aggregated_memory_tokens"]) >= 1)

    def test_cyberpunk_graph_visualizer_html(self):
        visualizer = CyberpunkGraphVisualizer(self.causal_graph)
        html = visualizer.generate_html("T-Zero Test Graph")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("T-ZERO 4D KNOWLEDGE & CAUSAL GRAPH", html)
        self.assertIn("graphCanvas", html)
        self.assertIn("domainColors", html)


if __name__ == "__main__":
    unittest.main()
