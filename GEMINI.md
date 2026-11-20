# TZeroAlgorithm - Antigravity Workspace Guide

Hoş geldiniz! Bu proje **T-Zero (Token Zero)** kurumsal seviye context mühendisliği, AST kod sıkıştırma ve sıfır-sızıntı (Zero-Leak) güvenlik motorudur.

---

## 📱 Uzaktan Erişim (Antigravity Remote / Telefon & Web)

Bu proje Google Antigravity için resmi workspace olarak yapılandırılmıştır:
- **Web / Telefon Bağlantı Adresi:** [https://antigravity.google.com](https://antigravity.google.com)
- **Hesap:** `siberakademi@org.tr` (Authorized Account)
- **Uzak Cihaz / Instance:** `toprak-zero-vertex`
- **Workspace:** `TZeroAlgorithm`
- **Daemon Durumu:** `agy --remote-control status` veya `agy remote-control status`

Telefonunuzdan veya herhangi bir tarayıcıdan `https://antigravity.google.com` adresine girdiğinizde doğrudan `toprak-zero-vertex` makinesini ve bu `TZeroAlgorithm` workspace'ini seçerek sohbet edebilir, kod yazabilir, testleri çalıştırabilir ve düzenlemeleri canlı olarak uygulayabilirsiniz.

---

## 🛠 Temel Komutlar ve Testler

- **Tüm Testleri Çalıştırma (628 Test, 100% Pass):**
  ```powershell
  python -m unittest discover tests -v
  ```
- **CLI Çalıştırma:**
  ```powershell
  tzero --help
  python tzero_v3.py --tree . --out tree.txt
  tzero share
  ```
- **Yapay Zeka ve Ajanlar İçin Proje İnceleme Rehberi:**
  - [AI_INSPECTION.md](file:///c:/Users/topra_n3vq63d/.gemini/antigravity-ide/scratch/TZeroAlgorithm/AI_INSPECTION.md)
  - [llms.txt](file:///c:/Users/topra_n3vq63d/.gemini/antigravity-ide/scratch/TZeroAlgorithm/llms.txt)
- **Masaüstü Arayüzü (GUI):**
  ```powershell
  tzero-gui
  ```
- **Web Karşılaştırma / Benchmark Sitesi:**
  ```powershell
  python benchmark-site\serve.py
  # http://localhost:8000
  ```
- **MCP Sunucusu:**
  - Dağıtım: `dist\TZeroMCP.exe`
  - Kaynak: `tzero_mcp.py`
  - Test: `python -m unittest tests.test_mcp`

---

## 🔒 Güvenlik ve Kurallar

1. **%100 Ücretsiz:** Hiçbir harici ücretli API kullanılmaz; tüm AST, BM25 ve token hesaplama araçları yerel/çevrimdışı çalışır.
2. **Sıfır-Sızıntı (Zero-Leak):** Gizli anahtarlar, tokenlar veya kimlik bilgileri commit edilmez veya dışarı sızdırılmaz.
3. **CI/CD:** GitHub Actions testleri 6 matrix ortamında (Windows & Ubuntu x Python 3.10, 3.11, 3.12) sürekli yeşil kalmalıdır.
