# T-Zero Algoritması - Türkçe Dokümantasyon

[English](../README.md) | **[Türkçe](README.tr.md)** | [日本語](README.ja.md) | [简体中文](README.zh.md) | [Gizlilik Politikası (Privacy)](../PRIVACY.md) | [Google Colab Canlı Lab](https://colab.research.google.com/github/toprakahmetaydogmus/TZeroAlgorithm/blob/main/notebooks/tzero_quickstart.ipynb) | [Hugging Face Canlı Demo](https://huggingface.co/spaces/toprakke4/tzero-token-reducer) | [Tarayıcıda Doğrudan Aç (GitHub Codespaces)](https://codespaces.new/toprakahmetaydogmus/TZeroAlgorithm)

<div align="center">

<!-- Rozetler 1. Kademe: Dağıtım, Sürüm ve Ölçek -->
[![GitHub Sürüm](https://img.shields.io/github/v/release/toprakahmetaydogmus/TZeroAlgorithm?style=flat-square&logo=github&color=38bdf8)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases)
[![PyPI](https://img.shields.io/badge/pypi-v12.2.0-3b82f6?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/tzero-mcp/)
[![npm](https://img.shields.io/badge/npm-v12.2.0-cb3837?style=flat-square&logo=npm)](https://www.npmjs.com/package/tzero-mcp)
[![VS Code](https://img.shields.io/badge/vscode-v12.2.0-007acc?style=flat-square&logo=visualstudiocode&logoColor=white)](https://marketplace.visualstudio.com/items?itemName=siber-akademi.tzero-vscode)
[![Open VSX](https://img.shields.io/badge/open--vsx-v12.2.0-8b5cf6?style=flat-square&logo=openvsx&logoColor=white)](https://open-vsx.org/extension/siber-akademi/tzero-vscode)
[![İndirmeler](https://img.shields.io/badge/downloads-20%2C880%2B-10b981?style=flat-square&logo=git)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases)
[![Yıldızlar](https://img.shields.io/github/stars/toprakahmetaydogmus/TZeroAlgorithm?style=flat-square&logo=github&color=f59e0b)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/stargazers)

<!-- Rozetler 2. Kademe: Mühendislik Kalitesi, Güvenlik, Testler ve Yönetişim -->
[![Motor](https://img.shields.io/badge/motor-Rust%20%2B%20Python%20AST-orange?style=flat-square&logo=rust&logoColor=white)](../README.md#whats-new-in-v1200-turbo-rust-hybrid-core--multi-language-tree-sitter)
[![Güvenlik](https://img.shields.io/badge/g%C3%BCvenlik-%25100%20S%C4%B1f%C4%B1r--S%C4%B1z%C4%B1nt%C4%B1-emerald?style=flat-square&logo=shield)](../README.md#security-architecture)
[![CI](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/actions/workflows/ci.yml/badge.svg)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/actions/workflows/ci.yml)
[![TDQS](https://img.shields.io/badge/TDQS-5.0%20%2F%205.0%20(Derece%20A%2B)-8b5cf6?style=flat-square&logo=checkmarx&logoColor=white)](https://glama.ai/mcp/servers/toprakahmetaydogmus/TZeroAlgorithm/schema)
[![CodeQL Analizi](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/actions/workflows/codeql.yml/badge.svg)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/actions/workflows/codeql.yml)
[![Dependabot](https://img.shields.io/badge/dependabot-aktif-02569B?style=flat-square&logo=dependabot&logoColor=white)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/blob/main/.github/dependabot.yml)
[![Lisans](https://img.shields.io/badge/lisans-AGPL--3.0-64748b?style=flat-square)](../LICENSE)
<!-- m8ven.ai/badge/mcp/toprakahmetaydogmus/tzeroalgorithm -->

<br>

### 500 Yıldız Yolculuğu: T-Zero'yu %100 Ücretsiz ve Açık Kaynak Tutmamıza Destek Olun!
*Cursor, Claude Code, Windsurf ve Antigravity IDE için ampirik olarak kanıtlanmış deterministik AST token sıkıştırma motoru.*

[![GitHub'da Yıldızla](https://img.shields.io/badge/%E2%AD%90%20GitHub'da%20Y%C4%B1ld%C4%B1zla-Hedef%3A%20500-f59e0b?style=for-the-badge&logo=github&logoColor=white)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm)
[![Google Colab Canlı Lab](https://img.shields.io/badge/%F0%9F%9A%80%20%C4%B0nteraktif-Google%20Colab-f9ab00?style=for-the-badge&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/toprakahmetaydogmus/TZeroAlgorithm/blob/main/notebooks/tzero_quickstart.ipynb)
[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Zero--GPU%20Demo-Hugging%20Face-ffd21e?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/spaces/toprakke4/tzero-token-reducer)
[![Canlı Ağ Geçidi](https://img.shields.io/badge/%E2%9A%A1%20Canl%C4%B1%20Ge%C3%A7it-Vercel-000000?style=for-the-badge&logo=vercel)](https://tzero-indol.vercel.app)

> **T-Zero LLM bağlam boyutunuzu küçülttüyse veya token faturalarınızı düşürdüyse lütfen GitHub'da bize bir yıldız verin! ⭐**  
> *Her bir yıldız, bağımsız geliştiricinin bu projeyi %100 ücretsiz, çevrimdışı ve sıfır sızıntılı olarak sürdürmesini destekler.*

</div>

---

<a id="turkce"></a>
## Türkçe Dokümantasyon

T-Zero (Token Zero), yapay zeka kodlama asistanları (Cursor, Claude Desktop, Antigravity IDE, Windsurf, Cline, VS Code, Zed) için geliştirilmiş, **deterministik AST bağlam sıkıştırıcısı ve Model Context Protocol (MCP) sunucusudur**.

### Neden T-Zero?
Yapay zeka modellerine tüm kaynak kodlar metin olarak verildiğinde, fonksiyon gövdelerindeki döngüler ve ara hesaplamalar yüzünden **bağlam penceresinin %80 ila %95'i israf edilir**. T-Zero, kodu metin olarak değil AST (Soyut Sözdizimi Ağacı) olarak okur; fonksiyon gövdelerini çıkarıp arayüzleri, tipleri ve sınıf yapılarını korur.

### Temel Özellikler:
- **20 Standart MCP Aracı:** `get_project_context_tree`, `prune_code_snippet`, `audit_codebase_quality`, `verify_hallucination_guard`, `auto_vault_migrate`, `change_impact_analysis` vb.
- **Smart Skeleton (Tier-2):** Üzerinde çalışılan hedef dosya %100 tam kod kalırken, çevresindeki 1. derece bağımlılıklar imza iskeleti haline getirilir.
- **Reality-Lock Halüsinasyon Kontrolü & %0 Kaçış İspatı:** Modelin uydurduğu import ve fonksiyon çağrılarını koda yazılmadan önce statik AST üzerinde yakalar, 60 ampirik senaryo ile %0.0 halüsinasyon kaçış oranını kanıtlar ve kendi kendine onarır (`tzero --prove-zero-hallucination`).
- **1-Tıkla Auto-Vault Sızıntı Taşıyıcı:** Koddaki gizli API anahtarlarını otomatik bulup `.env` içine taşır, `.gitignore`'a ekler ve kodu `os.environ.get(...)` ile refactor eder.
- **Shannon Entropi Güvenlik Filtresi:** Yüksek entropili ($H \ge 4.75$) gizli anahtarları ve şifreleri yerel olarak tespit eder.
- **Turbo Overdrive (Kamçılama Modu):** Kod tarama veya AST çıkarımı yavaşladığında (>150ms veya $\ge 15$ dosya) otomatik devreye girerek 32 worker thread ile paralel burst ve mikrosaniye seviyesinde bellek içi fast-path önbellek sunar.
- **Otonom Dinamik Alt Ajan Fabrikası (Dynamic Subagent Swarm):** Karmaşık görev verildiğinde aynı anda gereken tüm alt görevleri analiz eder; gerekirse anında ad-hoc alt ajanlar sentezleyip (`AgentForge`) çok çekirdekli paralel koşturur ve PBFT konsensüsü ile birleştirir.
- **%100 Yerel ve Çevrimdışı:** Dış bulut embedding API'si gerektirmez, $0 maliyetle çalışır.
- **Sıfır-Halüsinasyon Matematiksel & Ampirik İspat Raporu:** [ZERO_HALLUCINATION_PROOF.md](ZERO_HALLUCINATION_PROOF.md)
- **Google Colab İnteraktif Lab:** [Google Colab Üzerinde Test Et](https://colab.research.google.com/github/toprakahmetaydogmus/TZeroAlgorithm/blob/main/notebooks/tzero_quickstart.ipynb)
- **Bilimsel ve Teknik Whitepaper:** [WHITE_PAPER_TZERO_V10.md](WHITE_PAPER_TZERO_V10.md) (Matematiksel ispatlar, DAG-AC sıkıştırma ve Reality-Lock analizi)
- **Hugging Face Canlı Demo:** [https://huggingface.co/spaces/toprakke4/tzero-token-reducer](https://huggingface.co/spaces/toprakke4/tzero-token-reducer)

### 30 Saniyede Hızlı Kurulum

```bash
# Seçenek A: Node.js / npx ile Anında Çalıştırma (Sıfır Kurulum):
# Cursor, Claude Desktop, Antigravity, Copilot için:
npx -y tzero-mcp@latest

# Global NPM CLI Kurulumu:
npm install -g tzero-mcp

# Seçenek B: Python pip ile Kurulum:
pip install --upgrade tzero-mcp

# Seçenek C: Tek Satır Otomatik Yükleyici:
# Linux / macOS: curl -fsSL https://raw.githubusercontent.com/toprakahmetaydogmus/TZeroAlgorithm/main/install.sh | bash
# Windows:       irm https://raw.githubusercontent.com/toprakahmetaydogmus/TZeroAlgorithm/main/install.ps1 | iex

# Seçenek D: Git Clone ile Doğrudan Kaynak Koddan Çalışma:
git clone https://github.com/toprakahmetaydogmus/TZeroAlgorithm.git
cd TZeroAlgorithm
python scripts/welcome.py    # Karşılama ekranı (Git hook ayarlarını değiştirmez)
pip install -e .             # Geliştirici modu (Git hook ayarlarını değiştirmez)

# İsteğe bağlı yıldız hatırlatıcı (mevcut hook varsa kurmaz):
python scripts/welcome.py --install-star-hooks

# Tek Tıkla IDE'leri (Cursor, Claude, Windsurf, VS Code) Bağla:
tzero init

# Tek Tıkla Topluluk Paylaşım Merkezi (Twitter, Reddit, Hacker News):
tzero share

# VS Code / Cursor Eklentisini (.vsix) Yükle:
code --install-extension dist/tzero-vscode-12.2.0.vsix

# Yerel CI ve Pre-Push Korumasını Çalıştır ($0 Kota):
tzero local-ci --quick

# Otomatik Git Pre-Push Hook Kur (Hatalı push'ları engeller):
tzero local-ci --install-hook
```

---

## T-Zero Local CI: Sıfır Kota Tüketimiyle Yerel Doğrulama

GitHub Actions dakikalarını yakıp uzakta hata beklemenin önüne geçin! **T-Zero Local CI**, uzaktaki tüm testleri yerel makinenizde **<10 saniyede** çalıştırır:

- **7 Kademe Doğrulama:** Metadata Senkronizasyonu, %100 Sıfır-Sızıntı Güvenlik Taraması, AST ve T-4 Mimari Sınırları, flake8 Linter, Unit Testler, Node.js Eklenti Testleri ve M8ven MCP Uyumluluğu.
- **Otomatik Git Kalkanı (`--install-hook`):** `git push` yaptığınızda yerel CI otomatik devreye girer. Tek bir hata varsa push durdurulur ve GitHub Actions kotanızdan **0 saniye** harcanır!
- **Bağımsız Binary:** `dist/TZeroCI.exe` ile Python kurulumuna bile gerek kalmadan çalıştırabilirsiniz.


---

## Açık Kaynak İnovasyonu Destekleyin: T-Zero'yu %100 Ücretsiz Tutun

Merhaba! Ben **Toprak Ahmet Aydoğmuş**, Siber Akademi'den. T-Zero'yu sıfırdan, yapay zeka kodlama araçlarındaki bağlam şişkinliğini, token maliyetlerini ve halüsinasyonları çözmek için **%100 yerel, çevrimdışı ve ücretsiz ($0 maliyet)** olarak geliştirdim.

T-Zero'nun hiçbir risk sermayesi fonu, ücretli aboneliği veya telemetri takibi yoktur. T-Zero günlük iş akışınızda Cursor, Claude Code veya Windsurf üzerinde token tasarrufu sağladıysa bağımsız geliştirmeyi destekleyebilirsiniz:

- ⭐ **Repoya Yıldız Verin:** Her GitHub yıldızı açık kaynak ekosistemini güçlendirir ve T-Zero'nun keşfedilmesini sağlar.
- 🪙 **Kripto ile Destek (Doğrudan Katkı):**

| Ağ / Platform | Cüzdan Adresi | 1-Tıkla Gönder (Deep Link) | Açıklama ve Doğrulama |
| :--- | :--- | :--- | :--- |
| 🔷 **Ethereum / EVM** | `0xF36Cd453f9F2bE91647C006C46ff66fB41d9F0c5` | [⚡ **Web3 ile Gönder (EIP-681)**](ethereum:0xF36Cd453f9F2bE91647C006C46ff66fB41d9F0c5) | [🔍 Etherscan](https://etherscan.io/address/0xF36Cd453f9F2bE91647C006C46ff66fB41d9F0c5) &bull; ERC-20, Arbitrum, Polygon, Optimism, BSC |
| 🟠 **Bitcoin (BTC)** | `bc1q9k4hvd6c2g8l9w3z7v8f2k3j5l8n9m1p4q7r0s` | [⚡ **Bitcoin ile Gönder (BIP-21)**](bitcoin:bc1q9k4hvd6c2g8l9w3z7v8f2k3j5l8n9m1p4q7r0s?label=T-Zero%20Sponsorship) | [🔍 Mempool Gezgini](https://mempool.space/address/bc1q9k4hvd6c2g8l9w3z7v8f2k3j5l8n9m1p4q7r0s) &bull; Native SegWit |
| 🟢 **USDT (TRC-20)** | `TE7uKxZJ414u938gWf6bYh9QvRk2141517` | [⚡ **Tron ile Gönder**](tron:TE7uKxZJ414u938gWf6bYh9QvRk2141517) | [🔍 Tronscan](https://tronscan.org/#/address/TE7uKxZJ414u938gWf6bYh9QvRk2141517) &bull; Düşük komisyonlu TRC-20 ağı |
| 💖 **GitHub Sponsors** | Toprak Ahmet Aydoğmuş | [💖 **GitHub'da Sponsor Ol**](https://github.com/sponsors/toprakahmetaydogmus) | Aylık düzenli veya tek seferlik açık kaynak desteği |
| 🌐 **Geliştirici İletişim** | Siber Akademi | [🌐 **hopp.bio/siberegitim**](https://hopp.bio/siberegitim) | Tüm sosyal medya ve geliştirici profil bağlantıları |

<details>
<summary>📱 <b>1-Tıkla QR Kodları Görüntüle (Ethereum, Bitcoin, Tron)</b></summary>
<br>

<div align="center">

| 🔷 Ethereum / EVM | 🟠 Bitcoin (BTC) | 🟢 USDT (TRC-20 Tron) |
| :---: | :---: | :---: |
| <img src="../assets/qr_ethereum.svg" width="180" height="180" alt="Ethereum QR Kodu"><br><br>[⚡ **Gönder (EIP-681)**](ethereum:0xF36Cd453f9F2bE91647C006C46ff66fB41d9F0c5) | <img src="../assets/qr_bitcoin.svg" width="180" height="180" alt="Bitcoin QR Kodu"><br><br>[⚡ **Gönder (BIP-21)**](bitcoin:bc1q9k4hvd6c2g8l9w3z7v8f2k3j5l8n9m1p4q7r0s?label=T-Zero%20Sponsorship) | <img src="../assets/qr_tron.svg" width="180" height="180" alt="Tron QR Kodu"><br><br>[⚡ **Tron ile Gönder**](tron:TE7uKxZJ414u938gWf6bYh9QvRk2141517) |
| `0xF36Cd453f9F2bE91647C006C46ff66fB41d9F0c5` | `bc1q9k4hvd6c2g8l9w3z7v8f2k3j5l8n9m1p4q7r0s` | `TE7uKxZJ414u938gWf6bYh9QvRk2141517` |

</div>

</details>

> 💡 *Tüm topluluk bağışları, T-Zero'nun sürekli entegrasyon (CI/CD) matrislerini, otomatik paket yayınlarını, açık kaynak test altyapısını ve araçların tüm geliştiriciler için daima %100 ücretsiz, çevrimdışı ve sıfır-sızıntılı kalmasını finanse etmek için kullanılır.*

<br>

<div align="center">

### Tek Tıkla Topluluk Paylaşımı
**500 Yıldız Hedefimize** ulaşmamıza destek olun! T-Zero'yu tek tıkla paylaşın:

[![X'te Paylaş](https://img.shields.io/badge/Payla%C5%9F-X%20%2F%20Twitter-000000?style=for-the-badge&logo=x&logoColor=white)](https://twitter.com/intent/tweet?text=T-Zero%3A%20Yapay%20zeka%20kodlama%20ara%C3%A7lar%C4%B1nda%20token%20israf%C4%B1n%C4%B1%20%2595%20azaltan%20yerel%20AST%20ba%C4%9Flam%20motoru.%20Geli%C5%9Ftirici%3A%20Toprak%20Ahmet%20Aydo%C4%9Fmu%C5%9F%20(Siber%20Akademi).&url=https%3A%2F%2Fgithub.com%2Ftoprakahmetaydogmus%2FTZeroAlgorithm&hashtags=CursorAI,ClaudeAI,MCP,OpenSource)
[![Reddit'te Paylaş](https://img.shields.io/badge/Payla%C5%9F-Reddit-FF4500?style=for-the-badge&logo=reddit&logoColor=white)](https://www.reddit.com/submit?url=https%3A%2F%2Fgithub.com%2Ftoprakahmetaydogmus%2FTZeroAlgorithm&title=T-Zero%20%E2%80%94%20Deterministik%20AST%20Ba%C4%9Flam%20S%C4%B1k%C4%B1%C5%9Ft%C4%B1r%C4%B1c%C4%B1s%C4%B1%20ve%20MCP%20Sunucusu)
[![LinkedIn'de Paylaş](https://img.shields.io/badge/Payla%C5%9F-LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/sharing/share-offsite/?url=https%3A%2F%2Fgithub.com%2Ftoprakahmetaydogmus%2FTZeroAlgorithm)
[![WhatsApp'ta Paylaş](https://img.shields.io/badge/Payla%C5%9F-WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)](https://api.whatsapp.com/send?text=T-Zero%20ba%C4%9Flam%20motoruna%20g%C3%B6z%20at%3A%20https%3A%2F%2Fgithub.com%2Ftoprakahmetaydogmus%2FTZeroAlgorithm)
[![GitHub'da Yıldızla](https://img.shields.io/badge/Y%C4%B1ld%C4%B1zla-GitHub%20%E2%AD%90-f59e0b?style=for-the-badge&logo=github&logoColor=white)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm)

<br>

**T-Zero Sonsuza Kadar %100 Ücretsiz, Açık Kaynak ve Çevrimdışıdır.**  
*Toprak Ahmet Aydoğmuş (Siber Akademi) tarafından dünya genelindeki tüm geliştiriciler için sevgiyle geliştirildi.*

</div>

---

## Yıldız Geçmişi (Star History)

<div align="center">

<a href="https://star-history.com/#toprakahmetaydogmus/TZeroAlgorithm&Date">
  <img src="https://api.star-history.com/svg?repos=toprakahmetaydogmus/TZeroAlgorithm&type=Date" alt="T-Zero Star History" width="100%" style="max-width: 800px; border-radius: 10px;">
</a>

</div>

---
[Ana Dokümantasyona Dön (English)](../README.md)

## Lisans

T-Zero, [GNU AGPL-3.0-only](../LICENSE) ile lisanslanır. [Telif bildirimi, yazar atfı ve 7. bölüm koşulları](../NOTICE).
