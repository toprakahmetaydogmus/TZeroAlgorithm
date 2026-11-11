# -*- coding: utf-8 -*-
"""
T-ZERO JARVIS UNIVERSAL 3-LAYER SEMANTIC MEMORY & COMPRESSION ENGINE
---------------------------------------------------------------------
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Version: 4.3.0

Evrensel 3-Katmanlı Anlamsal Çekirdek ve Vektör Bellek Mimarisi:
Katman A: Çok Dilli ve Çok Alanlı Anlamsal Graf Çıkarımı (TR + EN + 12 Alanlı NER)
Katman B: Deterministik Vektör Kuantizasyon Sözlüğü (VQ Codebook + Graf Topolojisi)
Katman C: Dinamik Soft-Prompt Sanal Bellek Enjeksiyonu (<|tzero:mem:ID|>) + Bellek Arama
"""

import re
import os
import json
import hashlib
import ipaddress
from typing import List, Dict, Optional, Tuple, Any, Union, Set
from dataclasses import dataclass, asdict


class EntityType:
    HARDWARE = "HARDWARE"
    PROTOCOL = "PROTOCOL"
    IP = "IP"
    CRYPTO = "CRYPTO"
    VULN = "VULN"
    SOFTWARE = "SOFTWARE"
    QUANTUM = "QUANTUM"
    BIO = "BIO"
    AEROSPACE = "AEROSPACE"
    AUTOMOTIVE = "AUTOMOTIVE"
    FINANCE = "FINANCE"
    ROBOTICS = "ROBOTICS"
    GENERIC = "GENERIC"


@dataclass
class TypedEntity:
    name: str
    entity_type: str = EntityType.GENERIC

    def to_tagged_string(self) -> str:
        if self.entity_type == EntityType.GENERIC:
            return self.name
        return f"{self.name}:{self.entity_type}"


@dataclass
class SemanticTriplet:
    """Saf anlamsal çizge üçlüsü (Graph Triplet) with NER."""
    subject: str
    predicate: str
    objects: List[TypedEntity]
    contexts: List[TypedEntity]

    def to_graph_string(self) -> str:
        """Kompakt çizge gösterimi üretir: (Özne)->[Yüklem]->(Nesne:TIP + Nesne:TIP | Bağlam:TIP)"""
        obj_str = " + ".join(o.to_tagged_string() for o in self.objects) if self.objects else "Hedef"
        ctx_str = " | ".join(c.to_tagged_string() for c in self.contexts) if self.contexts else ""
        if ctx_str:
            return f"({self.subject})->[{self.predicate}]->({obj_str} | {ctx_str})"
        return f"({self.subject})->[{self.predicate}]->({obj_str})"

    def to_compact_code(self) -> str:
        """Token tasarrufu sağlayan ultra sıkışık format: &S:Özne#P:Eylem#O:Nesneler#C:Bağlamlar"""
        obj_str = "+".join(o.to_tagged_string() for o in self.objects)
        ctx_str = "|".join(c.to_tagged_string() for c in self.contexts)
        return f"&S:{self.subject}#P:{self.predicate}#O:{obj_str}#C:{ctx_str}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "objects": [asdict(o) for o in self.objects],
            "contexts": [asdict(c) for c in self.contexts],
            "graph_representation": self.to_graph_string(),
            "compact_code": self.to_compact_code()
        }


class SemanticTripletExtractor:
    """Katman A: Dolgu kelimeleri temizleyip mantıksal çizgeye dönüştüren evrensel çıkarıcı."""

    STOPWORDS = frozenset({
        # Türkçe Dolgular
        "ve", "veya", "ile", "için", "icin", "dolayısıyla", "dolayisiyla", "bu", "şu", "su", "o",
        "bir", "birkaç", "birkac", "dün", "dun", "akşam", "aksam", "sabah", "öğle", "ogle", "gece",
        "bugün", "bugun", "yarın", "yarin", "şimdi", "simdi", "üzerinde", "uzerinde", "üzerine", "uzerine",
        "altında", "altinda", "yanında", "yaninda", "tarafından", "tarafindan", "aracılığıyla", "araciligiyla",
        "vasıtasıyla", "vasitasiyla", "bağlayarak", "baglayarak", "kullanarak", "yoluyla", "şekilde", "sekilde",
        "falan", "filan", "şey", "sey", "dair", "göre", "gore", "kadar", "beri", "sonra", "önce", "once",
        "dolayı", "dolayi", "ötürü", "oturu", "adeta", "neredeyse",
        "kart", "karti", "kartı", "kartını", "kartini", "modül", "modul", "modülü", "modulu", "modülün", "modulun", "modülünü", "modulunu",
        "port", "portu", "portuna", "üzeri", "uzeri", "üzerin", "uzerin", "üzerinde", "uzerinde", "üzerine", "uzerine",
        "cihaz", "cihazı", "cihazi", "cihazını", "sunucu", "sunucusu", "sunucusunu", "küme", "kume", "kümesi", "kumesi",
        "kümesini", "tablo", "tablosu", "tablosunu", "ekip", "ekibi", "kütüphane", "kutuphane", "kütüphanesi",
        # İngilizce Dolgular
        "and", "or", "with", "for", "therefore", "thus", "hence", "the", "a", "an",
        "yesterday", "evening", "today", "morning", "night", "now", "on", "in", "at",
        "by", "through", "using", "via", "connecting", "connected", "over", "under", "into",
        "from", "to", "after", "before", "while", "during", "towards", "as", "well",
        "module", "card", "board", "chip", "port", "bus", "system", "environment", "device"
    })

    HARDWARE_KEYWORDS = frozenset({
        "ESP32", "ESP8266", "NRF24L01", "NRF24", "STM32", "ARDUINO", "RASPBERRY", "RASPBERRYPI",
        "PIC", "AVR", "FPGA", "CPLD", "RP2040", "TEENSY", "SENSOR", "OLED", "LCD", "SERVO",
        "MOTOR", "RELAY", "TRANSCEIVER", "ACCELEROMETER", "GYROSCOPE", "BAROMETER", "RFID",
        "MICROCONTROLLER", "MCU", "SOC", "RISCV", "RISC-V", "ARM", "CORTEX", "PCB", "ASIC"
    })

    PROTOCOL_KEYWORDS = frozenset({
        "SPI", "I2C", "UART", "CAN", "GPIO", "USB", "TCP", "UDP", "HTTP", "HTTPS",
        "REST", "GRPC", "WEBSOCKET", "MQTT", "COAP", "BLE", "WIFI", "LORA", "ZIGBEE",
        "TLS", "SSL", "SSH", "IPSEC", "MODBUS", "PROFIBUS", "ETHERNET", "PCIE", "DMA", "JTAG", "SWD"
    })

    CRYPTO_KEYWORDS = frozenset({
        "AES-256", "AES-128", "AES", "RSA-4096", "RSA-2048", "RSA", "ECC", "ECDSA",
        "SHA-256", "SHA-512", "SHA-3", "MD5", "HMAC", "PBKDF2", "CHACHA20", "POLY1305",
        "JWT", "OAUTH2", "ARGON2", "BCRYPT", "PGP", "GPG", "ZERO-KNOWLEDGE", "ZK-SNARK"
    })

    SOFTWARE_KEYWORDS = frozenset({
        "KUBERNETES", "K8S", "DOCKER", "POSTGRESQL", "POSTGRES", "MYSQL", "MONGODB",
        "REDIS", "RABBITMQ", "KAFKA", "NGINX", "APACHE", "LINUX", "WINDOWS", "PYTORCH",
        "TENSORFLOW", "FASTAPI", "NODEJS", "REACT", "VUE", "TAILWIND", "RUST", "PYTHON",
        "ELK", "ELASTICSEARCH", "PROMETHEUS", "GRAFANA", "TERRAFORM", "ANSIBLE", "GIT"
    })

    QUANTUM_KEYWORDS = frozenset({
        "QUBIT", "QUBITS", "QISKIT", "CIRQ", "SHOR", "GROVER", "HAMILTONIAN", "TELEPORTATION",
        "SUPERCONDUCTING", "IONTRAP", "QUANTUM_GATE", "QUANTUM", "BELL_STATE", "ENTANGLEMENT"
    })

    BIO_KEYWORDS = frozenset({
        "CRISPR", "CAS9", "ALPHAFOLD", "MRNA", "DNA", "RNA", "EXON", "INTRON", "CODON",
        "RIBOSOME", "GENOME", "GENOMICS", "PROTEIN", "BLAST", "TRANSCRIPTION", "TRANSLATION"
    })

    AEROSPACE_KEYWORDS = frozenset({
        "AVIONICS", "TELEMETRY", "IMU", "CANAEROSPACE", "ARINC429", "ARINC", "MIL-STD-1553",
        "GYROSCOPE", "THRUST", "RCS", "SATELLITE", "STARTRACKER", "ORBIT", "PROPULSION"
    })

    AUTOMOTIVE_KEYWORDS = frozenset({
        "AUTOSAR", "CAN_FD", "CANFD", "LIN", "FLEXRAY", "ECU", "BMS", "OBD2", "OBD",
        "OBD-II", "LIDAR", "ADAS", "RADAR", "DRIVEBYWIRE"
    })

    FINANCE_KEYWORDS = frozenset({
        "ORDERBOOK", "FIX", "VWAP", "ARBITRAGE", "MARKETMAKER", "HFT", "DERIVATIVE",
        "OPTION", "HEDGING", "ALGOTRADING", "EQUITY", "LIQUIDITY"
    })

    ROBOTICS_KEYWORDS = frozenset({
        "ROS", "ROS2", "MICROROS", "MICRO-ROS", "DDS", "URDF", "SLAM", "KINEMATICS",
        "GAZEBO", "ACTUATOR", "SERVO", "ODOMETRY"
    })

    ACTION_MAP = {
        # Türkçe Eylemler
        "test etti": "test_etti",
        "test_etti": "test_etti",
        "denedi": "test_etti",
        "devreye aldı": "devreye_aldi",
        "devreye aldi": "devreye_aldi",
        "bağladı": "bagladi",
        "bagladi": "bagladi",
        "çalıştırdı": "calistirdi",
        "calistirdi": "calistirdi",
        "derledi": "derledi",
        "yazdı": "yazdi",
        "analiz etti": "analiz_etti",
        "onardı": "onardi",
        "onardi": "onardi",
        "düzeltti": "onardi",
        "kurdu": "kurdu",
        "eğitti": "egitti",
        "egitti": "egitti",
        "şifreledi": "sifreledi",
        "sifreledi": "sifreledi",
        "doğruladı": "dogruladi",
        "dogruladi": "dogruladi",
        "izledi": "izledi",
        "kalibre etti": "kalibre_etti",
        "entegre etti": "entegre_etti",
        "sentezledi": "sentezledi",
        "simüle etti": "simule_etti",
        "yamaladı": "yamaladi",
        "yapılandırdı": "yapilandirdi",
        # İngilizce Eylemler
        "tested": "test_etti",
        "ran": "calistirdi",
        "compiled": "derledi",
        "analyzed": "analiz_etti",
        "fixed": "onardi",
        "repaired": "onardi",
        "deployed": "devreye_aldi",
        "trained": "egitti",
        "encrypted": "sifreledi",
        "verified": "dogruladi",
        "connected": "bagladi",
        "configured": "yapilandirdi",
        "patched": "yamaladi",
        "calibrated": "kalibre_etti",
        "integrated": "entegre_etti",
        "monitored": "izledi",
        "simulated": "simule_etti",
        "synthesized": "sentezledi",
        "reverse engineered": "tersine_muhendislik_yapti"
    }

    # 5. TÜRKÇE İSİM ÇEKİM EKLERİ TEMİZLEYİCİ (Stemmer / Lemmatizer)
    @classmethod
    def strip_turkish_suffixes(cls, word: str) -> str:
        """Kesme işaretini ve yönelme/ayrılma eklerini atar (ESP32'yi -> ESP32)."""
        base = word.split("'")[0].split("’")[0]
        suffixes = (
            "sinde", "sında", "sinden", "sından", "leriyle", "larıyla", "lerin", "ların",
            "lerinin", "larının", "lerine", "larına", "den", "dan", "ten", "tan", "nin",
            "nın", "nun", "nün", "de", "da", "te", "ta", "ye", "ya", "ne", "na",
            "in", "ın", "un", "ün", "e", "a", "i", "ı", "u", "ü"
        )
        clean = base
        clean_lower = clean.lower()
        # Meslek / fail / icracı eklerini koru (-ici, -ıcı, -ucu, -ücü, -maci, -macı)
        agent_suffixes = ("ici", "ıcı", "ucu", "ücü", "maci", "macı", "men", "man", "ist", "tor", "tör", "er", "or")
        if any(clean_lower.endswith(asuf) for asuf in agent_suffixes):
            return clean

        for suf in suffixes:
            if clean_lower.endswith(suf) and len(clean) > len(suf) + 3:
                clean = clean[:-len(suf)]
                break
        return clean

    # 3. VARLIK TİPİ TESPİTİ (12-Alanlı Kapsamlı NER Tagging)
    @classmethod
    def classify_entity(cls, token: str) -> str:
        upper = token.upper()

        # 1. IP Adresi
        try:
            ipaddress.IPv4Address(upper)
            return EntityType.IP
        except ValueError:
            pass

        # 2. Güvenlik Zafiyeti (CVE-YYYY-NNNNN vb.)
        if upper.startswith("CVE-") or "VULN" in upper or "EXPLOIT" in upper:
            return EntityType.VULN

        # 3. Kriptografi
        if upper in cls.CRYPTO_KEYWORDS or upper.startswith("AES") or upper.startswith("RSA"):
            return EntityType.CRYPTO

        # 4. Kuantum Bilişim
        if upper in cls.QUANTUM_KEYWORDS or upper.startswith("QUBIT"):
            return EntityType.QUANTUM

        # 5. Biyoinformatik & Genetik
        if upper in cls.BIO_KEYWORDS or upper.startswith("CRISPR") or upper.startswith("CAS9"):
            return EntityType.BIO

        # 6. Havacılık & Aviyonik
        if upper in cls.AEROSPACE_KEYWORDS:
            return EntityType.AEROSPACE

        # 7. Otomotiv & Otonom Sürüş
        if upper in cls.AUTOMOTIVE_KEYWORDS:
            return EntityType.AUTOMOTIVE

        # 8. Finansal Mühendislik & HFT
        if upper in cls.FINANCE_KEYWORDS:
            return EntityType.FINANCE

        # 9. Robotik & Kontrol
        if upper in cls.ROBOTICS_KEYWORDS or upper.startswith("ROS"):
            return EntityType.ROBOTICS

        # 10. Protokol
        if upper in cls.PROTOCOL_KEYWORDS:
            return EntityType.PROTOCOL

        # 11. Donanım
        if upper in cls.HARDWARE_KEYWORDS or upper.startswith("NRF") or upper.startswith("ESP") or upper.startswith("STM"):
            return EntityType.HARDWARE

        # 12. Yazılım
        if upper in cls.SOFTWARE_KEYWORDS:
            return EntityType.SOFTWARE

        return EntityType.GENERIC

    # 2. TÜRKÇE & İNGİLİZCE BİLEŞİK FİİLLER (Light Verbs) n-gram DEDEKTÖRÜ
    @classmethod
    def detect_compound_predicate(cls, tokens: List[str]) -> Optional[Tuple[str, int, int]]:
        auxiliaries = {"etti", "yaptı", "yapti", "aldı", "aldi", "kıldı", "kildi", "oldu", "verdi", "geçti", "gecti", "buldu"}
        for i in range(len(tokens) - 1):
            first = re.sub(r"[^\w]", "", tokens[i]).lower()
            second = re.sub(r"[^\w]", "", tokens[i + 1]).lower()
            combined = f"{first} {second}"
            if combined in cls.ACTION_MAP:
                return (cls.ACTION_MAP[combined], i, i + 1)
            if any(aux in second for aux in auxiliaries):
                return (f"{first}_{second}", i, i + 1)
        return None

    @classmethod
    def _normalize_predicate(cls, raw_verb: str) -> str:
        v = raw_verb.lower().strip()
        for k, val in cls.ACTION_MAP.items():
            if k in v:
                return val
        if "test" in v or "dene" in v:
            return "test_etti"
        if "bağla" in v or "connect" in v:
            return "bagladi"
        if "çalıştır" in v or "run" in v:
            return "calistirdi"
        if "derle" in v or "compile" in v:
            return "derledi"
        if "şifrele" in v or "encrypt" in v:
            return "sifreledi"
        if "dağıt" in v or "deploy" in v:
            return "devreye_aldi"
        if "kur" in v or "install" in v:
            return "kurdu"
        if "analiz" in v or "analyze" in v:
            return "analiz_etti"
        if "onar" in v or "fix" in v or "repair" in v:
            return "onardi"
        if "eğit" in v or "train" in v:
            return "egitti"
        if "doğrula" in v or "verify" in v:
            return "dogruladi"
        if "kalibre" in v or "calibrate" in v:
            return "kalibre_etti"
        if "entegre" in v or "integrate" in v:
            return "entegre_etti"
        return "islem_yapti"

    @classmethod
    def extract_triplets(cls, text: str) -> List[SemanticTriplet]:
        """Metinden anlamsal graf üçlülerini eksiksiz ve deterministik çıkarır."""
        triplets: List[SemanticTriplet] = []
        if not text or not text.strip():
            return triplets

        # Cümle bazlı ayrıştırma
        sentences = re.split(r"[\.\!\?;\n]+", text)
        for sent in sentences:
            sent_str = sent.strip()
            if not sent_str:
                continue

            raw_tokens = sent_str.split()
            if not raw_tokens:
                continue

            # 1. Bileşik Eylemleri n-gram ile yakala
            comp = cls.detect_compound_predicate(raw_tokens)
            if comp:
                predicate = comp[0]
                verb_start, verb_end = comp[1], comp[2]
            else:
                # SVO (İngilizce/Doğrudan) veya bilinen fiilleri ara (Örn: "Developer deployed Kubernetes")
                found_verb = None
                for idx, tok in enumerate(raw_tokens):
                    clean_tok = re.sub(r"[^\w]", "", tok).lower()
                    if clean_tok in cls.ACTION_MAP:
                        found_verb = (cls.ACTION_MAP[clean_tok], idx, idx)
                        break

                if found_verb:
                    predicate, verb_start, verb_end = found_verb
                else:
                    # SOV (Türkçe cümle sonu) fiilini kontrol et
                    verb_candidate = raw_tokens[-1]
                    predicate = cls._normalize_predicate(verb_candidate)
                    verb_start, verb_end = len(raw_tokens) - 1, len(raw_tokens) - 1

            # 2. Özne Tespiti
            subject = ""
            subject_idx = None
            for idx, tok in enumerate(raw_tokens):
                clean = cls.strip_turkish_suffixes(re.sub(r"[^\w\-\.]", "", tok))
                if clean and clean.lower() not in cls.STOPWORDS:
                    subject = clean
                    subject_idx = idx
                    break

            if not subject:
                subject = "Sistem"

            # 3. Nesneler & Bağlamlar
            objects: List[TypedEntity] = []
            contexts: List[TypedEntity] = []

            for idx, tok in enumerate(raw_tokens):
                if idx == subject_idx:
                    continue
                if verb_start is not None and verb_end is not None and verb_start <= idx <= verb_end:
                    continue

                stemmed = cls.strip_turkish_suffixes(re.sub(r"[^\w\-\.]", "", tok))
                if not stemmed or stemmed.lower() in cls.STOPWORDS:
                    continue

                ent_type = cls.classify_entity(stemmed)
                typed_ent = TypedEntity(stemmed, ent_type)

                # Evrensel Bağlam Tespiti (Morfolojik veya Anahtar Kelime)
                raw_low = tok.lower()
                clean_low = stemmed.lower()
                is_context = (
                    ent_type == EntityType.PROTOCOL or
                    any(raw_low.endswith(sfx) for sfx in (
                        "da", "de", "ta", "te", "dan", "den", "tan", "ten",
                        "ında", "inde", "sında", "sinde", "unda", "ünde", "sunda", "sünde"
                    )) or
                    any(env in clean_low or env in raw_low for env in (
                        "laboratuvar", "lab", "atölye", "atolye", "oda", "saha", "kart", "board", "pin", "port",
                        "sunucu", "server", "küme", "kume", "cluster", "cloud", "bulut", "production", "prod", "staging", "dev",
                        "ağ", "network", "subnet", "dmz", "vpn", "intranet", "internet", "firewall", "honeypot", "sandbox",
                        "kriyostat", "cryostat", "vakum", "kavite", "cavity", "lattice",
                        "hücre", "hucre", "cell", "doku", "tissue", "petri", "in_vitro", "in_vivo", "reaktör",
                        "yörünge", "yorunge", "orbit", "uzay", "space", "atmosfer", "istasyon", "hangar", "uydu",
                        "araç", "arac", "vehicle", "şasi", "sasi", "chassis", "motor", "otoyol", "highway", "kabin",
                        "borsa", "market", "piyasa", "exchange", "kasa", "cüzdan", "wallet", "banka", "bank",
                        "fabrika", "factory", "konveyör", "konveyor", "arena", "simülasyon", "simulasyon", "sim",
                        "ev", "ofis", "şehir", "sehir", "arşiv", "arsiv", "kütüphane", "kutuphane", "masada", "ekranda", "ortam", "environment"
                    ))
                )

                if is_context:
                    contexts.append(typed_ent)
                elif len(objects) < 8:
                    if not any(o.name == typed_ent.name for o in objects):
                        objects.append(typed_ent)

            triplets.append(SemanticTriplet(subject, predicate, objects, contexts))

        return triplets


class VectorQuantizedCodebook:
    """Katman B: VQ Codebook, Graf Topolojisi ve Kalıcı Disk Depolama."""

    def __init__(self, seed_code: int = 8421):
        self._codebook: Dict[int, SemanticTriplet] = {}
        self._reverse_index: Dict[str, int] = {}
        self._seed_reference_codes()

    def _seed_reference_codes(self):
        """12 Temel Evrensel Bilim ve Mühendislik Alanı için Çekirdek Referans Senaryolar."""
        omni_scenarios = [
            # 1. Hardware / Embedded IoT
            (8421, SemanticTriplet(
                subject="Toprak",
                predicate="test_etti",
                objects=[TypedEntity("ESP32", EntityType.HARDWARE), TypedEntity("nRF24L01", EntityType.HARDWARE)],
                contexts=[TypedEntity("SPI", EntityType.PROTOCOL), TypedEntity("laboratuvar", EntityType.GENERIC)]
            )),
            # 2. Software & Cloud DevOps
            (8422, SemanticTriplet(
                subject="Geliştirici",
                predicate="deploy_etti",
                objects=[TypedEntity("Kubernetes", EntityType.SOFTWARE), TypedEntity("PostgreSQL", EntityType.SOFTWARE)],
                contexts=[TypedEntity("Docker", EntityType.SOFTWARE), TypedEntity("production", EntityType.GENERIC)]
            )),
            # 3. Cybersecurity & Red Teaming
            (8423, SemanticTriplet(
                subject="Analist",
                predicate="tespit_etti",
                objects=[TypedEntity("CVE-2024-1234", EntityType.VULN), TypedEntity("BufferOverflow", EntityType.VULN)],
                contexts=[TypedEntity("DMZ", EntityType.GENERIC), TypedEntity("Exploit", EntityType.SOFTWARE)]
            )),
            # 4. Quantum Computing
            (8424, SemanticTriplet(
                subject="Fizikçi",
                predicate="dolaşıklaştırdı",
                objects=[TypedEntity("Qubit", EntityType.QUANTUM), TypedEntity("BellState", EntityType.QUANTUM)],
                contexts=[TypedEntity("Kriyostat", EntityType.QUANTUM), TypedEntity("Qiskit", EntityType.QUANTUM)]
            )),
            # 5. Bio-Informatics & Genomics
            (8425, SemanticTriplet(
                subject="Genetikçi",
                predicate="modifiye_etti",
                objects=[TypedEntity("CRISPR", EntityType.BIO), TypedEntity("Exon", EntityType.BIO)],
                contexts=[TypedEntity("AlphaFold", EntityType.BIO), TypedEntity("hücre", EntityType.BIO)]
            )),
            # 6. Aerospace & Avionics
            (8426, SemanticTriplet(
                subject="Mühendis",
                predicate="kalibre_etti",
                objects=[TypedEntity("Telemetry", EntityType.AEROSPACE), TypedEntity("Gyroscope", EntityType.AEROSPACE)],
                contexts=[TypedEntity("yörünge", EntityType.AEROSPACE), TypedEntity("Uydu", EntityType.AEROSPACE)]
            )),
            # 7. Automotive & Autonomous Driving
            (8427, SemanticTriplet(
                subject="Sürücü_Yazılımı",
                predicate="denetledi",
                objects=[TypedEntity("ECU", EntityType.AUTOMOTIVE), TypedEntity("LiDAR", EntityType.AUTOMOTIVE)],
                contexts=[TypedEntity("CAN", EntityType.PROTOCOL), TypedEntity("otoyol", EntityType.AUTOMOTIVE)]
            )),
            # 8. Financial Algorithmic Trading
            (8428, SemanticTriplet(
                subject="AlgoTrader",
                predicate="arbitraj_yaptı",
                objects=[TypedEntity("OrderBook", EntityType.FINANCE), TypedEntity("Derivative", EntityType.FINANCE)],
                contexts=[TypedEntity("Borsa", EntityType.FINANCE), TypedEntity("NASDAQ", EntityType.FINANCE)]
            )),
            # 9. Robotics & Automation
            (8429, SemanticTriplet(
                subject="Kontrolcü",
                predicate="harekete_geçirdi",
                objects=[TypedEntity("Actuator", EntityType.ROBOTICS), TypedEntity("Manipulator", EntityType.ROBOTICS)],
                contexts=[TypedEntity("ROS", EntityType.SOFTWARE), TypedEntity("fabrika", EntityType.ROBOTICS)]
            )),
            # 10. Cryptography & Zero-Knowledge
            (8430, SemanticTriplet(
                subject="Kriptograf",
                predicate="doğruladı",
                objects=[TypedEntity("ZK-SNARK", EntityType.CRYPTO), TypedEntity("SHA-256", EntityType.CRYPTO)],
                contexts=[TypedEntity("TLS", EntityType.PROTOCOL), TypedEntity("Blockchain", EntityType.CRYPTO)]
            )),
            # 11. Artificial Intelligence & LLMs
            (8431, SemanticTriplet(
                subject="Araştırmacı",
                predicate="fine_tune_etti",
                objects=[TypedEntity("Transformer", EntityType.SOFTWARE), TypedEntity("Weights", EntityType.SOFTWARE)],
                contexts=[TypedEntity("LoRA", EntityType.SOFTWARE), TypedEntity("GPU_Cluster", EntityType.HARDWARE)]
            )),
            # 12. Universal Science & Human Cognition
            (8432, SemanticTriplet(
                subject="İnsan",
                predicate="araştırdı",
                objects=[TypedEntity("Bilgi", EntityType.GENERIC), TypedEntity("Hipotez", EntityType.GENERIC)],
                contexts=[TypedEntity("Evren", EntityType.GENERIC), TypedEntity("Kütüphane", EntityType.GENERIC)]
            )),
        ]
        for code_id, triplet in omni_scenarios:
            self.register_triplet_with_code(code_id, triplet)

    def _compute_signature(self, triplet: SemanticTriplet) -> str:
        sorted_objs = sorted(o.to_tagged_string().lower() for o in triplet.objects)
        sorted_ctxs = sorted(c.to_tagged_string().lower() for c in triplet.contexts)
        obj_str = "+".join(sorted_objs)
        ctx_str = "|".join(sorted_ctxs)
        return f"{triplet.subject.lower()}::{triplet.predicate.lower()}::{obj_str}::{ctx_str}"

    def register_triplet(self, triplet: SemanticTriplet) -> int:
        sig = self._compute_signature(triplet)
        if sig in self._reverse_index:
            return self._reverse_index[sig]

        h = hashlib.sha256(sig.encode("utf-8")).hexdigest()
        code_id = (int(h[:6], 16) % 80000) + 1000

        while code_id in self._codebook and self._compute_signature(self._codebook[code_id]) != sig:
            code_id += 1

        self._codebook[code_id] = triplet
        self._reverse_index[sig] = code_id
        return code_id

    def register_triplet_with_code(self, code_id: int, triplet: SemanticTriplet):
        sig = self._compute_signature(triplet)
        self._codebook[code_id] = triplet
        self._reverse_index[sig] = code_id

    def lookup(self, code_id: int) -> Optional[SemanticTriplet]:
        return self._codebook.get(code_id)

    def size(self) -> int:
        return len(self._codebook)

    @property
    def codes(self) -> Dict[int, Dict[str, Any]]:
        """Sözlükteki tüm kodları metadata sözlüğü olarak döndürür."""
        result = {}
        for cid, trip in self._codebook.items():
            primary_dom = "GENERIC"
            if trip.objects:
                primary_dom = trip.objects[0].entity_type
            elif trip.contexts:
                primary_dom = trip.contexts[0].entity_type
            result[cid] = {
                "graph": trip.to_graph_string(),
                "compact_code": trip.to_compact_code(),
                "primary_domain": primary_dom,
                "triplet": trip
            }
        return result

    # -------------------------------------------------------------------------
    # ANLAMSAL GRAF ARAMA (Semantic Search across Knowledge Graph)
    # -------------------------------------------------------------------------
    def query_graph(
        self,
        entity: Optional[str] = None,
        predicate: Optional[str] = None,
        context: Optional[str] = None,
        text_query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Hafıza sözlüğünde kayıtlı çizgeleri varlık, eylem veya bağlam bazında filtreler."""
        results = []
        term = text_query.lower().strip() if text_query else None

        for code_id, trip in self._codebook.items():
            matched = True

            if entity:
                ent_low = entity.lower()
                subj_match = ent_low in trip.subject.lower()
                obj_match = any(ent_low in o.name.lower() for o in trip.objects)
                if not (subj_match or obj_match):
                    matched = False

            if predicate and matched:
                if predicate.lower() not in trip.predicate.lower():
                    matched = False

            if context and matched:
                ctx_low = context.lower()
                if not any(ctx_low in c.name.lower() for c in trip.contexts):
                    matched = False

            if term and matched:
                full_str = f"{trip.subject} {trip.predicate} {' '.join(o.name for o in trip.objects)} {' '.join(c.name for c in trip.contexts)}".lower()
                if term not in full_str:
                    matched = False

            if matched:
                results.append({
                    "code_id": code_id,
                    "virtual_token": f"<|tzero:mem:{code_id}|>",
                    "triplet": trip.to_dict(),
                    "graph_string": trip.to_graph_string(),
                    "compact_code": trip.to_compact_code()
                })

        return results

    # -------------------------------------------------------------------------
    # GRAF TOPOLOJİSİ (Graph Topology for Visual HUD)
    # -------------------------------------------------------------------------
    def get_topology(self) -> Dict[str, Any]:
        """Tüm hafıza çizgelerinden düğüm (Node) ve kenar (Edge) listesi çıkarır."""
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []

        for code_id, trip in self._codebook.items():
            # Subject Node
            if trip.subject not in nodes:
                nodes[trip.subject] = {"id": trip.subject, "label": trip.subject, "type": "SUBJECT"}

            # Objects & Contexts
            for o in trip.objects:
                if o.name not in nodes:
                    nodes[o.name] = {"id": o.name, "label": o.name, "type": o.entity_type}
                edges.append({
                    "from": trip.subject,
                    "to": o.name,
                    "predicate": trip.predicate,
                    "code_id": code_id
                })

            for c in trip.contexts:
                if c.name not in nodes:
                    nodes[c.name] = {"id": c.name, "label": c.name, "type": c.entity_type}
                edges.append({
                    "from": trip.subject,
                    "to": c.name,
                    "predicate": f"in_{c.name}",
                    "code_id": code_id
                })

        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "nodes": list(nodes.values()),
            "edges": edges
        }

    # -------------------------------------------------------------------------
    # KALICI DİSK DEPOLAMA (Persistent Memory Store)
    # -------------------------------------------------------------------------
    def save_to_disk(self, filepath: Optional[str] = None) -> str:
        """Kayıtlı hafızayı diske JSON olarak serialize eder."""
        target = filepath or os.path.join(os.path.dirname(__file__), "tzero_memory_store.json")
        data = {
            "version": "4.3.0",
            "codes": {
                str(code_id): trip.to_dict()
                for code_id, trip in self._codebook.items()
            }
        }
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return target

    def load_from_disk(self, filepath: Optional[str] = None) -> int:
        """Diskteki kayıtlı hafızayı bellek sözlüğüne yükler."""
        target = filepath or os.path.join(os.path.dirname(__file__), "tzero_memory_store.json")
        if not os.path.exists(target):
            return 0

        with open(target, "r", encoding="utf-8") as f:
            data = json.load(f)

        loaded_count = 0
        for code_str, tdict in data.get("codes", {}).items():
            code_id = int(code_str)
            objs = [TypedEntity(o["name"], o["entity_type"]) for o in tdict.get("objects", [])]
            ctxs = [TypedEntity(c["name"], c["entity_type"]) for c in tdict.get("contexts", [])]
            trip = SemanticTriplet(tdict["subject"], tdict["predicate"], objs, ctxs)
            self.register_triplet_with_code(code_id, trip)
            loaded_count += 1

        return loaded_count


class DynamicVirtualMemoryInjector:
    """Katman C: Dinamik Çözücü & Soft-Prompt / Virtual KV-Cache Enjeksiyonu."""

    def __init__(self, codebook: Optional[VectorQuantizedCodebook] = None):
        self.codebook = codebook or VectorQuantizedCodebook()

    def compress_text_to_virtual_tokens(self, text: str) -> Dict[str, Any]:
        """Tekil veya kısa cümleleri 3 katmandan geçirir."""
        triplets = SemanticTripletExtractor.extract_triplets(text)
        raw_words = text.split()
        original_token_count = max(1, int(len(raw_words) * 1.3))

        code_ids = []
        graph_strings = []
        compact_codes = []
        virtual_tokens = []

        for trip in triplets:
            code_id = self.codebook.register_triplet(trip)
            code_ids.append(code_id)
            graph_strings.append(trip.to_graph_string())
            compact_codes.append(trip.to_compact_code())
            virtual_tokens.append(f"<|tzero:mem:{code_id}|>")

        compressed_token_count = max(1, len(virtual_tokens))
        token_savings = max(0, original_token_count - compressed_token_count)
        reduction_ratio_pct = round((token_savings / original_token_count) * 100.0, 2)

        return {
            "original_text": text,
            "original_token_count": original_token_count,
            "triplets": [t.to_dict() for t in triplets],
            "graph_representations": graph_strings,
            "compact_codes": compact_codes,
            "codebook_ids": code_ids,
            "virtual_tokens": virtual_tokens,
            "virtual_token_string": " ".join(virtual_tokens),
            "compressed_token_count": compressed_token_count,
            "token_savings": token_savings,
            "reduction_ratio_pct": reduction_ratio_pct,
            "layer_breakdown": {
                "layer_a_semantic_triplets": graph_strings,
                "layer_b_vq_codes": [f"#{cid}" for cid in code_ids],
                "layer_c_virtual_injection": " ".join(virtual_tokens)
            }
        }

    # -------------------------------------------------------------------------
    # ÇOK PARAGRAFLI / DÖKÜMAN SIKIŞTIRMA (Hierarchical Document Compressor)
    # -------------------------------------------------------------------------
    def compress_document(self, doc_text: str) -> Dict[str, Any]:
        """
        Geniş teknik dokümanları, logları veya konuşma geçmişlerini (1000+ kelime)
        tam bir bilgi grafiğine ve kompozit sanal token zincirine dönüştürür.
        """
        paragraphs = [p.strip() for p in doc_text.split("\n\n") if p.strip()]
        all_triplets: List[SemanticTriplet] = []
        all_code_ids: List[int] = []
        all_virtual_tokens: List[str] = []
        all_graphs: List[str] = []

        raw_word_count = len(doc_text.split())
        original_token_count = max(1, int(raw_word_count * 1.3))

        for p in paragraphs:
            triplets = SemanticTripletExtractor.extract_triplets(p)
            for t in triplets:
                cid = self.codebook.register_triplet(t)
                all_triplets.append(t)
                all_code_ids.append(cid)
                all_virtual_tokens.append(f"<|tzero:mem:{cid}|>")
                all_graphs.append(t.to_graph_string())

        compressed_token_count = max(1, len(all_virtual_tokens))
        token_savings = max(0, original_token_count - compressed_token_count)
        reduction_ratio_pct = round((token_savings / original_token_count) * 100.0, 2) if original_token_count > 0 else 0.0

        return {
            "total_paragraphs": len(paragraphs),
            "total_triplets_extracted": len(all_triplets),
            "original_word_count": raw_word_count,
            "original_token_count": original_token_count,
            "compressed_token_count": compressed_token_count,
            "token_savings": token_savings,
            "reduction_ratio_pct": reduction_ratio_pct,
            "codebook_ids": all_code_ids,
            "virtual_token_string": " ".join(all_virtual_tokens),
            "graph_representations": all_graphs,
            "topology": self.codebook.get_topology()
        }

    def decode_virtual_token(self, token_or_code: Union[str, int]) -> Optional[Dict[str, Any]]:
        code_id = None
        if isinstance(token_or_code, int):
            code_id = token_or_code
        elif isinstance(token_or_code, str):
            m = re.search(r"(\d+)", token_or_code)
            if m:
                code_id = int(m.group(1))

        if code_id is None:
            return None

        triplet = self.codebook.lookup(code_id)
        if not triplet:
            return None

        obj_str = " + ".join(o.name for o in triplet.objects)
        ctx_str = " | ".join(c.name for c in triplet.contexts)
        reconstructed = f"{triplet.subject}, {obj_str} hedefini {ctx_str} ortamında {triplet.predicate}." if ctx_str else f"{triplet.subject}, {obj_str} hedefini {triplet.predicate}."

        return {
            "code_id": code_id,
            "virtual_token": f"<|tzero:mem:{code_id}|>",
            "graph_representation": triplet.to_graph_string(),
            "compact_code": triplet.to_compact_code(),
            "triplet": triplet.to_dict(),
            "reconstructed_summary": reconstructed
        }

    def query_memory(self, query: str) -> List[Dict[str, Any]]:
        """Hafıza sözlüğünde doğal dil veya varlık araması yapar."""
        return self.codebook.query_graph(text_query=query)

    def build_soft_prompt_prefix(self, virtual_tokens: List[str]) -> str:
        decoded_context = []
        for vt in virtual_tokens:
            info = self.decode_virtual_token(vt)
            if info:
                decoded_context.append(f"• {info['virtual_token']} => {info['compact_code']} ({info['graph_representation']})")

        return (
            "[T-ZERO HIGH-DENSITY VIRTUAL MEMORY STATE]\n"
            + "\n".join(decoded_context)
            + "\n[ATTENTION PRIMING COMPLETE - ZERO TOKEN OVERHEAD]\n"
        )

    # Kolaylık ve Uyumluluk Alias Metotları
    compress_text = compress_text_to_virtual_tokens
    decompress_code = decode_virtual_token

    def compress_statement(self, text: str) -> Dict[str, Any]:
        """Tekil bir cümleyi hızlıca sanal bellek tokenına dönüştürür."""
        res = self.compress_text_to_virtual_tokens(text)
        vt = res["virtual_tokens"][0] if res["virtual_tokens"] else "<|tzero:mem:0|>"
        return {
            "triplets": res["triplets"],
            "virtual_token": vt,
            "virtual_tokens": res["virtual_tokens"],
            "codebook_ids": res["codebook_ids"]
        }


_global_compressor = DynamicVirtualMemoryInjector()

def get_global_compressor() -> DynamicVirtualMemoryInjector:
    return _global_compressor

# Uyumluluk Aliası
SemanticExtractor = SemanticTripletExtractor
