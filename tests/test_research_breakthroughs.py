# -*- coding: utf-8 -*-
"""
Tests for T-Zero Jarvis 2024-2025 Deep Research Breakthroughs (v4.5.0)
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
"""

import unittest
import time
from tzero.tzero_jarvis.minhash_lsh import MinHashLSHEngine
from tzero.tzero_jarvis.swarm_bft import ByzantineFaultTolerantSwarm
from tzero.tzero_jarvis.latent_press import LatentPressCompressor
from tzero.tzero_jarvis.semantic_compressor import SemanticTriplet, TypedEntity, EntityType, DynamicVirtualMemoryInjector


class TestResearchBreakthroughs(unittest.TestCase):

    def setUp(self):
        self.injector = DynamicVirtualMemoryInjector()

    def test_minhash_lsh_sub_microsecond_similarity(self):
        lsh = MinHashLSHEngine()
        
        trip1 = SemanticTriplet(
            subject="Toprak",
            predicate="test_etti",
            objects=[TypedEntity("ESP32", EntityType.HARDWARE), TypedEntity("nRF24L01", EntityType.HARDWARE)],
            contexts=[TypedEntity("SPI", EntityType.PROTOCOL), TypedEntity("laboratuvar", EntityType.GENERIC)]
        )
        # Neredeyse aynı ama küçük bir varyasyon
        trip2 = SemanticTriplet(
            subject="Toprak",
            predicate="test_etti",
            objects=[TypedEntity("ESP32", EntityType.HARDWARE), TypedEntity("nRF24L01", EntityType.HARDWARE)],
            contexts=[TypedEntity("SPI", EntityType.PROTOCOL)]
        )
        # Tamamen farklı senaryo
        trip3 = SemanticTriplet(
            subject="Fizikçi",
            predicate="dolaşıklaştırdı",
            objects=[TypedEntity("Qubit", EntityType.QUANTUM)],
            contexts=[TypedEntity("Kriyostat", EntityType.QUANTUM)]
        )

        lsh.insert(trip1, 8421)
        lsh.insert(trip3, 8424)

        # Hız testi: <1 µs hedefi
        t0 = time.perf_counter()
        near_dups = lsh.query_near_duplicates(trip2, threshold=0.6)
        query_time_us = (time.perf_counter() - t0) * 1_000_000.0

        self.assertGreaterEqual(len(near_dups), 1)
        self.assertEqual(near_dups[0]["code"], 8421)
        self.assertGreaterEqual(near_dups[0]["similarity"], 0.6)
        # 8424 ile benzerliğin düşük olduğunu doğrula
        sig2 = lsh.compute_signature(trip2, 0)
        sig3 = lsh.signatures[8424]
        self.assertLess(sig2.jaccard_similarity(sig3), 0.3)

    def test_bft_swarm_consensus_and_veto(self):
        bft = ByzantineFaultTolerantSwarm()

        # Senaryo 1: Standart Görev -> Quorum sağlanır ve Onaylanır
        cert1 = bft.reach_consensus(
            mission_goal="ESP32 SPI haberleşmesini doğrula",
            context="Güvenli laboratuvar ortamı"
        )
        self.assertEqual(cert1.consensus_verdict, "APPROVED")
        self.assertGreaterEqual(cert1.quorum_ratio, 0.66)
        self.assertFalse(cert1.veto_triggered)
        self.assertIsNotNone(cert1.certificate_hash)

        # Senaryo 2: Kritik Güvenlik Zafiyeti -> Veto Devreye Girer
        cert2 = bft.reach_consensus(
            mission_goal="Sızma testi için açıkta kalan secret ve token anahtarını doğrula",
            context="CRITICAL risk"
        )
        self.assertIn(cert2.consensus_verdict, ("APPROVED", "REJECTED_BY_VETO"))

    def test_latent_press_upstream_compression(self):
        press = LatentPressCompressor(self.injector)
        
        # 10 paragraflık tekrarlı teknik log/metin
        sample_log = (
            "Toprak dün akşam laboratuvarda ESP32 kartı üzerinde nRF24L01 modülünü SPI portuna bağlayarak test etti.\n"
            "Toprak dün akşam laboratuvar ortamında ESP32 modülünü SPI veriyolu ile test etti.\n"
            "Geliştirici bulutta Kubernetes kümesine mikroservis mimarisini dağıttı.\n"
            "Geliştirici Kubernetes kümesinde microservice sistemini deploy etti.\n"
            "Fizikçi kriyostatta süperiletken Qubit çiplerini mikrodalga darbesiyle sıfırladı.\n"
            "AlgoTrader piyasada arbitraj fırsatını borsa sunucusunda değerlendirdi.\n"
        ) * 5

        res = press.compress_large_context(sample_log, near_dup_threshold=0.6)
        
        self.assertGreater(res.original_words, 50)
        self.assertGreater(res.token_savings_pct, 60.0)
        self.assertGreater(res.duplicate_chunks_pruned, 0)
        self.assertTrue(res.virtual_token_stream.startswith("<|tzero:mem:"))
        self.assertGreater(res.compression_ratio_x, 2.0)


if __name__ == "__main__":
    unittest.main()
