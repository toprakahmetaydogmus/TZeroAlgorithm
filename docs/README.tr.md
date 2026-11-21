# T-Zero Algoritması - Türkçe Dokümantasyon

[English](../README.md) | **[Türkçe](README.tr.md)** | [日本語](README.ja.md) | [简体中文](README.zh.md) | [Gizlilik Politikası (Privacy)](../PRIVACY.md) | [Google Colab Canlı Lab](https://colab.research.google.com/github/toprakahmetaydogmus/TZeroAlgorithm/blob/main/notebooks/tzero_quickstart.ipynb) | [Hugging Face Canlı Demo](https://huggingface.co/spaces/toprakke4/tzero-token-reducer) | [Tarayıcıda Doğrudan Aç (GitHub Codespaces)](https://codespaces.new/toprakahmetaydogmus/TZeroAlgorithm)

<div align="center">

[![GitHub Stars](https://img.shields.io/github/stars/toprakahmetaydogmus/TZeroAlgorithm?style=social)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm)
[![M8ven Score](https://m8ven.ai/badge/mcp/toprakahmetaydogmus/tzeroalgorithm)](https://m8ven.ai/mcp/toprakahmetaydogmus/tzeroalgorithm?s=readme)
[![Verified on FreeAPI](https://findfreeapi.com/api/badge/tzeroalgorithm)](https://findfreeapi.com/en/service/tzeroalgorithm)
[![PyPI](https://img.shields.io/pypi/v/tzero-mcp?color=38bdf8&style=flat-square&logo=pypi)](https://pypi.org/project/tzero-mcp/)
[![PyPI Toplam](https://img.shields.io/pepy/dt/tzero-mcp?color=38bdf8&style=flat-square&logo=pypi)](https://pypi.org/project/tzero-mcp/)
[![PyPI Aylık](https://img.shields.io/pypi/dm/tzero-mcp?color=38bdf8&style=flat-square&logo=pypi)](https://pypi.org/project/tzero-mcp/)
[![npm](https://img.shields.io/npm/v/tzero-mcp?color=cb3837&style=flat-square&logo=npm)](https://www.npmjs.com/package/tzero-mcp)
[![npm Toplam](https://img.shields.io/npm/dt/tzero-mcp?color=cb3837&style=flat-square&logo=npm)](https://www.npmjs.com/package/tzero-mcp)
[![npm Aylık](https://img.shields.io/npm/dm/tzero-mcp?color=cb3837&style=flat-square&logo=npm)](https://www.npmjs.com/package/tzero-mcp)
[![VS Code](https://img.shields.io/badge/VS%20Code-v12.1.0-007ACC?style=flat-square&logo=visualstudiocode&logoColor=white)](https://marketplace.visualstudio.com/items?itemName=siber-akademi.tzero-vscode)
[![Open VSX](https://img.shields.io/open-vsx/dt/siber-akademi/tzero-vscode?style=flat-square&logo=openvsx&color=purple)](https://open-vsx.org/extension/siber-akademi/tzero-vscode)

<br>

<p align="center">
  <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm">
    <img src="../assets/tzero_badge_card.svg" alt="T-Zero Context Architect Canlı Rozet Kartı" width="100%" style="max-width: 800px; border-radius: 14px; box-shadow: 0 18px 40px rgba(0, 0, 0, 0.8);">
  </a>
</p>

<div align="center">

### 🌟 100 Yıldız Yolculuğu: T-Zero'nun 100 Yıldız Hedefine Ulaşmasına Destek Olun!
[![GitHub Yıldızları](https://img.shields.io/github/stars/toprakahmetaydogmus/TZeroAlgorithm?style=for-the-badge&logo=github&logoColor=white&label=Y%C4%B1ld%C4%B1zlar%20%7C%20Hedef:%20100&color=f59e0b)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm)
[![%100 Ücretsiz & Açık Kaynak](https://img.shields.io/badge/Fiyat-0%20TL%20(%25100%20%C3%9Ccretsiz)-10b981?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](../LICENSE)
[![Geliştirici](https://img.shields.io/badge/Geli%C5%9Ftirici-Toprak%20Ahmet%20Aydo%C4%9Fmu%C5%9F-8b5cf6?style=for-the-badge&logo=visualstudiocode&logoColor=white)](https://linkedin.com/in/toprak-ahmet-aydo%C4%9Fmu%C5%9F-60462534b/)

> **T-Zero LLM bağlam boyutunuzu küçülttüyse veya token faturalarınızı düşürdüyse lütfen GitHub'da bize bir yıldız verin! ⭐**  
> *Her bir yıldız, bağımsız geliştiricinin bu projeyi %100 ücretsiz, çevrimdışı ve sıfır sızıntılı olarak sürdürmesini destekler.*

</div>

</div>

---

<a id="turkce"></a>
## 🇹🇷 Türkçe Dokümantasyon

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

### ⚡ 30 Saniyede Hızlı Kurulum

```bash
# 📦 Seçenek A: Node.js / npx ile Anında Çalıştırma (Sıfır Kurulum):
# Cursor, Claude Desktop, Antigravity, Copilot için:
npx -y tzero-mcp@latest

# Global NPM CLI Kurulumu:
npm install -g tzero-mcp

# 🐍 Seçenek B: Python pip ile Kurulum:
pip install --upgrade tzero-mcp

# 🌟 Seçenek C: Tek Satır Otomatik Yükleyici:
# Linux / macOS: curl -fsSL https://raw.githubusercontent.com/toprakahmetaydogmus/TZeroAlgorithm/main/install.sh | bash
# Windows:       irm https://raw.githubusercontent.com/toprakahmetaydogmus/TZeroAlgorithm/main/install.ps1 | iex

# 🐙 Seçenek D: Git Clone ile Doğrudan Kaynak Koddan Çalışma:
git clone https://github.com/toprakahmetaydogmus/TZeroAlgorithm.git
cd TZeroAlgorithm
python scripts/welcome.py    # Hoş geldin & otomatik git hook yıldız hatırlatıcı
pip install -e .             # Geliştirici modu (.githooks otomatik aktifleşir)

# 🚀 Tek Tıkla IDE'leri (Cursor, Claude, Windsurf, VS Code) Bağla:
tzero init

# 📢 Tek Tıkla Topluluk Paylaşım Merkezi (Twitter, Reddit, Hacker News):
tzero share

# 🧩 VS Code / Cursor Eklentisini (.vsix) Yükle:
code --install-extension dist/tzero-vscode-12.1.0.vsix

# ⚡ Yerel CI ve Pre-Push Korumasını Çalıştır ($0 Kota):
tzero local-ci --quick

# 🛡️ Otomatik Git Pre-Push Hook Kur (Hatalı push'ları engeller):
tzero local-ci --install-hook
```

---

## ⚡ T-Zero Local CI: Sıfır Kota Tüketimiyle Yerel Doğrulama

GitHub Actions dakikalarını yakıp uzakta hata beklemenin önüne geçin! **T-Zero Local CI**, uzaktaki tüm testleri yerel makinenizde **<10 saniyede** çalıştırır:

- **7 Kademe Doğrulama:** Metadata Senkronizasyonu, %100 Sıfır-Sızıntı Güvenlik Taraması, AST ve T-4 Mimari Sınırları, flake8 Linter, Unit Testler, Node.js Eklenti Testleri ve M8ven MCP Uyumluluğu.
- **Otomatik Git Kalkanı (`--install-hook`):** `git push` yaptığınızda yerel CI otomatik devreye girer. Tek bir hata varsa push durdurulur ve GitHub Actions kotanızdan **0 saniye** harcanır!
- **Bağımsız Binary:** `dist/TZeroCI.exe` ile Python kurulumuna bile gerek kalmadan çalıştırabilirsiniz.


---

## ⭐ Açık Kaynak İnovasyonu Destekleyin!

Merhaba! Ben **Toprak Ahmet Aydoğmuş**, Siber Akademi'den. T-Zero'yu sıfırdan, yapay zeka kodlama araçlarındaki token israfını ve halüsinasyonları çözmek için %100 yerel ve ücretsiz ($0 maliyet) olarak geliştirdim.

Eğer T-Zero işinize yaradıysa lütfen GitHub üzerinden bir ⭐ vermeyi unutmayın! Her yıldız açık kaynak ekosistemini güçlendirir. 🚀

<div align="center">

### 📊 Canlı Ekosistem ve Dağıtım İstatistikleri
*(GitHub API, npm Registry ve PyPI PePy üzerinden 7/24 anlık otomatik güncellenir)*

[![GitHub Yıldızları](https://img.shields.io/github/stars/toprakahmetaydogmus/TZeroAlgorithm?style=for-the-badge&logo=github&color=22c55e&label=GitHub%20Y%C4%B1ld%C4%B1zlar%C4%B1)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/stargazers)
[![GitHub Forklar](https://img.shields.io/github/forks/toprakahmetaydogmus/TZeroAlgorithm?style=for-the-badge&logo=github&color=3b82f6&label=Forklar)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/network/members)
[![npm Toplam İndirme](https://img.shields.io/npm/dt/tzero-mcp?style=for-the-badge&logo=npm&color=cb3837&label=npm%20Toplam%20%C4%B0ndirme)](https://www.npmjs.com/package/tzero-mcp)
[![npm Aylık İndirme](https://img.shields.io/npm/dm/tzero-mcp?style=for-the-badge&logo=npm&color=ef4444&label=npm%20Ayl%C4%B1k%20%C4%B0ndirme)](https://www.npmjs.com/package/tzero-mcp)
[![PyPI Toplam İndirme](https://img.shields.io/pepy/dt/tzero-mcp?style=for-the-badge&logo=pypi&color=38bdf8&label=PyPI%20Toplam%20%C4%B0ndirme)](https://pypi.org/project/tzero-mcp/)
[![PyPI Aylık İndirme](https://img.shields.io/pypi/dm/tzero-mcp?style=for-the-badge&logo=pypi&color=0284c7&label=PyPI%20Ayl%C4%B1k%20%C4%B0ndirme)](https://pypi.org/project/tzero-mcp/)
[![Open VSX İndirme](https://img.shields.io/open-vsx/dt/siber-akademi/tzero-vscode?style=for-the-badge&logo=openvsx&color=8b5cf6&label=Open-VSX%20%C4%B0ndirme)](https://open-vsx.org/extension/siber-akademi/tzero-vscode)
[![Son Commit](https://img.shields.io/github/last-commit/toprakahmetaydogmus/TZeroAlgorithm?style=for-the-badge&logo=github&color=10b981&label=Son%20Commit)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/commits/main)

<br>

### 🚀 Tek Tıkla Topluluk Paylaşımı
**100 Yıldız Hedefimize** ulaşmamıza destek olun! T-Zero'yu tek tıkla paylaşın:

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

## 📈 Yıldız Geçmişi (Star History)

<div align="center">

<a href="https://star-history.com/#toprakahmetaydogmus/TZeroAlgorithm&Date">
  <img src="https://api.star-history.com/svg?repos=toprakahmetaydogmus/TZeroAlgorithm&type=Date" alt="T-Zero Star History" width="100%" style="max-width: 800px; border-radius: 10px;">
</a>

</div>

---
[Ana Dokümantasyona Dön (English)](README.md)

## Lisans

T-Zero, [GNU AGPL-3.0-only](../LICENSE) ile lisanslanır. [Telif bildirimi, yazar atfı ve 7. bölüm koşulları](../NOTICE).
