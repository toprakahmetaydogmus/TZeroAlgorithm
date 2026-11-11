# T-Zero Algoritması - Türkçe Dokümantasyon

[English](README.md) | **[Türkçe](README.tr.md)** | [日本語](README.ja.md) | [简体中文](README.zh.md) | [Gizlilik Politikası (Privacy)](PRIVACY.md) | [Google Colab Canlı Lab](https://colab.research.google.com/github/toprakahmetaydogmus/TZeroAlgorithm/blob/main/notebooks/tzero_quickstart.ipynb) | [Hugging Face Canlı Demo](https://huggingface.co/spaces/toprakke4/tzero-token-reducer) | [Tarayıcıda Doğrudan Aç (GitHub Codespaces)](https://codespaces.new/toprakahmetaydogmus/TZeroAlgorithm)

<div align="center">

[![M8ven Verified](https://m8ven.ai/badge/mcp/toprakahmetaydogmus/tzeroalgorithm?variant=verified)](https://m8ven.ai/mcp/toprakahmetaydogmus/tzeroalgorithm?s=readme)
[![PyPI](https://img.shields.io/pypi/v/tzero-mcp?color=38bdf8&style=flat-square&logo=pypi)](https://pypi.org/project/tzero-mcp/)
[![npm](https://img.shields.io/npm/v/tzero-mcp?color=cb3837&style=flat-square&logo=npm)](https://www.npmjs.com/package/tzero-mcp)
[![VS Code](https://img.shields.io/visual-studio-marketplace/v/siber-akademi.tzero-vscode?style=flat-square&logo=visual-studio-code&color=007ACC)](https://marketplace.visualstudio.com/items?itemName=siber-akademi.tzero-vscode)

</div>

---

<a id="turkce"></a>
## 🇹🇷 Türkçe Dokümantasyon

T-Zero (Token Zero), yapay zeka kodlama asistanları (Cursor, Claude Desktop, Antigravity IDE, Windsurf, Cline, VS Code, Zed) için geliştirilmiş, **deterministik AST bağlam sıkıştırıcısı ve Model Context Protocol (MCP) sunucusudur**.

> 📈 **Resmi Kullanım İstatistikleri:** Toplam **17.387+ PyPI indirmesi** (`pip install tzero-mcp`), son 14 günde **1.275 Git klonlaması** (320 bağımsız mühendislik ekibi) ve 340+ binary release indirmesi.

### Neden T-Zero?
Yapay zeka modellerine tüm kaynak kodlar metin olarak verildiğinde, fonksiyon gövdelerindeki döngüler ve ara hesaplamalar yüzünden **bağlam penceresinin %80 ila %95'i israf edilir**. T-Zero, kodu metin olarak değil AST (Soyut Sözdizimi Ağacı) olarak okur; fonksiyon gövdelerini çıkarıp arayüzleri, tipleri ve sınıf yapılarını korur.

### Temel Özellikler:
- **20 Standart MCP Aracı:** `get_project_context_tree`, `prune_code_snippet`, `audit_codebase_quality`, `verify_hallucination_guard`, `auto_vault_migrate`, `change_impact_analysis` vb.
- **Smart Skeleton (Tier-2):** Üzerinde çalışılan hedef dosya %100 tam kod kalırken, çevresindeki 1. derece bağımlılıklar imza iskeleti haline getirilir.
- **Reality-Lock Halüsinasyon Kontrolü:** Modelin uydurduğu import ve fonksiyon çağrılarını koda yazılmadan önce statik AST üzerinde yakalar ve kendi kendine onarır.
- **1-Tıkla Auto-Vault Sızıntı Taşıyıcı:** Koddaki gizli API anahtarlarını otomatik bulup `.env` içine taşır, `.gitignore`'a ekler ve kodu `os.environ.get(...)` ile refactor eder.
- **Shannon Entropi Güvenlik Filtresi:** Yüksek entropili ($H \ge 4.75$) gizli anahtarları ve şifreleri yerel olarak tespit eder.
- **Turbo Overdrive (Kamçılama Modu):** Kod tarama veya AST çıkarımı yavaşladığında (>150ms veya $\ge 15$ dosya) otomatik devreye girerek 32 worker thread ile paralel burst ve mikrosaniye seviyesinde bellek içi fast-path önbellek sunar.
- **Otonom Dinamik Alt Ajan Fabrikası (Dynamic Subagent Swarm):** Karmaşık görev verildiğinde aynı anda gereken tüm alt görevleri analiz eder; gerekirse anında ad-hoc alt ajanlar sentezleyip (`AgentForge`) çok çekirdekli paralel koşturur ve PBFT konsensüsü ile birleştirir.
- **%100 Yerel ve Çevrimdışı:** Dış bulut embedding API'si gerektirmez, $0 maliyetle çalışır.
- **Google Colab İnteraktif Lab:** [Google Colab Üzerinde Test Et](https://colab.research.google.com/github/toprakahmetaydogmus/TZeroAlgorithm/blob/main/notebooks/tzero_quickstart.ipynb)
- **Bilimsel ve Teknik Whitepaper:** [docs/WHITE_PAPER_TZERO_V10.md](docs/WHITE_PAPER_TZERO_V10.md) (Matematiksel ispatlar, DAG-AC sıkıştırma ve Reality-Lock analizi)
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

# 🚀 Tek Tıkla IDE'leri (Cursor, Claude, Windsurf, VS Code) Bağla:
tzero init

# 🧩 VS Code / Cursor Eklentisini (.vsix) Yükle:
code --install-extension dist/tzero-vscode-10.8.0.vsix
```

---

## ⭐ Açık Kaynak İnovasyonu Destekleyin!

Merhaba! Ben **Toprak Ahmet Aydoğmuş**, Siber Akademi'den. T-Zero'yu sıfırdan, yapay zeka kodlama araçlarındaki token israfını ve halüsinasyonları çözmek için %100 yerel ve ücretsiz ($0 maliyet) olarak geliştirdim.

Eğer T-Zero işinize yaradıysa lütfen GitHub üzerinden bir ⭐ vermeyi unutmayın! Her yıldız açık kaynak ekosistemini güçlendirir. 🚀

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/toprakahmetaydogmus/TZeroAlgorithm?style=social)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm)

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
