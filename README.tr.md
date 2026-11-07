# T-Zero Algoritması - Türkçe Dokümantasyon

[English](README.md) | [Türkçe](README.tr.md) | [Google Colab Canlı Lab](https://colab.research.google.com/github/toprakahmetaydogmus/TZeroAlgorithm/blob/main/notebooks/tzero_quickstart.ipynb) | [Hugging Face Canlı Demo](https://huggingface.co/spaces/toprakke4/tzero-token-reducer) | [Tarayıcıda Doğrudan Aç (GitHub Codespaces)](https://codespaces.new/toprakahmetaydogmus/TZeroAlgorithm)

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
code --install-extension dist/tzero-vscode-10.7.4.vsix
```

---

## ⭐ 15 Yaşındaki Genç Bir Açık Kaynak Geliştiriciyi Destekleyin!

Merhaba! Ben **Toprak Ahmet Aydoğmuş**, Siber Akademi'den 15 yaşında genç bir yazılımcıyım. T-Zero'yu sıfırdan, yapay zeka kodlama araçlarındaki token israfını ve halüsinasyonları çözmek için %100 yerel ve ücretsiz ($0 maliyet) olarak geliştirdim.

Eğer T-Zero işinize yaradıysa lütfen GitHub üzerinden bir ⭐ vermeyi unutmayın! Her yıldız genç bir açık kaynak geliştirici için dünyalara bedel. 🚀

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
