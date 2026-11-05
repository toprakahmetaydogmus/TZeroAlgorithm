# T-Zero Algoritması - Türkçe Dokümantasyon

[English](README.md) | [Türkçe](README.tr.md) | [Hugging Face Canlı Demo](https://huggingface.co/spaces/toprakke4/tzero-token-reducer)

---

<a id="turkce"></a>
## 🇹🇷 Türkçe Dokümantasyon

T-Zero (Token Zero), yapay zeka kodlama asistanları (Cursor, Claude Desktop, Antigravity IDE, Windsurf, Cline, VS Code, Zed) için geliştirilmiş, **deterministik AST bağlam sıkıştırıcısı ve Model Context Protocol (MCP) sunucusudur**.

### Neden T-Zero?
Yapay zeka modellerine tüm kaynak kodlar metin olarak verildiğinde, fonksiyon gövdelerindeki döngüler ve ara hesaplamalar yüzünden **bağlam penceresinin %80 ila %95'i israf edilir**. T-Zero, kodu metin olarak değil AST (Soyut Sözdizimi Ağacı) olarak okur; fonksiyon gövdelerini çıkarıp arayüzleri, tipleri ve sınıf yapılarını korur.

### Temel Özellikler:
- **14 Standart MCP Aracı:** `get_project_context_tree`, `prune_code_snippet`, `audit_codebase_quality`, `verify_hallucination_guard` vb.
- **Smart Skeleton (Tier-2):** Üzerinde çalışılan hedef dosya %100 tam kod kalırken, çevresindeki 1. derece bağımlılıklar imza iskeleti haline getirilir.
- **Reality-Lock Halüsinasyon Kontrolü:** Modelin uydurduğu import ve fonksiyon çağrılarını koda yazılmadan önce statik AST üzerinde yakalar.
- **Shannon Entropi Güvenlik Filtresi:** Yüksek entropili ($H \ge 4.75$) gizli anahtarları ve şifreleri yerel olarak tespit eder.
- **%100 Yerel ve Çevrimdışı:** Dış bulut embedding API'si gerektirmez, $0 maliyetle çalışır.
- **Hugging Face Canlı Demo:** [https://huggingface.co/spaces/toprakke4/tzero-token-reducer](https://huggingface.co/spaces/toprakke4/tzero-token-reducer)

### 30 Saniyede Hızlı Kurulum:
```bash
# Kurulum:
pip install tzero-mcp

# 1 saniyede tüm IDE'leri otomatik yapılandır:
tzero init

# (İsteğe bağlı) VS Code & Cursor Eklentisini (.vsix) yükle:
code --install-extension dist/tzero-vscode-10.5.0.vsix

# Kod tabanını sıkıştır ve ağaç çıkar:
tzero --tree . --out context.txt

# Canlı web demosunu yerel başlat:
tzero space
```

---

---
[Ana Dokümantasyona Dön (English)](README.md)
