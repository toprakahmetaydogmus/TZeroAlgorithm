# -*- coding: utf-8 -*-
"""
Unit tests for T-Zero Jarvis 3-Layer Semantic Memory Compression Engine.
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Version: 4.2.0
"""

import os
import unittest
from tzero.tzero_jarvis.semantic_compressor import (
    SemanticTriplet,
    SemanticTripletExtractor,
    VectorQuantizedCodebook,
    DynamicVirtualMemoryInjector,
    EntityType,
    TypedEntity,
    get_global_compressor
)


class TestSemanticMemoryCompression(unittest.TestCase):

    def setUp(self):
        self.compressor = DynamicVirtualMemoryInjector()

    def test_user_reference_scenario(self):
        """
        Kullanıcının talep ettiği altın standart test senaryosu:
        'Toprak dün akşam laboratuvarda ESP32 kartı üzerinde nRF24L01 modülünü SPI portuna bağlayarak test etti.'
        """
        text = "Toprak dün akşam laboratuvarda ESP32 kartı üzerinde nRF24L01 modülünü SPI portuna bağlayarak test etti."
        res = self.compressor.compress_text_to_virtual_tokens(text)

        # 1. Token İndirgeme Oranı (> %80, kullanıcı hedefi ~%94-96)
        self.assertGreaterEqual(res["reduction_ratio_pct"], 80.0)
        self.assertEqual(res["compressed_token_count"], 1)

        # 2. Katman A: Çizge Doğrulaması
        triplet_dict = res["triplets"][0]
        self.assertEqual(triplet_dict["subject"], "Toprak")
        self.assertEqual(triplet_dict["predicate"], "test_etti")

        obj_names = [o["name"] for o in triplet_dict["objects"]]
        self.assertIn("ESP32", obj_names)
        self.assertIn("nRF24L01", obj_names)

        # 3. Katman B: VQ Codebook Eşlemesi (Önceden seed edilmiş #8421)
        self.assertIn(8421, res["codebook_ids"])

        # 4. Katman C: Sanal Bellek Token'ı (<|tzero:mem:8421|>)
        self.assertIn("<|tzero:mem:8421|>", res["virtual_tokens"])

        # 5. Dinamik Çözümleme (Round-trip decoding)
        decoded = self.compressor.decode_virtual_token(8421)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded["code_id"], 8421)
        self.assertIn("Toprak", decoded["reconstructed_summary"])

    def test_compound_light_verbs(self):
        """Türkçe bileşik eylemlerin (Light Verbs: devreye aldı, analiz yaptı vb.) doğru tespiti."""
        text = "Geliştirici ekibi sistemi devreye aldı."
        triplets = SemanticTripletExtractor.extract_triplets(text)
        self.assertEqual(len(triplets), 1)
        self.assertEqual(triplets[0].predicate, "devreye_aldi")

    def test_turkish_stemmer_and_agent_nouns(self):
        """Çekim eklerinin temizlenmesi ve meslek/icracı isimlerinin korunması."""
        # Kesme işareti ve yönelme eki
        self.assertEqual(SemanticTripletExtractor.strip_turkish_suffixes("ESP32'yi"), "ESP32")
        self.assertEqual(SemanticTripletExtractor.strip_turkish_suffixes("PostgreSQL'in"), "PostgreSQL")

        # İcracı/Meslek eklerinin korunması
        self.assertEqual(SemanticTripletExtractor.strip_turkish_suffixes("Geliştirici"), "Geliştirici")
        self.assertEqual(SemanticTripletExtractor.strip_turkish_suffixes("Araştırmacı"), "Araştırmacı")

    def test_ner_tagging(self):
        """Varlık tipi sınıflandırma testleri."""
        self.assertEqual(SemanticTripletExtractor.classify_entity("ESP32"), EntityType.HARDWARE)
        self.assertEqual(SemanticTripletExtractor.classify_entity("nRF24L01"), EntityType.HARDWARE)
        self.assertEqual(SemanticTripletExtractor.classify_entity("SPI"), EntityType.PROTOCOL)
        self.assertEqual(SemanticTripletExtractor.classify_entity("192.168.1.1"), EntityType.IP)
        self.assertEqual(SemanticTripletExtractor.classify_entity("AES-256"), EntityType.CRYPTO)
        self.assertEqual(SemanticTripletExtractor.classify_entity("CVE-2024-1234"), EntityType.VULN)
        self.assertEqual(SemanticTripletExtractor.classify_entity("Kubernetes"), EntityType.SOFTWARE)

    def test_extended_universal_domains(self):
        """Kuantum, Biyo, Havacılık, Otomotiv, Finans, Robotik varlık sınıflandırma testleri."""
        self.assertEqual(SemanticTripletExtractor.classify_entity("Qubit"), EntityType.QUANTUM)
        self.assertEqual(SemanticTripletExtractor.classify_entity("Qiskit"), EntityType.QUANTUM)
        self.assertEqual(SemanticTripletExtractor.classify_entity("CRISPR"), EntityType.BIO)
        self.assertEqual(SemanticTripletExtractor.classify_entity("Cas9"), EntityType.BIO)
        self.assertEqual(SemanticTripletExtractor.classify_entity("AlphaFold"), EntityType.BIO)
        self.assertEqual(SemanticTripletExtractor.classify_entity("Avionics"), EntityType.AEROSPACE)
        self.assertEqual(SemanticTripletExtractor.classify_entity("Telemetry"), EntityType.AEROSPACE)
        self.assertEqual(SemanticTripletExtractor.classify_entity("AUTOSAR"), EntityType.AUTOMOTIVE)
        self.assertEqual(SemanticTripletExtractor.classify_entity("ECU"), EntityType.AUTOMOTIVE)
        self.assertEqual(SemanticTripletExtractor.classify_entity("OrderBook"), EntityType.FINANCE)
        self.assertEqual(SemanticTripletExtractor.classify_entity("VWAP"), EntityType.FINANCE)
        self.assertEqual(SemanticTripletExtractor.classify_entity("ROS2"), EntityType.ROBOTICS)
        self.assertEqual(SemanticTripletExtractor.classify_entity("URDF"), EntityType.ROBOTICS)

    def test_multilingual_english_verbs(self):
        """İngilizce teknik eylemlerin canonical yükleme dönüştürülmesi."""
        text = "Developer deployed Kubernetes cluster via TLS connection."
        triplets = SemanticTripletExtractor.extract_triplets(text)
        self.assertEqual(len(triplets), 1)
        self.assertEqual(triplets[0].predicate, "devreye_aldi")

    def test_document_compression(self):
        """Çok paragraflı geniş teknik döküman sıkıştırması ve topoloji üretimi."""
        doc = (
            "Toprak dün akşam laboratuvarda ESP32 kartı üzerinde nRF24L01 modülünü SPI portuna bağlayarak test etti.\n\n"
            "Geliştirici ekibi Kubernetes kümesinde PostgreSQL veritabanını devreye aldı.\n\n"
            "Araştırmacı PyTorch kütüphanesinde Transformer modelini eğitti."
        )
        res = self.compressor.compress_document(doc)
        self.assertEqual(res["total_paragraphs"], 3)
        self.assertEqual(res["total_triplets_extracted"], 3)
        self.assertGreaterEqual(res["reduction_ratio_pct"], 80.0)
        self.assertIn("<|tzero:mem:8421|>", res["virtual_token_string"])
        self.assertIn("nodes", res["topology"])
        self.assertIn("edges", res["topology"])

    def test_knowledge_graph_query_and_persistence(self):
        """Bilgi grafiği sorgulama ve kalıcı disk depolama testi."""
        import tempfile
        # 1. Graf Sorgulama (Entity / Predicate)
        matches = self.compressor.codebook.query_graph(entity="ESP32")
        self.assertGreaterEqual(len(matches), 1)
        self.assertEqual(matches[0]["code_id"], 8421)

        # 2. Kalıcı Diske Kaydetme ve Yükleme
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            saved_file = self.compressor.codebook.save_to_disk(tmp_path)
            self.assertTrue(os.path.exists(saved_file))

            new_codebook = VectorQuantizedCodebook()
            loaded_count = new_codebook.load_from_disk(tmp_path)
            self.assertGreaterEqual(loaded_count, 1)
            self.assertIsNotNone(new_codebook.lookup(8421))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_compact_code_generation(self):
        """Kompakt anlamsal kod formatı (&S:..#P:..#O:..#C:..)."""
        trip = SemanticTriplet(
            subject="Toprak",
            predicate="test_etti",
            objects=[TypedEntity("ESP32", EntityType.HARDWARE)],
            contexts=[TypedEntity("SPI", EntityType.PROTOCOL)]
        )
        compact = trip.to_compact_code()
        self.assertEqual(compact, "&S:Toprak#P:test_etti#O:ESP32:HARDWARE#C:SPI:PROTOCOL")

    def test_soft_prompt_prefix_generation(self):
        """Dikkat katmanını prime eden Soft-Prompt öneki oluşturma."""
        prefix = self.compressor.build_soft_prompt_prefix(["<|tzero:mem:8421|>"])
        self.assertIn("[T-ZERO HIGH-DENSITY VIRTUAL MEMORY STATE]", prefix)
        self.assertIn("8421", prefix)
        self.assertIn("ATTENTION PRIMING COMPLETE", prefix)

    def test_omni_domain_universal_scenarios(self):
        """Her muhtemel senaryoyu (Kuantum, Biyoloji, Uzay, Otomotiv, Finans, Siber Güvenlik, Robotik) işleme testi."""
        scenarios = [
            # 1. Kuantum
            "Fizikçi laboratuvarda süperiletken Qubit çiplerini mikrodalga darbesiyle sıfırladı.",
            # 2. Otomotiv & Otonom Sürüş
            "Otonom araç otoyolda LiDAR sensör verilerini CAN veriyolu üzerinden analiz etti.",
            # 3. Biyogenetik
            "Genetikçi hücrede CRISPR enzimini AlphaFold modeline göre modifiye etti.",
            # 4. Siber Güvenlik & Exploit
            "Siber analist DMZ ağında BufferOverflow zafiyetini sandbox ortamında izole etti.",
            # 5. Uzay & Havacılık
            "Mühendis yörüngede uydu telemetri verilerini yer istasyonuna aktardı.",
            # 6. Finans & Borsa
            "AlgoTrader piyasada arbitraj fırsatını borsa sunucusunda değerlendirdi.",
            # 7. Robotik
            "Kontrolcü fabrikada konveyör hattında robotik manipülatörü kalibre etti.",
            # 8. Bulut & Yazılım
            "Geliştirici bulutta Kubernetes kümesine mikroservis mimarisini dağıttı."
        ]

        for s in scenarios:
            res = self.compressor.compress_text_to_virtual_tokens(s)
            self.assertGreater(len(res["triplets"]), 0)
            self.assertGreater(len(res["virtual_tokens"]), 0)
            self.assertTrue(res["virtual_tokens"][0].startswith("<|tzero:mem:"))
            self.assertGreater(res["reduction_ratio_pct"], 50.0)

            # Çift yönlü kod çözme doğrulaması
            vt = res["virtual_tokens"][0]
            decoded = self.compressor.decode_virtual_token(vt)
            self.assertIsNotNone(decoded)
            self.assertIn("subject", decoded["triplet"])


if __name__ == "__main__":
    unittest.main()
