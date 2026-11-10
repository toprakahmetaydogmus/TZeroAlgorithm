# T-Zero Algoritması

[![PyPI](https://img.shields.io/pypi/v/tzero-mcp)](https://pypi.org/project/tzero-mcp/)
[![npm](https://img.shields.io/npm/v/tzero-mcp)](https://www.npmjs.com/package/tzero-mcp)
[![VS Code Marketplace](https://img.shields.io/visual-studio-marketplace/v/siber-akademi.tzero-vscode)](https://marketplace.visualstudio.com/items?itemName=siber-akademi.tzero-vscode)
[![M8ven Publisher](https://m8ven.ai/badge/mcp/toprakahmetaydogmus/tzeroalgorithm?variant=verified)](https://m8ven.ai/mcp/toprakahmetaydogmus/tzeroalgorithm?s=readme)
[![Glama](https://img.shields.io/badge/MCP-Glama-635bff)](https://glama.ai/mcp/servers/toprakahmetaydogmus/TZeroAlgorithm)
[![Smithery](https://smithery.ai/badge/@toprakahmetaydogmus/TZeroAlgorithm)](https://smithery.ai/server/@toprakahmetaydogmus/TZeroAlgorithm)
[![CI](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/actions/workflows/ci.yml/badge.svg)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/actions/workflows/ci.yml)
[![TDQS](https://img.shields.io/badge/TDQS-5.0%2F5.0-15803d)](README.md#tdqs-certification)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776ab)](pyproject.toml)
[![MIT](https://img.shields.io/badge/License-MIT-slategray)](LICENSE)

[English](README.md) · [Türkçe](README.tr.md) · [日本語](README.ja.md) · [简体中文](README.zh.md) · [Gizlilik Politikası](PRIVACY.md)

T-Zero, kodlama asistanları için bir AST bağlam sıkıştırıcısı ve MCP sunucusudur. Varsayılan sunucu 21 araç sunar. `search_tools` ile diğer araçları keşfedebilir veya tam modda 58 aracın tamamını açabilirsiniz.

Paket sürümü **10.9.0**.

## v11 komutları

- `tzero --doctor --deep` — Yerel alt sistemleri denetler.
- `tzero --lsp` — Dil sunucusunu stdio üzerinden başlatır.
- `tzero hook / --hook-install` — Araç kancalarını değerlendirir ve editör yapılandırmasını kurar.
- `--federation export/import/verify/impact` — Depo manifestlerini paylaşır ve depolar arası etkiyi inceler.
- `--scip-import` — SCIP indeksini içe aktarır.
- `--snapshot / --cache-aligned` — AST anlık görüntüsü ve sabit önekli bağlam paketi oluşturur.
- `--contracts-sarif` — Sözleşme değişikliklerini SARIF olarak dışa aktarır.
- `--agent-kernel` — Yerel yürütme planlarını çalışma alanı sınırlarına göre denetler.

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
code --install-extension dist/tzero-vscode-10.9.0.vsix
```

---

## ⭐ Açık Kaynak İnovasyonu Destekleyin!

Merhaba! Ben **Toprak Ahmet Aydoğmuş**, Siber Akademi'den. T-Zero'yu sıfırdan, yapay zeka kodlama araçlarındaki token israfını ve halüsinasyonları çözmek için %100 yerel ve ücretsiz ($0 maliyet) olarak geliştirdim.

Eğer T-Zero işinize yaradıysa lütfen GitHub üzerinden bir ⭐ vermeyi unutmayın! Her yıldız açık kaynak ekosistemini güçlendirir. 🚀

---

## 📈 Yıldız Geçmişi (Star History)

<div align="center">

<a href="https://star-history.com/#toprakahmetaydogmus/TZeroAlgorithm&Date">
  <img src="https://api.star-history.com/svg?repos=toprakahmetaydogmus/TZeroAlgorithm&type=Date" alt="T-Zero Star History" width="100%" style="max-width: 800px; border-radius: 10px;">
</a>

</div>

---
[Ana Dokümantasyona Dön (English)](README.md)
