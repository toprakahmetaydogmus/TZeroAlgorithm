# T-Zero Context Architect V3 — Geliştirme Rehberi (Walkthrough)

> Bu belge, T-Zero Context Architect V3 projesinin tüm geliştirme sürecini,
> mimari kararlarını ve teknik detaylarını kapsamlı şekilde anlatır.

**Geliştirici:** Toprak Ahmet Aydoğmuş  
**Ana Site:** [https://utspro.co](https://utspro.co)  
**Biyografi:** [https://hopp.bio/siberegitim](https://hopp.bio/siberegitim)

---

## 🏗 Mimari Genel Bakış

T-Zero V3, **tek dosya mimarisinde** (monolithic single-file) tasarlanmıştır. Bu yaklaşım:
- Çift tıkla çalıştırmayı kolaylaştırır
- Modül import hatalarını ortadan kaldırır  
- PyInstaller ile tek .exe çıktısı üretmeyi basitleştirir
- Deployment ve dağıtım sürecini minimalize eder

### Katmanlı Yapı (tzero_v3.py içinde)

```
┌────────────────────────────────────────┐
│ 1. CONFIGURATION LAYER                 │ → ConfigManager, Keyring, Profiller
├────────────────────────────────────────┤
│ 2. PROVIDERS INTEGRATION LAYER         │ → 6 AI Sağlayıcı adaptörü
├────────────────────────────────────────┤
│ 3. AST SCANNER & DEPENDENCY ANALYZER   │ → TokenReducer, CodebaseScanner
├────────────────────────────────────────┤
│ 4. STATIC CODE ANALYZER               │ → Code smell tespiti
├────────────────────────────────────────┤
│ 5. AST STRUCTURE & REFACTORER          │ → PythonASTParser, Refactorer
├────────────────────────────────────────┤
│ 6. KEYRING SECRETS EDITOR & BACKUP     │ → Şifreli yedekleme/geri yükleme
├────────────────────────────────────────┤
│ 7. WORKSPACE DUPLICITY FINDER          │ → Duplicate kod bloğu tespiti
├────────────────────────────────────────┤
│ 8. MARKDOWN TEXT TAGGER                │ → Zengin metin formatlama
├────────────────────────────────────────┤
│ 9. WORKSPACE PRESETS & PROFILE I/O     │ → Hazır filtre şablonları
├────────────────────────────────────────┤
│ 10. TEMPLATES & GENERATOR              │ → Prompt derleme ve API çağrısı
├────────────────────────────────────────┤
│ 11. GIT COMMIT GRAPH DRAWER            │ → Özel Canvas çizimi
├────────────────────────────────────────┤
│ 12. GUI COMPONENTS                     │ → GlassCard, StarfieldCanvas, Charts
├────────────────────────────────────────┤
│ 13. MAIN GUI DASHBOARD                 │ → 6 sekmeli tam arayüz
├────────────────────────────────────────┤
│ 14. CLI WIZARD & STARTUP               │ → Komut satırı modu
└────────────────────────────────────────┘
```

---

## 🎨 Tema Sistemi

3 önceden tanımlı tema paleti + özel renk seçici:

| Tema | Karakter |
|------|----------|
| **Glass Dark** | Modern, kurumsal, cam efekti |
| **Siber Retro** | Sıcak tonlar, retro hacker hissi |
| **Neon Cyberpunk** | Parlak neon, karanlık arka plan |

Her tema 11 renk değişkeni tanımlar: `bg_start`, `card_bg`, `card_border`, `card_hover`, `text_main`, `text_muted`, `accent_cyan`, `accent_green`, `accent_purple`, `success`, `error`.

---

## 🔐 Güvenlik Mimarisi

### Keyring Entegrasyonu
- API anahtarları `keyring` kütüphanesi ile OS-native credential store'da saklanır
- Windows: Windows Credential Manager
- macOS: Keychain
- Linux: Secret Service (GNOME Keyring / KDE Wallet)

### XOR Şifreli Yedekleme
- `KeyringSecretsBackupManager` sınıfı master anahtar ile XOR şifreleme yapar
- Yedek dosya `.dat` uzantılı binary olarak kaydedilir
- Geri yükleme aynı master anahtar ile yapılır

### Dosya İzinleri
- POSIX sistemlerde yapılandırma dosyaları `0o600` iznine sahiptir
- Yedek dosyalar da aynı izin korumasına tabidir

---

## 📊 Token Yönetimi

### TokenReducer Stratejileri

| Mod | Açıklama |
|-----|----------|
| **Ultra** | Sadece fonksiyon/sınıf imzaları, import'lar |
| **Balanced** | İmzalar + basit gövde satırları |
| **None** | Tam kaynak kod |

### Dil Desteği
- **Python**: AST tabanlı docstring filtreleme, import/def/class çıkarımı
- **JavaScript/TypeScript**: Export, function, class, const/let çıkarımı  
- **C/C++/Go/Rust**: Include/package, fonksiyon imzası çıkarımı
- **Diğer**: İlk 60 boş olmayan satır

---

## 🛠 Geliştirme Süreci

### Aşama 1: Temel Altyapı
- ConfigManager sınıfı (profil CRUD, JSON persistance)
- Keyring güvenli anahtar yönetimi
- 6 AI sağlayıcı adaptörü (Provider pattern)

### Aşama 2: Kod Tarama Motoru  
- Multi-threaded CodebaseScanner
- AST tabanlı TokenReducer
- Dosya filtreleme (uzantı + klasör ignore)

### Aşama 3: GUI Arayüzü
- StarfieldCanvas animasyonlu arka plan
- GlassCard cam efekti bileşenleri
- 6 sekmeli tab navigasyonu
- Pygments syntax highlighting editör

### Aşama 4: İleri Özellikler
- StaticCodeAnalyzer (code smell tespiti)
- WorkspaceDuplicityFinder (kopya kod bulucu)
- PythonASTRefactorer (AST transformer)
- GitCommitGraphCanvas (özel commit grafiği)
- AdvancedTokenDistributionChart (dil dağılımı)

### Aşama 5: Paketleme
- install_requirements.bat (Python auto-install dahil)
- build_exe.bat (PyInstaller tek dosya .exe)
- Siber Akademi branded icon

---

## 📈 Proje İstatistikleri

| Metrik | Değer |
|--------|-------|
| **Ana dosya satır sayısı** | 3862 |
| **Toplam Python sınıfı** | 30+ |
| **AI sağlayıcı adaptörü** | 6 |
| **GUI sekmesi** | 6 |
| **Tema paleti** | 3 + özel |
| **Dil desteği** | TR / EN |
| **Canvas widget** | 7 (Starfield, Node, Perf, Donut, Lang, Git, Matrix) |

---

## ✅ Test Kontrol Listesi

- [x] Uygulama hatasız başlatılıyor
- [x] Tema değişimi çalışıyor
- [x] TR/EN dil geçişi çalışıyor
- [x] Dizin tarama çalışıyor
- [x] Dosya seçici ağaç yapısı oluşuyor
- [x] Kod editörü syntax highlighting yapıyor
- [x] Git log çekme çalışıyor
- [x] Git diff görüntüleme çalışıyor
- [x] Offline dry-run context oluşturuyor
- [x] Profil oluşturma/silme/değiştirme çalışıyor
- [x] Keyring yönetimi çalışıyor
- [x] Klavye kısayolları çalışıyor

---

> **SİBER AKADEMİ** — T-Zero Context Architect V3  
> © 2024-2026 Toprak Ahmet Aydoğmuş | [utspro.co](https://utspro.co)
