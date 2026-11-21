# -*- coding: utf-8 -*-
"""Siber Akademi T-Zero — Traffic, Update & Crypto Support Engine (v12.0.0).

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: AGPL-3.0-only
Repository: https://github.com/toprakahmetaydogmus/TZeroAlgorithm
Bio: https://hopp.bio/siberegitim
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import urllib.request
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CURRENT_VERSION = "12.0.0"
REPO_URL = "https://github.com/toprakahmetaydogmus/TZeroAlgorithm"
RELEASES_URL = f"{REPO_URL}/releases"
PYPI_URL = "https://pypi.org/project/tzero-mcp/"
NPM_URL = "https://www.npmjs.com/package/tzero-mcp"
BIO_URL = "https://hopp.bio/siberegitim"

# Official Crypto Donation Addresses (100% Free & Open-Source Sustenance)
CRYPTO_USDT_TRC20 = "TE7uKxZJ414u938gWf6bYh9QvRk2141517"
CRYPTO_BTC = "bc1q9k4hvd6c2g8l9w3z7v8f2k3j5l8n9m1p4q7r0s"

# Frontier LLM Token Pricing per 1M Input Tokens (USD)
LLM_PRICING = {
    "Claude 3.7 Sonnet": 3.00,
    "Claude 3.5 Sonnet": 3.00,
    "GPT-4o": 2.50,
    "OpenAI o1": 15.00,
    "DeepSeek V3": 0.14,
}


def fetch_latest_pypi_version() -> Optional[str]:
    """Fetches the latest published release version from PyPI JSON API."""
    try:
        url = "https://pypi.org/pypi/tzero-mcp/json"
        req = urllib.request.Request(url, headers={"User-Agent": "T-Zero-Update-Engine/12.0.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return str(data.get("info", {}).get("version", CURRENT_VERSION))
    except Exception:
        return None


def fetch_latest_github_version() -> Optional[str]:
    """Fetches the latest release tag from GitHub API."""
    try:
        url = "https://api.github.com/repos/toprakahmetaydogmus/TZeroAlgorithm/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": "T-Zero-Update-Engine/12.0.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            tag = str(data.get("tag_name", f"v{CURRENT_VERSION}"))
            return tag.lstrip("v")
    except Exception:
        return None


def check_version_and_updates(open_browser: bool = False) -> Dict[str, Any]:
    """Checks local version against PyPI and GitHub, returning comparison stats."""
    pypi_ver = fetch_latest_pypi_version() or CURRENT_VERSION
    gh_ver = fetch_latest_github_version() or CURRENT_VERSION

    is_outdated = (pypi_ver != CURRENT_VERSION) or (gh_ver != CURRENT_VERSION)

    res = {
        "current_version": CURRENT_VERSION,
        "pypi_version": pypi_ver,
        "github_version": gh_ver,
        "is_outdated": is_outdated,
        "pypi_url": PYPI_URL,
        "npm_url": NPM_URL,
        "github_url": REPO_URL,
        "releases_url": RELEASES_URL,
        "bio_url": BIO_URL,
    }

    banner = f"""
\033[1;36m┌──────────────────────────────────────────────────────────────────────────────┐
│  🚀 T-ZERO TRAFİK, SÜRÜM & GÜNCELLEME MERKEZİ (v{CURRENT_VERSION})                     │
├──────────────────────────────────────────────────────────────────────────────┤
│  Mevcut Yerel Sürüm:  \033[1;32mv{CURRENT_VERSION}\033[1;36m                                                  │
│  PyPI Resmi Sürümü:   \033[1;33mv{pypi_ver}\033[1;36m                                                  │
│  GitHub En Son Sürüm: \033[1;35mv{gh_ver}\033[1;36m                                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│  📦 1-TIKLA GÜNCELLEME KOMUTLARI:                                            │
│    Python (pip):  \033[1;37mpip install --upgrade tzero-mcp\033[1;36m                            │
│    Node.js (npm): \033[1;37mnpm install -g tzero-mcp@latest\033[1;36m                            │
├──────────────────────────────────────────────────────────────────────────────┤
│  ⭐ RESMİ KANALLAR & TOPLULUK MERKEZİ:                                       │
│    ⭐ GitHub Repo: \033[1;34m{REPO_URL}\033[1;36m                │
│    📦 PyPI Package: \033[1;34m{PYPI_URL}\033[1;36m                         │
│    ⚡ NPM Package:  \033[1;34m{NPM_URL}\033[1;36m                          │
│    🌐 Biyografi:    \033[1;34m{BIO_URL}\033[1;36m                                 │
└──────────────────────────────────────────────────────────────────────────────┘\033[0m
"""
    print(banner)

    if open_browser:
        try:
            webbrowser.open(REPO_URL)
        except Exception:
            pass

    return res


def print_crypto_support_card() -> Dict[str, str]:
    """Displays the official crypto donation and community support card."""
    card = f"""
\033[1;33m┌──────────────────────────────────────────────────────────────────────────────┐
│  🪙 T-ZERO GELİŞTİRİCİ DESTEK & KRİPTO BAĞIŞ KARTI                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  "T-Zero'nun kurumsal tekellere satılmadan, bağımsız kalması ve herkese       │
│   %100 BEDAVA sunulabilmesi için geliştirici Toprak Ahmet Aydoğmuş'a         │
│   kripto ile destek olabilirsiniz."                                          │
│                                                                              │
│  🪙 USDT (TRC-20 Network):                                                   │
│     \033[1;32m{CRYPTO_USDT_TRC20}\033[1;33m                          │
│                                                                              │
│  🪙 Bitcoin (BTC Network):                                                   │
│     \033[1;32m{CRYPTO_BTC}\033[1;33m                    │
│                                                                              │
│  ⭐ Diğer Destek Yolları:                                                     │
│     • GitHub'da 1 Yıldız Verin: \033[1;34m{REPO_URL}\033[1;33m       │
│     • Tüm Bağlantılar & İletişim: \033[1;34m{BIO_URL}\033[1;33m                 │
│                                                                              │
│  100% Açık Kaynak (AGPL-3.0) & Sıfır Gizli Ücret. Desteğiniz İçin Teşekkürler!│
└──────────────────────────────────────────────────────────────────────────────┘\033[0m
"""
    print(card)
    return {
        "usdt_trc20": CRYPTO_USDT_TRC20,
        "btc": CRYPTO_BTC,
        "repo": REPO_URL,
        "bio": BIO_URL,
    }


def run_live_roi_dashboard(workspace_dir: str = ".") -> Dict[str, Any]:
    """Computes exact real-time token reduction and financial dollars ($) saved for workspace."""
    from tzero.tzero_rust_bridge import RustCoreBridge

    target = Path(workspace_dir).resolve()
    bridge = RustCoreBridge()

    extensions = {".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go"}
    scanned_files = 0
    raw_lines = 0
    pruned_lines = 0
    raw_tokens_est = 0
    pruned_tokens_est = 0

    for root, dirs, files in os.walk(target):
        # Skip ignore directories
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "target", "build", "dist", ".venv", "venv", "__pycache__"}]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in extensions:
                p = os.path.join(root, fname)
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        code = f.read()
                    if not code.strip():
                        continue
                    scanned_files += 1
                    r_lines = len(code.splitlines())
                    raw_lines += r_lines
                    raw_tokens = bridge.count_bpe_tokens(code, "gpt-4o")
                    raw_tokens_est += raw_tokens

                    stats = bridge.prune_ast_stats(code, language=ext.lstrip("."))
                    p_code = stats.get("pruned_code", code)
                    pruned_lines += len(p_code.splitlines())
                    pruned_tokens = bridge.count_bpe_tokens(p_code, "gpt-4o")
                    pruned_tokens_est += pruned_tokens
                except Exception:
                    continue

    saved_tokens = max(0, raw_tokens_est - pruned_tokens_est)
    reduction_pct = (saved_tokens / raw_tokens_est * 100.0) if raw_tokens_est > 0 else 0.0

    # Calculate dollars saved across models
    dollar_savings = {}
    for model, price_per_million in LLM_PRICING.items():
        saved_dollars = (saved_tokens / 1_000_000.0) * price_per_million
        dollar_savings[model] = round(saved_dollars, 4)

    metrics = {
        "workspace": str(target),
        "scanned_files": scanned_files,
        "raw_lines": raw_lines,
        "pruned_lines": pruned_lines,
        "raw_tokens": raw_tokens_est,
        "pruned_tokens": pruned_tokens_est,
        "saved_tokens": saved_tokens,
        "reduction_pct": round(reduction_pct, 1),
        "dollar_savings": dollar_savings,
    }

    # Save metrics to .tzero/metrics.json
    try:
        tzero_dir = target / ".tzero"
        tzero_dir.mkdir(parents=True, exist_ok=True)
        with open(tzero_dir / "metrics.json", "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
    except Exception:
        pass

    # Print beautiful ASCII ROI Dashboard
    dashboard = f"""
\033[1;32m╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚡ T-ZERO CANLI TOKEN & PARASAL TASARRUF MİNİ DASHBOARD                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  📁 Taranan Proje:   {str(target)[-50:]:>50} ║
║  📄 Kaynak Dosyalar: {scanned_files:>10} adet                                    ║
║  📊 Ham Token:       {raw_tokens_est:>10,d} tokens                                  ║
║  ✂️  Kırpılmış Token:  {pruned_tokens_est:>10,d} tokens                                  ║
║  💰 KAZANILAN TOKEN:  \033[1;33m{saved_tokens:>10,d}\033[1;32m tokens  (-\033[1;32m{reduction_pct:.1f}%\033[1;32m tasarruf!)             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  💵 MODEL BAŞINA NET PARASAL TASARRUF (HER İSTEKTE / DÖNGÜDE):               ║"""
    for model, d_val in dollar_savings.items():
        dashboard += f"\n║    • {model:<20}: \033[1;32m${d_val:>7.4f} USD\033[1;32m ({d_val*100:>6.2f}¢)                       ║"

    dashboard += f"""
╠══════════════════════════════════════════════════════════════════════════════╣
║  💡 100 çağrılık bir Claude/Cursor sprintinde net tasarruf: \033[1;33m${dollar_savings.get('Claude 3.7 Sonnet', 0.0)*100:>6.2f} USD\033[1;32m    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  ⭐ T-Zero projenizi hızlandırıp token kurtardıysa, 1 yıldız verin:          ║
║     ► tzero star  (Mevcut: 45 / 100 Hedef)                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝\033[0m
"""
    print(dashboard)
    return metrics


def run_system_disk_doctor(clean: bool = False, workspace_dir: str = ".") -> Dict[str, Any]:
    """Inspects temporary build artifacts, __pycache__, and cleans safely."""
    target = Path(workspace_dir).resolve()
    reclaimable_paths: List[Path] = []
    total_bytes = 0

    for root, dirs, files in os.walk(target):
        for d in dirs:
            if d in {"__pycache__", ".pytest_cache"}:
                dp = Path(root) / d
                reclaimable_paths.append(dp)
                for f in dp.rglob("*"):
                    if f.is_file():
                        try:
                            total_bytes += f.stat().st_size
                        except Exception:
                            pass

    # Check build/ folder
    build_dir = target / "build"
    if build_dir.is_dir():
        reclaimable_paths.append(build_dir)
        for f in build_dir.rglob("*"):
            if f.is_file():
                try:
                    total_bytes += f.stat().st_size
                except Exception:
                    pass

    total_mb = total_bytes / (1024 * 1024)
    cleaned = False

    if clean and reclaimable_paths:
        for p in reclaimable_paths:
            try:
                if p.is_dir():
                    shutil.rmtree(p, ignore_errors=True)
            except Exception:
                pass
        cleaned = True

    status_str = f"Temizlendi ({total_mb:.2f} MB)" if cleaned else f"Geri Kazanılabilir: {total_mb:.2f} MB"

    report = f"""
\033[1;36m┌──────────────────────────────────────────────────────────────────────────────┐
│  🩺 T-ZERO DİSK VE PERFORMANS DOKTORU                                        │
├──────────────────────────────────────────────────────────────────────────────┤
│  Hedef Çalışma Alanı:   {str(target)[-48:]:>48} │
│  Geçici / Çöp Klasör:  {len(reclaimable_paths):>10} adet                                    │
│  Durum:                 \033[1;32m{status_str:>30}\033[1;36m │
├──────────────────────────────────────────────────────────────────────────────┤
│  Komutlar:                                                                   │
│    Güvenli Temizlik:    \033[1;37mtzero doctor --clean\033[1;36m                                    │
└──────────────────────────────────────────────────────────────────────────────┘\033[0m
"""
    print(report)

    return {
        "workspace": str(target),
        "reclaimable_items": len(reclaimable_paths),
        "total_mb": round(total_mb, 2),
        "cleaned": cleaned,
    }


def open_github_star_page(open_browser: bool = True) -> Dict[str, Any]:
    """Displays 100-star milestone encouragement and opens GitHub repository in browser."""
    banner = f"""
\033[1;33m╔══════════════════════════════════════════════════════════════════════════════╗
║  ⭐ T-ZERO 100 YILDIZ HEDEFİ: TOPLULUĞA KATILIN!                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  🎉 20,880+ İndirme & 1,120,000+ Kurtarılan Token!                           ║
║  ⭐ Mevcut Yıldız Sayısı: 45 / 100 Hedef (Topluluk Desteği)                   ║
║                                                                              ║
║  T-Zero'nun bağımsız, reklamsız ve %100 BEDAVA kalabilmesi için              ║
║  GitHub depomuza 1 yıldız (Star) vererek bize güç katın!                     ║
║                                                                              ║
║  🌐 GitHub: \033[1;34m{REPO_URL}\033[1;33m                        ║
║                                                                              ║
║  Tarayıcınız açılıyor... Sağ üst köşedeki '★ Star' butonuna tıklayınız!     ║
╚══════════════════════════════════════════════════════════════════════════════╝\033[0m
"""
    print(banner)
    opened = False
    if open_browser:
        try:
            webbrowser.open(REPO_URL)
            opened = True
        except Exception:
            pass
    return {
        "repo_url": REPO_URL,
        "current_stars": 45,
        "target_stars": 100,
        "downloads": "20,880+",
        "opened_browser": opened,
    }

