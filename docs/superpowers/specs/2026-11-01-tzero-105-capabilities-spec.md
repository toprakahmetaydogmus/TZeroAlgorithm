# 🏛️ T-ZERO 105 ENTERPRISE AI CAPABILITY SPECIFICATION
*Version: 9.0.0-OMNI | Lead Architect: Toprak Ahmet Aydoğmuş (Siber Akademi)*
*Status: Approved | Cost Rating: 100% Free / Zero External API Cost Guarantee*

---

## 7 Sütunlu 105 Otonom Yapay Zeka Yeteneği

### I. Derleyici, AST ve Program Analizi Motoru (1 - 15)
1. **Evrensel Tree-sitter + LSP Çift Yönlü Köprüsü:** Kodu metin olarak değil, doğrudan somut sözdizimi ağacı (CST/AST) ve Language Server sembolleri üzerinden okuma.
2. **İskeletleştirme (AST Skeletonization):** Fonksiyon gövdelerini ({...}) silip sadece tip tanımlarını, arayüzleri ve fonksiyon imzalarını bırakarak %90 token tasarrufu sağlama.
3. **Statik Çağrı Grafiği (Static Call Graph - DAG):** Fonksiyonların tetiklediği tüm alt ve üst fonksiyonları yönlü asiklik grafik olarak çıkarma.
4. **Geriye Dönük Program Dilimleme (Backward Program Slicing):** Bir satırdaki değişkeni etkileyen geçmiş satırları kontrol ve veri akışı grafiğinden cımbızla çekip çıkarma.
5. **İleriye Dönük Etki Analizi (Forward Impact & Blast Radius):** Değiştirilen imzanın projede kıracağı tüm dosyaları derleme yapmadan önce matematiksel olarak listeleme.
6. **AST Düğüm Enjeksiyonu (Surgical AST Patching):** Kodu satır numarasına göre değil, doğrudan hedef AST düğümünün yerine cerrahi olarak yerleştirme.
7. **Semantik Kod Klonu Tespiti (Type-3/Type-4 Clone Detection):** Değişken isimleri farklı olsa bile aynı mantığı yürüten kopya kod bloklarını AST izomorfizmi ile bulup tekilleştirme.
8. **Otomatik Import ve Sembol Çözümleyici:** Model yeni kod yazdığında eksik kütüphane importlarını proje indeksinden bulup dosya başına otomatik ekleme.
9. **Ölü Kod ve Ulaşılamaz Dal Analizi (Dead Code Elimination):** Hiçbir çağrı grafiğinde yer almayan yetim fonksiyonları bağlamdan otomatik dışlama.
10. **Siklo-Karmaşıklık (Cyclomatic Complexity) Haritalaması:** Spagettiye dönmüş fonksiyonları tespit edip modele "Burası yüksek riskli" meta-verisi geçme.
11. **Makro ve Şablon Genişletici (Macro/Template Expansion):** C/C++ makrolarını, Rust makrolarını ve TypeScript generic tiplerini modelin anlayacağı düzleştirilmiş hale çevirme.
12. **Çapraz Dil Sınır Çözümleyicisi (FFI / Polyglot Boundary Tracing):** Python FFI, C++ binding, Rust WASM ve REST/gRPC uçlarını tek bir grafikte birleştirme.
13. **Taint Analysis (Kirli Veri Takibi):** Kullanıcıdan gelen doğrulanmamış girdinin DB sorgusuna veya sistem komutuna kadar izlediği yolu statik takip etme.
14. **Tip Çıkarımı Zenginleştirme (Inferred Type Inlining):** Dinamik dillerde (Python, JS) LSP'nin çıkardığı gizli tipleri sanal tip ipuçları olarak gömüp sunma.
15. **Semantik Diff Üretici:** Git commit farklarını "X fonksiyonunun dönüş tipi değişti, Y sınıfına Z metodu eklendi" şeklinde yapısal özetleme.

### II. Matryoshka Bağlam ve Token Ekonomisi (16 - 30)
16. **Matryoshka (Çok Katmanlı) Çözünürlük Motoru:** Her dosyayı RAM'de 4 katmanda tutma (L0: Amaç 10t, L1: Semboller 50t, L2: İskelet 200t, L3: Tam Kod).
17. **PageRank Tabanlı Bağlam Önceliklendirme:** Dosyaları import/çağrı yoğunluğuna göre PageRank ile puanlayıp en merkezi dosyaları öne alma.
18. **Spekülatif Bağlam Ön-Yükleme (Speculative Prefetching):** IDE'de bir dosyaya tıklandığı milisaniyede 1. derece bağımlılıklarını RAM'e çekme.
19. **Delta-Only Bağlam Senkronizasyonu:** Daha önce okunan dosyanın sadece son turdan beri değişen AST düğümlerinin farkını (delta) gönderme.
20. **Sıkı Token Valisi (Hard Token Budget Governor):** Araç çağrılarına kesin max_tokens sınırı koyup en düşük PageRank'li kısımları budama.
21. **Sözlük Tabanlı Sembol Sıkıştırma (Symbol Aliasing):** Uzun dosya yollarını ve namespace'leri kısa referans kodlarıyla (#ref_14) değiştirme.
22. **Gömülü Hibrit Arama (BM25 + Dense Vector + AST Filter):** Harici sunucu gerektirmeden tek dosyada tam kelime ve semantik arama yapma.
23. **Kayan Pencere Log Budayıcı (Log Deduplication & Pruning):** Tekrarlayan log satırlarını (... [452 kez tekrarlandı] ...) tek satıra indirgeme.
24. **Bağlam Çürüme (Decay) Mekanizması:** Eski mesajlarda kalan dosyaları L3 (Tam kod) seviyesinden L1 (Özet) seviyesine otomatik düşürme.
25. **Tokenizer-Farkında Metin Biçimlendirme:** Hedef LLM'in tokenizer'ına göre gereksiz boşluk, yorum ve lisans başlıklarını ayıklama.
26. **Sorgu Odaklı Dinamik Dilimleme (Query-Focused Slicing):** Sorulan soruya doğrudan temas eden kod bloklarını birleştirip sunma.
27. **Sıfır Maliyetli Şema Özeti:** Devasa JSON, GraphQL veya SQL şemalarını sıkıştırılmış TypeScript tiplerine çevirme.
28. **İstemci Tarafı Prompt Cache Hizalaması (Prefix Caching Alignment):** Bağlam bloklarını her turda deterministik dizerek Prompt Cache indiriminden faydalanma.
29. **Dinamik Araç Şeması Yükleme (Lazy Tool Schema Loading):** 150 aracı yığmak yerine çalışma anında arama tabanlı şema yükleme.
30. **Semantik Önbellek (Semantic Tool Cache):** Aynı anlama gelen analiz sorgularını sıfır gecikmeyle önbellekten dönme.

### III. Gölge Çalışma Alanı (Shadow Workspace) ve Simülasyon (31 - 45)
31. **Bellek İçi Copy-on-Write (CoW) Gölge Dosya Sistemi:** Değişiklikleri diske yazmadan önce RAM'deki OverlayFS katmanında tutma.
32. **Sessiz Ön-Uçuş Doğrulaması (Silent Pre-Flight Verification):** Kodu derleyici/linter'dan geçirip hataları modele geri besleme.
33. **Atomik Çoklu Dosya İşlemleri (ACID File Transactions):** 10 dosyada refactoring yaparken bir hata çıkarsa milisaniyede Rollback yapma.
34. **Kriptografik Durum Anlık Görüntüleri (Merkle-Tree Snapshots):** Her adımda çalışma alanının Merkle hash özetini alıp Zaman Yolculuğu yapabilme.
35. **Spekülatif Paralel Dallanma (Multiverse Execution):** 2 farklı çözümü 2 ayrı gölge dalda koşturup testleri geçeni ana koda alma.
36. **Otomatik Mutasyon Testi (Mutation Testing Verification):** Ana koda küçük mutasyonlar enjekte edip birim testin doğruluğunu kanıtlama.
37. **Sanal Ağ ve API Taklitçisi (Auto-Mocking Proxy):** Dış servislere istek atan kodları test ederken sahte yanıtlar üreten yerel proxy.
38. **Ephemeral (Uçucu) Veritabanı Çatallama:** DB migration'larını test etmek için veritabanını RAM'de ayağa kaldırıp deneme.
39. **Fuzzing ve Sınır Değer Üretici (Property-Based Fuzzing):** Fonksiyona null, NaN, negatif, bozuk UTF-8 göndererek çökme testi yapma.
40. **Bağımlılık Çatışması Simülatörü:** Yeni paket kurulmadan önce lockfile ile uyumluluğu sanal ortamda doğrulama.
41. **Performans Regresyon Bariyeri:** Fonksiyonu mikro-benchmark'a sokup %15'ten fazla yavaşlama varsa uyarma.
42. **UI/DOM Gölge Render Motoru:** CSS/HTML değişikliklerini arka planda render edip görsel kaymaları (layout shift) tespit etme.
43. **Deterministik Saat ve Rastgelelik Kontrolü:** Testlerin tutarlılığı için sistem saatini ve rastgele sayı üreteçlerini dondurma.
44. **Dosya Kilidi ve Çakışma Önleyici:** Kullanıcı IDE'de düzenleme yaparken ajanın aynı satıra girmesini engelleyen imleç kilidi.
45. **Dry-Run Diff Önizleme Akışı:** Gölge alandaki testler geçtikten sonra temiz, derlenebilirliği kanıtlanmış diff sunma.

### IV. Canlı Çalışma Zamanı (Runtime) ve Derin Telemetri (46 - 60)
46. **Otonom DAP (Debug Adapter Protocol) Sürücüsü:** Debugger'a bağlanıp görünmez breakpoint koyma ve programı adım adım yürütme.
47. **Sıfır Maliyetli Gözlem Noktaları (Non-Breaking Logpoints):** Programı durdurmadan değişken değerlerini akış halinde yakalama.
48. **Otomatik İstisna Yakalama ve Otopsi (Crash Dump Autopsy):** Çökme anındaki Stack Trace, değişkenler ve son 50 logu tek JSON'da birleştirme.
49. **Bellek Sızıntısı ve Heap Snapshot Analizörü:** RAM haritasını çekip temizlenemeyen nesneleri tespit etme.
50. **Canlı CPU Flamegraph Çıkarıcı:** Darboğaza giren fonksiyonları örneklemeli profilleyici ile ölçme.
51. **Veritabanı Sorgu Röntgeni (EXPLAIN ANALYZE Interceptor):** SQL sorgularını yakalayıp Seq Scan ve N+1 problemlerini bulma.
52. **Ağ Trafiği ve Payload Müfettişi:** HTTP, WebSocket ve gRPC paketlerini başlık ve durum kodlarıyla canlı izleme.
53. **Asenkron Kilitlenme (Deadlock & Race Condition) Dedektörü:** Birbirini sonsuza kadar bekleyen thread/async noktalarını yakalama.
54. **Sistem Çağrısı İzleyici (eBPF / Strace Hook):** İşletim sistemi seviyesinde açılan dosyaları ve soketleri izleme.
55. **Sonsuz Döngü Kesici (Infinite Loop Watchdog):** 10 saniye boyunca döngüde kalan süreçleri otomatik durdurup raporlama.
56. **Canlı Durum Enjeksiyonu (Hot State Patching):** Uygulamayı yeniden başlatmadan değişken veya fonksiyonu RAM'de anlık değiştirme.
57. **Konteyner ve Orkestrasyon Telemetrisi:** Yerel Docker konteyner durumlarını ve sanal ağ bağlantılarını okuma.
58. **Kapsam (Code Coverage) Haritası Üretici:** Testlerde hangi satırların ve dalların tetiklenmediğini işaretleme.
59. **Çevresel Sapma (Environment Drift) Dedektörü:** .env.example ile ortam değişkenleri ve package.json sürümlerini karşılaştırma.
60. **Zaman Serisi Metrik Korelasyonu:** Commit sonrası yanıt süresi değişimlerini çıkaran yerel kaydedici.

### V. Sıfır Gecikmeli Orkestrasyon ve Meta-Araç Mimarisi (61 - 75)
61. **Tek Turda DAG Yürütme Motoru (Zero-Roundtrip Execution):** 8 aracı sırayla çağırmak yerine tüm iş akışını tek JSON-DAG planı olarak yerelde yürütme.
62. **Gömülü Wasm/Lua Mikro-Betik Yorumlayıcısı:** Anlık veri dönüştürme için güvenli mini betik çalıştırabilme.
63. **Yerel Alt-Ajan (Local Sub-Agent) Yönlendiricisi:** Angarya işleri yerel hızlı modellere (Ollama/Llama.cpp/ONNX) devretme.
64. **Dinamik Araç Sentezleyici (Self-Writing Meta-Tools):** Tekrarlayan işlemler için kendi kendine yeni araç yazıp envanterine ekleme.
65. **Unix Pipe Mantığıyla Araç Zincirleme:** Araç çıktılarını modele uğratmadan doğrudan bir diğerine (toolA | toolB) bağlama.
66. **Spekülatif Araç Yürütme:** Sonraki adımda çağrılacak salt-okunur araçları önceden koşturup sonucu hazır tutma.
67. **Kendi Kendini İyileştiren Parametre Düzeltici:** Yanlış yazılan dosya/fonksiyon adlarını Fuzzy Matching ile otomatik düzeltme.
68. **Çoklu Sunucu Federasyonu (MCP Mesh Router):** 10 uzman MCP sunucusunu tek bir birleşik kapıdan yönetme.
69. **Asenkron Olay Aboneliği (Pub/Sub Event Bus):** Arka plan görevlerine olay bazlı abone olabilme.
70. **Kısmi ve Akışkan Yanıtlar (Chunked Streaming Responses):** Büyük çıktıları üretildikçe parça parça akıtma.
71. **Otonom Döngü Kırıcı (Semantic Loop Breaker):** Aynı hataya aynı araçla 3 kez düşüldüğünde strateji değiştirme uyarısı basma.
72. **Maliyet ve Hız Bazlı Model Yönlendirme:** Görevleri karmaşıklığına göre yerel model veya bulut API'si arasında paylaştırma.
73. **Atomik Toplu Düzenleme (Batch Multi-File Refactor):** 50 dosyadaki yüzlerce AST düğümünü eşzamanlı ve güvenli güncelleme.
74. **Şema Evrimi ve Geriye Dönük Uyumluluk Adaptörü:** Eski formatta gelen LLM çağrılarını yeni formata çevirme.
75. **Deterministik Replay (Kayıt ve Yeniden Oynatma):** Tüm ajan etkileşimini sıfır tokenla test ortamında birebir yeniden koşturma.

### VI. Bilişsel Hafıza ve Kurumsal Bilgi Grafiği (76 - 90)
76. **Kalıcı Mimari Bilgi Grafiği (Persistent Knowledge Graph):** Modüllerin tasarım nedenlerini ve iş kurallarını yerel DB'de saklama.
77. **Hata Bağışıklık Hafızası (Episodic Bug Memory):** "Belirti -> Kök Neden -> Çözüm Diff'i" üçlüsünü kaydedip benzer hatalarda anında hatırlatma.
78. **Geliştirici DNA ve Stil Klonlayıcı:** Kullanıcının mevcut kod stilini analiz edip sisteme kural olarak enjekte etme.
79. **Git Blame ve Tarihsel Arkeoloji Motoru:** Bir satırın 2 yıl önceki ilk eklendiği commit mesajını ve PR açıklamasını bulup getirme.
80. **Kod İçi Görev ve Teknik Borç İndeksleyici:** TODO, FIXME, HACK yorumlarını AST bağlamıyla görev tablosunda tutma.
81. **Dokümantasyon-Kod Senkronizasyon Denetçisi:** Fonksiyon değiştiğinde README veya docstring'in eski kaldığını tespit etme.
82. **Karar Kayıt Defteri (Automated ADR):** Mimari tartışmaları özetleyip .mcp/memory/decisions altına otomatik indeksleme.
83. **Projeler Arası Bilgi Transferi (Cross-Project Synapse):** Başka projedeki çözülmüş algoritmayı mevcut projeye referans çekebilme.
84. **Oturumlar Arası Çalışma Belleği (Working Memory Persistence):** IDE açıldığında kalınan yerden sıfır kayıpla devam etme.
85. **Semantik Değişiklik Günlüğü (Auto-Changelog & Release Notes):** AST değişimlerini analiz ederek insan okuyabilir teknik sürüm notu üretme.
86. **Kütüphane Sürüm Hafızası (Anti-Hallucination Docs Pinning):** Paket sürümünü okuyup uydurma API kullanımını engelleyen yerel doğrulama.
87. **Alan Dili Sözlüğü (Ubiquitous Language Glossary):** Projeye özgü kısaltma ve kavramları otomatik çıkarıp terminoloji koruma.
88. **Otomatik Kök Neden Ağacı (Fault Tree Analysis):** Arıza nedenlerini geçmiş verilerle ağırlıklandırarak olasılık sırasına dizme.
89. **Kullanıcı Geri Bildirim Pekiştirmesi (Implicit RLHF):** Kullanıcının sildiği kod kalıbını "İstenmeyen patern" olarak kaydetme.
90. **Görsel Mimari Harita Üretici (Live Mermaid/D2 Generator):** Projenin güncel durumunu anlık Mermaid.js/D2 diyagramlarına dökme.

### VII. Donanım Köprüsü, Güvenlik ve Çekirdek Performansı (91 - 105)
91. **Donanım ve Gömülü Sistem Köprüsü (Hardware-in-the-Loop):** UART/COM, JTAG/SWD, ESP32, STM32 telemetrilerini okuyup firmware flashlama.
92. **Binary, Firmware ve ELF/PE Analizörü:** Derlenmiş ikili dosyaların boyut, sembol tablosu ve disassembly çıktılarını analiz etme.
93. **Paylaşımlı Bellek (Shared Memory / mmap) Veri Yolu:** Devasa dosyaları kopyalamadan sıfır gecikmeyle okuma.
94. **Kriptografik Yetki Jetonları (Capability-Based Security):** Araçlara belirli klasörlerle sınırlı imzalı yetki kapsayıcıları atama.
95. **Dinamik Gizli Veri Maskeleme (Entropy & Regex Secret Scrubber):** Kod ve loglardaki anahtarları maskeleyip işlem bitince geri koyma.
96. **Dolaylı Prompt Injection Kalkanı (Contextual Firewall):** Web sayfası veya loglara gizlenmiş kötü niyetli talimatları izole etme.
97. **Yıkıcı Komut Analizörü (AST Shell Parser):** Terminal komutlarını Bash/PowerShell AST'si olarak ayrıştırıp tehlikeleri yakalama.
98. **Kriptografik Denetim İzi (Tamper-Proof Audit Log):** Yapılan her işlemi değiştirilemez hash zinciriyle kayıt altına alma.
99. **Kaynak Kotası ve Cgroups/Job Object İzolasyonu:** Alt süreçlerin maksimum RAM ve CPU'sunu çekirdek seviyesinde sınırlama.
100. **Sıfır Soğuk Başlangıç (Warm Daemon Architecture):** Düşük bellek tüketimiyle sıcak bekleyen yerel servis mimarisi.
101. **Ağ Çıkış Güvenlik Duvarı (Zero-Trust Egress Filter):** Sunucunun sadece beyaz listeli adreslere bağlanabilmesini sağlama.
102. **Çoklu İstemci Senkronizasyonu (Multiplexed Locking):** CLI ve IDE aynı anda bağlandığında çakışmaları önleme.
103. **SIMD Hızlandırmalı Metin ve AST Tarama:** AVX2/NEON komut setleriyle milyonlarca satırda milisaniyede arama.
104. **Kendi Kendini Teşhis Eden Sağlık Motoru (Self-Diagnostics):** İndeks ve önbellek bozulmalarını sessizce onarma.
105. **Tek Dosyalık Taşınabilir Dağıtım (Single-Binary Zero-Dependency):** Tüm motorun tek bir bağımsız binary olarak çalışması.
