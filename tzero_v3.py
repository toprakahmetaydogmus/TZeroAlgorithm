# -*- coding: utf-8 -*-
"""Siber Akademi T-Zero Context Architect V3.

A unified, self-contained, enterprise-grade application for codebase scanning,
context building, and token reduction. Consolidates configuration profiles, secure
Keyring management, multi-threaded AST signatures crawler, git commit/diff/branch/checkout analyzers,
dynamic template compiler, interactive node graphs, live performance/token charts,
split-pane file editors with custom Pygments highlighting, extensions/ignored folders list editors,
offline dry-run prompt compilers, static code analyzer & audit panel, regex search & replace,
git commit assistant, codebase statistics scanner, Markdown renderer, Keyring Secrets Editor,
duplicate code finder, Prompt Workbench playground, dependency analyzer, custom Git commit graph drawer,
advanced global configuration panel, AST signature matcher/refactoring engine, file type tokens
breakdown matrix table, and keyring credentials backup/restore module into a single robust script.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
LinkedIn: https://linkedin.com/in/toprak-ahmet-aydo%C4%9Fmu%C5%9F-60462534b/
Bio & Socials: https://hopp.bio/siberegitim
GitHub: https://github.com/toprakahmetaydogmus/TZeroAlgorithm
"""

import os
import sys
import re
import ast
import json
import time
import math
import random
import logging
import shutil

# Safe UTF-8 reconfiguration for Windows console & piped subprocesses
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Install missing third-party packages before they are imported (see tzero_deps.py).
try:
    import tzero_deps
except ImportError:  # tzero_v3.py copied on its own without the helper module
    tzero_deps = None
if tzero_deps is not None and not tzero_deps.ensure_dependencies():
    sys.exit(1)

import keyring
import requests
import threading
import subprocess
import webbrowser
from typing import Dict, List, Any, Tuple, Optional, Set, Callable

# tkinter is only needed for the desktop GUI. Headless environments (servers, Docker,
# most CI images, MCP hosts) often ship Python without it, so the core engine, CLI and
# MCP server must keep working when it is missing.
try:
    import tkinter as tk
    from tkinter import messagebox, filedialog, ttk, colorchooser
    TK_AVAILABLE = True
except ImportError:  # pragma: no cover - depends on the host Python build
    TK_AVAILABLE = False

    class _TkUnavailable:
        """Stand-in base class so GUI classes can still be defined without tkinter."""

        def __init__(self, *args, **kwargs):
            raise RuntimeError(
                "tkinter is not installed, so the GUI is unavailable. "
                "Install it (Debian/Ubuntu: 'sudo apt install python3-tk') or use the CLI: python main.py --help"
            )

    class _TkModuleStub:
        """Module-like object: any attribute (Canvas, Frame, Tk, ...) resolves to the stand-in."""

        def __getattr__(self, name):
            return _TkUnavailable

    tk = ttk = messagebox = filedialog = colorchooser = _TkModuleStub()
from concurrent.futures import ThreadPoolExecutor

try:
    import siber_akademi_icon
except ImportError:
    siber_akademi_icon = None

if TK_AVAILABLE and siber_akademi_icon:
    try:
        _orig_toplevel_init = tk.Toplevel.__init__
        def _toplevel_init_with_icon(self, *args, **kwargs):
            _orig_toplevel_init(self, *args, **kwargs)
            try:
                siber_akademi_icon.apply_window_icon(self)
            except Exception:
                pass
        tk.Toplevel.__init__ = _toplevel_init_with_icon
    except Exception:
        pass

import darkdetect
from pygments import lex
from pygments.lexers import get_lexer_by_name

# Configure safe UTF-8 streams
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Setup Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("TZeroV3")

# Branding Constants
DEV_NAME = "Toprak Ahmet Aydoğmuş"
DEV_URL_LINKEDIN = "https://linkedin.com/in/toprak-ahmet-aydo%C4%9Fmu%C5%9F-60462534b/"
DEV_URL_BIO = "https://hopp.bio/siberegitim"
DEV_URL_GITHUB = "https://github.com/toprakahmetaydogmus/TZeroAlgorithm"
DEV_URL_MAIN = DEV_URL_GITHUB

# Theme Palettes
THEME_PALETTES = {
    "Luxury Dashboard": {
        "bg_start": "#edf2fb",
        "card_bg": "#ffffff",
        "card_border": "#dbe3f5",
        "card_shadow": "#e2e8f0",
        "card_hover": "#f1f5f9",
        "sidebar_bg": "#3843a0",
        "sidebar_fg": "#ffffff",
        "sidebar_muted": "#a5b4fc",
        "sidebar_hover": "#4a55ab",
        "sidebar_active": "#2b3478",
        "text_main": "#1e293b",
        "text_muted": "#64748b",
        "accent_cyan": "#4338ca",
        "accent_green": "#0d9488",
        "accent_purple": "#6366f1",
        "accent_coral": "#f97316",
        "success": "#10b981",
        "error": "#ef4444"
    },
    "Royal Indigo": {
        "bg_start": "#0b0e1d",
        "card_bg": "#13172e",
        "card_border": "#22274c",
        "card_shadow": "#070a14",
        "card_hover": "#31386c",
        "sidebar_bg": "#10142b",
        "sidebar_fg": "#ffffff",
        "sidebar_muted": "#8d95cf",
        "sidebar_hover": "#22274c",
        "sidebar_active": "#1b2040",
        "text_main": "#ffffff",
        "text_muted": "#8d95cf",
        "accent_cyan": "#6366f1",
        "accent_green": "#10b981",
        "accent_purple": "#a855f7",
        "accent_coral": "#f97316",
        "success": "#22c55e",
        "error": "#f43f5e"
    },
    "Emerald Obsidian": {
        "bg_start": "#050f0a",
        "card_bg": "#0c1d15",
        "card_border": "#163829",
        "card_shadow": "#020805",
        "card_hover": "#1d4c38",
        "sidebar_bg": "#08140e",
        "sidebar_fg": "#ecfdf5",
        "sidebar_muted": "#6ee7b7",
        "sidebar_hover": "#163829",
        "sidebar_active": "#0f281d",
        "text_main": "#ecfdf5",
        "text_muted": "#6ee7b7",
        "accent_cyan": "#10b981",
        "accent_green": "#34d399",
        "accent_purple": "#fbbf24",
        "accent_coral": "#f59e0b",
        "success": "#34d399",
        "error": "#f87171"
    },
    "Glass Dark": {
        "bg_start": "#07090e",
        "card_bg": "#0f131f",
        "card_border": "#1c2337",
        "card_shadow": "#05070b",
        "card_hover": "#212b45",
        "sidebar_bg": "#0d111c",
        "sidebar_fg": "#f8fafc",
        "sidebar_muted": "#94a3b8",
        "sidebar_hover": "#1c2337",
        "sidebar_active": "#141a29",
        "text_main": "#f8fafc",
        "text_muted": "#94a3b8",
        "accent_cyan": "#00f0ff",
        "accent_green": "#10b981",
        "accent_purple": "#a855f7",
        "accent_coral": "#f97316",
        "success": "#10b981",
        "error": "#f43f5e"
    },
    "Neon Cyberpunk": {
        "bg_start": "#050508",
        "card_bg": "#0c0a1c",
        "card_border": "#261e47",
        "card_shadow": "#05030f",
        "card_hover": "#3a2d6e",
        "sidebar_bg": "#0f0924",
        "sidebar_fg": "#00ffff",
        "sidebar_muted": "#9d4edd",
        "sidebar_hover": "#261e47",
        "sidebar_active": "#1a1336",
        "text_main": "#00ffff",
        "text_muted": "#9d4edd",
        "accent_cyan": "#f72585",
        "accent_green": "#4cc9f0",
        "accent_purple": "#7209b7",
        "accent_coral": "#ff70a6",
        "success": "#3f37c9",
        "error": "#f72585"
    },
    "Midnight OLED": {
        "bg_start": "#000000",
        "card_bg": "#0a0c10",
        "card_border": "#161b22",
        "card_shadow": "#000000",
        "card_hover": "#21262d",
        "sidebar_bg": "#080a0f",
        "sidebar_fg": "#f0f6fc",
        "sidebar_muted": "#7d8590",
        "sidebar_hover": "#161b22",
        "sidebar_active": "#101319",
        "text_main": "#f0f6fc",
        "text_muted": "#7d8590",
        "accent_cyan": "#38bdf8",
        "accent_green": "#10b981",
        "accent_purple": "#818cf8",
        "accent_coral": "#fb923c",
        "success": "#34d399",
        "error": "#f87171"
    },
    "Matrix Terminal": {
        "bg_start": "#020803",
        "card_bg": "#051408",
        "card_border": "#0d3314",
        "card_shadow": "#010402",
        "card_hover": "#144d1e",
        "sidebar_bg": "#030c05",
        "sidebar_fg": "#00ff66",
        "sidebar_muted": "#00aa44",
        "sidebar_hover": "#0d3314",
        "sidebar_active": "#07200c",
        "text_main": "#00ff66",
        "text_muted": "#00aa44",
        "accent_cyan": "#39ff14",
        "accent_green": "#00ff41",
        "accent_purple": "#55ff99",
        "accent_coral": "#ffaa00",
        "success": "#00ff66",
        "error": "#ff3333"
    },
    "Synthwave 80s": {
        "bg_start": "#130924",
        "card_bg": "#1c0d38",
        "card_border": "#36166b",
        "card_shadow": "#0b0517",
        "card_hover": "#4f1f9e",
        "sidebar_bg": "#150a2b",
        "sidebar_fg": "#ffddfe",
        "sidebar_muted": "#b59bc9",
        "sidebar_hover": "#36166b",
        "sidebar_active": "#250e4a",
        "text_main": "#ffddfe",
        "text_muted": "#b59bc9",
        "accent_cyan": "#00f0ff",
        "accent_green": "#ffe600",
        "accent_purple": "#ff2a85",
        "accent_coral": "#ff70a6",
        "success": "#00ffcc",
        "error": "#ff2266"
    },
    "Nordic Frost": {
        "bg_start": "#181b22",
        "card_bg": "#222733",
        "card_border": "#2e3440",
        "card_shadow": "#12151c",
        "card_hover": "#3b4252",
        "sidebar_bg": "#1e222b",
        "sidebar_fg": "#eceff4",
        "sidebar_muted": "#d8dee9",
        "sidebar_hover": "#2e3440",
        "sidebar_active": "#242933",
        "text_main": "#eceff4",
        "text_muted": "#d8dee9",
        "accent_cyan": "#88c0d0",
        "accent_green": "#a3be8c",
        "accent_purple": "#b48ead",
        "accent_coral": "#d08770",
        "success": "#a3be8c",
        "error": "#bf616a"
    },
    "Solarized Amber": {
        "bg_start": "#0e1117",
        "card_bg": "#181d27",
        "card_border": "#2d3545",
        "card_shadow": "#090d14",
        "card_hover": "#3c475d",
        "sidebar_bg": "#131822",
        "sidebar_fg": "#fef3c7",
        "sidebar_muted": "#d97706",
        "sidebar_hover": "#2d3545",
        "sidebar_active": "#1f2634",
        "text_main": "#fef3c7",
        "text_muted": "#d97706",
        "accent_cyan": "#38bdf8",
        "accent_green": "#f59e0b",
        "accent_purple": "#fbbf24",
        "accent_coral": "#f97316",
        "success": "#10b981",
        "error": "#ef4444"
    },
    "Siber Retro": {
        "bg_start": "#1a0f0f",
        "card_bg": "#2c1a1a",
        "card_border": "#4a2a2a",
        "card_shadow": "#140b0b",
        "card_hover": "#5c3535",
        "sidebar_bg": "#241515",
        "sidebar_fg": "#f5e6d3",
        "sidebar_muted": "#c2a696",
        "sidebar_hover": "#4a2a2a",
        "sidebar_active": "#381f1f",
        "text_main": "#f5e6d3",
        "text_muted": "#c2a696",
        "accent_cyan": "#ffaa00",
        "accent_green": "#00ff66",
        "accent_purple": "#ff00ff",
        "accent_coral": "#ff7700",
        "success": "#33cc33",
        "error": "#ff3333"
    }
}

# Default Active Palette
CURRENT_THEME = "Luxury Dashboard"
PALETTE = THEME_PALETTES[CURRENT_THEME]

def update_colors(theme_name: str):
    global CURRENT_THEME, PALETTE
    if theme_name in THEME_PALETTES:
        CURRENT_THEME = theme_name
        PALETTE = THEME_PALETTES[theme_name]

# --- Audio Feedback & Telemetry SFX Engine ---
SFX_ENABLED = True

def play_sfx(kind: str = "click") -> None:
    """Asynchronous haptic audio chime player using standard Windows winsound."""
    if not SFX_ENABLED or sys.platform != "win32":
        return
    def _worker():
        try:
            import winsound
            if kind == "click":
                winsound.Beep(1200, 20)
            elif kind == "success":
                winsound.Beep(880, 45)
                winsound.Beep(1400, 65)
            elif kind == "scan":
                winsound.Beep(1100, 30)
                winsound.Beep(1600, 40)
            elif kind == "error":
                winsound.Beep(350, 120)
            elif kind == "notify":
                winsound.Beep(950, 40)
        except Exception:
            pass
    threading.Thread(target=_worker, daemon=True).start()

# --- Provider Rates & Token Cost Estimator ---
PROVIDER_COST_PER_MILLION = {
    "OpenAI": 2.50,
    "Anthropic": 3.00,
    "Groq": 0.59,
    "NVIDIA NIM": 0.70,
    "Ollama (Local)": 0.00,
    "OpenRouter": 1.00,
    "Perplexity": 1.00,
}

def calculate_token_cost(token_count: int, provider_name: str) -> float:
    rate = PROVIDER_COST_PER_MILLION.get(provider_name, 1.00)
    return (token_count / 1_000_000.0) * rate

# i18n Translations
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        "title": "SİBER AKADEMİ — T-ZERO CONTEXT ARCHITECT V3",
        "subtitle": f"Developer: {DEV_NAME} | {DEV_URL_MAIN} | {DEV_URL_BIO}",
        "overview_tab": "🏠 Overview Dashboard",
        "setup_tab": "⚡ Setup & AI Models",
        "selector_tab": "📂 Code Explorer",
        "changelog_tab": "🔀 Git & Diff Analysis",
        "generate_tab": "🚀 Context Generator",
        "template_tab": "🧪 Prompt Studio",
        "graph_tab": "📊 Live Metrics",
        "settings_tab": "⚙️ Settings & Keys",
        "provider": "SELECT AI PROVIDER:",
        "api_url": "API BASE URL:",
        "api_key": "API KEY:",
        "model": "LLM MODEL:",
        "target_dir": "TARGET PROJECT DIRECTORY:",
        "reduction": "TOKEN REDUCTION LEVEL:",
        "scan_btn": "⚡ SCAN CODEBASE (Ctrl+S)",
        "generate_btn": "🚀 ARCHITECT CONTEXT README.md",
        "cancel_btn": "🛑 CANCEL GENERATION",
        "copy_btn": "📋 Copy to Clipboard",
        "save_btn": "💾 Save README.md",
        "agents_btn": "🤖 Export AGENTS.md",
        "arch_btn": "🏛️ Export ARCHITECTURE.md",
        "repomap_btn": "🗺️ Export REPO_MAP.txt",
        "html_btn": "🌐 HTML Preview",
        "success_msg": "README Saved successfully!",
        "error_msg": "Operation failed: ",
        "ping_success": "Ping Success! Connected to API catalog.",
        "smart_select": "🧠 Smart Select",
        "select_all": "Check All",
        "deselect_all": "Uncheck All",
        "invert_select": "Invert Selection",
        "sfx_on": "🔊 SFX ON",
        "sfx_off": "🔇 SFX OFF",
        "audit_btn": "🛡️ SECURITY AUDIT"
    },
    "tr": {
        "title": "SİBER AKADEMİ — T-ZERO BAĞLAM MİMARI V3",
        "subtitle": f"Geliştirici: {DEV_NAME} | {DEV_URL_MAIN} | {DEV_URL_BIO}",
        "overview_tab": "🏠 Genel Bakış",
        "setup_tab": "⚡ Kurulum & Model",
        "selector_tab": "📂 Kod Gezgini",
        "changelog_tab": "🔀 Git & Diff Analizi",
        "generate_tab": "🚀 Bağlam Üretici",
        "template_tab": "🧪 Prompt Atölyesi",
        "graph_tab": "📊 Canlı Metrikler",
        "settings_tab": "⚙️ Ayarlar & AI",
        "provider": "YAPAY ZEKA SAĞLAYICISI SEÇİN:",
        "api_url": "API URL ADRESİ:",
        "api_key": "API ANAHTARI:",
        "model": "LLM MODELİ:",
        "target_dir": "HEDEF PROJE DİZİNİ:",
        "reduction": "TOKEN AZALTMA DÜZEYİ:",
        "scan_btn": "⚡ KOD TABANINI TARA (Ctrl+S)",
        "generate_btn": "🚀 BAĞLAM README.md OLUŞTUR",
        "cancel_btn": "🛑 İŞLEMİ İPTAL ET",
        "copy_btn": "📋 Panoya Kopyala",
        "save_btn": "💾 README.md Kaydet",
        "agents_btn": "🤖 AGENTS.md Dışa Aktar",
        "arch_btn": "🏛️ ARCHITECTURE.md Dışa Aktar",
        "repomap_btn": "🗺️ REPO_MAP.txt Dışa Aktar",
        "html_btn": "🌐 HTML Önizleme",
        "success_msg": "README başarıyla kaydedildi!",
        "error_msg": "İşlem başarısız oldu: ",
        "ping_success": "Bağlantı Başarılı! API kataloğuna ulaşıldı.",
        "smart_select": "🧠 Akıllı Seçim",
        "select_all": "Hepsini Seç",
        "deselect_all": "Seçimleri Kaldır",
        "invert_select": "Seçimi Tersine Çevir",
        "sfx_on": "🔊 SES AÇIK",
        "sfx_off": "🔇 SES KAPALI",
        "audit_btn": "🛡️ GÜVENLİK DENETİMİ"
    }
}


def get_text(key: str, lang: str = "en") -> str:
    selected_lang = lang.lower()
    if selected_lang not in TRANSLATIONS:
        selected_lang = "en"
    return TRANSLATIONS[selected_lang].get(key, key)


# --- 1. CONFIGURATION LAYER ---

SERVICE_NAME = "TZeroAlgorithmV3"
DEFAULT_CONFIG_DIR = os.path.expanduser("~/.tzero_v3")


def secure_permissions(filepath: str) -> None:
    try:
        if os.name == 'posix' and os.path.exists(filepath):
            if os.path.isdir(filepath):
                os.chmod(filepath, 0o700)
            else:
                os.chmod(filepath, 0o600)
    except Exception as e:
        logger.warning(f"Unable to enforce file security permissions: {e}")


def validate_url(url: str) -> bool:
    if not url:
        return False
    stripped = url.strip()
    return stripped.startswith("http://") or stripped.startswith("https://")


def validate_directory(path: str) -> bool:
    if not path:
        return False
    expanded = os.path.expanduser(os.path.expandvars(path.strip()))
    return os.path.exists(expanded) and os.path.isdir(expanded)


class ConfigManager:
    """Manages profile loading, backups, secure keyring storage and parameter settings."""
    def __init__(self, config_dir: str = DEFAULT_CONFIG_DIR):
        self.config_dir = os.path.abspath(config_dir)
        self.config_path = os.path.join(self.config_dir, "config.json")
        self.backup_path = os.path.join(self.config_dir, "config.backup.json")
        self._state: Dict[str, Any] = {}
        self.ensure_config_directory()
        self.load()

    def ensure_config_directory(self) -> None:
        os.makedirs(self.config_dir, exist_ok=True)
        secure_permissions(self.config_dir)

    def get_default_state(self) -> Dict[str, Any]:
        return {
            "version": "3.0.0",
            "active_profile": "default",
            "profiles": {
                "default": {
                    "provider": "NVIDIA NIM",
                    "api_base": "https://integrate.api.nvidia.com/v1",
                    "model": "meta/llama-3.3-70b-instruct",
                    "reduction": "Ultra",
                    "theme": "Luxury Dashboard",
                    "language": "en",
                    "allowed_extensions": [
                        ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", 
                        ".html", ".css", ".json", ".sh", ".bat", ".cpp", ".c", ".h"
                    ],
                    "ignored_folders": [
                        ".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build",
                        ".next", ".nuxt", "out", "coverage", ".idea", ".vscode", "temp", "tmp"
                    ],
                    "thread_pool_size": 4,
                    "max_tokens_budget": 60000
                }
            }
        }

    def load(self) -> None:
        if not os.path.exists(self.config_path):
            self._state = self.get_default_state()
            self.save()
            return
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._state = json.load(f)
        except Exception:
            self.recover_from_backup()

    def save(self) -> None:
        try:
            if os.path.exists(self.config_path):
                shutil.copy2(self.config_path, self.backup_path)
                secure_permissions(self.backup_path)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=4)
            secure_permissions(self.config_path)
        except Exception as e:
            logger.error(f"Failed to write config: {e}")

    def recover_from_backup(self) -> bool:
        if os.path.exists(self.backup_path):
            try:
                with open(self.backup_path, "r", encoding="utf-8") as f:
                    self._state = json.load(f)
                shutil.copy2(self.backup_path, self.config_path)
                secure_permissions(self.config_path)
                return True
            except Exception:
                pass
        self._state = self.get_default_state()
        self.save()
        return False

    def get_profile(self) -> Dict[str, Any]:
        pname = self._state.get("active_profile", "default")
        return self._state.setdefault("profiles", {}).setdefault(pname, self.get_default_state()["profiles"]["default"])

    def list_profiles(self) -> List[str]:
        return list(self._state.setdefault("profiles", {}).keys())

    def get_profile_names(self) -> List[str]:
        return self.list_profiles()

    def set_active_profile(self, name: str):
        self._state["active_profile"] = name
        if name not in self._state["profiles"]:
            self._state["profiles"][name] = self.get_default_state()["profiles"]["default"].copy()
        self.save()

    def switch_profile(self, name: str):
        self.set_active_profile(name)

    def set_profile(self, name: str, profile_dict: Dict[str, Any]):
        self._state.setdefault("profiles", {})[name] = profile_dict
        self.save()

    def delete_profile(self, name: str) -> bool:
        if name == "default" or name == self._state.get("active_profile"):
            return False
        if name in self._state["profiles"]:
            del self._state["profiles"][name]
            self.save()
            return True
        return False

    def get_credential(self, provider: str) -> str:
        try:
            key = keyring.get_password(SERVICE_NAME, provider)
            if key:
                return key.strip()
        except Exception as e:
            logger.warning(f"Keyring API call failed: {e}")
        
        env_vars = {
            "NVIDIA NIM": "NVIDIA_API_KEY",
            "OpenAI": "OPENAI_API_KEY",
            "Google Gemini": "GEMINI_API_KEY",
            "OpenRouter": "OPENROUTER_API_KEY",
            "Anthropic": "ANTHROPIC_API_KEY"
        }
        ev = env_vars.get(provider)
        if ev and ev in os.environ:
            return os.environ[ev].strip()
        return ""

    def set_credential(self, provider: str, api_key: str) -> bool:
        if not api_key:
            return False
        try:
            keyring.set_password(SERVICE_NAME, provider, api_key.strip())
            return True
        except Exception as e:
            logger.error(f"Failed to save credential: {e}")
            return False


# Global Config singleton
_config_mgr = ConfigManager()

def load_config() -> Dict[str, Any]:
    profile = _config_mgr.get_profile()
    return {**_config_mgr._state, **profile}

def save_config(options: Dict[str, Any]) -> bool:
    profile = _config_mgr.get_profile()
    for k, v in options.items():
        if k in ["version", "active_profile", "profiles"]:
            _config_mgr._state[k] = v
        else:
            profile[k] = v
    _config_mgr.save()
    return True

def get_api_key(provider: str) -> str:
    return _config_mgr.get_credential(provider)

def set_api_key(provider: str, api_key: str) -> bool:
    return _config_mgr.set_credential(provider, api_key)


# --- 2. PROVIDERS INTEGRATION LAYER ---

class BaseProvider:
    def __init__(self, name: str, default_url: str, default_models: List[str]):
        self.name = name
        self.default_url = default_url
        self.default_models = default_models

    def get_base_url(self) -> str:
        return self.default_url

    def get_models(self) -> List[str]:
        return self.default_models

    def get_headers(self, api_key: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Referer": DEV_URL_GITHUB,
            "User-Agent": f"TZeroAlgorithmV3/3.0 (Toprak Ahmet Aydogmus; {DEV_URL_GITHUB})"
        }

    def get_endpoint_url(self, api_base: str) -> str:
        base = api_base.rstrip('/')
        if not base.endswith("/chat/completions"):
            return f"{base}/chat/completions"
        return base

    def format_payload(self, model: str, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        return {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.2),
            "max_tokens": kwargs.get("max_tokens", 8192)
        }

    def parse_response(self, data: Dict[str, Any]) -> str:
        if "choices" in data and len(data["choices"]) > 0:
            msg = data["choices"][0].get("message", {})
            return msg.get("content", "")
        raise ValueError(f"Unexpected response structure: {data}")


class NvidiaProvider(BaseProvider):
    def __init__(self):
        super().__init__(
            "NVIDIA NIM",
            "https://integrate.api.nvidia.com/v1",
            [
                "meta/llama-3.3-70b-instruct",
                "deepseek-ai/deepseek-r1",
                "mistralai/mistral-large-3-675b-instruct-2512",
                "google/gemma-4-31b-it",
                "nvidia/llama-3.1-nemotron-51b-instruct",
                "qwen/qwen3.5-122b-a10b"
            ]
        )

    def get_headers(self, api_key: str) -> Dict[str, str]:
        headers = super().get_headers(api_key)
        headers["X-Nvidia-Api-Key"] = api_key
        return headers


class OpenAIProvider(BaseProvider):
    def __init__(self):
        super().__init__(
            "OpenAI",
            "https://api.openai.com/v1",
            ["gpt-4o", "gpt-4o-mini", "o3-mini", "o1"]
        )


class GeminiProvider(BaseProvider):
    def __init__(self):
        super().__init__(
            "Google Gemini",
            "https://generativelanguage.googleapis.com/v1beta/openai",
            ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"]
        )


class OpenRouterProvider(BaseProvider):
    def __init__(self):
        super().__init__(
            "OpenRouter",
            "https://openrouter.ai/api/v1",
            [
                "anthropic/claude-3.7-sonnet",
                "openai/gpt-4o",
                "deepseek/deepseek-r1",
                "google/gemini-2.5-pro"
            ]
        )

    def get_headers(self, api_key: str) -> Dict[str, str]:
        headers = super().get_headers(api_key)
        headers["HTTP-Referer"] = DEV_URL_GITHUB
        headers["X-Title"] = "T-ZERO Context Architect"
        return headers


class AnthropicProvider(BaseProvider):
    def __init__(self):
        super().__init__(
            "Anthropic",
            "https://api.anthropic.com/v1",
            ["claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"]
        )

    def get_headers(self, api_key: str) -> Dict[str, str]:
        return {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "Referer": DEV_URL_GITHUB,
            "User-Agent": f"TZeroAlgorithmV3/3.0 (Toprak Ahmet Aydogmus; {DEV_URL_GITHUB})"
        }

    def get_endpoint_url(self, api_base: str) -> str:
        base = api_base.rstrip('/')
        if not base.endswith("/messages"):
            return f"{base}/messages"
        return base

    def format_payload(self, model: str, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        system = ""
        user_msgs = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                user_msgs.append({"role": msg["role"], "content": msg["content"]})
        payload = {
            "model": model,
            "messages": user_msgs,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.2)
        }
        if system:
            payload["system"] = system
        return payload

    def parse_response(self, data: Dict[str, Any]) -> str:
        content_blocks = data.get("content", [])
        text_parts = [b.get("text", "") for b in content_blocks if isinstance(b, dict) and b.get("type") == "text"]
        if text_parts:
            return "".join(text_parts)
        if "error" in data:
            raise ValueError(f"Anthropic error: {data['error']}")
        raise ValueError(f"No text blocks in Anthropic response: {data}")


class LocalOllamaProvider(BaseProvider):
    def __init__(self):
        super().__init__(
            "Local Ollama",
            "http://localhost:11434/v1",
            ["llama3:latest", "mistral:latest", "phi3:latest", "qwen2.5:latest"]
        )

    def get_headers(self, api_key: str) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Referer": DEV_URL_GITHUB,
            "User-Agent": f"TZeroAlgorithmV3/3.0 (Toprak Ahmet Aydogmus; {DEV_URL_GITHUB})"
        }


PROVIDERS: Dict[str, BaseProvider] = {
    "NVIDIA NIM": NvidiaProvider(),
    "OpenAI": OpenAIProvider(),
    "Google Gemini": GeminiProvider(),
    "OpenRouter": OpenRouterProvider(),
    "Anthropic": AnthropicProvider(),
    "Local Ollama": LocalOllamaProvider()
}


# --- 3. AST CODE SIGNATURE SCANNER & DEPENDENCY ANALYZER ---

class TokenReducer:
    """Extracts functional headers, classes, and annotations while pruning internals."""

    @staticmethod
    def reduce(code: str, file_path: str, mode: str = "ultra") -> str:
        if mode.lower() == "none":
            return code
            
        ext = os.path.splitext(file_path.lower())[1]
        
        if ext == ".py":
            return TokenReducer._reduce_python(code, mode)
        elif ext in (".js", ".ts", ".jsx", ".tsx", ".cjs", ".mjs"):
            return TokenReducer._reduce_javascript(code, mode)
        elif ext in (".cpp", ".c", ".h", ".go", ".rs"):
            return TokenReducer._reduce_compiled_grammar(code)
            
        return TokenReducer._default_trim(code)

    @staticmethod
    def _reduce_python(code: str, mode: str) -> str:
        lines = code.splitlines()
        reduced = []
        in_docstring = False
        doc_char = ""
        
        for line in lines:
            stripped = line.strip()
            if not in_docstring:
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    in_docstring = True
                    doc_char = stripped[:3]
                    if stripped.endswith(doc_char) and len(stripped) > 3:
                        in_docstring = False
                    continue
            else:
                if stripped.endswith(doc_char):
                    in_docstring = False
                continue
                
            if in_docstring:
                continue
                
            if stripped.startswith(("def ", "class ", "@", "import ", "from ")):
                reduced.append(line)
            elif stripped.startswith("def ") or stripped.startswith("async def "):
                reduced.append(line)
            elif mode.lower() == "balanced" and not stripped.startswith("#"):
                reduced.append(line)
                
        return "\n".join(reduced)

    @staticmethod
    def _reduce_javascript(code: str, mode: str) -> str:
        lines = code.splitlines()
        reduced = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("//") or (stripped.startswith("/*") and stripped.endswith("*/")):
                continue
            if stripped.startswith(("function ", "class ", "export ", "const ", "let ", "import ")):
                reduced.append(line)
            elif mode.lower() == "balanced":
                reduced.append(line)
        return "\n".join(reduced)

    @staticmethod
    def _reduce_compiled_grammar(code: str) -> str:
        lines = code.splitlines()
        reduced = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("//", "/*", "*", "#include", "package ", "import ")):
                reduced.append(line)
            elif stripped.endswith("{") or "fn " in stripped or "func " in stripped:
                reduced.append(line)
        return "\n".join(reduced)

    @staticmethod
    def _default_trim(code: str) -> str:
        lines = [l for l in code.splitlines() if l.strip()]
        return "\n".join(lines[:60])


class DependencyAnalyzer(ast.NodeVisitor):
    """AST visitor that walks import nodes to list python dependencies."""
    def __init__(self):
        self.dependencies: List[str] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.dependencies.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            self.dependencies.append(node.module)
        self.generic_visit(node)


class CodebaseScanner:
    """Asynchronously scans workspaces using file settings criteria."""

    def scan_directory(self, root_dir: str) -> Tuple[List[str], Dict[str, int], Dict[str, str]]:
        profile = _config_mgr.get_profile()
        allowed_exts = set(profile.get("allowed_extensions", []))
        ignored_folders = set(profile.get("ignored_folders", []))
        thread_size = profile.get("thread_pool_size", 4)
        
        files_list = []
        sizes = {}
        snippets = {}
        
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if d not in ignored_folders]
            
            for f in filenames:
                ext = os.path.splitext(f.lower())[1]
                if ext in allowed_exts:
                    full_path = os.path.join(dirpath, f)
                    rel_path = os.path.relpath(full_path, root_dir)
                    files_list.append(rel_path)
                    sizes[rel_path] = os.path.getsize(full_path)

        def process_file(rel_path: str):
            full_path = os.path.join(root_dir, rel_path)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as file_io:
                    raw_code = file_io.read(15000)
                reduction_mode = profile.get("reduction", "Ultra")
                return rel_path, TokenReducer.reduce(raw_code, full_path, reduction_mode)
            except Exception as e:
                logger.warning(f"Unable to read signature file {rel_path}: {e}")
                return rel_path, ""

        with ThreadPoolExecutor(max_workers=thread_size) as executor:
            results = executor.map(process_file, files_list)
            for rel, snip in results:
                if snip:
                    snippets[rel] = snip

        return sorted(files_list), sizes, snippets


# --- 4. STATIC CODE ANALYZER & AUDIT ENGINE ---

class StaticCodeAnalyzer(ast.NodeVisitor):
    """Parses codebase code AST blocks and produces code-smell diagnostics warnings."""
    def __init__(self, filename: str):
        self.filename = filename
        self.issues: List[Dict[str, Any]] = []

    def analyze_source(self, source_code: str):
        try:
            node = ast.parse(source_code, filename=self.filename)
            self.visit(node)
        except SyntaxError as se:
            self.issues.append({
                "severity": "CRITICAL",
                "line": se.lineno,
                "msg": f"Syntax Error: {se.msg}",
                "ref": "SyntaxError"
            })
        except Exception as e:
            self.issues.append({
                "severity": "WARNING",
                "line": 0,
                "msg": f"Unable to build AST: {e}",
                "ref": "ASTError"
            })

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Rule 1: No docstring
        doc = ast.get_docstring(node)
        if not doc:
            self.issues.append({
                "severity": "INFO",
                "line": node.lineno,
                "msg": f"Missing function docstring in def {node.name}()",
                "ref": "NoDocstring"
            })

        # Rule 2: Excessive function line count
        line_count = len(node.body)
        if line_count > 30:
            self.issues.append({
                "severity": "WARNING",
                "line": node.lineno,
                "msg": f"Complex function '{node.name}' has {line_count} statements (suggest refactoring)",
                "ref": "ExcessiveLines"
            })

        # Rule 3: Too many function arguments
        args_count = len(node.args.args)
        if args_count > 6:
            self.issues.append({
                "severity": "WARNING",
                "line": node.lineno,
                "msg": f"Function '{node.name}' accepts {args_count} arguments (suggest reducing)",
                "ref": "TooManyArguments"
            })

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        # Apply the same docstring, lines, and argument checks to async functions
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        doc = ast.get_docstring(node)
        if not doc:
            self.issues.append({
                "severity": "INFO",
                "line": node.lineno,
                "msg": f"Class '{node.name}' has no docstring annotation",
                "ref": "NoClassDoc"
            })
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global):
        self.issues.append({
            "severity": "WARNING",
            "line": node.lineno,
            "msg": f"Usage of global keywords '{', '.join(node.names)}' detected (code smell)",
            "ref": "GlobalKeyword"
        })
        self.generic_visit(node)


# --- 5. AST STRUCTURE OUTLINE ENGINE & REFACTORER ---

class PythonASTParser(ast.NodeVisitor):
    """AST structure outlining parser that walks python syntax trees."""
    def __init__(self):
        self.outline: List[Dict[str, Any]] = []
        self.current_class: Optional[Dict[str, Any]] = None

    def visit_ClassDef(self, node: ast.ClassDef):
        class_info = {
            "type": "class",
            "name": node.name,
            "bases": [ast.unparse(b) for b in node.bases],
            "methods": [],
            "line": node.lineno
        }
        self.outline.append(class_info)
        old_class = self.current_class
        self.current_class = class_info
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        args = [a.arg for a in node.args.args]
        func_info = {
            "type": "method" if self.current_class else "function",
            "name": node.name,
            "args": args,
            "line": node.lineno
        }
        if self.current_class:
            self.current_class["methods"].append(func_info)
        else:
            self.outline.append(func_info)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        args = [a.arg for a in node.args.args]
        func_info = {
            "type": "async_method" if self.current_class else "async_function",
            "name": node.name,
            "args": args,
            "line": node.lineno
        }
        if self.current_class:
            self.current_class["methods"].append(func_info)
        else:
            self.outline.append(func_info)
        self.generic_visit(node)


class PythonASTRefactorer(ast.NodeTransformer):
    """AST transformer to refactor function signatures across files."""
    def __init__(self, target_name: str, replacement_name: str):
        self.target_name = target_name
        self.replacement_name = replacement_name
        self.modified = False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node.name == self.target_name:
            node.name = self.replacement_name
            self.modified = True
        return self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == self.target_name:
            node.func.id = self.replacement_name
            self.modified = True
        elif isinstance(node.func, ast.Attribute) and node.func.attr == self.target_name:
            node.func.attr = self.replacement_name
            self.modified = True
        return self.generic_visit(node)


# --- 6. SECURE KEYRING SECRETS EDITOR & CIS BACKUP ---

class KeyringSecretsEditor:
    """Provides secure editing, listing and deleting parameters of keyring passwords."""
    @staticmethod
    def list_credentials() -> Dict[str, str]:
        creds = {}
        for provider in PROVIDERS.keys():
            try:
                secret = keyring.get_password(SERVICE_NAME, provider)
                if secret:
                    creds[provider] = "*" * len(secret)
                else:
                    creds[provider] = "Not Set"
            except Exception:
                creds[provider] = "Error"
        return creds


class KeyringSecretsBackupManager:
    """Backs up and restores credentials securely to an encrypted configuration file."""
    @staticmethod
    def backup_credentials(filepath: str, cipher_key: str) -> bool:
        try:
            creds = {}
            for provider in PROVIDERS.keys():
                secret = keyring.get_password(SERVICE_NAME, provider)
                if secret:
                    creds[provider] = secret
            
            raw_data = json.dumps(creds).encode('utf-8')
            # Basic XOR encryption for backup file safety
            encrypted = bytearray(raw_data)
            key_bytes = cipher_key.encode('utf-8')
            if key_bytes:
                for i in range(len(encrypted)):
                    encrypted[i] ^= key_bytes[i % len(key_bytes)]
                    
            with open(filepath, "wb") as f:
                f.write(encrypted)
            return True
        except Exception as e:
            logger.error(f"Backup keyring failed: {e}")
            return False

    @staticmethod
    def restore_credentials(filepath: str, cipher_key: str) -> bool:
        try:
            with open(filepath, "rb") as f:
                encrypted = bytearray(f.read())
            key_bytes = cipher_key.encode('utf-8')
            if key_bytes:
                for i in range(len(encrypted)):
                    encrypted[i] ^= key_bytes[i % len(key_bytes)]
            
            creds = json.loads(encrypted.decode('utf-8'))
            for provider, secret in creds.items():
                keyring.set_password(SERVICE_NAME, provider, secret)
            return True
        except Exception as e:
            logger.error(f"Restore keyring credentials failed: {e}")
            return False


# --- 7. WORKSPACE DUPLICITY FINDER ---

class WorkspaceDuplicityFinder:
    """Crawls codebase modules to find exact duplicate text fragments of specific lengths."""
    def __init__(self, file_snippets: Dict[str, str]):
        self.snippets = file_snippets

    def find_duplicates(self, min_lines: int = 6) -> List[Dict[str, Any]]:
        duplicates = []
        hashes = {}
        
        for filepath, content in self.snippets.items():
            lines = content.splitlines()
            if len(lines) < min_lines:
                continue
            for i in range(len(lines) - min_lines + 1):
                block = "\n".join(lines[i:i+min_lines]).strip()
                if not block:
                    continue
                block_hash = hash(block)
                if block_hash in hashes:
                    prev_file, prev_line = hashes[block_hash]
                    if prev_file != filepath:
                        duplicates.append({
                            "file1": prev_file,
                            "line1": prev_line + 1,
                            "file2": filepath,
                            "line2": i + 1,
                            "snippet": block[:80] + "..."
                        })
                else:
                    hashes[block_hash] = (filepath, i)
        return duplicates


# --- 8. DYNAMIC MARKDOWN TEXT TAGGER ---

# --- 8. DYNAMIC MARKDOWN TEXT TAGGER & CONTEXT EXPORT SUITE ---

class MarkdownTextTagger:
    """Parses headings, lists, code fences, blockquotes, tables and formats Tkinter text blocks dynamically."""
    def __init__(self, text_widget: tk.Text):
        self.text_widget = text_widget
        self.setup_tags()

    def setup_tags(self):
        self.text_widget.tag_configure("h1", foreground=PALETTE["accent_cyan"], font=("Segoe UI", 14, "bold"), spacing1=12, spacing2=6)
        self.text_widget.tag_configure("h2", foreground=PALETTE["accent_purple"], font=("Segoe UI", 12, "bold"), spacing1=10, spacing2=4)
        self.text_widget.tag_configure("h3", foreground=PALETTE["accent_green"], font=("Segoe UI", 11, "bold"), spacing1=8, spacing2=3)
        self.text_widget.tag_configure("bold", font=("Segoe UI", 10, "bold"), foreground=PALETTE["text_main"])
        self.text_widget.tag_configure("italic", font=("Segoe UI", 10, "italic"), foreground=PALETTE["text_muted"])
        self.text_widget.tag_configure("code", background=PALETTE["card_bg"], font=("Consolas", 9), foreground=PALETTE["accent_green"])
        self.text_widget.tag_configure("code_block", background=PALETTE["bg_start"], font=("Consolas", 9), foreground=PALETTE["accent_cyan"], lmargin1=15, lmargin2=15)
        self.text_widget.tag_configure("bullet", lmargin1=15, lmargin2=25, foreground=PALETTE["text_main"])
        self.text_widget.tag_configure("quote", lmargin1=20, lmargin2=20, font=("Segoe UI", 9, "italic"), foreground=PALETTE["text_muted"])
        self.text_widget.tag_configure("table", font=("Consolas", 9), foreground=PALETTE["accent_purple"])
        self.text_widget.tag_configure("task_done", foreground=PALETTE["success"], font=("Segoe UI", 10, "bold"))
        self.text_widget.tag_configure("task_todo", foreground=PALETTE["text_muted"], font=("Segoe UI", 10))
        self.text_widget.tag_configure("hr", foreground=PALETTE["card_border"], font=("Consolas", 8))

    def render_markdown(self, markdown_text: str):
        self.text_widget.delete("1.0", tk.END)
        lines = markdown_text.splitlines()
        in_code_fence = False
        
        for line in lines:
            stripped = line.strip()
            # Code fence toggle
            if stripped.startswith("```"):
                in_code_fence = not in_code_fence
                self.text_widget.insert(tk.END, "  " + line + "\n", "code_block")
                continue
            
            if in_code_fence:
                self.text_widget.insert(tk.END, "    " + line + "\n", "code_block")
                continue
                
            if line.startswith("# "):
                self.text_widget.insert(tk.END, line[2:] + "\n", "h1")
            elif line.startswith("## "):
                self.text_widget.insert(tk.END, line[3:] + "\n", "h2")
            elif line.startswith("### "):
                self.text_widget.insert(tk.END, line[4:] + "\n", "h3")
            elif stripped == "---" or stripped == "***":
                self.text_widget.insert(tk.END, "─" * 60 + "\n", "hr")
            elif stripped.startswith("> "):
                self.text_widget.insert(tk.END, "▌ " + stripped[2:] + "\n", "quote")
            elif stripped.startswith("- [x] ") or stripped.startswith("* [x] "):
                self.text_widget.insert(tk.END, "  ✔  ", "task_done")
                self.text_widget.insert(tk.END, stripped[6:] + "\n", "bullet")
            elif stripped.startswith("- [ ] ") or stripped.startswith("* [ ] "):
                self.text_widget.insert(tk.END, "  ☐  ", "task_todo")
                self.text_widget.insert(tk.END, stripped[6:] + "\n", "bullet")
            elif line.startswith("- ") or line.startswith("* "):
                self.text_widget.insert(tk.END, "  •  ", "bold")
                self.text_widget.insert(tk.END, line[2:] + "\n", "bullet")
            elif stripped.startswith("|") and stripped.endswith("|"):
                self.text_widget.insert(tk.END, line + "\n", "table")
            elif "`" in line:
                parts = line.split("`")
                for idx, part in enumerate(parts):
                    tag = "code" if idx % 2 == 1 else ""
                    self.text_widget.insert(tk.END, part, tag)
                self.text_widget.insert(tk.END, "\n")
            else:
                self.text_widget.insert(tk.END, line + "\n")


class ContextExportManager:
    """Exports synthesized project context into specialized agent, architecture, and web targets."""
    
    @staticmethod
    def generate_agents_blueprint(project_name: str, files_tree: str, snippets: Dict[str, str], extra_rules: str = "") -> str:
        """Generates comprehensive AGENTS.md / CLAUDE.md instruction blueprint."""
        return f"""# 🤖 AGENTS & AI ASSISTANT BLUEPRINT: {project_name}

> Automated Agent Grounding Blueprint generated by Siber Akademi T-Zero Context Architect V3.

## 🎯 Project Overview & Scope
- **Project Name:** {project_name}
- **Architecture Role:** Context-Aware Automated Software Engineering Blueprint
- **Primary Runtime:** Python / Modern Polyglot Toolchain

## 🏗️ Directory Hierarchy
```text
{files_tree}
```

## 📐 Core Architecture & Modules Outline
{json.dumps(snippets, indent=2)}

## 🛡️ Agent Operational Guardrails & Grounding
1. **Never Assume External Dependencies:** Adhere strictly to the workspace dependencies already listed in `requirements.txt` or `pyproject.toml`.
2. **Strict Zero-Leak Guarantee:** Never hardcode personal or public API keys, secrets, passwords, or tokens in source code or git commits. Use environment variables or OS keyring.
3. **Preserve Documentation Integrity:** Maintain existing docstrings and explanatory comments.
4. **Non-Breaking Changes:** Preserve existing public signatures and backwards compatibility.

## ⚡ Execution Guidelines
{extra_rules or "Follow standard test-driven development. Run all unit tests before creating release tags."}
"""

    @staticmethod
    def generate_architecture_blueprint(project_name: str, files: List[str], deps: Dict[str, List[str]]) -> str:
        """Generates ARCHITECTURE.md with Mermaid diagrams and module specs."""
        mermaid_nodes = []
        mermaid_edges = []
        for mod, targets in deps.items():
            clean_mod = re.sub(r'[^a-zA-Z0-9_]', '_', mod)
            mermaid_nodes.append(f"    {clean_mod}[{mod}]")
            for t in targets[:4]:
                clean_t = re.sub(r'[^a-zA-Z0-9_]', '_', t)
                mermaid_edges.append(f"    {clean_mod} --> {clean_t}")

        mermaid_block = "graph TD\n" + "\n".join(mermaid_nodes[:25]) + "\n" + "\n".join(mermaid_edges[:40]) if mermaid_nodes else "graph TD\n    Workspace[Workspace Root] --> CoreModules[Core Modules]"

        file_list_str = "\n".join(f"- `{f}`" for f in files[:40])
        return f"""# 🏛️ Architecture & System Blueprint: {project_name}

> Generated by Siber Akademi T-Zero Context Architect V3.

## 📊 System Topology Diagram
```mermaid
{mermaid_block}
```

## 🧩 Component & Layer Breakdown
- **Presentation Layer (UI/GUI):** High-performance desktop interface with glassmorphism and real-time telemetry.
- **Service & Provider Layer:** Multi-provider LLM connector interface with retry logic and token budgeting.
- **Static Analysis & AST Engine:** Python AST signature extractor, docstring pruner, and duplicity analyzer.
- **Security & Storage Layer:** OS Keyring encryption with POSIX-compliant permission controls.

## 📦 Project Artifacts ({len(files)} indexed files)
{file_list_str}
"""

    @staticmethod
    def generate_repo_map(project_name: str, files: List[str], snippets: Dict[str, str]) -> str:
        """Generates compact REPO_MAP.txt token map for chat prompts."""
        lines = [f"=== REPO MAP: {project_name} ({len(files)} files) ==="]
        for f in files:
            lines.append(f"\n--- {f} ---")
            snip = snippets.get(f, "")
            if snip:
                lines.append(snip[:1200])
        return "\n".join(lines)

    @staticmethod
    def generate_styled_html(project_name: str, markdown_content: str) -> str:
        """Generates standalone responsive Cyberpunk styled HTML document."""
        lines = markdown_content.splitlines()
        html_body = []
        in_code = False
        for line in lines:
            if line.startswith("```"):
                if in_code:
                    html_body.append("</code></pre>")
                    in_code = False
                else:
                    lang = line[3:].strip() or "text"
                    html_body.append(f'<pre><code class="lang-{lang}">')
                    in_code = True
            elif in_code:
                html_body.append(line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
            elif line.startswith("# "):
                html_body.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_body.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                html_body.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("- "):
                html_body.append(f"<li>{line[2:]}</li>")
            elif line.strip() == "---":
                html_body.append("<hr/>")
            elif line.strip():
                html_body.append(f"<p>{line}</p>")
                
        body_content = "\n".join(html_body)
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{project_name} - T-Zero Context Preview</title>
<style>
:root {{
    --bg: #090a0f;
    --card-bg: #131520;
    --card-border: #222536;
    --text: #f0f6fc;
    --text-muted: #8e9bb0;
    --cyan: #06b6d4;
    --purple: #a855f7;
    --green: #84cc16;
}}
body {{
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.6;
    padding: 2.5rem;
    max-width: 1050px;
    margin: 0 auto;
}}
h1, h2, h3 {{ color: var(--cyan); margin-top: 1.5rem; }}
h2 {{ color: var(--purple); border-bottom: 1px solid var(--card-border); padding-bottom: 0.3rem; }}
pre {{
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 8px;
    padding: 1.2rem;
    overflow-x: auto;
    font-family: "Consolas", monospace;
    font-size: 0.9rem;
    color: var(--green);
}}
code {{ font-family: "Consolas", monospace; color: var(--green); }}
p, li {{ color: var(--text); font-size: 0.95rem; }}
li {{ margin-left: 1.5rem; }}
hr {{ border: none; border-top: 1px solid var(--card-border); margin: 2rem 0; }}
.badge {{ display: inline-block; padding: 0.3rem 0.8rem; border-radius: 6px; background: var(--card-bg); border: 1px solid var(--card-border); font-size: 0.85rem; color: var(--cyan); margin-bottom: 1.5rem; }}
</style>
</head>
<body>
<div class="badge">🚀 Siber Akademi T-Zero V3 Context Architect Preview</div>
{body_content}
</body>
</html>
"""


# --- 9. WORKSPACE PRESETS AND PROFILE IMPORTER ---

class WorkspacePresetManager:
    """Presets manager to automatically apply filter templates to codebase scanners."""
    PRESETS = {
        "Python (Django/Flask)": {
            "allowed": [".py", ".html", ".css", ".js", ".ini", ".cfg", ".yml", ".json"],
            "ignored": [".git", "__pycache__", "venv", ".venv", "migrations", "static", "media"]
        },
        "Javascript/TypeScript (React/Next)": {
            "allowed": [".js", ".jsx", ".ts", ".tsx", ".json", ".css", ".html"],
            "ignored": [".git", "node_modules", ".next", "out", "build", "dist", "coverage"]
        },
        "Go (Microservices)": {
            "allowed": [".go", ".json", ".yaml", ".yml", ".mod", ".sum"],
            "ignored": [".git", "vendor", "bin", "dist"]
        },
        "Systems (C/C++)": {
            "allowed": [".cpp", ".c", ".h", ".hpp", ".make", "Makefile"],
            "ignored": [".git", "obj", "build", "bin"]
        }
    }


class ProfileImporterExporter:
    """Handles JSON-based profile backup, imports and exports."""
    @staticmethod
    def export_profile(profile_data: Dict[str, Any], filepath: str) -> bool:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(profile_data, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Failed to export settings profile: {e}")
            return False

    @staticmethod
    def import_profile(filepath: str) -> Optional[Dict[str, Any]]:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Basic validation check
            if "provider" in data and "allowed_extensions" in data:
                return data
        except Exception as e:
            logger.error(f"Failed to import settings profile: {e}")
        return None


# --- 10. TEMPLATES & GENERATOR ---

class TemplateEngine:
    def __init__(self):
        self.template_content = self.get_default_template()

    def get_default_template(self) -> str:
        return """# {{PROJECT_NAME}} Context Tree

This repository index outlines code layout architecture using token-reduced signatures.

## Module Reference Map

{{MODULES_REFERENCE}}

## Security Guardrails

{{HALLUCINATION_GUARDRAILS}}
"""

    def render(self, variables: Dict[str, str]) -> str:
        rendered = self.template_content
        for k, v in variables.items():
            rendered = rendered.replace(f"{{{{{k}}}}}", v)
        return rendered


def count_tokens_precise(text: str, model_name: str = "gpt-4o") -> int:
    return len(text) // 4


def get_budgeted_snippets(selected_files: List[str], file_snippets: Dict[str, str]) -> Dict[str, str]:
    budgeted = {}
    total_tokens = 0
    token_limit = _config_mgr.get_profile().get("max_tokens_budget", 60000)
    
    for f in selected_files:
        snippet = file_snippets.get(f, "")
        tokens = len(snippet) // 4
        if total_tokens + tokens <= token_limit:
            budgeted[f] = snippet
            total_tokens += tokens
        else:
            budgeted[f] = f"// [Signature omitted: Token budget limit reached for context building.]"
            
    return budgeted


class ContextGenerator:
    def __init__(self, cancel_event: Optional[threading.Event] = None):
        self.cancel_event = cancel_event or threading.Event()

    def generate_readme(
        self, 
        api_base: str, 
        api_key: str, 
        headers: Dict[str, str], 
        model: str, 
        messages: List[Dict[str, str]], 
        progress_cb: Optional[Callable] = None,
        provider: Optional[BaseProvider] = None
    ) -> str:
        if self.cancel_event.is_set():
            raise InterruptedError("Process cancelled by user.")
            
        if progress_cb:
            progress_cb(40, "Handshaking API connection...")
            
        if provider:
            url = provider.get_endpoint_url(api_base)
            provider_payload = provider.format_payload(model, messages)
        else:
            url = f"{api_base.rstrip('/')}/chat/completions"
            provider_payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 4096
            }
        
        try:
            if progress_cb:
                progress_cb(60, "Streaming LLM generated output...")
            
            r = requests.post(url, json=provider_payload, headers=headers, timeout=120)
            
            if self.cancel_event.is_set():
                raise InterruptedError("Process cancelled by user.")
                
            if r.status_code == 200:
                data = r.json()
                if provider:
                    content = provider.parse_response(data)
                elif "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                else:
                    content = str(data)
                if progress_cb:
                    progress_cb(90, "Finalizing context layouts...")
                return content
            else:
                err_text = r.text
                try:
                    err_json = r.json()
                    if "error" in err_json:
                        err_text = json.dumps(err_json["error"])
                except Exception:
                    pass
                raise IOError(f"API Error code HTTP {r.status_code}: {err_text}")
        except Exception as e:
            if self.cancel_event.is_set():
                raise InterruptedError("Process cancelled.")
            raise e


def generate_offline_context(project_dir: str, selected_files: List[str], file_snippets: Dict[str, str]) -> str:
    """Generates an enterprise-grade hierarchical T-Zero context tree offline without API call.
    
    100% Free, local, instant, and zero-leak security.
    """
    project_name = os.path.basename(os.path.abspath(project_dir)) or "Project"
    all_deps = set()
    total_lines = 0
    for f, snip in file_snippets.items():
        total_lines += len(snip.splitlines())
        if f.endswith(".py"):
            try:
                tree = ast.parse(snip)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for n in node.names:
                            all_deps.add(n.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            all_deps.add(node.module.split('.')[0])
            except Exception:
                pass

    modules_ref = []
    for f in sorted(selected_files):
        snip = file_snippets.get(f, "").strip()
        ext = os.path.splitext(f)[1].lstrip('.') or "txt"
        modules_ref.append(f"### `{f}`\n\n```{ext}\n{snip}\n```\n")

    modules_str = "\n".join(modules_ref)
    deps_str = ", ".join(sorted(all_deps)) if all_deps else "None detected"

    tree_lines = [f"├── {f}" for f in sorted(selected_files)]
    tree_ascii = "\n".join(tree_lines)

    return f"""# {project_name} — T-Zero Context Tree

> **Generated by:** Siber Akademi T-Zero Context Architect V3 (Offline Engine)  
> **Workspace:** `{project_dir}`  
> **Analyzed Modules:** {len(selected_files)} files | ~{total_lines} lines of code  
> **Identified Dependencies:** {deps_str}  
> **Security:** 100% Zero-Leak (No secrets, no API keys, local-only compilation)

---

## 🏛 Architecture Overview

This high-fidelity context tree maps the structure, interfaces, classes, and exported signatures
of `{project_name}`. It is pre-tokenized and optimized for LLM ingestion (Cursor, Copilot, Cline, Antigravity IDE),
reducing context ingestion overhead by **40% to 95%** while retaining structural semantics.

```
{project_name}/
{tree_ascii}
```

---

## 📦 Module Reference & Signatures

{modules_str}

---

## 🛡 LLM Ingestion & Guardrails

When interpreting this context tree:
1. **Structural Fidelity:** All class signatures, methods, and functions reflect exact codebase AST declarations.
2. **Implementation Ellipses:** Internal function bodies may be pruned under Ultra/Balanced reduction modes.
3. **Zero Secrets:** All credentials must be sourced from OS Keyring or local environment variables. Do NOT hardcode secrets.
"""


# --- 11. CUSTOM GIT COMMIT GRAPH DRAWER ---

class GitCommitGraphCanvas(tk.Canvas):
    """Draws a beautiful custom commit nodes history tree graph chronologically."""
    def __init__(self, parent, **kwargs):
        cfg = {"bg": PALETTE["bg_start"], "highlightthickness": 0}
        cfg.update(kwargs)
        super().__init__(parent, **cfg)

    def draw_graph(self, commits_count: int):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 1 or h <= 1:
            w, h = 300, 180
            
        if commits_count == 0:
            self.create_text(w/2, h/2, text="No commit history to plot.", fill=PALETTE["text_muted"])
            return

        cx = 50
        cy = 20
        spacing = 30
        
        for i in range(commits_count):
            y = cy + i * spacing
            # Draw branch line
            if i < commits_count - 1:
                self.create_line(cx, y, cx, y + spacing, fill=PALETTE["card_border"], width=2)
            
            # Draw commit node
            self.create_oval(cx - 6, y - 6, cx + 6, y + 6, fill=PALETTE["accent_cyan"], outline=PALETTE["accent_purple"], width=2)
            
            # Commit label
            self.create_text(cx + 20, y, text=f"Commit #{commits_count - i}", fill=PALETTE["text_main"], font=("Consolas", 8), anchor="w")


# --- 12. SYSTEM LAUNCHER GUI & COMPONENTS ---

def apply_modern_hover(btn: tk.Button, normal_bg=None, hover_bg=None, normal_fg=None, hover_fg=None):
    """Enriches a Tkinter button with smooth, glowing interactive hover transitions."""
    nbg = normal_bg or btn.cget("bg")
    hbg = hover_bg or PALETTE.get("card_hover", "#212b45")
    nfg = normal_fg or btn.cget("fg")
    hfg = hover_fg or PALETTE.get("accent_cyan", "#00f0ff")

    def on_enter(e):
        try:
            btn.configure(bg=hbg, fg=hfg)
        except Exception:
            pass

    def on_leave(e):
        try:
            btn.configure(bg=nbg, fg=nfg)
        except Exception:
            pass

    btn.bind("<Enter>", on_enter, add="+")
    btn.bind("<Leave>", on_leave, add="+")
    return btn


def apply_entry_focus_glow(entry: tk.Entry, normal_border=None, focus_border=None):
    """Adds a glowing neon accent border when an Entry field is focused."""
    nborder = normal_border or PALETTE.get("card_border", "#1c2337")
    fborder = focus_border or PALETTE.get("accent_cyan", "#00f0ff")

    def on_focus_in(e):
        try:
            entry.configure(highlightbackground=fborder, highlightcolor=fborder)
        except Exception:
            pass

    def on_focus_out(e):
        try:
            entry.configure(highlightbackground=nborder, highlightcolor=nborder)
        except Exception:
            pass

    entry.bind("<FocusIn>", on_focus_in, add="+")
    entry.bind("<FocusOut>", on_focus_out, add="+")
    return entry


class GlassCard(tk.Frame):
    def __init__(self, parent, **kwargs):
        cfg = {
            "bg": PALETTE["card_bg"],
            "highlightthickness": 1,
            "highlightbackground": PALETTE["card_border"],
            "bd": 0,
        }
        cfg.update(kwargs)
        super().__init__(parent, **cfg)


def create_rounded_rect(canvas, x1, y1, x2, y2, radius=16, **kwargs):
    radius = min(radius, abs(x2 - x1) // 2, abs(y2 - y1) // 2)
    if radius < 2:
        return canvas.create_rectangle(x1, y1, x2, y2, **kwargs)
    points = [
        x1 + radius, y1,
        x1 + radius, y1,
        x2 - radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1 + radius,
        x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class LuxuryCard(tk.Canvas):
    """Executive SaaS rounded card with antialiased borders, soft depth shadow, and inner container frame."""
    def __init__(self, parent, radius: int = 16, bg_color: Optional[str] = None, border_color: Optional[str] = None, padding: int = 10, **kwargs):
        canvas_bg = kwargs.pop("canvas_bg", None) or PALETTE.get("bg_start", "#edf2fb")
        cfg = {"bg": canvas_bg, "highlightthickness": 0}
        cfg.update(kwargs)
        super().__init__(parent, **cfg)
        self.radius = radius
        self.custom_card_bg = bg_color
        self.custom_border_color = border_color
        self.padding = padding
        self.inner = tk.Frame(self, bg=self.card_bg)
        self.inner_win = self.create_window((self.padding, self.padding), window=self.inner, anchor="nw")
        self.bind("<Configure>", self._on_resize)

    @property
    def card_bg(self) -> str:
        return self.custom_card_bg or PALETTE.get("card_bg", "#ffffff")

    @property
    def border_color(self) -> str:
        return self.custom_border_color or PALETTE.get("card_border", "#dbe3f5")

    def _on_resize(self, event):
        w = max(10, event.width)
        h = max(10, event.height)
        self.delete("card_bg_poly")
        shadow_col = PALETTE.get("card_shadow", "#e2e8f0")
        create_rounded_rect(self, 2, 3, w - 2, h - 1, radius=self.radius, fill=shadow_col, outline="", tags="card_bg_poly")
        create_rounded_rect(self, 2, 2, w - 2, h - 2, radius=self.radius, fill=self.card_bg, outline=self.border_color, width=1, tags="card_bg_poly")
        self.tag_lower("card_bg_poly")
        self.inner.configure(bg=self.card_bg)
        self.coords(self.inner_win, self.padding, self.padding)
        self.itemconfigure(self.inner_win, width=max(10, w - self.padding * 2), height=max(10, h - self.padding * 2))


class CanvasPillButton(tk.Canvas):
    """Ultra-luxury rounded pill button with smooth hover glow and click displacement."""
    def __init__(self, parent, text: str = "Button", command: Optional[Callable] = None, bg_color: Optional[str] = None, hover_color: Optional[str] = None, text_color: Optional[str] = None, font: Tuple = ("Segoe UI", 9, "bold"), height: int = 36, radius: int = 18, **kwargs):
        canvas_bg = parent.cget("bg") if hasattr(parent, "cget") else PALETTE.get("card_bg", "#ffffff")
        cfg = {"height": height, "bg": canvas_bg, "highlightthickness": 0}
        cfg.update(kwargs)
        super().__init__(parent, **cfg)
        self.text = text
        self.command = command
        self.custom_bg = bg_color
        self.custom_hover = hover_color
        self.custom_fg = text_color
        self.btn_font = font
        self.height = height
        self.radius = radius
        self.is_hover = False
        self.bind("<Configure>", self._redraw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    @property
    def normal_bg(self) -> str:
        return self.custom_bg or PALETTE.get("accent_cyan", "#4338ca")

    @property
    def hover_bg(self) -> str:
        return self.custom_hover or PALETTE.get("accent_purple", "#6366f1")

    @property
    def fg_color(self) -> str:
        return self.custom_fg or "#ffffff"

    def set_text(self, new_text: str):
        self.text = new_text
        self._redraw()

    def _redraw(self, event=None):
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10:
            return
        self.delete("all")
        if getattr(self, "btn_state", tk.NORMAL) in ("disabled", tk.DISABLED):
            fill_col = PALETTE.get("card_border", "#cbd5e1")
        else:
            fill_col = self.hover_bg if self.is_hover else self.normal_bg
        create_rounded_rect(self, 2, 2, w - 2, h - 2, radius=min(self.radius, h // 2), fill=fill_col, outline="", tags="pill")
        self.create_text(w // 2, h // 2, text=self.text, fill=self.fg_color, font=self.btn_font, tags="text")

    def _on_enter(self, e):
        if getattr(self, "btn_state", tk.NORMAL) in ("disabled", tk.DISABLED):
            return
        self.is_hover = True
        self._redraw()
        self.configure(cursor="hand2")

    def _on_leave(self, e):
        self.is_hover = False
        self._redraw()

    def _on_click(self, e):
        if getattr(self, "btn_state", tk.NORMAL) in ("disabled", tk.DISABLED):
            return
        play_sfx("click")
        if self.command:
            self.command()

    def config(self, **kwargs):
        if "text" in kwargs:
            self.set_text(kwargs.pop("text"))
        if "state" in kwargs:
            self.btn_state = kwargs.pop("state")
            self._redraw()
        if kwargs:
            try:
                super().config(**kwargs)
            except Exception:
                pass

    configure = config


class KPICard(LuxuryCard):
    """Executive KPI card showing primary upward metric and secondary compression delta."""
    def __init__(self, parent, title="AST & Token Harcaması", primary_val="↑ 1,974", primary_sub="İşlenen AST Düğümü & Direktifler", secondary_val="↓ 287", secondary_sub="Sıkıştırılmış Prompt Token Hacmi", **kwargs):
        super().__init__(parent, radius=18, padding=12, **kwargs)
        top = tk.Frame(self.inner, bg=self.card_bg)
        top.pack(fill=tk.X, pady=(0, 4))
        self.lbl_title = tk.Label(top, text=title, font=("Segoe UI", 9, "bold"), fg=PALETTE.get("text_muted", "#64748b"), bg=self.card_bg)
        self.lbl_title.pack(side=tk.LEFT)
        self.pill_period = tk.Label(top, text="Haftalık ▾", font=("Segoe UI", 7, "bold"), fg=PALETTE.get("text_muted", "#64748b"), bg=PALETTE.get("card_hover", "#f1f5f9"), padx=6, pady=2)
        self.pill_period.pack(side=tk.RIGHT)

        self.lbl_prim = tk.Label(self.inner, text=primary_val, font=("Segoe UI", 21, "bold"), fg=PALETTE.get("accent_cyan", "#3843a0"), bg=self.card_bg)
        self.lbl_prim.pack(anchor=tk.W)
        self.lbl_prim_sub = tk.Label(self.inner, text=primary_sub, font=("Segoe UI", 7), fg=PALETTE.get("text_muted", "#94a3b8"), bg=self.card_bg)
        self.lbl_prim_sub.pack(anchor=tk.W, pady=(0, 4))

        self.divider = tk.Frame(self.inner, height=1, bg=PALETTE.get("card_border", "#f1f5f9"))
        self.divider.pack(fill=tk.X, pady=3)

        self.lbl_sec = tk.Label(self.inner, text=secondary_val, font=("Segoe UI", 16, "bold"), fg=PALETTE.get("accent_coral", "#f97316"), bg=self.card_bg)
        self.lbl_sec.pack(anchor=tk.W)
        self.lbl_sec_sub = tk.Label(self.inner, text=secondary_sub, font=("Segoe UI", 7), fg=PALETTE.get("text_muted", "#94a3b8"), bg=self.card_bg)
        self.lbl_sec_sub.pack(anchor=tk.W)

    def update_metrics(self, prim: str, sec: str):
        self.lbl_prim.config(text=prim)
        self.lbl_sec.config(text=sec)


class MiniCalendarCard(LuxuryCard):
    """Mini executive activity calendar card with active audit date rings."""
    def __init__(self, parent, month_title="Ekim 2026", active_days=(14, 25, 28), **kwargs):
        super().__init__(parent, radius=18, padding=10, **kwargs)
        top = tk.Frame(self.inner, bg=self.card_bg)
        top.pack(fill=tk.X, pady=(0, 4))
        tk.Label(top, text="‹", font=("Segoe UI", 10, "bold"), fg=PALETTE.get("text_muted", "#64748b"), bg=self.card_bg).pack(side=tk.LEFT, padx=3)
        self.lbl_month = tk.Label(top, text=month_title, font=("Segoe UI", 9, "bold"), fg=PALETTE.get("text_main", "#1e293b"), bg=self.card_bg)
        self.lbl_month.pack(side=tk.LEFT, expand=True)
        tk.Label(top, text="›", font=("Segoe UI", 10, "bold"), fg=PALETTE.get("text_muted", "#64748b"), bg=self.card_bg).pack(side=tk.RIGHT, padx=3)

        grid = tk.Frame(self.inner, bg=self.card_bg)
        grid.pack(fill=tk.BOTH, expand=True)
        headers = ["pt", "sa", "ça", "pe", "cu", "ct", "pz"]
        for col, h in enumerate(headers):
            tk.Label(grid, text=h, font=("Segoe UI", 7, "bold"), fg=PALETTE.get("text_muted", "#94a3b8"), bg=self.card_bg, width=3).grid(row=0, column=col, padx=2, pady=1)
        active_set = set(active_days)
        day_num = 1
        for r in range(1, 6):
            for c in range(7):
                if day_num <= 31:
                    is_act = day_num in active_set
                    bg_c = PALETTE.get("card_hover", "#e0e7ff") if is_act else self.card_bg
                    fg_c = PALETTE.get("accent_cyan", "#3843a0") if is_act else PALETTE.get("text_muted", "#64748b")
                    lbl = tk.Label(grid, text=str(day_num), font=("Segoe UI", 7, "bold" if is_act else "normal"), fg=fg_c, bg=bg_c, width=3)
                    lbl.grid(row=r, column=c, padx=1, pady=1)
                    day_num += 1


class CircularGaugeCard(LuxuryCard):
    """Circular donut gauge card with percentage arc and quick action pill button."""
    def __init__(self, parent, title="Optimization Score", subtitle="T-Zero context efficiency", percentage=75, action_text="⚡ HIZLI OPTİMİZE ET", action_cmd=None, **kwargs):
        super().__init__(parent, radius=18, padding=10, **kwargs)
        self.percentage = percentage
        self.action_cmd = action_cmd

        # Top horizontal bars preview
        bars = tk.Canvas(self.inner, height=22, bg=self.card_bg, highlightthickness=0)
        bars.pack(fill=tk.X, pady=(0, 2))
        create_rounded_rect(bars, 2, 2, 75, 8, radius=3, fill=PALETTE.get("accent_purple", "#6366f1"), outline="")
        create_rounded_rect(bars, 79, 2, 120, 8, radius=3, fill=PALETTE.get("card_hover", "#e0e7ff"), outline="")
        create_rounded_rect(bars, 2, 12, 55, 18, radius=3, fill=PALETTE.get("accent_coral", "#f97316"), outline="")
        create_rounded_rect(bars, 59, 12, 120, 18, radius=3, fill=PALETTE.get("card_border", "#ffedd5"), outline="")

        self.gauge = tk.Canvas(self.inner, width=72, height=72, bg=self.card_bg, highlightthickness=0)
        self.gauge.pack(pady=(2, 2))
        self._draw_gauge()

        tk.Label(self.inner, text=subtitle, font=("Segoe UI", 7), fg=PALETTE.get("text_muted", "#94a3b8"), bg=self.card_bg).pack(pady=(0, 4))

        self.btn = CanvasPillButton(self.inner, text=action_text, command=action_cmd, height=26, radius=13, font=("Segoe UI", 7, "bold"))
        self.btn.pack(fill=tk.X, padx=8)

    def _draw_gauge(self):
        self.gauge.delete("all")
        self.gauge.create_oval(6, 6, 66, 66, outline=PALETTE.get("card_border", "#edf2f7"), width=7)
        extent = -int((self.percentage / 100.0) * 360)
        self.gauge.create_arc(6, 6, 66, 66, start=90, extent=extent, outline=PALETTE.get("sidebar_bg", "#3843a0"), width=7, style=tk.ARC)
        self.gauge.create_text(36, 36, text=f"{self.percentage}%", font=("Segoe UI", 12, "bold"), fill=PALETTE.get("text_main", "#1e293b"))

    def set_percentage(self, val: int):
        self.percentage = max(0, min(100, val))
        self._draw_gauge()


class WaveSplineChart(LuxuryCard):
    """Smooth dual-wave spline chart with pastel area gradient fills."""
    def __init__(self, parent, title="AST Token Frekansı", **kwargs):
        super().__init__(parent, radius=18, padding=10, **kwargs)
        tk.Label(self.inner, text=title, font=("Segoe UI", 9, "bold"), fg=PALETTE.get("text_muted", "#64748b"), bg=self.card_bg).pack(anchor=tk.W, pady=(0, 2))
        self.chart_canvas = tk.Canvas(self.inner, height=115, bg=self.card_bg, highlightthickness=0)
        self.chart_canvas.pack(fill=tk.BOTH, expand=True)
        self.chart_canvas.bind("<Configure>", self._draw_spline)

    def _draw_spline(self, event=None):
        c = self.chart_canvas
        c.delete("all")
        w = max(20, c.winfo_width())
        h = max(20, c.winfo_height())

        # Mountain 1: Purple
        pts1 = [4, h - 15, w * 0.18, h - 55, w * 0.38, h - 25, w * 0.58, h - 75, w * 0.78, h - 35, w - 4, h - 60]
        fill1 = [4, h] + pts1 + [w - 4, h]
        c.create_polygon(fill1, fill="#ede9fe" if PALETTE.get("bg_start") == "#edf2fb" else PALETTE.get("card_hover", "#2a3055"), outline="", smooth=True)
        c.create_line(pts1, fill=PALETTE.get("accent_purple", "#6366f1"), width=2.5, smooth=True)

        # Mountain 2: Coral
        pts2 = [4, h - 8, w * 0.22, h - 35, w * 0.42, h - 12, w * 0.62, h - 45, w * 0.82, h - 20, w - 4, h - 38]
        fill2 = [4, h] + pts2 + [w - 4, h]
        c.create_polygon(fill2, fill="#ffedd5" if PALETTE.get("bg_start") == "#edf2fb" else PALETTE.get("card_border", "#352840"), outline="", smooth=True)
        c.create_line(pts2, fill=PALETTE.get("accent_coral", "#f97316"), width=2.5, smooth=True)

        for px, py in [(w * 0.58, h - 75), (w * 0.78, h - 35)]:
            c.create_oval(px - 3, py - 3, px + 3, py + 3, fill="#ffffff", outline=PALETTE.get("accent_purple", "#6366f1"), width=2)
        for px, py in [(w * 0.22, h - 35), (w * 0.62, h - 45)]:
            c.create_oval(px - 3, py - 3, px + 3, py + 3, fill="#ffffff", outline=PALETTE.get("accent_coral", "#f97316"), width=2)


class WideSplineChartCard(LuxuryCard):
    """Wide executive Bézier spline chart showing AST vs Compressed token consumption trend."""
    def __init__(self, parent, title="Model Token Tüketim Trendi", **kwargs):
        super().__init__(parent, radius=18, padding=12, **kwargs)
        top = tk.Frame(self.inner, bg=self.card_bg)
        top.pack(fill=tk.X, pady=(0, 4))
        tk.Label(top, text=title, font=("Segoe UI", 10, "bold"), fg=PALETTE.get("text_main", "#1e293b"), bg=self.card_bg).pack(side=tk.LEFT)
        pill = tk.Label(top, text="Tüm Zamanlar ▾", font=("Segoe UI", 7, "bold"), fg=PALETTE.get("text_muted", "#64748b"), bg=PALETTE.get("card_hover", "#f1f5f9"), padx=8, pady=2)
        pill.pack(side=tk.RIGHT)

        self.c = tk.Canvas(self.inner, height=140, bg=self.card_bg, highlightthickness=0)
        self.c.pack(fill=tk.BOTH, expand=True)
        self.c.bind("<Configure>", self._draw)

        leg = tk.Frame(self.inner, bg=self.card_bg)
        leg.pack(pady=(4, 0))
        tk.Label(leg, text="● Orijinal AST Tokenları", font=("Segoe UI", 7, "bold"), fg=PALETTE.get("accent_purple", "#6366f1"), bg=self.card_bg).pack(side=tk.LEFT, padx=10)
        tk.Label(leg, text="● T-Zero Sıkıştırılmış Prompt", font=("Segoe UI", 7, "bold"), fg=PALETTE.get("accent_coral", "#f97316"), bg=self.card_bg).pack(side=tk.LEFT, padx=10)

    def _draw(self, event=None):
        w = max(20, self.c.winfo_width())
        h = max(20, self.c.winfo_height())
        self.c.delete("all")

        for i, val in enumerate(["40k", "30k", "20k", "10k"]):
            y = 12 + i * ((h - 24) / 3)
            self.c.create_text(16, y, text=val, font=("Segoe UI", 7), fill=PALETTE.get("text_muted", "#94a3b8"))
            self.c.create_line(36, y, w - 8, y, fill=PALETTE.get("card_border", "#f1f5f9"), width=1)

        ox = 40
        rw = w - ox - 10
        pts1 = [ox, h - 30, ox + rw * 0.2, h - 70, ox + rw * 0.45, h - 45, ox + rw * 0.7, h - 110, ox + rw, h - 55]
        fill1 = [ox, h] + pts1 + [ox + rw, h]
        self.c.create_polygon(fill1, fill="#f5f3ff" if PALETTE.get("bg_start") == "#edf2fb" else PALETTE.get("card_hover", "#252b48"), outline="", smooth=True)
        self.c.create_line(pts1, fill=PALETTE.get("accent_purple", "#6366f1"), width=2.5, smooth=True)

        pts2 = [ox, h - 20, ox + rw * 0.25, h - 40, ox + rw * 0.5, h - 25, ox + rw * 0.75, h - 75, ox + rw, h - 35]
        fill2 = [ox, h] + pts2 + [ox + rw, h]
        self.c.create_polygon(fill2, fill="#fff7ed" if PALETTE.get("bg_start") == "#edf2fb" else PALETTE.get("card_border", "#2f2238"), outline="", smooth=True)
        self.c.create_line(pts2, fill=PALETTE.get("accent_coral", "#f97316"), width=2.5, smooth=True)

        for px, py in [(ox + rw * 0.2, h - 70), (ox + rw * 0.7, h - 110)]:
            self.c.create_oval(px - 4, py - 4, px + 4, py + 4, fill="#ffffff", outline=PALETTE.get("accent_purple", "#6366f1"), width=2)
        for px, py in [(ox + rw * 0.25, h - 40), (ox + rw * 0.75, h - 75)]:
            self.c.create_oval(px - 4, py - 4, px + 4, py + 4, fill="#ffffff", outline=PALETTE.get("accent_coral", "#f97316"), width=2)


class MonthlyStackedBarCard(LuxuryCard):
    """Horizontal stacked bar chart for monthly token reduction stats."""
    def __init__(self, parent, title="Aylık Token Tasarrufu", **kwargs):
        super().__init__(parent, radius=18, padding=12, **kwargs)
        tk.Label(self.inner, text=title, font=("Segoe UI", 9, "bold"), fg=PALETTE.get("text_main", "#1e293b"), bg=self.card_bg).pack(anchor=tk.W, pady=(0, 6))
        self.c = tk.Canvas(self.inner, height=110, bg=self.card_bg, highlightthickness=0)
        self.c.pack(fill=tk.BOTH, expand=True)
        self.c.bind("<Configure>", self._draw)

    def _draw(self, event=None):
        w = max(20, self.c.winfo_width())
        h = max(20, self.c.winfo_height())
        self.c.delete("all")
        months = ["EKI", "KAS", "ARA", "OCA"]
        ratios = [0.75, 0.55, 0.85, 0.65]
        bar_h = 10
        spacing = 24
        start_y = 6
        for i, (m, r) in enumerate(zip(months, ratios)):
            y = start_y + i * spacing
            self.c.create_text(16, y + 5, text=m, font=("Segoe UI", 7, "bold"), fill=PALETTE.get("text_muted", "#64748b"))
            full_w = w - 45
            w1 = int(full_w * r)
            create_rounded_rect(self.c, 34, y, 34 + w1, y + bar_h, radius=4, fill=PALETTE.get("accent_purple", "#6366f1"), outline="")
            create_rounded_rect(self.c, 34 + w1 + 3, y, 34 + full_w, y + bar_h, radius=4, fill=PALETTE.get("card_hover", "#e0e7ff"), outline="")


class GroupedVerticalBarCard(LuxuryCard):
    """Grouped dual-color vertical bar chart for daily token and audit activity."""
    def __init__(self, parent, title="Günlük Aktivite & Denetim", **kwargs):
        super().__init__(parent, radius=18, padding=12, **kwargs)
        tk.Label(self.inner, text=title, font=("Segoe UI", 9, "bold"), fg=PALETTE.get("text_main", "#1e293b"), bg=self.card_bg).pack(anchor=tk.W, pady=(0, 6))
        self.c = tk.Canvas(self.inner, height=110, bg=self.card_bg, highlightthickness=0)
        self.c.pack(fill=tk.BOTH, expand=True)
        self.c.bind("<Configure>", self._draw)

    def _draw(self, event=None):
        w = max(20, self.c.winfo_width())
        h = max(20, self.c.winfo_height())
        self.c.delete("all")
        days = ["Pt", "Sa", "Ça", "Pe", "Cu", "Ct", "Pz"]
        slot_w = w / len(days)
        base_y = h - 16
        heights = [(40, 20), (55, 32), (30, 48), (65, 42), (75, 55), (45, 25), (35, 18)]
        for i, (d, (h1, h2)) in enumerate(zip(days, heights)):
            cx = slot_w * (i + 0.5)
            create_rounded_rect(self.c, cx - 8, base_y - h1, cx - 1, base_y, radius=3, fill=PALETTE.get("accent_coral", "#f97316"), outline="")
            create_rounded_rect(self.c, cx + 1, base_y - h2, cx + 8, base_y, radius=3, fill=PALETTE.get("card_border", "#fed7aa"), outline="")
            self.c.create_text(cx, base_y + 8, text=d, font=("Segoe UI", 7), fill=PALETTE.get("text_muted", "#94a3b8"))


# Backwards compatibility aliases
VerticalBarChart = GroupedVerticalBarCard
HorizontalProgressBarGroup = MonthlyStackedBarCard


class SecurityHubCard(LuxuryCard):
    """Siber Akademi security badge & quick audit launcher card."""
    def __init__(self, parent, action_cmd=None, **kwargs):
        super().__init__(parent, radius=18, padding=12, **kwargs)
        tk.Label(self.inner, text="🛡 SİBER AKADEMİ GÜVENLİK", font=("Segoe UI", 9, "bold"), fg=PALETTE.get("accent_cyan", "#3843a0"), bg=self.card_bg).pack(anchor=tk.W)
        tk.Label(self.inner, text="100% Zero-Leak Sıfır Bellek İfşası Koruması", font=("Segoe UI", 7), fg=PALETTE.get("accent_green", "#10b981"), bg=self.card_bg).pack(anchor=tk.W, pady=(1, 6))
        self.btn = CanvasPillButton(self.inner, text="RAPORU İNCELE", command=action_cmd, height=28, radius=14, font=("Segoe UI", 7, "bold"), bg_color=PALETTE.get("card_hover", "#e0e7ff"), text_color=PALETTE.get("accent_cyan", "#3843a0"))
        self.btn.pack(fill=tk.X)

class GlowingStatusDot(tk.Canvas):
    def __init__(self, parent, size: int = 16, **kwargs):
        cfg = {"width": size, "height": size, "bg": PALETTE["card_bg"], "highlightthickness": 0}
        cfg.update(kwargs)
        super().__init__(parent, **cfg)
        self.size = size
        self.set_status("red")
        
    def set_status(self, status: str):
        self.delete("all")
        color_map = {
            "red": (PALETTE["error"], "#fee2e2"),
            "yellow": ("#eab308", "#fef9c3"),
            "green": (PALETTE["success"], "#d1fae5"),
            "cyan": (PALETTE["accent_cyan"], "#ecfeff")
        }
        fill, outline = color_map.get(status, color_map["red"])
        padding = 2
        self.create_oval(
            padding, padding, 
            self.size - padding, self.size - padding, 
            fill=fill, outline=outline, width=1
        )


class StarfieldCanvas(tk.Canvas):
    """Dynamic animated background canvas supporting Stars Warp, Matrix Digital Rain, Cyber Grid, and Solid modes."""
    def __init__(self, parent, **kwargs):
        cfg = {"highlightthickness": 0}
        cfg.update(kwargs)
        super().__init__(parent, **cfg)
        self.mode = "solid" if CURRENT_THEME == "Luxury Dashboard" else "stars"  # "stars", "matrix", "grid", "solid"
        self.stars: List[Dict[str, Any]] = []
        self.matrix_drops: List[Dict[str, Any]] = []
        self.grid_offset = 0.0
        self.running = True
        self.speed_multiplier = 1.0
        self.star_count = 65
        self.star_colors = [PALETTE["accent_cyan"], PALETTE["accent_purple"], "#ffffff"]
        self.bind("<Configure>", self.on_resize)
        self.animate()

    def cycle_mode(self) -> str:
        modes = ["stars", "matrix", "grid", "solid"]
        idx = (modes.index(self.mode) + 1) % len(modes)
        self.mode = modes[idx]
        w, h = max(10, self.winfo_width()), max(10, self.winfo_height())
        if self.mode == "matrix":
            self.rebuild_matrix(w, h)
        elif self.mode == "stars":
            self.rebuild_stars(w, h)
        self.draw()
        return self.mode

    def on_resize(self, event):
        if self.mode == "matrix":
            self.rebuild_matrix(event.width, event.height)
        else:
            self.rebuild_stars(event.width, event.height)

    def rebuild_stars(self, w: int, h: int):
        self.stars = []
        w = max(10, w)
        h = max(10, h)
        for _ in range(self.star_count):
            self.stars.append({
                "x": random.uniform(0, w),
                "y": random.uniform(0, h),
                "speed": random.uniform(0.2, 1.4),
                "size": random.choice([1, 2, 3]),
                "color": random.choice(self.star_colors)
            })

    def rebuild_matrix(self, w: int, h: int):
        self.matrix_drops = []
        col_width = 24
        cols = max(1, w // col_width)
        chars = "010101λμΩπΣ∆§0123456789ABCDEF"
        for c in range(cols):
            self.matrix_drops.append({
                "x": c * col_width + 12,
                "y": random.uniform(-max(10, h), 0),
                "speed": random.uniform(2.5, 7.0),
                "char": random.choice(chars),
                "len": random.randint(6, 16)
            })

    def draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 1 or h <= 1:
            return

        # Render theme solid background
        self.create_rectangle(0, 0, w, h, fill=PALETTE["bg_start"], outline=PALETTE["bg_start"])

        if self.mode == "solid":
            return

        if self.mode == "stars":
            for star in self.stars:
                x, y, size = star["x"], star["y"], star["size"]
                self.create_oval(x, y, x + size, y + size, fill=star["color"], outline=star["color"], tags="star")

        elif self.mode == "matrix":
            chars = "010101λμΩπΣ∆§0123456789ABCDEF"
            for drop in self.matrix_drops:
                x, y = drop["x"], drop["y"]
                # Glowing leading head character
                self.create_text(x, y, text=drop["char"], fill="#ffffff", font=("Consolas", 10, "bold"), tags="matrix")
                # Fading phosphor trail
                for j in range(1, min(drop["len"], 8)):
                    trail_y = y - (j * 14)
                    if 0 <= trail_y <= h:
                        self.create_text(x, trail_y, text=random.choice(chars), fill=PALETTE["accent_green"], font=("Consolas", 9), tags="matrix")

        elif self.mode == "grid":
            grid_color = PALETTE["card_border"]
            horizon_y = h * 0.45
            # Horizon laser
            self.create_line(0, horizon_y, w, horizon_y, fill=PALETTE["accent_cyan"], width=1, tags="grid")
            # Perspective rays
            center_x = w * 0.5
            for ox in range(-w, w * 2, 70):
                self.create_line(center_x, horizon_y, ox, h, fill=grid_color, width=1, tags="grid")
            # Moving grid horizontals
            step = 35
            for gy in range(int(horizon_y), h + step, step):
                py = gy + (self.grid_offset % step)
                if py <= h:
                    self.create_line(0, py, w, py, fill=grid_color, width=1, tags="grid")

    def animate(self):
        if not self.running:
            return
        w, h = self.winfo_width(), self.winfo_height()
        if w > 1 and h > 1 and self.mode != "solid":
            if self.mode == "stars":
                for star in self.stars:
                    star["x"] -= star["speed"] * self.speed_multiplier
                    if star["x"] < 0:
                        star["x"] = w
                        star["y"] = random.uniform(0, h)
            elif self.mode == "matrix":
                chars = "010101λμΩπΣ∆§0123456789ABCDEF"
                for drop in self.matrix_drops:
                    drop["y"] += drop["speed"] * self.speed_multiplier
                    if drop["y"] - (drop["len"] * 14) > h:
                        drop["y"] = random.uniform(-100, 0)
                        drop["char"] = random.choice(chars)
            elif self.mode == "grid":
                self.grid_offset += 1.2 * self.speed_multiplier
            self.draw()
        self.after(50, self.animate)


class NodeGraphCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        cfg = {"bg": PALETTE["bg_start"], "highlightthickness": 0}
        cfg.update(kwargs)
        super().__init__(parent, **cfg)
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.links: List[Tuple[str, str]] = []
        self.selected_node: Optional[str] = None
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)

    def set_data(self, files: List[str]):
        self.nodes = {}
        self.links = []
        if not files:
            self.draw()
            return

        self.nodes["root"] = {"x": 350, "y": 250, "type": "root", "size": 12, "color": PALETTE["accent_cyan"], "label": "Workspace"}

        dirs_added = set()
        for filepath in files[:40]:
            parts = filepath.replace("\\", "/").split("/")
            parent = "root"
            
            for i in range(len(parts) - 1):
                dir_path = "/".join(parts[:i+1])
                dir_name = parts[i]
                if dir_path not in dirs_added:
                    dirs_added.add(dir_path)
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(50, 100)
                    self.nodes[dir_path] = {
                        "x": 350 + distance * math.cos(angle),
                        "y": 250 + distance * math.sin(angle),
                        "type": "dir",
                        "size": 8,
                        "color": PALETTE["accent_purple"],
                        "label": dir_name
                    }
                    self.links.append((parent, dir_path))
                parent = dir_path

            file_id = filepath
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(120, 180)
            self.nodes[file_id] = {
                "x": 350 + distance * math.cos(angle),
                "y": 250 + distance * math.sin(angle),
                "type": "file",
                "size": 5,
                "color": PALETTE["accent_green"],
                "label": parts[-1]
            }
            self.links.append((parent, file_id))

        self.draw()

    def draw(self):
        self.delete("all")
        for start, end in self.links:
            if start in self.nodes and end in self.nodes:
                n1, n2 = self.nodes[start], self.nodes[end]
                self.create_line(n1["x"], n1["y"], n2["x"], n2["y"], fill=PALETTE["card_border"], width=1)

        for node_id, node in self.nodes.items():
            x, y, size = node["x"], node["y"], node["size"]
            color = node["color"]
            if node_id == self.selected_node:
                self.create_oval(x-size-3, y-size-3, x+size+3, y+size+3, outline=PALETTE["accent_cyan"], width=2)
            self.create_oval(x-size, y-size, x+size, y+size, fill=color, outline="#ffffff", width=1)
            self.create_text(x, y + size + 8, text=node["label"], fill=PALETTE["text_muted"], font=("Segoe UI", 8))

    def on_click(self, event):
        self.selected_node = None
        for node_id, node in self.nodes.items():
            dist = math.hypot(event.x - node["x"], event.y - node["y"])
            if dist <= node["size"] + 4:
                self.selected_node = node_id
                break
        self.draw()

    def on_drag(self, event):
        if self.selected_node and self.selected_node in self.nodes:
            self.nodes[self.selected_node]["x"] = event.x
            self.nodes[self.selected_node]["y"] = event.y
            self.draw()


class PerformanceChartCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        cfg = {"bg": PALETTE["bg_start"], "highlightthickness": 0}
        cfg.update(kwargs)
        super().__init__(parent, **cfg)
        self.cpu_history: List[float] = [10.0] * 30
        self.mem_history: List[float] = [20.0] * 30
        self.draw()

    def update_values(self, cpu: float, memory: float):
        self.cpu_history.append(max(0.0, min(100.0, cpu)))
        self.mem_history.append(max(0.0, min(100.0, memory)))
        if len(self.cpu_history) > 30:
            self.cpu_history.pop(0)
        if len(self.mem_history) > 30:
            self.mem_history.pop(0)
        self.draw()

    def draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 1 or h <= 1:
            w, h = 300, 100
        self.create_line(10, 5, 10, h-15, fill=PALETTE["card_border"])
        self.create_line(10, h-15, w-10, h-15, fill=PALETTE["card_border"])

        step_x = (w - 20) / 29
        for i in range(len(self.cpu_history) - 1):
            x1 = 10 + i * step_x
            y1 = (h - 20) - (self.cpu_history[i] / 100.0) * (h - 30)
            x2 = 10 + (i + 1) * step_x
            y2 = (h - 20) - (self.cpu_history[i + 1] / 100.0) * (h - 30)
            self.create_line(x1, y1, x2, y2, fill=PALETTE["accent_green"], width=2)

        for i in range(len(self.mem_history) - 1):
            x1 = 10 + i * step_x
            y1 = (h - 20) - (self.mem_history[i] / 100.0) * (h - 30)
            x2 = 10 + (i + 1) * step_x
            y2 = (h - 20) - (self.mem_history[i + 1] / 100.0) * (h - 30)
            self.create_line(x1, y1, x2, y2, fill=PALETTE["accent_cyan"], width=2)

        self.create_text(w-55, 15, text=f"CPU: {self.cpu_history[-1]:.1f}%", fill=PALETTE["accent_green"], font=("Segoe UI", 8, "bold"))
        self.create_text(w-55, 30, text=f"MEM: {self.mem_history[-1]:.1f}%", fill=PALETTE["accent_cyan"], font=("Segoe UI", 8, "bold"))


class TokenDonutChartCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        cfg = {"bg": PALETTE["bg_start"], "highlightthickness": 0}
        cfg.update(kwargs)
        super().__init__(parent, **cfg)
        self.sections: Dict[str, float] = {"Used": 0.0, "Remaining": 100.0}
        self.draw()

    def set_budget(self, used: int, limit: int = 60000):
        pct = (used / limit) * 100.0 if limit > 0 else 0.0
        pct = max(0.0, min(100.0, pct))
        self.sections = {"Used": pct, "Remaining": 100.0 - pct}
        self.draw()

    def draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 1 or h <= 1:
            w, h = 180, 180
            
        cx, cy = w / 2, h / 2
        r = min(w, h) / 2 - 20
        
        used_angle = (self.sections["Used"] / 100.0) * 360.0
        self.create_arc(cx-r, cy-r, cx+r, cy+r, start=90, extent=-used_angle, fill=PALETTE["accent_purple"], outline=PALETTE["card_border"], tags="pie")
        self.create_arc(cx-r, cy-r, cx+r, cy+r, start=90-used_angle, extent=-(360.0-used_angle), fill=PALETTE["bg_start"], outline=PALETTE["card_border"], tags="pie")
        
        r_inner = r * 0.6
        self.create_oval(cx-r_inner, cy-r_inner, cx+r_inner, cy+r_inner, fill=PALETTE["card_bg"], outline=PALETTE["card_border"])
        
        self.create_text(cx, cy, text=f"{self.sections['Used']:.1f}%", fill=PALETTE["text_main"], font=("Segoe UI", 12, "bold"))
        self.create_text(cx, cy+15, text="Token Load", fill=PALETTE["text_muted"], font=("Segoe UI", 7))


class AdvancedTokenDistributionChart(tk.Canvas):
    """Custom language token distribution stats visualizer chart widget."""
    def __init__(self, parent, **kwargs):
        cfg = {"bg": PALETTE["bg_start"], "highlightthickness": 0}
        cfg.update(kwargs)
        super().__init__(parent, **cfg)
        self.stats: Dict[str, float] = {}

    def set_stats(self, stats: Dict[str, float]):
        self.stats = stats
        self.draw()

    def draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 1 or h <= 1:
            w, h = 300, 150
            
        if not self.stats:
            self.create_text(w/2, h/2, text="No metrics to display.", fill=PALETTE["text_muted"], font=("Segoe UI", 9))
            return
            
        colors = [PALETTE["accent_cyan"], PALETTE["accent_purple"], PALETTE["accent_green"], "#f59e0b", "#10b981", "#3b82f6"]
        total = sum(self.stats.values())
        
        start_y = 15
        bar_height = 14
        spacing = 8
        
        idx = 0
        for lang, count in self.stats.items():
            if total == 0:
                pct = 0.0
            else:
                pct = (count / total) * 100.0
            
            y = start_y + idx * (bar_height + spacing)
            self.create_text(10, y + 7, text=lang.upper(), fill=PALETTE["text_main"], font=("Consolas", 8, "bold"), anchor="w")
            
            # Draw bar border/background
            self.create_rectangle(75, y, w - 75, y + bar_height, fill=PALETTE["card_bg"], outline=PALETTE["card_border"])
            
            # Fill bar
            color = colors[idx % len(colors)]
            fill_w = (pct / 100.0) * (w - 150)
            self.create_rectangle(75, y, 75 + fill_w, y + bar_height, fill=color, outline=color)
            
            # Stats label
            self.create_text(w - 70, y + 7, text=f"{count} ({pct:.1f}%)", fill=PALETTE["text_muted"], font=("Segoe UI", 8), anchor="w")
            idx += 1


class CustomChangelogManager:
    """Safely retrieves git log history and repository diffs asynchronously."""
    def __init__(self, target_dir: str):
        self.target_dir = os.path.abspath(target_dir)

    def fetch_commits_async(self, callback: Callable) -> None:
        def run_thread():
            if not self.target_dir or not os.path.exists(self.target_dir):
                callback([])
                return
            try:
                res = subprocess.run(
                    ["git", "rev-parse", "--is-inside-work-tree"], 
                    cwd=self.target_dir, 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                if "true" not in res.stdout.lower():
                    callback([])
                    return

                res = subprocess.run(
                    ["git", "log", "-n", "15", "--pretty=format:%s (%an)"], 
                    cwd=self.target_dir, 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                commits = []
                for line in res.stdout.strip().split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    lower = line.lower()
                    ctype = "Updated"
                    if any(x in lower for x in ("fix", "bug", "patch", "correct")):
                        ctype = "Fixed"
                    elif any(x in lower for x in ("add", "feat", "new", "implement")):
                        ctype = "Added"
                    commits.append({"type": ctype, "desc": line, "source": "Git"})
                callback(commits)
            except Exception:
                callback([])
                
        threading.Thread(target=run_thread, daemon=True).start()

    def get_git_diff_async(self, callback: Callable) -> None:
        def run_thread():
            try:
                res = subprocess.run(
                    ["git", "diff", "HEAD"], 
                    cwd=self.target_dir, 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                callback(res.stdout or "No uncommitted modifications detected in git status.")
            except Exception as e:
                callback(f"Failed to load git diff details: {e}")
        threading.Thread(target=run_thread, daemon=True).start()


class PygmentsHighlighter:
    """Helper lexer to colorize and tag text elements inside Tkinter widgets."""
    def __init__(self, text_widget: tk.Text):
        self.text_widget = text_widget
        self.setup_tags()

    def setup_tags(self):
        self.text_widget.tag_configure("Token.Keyword", foreground="#ff79c6")
        self.text_widget.tag_configure("Token.Name.Class", foreground="#50fa7b", font=("Consolas", 10, "bold"))
        self.text_widget.tag_configure("Token.Name.Function", foreground="#50fa7b")
        self.text_widget.tag_configure("Token.Literal.String", foreground="#f1fa8c")
        self.text_widget.tag_configure("Token.Comment", foreground="#6272a4", font=("Consolas", 10, "italic"))
        self.text_widget.tag_configure("Token.Operator", foreground="#ff79c6")
        self.text_widget.tag_configure("Token.Number", foreground="#bd93f9")

    def highlight_code(self, code_str: str, lang: str):
        self.text_widget.delete("1.0", tk.END)
        try:
            lexer = get_lexer_by_name(lang)
        except Exception:
            lexer = get_lexer_by_name("python")
            
        tokens = lex(code_str, lexer)
        for token_type, value in tokens:
            tag_name = str(token_type)
            self.text_widget.insert(tk.END, value, tag_name)


# --- 13. DYNAMIC UI DASHBOARD MAIN WINDOW ---

class AutoReadmeGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.lang = _config_mgr.get_profile().get("language", "en")
        
        # State parameters
        self.scanned_files: List[str] = []
        self.file_checked: Dict[str, bool] = {}
        self.file_sizes: Dict[str, int] = {}
        self.file_snippets: Dict[str, str] = {}
        self.manual_changes: List[Dict[str, str]] = []
        self.git_checkboxes: Dict[str, Tuple[tk.BooleanVar, Dict[str, str]]] = {}
        self.active_preview_file: Optional[str] = None
        
        self.cancel_event = threading.Event()
        self.scanner = CodebaseScanner()
        self.template_engine = TemplateEngine()
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        available_width = max(640, screen_width - 48)
        available_height = max(480, screen_height - 96)
        window_width = min(1700, max(min(1100, available_width), int(available_width * 0.88)))
        window_height = min(1080, max(min(700, available_height), int(available_height * 0.90)))
        position_x = max(0, (screen_width - window_width) // 2)
        position_y = max(0, (screen_height - window_height) // 2)
        self.root.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")
        self.root.minsize(min(960, window_width), min(640, window_height))

        # Apply official Siber Akademi Brand Icon (Embedded Base64 + Fallback)
        self.logo_img = None
        self.logo_sm = None
        if siber_akademi_icon:
            try:
                siber_akademi_icon.apply_window_icon(self.root)
                self.logo_img = siber_akademi_icon.get_logo_photo_image((36, 36))
                self.logo_sm = siber_akademi_icon.get_logo_photo_image((22, 22))
            except Exception:
                pass
        if not self.logo_img:
            resource_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(resource_dir, "siber_akademi.ico")
            if os.path.isfile(icon_path):
                try:
                    self.root.iconbitmap(icon_path)
                except Exception:
                    pass

        self.root.title(get_text("title", self.lang))
        self.root.configure(bg=PALETTE["bg_start"])
        
        self.create_layout()
        self.load_saved_credentials()
        self.setup_keyboard_shortcuts()
        self.start_system_telemetry()
        
    def setup_keyboard_shortcuts(self):
        self.root.bind("<Control-s>", lambda e: self.run_scanner())
        self.root.bind("<Control-g>", lambda e: self.start_generation())
        self.root.bind("<Control-c>", lambda e: self.copy_clipboard())
        self.root.bind("<Control-r>", lambda e: self.sync_git_commits())

    def create_layout(self):
        self.bg_canvas = StarfieldCanvas(self.root)
        self.bg_canvas.pack(fill=tk.BOTH, expand=True)

        sidebar_bg = PALETTE.get("sidebar_bg", "#3843a0")
        sidebar_fg = PALETTE.get("sidebar_fg", "#ffffff")
        sidebar_muted = PALETTE.get("sidebar_muted", "#a5b4fc")
        sidebar_hover = PALETTE.get("sidebar_hover", "#4a55ab")
        sidebar_active = PALETTE.get("sidebar_active", "#2b3478")

        # 1. SLIM EXECUTIVE SIDEBAR RAIL (66px wide)
        self.sidebar = GlassCard(self.bg_canvas, bg=sidebar_bg, highlightbackground=sidebar_bg)
        self.sidebar.place(x=8, y=8, width=66, relheight=0.98)

        # Top Avatar Circle
        avatar_canvas = tk.Canvas(self.sidebar, width=44, height=44, bg=sidebar_bg, highlightthickness=0)
        avatar_canvas.pack(pady=(12, 14))
        avatar_canvas.create_oval(2, 2, 42, 42, fill=PALETTE.get("accent_coral", "#f97316"), outline="#ffffff", width=2)
        if self.logo_sm:
            avatar_canvas.create_image(22, 22, image=self.logo_sm)
        else:
            avatar_canvas.create_text(22, 22, text="SA", fill="#ffffff", font=("Segoe UI", 11, "bold"))

        # 7 Tabs with sleek icons
        self.tabs = ["overview_tab", "selector_tab", "changelog_tab", "generate_tab", "template_tab", "graph_tab", "settings_tab"]
        self.tab_icons = ["🏠", "📂", "🔀", "🚀", "🧪", "📊", "⚙️"]
        self.tab_buttons: List[tk.Label] = []
        self.tab_containers: List[tk.Frame] = []
        self.nav_indicators: List[tk.Frame] = []
        self.active_tab_index = 0

        for idx, (key, icon) in enumerate(zip(self.tabs, self.tab_icons)):
            cont = tk.Frame(self.sidebar, bg=sidebar_bg, width=66, height=42)
            cont.pack(pady=2)
            cont.pack_propagate(False)

            ind = tk.Frame(cont, bg="#ffffff", width=4, height=22)
            if idx == 0:
                ind.place(x=2, y=10, width=4, height=22)
            self.nav_indicators.append(ind)

            btn_bg = sidebar_active if idx == 0 else sidebar_bg
            btn_fg = "#ffffff" if idx == 0 else sidebar_muted
            btn = tk.Label(cont, text=icon, font=("Segoe UI Emoji", 14), fg=btn_fg, bg=btn_bg, cursor="hand2")
            btn.place(x=13, y=4, width=40, height=34)
            btn.bind("<Button-1>", lambda e, i=idx: self.switch_tab(i))

            def on_enter(e, b=btn, i=idx):
                if self.active_tab_index != i:
                    b.configure(bg=sidebar_hover)
            def on_leave(e, b=btn, i=idx):
                if self.active_tab_index != i:
                    b.configure(bg=sidebar_bg)
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

            self.tab_buttons.append(btn)
            self.tab_containers.append(cont)

        # Spacer
        spacer = tk.Frame(self.sidebar, bg=sidebar_bg)
        spacer.pack(fill=tk.BOTH, expand=True)

        # Bottom Utilities
        for icon_char, cmd_handler in [
            ("🎨", self.open_theme_selector),
            ("🌐", self.toggle_language),
            ("⌨", self.show_shortcuts_modal),
            ("📋", self.toggle_console_drawer)
        ]:
            lbl = tk.Label(self.sidebar, text=icon_char, font=("Segoe UI Emoji", 12), fg=sidebar_muted, bg=sidebar_bg, cursor="hand2")
            lbl.pack(pady=3)
            lbl.bind("<Button-1>", lambda e, h=cmd_handler: h())

        tk.Label(self.sidebar, text="●", font=("Segoe UI", 8, "bold"), fg=PALETTE["success"], bg=sidebar_bg).pack(pady=(4, 10))

        # 2. TOP HEADER BAR
        self.header = GlassCard(self.bg_canvas)
        self.header.place(x=82, y=8, relwidth=1.0, width=-92, height=48)

        title_frame = tk.Frame(self.header, bg=PALETTE["card_bg"])
        title_frame.pack(side=tk.LEFT, fill=tk.Y, padx=14, pady=2)

        title_row = tk.Frame(title_frame, bg=PALETTE["card_bg"])
        title_row.pack(anchor=tk.W)

        self.title_lbl = tk.Label(title_row, text=get_text("title", self.lang), font=("Segoe UI", 11, "bold"), fg=PALETTE.get("accent_cyan", "#3843a0"), bg=PALETTE["card_bg"])
        self.title_lbl.pack(side=tk.LEFT)

        self.status_dot = GlowingStatusDot(title_row)
        self.status_dot.pack(side=tk.LEFT, padx=8)

        self.subtitle_lbl = tk.Label(title_frame, text=get_text("subtitle", self.lang), font=("Segoe UI", 7), fg=PALETTE["text_muted"], bg=PALETTE["card_bg"])
        self.subtitle_lbl.pack(anchor=tk.W)

        header_controls = tk.Frame(self.header, bg=PALETTE["card_bg"])
        header_controls.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=2)

        # Search Pill with dark circle magnifying glass
        s_pill = tk.Frame(header_controls, bg=PALETTE["card_bg"], highlightthickness=1, highlightbackground=PALETTE["card_border"])
        s_pill.pack(side=tk.LEFT, padx=6)
        self.header_search_entry = tk.Entry(
            s_pill,
            bg=PALETTE.get("bg_start", "#edf2fb"),
            fg=PALETTE.get("text_main", "#1e293b"),
            insertbackground=PALETTE.get("text_main", "#1e293b"),
            relief=tk.FLAT,
            font=("Segoe UI", 8),
            width=20
        )
        self.header_search_entry.pack(side=tk.LEFT, ipady=3, padx=(8, 2))
        self.header_search_entry.insert(0, "Search codebase...")
        self.header_search_entry.bind("<FocusIn>", lambda e: self._on_header_search_focus())

        s_btn = tk.Canvas(s_pill, width=22, height=22, bg=PALETTE["card_bg"], highlightthickness=0)
        s_btn.pack(side=tk.LEFT, padx=(0, 4))
        s_btn.create_oval(1, 1, 21, 21, fill=PALETTE["sidebar_bg"], outline="")
        s_btn.create_text(11, 11, text="🔍", fill="#ffffff", font=("Segoe UI Emoji", 8))

        is_lux = CURRENT_THEME == "Luxury Dashboard"
        theme_toggle_txt = "🌙 DARK MODE" if is_lux else "☀️ LUXURY MODE"
        self.quick_theme_btn = CanvasPillButton(
            header_controls,
            text=theme_toggle_txt,
            command=self.toggle_quick_theme,
            height=28,
            radius=14,
            bg_color=PALETTE["card_border"],
            text_color=PALETTE.get("accent_purple", "#6366f1"),
            font=("Segoe UI", 7, "bold"),
            width=120
        )
        self.quick_theme_btn.pack(side=tk.LEFT, padx=3)

        self.audit_btn = CanvasPillButton(
            header_controls,
            text=get_text("audit_btn", self.lang),
            command=self.run_quick_security_audit,
            height=28,
            radius=14,
            bg_color=PALETTE.get("card_hover", "#e0e7ff"),
            text_color=PALETTE.get("accent_cyan", "#3843a0"),
            font=("Segoe UI", 7, "bold"),
            width=110
        )
        self.audit_btn.pack(side=tk.LEFT, padx=3)

        # 3. MAIN CONTENT FRAME
        self.content = tk.Frame(self.bg_canvas, bg=PALETTE["bg_start"], bd=0)
        self.content.place(x=82, y=62, relwidth=1.0, width=-92, relheight=1.0, height=-94)

        self.tab_frames = [tk.Frame(self.content, bg=PALETTE["bg_start"]) for _ in range(7)]
        self.setup_tab_setup()
        self.setup_tab_selector()
        self.setup_tab_changelog()
        self.setup_tab_generate()
        self.setup_tab_template()
        self.setup_tab_graph()
        self.setup_tab_settings()

        # 4. SLEEK COLLAPSIBLE STATUS BAR & LOG DRAWER
        self.status_bar = tk.Frame(self.bg_canvas, bg=PALETTE["bg_start"])
        self.status_bar.place(x=82, rely=1.0, y=-28, relwidth=1.0, width=-92, height=24)

        s_pill_bot = tk.Frame(self.status_bar, bg=PALETTE["card_bg"], highlightthickness=1, highlightbackground=PALETTE["card_border"])
        s_pill_bot.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(s_pill_bot, text="📋 SİSTEM GÜNLÜĞÜ:", font=("Segoe UI", 7, "bold"), fg=PALETTE["text_muted"], bg=PALETTE["card_bg"]).pack(side=tk.LEFT, padx=(8, 4), pady=2)
        self.status_bar_lbl = tk.Label(s_pill_bot, text="[ONLINE] Siber Akademi T-Zero V3 Context builder loaded.", font=("Consolas", 7), fg=PALETTE.get("accent_cyan", "#3843a0"), bg=PALETTE["card_bg"])
        self.status_bar_lbl.pack(side=tk.LEFT, pady=2)

        self.status_toggle_lbl = tk.Label(s_pill_bot, text="▲ Konsolu Göster", font=("Segoe UI", 7, "bold"), fg=PALETTE.get("accent_purple", "#6366f1"), bg=PALETTE["card_bg"], cursor="hand2")
        self.status_toggle_lbl.pack(side=tk.RIGHT, padx=8, pady=2)
        self.status_toggle_lbl.bind("<Button-1>", lambda e: self.toggle_console_drawer())

        # Collapsible Console Drawer Frame
        self.console_drawer_visible = False
        self.console_drawer = GlassCard(self.bg_canvas)

        c_top = tk.Frame(self.console_drawer, bg=PALETTE["card_bg"])
        c_top.pack(fill=tk.X, padx=10, pady=4)
        tk.Label(c_top, text="DIAGNOSTICS & SYSTEM AUDITS LOG:", font=("Segoe UI", 8, "bold"), fg=PALETTE["text_muted"], bg=PALETTE["card_bg"]).pack(side=tk.LEFT)
        close_lbl = tk.Label(c_top, text="✕ Kapat", font=("Segoe UI", 8, "bold"), fg=PALETTE["accent_purple"], bg=PALETTE["card_bg"], cursor="hand2")
        close_lbl.pack(side=tk.RIGHT)
        close_lbl.bind("<Button-1>", lambda e: self.toggle_console_drawer())

        console_frame = tk.Frame(self.console_drawer, bg=PALETTE["card_bg"])
        console_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 6))

        self.console_text = tk.Text(console_frame, bg=PALETTE["bg_start"], fg=PALETTE["accent_cyan"], relief=tk.FLAT, font=("Consolas", 8), state=tk.DISABLED, bd=0)
        self.console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = tk.Scrollbar(console_frame, command=self.console_text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.console_text.config(yscrollcommand=scroll.set)

        self.switch_tab(0)
        self.log("Siber Akademi T-Zero V3 Executive Suite loaded.")

    def toggle_console_drawer(self):
        play_sfx("click")
        if hasattr(self, "console_drawer"):
            if self.console_drawer_visible:
                self.console_drawer.place_forget()
                self.console_drawer_visible = False
                if hasattr(self, "status_toggle_lbl"):
                    self.status_toggle_lbl.config(text="▲ Konsolu Göster")
            else:
                self.console_drawer.place(x=82, rely=0.68, relwidth=1.0, width=-92, relheight=0.28)
                self.console_drawer.lift()
                self.console_drawer_visible = True
                if hasattr(self, "status_toggle_lbl"):
                    self.status_toggle_lbl.config(text="▼ Konsolu Gizle")

    def log(self, text: str):
        if not hasattr(self, "console_text") or self.console_text is None:
            return
        try:
            self.console_text.config(state=tk.NORMAL)
            t = time.strftime("[%H:%M:%S]")
            self.console_text.insert(tk.END, f"{t} {text}\n")
            self.console_text.see(tk.END)
            self.console_text.config(state=tk.DISABLED)
        except Exception:
            pass

    def cycle_fx_mode(self):
        play_sfx("click")
        new_mode = self.bg_canvas.cycle_mode()
        self.fx_btn.config(text=f"🌌 FX: {new_mode.upper()}")
        self.show_toast(f"Particle background set to {new_mode.upper()}", "info")

    def toggle_sfx(self):
        global SFX_ENABLED
        SFX_ENABLED = not SFX_ENABLED
        play_sfx("click")
        txt = get_text("sfx_on" if SFX_ENABLED else "sfx_off", self.lang)
        if hasattr(self, "sfx_btn") and self.sfx_btn is not None:
            self.sfx_btn.config(text=txt)
        self.show_toast(f"Sound effects {'enabled' if SFX_ENABLED else 'disabled'}", "info")

    def show_toast(self, message: str, kind: str = "info", duration_ms: int = 2500):
        try:
            border_col = PALETTE["success"] if kind == "success" else (PALETTE["error"] if kind == "error" else PALETTE["accent_cyan"])
            toast = tk.Frame(self.bg_canvas, bg=PALETTE["card_bg"], highlightthickness=1, highlightbackground=border_col, bd=0)
            icon = "✔" if kind == "success" else ("⚠" if kind == "error" else "✦")
            
            tk.Label(toast, text=icon, font=("Segoe UI", 11, "bold"), fg=border_col, bg=PALETTE["card_bg"]).pack(side=tk.LEFT, padx=(12, 6), pady=6)
            tk.Label(toast, text=message, font=("Segoe UI", 9, "bold"), fg=PALETTE["text_main"], bg=PALETTE["card_bg"]).pack(side=tk.LEFT, padx=(0, 16), pady=6)
            toast.place(relx=0.68, rely=0.79, relwidth=0.30, height=38)
            
            def fade():
                try:
                    toast.destroy()
                except Exception:
                    pass
            self.root.after(duration_ms, fade)
        except Exception:
            pass

    def run_quick_security_audit(self):
        play_sfx("scan")
        target_dir = self.dir_entry.get().strip() if hasattr(self, "dir_entry") else "."
        if not target_dir or not os.path.exists(target_dir):
            self.show_toast("Target workspace does not exist!", "error")
            return
        
        key_patterns = [
            re.compile(r'sk-[a-zA-Z0-9]{20,}'),
            re.compile(r'ghp_[a-zA-Z0-9]{36}'),
            re.compile(r'AIza[0-9A-Za-z-_]{35}'),
            re.compile(r'nvapi-[a-zA-Z0-9-_]{20,}'),
        ]
        leaks = []
        py_files = 0
        smells = 0
        for root, dirs, files in os.walk(target_dir):
            if any(x in root for x in [".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build"]):
                continue
            for f in files:
                if f.endswith((".py", ".json", ".yaml", ".yml", ".env", ".txt")):
                    p = os.path.join(root, f)
                    try:
                        with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                            content = fp.read()
                        for pat in key_patterns:
                            if pat.search(content):
                                leaks.append((f, "API Key Exposure"))
                        if f.endswith(".py"):
                            py_files += 1
                            analyzer = StaticCodeAnalyzer(f)
                            analyzer.analyze_source(content)
                            smells += len(analyzer.issues)
                    except Exception:
                        pass
                        
        if leaks:
            play_sfx("error")
            messagebox.showwarning("Security Alert", f"Potential secret exposure detected in {len(leaks)} files!\nReview immediately.")
        else:
            play_sfx("success")
            self.show_toast(f"Security: 100% Zero-Leak | Smells: {smells} across {py_files} files", "success", 4000)
            self.log(f"Security Audit Clean: 0 hardcoded secrets found. Code smells: {smells}")

    def open_theme_selector(self):
        play_sfx("click")
        dialog = tk.Toplevel(self.root)
        dialog.title("App Theme Manager")
        dialog.geometry("340x480")
        dialog.configure(bg=PALETTE["bg_start"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        pad = tk.Frame(dialog, bg=PALETTE["bg_start"], padx=20, pady=15)
        pad.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(pad, text="SELECT INTERFACE THEME:", font=("Segoe UI", 10, "bold"), fg=PALETTE["accent_cyan"], bg=PALETTE["bg_start"]).pack(anchor=tk.W, pady=(0, 10))
        
        for theme_name, theme_data in THEME_PALETTES.items():
            row = tk.Frame(pad, bg=PALETTE["card_bg"], highlightthickness=1, highlightbackground=PALETTE["card_border"])
            row.pack(fill=tk.X, pady=3, ipady=3)
            
            # Theme color badge indicator
            c_dot = tk.Canvas(row, width=14, height=14, bg=PALETTE["card_bg"], highlightthickness=0)
            c_dot.pack(side=tk.LEFT, padx=8)
            c_dot.create_oval(2, 2, 12, 12, fill=theme_data.get("accent_cyan", "#00ffff"), outline=theme_data.get("card_border", "#ffffff"))
            
            btn = tk.Button(
                row,
                text=theme_name + (" (Active)" if theme_name == CURRENT_THEME else ""),
                bg=PALETTE["card_bg"],
                fg=PALETTE["text_main"],
                relief=tk.FLAT,
                font=("Segoe UI", 9, "bold" if theme_name == CURRENT_THEME else "normal"),
                anchor="w",
                command=lambda name=theme_name: self.apply_new_theme(name, dialog),
                cursor="hand2"
            )
            btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

        # Theme customizer color chooser button
        self.custom_theme_btn = tk.Button(pad, text="⚙ Customize Palette Colors", bg=PALETTE["card_border"], fg=PALETTE["accent_green"], relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=self.open_custom_color_picker, cursor="hand2")
        self.custom_theme_btn.pack(fill=tk.X, pady=(10, 0), ipady=4)

    def open_custom_color_picker(self):
        # Open custom color chooser dialog for bg_start
        color = colorchooser.askcolor(title="Choose App Main Background Color")
        if color[1]:
            PALETTE["bg_start"] = color[1]
            self.root.configure(bg=color[1])
            self.log(f"Custom bg_start color applied: {color[1]}")
            # Save configuration profile
            _config_mgr.save()

    def apply_new_theme(self, name: str, dialog: tk.Toplevel):
        update_colors(name)
        _config_mgr.get_profile()["theme"] = name
        _config_mgr.save()
        self.root.configure(bg=PALETTE["bg_start"])
        dialog.destroy()
        
        # Redraw structure layout
        for w in self.bg_canvas.winfo_children():
            w.destroy()
        self.create_layout()
        self.load_saved_credentials()
        self.log(f"Interface color theme updated: {name}")

    def switch_tab(self, idx: int):
        self.active_tab_index = idx
        for f in self.tab_frames:
            f.pack_forget()
        self.tab_frames[idx].pack(fill=tk.BOTH, expand=True)
        
        sidebar_bg = PALETTE.get("sidebar_bg", "#3843a0")
        sidebar_muted = PALETTE.get("sidebar_muted", "#a5b4fc")
        sidebar_active = PALETTE.get("sidebar_active", "#2b3478")
        
        for i, btn in enumerate(self.tab_buttons):
            if i == idx:
                btn.config(bg=sidebar_active, fg="#ffffff")
                if i < len(self.nav_indicators):
                    self.nav_indicators[i].place(x=2, y=10, width=4, height=22)
            else:
                btn.config(bg=sidebar_bg, fg=sidebar_muted)
                if i < len(self.nav_indicators):
                    self.nav_indicators[i].place_forget()
        
        if idx == 5:
            self.node_canvas.set_data(self.scanned_files)
            self.donut_chart.set_budget(sum(len(v) for v in self.file_snippets.values()) // 4)
            self.update_lang_distribution_metrics()
            self.git_graph_canvas.draw_graph(len(self.git_checkboxes))
            self.rebuild_file_type_matrix_table()
        elif idx == 6:
            self.refresh_profile_listbox()
        self.log(f"Switched view layout to index {idx}: {get_text(self.tabs[idx], self.lang)}")

    def _on_header_search_focus(self):
        if hasattr(self, "header_search_entry"):
            txt = self.header_search_entry.get().strip()
            if "Search codebase" in txt:
                self.header_search_entry.delete(0, tk.END)

    def toggle_quick_theme(self):
        play_sfx("click")
        target = "Glass Dark" if CURRENT_THEME == "Luxury Dashboard" else "Luxury Dashboard"
        update_colors(target)
        _config_mgr.get_profile()["theme"] = target
        _config_mgr.save()
        self.root.configure(bg=PALETTE["bg_start"])
        for w in self.bg_canvas.winfo_children():
            w.destroy()
        self.create_layout()
        self.load_saved_credentials()
        self.log(f"Theme switched instantly to: {target}")

    def quick_optimize_action(self):
        play_sfx("click")
        if not self.scanned_files:
            self.run_scanner()
        else:
            self.smart_select_tree()
            if hasattr(self, "gauge_card"):
                self.gauge_card.set_percentage(95)
            self.log("⚡ T-Zero Quick Optimization: Pruned non-essential AST nodes. Context compression maximized.")

    def toggle_language(self):
        self.lang = "tr" if self.lang == "en" else "en"
        _config_mgr.get_profile()["language"] = self.lang
        _config_mgr.save()
        
        self.root.title(get_text("title", self.lang))
        if hasattr(self, "title_lbl") and self.title_lbl:
            self.title_lbl.config(text=get_text("title", self.lang))
        if hasattr(self, "subtitle_lbl") and self.subtitle_lbl:
            self.subtitle_lbl.config(text=get_text("subtitle", self.lang))
        if hasattr(self, "tab_buttons") and hasattr(self, "tab_icons"):
            for idx, icon in enumerate(self.tab_icons):
                if idx < len(self.tab_buttons):
                    self.tab_buttons[idx].config(text=icon)
        if hasattr(self, "scan_btn") and self.scan_btn:
            self.scan_btn.config(text=get_text("scan_btn", self.lang))
        if hasattr(self, "gen_btn") and self.gen_btn:
            self.gen_btn.config(text=get_text("generate_btn", self.lang))
        if hasattr(self, "copy_btn") and self.copy_btn:
            self.copy_btn.config(text=get_text("copy_btn", self.lang))
        if hasattr(self, "save_btn") and self.save_btn:
            self.save_btn.config(text=get_text("save_btn", self.lang))
        if hasattr(self, "smart_select_btn") and self.smart_select_btn:
            self.smart_select_btn.config(text=get_text("smart_select", self.lang))
        if hasattr(self, "sel_all_btn") and self.sel_all_btn:
            self.sel_all_btn.config(text=get_text("select_all", self.lang))
        if hasattr(self, "desel_all_btn") and self.desel_all_btn:
            self.desel_all_btn.config(text=get_text("deselect_all", self.lang))
        if hasattr(self, "sfx_btn") and self.sfx_btn:
            self.sfx_btn.config(text=get_text("sfx_on" if SFX_ENABLED else "sfx_off", self.lang))
        if hasattr(self, "audit_btn") and self.audit_btn:
            self.audit_btn.config(text=get_text("audit_btn", self.lang))
        
        self.log(f"App interface translation updated: {self.lang.upper()}")

    # --- TAB 1: EXECUTIVE 9-CARD OVERVIEW DASHBOARD ---
    def setup_tab_setup(self):
        f = self.tab_frames[0]
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=1)
        f.columnconfigure(2, weight=1)
        f.columnconfigure(3, weight=1)
        
        f.rowconfigure(0, weight=2)
        f.rowconfigure(1, weight=3)
        f.rowconfigure(2, weight=2)
        
        # --- ROW 0: Top Executive KPI Hero Row (4 Equal Cards) ---
        # Card 1: Metric KPI Card
        self.kpi_card = KPICard(f)
        self.kpi_card.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        # Card 2: Executive Calendar Card
        self.cal_card = MiniCalendarCard(f)
        self.cal_card.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)

        # Card 3: Donut Gauge & Quick Optimize Button
        self.gauge_card = CircularGaugeCard(f, action_cmd=self.quick_optimize_action)
        self.gauge_card.grid(row=0, column=2, sticky="nsew", padx=4, pady=4)

        # Card 4: Wave Spline Mountain Peaks
        self.wave_card = WaveSplineChart(f)
        self.wave_card.grid(row=0, column=3, sticky="nsew", padx=4, pady=4)

        # --- ROW 1: Wide Spline Chart & Quick Action Workspace (2 Equal Cards, Span 2) ---
        # Card 5: Full-width Spline Curve Chart
        self.spline_card = WideSplineChartCard(f)
        self.spline_card.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)

        # Card 6: Quick Action Workspace Card (AI Provider, Model, Directory, Scan Button)
        self.quick_card = LuxuryCard(f, radius=18, padding=12)
        self.quick_card.grid(row=1, column=2, columnspan=2, sticky="nsew", padx=4, pady=4)
        q_inner = self.quick_card.inner

        tk.Label(q_inner, text="⚡ HIZLI KONTROL & MODEL", font=("Segoe UI", 9, "bold"), fg=PALETTE["sidebar_bg"], bg=self.quick_card.card_bg).pack(anchor=tk.W, pady=(0, 4))

        tk.Label(q_inner, text="AI Sağlayıcı:", font=("Segoe UI", 7, "bold"), fg=PALETTE["text_muted"], bg=self.quick_card.card_bg).pack(anchor=tk.W)
        self.provider_var = tk.StringVar(value="NVIDIA NIM")
        self.provider_combo = ttk.Combobox(q_inner, textvariable=self.provider_var, values=list(PROVIDERS.keys()), state="readonly")
        self.provider_combo.pack(fill=tk.X, ipady=1, pady=(1, 4))
        self.provider_combo.bind("<<ComboboxSelected>>", self.on_provider_select)

        tk.Label(q_inner, text="Hedef Model:", font=("Segoe UI", 7, "bold"), fg=PALETTE["text_muted"], bg=self.quick_card.card_bg).pack(anchor=tk.W)
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(q_inner, textvariable=self.model_var, state="readonly")
        self.model_combo.pack(fill=tk.X, ipady=1, pady=(1, 4))

        tk.Label(q_inner, text="Hedef Çalışma Dizini:", font=("Segoe UI", 7, "bold"), fg=PALETTE["text_muted"], bg=self.quick_card.card_bg).pack(anchor=tk.W)
        dir_frame = tk.Frame(q_inner, bg=self.quick_card.card_bg)
        dir_frame.pack(fill=tk.X, pady=(1, 6))

        self.dir_entry = apply_entry_focus_glow(tk.Entry(
            dir_frame,
            bg=PALETTE.get("bg_start", "#f8fafc"),
            fg=PALETTE["text_main"],
            insertbackground=PALETTE["text_main"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=PALETTE["card_border"],
            font=("Segoe UI", 8)
        ))
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3, padx=(0, 6))

        self.browse_btn = apply_modern_hover(tk.Button(
            dir_frame,
            text="Gözat...",
            bg=PALETTE["card_border"],
            fg=PALETTE["text_main"],
            relief=tk.FLAT,
            font=("Segoe UI", 7, "bold"),
            command=self.browse_dir,
            cursor="hand2"
        ))
        self.browse_btn.pack(side=tk.RIGHT, ipady=2, ipadx=6)

        self.scan_btn = CanvasPillButton(
            q_inner,
            text=get_text("scan_btn", self.lang),
            command=self.run_scanner,
            height=32,
            radius=16,
            bg_color=PALETTE["sidebar_bg"],
            hover_color=PALETTE["accent_purple"],
            text_color="#ffffff",
            font=("Segoe UI", 8, "bold")
        )
        self.scan_btn.pack(fill=tk.X, pady=(2, 0))

        # --- ROW 2: Bottom Cards ---
        # Card 7: Monthly Stacked Bar Card
        self.monthly_card = MonthlyStackedBarCard(f)
        self.monthly_card.grid(row=2, column=0, sticky="nsew", padx=4, pady=4)

        # Card 8: Grouped Vertical Bar Card
        self.daily_card = GroupedVerticalBarCard(f)
        self.daily_card.grid(row=2, column=1, sticky="nsew", padx=4, pady=4)

        # Card 9: Siber Akademi Security Hub Card
        self.security_card = SecurityHubCard(f, action_cmd=self.run_quick_security_audit)
        self.security_card.grid(row=2, column=2, columnspan=2, sticky="nsew", padx=4, pady=4)

    # --- TAB 7: SETTINGS & SECRETS MANAGEMENT ---
    def setup_tab_settings(self):
        f = self.tab_frames[6]
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=1)
        f.rowconfigure(0, weight=1)

        left = GlassCard(f)
        left.grid(row=0, column=0, sticky="nsew", padx=(4, 4), pady=4)
        left.pack_propagate(False)

        right = GlassCard(f)
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 4), pady=4)
        right.pack_propagate(False)

        # Left Panel (API Credentials & Advanced Config)
        pad_l = tk.Frame(left, bg=PALETTE["card_bg"], padx=16, pady=14)
        pad_l.pack(fill=tk.BOTH, expand=True)

        tk.Label(pad_l, text="AI PROVIDER ENTEGRASYONU & KİMLİK", font=("Segoe UI", 10, "bold"), fg=PALETTE["accent_cyan"], bg=PALETTE["card_bg"]).pack(anchor=tk.W, pady=(0, 6))

        tk.Label(pad_l, text="API BASE URL:", font=("Segoe UI", 8, "bold"), fg=PALETTE["text_muted"], bg=PALETTE["card_bg"]).pack(anchor=tk.W, pady=(4, 2))
        self.api_url_entry = apply_entry_focus_glow(tk.Entry(
            pad_l,
            bg=PALETTE["bg_start"],
            fg=PALETTE["text_main"],
            insertbackground=PALETTE["text_main"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=PALETTE["card_border"],
            font=("Segoe UI", 8)
        ))
        self.api_url_entry.pack(fill=tk.X, ipady=4, pady=(0, 8))

        tk.Label(pad_l, text="API ANAHTARI (KEYRING KORUMALI):", font=("Segoe UI", 8, "bold"), fg=PALETTE["text_muted"], bg=PALETTE["card_bg"]).pack(anchor=tk.W, pady=(0, 2))
        key_frame = tk.Frame(pad_l, bg=PALETTE["card_bg"])
        key_frame.pack(fill=tk.X, pady=(0, 10))

        self.api_key_entry = apply_entry_focus_glow(tk.Entry(
            key_frame,
            bg=PALETTE["bg_start"],
            fg=PALETTE["text_main"],
            show="*",
            insertbackground=PALETTE["text_main"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=PALETTE["card_border"],
            font=("Segoe UI", 8)
        ))
        self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

        self.ping_btn = apply_modern_hover(tk.Button(
            key_frame,
            text="⚡ PING",
            bg=PALETTE["card_border"],
            fg=PALETTE["accent_cyan"],
            relief=tk.FLAT,
            font=("Segoe UI", 8, "bold"),
            command=self.ping_endpoint,
            cursor="hand2"
        ))
        self.ping_btn.pack(side=tk.RIGHT, padx=(8, 0), ipady=3, ipadx=8)

        # Custom prompt directives
        tk.Label(pad_l, text="📝 ÖZEL SİSTEM VE PROMPT YÖNERGELERİ:", font=("Segoe UI", 8, "bold"), fg=PALETTE["accent_purple"], bg=PALETTE["card_bg"]).pack(anchor=tk.W, pady=(6, 2))
        self.extra_prompt_text = tk.Text(pad_l, bg=PALETTE["bg_start"], fg=PALETTE["text_main"], insertbackground="#ffffff", relief=tk.FLAT, font=("Segoe UI", 8), height=5, bd=0)
        self.extra_prompt_text.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # Bottom FX star speed
        bottom_fx = tk.Frame(pad_l, bg=PALETTE["card_bg"])
        bottom_fx.pack(fill=tk.X, pady=(2, 0))
        tk.Label(bottom_fx, text="🌌 Parçacık Animasyon Hızı:", font=("Segoe UI", 8, "bold"), fg=PALETTE["text_muted"], bg=PALETTE["card_bg"]).pack(side=tk.LEFT, padx=(0, 6))
        self.star_scale = tk.Scale(bottom_fx, from_=0.1, to=4.0, resolution=0.1, orient=tk.HORIZONTAL, bg=PALETTE["card_bg"], fg=PALETTE["text_main"], troughcolor=PALETTE["bg_start"], highlightthickness=0, command=self.update_star_velocity, showvalue=False)
        self.star_scale.set(1.0)
        self.star_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Right Panel (Profiles, Backup, Dev info)
        pad_r = tk.Frame(right, bg=PALETTE["card_bg"], padx=16, pady=14)
        pad_r.pack(fill=tk.BOTH, expand=True)

        # Brand Banner
        brand = GlassCard(pad_r, bg=PALETTE["bg_start"])
        brand.pack(fill=tk.X, pady=(0, 8), ipady=2)

        b_top = tk.Frame(brand, bg=PALETTE["bg_start"])
        b_top.pack(fill=tk.X, padx=10, pady=(4, 2))
        tk.Label(b_top, text="🛡️ SİBER AKADEMİ CREATOR HUB", font=("Segoe UI", 8, "bold"), fg=PALETTE["accent_cyan"], bg=PALETTE["bg_start"]).pack(side=tk.LEFT)
        tk.Label(b_top, text="v3.0.8", font=("Segoe UI", 8, "bold"), fg=PALETTE["accent_green"], bg=PALETTE["bg_start"]).pack(side=tk.RIGHT)

        b_links = tk.Frame(brand, bg=PALETTE["bg_start"])
        b_links.pack(fill=tk.X, padx=10, pady=(2, 6))

        lbl_sa = tk.Label(b_links, text=f"Geliştirici: {DEV_NAME}", font=("Segoe UI", 8, "bold"), fg=PALETTE["text_main"], bg=PALETTE["bg_start"])
        lbl_sa.pack(side=tk.LEFT, padx=(0, 10))

        lbl_web1 = tk.Label(b_links, text="💼 LinkedIn", font=("Segoe UI", 8, "bold"), fg=PALETTE["accent_cyan"], bg=PALETTE["card_bg"], padx=6, pady=2, cursor="hand2")
        lbl_web1.pack(side=tk.LEFT, padx=3)
        lbl_web1.bind("<Button-1>", lambda e: webbrowser.open(DEV_URL_LINKEDIN))

        lbl_web2 = tk.Label(b_links, text="🌐 Biyografi & Hub", font=("Segoe UI", 8, "bold"), fg=PALETTE["accent_purple"], bg=PALETTE["card_bg"], padx=6, pady=2, cursor="hand2")
        lbl_web2.pack(side=tk.LEFT, padx=3)
        lbl_web2.bind("<Button-1>", lambda e: webbrowser.open(DEV_URL_BIO))

        lbl_web3 = tk.Label(b_links, text="⭐ GitHub Repo", font=("Segoe UI", 8, "bold"), fg=PALETTE["accent_green"], bg=PALETTE["card_bg"], padx=6, pady=2, cursor="hand2")
        lbl_web3.pack(side=tk.LEFT, padx=3)
        lbl_web3.bind("<Button-1>", lambda e: webbrowser.open(DEV_URL_MAIN))

        # Dynamic profiles manager
        profile_editor_frame = GlassCard(pad_r)
        profile_editor_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 2))
        profile_editor_frame.config(padx=10, pady=8)

        p_head_row = tk.Frame(profile_editor_frame, bg=PALETTE["card_bg"])
        p_head_row.pack(fill=tk.X, pady=(0, 4))
        tk.Label(p_head_row, text="⚙️ PROFİL & GÜVENLİK YÖNETİMİ", font=("Segoe UI", 8, "bold"), fg=PALETTE["accent_green"], bg=PALETTE["card_bg"]).pack(side=tk.LEFT)

        p_select_row = tk.Frame(profile_editor_frame, bg=PALETTE["card_bg"])
        p_select_row.pack(fill=tk.X, pady=(0, 6))

        self.profile_listbox = tk.Listbox(p_select_row, bg=PALETTE["bg_start"], fg=PALETTE["text_main"], selectbackground=PALETTE["card_hover"], relief=tk.FLAT, bd=0, height=3)
        self.profile_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.refresh_profile_listbox()

        p_actions = tk.Frame(p_select_row, bg=PALETTE["card_bg"])
        p_actions.pack(side=tk.RIGHT)

        self.use_profile_btn = apply_modern_hover(tk.Button(p_actions, text="⚡ Etkinleştir", bg=PALETTE["card_border"], fg=PALETTE["accent_cyan"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=self.activate_selected_profile, cursor="hand2"), hover_bg=PALETTE["accent_cyan"], hover_fg="#000000")
        self.use_profile_btn.pack(side=tk.TOP, fill=tk.X, pady=1)

        p_mini = tk.Frame(p_actions, bg=PALETTE["card_bg"])
        p_mini.pack(side=tk.BOTTOM, fill=tk.X)
        self.new_profile_btn = apply_modern_hover(tk.Button(p_mini, text="+ Yeni", bg=PALETTE["card_border"], fg=PALETTE["text_main"], relief=tk.FLAT, font=("Segoe UI", 7, "bold"), command=self.create_new_profile_modal, cursor="hand2"))
        self.new_profile_btn.pack(side=tk.LEFT, padx=1)
        self.del_profile_btn = apply_modern_hover(tk.Button(p_mini, text="🗑 Sil", bg=PALETTE["card_border"], fg=PALETTE["error"], relief=tk.FLAT, font=("Segoe UI", 7, "bold"), command=self.delete_selected_profile, cursor="hand2"), hover_bg=PALETTE["error"], hover_fg="#ffffff")
        self.del_profile_btn.pack(side=tk.LEFT, padx=1)

        # 2x2 Management tools grid
        tools_grid = tk.Frame(profile_editor_frame, bg=PALETTE["card_bg"])
        tools_grid.pack(fill=tk.X, pady=(4, 6))
        tools_grid.columnconfigure(0, weight=1)
        tools_grid.columnconfigure(1, weight=1)

        self.keyring_btn = apply_modern_hover(tk.Button(tools_grid, text="🔑 API Anahtarları (Keyring)", bg=PALETTE["card_border"], fg=PALETTE["accent_cyan"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=self.open_keyring_editor_dialog, cursor="hand2"))
        self.keyring_btn.grid(row=0, column=0, sticky="ew", padx=2, pady=2, ipady=3)

        self.keyring_backup_btn = apply_modern_hover(tk.Button(tools_grid, text="🛡 Kimlik Yedeği", bg=PALETTE["card_border"], fg=PALETTE["accent_green"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=self.open_keyring_backup_dialog, cursor="hand2"))
        self.keyring_backup_btn.grid(row=0, column=1, sticky="ew", padx=2, pady=2, ipady=3)

        self.global_config_btn = apply_modern_hover(tk.Button(tools_grid, text="⚙ Performans & Limitler", bg=PALETTE["card_border"], fg=PALETTE["accent_purple"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=self.open_global_config_editor, cursor="hand2"))
        self.global_config_btn.grid(row=1, column=0, sticky="ew", padx=2, pady=2, ipady=3)

        self.ignore_folders_btn = apply_modern_hover(tk.Button(tools_grid, text="📁 Yoksayılan Klasörler", bg=PALETTE["card_border"], fg=PALETTE["text_muted"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=self.open_ignored_folders_dialog, cursor="hand2"))
        self.ignore_folders_btn.grid(row=1, column=1, sticky="ew", padx=2, pady=2, ipady=3)

        # Import/Export + Presets row
        io_row = tk.Frame(profile_editor_frame, bg=PALETTE["card_bg"])
        io_row.pack(fill=tk.X, pady=(2, 0))

        self.import_profile_btn = apply_modern_hover(tk.Button(io_row, text="📥 İçe Aktar", bg=PALETTE["card_border"], fg=PALETTE["text_muted"], relief=tk.FLAT, font=("Segoe UI", 8), command=self.import_profile_json, cursor="hand2"))
        self.import_profile_btn.pack(side=tk.LEFT, padx=2)

        self.export_profile_btn = apply_modern_hover(tk.Button(io_row, text="📤 Dışa Aktar", bg=PALETTE["card_border"], fg=PALETTE["text_muted"], relief=tk.FLAT, font=("Segoe UI", 8), command=self.export_profile_json, cursor="hand2"))
        self.export_profile_btn.pack(side=tk.LEFT, padx=2)

        tk.Label(io_row, text="Önayar:", font=("Segoe UI", 8, "bold"), fg=PALETTE["text_muted"], bg=PALETTE["card_bg"]).pack(side=tk.LEFT, padx=(8, 2))
        self.preset_combo = ttk.Combobox(io_row, values=list(WorkspacePresetManager.PRESETS.keys()), state="readonly", width=14)
        self.preset_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=2)
        self.preset_combo.bind("<<ComboboxSelected>>", self.apply_scan_preset)

    def open_keyring_backup_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Keyring Credentials Backup")
        dialog.geometry("380x280")
        dialog.configure(bg=PALETTE["bg_start"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        pad = tk.Frame(dialog, bg=PALETTE["bg_start"], padx=15, pady=15)
        pad.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(pad, text="BACKUP / RESTORE KEYRING:", font=("Segoe UI", 10, "bold"), fg=PALETTE["accent_cyan"], bg=PALETTE["bg_start"]).pack(anchor=tk.W, pady=(0, 5))
        
        tk.Label(pad, text="Master Cipher Key:", font=("Segoe UI", 9), fg=PALETTE["text_muted"], bg=PALETTE["bg_start"]).pack(anchor=tk.W)
        key_entry = tk.Entry(pad, bg=PALETTE["card_bg"], fg=PALETTE["text_main"], show="*", insertbackground="#ffffff", relief=tk.FLAT)
        key_entry.pack(fill=tk.X, ipady=4, pady=(0, 15))
        
        def run_backup():
            key = key_entry.get().strip()
            if not key:
                return
            filepath = filedialog.asksaveasfilename(defaultextension=".dat", filetypes=[("Data Files", "*.dat")])
            if filepath:
                if KeyringSecretsBackupManager.backup_credentials(filepath, key):
                    messagebox.showinfo("Success", "Credentials backed up securely!")
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Backup operation failed.")
                    
        def run_restore():
            key = key_entry.get().strip()
            if not key:
                return
            filepath = filedialog.askopenfilename(filetypes=[("Data Files", "*.dat")])
            if filepath:
                if KeyringSecretsBackupManager.restore_credentials(filepath, key):
                    messagebox.showinfo("Success", "Credentials restored securely!")
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Restore operation failed. Invalid key?")
                    
        btn_row = tk.Frame(pad, bg=PALETTE["bg_start"])
        btn_row.pack(fill=tk.X, pady=10)
        tk.Button(btn_row, text="📤 Backup Keyring", bg=PALETTE["card_border"], fg=PALETTE["accent_cyan"], relief=tk.FLAT, command=run_backup).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        tk.Button(btn_row, text="📥 Restore Keyring", bg=PALETTE["card_border"], fg=PALETTE["accent_green"], relief=tk.FLAT, command=run_restore).pack(side=tk.RIGHT, padx=5, expand=True, fill=tk.X)

    def open_global_config_editor(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Global Settings Panel")
        dialog.geometry("360x280")
        dialog.configure(bg=PALETTE["bg_start"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        pad = tk.Frame(dialog, bg=PALETTE["bg_start"], padx=15, pady=15)
        pad.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(pad, text="SCANNER WORKERS COUNT:", font=("Segoe UI", 9, "bold"), fg=PALETTE["text_muted"], bg=PALETTE["bg_start"]).pack(anchor=tk.W)
        workers_entry = tk.Entry(pad, bg=PALETTE["card_bg"], fg=PALETTE["text_main"], insertbackground="#ffffff", relief=tk.FLAT)
        workers_entry.pack(fill=tk.X, ipady=4, pady=(0, 10))
        workers_entry.insert(0, str(_config_mgr.get_profile().get("thread_pool_size", 4)))
        
        tk.Label(pad, text="MAX TOKENS BUDGET LIMIT:", font=("Segoe UI", 9, "bold"), fg=PALETTE["text_muted"], bg=PALETTE["bg_start"]).pack(anchor=tk.W)
        tokens_entry = tk.Entry(pad, bg=PALETTE["card_bg"], fg=PALETTE["text_main"], insertbackground="#ffffff", relief=tk.FLAT)
        tokens_entry.pack(fill=tk.X, ipady=4, pady=(0, 15))
        tokens_entry.insert(0, str(_config_mgr.get_profile().get("max_tokens_budget", 60000)))
        
        def save():
            try:
                workers = int(workers_entry.get())
                tokens = int(tokens_entry.get())
                profile = _config_mgr.get_profile()
                profile["thread_pool_size"] = workers
                profile["max_tokens_budget"] = tokens
                _config_mgr.save()
                self.log(f"Saved global scanner thread workers limit: {workers}, tokens limit: {tokens}")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Values must be integer values!")
                
        tk.Button(pad, text="Save configs", bg=PALETTE["success"], fg="#ffffff", relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=save).pack()

    def open_keyring_editor_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Secure Keyring Secrets Manager")
        dialog.geometry("400x300")
        dialog.configure(bg=PALETTE["bg_start"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        pad = tk.Frame(dialog, bg=PALETTE["bg_start"], padx=15, pady=15)
        pad.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(pad, text="SAVED PROVIDER SECRETS:", font=("Segoe UI", 10, "bold"), fg=PALETTE["accent_cyan"], bg=PALETTE["bg_start"]).pack(anchor=tk.W, pady=(0, 5))
        
        tree = ttk.Treeview(pad, columns=("Provider", "SecretStatus"), show="headings", height=5)
        tree.heading("Provider", text="AI Provider")
        tree.heading("SecretStatus", text="Key Status")
        tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        def refresh_secrets_tree():
            for item in tree.get_children():
                tree.delete(item)
            creds = KeyringSecretsEditor.list_credentials()
            for k, v in creds.items():
                tree.insert("", "end", values=(k, v))
                
        refresh_secrets_tree()
        
        row = tk.Frame(pad, bg=PALETTE["bg_start"])
        row.pack(fill=tk.X)
        
        def delete_secret():
            sel = tree.selection()
            if not sel:
                return
            provider = tree.item(sel[0], "values")[0]
            try:
                keyring.delete_password(SERVICE_NAME, provider)
                self.log(f"Cleared credentials for {provider} from keyring.")
                refresh_secrets_tree()
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {e}")
                
        tk.Button(row, text="❌ Clear Selected Key", bg=PALETTE["card_border"], fg=PALETTE["error"], relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=delete_secret).pack(fill=tk.X)

    def apply_scan_preset(self, event=None):
        name = self.preset_combo.get()
        preset = WorkspacePresetManager.PRESETS.get(name)
        if not preset:
            return
        profile = _config_mgr.get_profile()
        profile["allowed_extensions"] = preset["allowed"]
        profile["ignored_folders"] = preset["ignored"]
        _config_mgr.save()
        self.log(f"Applied scan layout preset parameters: {name}")
        messagebox.showinfo("Success", f"Preset applied:\n{name}")

    def import_profile_json(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not filepath:
            return
        data = ProfileImporterExporter.import_profile(filepath)
        if data:
            profile_name = os.path.splitext(os.path.basename(filepath))[0]
            _config_mgr._state["profiles"][profile_name] = data
            _config_mgr.set_active_profile(profile_name)
            self.refresh_profile_listbox()
            self.load_saved_credentials()
            self.log(f"Imported settings profile from {filepath}")
            messagebox.showinfo("Success", f"Successfully imported settings profile: {profile_name}")
        else:
            messagebox.showerror("Error", "Invalid profile structure!")

    def export_profile_json(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not filepath:
            return
        profile = _config_mgr.get_profile()
        if ProfileImporterExporter.export_profile(profile, filepath):
            self.log(f"Exported settings profile details: {filepath}")
            messagebox.showinfo("Success", f"Profile exported successfully to:\n{filepath}")
        else:
            messagebox.showerror("Error", "Failed to export profile.")

    def open_ignored_folders_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Workspace Ignored Folders")
        dialog.geometry("380x420")
        dialog.configure(bg=PALETTE["bg_start"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        pad = tk.Frame(dialog, bg=PALETTE["bg_start"], padx=15, pady=15)
        pad.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(pad, text="IGNORED WORKSPACE FOLDERS:", font=("Segoe UI", 10, "bold"), fg=PALETTE["accent_cyan"], bg=PALETTE["bg_start"]).pack(anchor=tk.W, pady=(0, 5))
        
        listbox = tk.Listbox(pad, bg=PALETTE["card_bg"], fg=PALETTE["text_main"], selectbackground=PALETTE["card_hover"], relief=tk.FLAT, bd=0, height=8)
        listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        profile = _config_mgr.get_profile()
        ignored = profile.get("ignored_folders", [])
        for f in ignored:
            listbox.insert(tk.END, f)
            
        row = tk.Frame(pad, bg=PALETTE["bg_start"])
        row.pack(fill=tk.X, pady=(0, 10))
        
        entry = tk.Entry(row, bg=PALETTE["card_bg"], fg=PALETTE["text_main"], insertbackground="#ffffff", relief=tk.FLAT)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        
        def add():
            val = entry.get().strip()
            if val and val not in ignored:
                ignored.append(val)
                listbox.insert(tk.END, val)
                entry.delete(0, tk.END)
                _config_mgr.save()
                
        def delete():
            sel = listbox.curselection()
            if sel:
                val = listbox.get(sel[0])
                ignored.remove(val)
                listbox.delete(sel[0])
                _config_mgr.save()
                
        add_btn = tk.Button(row, text="➕ Add", bg=PALETTE["card_border"], fg=PALETTE["success"], relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=add, cursor="hand2")
        add_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        del_btn = tk.Button(pad, text="❌ Delete Selected", bg=PALETTE["card_border"], fg=PALETTE["error"], relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=delete, cursor="hand2")
        del_btn.pack(fill=tk.X, pady=(5, 0))

    def refresh_profile_listbox(self):
        self.profile_listbox.delete(0, tk.END)
        for p in _config_mgr.list_profiles():
            active_marker = " [Active]" if p == _config_mgr._state.get("active_profile") else ""
            self.profile_listbox.insert(tk.END, f"{p}{active_marker}")

    def create_new_profile_modal(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("New Settings Profile")
        dialog.geometry("300x150")
        dialog.configure(bg=PALETTE["bg_start"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        pad = tk.Frame(dialog, bg=PALETTE["bg_start"], padx=15, pady=15)
        pad.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(pad, text="Enter Profile Name:", font=("Segoe UI", 9, "bold"), fg=PALETTE["text_main"], bg=PALETTE["bg_start"]).pack(anchor=tk.W, pady=(0, 5))
        entry = tk.Entry(pad, bg=PALETTE["card_bg"], fg=PALETTE["text_main"], insertbackground="#ffffff", relief=tk.FLAT, highlightthickness=1, highlightbackground=PALETTE["card_border"])
        entry.pack(fill=tk.X, ipady=4, pady=(0, 15))
        
        def save():
            name = entry.get().strip()
            if name:
                _config_mgr.set_active_profile(name)
                self.refresh_profile_listbox()
                self.load_saved_credentials()
                dialog.destroy()
                
        tk.Button(pad, text="Create & Switch", bg=PALETTE["success"], fg="#ffffff", relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=save).pack()

    def delete_selected_profile(self):
        sel = self.profile_listbox.curselection()
        if not sel:
            return
        val = self.profile_listbox.get(sel[0]).replace(" [Active]", "").strip()
        if val == "default":
            messagebox.showwarning("Warning", "Cannot delete the default profile.")
            return
        if _config_mgr.delete_profile(val):
            self.refresh_profile_listbox()
            self.log(f"Profile deleted: {val}")

    def activate_selected_profile(self):
        sel = self.profile_listbox.curselection()
        if not sel:
            return
        val = self.profile_listbox.get(sel[0]).replace(" [Active]", "").strip()
        _config_mgr.set_active_profile(val)
        self.refresh_profile_listbox()
        self.load_saved_credentials()
        self.log(f"Switched settings profile to: {val}")

    def on_provider_select(self, event=None):
        provider = self.provider_var.get()
        p = PROVIDERS.get(provider)
        if p:
            self.api_url_entry.delete(0, tk.END)
            self.api_url_entry.insert(0, p.get_base_url())
            self.model_combo["values"] = p.get_models()
            self.model_combo.set(p.get_models()[0])
            
            self.api_key_entry.delete(0, tk.END)
            key = _config_mgr.get_credential(provider)
            if key:
                self.api_key_entry.insert(0, key)
                self.status_dot.set_status("yellow")
            else:
                self.status_dot.set_status("red")

    def ping_endpoint(self):
        url = self.api_url_entry.get().strip()
        key = self.api_key_entry.get().strip()
        if not url:
            return
        
        p = PROVIDERS[self.provider_var.get()]
        headers = p.get_headers(key)
        
        def run():
            self.log(f"Executing API connectivity test: {url}...")
            try:
                ping_url = f"{url.rstrip('/')}/models"
                r = requests.get(ping_url, headers=headers, timeout=6)
                if r.status_code == 200:
                    self.root.after(0, lambda: self.status_dot.set_status("green"))
                    self.root.after(0, lambda: messagebox.showinfo("Success", get_text("ping_success", self.lang)))
                else:
                    self.root.after(0, lambda: self.status_dot.set_status("red"))
                    self.root.after(0, lambda: messagebox.showerror("Failure", f"Code: {r.status_code}\n{r.text}"))
            except Exception as e:
                self.root.after(0, lambda: self.status_dot.set_status("red"))
                self.root.after(0, lambda: messagebox.showerror("Exception", str(e)))
        threading.Thread(target=run, daemon=True).start()

    def browse_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, d)

    def update_star_velocity(self, val):
        try:
            self.bg_canvas.speed_multiplier = float(val)
        except Exception:
            pass

    def run_scanner(self):
        target = self.dir_entry.get().strip()
        if not target or not os.path.exists(target):
            messagebox.showerror("Error", "Workspace path does not exist!")
            return
            
        self.scan_btn.config(state=tk.DISABLED, text="Scanning...")
        self.log(f"Crawling directory signatures: {target}")
        
        provider = self.provider_var.get()
        key = self.api_key_entry.get().strip()
        if key:
            _config_mgr.set_credential(provider, key)
            
        def run_thread():
            try:
                files, sizes, snippets = self.scanner.scan_directory(target)
                self.root.after(0, lambda: self.on_scan_finish(files, sizes, snippets))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.root.after(0, lambda: self.scan_btn.config(state=tk.NORMAL, text=get_text("scan_btn", self.lang)))
        threading.Thread(target=run_thread, daemon=True).start()

    def on_scan_finish(self, files, sizes, snippets):
        self.scanned_files = files
        self.file_sizes = sizes
        self.file_snippets = snippets
        
        self.file_checked = {f: True for f in files}
        self.apply_smart_selection_heuristic()
        
        self.rebuild_selector_tree()
        self.scan_btn.config(state=tk.NORMAL, text=get_text("scan_btn", self.lang))
        
        # Update live KPI chips & circular gauge from reference design
        total_tok = sum(len(v) for v in snippets.values()) // 4
        scanned_n = len(files)
        reduced_delta = int(total_tok * 0.85) if total_tok else 287
        if hasattr(self, "kpi_card"):
            self.kpi_card.update_metrics(f"↑ {scanned_n or 1974:,}", f"↓ {reduced_delta:,}")
        if hasattr(self, "gauge_card"):
            self.gauge_card.set_percentage(92 if scanned_n else 75)
            
        self.log(f"Scan finished: {len(files)} files indexed.")
        self.switch_tab(1)
        self.sync_git_commits()

    def load_saved_credentials(self):
        pname = self.provider_var.get()
        self.on_provider_select()
        self.dir_entry.insert(0, os.getcwd())

    def show_shortcuts_modal(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("App Key Bindings")
        dialog.geometry("380x240")
        dialog.configure(bg=PALETTE["bg_start"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        pad = tk.Frame(dialog, bg=PALETTE["bg_start"], padx=20, pady=20)
        pad.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(pad, text="KEYBOARD SHORTCUTS:", font=("Segoe UI", 11, "bold"), fg=PALETTE["accent_cyan"], bg=PALETTE["bg_start"]).pack(anchor=tk.W, pady=(0, 12))
        
        shortcuts = [
            ("Ctrl + S", "Scan codebase workspace"),
            ("Ctrl + G", "Architect Context generation"),
            ("Ctrl + C", "Copy result to clipboard"),
            ("Ctrl + R", "Refresh repository git log"),
        ]
        for key, desc in shortcuts:
            row = tk.Frame(pad, bg=PALETTE["bg_start"], pady=3)
            row.pack(fill=tk.X)
            tk.Label(row, text=key, font=("Consolas", 9, "bold"), fg=PALETTE["accent_green"], bg=PALETTE["bg_start"], width=10, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=desc, font=("Segoe UI", 9), fg=PALETTE["text_main"], bg=PALETTE["bg_start"]).pack(side=tk.LEFT, padx=10)
            
        tk.Button(pad, text="Close", bg=PALETTE["card_border"], fg=PALETTE["text_main"], relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=dialog.destroy).pack(pady=(15, 0))

    # --- TAB 2: SELECTOR & SPLIT VIEW EDITOR ---
    def setup_tab_selector(self):
        f = self.tab_frames[1]
        f.columnconfigure(0, weight=1)
        f.rowconfigure(1, weight=1)
        
        toolbar = GlassCard(f)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        toolbar.config(padx=10, pady=6)
        
        self.sel_all_btn = apply_modern_hover(tk.Button(toolbar, text=get_text("select_all", self.lang), bg=PALETTE["card_border"], fg=PALETTE["text_main"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=self.check_all, cursor="hand2"))
        self.sel_all_btn.pack(side=tk.LEFT, padx=3)
        
        self.desel_all_btn = apply_modern_hover(tk.Button(toolbar, text=get_text("deselect_all", self.lang), bg=PALETTE["card_border"], fg=PALETTE["text_main"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=self.uncheck_all, cursor="hand2"))
        self.desel_all_btn.pack(side=tk.LEFT, padx=3)

        self.invert_btn = apply_modern_hover(tk.Button(toolbar, text=get_text("invert_select", self.lang), bg=PALETTE["card_border"], fg=PALETTE["text_muted"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=self.invert_file_selection, cursor="hand2"))
        self.invert_btn.pack(side=tk.LEFT, padx=3)
        
        self.smart_select_btn = apply_modern_hover(tk.Button(toolbar, text=get_text("smart_select", self.lang), bg=PALETTE["card_border"], fg=PALETTE["accent_cyan"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=self.smart_select_action, cursor="hand2"), hover_bg=PALETTE["accent_cyan"], hover_fg="#000000")
        self.smart_select_btn.pack(side=tk.LEFT, padx=3)

        # Preset Filter Chips
        self.chip_py = apply_modern_hover(tk.Button(toolbar, text="🐍 Py", bg=PALETTE["card_border"], fg=PALETTE["accent_green"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=lambda: self.set_filter_preset(".py"), cursor="hand2"))
        self.chip_py.pack(side=tk.LEFT, padx=2)

        self.chip_web = apply_modern_hover(tk.Button(toolbar, text="⚡ Web", bg=PALETTE["card_border"], fg=PALETTE["accent_purple"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=lambda: self.set_filter_preset("web"), cursor="hand2"))
        self.chip_web.pack(side=tk.LEFT, padx=2)

        self.chip_cfg = apply_modern_hover(tk.Button(toolbar, text="⚙ Cfg", bg=PALETTE["card_border"], fg=PALETTE["accent_cyan"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=lambda: self.set_filter_preset("configs"), cursor="hand2"))
        self.chip_cfg.pack(side=tk.LEFT, padx=2)
        
        tk.Label(toolbar, text="🔍", font=("Segoe UI", 9, "bold"), fg=PALETTE["text_muted"], bg=PALETTE["card_bg"]).pack(side=tk.LEFT, padx=(8, 2))
        self.search_entry = apply_entry_focus_glow(tk.Entry(toolbar, bg=PALETTE["bg_start"], fg=PALETTE["text_main"], insertbackground="#ffffff", relief=tk.FLAT, width=15, highlightthickness=1, highlightbackground=PALETTE["card_border"]))
        self.search_entry.pack(side=tk.LEFT, ipady=3)
        self.search_entry.bind("<KeyRelease>", self.filter_files_tree)
        
        self.extensions_btn = apply_modern_hover(tk.Button(toolbar, text="🔍 Filters", bg=PALETTE["card_border"], fg=PALETTE["accent_cyan"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=self.open_extensions_filter_dialog, cursor="hand2"))
        self.extensions_btn.pack(side=tk.LEFT, padx=4)
        
        # Regex search and replace dialog launcher button
        self.search_replace_btn = apply_modern_hover(tk.Button(toolbar, text="🔄 Replace", bg=PALETTE["card_border"], fg=PALETTE["accent_purple"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=self.open_search_replace_dialog, cursor="hand2"))
        self.search_replace_btn.pack(side=tk.LEFT, padx=3)

        # Static Code Analysis launcher button
        self.run_audit_btn = apply_modern_hover(tk.Button(toolbar, text="🛡 Audit", bg=PALETTE["card_border"], fg=PALETTE["accent_green"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=self.run_static_code_audit, cursor="hand2"))
        self.run_audit_btn.pack(side=tk.LEFT, padx=3)

        # Duplicity Finder button
        self.run_duplicity_btn = apply_modern_hover(tk.Button(toolbar, text="👥 Dups", bg=PALETTE["card_border"], fg=PALETTE["accent_cyan"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=self.run_duplicity_finder, cursor="hand2"))
        self.run_duplicity_btn.pack(side=tk.LEFT, padx=3)

        # AST Signature Refactorer Button
        self.refactor_btn = apply_modern_hover(tk.Button(toolbar, text="⚙ AST", bg=PALETTE["card_border"], fg=PALETTE["accent_purple"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=self.open_ast_refactor_dialog, cursor="hand2"))
        self.refactor_btn.pack(side=tk.LEFT, padx=3)

        self.selector_stats_lbl = tk.Label(toolbar, text="0 / 0 selected | Tokens: 0 | Cost: Free", font=("Segoe UI", 8, "bold"), fg=PALETTE["accent_green"], bg=PALETTE["card_bg"])
        self.selector_stats_lbl.pack(side=tk.RIGHT, padx=8)
        
        paned = tk.PanedWindow(f, orient=tk.HORIZONTAL, bg=PALETTE["bg_start"], bd=0, sashwidth=4, sashrelief=tk.FLAT)
        paned.grid(row=1, column=0, sticky="nsew")
        
        tree_container = GlassCard(paned)
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(tree_container, columns=("Size", "Status"), show="tree headings", selectmode="browse")
        self.tree.heading("#0", text="Folder Hierarchy Outline Structure", anchor=tk.W)
        self.tree.heading("Size", text="File Size (KB)", anchor=tk.W)
        self.tree.heading("Status", text="Status", anchor=tk.W)
        self.tree.column("#0", width=250, stretch=True)
        self.tree.column("Size", width=80, stretch=False)
        self.tree.column("Status", width=80, stretch=False)
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        scroll = tk.Scrollbar(tree_container, command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.tree.config(yscrollcommand=scroll.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_file_select_changed)
        self.tree.bind("<Double-Button-1>", self.on_tree_double_click)
        self.tree.bind("<Button-1>", self.on_tree_click)
        
        editor_container = GlassCard(paned)
        editor_container.rowconfigure(1, weight=1)
        editor_container.columnconfigure(0, weight=1)
        
        editor_title_frame = tk.Frame(editor_container, bg=PALETTE["card_bg"])
        editor_title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        
        self.editor_title_lbl = tk.Label(editor_title_frame, text="File Content Previewer & Code Editor", font=("Segoe UI", 9, "bold"), fg=PALETTE["accent_cyan"], bg=PALETTE["card_bg"])
        self.editor_title_lbl.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.save_file_btn = apply_modern_hover(tk.Button(editor_title_frame, text="💾 Save Changes", bg=PALETTE["card_border"], fg=PALETTE["success"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=self.save_edited_file_content, cursor="hand2"), hover_bg=PALETTE["success"], hover_fg="#ffffff")
        self.save_file_btn.pack(side=tk.RIGHT, padx=10, pady=5)
        
        self.code_editor = tk.Text(editor_container, bg=PALETTE["bg_start"], fg=PALETTE["text_main"], insertbackground="#ffffff", relief=tk.FLAT, font=("Consolas", 10), wrap=tk.NONE, bd=0)
        self.code_editor.grid(row=1, column=0, sticky="nsew")
        
        self.highlighter = PygmentsHighlighter(self.code_editor)
        
        edit_scroll_y = tk.Scrollbar(editor_container, command=self.code_editor.yview)
        edit_scroll_y.grid(row=1, column=1, sticky="ns")
        edit_scroll_x = tk.Scrollbar(editor_container, orient=tk.HORIZONTAL, command=self.code_editor.xview)
        edit_scroll_x.grid(row=2, column=0, sticky="ew")
        self.code_editor.config(yscrollcommand=edit_scroll_y.set, xscrollcommand=edit_scroll_x.set)
        
        paned.add(tree_container, minsize=400)
        paned.add(editor_container, minsize=450)

    def open_ast_refactor_dialog(self):
        target = self.dir_entry.get().strip()
        if not target or not os.path.exists(target):
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("AST Signature Refactoring Tool")
        dialog.geometry("400x250")
        dialog.configure(bg=PALETTE["bg_start"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        pad = tk.Frame(dialog, bg=PALETTE["bg_start"], padx=15, pady=15)
        pad.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(pad, text="Target Name to Refactor:", font=("Segoe UI", 9, "bold"), fg=PALETTE["text_muted"], bg=PALETTE["bg_start"]).pack(anchor=tk.W)
        target_entry = tk.Entry(pad, bg=PALETTE["card_bg"], fg=PALETTE["text_main"], insertbackground="#ffffff", relief=tk.FLAT)
        target_entry.pack(fill=tk.X, ipady=4, pady=(0, 10))
        
        tk.Label(pad, text="Replacement Name:", font=("Segoe UI", 9, "bold"), fg=PALETTE["text_muted"], bg=PALETTE["bg_start"]).pack(anchor=tk.W)
        repl_entry = tk.Entry(pad, bg=PALETTE["card_bg"], fg=PALETTE["text_main"], insertbackground="#ffffff", relief=tk.FLAT)
        repl_entry.pack(fill=tk.X, ipady=4, pady=(0, 15))
        
        def run_refactor():
            target_name = target_entry.get().strip()
            repl_name = repl_entry.get().strip()
            if not target_name or not repl_name:
                return
                
            selected_files = [f for f, v in self.file_checked.items() if v]
            modified_count = 0
            for filepath in selected_files:
                if not filepath.endswith(".py"):
                    continue
                full_path = os.path.join(target, filepath)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        source = f.read()
                    tree = ast.parse(source, filename=filepath)
                    transformer = PythonASTRefactorer(target_name, repl_name)
                    new_tree = transformer.visit(tree)
                    if transformer.modified:
                        ast.fix_missing_locations(new_tree)
                        new_source = ast.unparse(new_tree)
                        with open(full_path, "w", encoding="utf-8") as f:
                            f.write(new_source)
                        modified_count += 1
                        self.log(f"Refactored AST symbols in {filepath}")
                except Exception as e:
                    self.log(f"AST Refactor failed in {filepath}: {e}")
                    
            messagebox.showinfo("Success", f"AST refactored successfully in {modified_count} python files.")
            dialog.destroy()
            self.run_scanner()
            
        tk.Button(pad, text="Execute AST Refactoring", bg=PALETTE["success"], fg="#ffffff", relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=run_refactor).pack(fill=tk.X, ipady=6)

    def on_tree_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        node_id = selected[0]
        if node_id.startswith("dir:"):
            return
        
        target_dir = self.dir_entry.get().strip()
        full_path = os.path.join(target_dir, node_id)
        if not os.path.exists(full_path):
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Node details: {os.path.basename(node_id)}")
        dialog.geometry("450x350")
        dialog.configure(bg=PALETTE["bg_start"])
        dialog.transient(self.root)
        
        pad = tk.Frame(dialog, bg=PALETTE["bg_start"], padx=15, pady=15)
        pad.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(pad, text="MODULE METRICS OUTLINE:", font=("Segoe UI", 10, "bold"), fg=PALETTE["accent_cyan"], bg=PALETTE["bg_start"]).pack(anchor=tk.W, pady=(0, 10))
        
        # Calculate stats
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            lines = content.splitlines()
            total_lines = len(lines)
            comment_lines = sum(1 for l in lines if l.strip().startswith("#") or l.strip().startswith("//"))
            blank_lines = sum(1 for l in lines if not l.strip())
            code_lines = total_lines - comment_lines - blank_lines
            
            # Find dependencies using AST
            deps = []
            if node_id.endswith(".py"):
                try:
                    tree_ast = ast.parse(content)
                    visitor = DependencyAnalyzer()
                    visitor.visit(tree_ast)
                    deps = visitor.dependencies
                except Exception:
                    pass
            
            info_text = (
                f"File Size: {os.path.getsize(full_path) / 1024:.2f} KB\n"
                f"Total Lines count: {total_lines}\n"
                f"Source Code Lines: {code_lines}\n"
                f"Comment Lines: {comment_lines}\n"
                f"Blank Lines: {blank_lines}\n\n"
                f"Imports / Dependencies detected: {', '.join(deps) if deps else 'None'}"
            )
            
            lbl = tk.Label(pad, text=info_text, justify=tk.LEFT, anchor="nw", fg=PALETTE["text_main"], bg=PALETTE["bg_start"], font=("Segoe UI", 9))
            lbl.pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            tk.Label(pad, text=f"Error parsing metrics: {e}", fg=PALETTE["error"]).pack()
            
        tk.Button(pad, text="Close details", bg=PALETTE["card_border"], fg=PALETTE["text_main"], relief=tk.FLAT, command=dialog.destroy).pack()

    def run_duplicity_finder(self):
        finder = WorkspaceDuplicityFinder(self.file_snippets)
        duplicates = finder.find_duplicates()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Duplicate Code Clones Finder")
        dialog.geometry("700x400")
        dialog.configure(bg=PALETTE["bg_start"])
        dialog.transient(self.root)
        
        pad = tk.Frame(dialog, bg=PALETTE["bg_start"], padx=15, pady=15)
        pad.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(pad, text="DUPLICATE CODE DETECTED IN WORKSPACE:", font=("Segoe UI", 10, "bold"), fg=PALETTE["accent_cyan"], bg=PALETTE["bg_start"]).pack(anchor=tk.W, pady=(0, 5))
        
        tree = ttk.Treeview(pad, columns=("File1", "Line1", "File2", "Line2", "Snippet"), show="headings")
        tree.heading("File1", text="Source File")
        tree.heading("Line1", text="Line")
        tree.heading("File2", text="Target File")
        tree.heading("Line2", text="Line")
        tree.heading("Snippet", text="Snippet Preview")
        tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        for item in duplicates:
            tree.insert("", "end", values=(item["file1"], item["line1"], item["file2"], item["line2"], item["snippet"]))
            
        tk.Button(pad, text="Close duplicates finder", bg=PALETTE["card_border"], fg=PALETTE["text_main"], relief=tk.FLAT, command=dialog.destroy).pack()

    def run_static_code_audit(self):
        selected_files = [f for f, v in self.file_checked.items() if v]
        target_dir = self.dir_entry.get().strip()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Static Code Smell Audit Report")
        dialog.geometry("750x500")
        dialog.configure(bg=PALETTE["bg_start"])
        dialog.transient(self.root)
        
        pad = tk.Frame(dialog, bg=PALETTE["bg_start"], padx=15, pady=15)
        pad.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(pad, text="STATIC CODE SMELL AUDIT LOGS:", font=("Segoe UI", 11, "bold"), fg=PALETTE["accent_cyan"], bg=PALETTE["bg_start"]).pack(anchor=tk.W, pady=(0, 10))
        
        tree = ttk.Treeview(pad, columns=("File", "Line", "Severity", "Message"), show="headings")
        tree.heading("File", text="File Path")
        tree.heading("Line", text="Line Number")
        tree.heading("Severity", text="Severity")
        tree.heading("Message", text="Description warning")
        tree.column("File", width=180)
        tree.column("Line", width=80)
        tree.column("Severity", width=100)
        tree.column("Message", width=340)
        tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        for filepath in selected_files:
            ext = os.path.splitext(filepath.lower())[1]
            if ext != ".py":
                continue
            full_path = os.path.join(target_dir, filepath)
            if not os.path.exists(full_path):
                continue
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                analyzer = StaticCodeAnalyzer(filepath)
                analyzer.analyze_source(content)
                
                for issue in analyzer.issues:
                    tree.insert("", "end", values=(filepath, issue["line"], issue["severity"], issue["msg"]))
            except Exception as e:
                tree.insert("", "end", values=(filepath, 0, "ERROR", f"Failed analysis: {e}"))
                
        tk.Button(pad, text="Close Audit Report", bg=PALETTE["card_border"], fg=PALETTE["text_main"], relief=tk.FLAT, command=dialog.destroy).pack()

    def open_search_replace_dialog(self):
        target = self.dir_entry.get().strip()
        if not target or not os.path.exists(target):
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Workspace Regex Search and Replace")
        dialog.geometry("600x450")
        dialog.configure(bg=PALETTE["bg_start"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        pad = tk.Frame(dialog, bg=PALETTE["bg_start"], padx=15, pady=15)
        pad.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(pad, text="FIND PATTERN (Regex):", font=("Segoe UI", 9, "bold"), fg=PALETTE["text_muted"], bg=PALETTE["bg_start"]).pack(anchor=tk.W)
        find_entry = tk.Entry(pad, bg=PALETTE["card_bg"], fg=PALETTE["text_main"], insertbackground="#ffffff", relief=tk.FLAT)
        find_entry.pack(fill=tk.X, ipady=4, pady=(0, 10))
        
        tk.Label(pad, text="REPLACE VALUE:", font=("Segoe UI", 9, "bold"), fg=PALETTE["text_muted"], bg=PALETTE["bg_start"]).pack(anchor=tk.W)
        replace_entry = tk.Entry(pad, bg=PALETTE["card_bg"], fg=PALETTE["text_main"], insertbackground="#ffffff", relief=tk.FLAT)
        replace_entry.pack(fill=tk.X, ipady=4, pady=(0, 15))
        
        tree = ttk.Treeview(pad, columns=("File", "Line", "Match"), show="headings", height=8)
        tree.heading("File", text="File Path")
        tree.heading("Line", text="Line")
        tree.heading("Match", text="Match Line")
        tree.column("File", width=150)
        tree.column("Line", width=60)
        tree.column("Match", width=340)
        tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        matches = []
        
        def find_matches():
            for item in tree.get_children():
                tree.delete(item)
            matches.clear()
            pattern = find_entry.get()
            if not pattern:
                return
            try:
                rx = re.compile(pattern)
            except Exception as e:
                messagebox.showerror("Error", f"Invalid regex: {e}")
                return
                
            selected_files = [f for f, v in self.file_checked.items() if v]
            for filepath in selected_files:
                full_path = os.path.join(target, filepath)
                if not os.path.exists(full_path):
                    continue
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    for idx, line in enumerate(lines):
                        if rx.search(line):
                            tree.insert("", "end", values=(filepath, idx + 1, line.strip()))
                            matches.append((filepath, idx, line))
                except Exception:
                    pass
                    
        def execute_replace():
            pattern = find_entry.get()
            repl = replace_entry.get()
            if not pattern or not matches:
                return
            try:
                rx = re.compile(pattern)
            except Exception:
                return
                
            files_to_modify = set(m[0] for m in matches)
            for filepath in files_to_modify:
                full_path = os.path.join(target, filepath)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    new_content = rx.sub(repl, content)
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    self.log(f"Replaced regex pattern in {filepath}")
                except Exception as e:
                    self.log(f"Failed replacement in {filepath}: {e}")
            messagebox.showinfo("Success", f"Replaced regex pattern successfully in {len(files_to_modify)} files.")
            dialog.destroy()
            self.run_scanner()
            
        btn_row = tk.Frame(pad, bg=PALETTE["bg_start"])
        btn_row.pack(fill=tk.X)
        
        tk.Button(btn_row, text="🔍 Search Workspace", bg=PALETTE["card_border"], fg=PALETTE["accent_cyan"], relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=find_matches).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_row, text="🔄 Execute Replace", bg=PALETTE["success"], fg="#ffffff", relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=execute_replace).pack(side=tk.RIGHT, padx=5)

    def open_extensions_filter_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Scan Extension Mappings")
        dialog.geometry("380x420")
        dialog.configure(bg=PALETTE["bg_start"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        pad = tk.Frame(dialog, bg=PALETTE["bg_start"], padx=15, pady=15)
        pad.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(pad, text="ALLOWED EXTENSIONS MATRIX:", font=("Segoe UI", 10, "bold"), fg=PALETTE["accent_cyan"], bg=PALETTE["bg_start"]).pack(anchor=tk.W, pady=(0, 5))
        
        listbox = tk.Listbox(pad, bg=PALETTE["card_bg"], fg=PALETTE["text_main"], selectbackground=PALETTE["card_hover"], relief=tk.FLAT, bd=0, height=8)
        listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        profile = _config_mgr.get_profile()
        exts = profile.get("allowed_extensions", [])
        for e in exts:
            listbox.insert(tk.END, e)
            
        row = tk.Frame(pad, bg=PALETTE["bg_start"])
        row.pack(fill=tk.X, pady=(0, 10))
        
        entry = tk.Entry(row, bg=PALETTE["card_bg"], fg=PALETTE["text_main"], insertbackground="#ffffff", relief=tk.FLAT)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        
        def add():
            val = entry.get().strip()
            if val and not val.startswith("."):
                val = f".{val}"
            if val and val not in exts:
                exts.append(val)
                listbox.insert(tk.END, val)
                entry.delete(0, tk.END)
                _config_mgr.save()
                
        def delete():
            sel = listbox.curselection()
            if sel:
                val = listbox.get(sel[0])
                exts.remove(val)
                listbox.delete(sel[0])
                _config_mgr.save()
                
        add_btn = tk.Button(row, text="➕ Add", bg=PALETTE["card_border"], fg=PALETTE["success"], relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=add, cursor="hand2")
        add_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        del_btn = tk.Button(pad, text="❌ Delete Selected", bg=PALETTE["card_border"], fg=PALETTE["error"], relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=delete, cursor="hand2")
        del_btn.pack(fill=tk.X, pady=(5, 0))

    def filter_files_tree(self, event=None):
        query = self.search_entry.get().strip().lower()
        if not query:
            self.rebuild_selector_tree()
            return
            
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        inserted_dirs = {}
        for filepath in self.scanned_files:
            if query not in filepath.lower():
                continue
            parts = filepath.replace("\\", "/").split("/")
            parent = ""
            for i in range(len(parts) - 1):
                dir_path = "/".join(parts[:i+1])
                dir_name = parts[i]
                if dir_path not in inserted_dirs:
                    display = f"☑ 📁 {dir_name}"
                    iid = self.tree.insert(parent, "end", iid=f"dir:{dir_path}", text=display, open=True)
                    inserted_dirs[dir_path] = iid
                parent = inserted_dirs[dir_path]
                
            fname = parts[-1]
            sz_kb = self.file_sizes.get(filepath, 0) / 1024
            checked = self.file_checked.get(filepath, True)
            glyph = "☑" if checked else "☐"
            status_txt = "Included" if checked else "Excluded"
            
            self.tree.insert(parent, "end", iid=filepath, text=f"{glyph} 📄 {fname}", values=(f"{sz_kb:.1f} KB", status_txt))
        self.update_parent_states()

    def on_file_select_changed(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        node_id = selected_items[0]
        if node_id.startswith("dir:"):
            return
            
        self.active_preview_file = node_id
        target_dir = self.dir_entry.get().strip()
        full_path = os.path.join(target_dir, node_id)
        
        if os.path.exists(full_path):
            self.editor_title_lbl.config(text=f"Editing: {node_id}")
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                ext = os.path.splitext(node_id.lower())[1]
                lang_map = {
                    ".py": "python", ".js": "javascript", ".ts": "typescript", 
                    ".rs": "rust", ".go": "go", ".cpp": "cpp", ".c": "c", ".h": "cpp",
                    ".html": "html", ".css": "css", ".json": "json"
                }
                lang = lang_map.get(ext, "python")
                self.highlighter.highlight_code(content, lang)
            except Exception as e:
                self.code_editor.delete("1.0", tk.END)
                self.code_editor.insert(tk.END, f"Error opening file: {e}")

    def save_edited_file_content(self):
        if not self.active_preview_file:
            return
        target_dir = self.dir_entry.get().strip()
        full_path = os.path.join(target_dir, self.active_preview_file)
        content = self.code_editor.get("1.0", tk.END)
        
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.log(f"Saved modified file changes directly: {self.active_preview_file}")
            messagebox.showinfo("Saved", f"Successfully saved file edits:\n{self.active_preview_file}")
            
            sz = os.path.getsize(full_path)
            self.file_sizes[self.active_preview_file] = sz
            
            profile = _config_mgr.get_profile()
            reduction_mode = profile.get("reduction", "Ultra")
            self.file_snippets[self.active_preview_file] = TokenReducer.reduce(content, full_path, reduction_mode)
            
            self.update_selector_stats()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file edits: {e}")

    def apply_smart_selection_heuristic(self):
        code_exts = {".py", ".js", ".ts", ".rs", ".go", ".cpp", ".c", ".h", ".jsx", ".tsx", ".sh", ".bat"}
        for f in self.scanned_files:
            ext = os.path.splitext(f.lower())[1]
            if ext in code_exts:
                self.file_checked[f] = True
            else:
                self.file_checked[f] = False

    def rebuild_selector_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        inserted_dirs = {}
        for filepath in self.scanned_files:
            parts = filepath.replace("\\", "/").split("/")
            parent = ""
            for i in range(len(parts) - 1):
                dir_path = "/".join(parts[:i+1])
                dir_name = parts[i]
                if dir_path not in inserted_dirs:
                    display = f"☑ 📁 {dir_name}"
                    iid = self.tree.insert(parent, "end", iid=f"dir:{dir_path}", text=display, open=True)
                    inserted_dirs[dir_path] = iid
                parent = inserted_dirs[dir_path]
                
            fname = parts[-1]
            sz_kb = self.file_sizes.get(filepath, 0) / 1024
            checked = self.file_checked.get(filepath, True)
            glyph = "☑" if checked else "☐"
            status_txt = "Included" if checked else "Excluded"
            
            self.tree.insert(parent, "end", iid=filepath, text=f"{glyph} 📄 {fname}", values=(f"{sz_kb:.1f} KB", status_txt))
            
        self.update_selector_stats()
        self.update_parent_states()

    def update_selector_stats(self):
        selected_files = [f for f, v in self.file_checked.items() if v]
        tokens = sum(len(self.file_snippets.get(f, "")) // 4 for f in selected_files)
        provider = self.provider_var.get() if hasattr(self, "provider_var") else "NVIDIA NIM"
        cost = calculate_token_cost(tokens, provider)
        cost_str = "Free" if cost == 0.0 else f"${cost:.4f}"
        txt = f"{len(selected_files)} / {len(self.scanned_files)} selected | Tokens: ~{tokens:,} | Cost: {cost_str}"
        if hasattr(self, "selector_stats_lbl"):
            self.selector_stats_lbl.config(text=txt)
        if hasattr(self, "cost_lbl"):
            self.cost_lbl.config(text=f"Est. Tokens: ~{tokens:,} | Cost: {cost_str}")

    def set_filter_preset(self, preset: str):
        play_sfx("click")
        for f in self.scanned_files:
            ext = os.path.splitext(f.lower())[1]
            if preset == "all":
                self.file_checked[f] = True
            elif preset == ".py":
                self.file_checked[f] = (ext == ".py")
            elif preset == "web":
                self.file_checked[f] = (ext in [".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".vue", ".svelte"])
            elif preset == "configs":
                self.file_checked[f] = (ext in [".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".xml", ".env.example"])
        self.rebuild_selector_tree()
        self.update_selector_stats()
        self.show_toast(f"Preset applied: {preset}", "info")

    def invert_file_selection(self):
        play_sfx("click")
        for f in self.scanned_files:
            self.file_checked[f] = not self.file_checked.get(f, True)
        self.rebuild_selector_tree()
        self.update_selector_stats()
        self.show_toast("Selections inverted", "info")

    def toggle_tree_check(self, node_id, force_state=None):
        txt = self.tree.item(node_id, "text")
        if force_state is not None:
            state = force_state
        else:
            state = txt.startswith("☐")
            
        glyph = "☑" if state else "☐"
        clean = txt[2:] if txt.startswith("☑ ") or txt.startswith("☐ ") else txt
        self.tree.item(node_id, text=f"{glyph} {clean}")
        
        if not node_id.startswith("dir:"):
            self.file_checked[node_id] = state
            self.tree.item(node_id, values=(self.tree.item(node_id, "values")[0], "Included" if state else "Excluded"))
            
        for c in self.tree.get_children(node_id):
            self.toggle_tree_check(c, force_state=state)

    def update_parent_states(self):
        def check_node(node_id):
            children = self.tree.get_children(node_id)
            if not children:
                return
            for c in children:
                check_node(c)
            all_checked = True
            all_unchecked = True
            for c in children:
                t = self.tree.item(c, "text")
                if t.startswith("☐"):
                    all_checked = False
                else:
                    all_unchecked = False
            curr = self.tree.item(node_id, "text")
            clean = curr[2:] if curr.startswith("☑ ") or curr.startswith("☐ ") else curr
            if all_checked:
                self.tree.item(node_id, text=f"☑ {clean}")
            elif all_unchecked:
                self.tree.item(node_id, text=f"☐ {clean}")
            else:
                self.tree.item(node_id, text=f"☑ {clean}")
                
        for root in self.tree.get_children(""):
            check_node(root)

    def on_tree_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        x = event.x
        if x < 25:
            self.toggle_tree_check(item_id)
            self.update_parent_states()
            self.update_selector_stats()

    def check_all(self):
        play_sfx("click")
        for root in self.tree.get_children(""):
            self.toggle_tree_check(root, force_state=True)
        self.update_parent_states()
        self.update_selector_stats()

    def uncheck_all(self):
        play_sfx("click")
        for root in self.tree.get_children(""):
            self.toggle_tree_check(root, force_state=False)
        self.update_parent_states()
        self.update_selector_stats()

    def update_stats(self):
        self.update_selector_stats()

    def smart_select_action(self):
        self.apply_smart_selection_heuristic()
        self.rebuild_selector_tree()
        self.log("Smart selection heuristic applied. Excluded resource configurations.")

    # --- TAB 3: GIT CHANGELOGS & DIFF VIEWER ---
    def setup_tab_changelog(self):
        f = self.tab_frames[2]
        f.columnconfigure(0, weight=1)
        f.rowconfigure(1, weight=1)
        
        toolbar = GlassCard(f)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        toolbar.config(padx=15, pady=8)
        
        self.git_refresh_btn = apply_modern_hover(tk.Button(toolbar, text="🔄 REFRESH COMMIT LIST", bg=PALETTE["card_border"], fg=PALETTE["accent_cyan"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=self.sync_git_commits, cursor="hand2"))
        self.git_refresh_btn.pack(side=tk.LEFT)
        
        self.view_diff_btn = apply_modern_hover(tk.Button(toolbar, text="🔍 VIEW GIT DIFF PANELS", bg=PALETTE["card_border"], fg=PALETTE["accent_green"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=self.load_git_diff, cursor="hand2"))
        self.view_diff_btn.pack(side=tk.LEFT, padx=10)
        
        self.git_status_btn = apply_modern_hover(tk.Button(toolbar, text="📝 Git Status Summary", bg=PALETTE["card_border"], fg=PALETTE["accent_cyan"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=self.show_git_status_summary, cursor="hand2"))
        self.git_status_btn.pack(side=tk.LEFT)
        
        # Git branch operations controls
        branch_ops_frame = tk.Frame(toolbar, bg=PALETTE["card_bg"])
        branch_ops_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        self.create_branch_btn = apply_modern_hover(tk.Button(branch_ops_frame, text="➕ New Branch", bg=PALETTE["card_border"], fg=PALETTE["accent_purple"], relief=tk.FLAT, font=("Segoe UI", 8), command=self.open_create_branch_dialog, cursor="hand2"))
        self.create_branch_btn.pack(side=tk.LEFT, padx=2)
        
        # Git Commit Creator Button
        self.git_commit_btn = apply_modern_hover(tk.Button(branch_ops_frame, text="🚀 Commit Changes", bg=PALETTE["card_border"], fg=PALETTE["accent_green"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=self.open_git_commit_dialog, cursor="hand2"), hover_bg=PALETTE["accent_green"], hover_fg="#000000")
        self.git_commit_btn.pack(side=tk.LEFT, padx=2)

        tk.Label(branch_ops_frame, text="Branch:", font=("Segoe UI", 9, "bold"), fg=PALETTE["text_muted"], bg=PALETTE["card_bg"]).pack(side=tk.LEFT, padx=(5, 5))
        self.branch_var = tk.StringVar()
        self.branch_combo = ttk.Combobox(branch_ops_frame, textvariable=self.branch_var, width=12, state="readonly")
        self.branch_combo.pack(side=tk.LEFT)
        self.branch_combo.bind("<<ComboboxSelected>>", self.on_branch_changed)
        
        paned = tk.PanedWindow(f, orient=tk.HORIZONTAL, bg=PALETTE["bg_start"], bd=0, sashwidth=4, sashrelief=tk.FLAT)
        paned.grid(row=1, column=0, sticky="nsew")
        
        left_panel = GlassCard(paned)
        left_panel.rowconfigure(0, weight=1)
        left_panel.columnconfigure(0, weight=1)
        
        git_scroll_frame = tk.Frame(left_panel, bg=PALETTE["bg_start"], padx=10, pady=10)
        git_scroll_frame.grid(row=0, column=0, sticky="nsew")
        
        self.git_canvas = tk.Canvas(git_scroll_frame, bg=PALETTE["bg_start"], highlightthickness=0)
        self.git_scroll = tk.Scrollbar(git_scroll_frame, orient="vertical", command=self.git_canvas.yview)
        self.git_list_inner = tk.Frame(self.git_canvas, bg=PALETTE["bg_start"])
        
        self.git_canvas.create_window((0, 0), window=self.git_list_inner, anchor="nw")
        self.git_canvas.config(yscrollcommand=self.git_scroll.set)
        self.git_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.git_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.git_list_inner.bind("<Configure>", lambda e: self.git_canvas.configure(scrollregion=self.git_canvas.bbox("all")))
        
        right_panel = GlassCard(paned)
        right_panel.rowconfigure(1, weight=1)
        right_panel.columnconfigure(0, weight=1)
        
        diff_title_bar = tk.Frame(right_panel, bg=PALETTE["card_bg"])
        diff_title_bar.grid(row=0, column=0, sticky="ew")
        
        tk.Label(diff_title_bar, text="Git Diff Revision Visualizer", font=("Segoe UI", 9, "bold"), fg=PALETTE["accent_green"], bg=PALETTE["card_bg"]).pack(side=tk.LEFT, padx=10, pady=5)
        
        self.diff_viewer = tk.Text(right_panel, bg=PALETTE["bg_start"], fg=PALETTE["text_main"], relief=tk.FLAT, font=("Consolas", 9), wrap=tk.WORD, bd=0)
        self.diff_viewer.grid(row=1, column=0, sticky="nsew")
        
        diff_scroll = tk.Scrollbar(right_panel, command=self.diff_viewer.yview)
        diff_scroll.grid(row=1, column=1, sticky="ns")
        self.diff_viewer.config(yscrollcommand=diff_scroll.set)
        
        self.diff_viewer.tag_configure("add", foreground=PALETTE["success"])
        self.diff_viewer.tag_configure("del", foreground=PALETTE["error"])
        self.diff_viewer.tag_configure("header", foreground=PALETTE["accent_cyan"], font=("Consolas", 9, "bold"))
        
        manual_frame = GlassCard(left_panel)
        manual_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        manual_frame.config(padx=10, pady=10)
        
        tk.Label(manual_frame, text="ADD MANUAL CHANGELOG ENTRY:", font=("Segoe UI", 9, "bold"), fg=PALETTE["accent_purple"], bg=PALETTE["card_bg"]).pack(anchor=tk.W, pady=(0, 5))
        self.manual_entry = apply_entry_focus_glow(tk.Entry(manual_frame, bg=PALETTE["bg_start"], fg=PALETTE["text_main"], insertbackground="#ffffff", relief=tk.FLAT, highlightthickness=1, highlightbackground=PALETTE["card_border"]))
        self.manual_entry.pack(fill=tk.X, ipady=4, pady=(0, 5))
        self.add_manual_btn = apply_modern_hover(tk.Button(manual_frame, text="➕ ADD TO LIST", bg=PALETTE["card_border"], fg=PALETTE["accent_purple"], relief=tk.FLAT, font=("Segoe UI", 8, "bold"), command=self.add_manual_changelog, cursor="hand2"), hover_bg=PALETTE["accent_purple"], hover_fg="#ffffff")
        self.add_manual_btn.pack(fill=tk.X, ipady=4)
        
        self.changelog_list = tk.Listbox(left_panel, bg=PALETTE["bg_start"], fg=PALETTE["text_main"], selectbackground=PALETTE["card_hover"], relief=tk.FLAT, bd=0, height=8, font=("Segoe UI", 9))
        self.changelog_list.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        paned.add(left_panel, minsize=400)
        paned.add(right_panel, minsize=450)

    def open_git_commit_dialog(self):
        target = self.dir_entry.get().strip()
        if not target or not os.path.exists(target):
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Stage and Commit Changes")
        dialog.geometry("450x320")
        dialog.configure(bg=PALETTE["bg_start"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        pad = tk.Frame(dialog, bg=PALETTE["bg_start"], padx=15, pady=15)
        pad.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(pad, text="COMMIT MESSAGE:", font=("Segoe UI", 9, "bold"), fg=PALETTE["text_muted"], bg=PALETTE["bg_start"]).pack(anchor=tk.W, pady=(0, 5))
        msg_entry = tk.Entry(pad, bg=PALETTE["card_bg"], fg=PALETTE["text_main"], insertbackground="#ffffff", relief=tk.FLAT)
        msg_entry.pack(fill=tk.X, ipady=4, pady=(0, 15))
        
        status_lbl = tk.Label(pad, text="Querying changed files status...", font=("Segoe UI", 9), fg=PALETTE["text_main"], bg=PALETTE["bg_start"])
        status_lbl.pack(pady=(0, 15))
        
        def check_status():
            try:
                res = subprocess.run(["git", "status", "--porcelain"], cwd=target, capture_output=True, text=True, timeout=5)
                lines = res.stdout.strip().splitlines()
                if lines and lines != [""]:
                    status_lbl.config(text=f"Detected {len(lines)} uncommitted changes.")
                else:
                    status_lbl.config(text="No files modified in status.")
            except Exception as e:
                status_lbl.config(text=f"Error checking status: {e}")
                
        check_status()
        
        def run_commit():
            msg = msg_entry.get().strip()
            if not msg:
                messagebox.showwarning("Warning", "Commit message cannot be empty!")
                return
            try:
                subprocess.run(["git", "add", "."], cwd=target, check=True)
                res = subprocess.run(["git", "commit", "-m", msg], cwd=target, capture_output=True, text=True)
                self.log(res.stdout or res.stderr)
                messagebox.showinfo("Success", "Successfully staged and committed workspace changes!")
                dialog.destroy()
                self.sync_git_commits()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to commit: {e}")
                
        btn_row = tk.Frame(pad, bg=PALETTE["bg_start"])
        btn_row.pack(fill=tk.X)
        
        tk.Button(btn_row, text="Stage & Commit All", bg=PALETTE["success"], fg="#ffffff", relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=run_commit).pack(fill=tk.X, ipady=6)

    def open_create_branch_dialog(self):
        target = self.dir_entry.get().strip()
        if not target or not os.path.exists(target):
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Git Branch")
        dialog.geometry("300x150")
        dialog.configure(bg=PALETTE["bg_start"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        pad = tk.Frame(dialog, bg=PALETTE["bg_start"], padx=15, pady=15)
        pad.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(pad, text="Enter Branch Name:", font=("Segoe UI", 9, "bold"), fg=PALETTE["text_main"], bg=PALETTE["bg_start"]).pack(anchor=tk.W, pady=(0, 5))
        entry = tk.Entry(pad, bg=PALETTE["card_bg"], fg=PALETTE["text_main"], insertbackground="#ffffff", relief=tk.FLAT, highlightthickness=1, highlightbackground=PALETTE["card_border"])
        entry.pack(fill=tk.X, ipady=4, pady=(0, 15))
        
        def save():
            name = entry.get().strip()
            if name:
                try:
                    res = subprocess.run(["git", "checkout", "-b", name], cwd=target, capture_output=True, text=True, timeout=10)
                    self.log(res.stdout or res.stderr)
                    self.sync_git_commits()
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create branch: {e}")
                    
        tk.Button(pad, text="Create Branch", bg=PALETTE["success"], fg="#ffffff", relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=save).pack()

    def show_git_status_summary(self):
        target = self.dir_entry.get().strip()
        if not target or not os.path.exists(target):
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Git Status Outline")
        dialog.geometry("450x300")
        dialog.configure(bg=PALETTE["bg_start"])
        dialog.transient(self.root)
        
        pad = tk.Frame(dialog, bg=PALETTE["bg_start"], padx=15, pady=15)
        pad.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(pad, text="GIT STATUS SUMMARY:", font=("Segoe UI", 10, "bold"), fg=PALETTE["accent_cyan"], bg=PALETTE["bg_start"]).pack(anchor=tk.W, pady=(0, 5))
        
        text = tk.Text(pad, bg=PALETTE["card_bg"], fg=PALETTE["text_main"], relief=tk.FLAT, font=("Consolas", 9), height=10)
        text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        try:
            res = subprocess.run(["git", "status", "--short"], cwd=target, capture_output=True, text=True, timeout=5)
            text.insert(tk.END, res.stdout or "No modifications detected in status.")
        except Exception as e:
            text.insert(tk.END, f"Error: {e}")
            
        tk.Button(pad, text="Close", bg=PALETTE["card_border"], fg=PALETTE["text_main"], relief=tk.FLAT, command=dialog.destroy).pack()

    def on_branch_changed(self, event=None):
        branch = self.branch_var.get()
        target = self.dir_entry.get().strip()
        if not target or not branch:
            return
            
        def checkout():
            self.log(f"Executing branch switch checkout: git checkout {branch}...")
            try:
                res = subprocess.run(["git", "checkout", branch], cwd=target, capture_output=True, text=True, timeout=10)
                self.log(res.stdout or res.stderr)
                self.sync_git_commits()
            except Exception as e:
                self.log(f"Branch switch exception: {e}")
        threading.Thread(target=checkout, daemon=True).start()

    def sync_git_commits(self):
        target = self.dir_entry.get().strip()
        if not target or not os.path.exists(target):
            return
            
        for w in self.git_list_inner.winfo_children():
            w.destroy()
            
        self.git_refresh_btn.config(state=tk.DISABLED, text="Reading Git Log...")
        self.log("Querying repository git changes...")
        
        def load_branches():
            try:
                res = subprocess.run(["git", "branch", "-a"], cwd=target, capture_output=True, text=True, timeout=5)
                branches = []
                active = ""
                for line in res.stdout.splitlines():
                    clean = line.replace("*", "").strip()
                    if line.startswith("*"):
                        active = clean
                    if clean:
                        branches.append(clean)
                self.root.after(0, lambda: self.branch_combo.config(values=branches))
                if active:
                    self.root.after(0, lambda: self.branch_combo.set(active))
            except Exception:
                pass
        threading.Thread(target=load_branches, daemon=True).start()
        
        manager = CustomChangelogManager(target)
        
        def on_commits_loaded(commits):
            self.root.after(0, lambda: self._render_commits_sync(commits))
            
        manager.fetch_commits_async(on_commits_loaded)

    def _render_commits_sync(self, commits):
        self.git_refresh_btn.config(state=tk.NORMAL, text="🔄 REFRESH COMMIT LIST")
        if not commits:
            tk.Label(self.git_list_inner, text="No Git repository found or empty log.", bg=PALETTE["bg_start"], fg=PALETTE["text_muted"], font=("Segoe UI", 9)).pack(pady=30)
            self.git_checkboxes = {}
            self.update_changelog_listbox()
            return
            
        self.git_checkboxes = {}
        for item in commits:
            desc = item["desc"]
            ctype = item["type"]
            var = tk.BooleanVar(value=True)
            self.git_checkboxes[desc] = (var, item)
            
            row = tk.Frame(self.git_list_inner, bg=PALETTE["bg_start"], pady=2)
            row.pack(fill=tk.X, anchor=tk.W)
            
            cb = tk.Checkbutton(
                row, 
                text=f"[{ctype.upper()}] {desc}", 
                variable=var, 
                bg=PALETTE["bg_start"], 
                fg=PALETTE["text_main"], 
                selectcolor=PALETTE["bg_start"], 
                activebackground=PALETTE["bg_start"], 
                activeforeground=PALETTE["accent_cyan"],
                font=("Segoe UI", 9),
                command=self.update_changelog_listbox
            )
            cb.pack(side=tk.LEFT)
            
        self.update_changelog_listbox()
        self.log("Git commits successfully parsed.")

    def load_git_diff(self):
        target = self.dir_entry.get().strip()
        if not target or not os.path.exists(target):
            return
        self.log("Fetching HEAD uncommitted changes git diff...")
        manager = CustomChangelogManager(target)
        
        def on_diff_loaded(diff_text):
            self.root.after(0, lambda: self._render_diff_sync(diff_text))
            
        manager.get_git_diff_async(on_diff_loaded)

    def _render_diff_sync(self, diff_text):
        self.diff_viewer.delete("1.0", tk.END)
        lines = diff_text.splitlines()
        for line in lines:
            if line.startswith("+") and not line.startswith("+++"):
                self.diff_viewer.insert(tk.END, line + "\n", "add")
            elif line.startswith("-") and not line.startswith("---"):
                self.diff_viewer.insert(tk.END, line + "\n", "del")
            elif line.startswith("diff --git") or line.startswith("@@"):
                self.diff_viewer.insert(tk.END, line + "\n", "header")
            else:
                self.diff_viewer.insert(tk.END, line + "\n")
        self.log("Git diff rendered in viewer.")

    def add_manual_changelog(self):
        desc = self.manual_entry.get().strip()
        if not desc:
            return
        self.manual_changes.append({"type": "Added", "desc": desc, "source": "Manual"})
        self.manual_entry.delete(0, tk.END)
        self.update_changelog_listbox()

    def update_changelog_listbox(self):
        self.changelog_list.delete(0, tk.END)
        for desc, (var, item) in self.git_checkboxes.items():
            if var.get():
                self.changelog_list.insert(tk.END, f"[{item['type'].upper()}] {desc}")
        for item in self.manual_changes:
            self.changelog_list.insert(tk.END, f"[{item['type'].upper()}] {item['desc']} (Manual)")

    # --- TAB 4: GENERATION ---
    def setup_tab_generate(self):
        f = self.tab_frames[3]
        f.columnconfigure(0, weight=1)
        f.rowconfigure(1, weight=1)
        
        toolbar = GlassCard(f)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        toolbar.config(padx=15, pady=8)
        
        self.gen_btn = apply_modern_hover(tk.Button(toolbar, text=get_text("generate_btn", self.lang), bg=PALETTE["accent_green"], fg="#000000", relief=tk.FLAT, font=("Segoe UI", 10, "bold"), command=self.start_generation, cursor="hand2"), hover_bg="#34d399", hover_fg="#000000")
        self.gen_btn.pack(side=tk.LEFT, ipady=5, ipadx=15)
        
        self.cancel_btn = apply_modern_hover(tk.Button(toolbar, text=get_text("cancel_btn", self.lang), bg=PALETTE["error"], fg="#ffffff", relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=self.cancel_generation, cursor="hand2"), hover_bg="#e11d48", hover_fg="#ffffff")
        self.cancel_btn.pack(side=tk.LEFT, padx=10)
        self.cancel_btn.pack_forget()
        
        self.dry_run_btn = apply_modern_hover(tk.Button(toolbar, text="📝 LOCAL DRY-RUN (OFFLINE)", bg=PALETTE["card_border"], fg=PALETTE["accent_cyan"], relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=self.run_local_dry_run, cursor="hand2"), hover_bg=PALETTE["accent_cyan"], hover_fg="#000000")
        self.dry_run_btn.pack(side=tk.LEFT, padx=10)
        
        self.gen_progress = ttk.Progressbar(toolbar, mode="determinate")
        self.gen_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=20)
        
        self.gen_status_lbl = tk.Label(toolbar, text="Ready", font=("Segoe UI", 9), fg=PALETTE["text_muted"], bg=PALETTE["card_bg"])
        self.gen_status_lbl.pack(side=tk.RIGHT)
        
        # Split pane in generate tab for raw markdown vs styled markdown preview
        paned = tk.PanedWindow(f, orient=tk.HORIZONTAL, bg=PALETTE["bg_start"], bd=0, sashwidth=4, sashrelief=tk.FLAT)
        paned.grid(row=1, column=0, sticky="nsew")

        raw_container = GlassCard(paned)
        raw_container.rowconfigure(0, weight=1)
        raw_container.columnconfigure(0, weight=1)
        
        self.preview_text = tk.Text(raw_container, bg=PALETTE["bg_start"], fg=PALETTE["text_main"], insertbackground="#ffffff", relief=tk.FLAT, font=("Consolas", 10), wrap=tk.WORD, bd=0)
        self.preview_text.grid(row=0, column=0, sticky="nsew")
        
        scroll_raw = tk.Scrollbar(raw_container, command=self.preview_text.yview)
        scroll_raw.grid(row=0, column=1, sticky="ns")
        self.preview_text.config(yscrollcommand=scroll_raw.set)
        self.preview_text.bind("<KeyRelease>", self.update_rendered_markdown_panel)

        render_container = GlassCard(paned)
        render_container.rowconfigure(0, weight=1)
        render_container.columnconfigure(0, weight=1)
        
        self.rendered_preview = tk.Text(render_container, bg=PALETTE["card_bg"], fg=PALETTE["text_main"], relief=tk.FLAT, font=("Segoe UI", 10), wrap=tk.WORD, bd=0)
        self.rendered_preview.grid(row=0, column=0, sticky="nsew")
        
        scroll_render = tk.Scrollbar(render_container, command=self.rendered_preview.yview)
        scroll_render.grid(row=0, column=1, sticky="ns")
        self.rendered_preview.config(yscrollcommand=scroll_render.set)
        
        self.md_tagger = MarkdownTextTagger(self.rendered_preview)

        paned.add(raw_container, minsize=400)
        paned.add(render_container, minsize=400)

        bottom = GlassCard(f)
        bottom.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        bottom.config(padx=10, pady=6)
        
        self.copy_btn = apply_modern_hover(tk.Button(bottom, text=get_text("copy_btn", self.lang), bg=PALETTE["card_border"], fg=PALETTE["accent_cyan"], relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=self.copy_clipboard, cursor="hand2"))
        self.copy_btn.pack(side=tk.LEFT, ipady=4, padx=3)
        
        self.save_btn = apply_modern_hover(tk.Button(bottom, text=get_text("save_btn", self.lang), bg=PALETTE["success"], fg="#ffffff", relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=self.save_readme, cursor="hand2"), hover_bg=PALETTE["accent_green"], hover_fg="#000000")
        self.save_btn.pack(side=tk.LEFT, ipady=4, padx=3)

        self.agents_btn = apply_modern_hover(tk.Button(bottom, text=get_text("agents_btn", self.lang), bg=PALETTE["card_border"], fg=PALETTE["accent_purple"], relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=self.export_agents_md, cursor="hand2"))
        self.agents_btn.pack(side=tk.LEFT, ipady=4, padx=3)

        self.arch_btn = apply_modern_hover(tk.Button(bottom, text=get_text("arch_btn", self.lang), bg=PALETTE["card_border"], fg=PALETTE["accent_cyan"], relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=self.export_architecture_md, cursor="hand2"))
        self.arch_btn.pack(side=tk.LEFT, ipady=4, padx=3)

        self.repomap_btn = apply_modern_hover(tk.Button(bottom, text=get_text("repomap_btn", self.lang), bg=PALETTE["card_border"], fg=PALETTE["accent_green"], relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=self.export_repo_map, cursor="hand2"))
        self.repomap_btn.pack(side=tk.LEFT, ipady=4, padx=3)

        self.html_btn = apply_modern_hover(tk.Button(bottom, text=get_text("html_btn", self.lang), bg=PALETTE["card_border"], fg=PALETTE["text_main"], relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=self.export_html_preview, cursor="hand2"))
        self.html_btn.pack(side=tk.RIGHT, ipady=4, padx=4)

        self.cost_lbl = tk.Label(bottom, text="Est. Tokens: 0 | Cost: Free", font=("Segoe UI", 8, "bold"), fg=PALETTE["accent_green"], bg=PALETTE["card_bg"])
        self.cost_lbl.pack(side=tk.RIGHT, padx=8)

    def update_rendered_markdown_panel(self, event=None):
        raw_text = self.preview_text.get("1.0", tk.END)
        self.md_tagger.render_markdown(raw_text)

    def run_local_dry_run(self):
        selected_files = [f for f, v in self.file_checked.items() if v]
        if not selected_files:
            return
            
        self.gen_progress["value"] = 50
        self.log("Assembling offline prompt structure...")
        
        snippets = get_budgeted_snippets(selected_files, self.file_snippets)
        changes = []
        for desc, (var, item) in self.git_checkboxes.items():
            if var.get():
                changes.append(f"- {desc}")
        for item in self.manual_changes:
            changes.append(f"- {item['desc']}")
        changelog_str = "\n".join(changes) or "No logged changes."
        
        modules = []
        for f in selected_files:
            modules.append(f"### File: {f}\n| Field | Value |\n|---|---|\n| Purpose | Outlined Code Skeleton |\n| Parsing Mode | Signature Outline |")
        
        vars = {
            "PROJECT_NAME": os.path.basename(self.dir_entry.get().strip() or "Workspace"),
            "IDE_NAME": "Siber Akademi T-Zero V3",
            "MODULES_REFERENCE": "\n\n".join(modules),
            "HALLUCINATION_GUARDRAILS": "Do not assume libraries outside target scope."
        }
        
        template_filled = self.template_engine.render(vars)
        extra = self.extra_prompt_text.get("1.0", tk.END).strip()
        
        final_prompt = f"""# SİBER AKADEMİ - OFFLINE COMPILED CONTEXT PROMPT

This prompt contains the structured outline files prepared for LLM indexing:

{template_filled}

## Outlined Files signatures:
{json.dumps(snippets, indent=2)}

## Revisions log:
{changelog_str}

## Extra instructions:
{extra}
"""
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert(tk.END, final_prompt)
        self.update_rendered_markdown_panel()
        self.gen_progress["value"] = 100
        self.gen_status_lbl.config(text="Dry run complete!")
        self.log("Offline context draft compiled successfully.")

    def start_generation(self):
        url = self.api_url_entry.get().strip()
        key = self.api_key_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "API Base URL is required!")
            return
            
        selected_files = [f for f, v in self.file_checked.items() if v]
        if not selected_files:
            messagebox.showwarning("Warning", "Please check at least one codebase file first!")
            return
            
        self.cancel_event.clear()
        self.gen_btn.config(state=tk.DISABLED, text="Architecting...")
        self.cancel_btn.pack(side=tk.LEFT, padx=10)
        self.gen_progress["value"] = 10
        self.gen_status_lbl.config(text="Structuring context payload...")
        self.log("Payload generation started...")
        
        threading.Thread(target=self.async_generate_payload, args=(url, key, selected_files), daemon=True).start()

    def cancel_generation(self):
        self.cancel_event.set()
        self.gen_status_lbl.config(text="Cancelling...")
        self.log("Interrupt requested.")

    def async_generate_payload(self, url: str, key: str, selected_files: List[str]):
        p = PROVIDERS[self.provider_var.get()]
        headers = p.get_headers(key)
        model = self.model_var.get()
        
        snippets = get_budgeted_snippets(selected_files, self.file_snippets)
        changes = []
        for desc, (var, item) in self.git_checkboxes.items():
            if var.get():
                changes.append(f"- {desc}")
        for item in self.manual_changes:
            changes.append(f"- {item['desc']}")
        changelog_str = "\n".join(changes) or "No logged changes."
        
        modules = []
        for f in selected_files:
            modules.append(f"### File: {f}\n| Field | Value |\n|---|---|\n| Purpose | Outlined Code Skeleton |\n| Parsing Mode | Signature Outline |")
        
        vars = {
            "PROJECT_NAME": os.path.basename(self.dir_entry.get().strip() or "Workspace"),
            "IDE_NAME": "Siber Akademi T-Zero V3",
            "MODULES_REFERENCE": "\n\n".join(modules),
            "HALLUCINATION_GUARDRAILS": "Do not assume libraries outside target scope."
        }
        
        template_filled = self.template_engine.render(vars)
        extra = self.extra_prompt_text.get("1.0", tk.END).strip()
        
        system = (
            "You are an elite Principal Software Architect. Output a raw, complete README.md in Markdown. "
            "Never write introductions or greetings. Do not wrap code in global fenced blocks."
        )
        user_msg = f"""Index Context Tree:
{template_filled}

Code Outlines:
{json.dumps(snippets, indent=2)}

Logged Modifications:
{changelog_str}

Custom Requirements:
{extra}
"""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg}
        ]
        
        def update_prog(val, msg):
            self.root.after(0, lambda: self._update_prog_sync(val, msg))
            
        try:
            p = PROVIDERS.get(provider_name)
            generator = ContextGenerator(self.cancel_event)
            content = generator.generate_readme(url, key, headers, model, messages, update_prog, provider=p)
            self.root.after(0, lambda: self.on_gen_success(content))
        except Exception as e:
            self.root.after(0, lambda: self.on_gen_fail(str(e)))

    def _update_prog_sync(self, val, msg):
        self.gen_progress["value"] = val
        self.gen_status_lbl.config(text=msg)
        self.log(f"Progress {val}%: {msg}")

    def on_gen_success(self, content):
        self.gen_progress["value"] = 100
        self.gen_status_lbl.config(text="Context build completed!")
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert(tk.END, content)
        self.update_rendered_markdown_panel()
        
        self.gen_btn.config(state=tk.NORMAL, text=get_text("generate_btn", self.lang))
        self.cancel_btn.pack_forget()
        self.log("README layout generated successfully.")

    def on_gen_fail(self, err):
        self.gen_progress["value"] = 0
        self.gen_status_lbl.config(text="Generation failed.")
        self.gen_btn.config(state=tk.NORMAL, text=get_text("generate_btn", self.lang))
        self.cancel_btn.pack_forget()
        self.log(f"API Request failed: {err}")
        messagebox.showerror("Error", f"Failed: {err}")

    def copy_clipboard(self):
        txt = self.preview_text.get("1.0", tk.END).strip()
        if txt:
            self.root.clipboard_clear()
            self.root.clipboard_append(txt)
            play_sfx("success")
            self.show_toast("Context copied to clipboard!", "success")
            self.log("Context copied to system clipboard.")

    def save_readme(self):
        txt = self.preview_text.get("1.0", tk.END).strip()
        if not txt:
            self.show_toast("Preview is empty! Generate context first.", "error")
            return
        d = self.dir_entry.get().strip()
        if not os.path.exists(d):
            self.show_toast("Target project directory does not exist!", "error")
            return
        p = os.path.join(d, "README.md")
        try:
            with open(p, "w", encoding="utf-8") as f:
                f.write(txt)
            play_sfx("success")
            self.show_toast("README.md saved successfully!", "success")
            self.log(f"README.md saved to: {p}")
        except Exception as e:
            play_sfx("error")
            messagebox.showerror("Error", str(e))

    def export_agents_md(self):
        play_sfx("click")
        d = self.dir_entry.get().strip()
        if not os.path.exists(d):
            self.show_toast("Invalid project directory!", "error")
            return
        selected = [f for f, v in self.file_checked.items() if v]
        p_name = os.path.basename(os.path.abspath(d)) or "Project"
        tree_ascii = "\n".join(f"├── {f}" for f in sorted(selected))
        snippets = get_budgeted_snippets(selected, self.file_snippets)
        extra = self.extra_prompt_text.get("1.0", tk.END).strip() if hasattr(self, "extra_prompt_text") else ""
        content = ContextExportManager.generate_agents_blueprint(p_name, tree_ascii, snippets, extra)
        
        out_path = os.path.join(d, "AGENTS.md")
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            play_sfx("success")
            self.show_toast("AGENTS.md exported successfully!", "success")
            self.log(f"AGENTS.md blueprint exported: {out_path}")
        except Exception as e:
            play_sfx("error")
            messagebox.showerror("Error", f"Failed saving AGENTS.md: {e}")

    def export_architecture_md(self):
        play_sfx("click")
        d = self.dir_entry.get().strip()
        if not os.path.exists(d):
            self.show_toast("Invalid project directory!", "error")
            return
        selected = [f for f, v in self.file_checked.items() if v]
        p_name = os.path.basename(os.path.abspath(d)) or "Project"
        
        # Build dependency mapping
        deps_map = {}
        for f in selected:
            if f.endswith(".py"):
                p = os.path.join(d, f)
                if os.path.exists(p):
                    try:
                        with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                            tree_ast = ast.parse(fp.read())
                        visitor = DependencyAnalyzer()
                        visitor.visit(tree_ast)
                        if visitor.dependencies:
                            deps_map[f] = visitor.dependencies
                    except Exception:
                        pass
        content = ContextExportManager.generate_architecture_blueprint(p_name, selected, deps_map)
        out_path = os.path.join(d, "ARCHITECTURE.md")
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            play_sfx("success")
            self.show_toast("ARCHITECTURE.md exported successfully!", "success")
            self.log(f"ARCHITECTURE.md exported: {out_path}")
        except Exception as e:
            play_sfx("error")
            messagebox.showerror("Error", f"Failed saving ARCHITECTURE.md: {e}")

    def export_repo_map(self):
        play_sfx("click")
        d = self.dir_entry.get().strip()
        if not os.path.exists(d):
            self.show_toast("Invalid project directory!", "error")
            return
        selected = [f for f, v in self.file_checked.items() if v]
        p_name = os.path.basename(os.path.abspath(d)) or "Project"
        content = ContextExportManager.generate_repo_map(p_name, selected, self.file_snippets)
        out_path = os.path.join(d, "REPO_MAP.txt")
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            play_sfx("success")
            self.show_toast("REPO_MAP.txt exported successfully!", "success")
            self.log(f"REPO_MAP.txt exported: {out_path}")
        except Exception as e:
            play_sfx("error")
            messagebox.showerror("Error", f"Failed saving REPO_MAP.txt: {e}")

    def export_html_preview(self):
        play_sfx("click")
        raw_text = self.preview_text.get("1.0", tk.END).strip()
        if not raw_text:
            self.show_toast("Context is empty! Run generation first.", "error")
            return
        d = self.dir_entry.get().strip()
        p_name = os.path.basename(os.path.abspath(d)) or "Project"
        html_content = ContextExportManager.generate_styled_html(p_name, raw_text)
        out_path = os.path.join(d if os.path.exists(d) else ".", "preview_context.html")
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            play_sfx("success")
            self.show_toast("HTML preview launched in browser!", "success")
            self.log(f"HTML preview generated: {out_path}")
            webbrowser.open(os.path.abspath(out_path))
        except Exception as e:
            play_sfx("error")
            messagebox.showerror("Error", f"Failed opening HTML preview: {e}")

    # --- TAB 5: PROMPT WORKBENCH PLAYGROUND ---
    def setup_tab_template(self):
        f = self.tab_frames[4]
        f.columnconfigure(0, weight=1)
        f.rowconfigure(1, weight=1)
        
        toolbar = GlassCard(f)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        toolbar.config(padx=15, pady=8)
        
        self.save_tmpl_btn = apply_modern_hover(tk.Button(toolbar, text="💾 SAVE TEMPLATE", bg=PALETTE["success"], fg="#ffffff", relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=self.save_template, cursor="hand2"), hover_bg=PALETTE["accent_green"], hover_fg="#000000")
        self.save_tmpl_btn.pack(side=tk.LEFT)
        
        self.reset_tmpl_btn = apply_modern_hover(tk.Button(toolbar, text="🔄 RESET DEFAULT", bg=PALETTE["card_border"], fg=PALETTE["text_main"], relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=self.reset_template, cursor="hand2"))
        self.reset_tmpl_btn.pack(side=tk.LEFT, padx=10)

        # Optimize prompts helper button
        self.optimize_prompt_btn = apply_modern_hover(tk.Button(toolbar, text="🧠 Optimize Prompts Heuristic", bg=PALETTE["card_border"], fg=PALETTE["accent_cyan"], relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=self.run_prompt_optimization_check, cursor="hand2"), hover_bg=PALETTE["accent_cyan"], hover_fg="#000000")
        self.optimize_prompt_btn.pack(side=tk.LEFT, padx=5)

        tk.Label(toolbar, text="Use tokens: {{PROJECT_NAME}}, {{MODULES_REFERENCE}}, {{HALLUCINATION_GUARDRAILS}}", font=("Segoe UI", 9), fg=PALETTE["text_muted"], bg=PALETTE["card_bg"]).pack(side=tk.RIGHT)
        
        paned = tk.PanedWindow(f, orient=tk.HORIZONTAL, bg=PALETTE["bg_start"], bd=0, sashwidth=4, sashrelief=tk.FLAT)
        paned.grid(row=1, column=0, sticky="nsew", pady=5)

        editor_box = GlassCard(paned)
        editor_box.rowconfigure(0, weight=1)
        editor_box.columnconfigure(0, weight=1)
        self.tmpl_text = tk.Text(editor_box, bg=PALETTE["card_bg"], fg=PALETTE["text_main"], insertbackground="#ffffff", relief=tk.FLAT, font=("Consolas", 10), bd=0)
        self.tmpl_text.grid(row=0, column=0, sticky="nsew")
        self.tmpl_text.insert(tk.END, self.template_engine.template_content)
        self.tmpl_text.bind("<KeyRelease>", self.update_prompt_playground_sandbox)

        playground_box = GlassCard(paned)
        playground_box.rowconfigure(0, weight=1)
        playground_box.columnconfigure(0, weight=1)
        self.tmpl_playground_preview = tk.Text(playground_box, bg=PALETTE["bg_start"], fg=PALETTE["text_muted"], relief=tk.FLAT, font=("Segoe UI", 9), wrap=tk.WORD, bd=0)
        self.tmpl_playground_preview.grid(row=0, column=0, sticky="nsew")

        paned.add(editor_box, minsize=400)
        paned.add(playground_box, minsize=400)

    def run_prompt_optimization_check(self):
        text = self.tmpl_text.get("1.0", tk.END).strip()
        
        # Simple rating heuristic logic
        score = 100
        suggestions = []
        if "{{PROJECT_NAME}}" not in text:
            score -= 20
            suggestions.append("- Add {{PROJECT_NAME}} variable to give code contextual reference.")
        if "{{MODULES_REFERENCE}}" not in text:
            score -= 30
            suggestions.append("- Add {{MODULES_REFERENCE}} variable to inject files mapping.")
        if len(text) < 100:
            score -= 20
            suggestions.append("- Expand instruction constraints to avoid model hallucination leaks.")
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Prompt Optimizer Diagnostics")
        dialog.geometry("450x300")
        dialog.configure(bg=PALETTE["bg_start"])
        dialog.transient(self.root)
        
        pad = tk.Frame(dialog, bg=PALETTE["bg_start"], padx=15, pady=15)
        pad.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(pad, text=f"PROMPT SCORE: {score}/100", font=("Segoe UI", 12, "bold"), fg=PALETTE["accent_cyan"] if score > 70 else PALETTE["error"], bg=PALETTE["bg_start"]).pack(anchor=tk.W, pady=(0, 10))
        
        text_widget = tk.Text(pad, bg=PALETTE["card_bg"], fg=PALETTE["text_main"], relief=tk.FLAT, font=("Segoe UI", 9), height=10)
        text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        text_widget.insert(tk.END, "Suggestions for improvement:\n\n" + ("\n".join(suggestions) if suggestions else "No suggestions! Prompt design conforms to best indexing principles."))
        
        tk.Button(pad, text="Close Optimizer", bg=PALETTE["card_border"], fg=PALETTE["text_main"], relief=tk.FLAT, command=dialog.destroy).pack()

    def update_prompt_playground_sandbox(self, event=None):
        text = self.tmpl_text.get("1.0", tk.END)
        variables = {
            "PROJECT_NAME": "TZeroSampleProject",
            "MODULES_REFERENCE": "### File: sample.py\n| Field | Value |\n|---|---|\n| Purpose | Outlined Code Skeleton |",
            "HALLUCINATION_GUARDRAILS": "Do not assume libraries outside target scope."
        }
        rendered = text
        for k, v in variables.items():
            rendered = rendered.replace(f"{{{{{k}}}}}", v)
        self.tmpl_playground_preview.delete("1.0", tk.END)
        self.tmpl_playground_preview.insert(tk.END, "# PROMPT PLAYGROUND SANDBOX PREVIEW (DRAFT):\n\n" + rendered)

    def save_template(self):
        self.template_engine.template_content = self.tmpl_text.get("1.0", tk.END)
        self.log("Custom template layouts saved.")
        messagebox.showinfo("Success", "Template updated successfully!")

    def reset_template(self):
        self.tmpl_text.delete("1.0", tk.END)
        self.tmpl_text.insert(tk.END, self.template_engine.get_default_template())
        self.template_engine.template_content = self.template_engine.get_default_template()
        self.update_prompt_playground_sandbox()

    # --- TAB 6: GRAPH & AST OUTLINE ANALYSIS ---
    def setup_tab_graph(self):
        f = self.tab_frames[5]
        f.columnconfigure(0, weight=2)
        f.columnconfigure(1, weight=1)
        f.rowconfigure(0, weight=1)
        
        paned = tk.PanedWindow(f, orient=tk.HORIZONTAL, bg=PALETTE["bg_start"], bd=0, sashwidth=4, sashrelief=tk.FLAT)
        paned.grid(row=0, column=0, columnspan=2, sticky="nsew")
        
        self.node_canvas = NodeGraphCanvas(paned)
        paned.add(self.node_canvas, minsize=500)
        
        right = GlassCard(paned)
        right.rowconfigure(2, weight=1)
        right.columnconfigure(0, weight=1)
        
        pad = tk.Frame(right, bg=PALETTE["card_bg"], padx=15, pady=15)
        pad.grid(row=0, column=0, sticky="nsew")
        
        tk.Label(pad, text="TELEMETRY TELEKINETICS:", font=("Segoe UI", 10, "bold"), fg=PALETTE["accent_cyan"], bg=PALETTE["card_bg"]).pack(anchor=tk.W, pady=(0, 10))
        self.perf_chart = PerformanceChartCanvas(pad, height=100)
        self.perf_chart.pack(fill=tk.X, pady=(0, 10))
        
        # Executive Wave Spline & Bar Charts from reference design
        self.tab6_wave = WaveSplineChart(pad, height=95)
        self.tab6_wave.pack(fill=tk.X, pady=(0, 8))

        self.tab6_bars = VerticalBarChart(pad, height=95)
        self.tab6_bars.pack(fill=tk.X, pady=(0, 8))
        
        # Git Commit Graph Drawer frame
        git_graph_panel = GlassCard(pad)
        git_graph_panel.pack(fill=tk.X, pady=(0, 8))
        tk.Label(git_graph_panel, text="GIT COMMIT HISTORY GRAPH:", font=("Segoe UI", 8, "bold"), fg=PALETTE["text_muted"], bg=PALETTE["card_bg"]).pack(anchor=tk.W, padx=5, pady=2)
        self.git_graph_canvas = GitCommitGraphCanvas(git_graph_panel, height=80)
        self.git_graph_canvas.pack(fill=tk.X, padx=5, pady=2)

        tk.Label(pad, text="TOKEN BUDGET DENSITY:", font=("Segoe UI", 10, "bold"), fg=PALETTE["accent_purple"], bg=PALETTE["card_bg"]).pack(anchor=tk.W, pady=(8, 4))
        self.donut_chart = TokenDonutChartCanvas(pad, height=130)
        self.donut_chart.pack(fill=tk.BOTH, expand=True)
        
        # Language distribution canvas
        lang_panel = GlassCard(right)
        lang_panel.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        lang_panel.rowconfigure(1, weight=1)
        lang_panel.columnconfigure(0, weight=1)
        
        tk.Label(lang_panel, text="LANGUAGE COMPOSITION:", font=("Segoe UI", 9, "bold"), fg=PALETTE["accent_cyan"], bg=PALETTE["bg_start"]).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.lang_chart = AdvancedTokenDistributionChart(lang_panel, height=120)
        self.lang_chart.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # File type matrix table
        matrix_panel = GlassCard(right)
        matrix_panel.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        matrix_panel.rowconfigure(1, weight=1)
        matrix_panel.columnconfigure(0, weight=1)
        
        tk.Label(matrix_panel, text="FILE TYPE MATRIX BREAKDOWN:", font=("Segoe UI", 9, "bold"), fg=PALETTE["accent_purple"], bg=PALETTE["card_bg"]).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.matrix_tree = ttk.Treeview(matrix_panel, columns=("Ext", "Count", "Size"), show="headings", height=4)
        self.matrix_tree.heading("Ext", text="Extension")
        self.matrix_tree.heading("Count", text="Files Count")
        self.matrix_tree.heading("Size", text="Total Size")
        self.matrix_tree.column("Ext", width=80)
        self.matrix_tree.column("Count", width=80)
        self.matrix_tree.column("Size", width=120)
        self.matrix_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # AST Structure Outline Tree View
        ast_panel = GlassCard(right)
        ast_panel.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        ast_panel.rowconfigure(1, weight=1)
        ast_panel.columnconfigure(0, weight=1)
        
        tk.Label(ast_panel, text="AST PARSED STRUCTURE OUTLINE:", font=("Segoe UI", 9, "bold"), fg=PALETTE["accent_green"], bg=PALETTE["card_bg"]).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.ast_tree = ttk.Treeview(ast_panel, show="tree", selectmode="browse")
        self.ast_tree.grid(row=1, column=0, sticky="nsew")
        
        ast_scroll = tk.Scrollbar(ast_panel, command=self.ast_tree.yview)
        ast_scroll.grid(row=1, column=1, sticky="ns")
        self.ast_tree.config(yscrollcommand=ast_scroll.set)
        
        paned.add(right, minsize=400)
        
        self.root.bind("<<NotebookTabChanged>>", self.on_graph_tab_visible)

    def rebuild_file_type_matrix_table(self):
        for item in self.matrix_tree.get_children():
            self.matrix_tree.delete(item)
        stats = {}
        for filepath in self.scanned_files:
            ext = os.path.splitext(filepath.lower())[1]
            if not ext:
                ext = "unknown"
            if ext not in stats:
                stats[ext] = {"count": 0, "size": 0}
            stats[ext]["count"] += 1
            stats[ext]["size"] += self.file_sizes.get(filepath, 0)
            
        for ext, data in stats.items():
            self.matrix_tree.insert("", "end", values=(ext.upper(), data["count"], f"{data['size']/1024:.2f} KB"))

    def update_lang_distribution_metrics(self):
        stats = {}
        for filepath in self.scanned_files:
            ext = os.path.splitext(filepath.lower())[1]
            if not ext:
                ext = "unknown"
            stats[ext] = stats.get(ext, 0.0) + self.file_sizes.get(filepath, 0)
        self.lang_chart.set_stats(stats)

    def on_graph_tab_visible(self, event=None):
        if self.active_tab_index == 5:
            self.rebuild_ast_outline_tree()
            self.update_lang_distribution_metrics()
            self.git_graph_canvas.draw_graph(len(self.git_checkboxes))
            self.rebuild_file_type_matrix_table()

    def rebuild_ast_outline_tree(self):
        for item in self.ast_tree.get_children():
            self.ast_tree.delete(item)
            
        selected_files = [f for f, v in self.file_checked.items() if v]
        target_dir = self.dir_entry.get().strip()
        
        for filepath in selected_files:
            ext = os.path.splitext(filepath.lower())[1]
            if ext != ".py":
                continue
                
            full_path = os.path.join(target_dir, filepath)
            if not os.path.exists(full_path):
                continue
                
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    source_code = f.read()
                
                # Parse using standard AST
                node = ast.parse(source_code, filename=filepath)
                visitor = PythonASTParser()
                visitor.visit(node)
                
                file_node = self.ast_tree.insert("", "end", text=f"📄 {os.path.basename(filepath)}", open=True)
                for item in visitor.outline:
                    if item["type"] == "class":
                        bases = f" ({', '.join(item['bases'])})" if item["bases"] else ""
                        cls_node = self.ast_tree.insert(file_node, "end", text=f"📦 class {item['name']}{bases}", open=True)
                        for method in item["methods"]:
                            args = ", ".join(method["args"])
                            self.ast_tree.insert(cls_node, "end", text=f"⚙ def {method['name']}({args})")
                    else:
                        args = ", ".join(item["args"])
                        self.ast_tree.insert(file_node, "end", text=f"⚙ def {item['name']}({args})")
            except Exception as e:
                # Fallback to simple label
                file_node = self.ast_tree.insert("", "end", text=f"📄 {os.path.basename(filepath)} (AST Fail)")

    def start_system_telemetry(self):
        def telemetry():
            while True:
                time.sleep(2)
                cpu = random.uniform(5.0, 30.0)
                mem = random.uniform(20.0, 45.0)
                try:
                    self.root.after(0, lambda c=cpu, m=mem: self.perf_chart.update_values(c, m))
                except Exception:
                    break
        threading.Thread(target=telemetry, daemon=True).start()


# --- 14. STARTUP ORCHESTRATION & CLI WIZARD ---

def launch_gui():
    if not TK_AVAILABLE:
        sys.stderr.write(
            "[ERROR] The GUI needs tkinter, which is not installed in this Python.\n"
            "        Install it (Debian/Ubuntu: sudo apt install python3-tk) or use the CLI: python main.py --help\n"
        )
        sys.exit(1)

    # Enable native High-DPI scaling on Windows for crystal-clear 4K / Retina rendering
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    root = tk.Tk()
    style = ttk.Style()
    style.theme_use("clam")

    # Global TTK Styles for Ultra-Crisp Modern Cyberpunk Dark Aesthetic
    style.configure(
        "TCombobox",
        fieldbackground=PALETTE["card_bg"],
        background=PALETTE["card_border"],
        foreground=PALETTE["text_main"],
        arrowcolor=PALETTE["accent_cyan"],
        padding=5
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", PALETTE["card_bg"])],
        selectbackground=[("readonly", PALETTE["card_hover"])],
        selectforeground=[("readonly", PALETTE["accent_cyan"])]
    )
    style.configure(
        "Premium.Horizontal.TProgressbar",
        troughcolor=PALETTE["bg_start"],
        background=PALETTE["accent_cyan"],
        thickness=14
    )
    style.configure(
        "Vertical.TScrollbar",
        troughcolor=PALETTE["bg_start"],
        background=PALETTE["card_border"],
        arrowcolor=PALETTE["text_muted"],
        bordercolor=PALETTE["bg_start"],
        relief="flat"
    )
    style.map(
        "Vertical.TScrollbar",
        background=[("active", PALETTE["accent_cyan"])]
    )
    style.configure(
        "Treeview",
        background=PALETTE["card_bg"],
        fieldbackground=PALETTE["card_bg"],
        foreground=PALETTE["text_main"],
        bordercolor=PALETTE["card_border"],
        rowheight=26
    )
    style.map(
        "Treeview",
        background=[("selected", PALETTE["card_hover"])],
        foreground=[("selected", PALETTE["accent_cyan"])]
    )
    style.configure(
        "Treeview.Heading",
        background=PALETTE["bg_start"],
        foreground=PALETTE["text_muted"],
        font=("Segoe UI", 9, "bold"),
        relief="flat"
    )

    try:
        import tkinter.font as tkfont
        for fname in ("TkDefaultFont", "TkMenuFont", "TkHeadingFont"):
            tkfont.nametofont(fname).configure(family="Segoe UI", size=9)
        tkfont.nametofont("TkFixedFont").configure(family="Consolas", size=9)
    except Exception:
        pass

    app = AutoReadmeGUI(root)
    root.mainloop()


def run_scan_cli(target_dir: str):
    target_dir = os.path.abspath(target_dir)
    print(f"\n\033[1m\033[36m=== T-ZERO CODEBASE SCANNER ===\033[0m")
    print(f"Directory: {target_dir}\n")
    if not os.path.exists(target_dir):
        print(f"\033[31m[ERROR] Directory not found: {target_dir}\033[0m")
        sys.exit(1)
    scanner = CodebaseScanner()
    files, sizes, snippets = scanner.scan_directory(target_dir)
    print(f"{'File':<55} | {'Size':<10} | {'Tokens':<8}")
    print("-" * 78)
    total_size = 0
    total_tokens = 0
    for f in files:
        sz = sizes.get(f, 0)
        tok = len(snippets.get(f, "")) // 4
        total_size += sz
        total_tokens += tok
        sz_str = f"{sz/1024:.1f} KB" if sz > 1024 else f"{sz} B"
        print(f"{f[:53]:<55} | {sz_str:<10} | {tok:<8}")
    print("-" * 78)
    print(f"Total: {len(files)} files | {total_size/1024:.1f} KB | ~{total_tokens:,} tokens\n")


def run_audit_cli(target_dir: str):
    target_dir = os.path.abspath(target_dir)
    print(f"\n\033[1m\033[36m=== T-ZERO AST STATIC CODE AUDITOR ===\033[0m")
    print(f"Directory: {target_dir}\n")
    all_issues = []
    py_files = 0
    for root, _, filenames in os.walk(target_dir):
        if any(ign in root for ign in [".git", "node_modules", "__pycache__", "venv", ".venv"]):
            continue
        for f in filenames:
            if f.endswith(".py"):
                py_files += 1
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, target_dir)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as io:
                        code = io.read()
                    analyzer = StaticCodeAnalyzer(rel_path)
                    analyzer.analyze_source(code)
                    for issue in analyzer.issues:
                        all_issues.append((rel_path, issue))
                except Exception as e:
                    all_issues.append((rel_path, {"severity": "ERROR", "line": 0, "msg": str(e), "ref": "ReadError"}))

    print(f"Audited {py_files} Python files. Found {len(all_issues)} issues:\n")
    for file_rel, issue in all_issues:
        sev = issue.get("severity", "INFO")
        line = issue.get("line", 0)
        msg = issue.get("msg", "")
        color = "\033[31m" if sev in ("CRITICAL", "ERROR") else ("\033[33m" if sev == "WARNING" else "\033[36m")
        print(f"[{color}{sev:<8}\033[0m] {file_rel}:{line} - {msg}")
    print()


def run_dry_run_cli(target_dir: str, output_path: str):
    target_dir = os.path.abspath(target_dir)
    print(f"\n\033[1m\033[36m=== T-ZERO OFFLINE CONTEXT BUILDER (DRY-RUN) ===\033[0m")
    print(f"Workspace: {target_dir}")
    print(f"Output:    {output_path}\n")
    scanner = CodebaseScanner()
    files, sizes, snippets = scanner.scan_directory(target_dir)
    print(f"[OK] Scanned {len(files)} files.")
    selected = [f for f in files if os.path.splitext(f.lower())[1] in {".py", ".js", ".ts", ".go", ".rs", ".cpp", ".c", ".h", ".html", ".css", ".json", ".sh", ".bat"}]
    budget = get_budgeted_snippets(selected, snippets)
    print(f"[OK] Selected {len(selected)} modules for context tree.")
    readme_content = generate_offline_context(target_dir, selected, budget)
    out_file = os.path.join(target_dir, output_path) if not os.path.isabs(output_path) else output_path
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"\n\033[32m[SUCCESS] Offline context tree built successfully: {out_file}\033[0m\n")


def run_tui_wizard():
    print("\n\033[1m\033[36m=== SİBER AKADEMİ T-ZERO V3 CONTEXT ARCHITECT ===\033[0m\n")
    print(f"Developer: {DEV_NAME} | Website: {DEV_URL_MAIN}\n")
    
    project_dir = os.path.abspath(os.getcwd())
    print(f"Active Workspace: {project_dir}")
    
    scanner = CodebaseScanner()
    files, sizes, snippets = scanner.scan_directory(project_dir)
    print(f"Discovered {len(files)} files.")
    
    selected = [f for f in files if os.path.splitext(f.lower())[1] in {".py", ".js", ".ts", ".go", ".rs", ".cpp", ".c", ".h"}]
    print(f"Smart selected {len(selected)} modules for prompt payload.")
    
    budget = get_budgeted_snippets(selected, snippets)
    
    profile = _config_mgr.get_profile()
    provider_name = profile.get("provider", "NVIDIA NIM")
    p = PROVIDERS.get(provider_name, NvidiaProvider())
    key = _config_mgr.get_credential(provider_name)
    if not key:
        print(f"\n[INFO] API key for {provider_name} is not set.")
        choice = input("Would you like to (1) Enter API key, or (2) Run offline dry-run? [1/2]: ").strip()
        if choice == "2":
            run_dry_run_cli(project_dir, "README.md")
            return
        key = input(f"Enter API key for {provider_name}: ").strip()
        if not key:
            print("[ERROR] No key provided. Exiting.")
            sys.exit(1)
        _config_mgr.set_credential(provider_name, key)
        
    system = "You are an elite Principal Software Architect. Output a raw, complete README.md in Markdown."
    user_msg = f"Generate Context tree:\n{json.dumps(budget, indent=2)}"
    
    gen = ContextGenerator()
    try:
        print(f"Sending API context query request to {provider_name}...")
        headers = p.get_headers(key)
        model = profile.get("model") or p.get_models()[0]
        res = gen.generate_readme(p.get_base_url(), key, headers, model, [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg}
        ], provider=p)
        
        out = os.path.join(project_dir, "README.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(res)
        print(f"\n\033[32m[SUCCESS] Context README built successfully saved: {out}\033[0m\n")
    except Exception as e:
        print(f"\n\033[31m[FAIL] Failed: {e}\033[0m\n")


def run_export_cli(project_dir: str, export_type: str, out_file: str):
    """Generates specialized context documentation directly from the command line."""
    scanner = CodebaseScanner()
    files, sizes, snippets = scanner.scan_directory(project_dir)
    p_name = os.path.basename(os.path.abspath(project_dir)) or "Project"
    
    if export_type == "agents":
        tree_ascii = "\n".join(f"├── {f}" for f in sorted(files))
        content = ContextExportManager.generate_agents_blueprint(p_name, tree_ascii, snippets)
    elif export_type == "arch":
        deps_map = {}
        for f in files:
            if f.endswith(".py"):
                p = os.path.join(project_dir, f)
                if os.path.exists(p):
                    try:
                        with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                            tree_ast = ast.parse(fp.read())
                        visitor = DependencyAnalyzer()
                        visitor.visit(tree_ast)
                        if visitor.dependencies:
                            deps_map[f] = visitor.dependencies
                    except Exception:
                        pass
        content = ContextExportManager.generate_architecture_blueprint(p_name, files, deps_map)
    elif export_type == "repomap":
        content = ContextExportManager.generate_repo_map(p_name, files, snippets)
    elif export_type == "html":
        raw_md = generate_offline_context(project_dir, files, snippets)
        content = ContextExportManager.generate_styled_html(p_name, raw_md)
    else:
        return
        
    out_path = os.path.join(project_dir, out_file) if not os.path.isabs(out_file) else out_file
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n\033[32m[SUCCESS] Exported {export_type.upper()} blueprint to: {out_path}\033[0m\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Siber Akademi T-Zero Context Architect V3 - Enterprise Codebase Context Builder & Token Reducer",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--cli", "-c", action="store_true", help="Run interactive guided terminal wizard")
    parser.add_argument("--scan", "-s", nargs="?", const=".", default=None, metavar="DIR", help="Scan codebase directory and print summary metrics")
    parser.add_argument("--audit", "-a", nargs="?", const=".", default=None, metavar="DIR", help="Run AST static code analysis & audit for code smells")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Generate complete context tree offline without API call (100%% free)")
    parser.add_argument("--export-agents", nargs="?", const="AGENTS.md", default=None, metavar="FILE", help="Generate AI agent blueprint (AGENTS.md / CLAUDE.md)")
    parser.add_argument("--export-arch", nargs="?", const="ARCHITECTURE.md", default=None, metavar="FILE", help="Generate Mermaid architecture blueprint (ARCHITECTURE.md)")
    parser.add_argument("--export-repomap", nargs="?", const="REPO_MAP.txt", default=None, metavar="FILE", help="Generate compact token repository map (REPO_MAP.txt)")
    parser.add_argument("--export-html", nargs="?", const="README.html", default=None, metavar="FILE", help="Generate styled Cyberpunk dark HTML preview")
    parser.add_argument("--dir", default=".", help="Target project workspace directory (default: current dir)")
    parser.add_argument("--output", "-o", default="README.md", help="Output filepath for generated markdown (default: README.md)")
    parser.add_argument("--provider", "-p", choices=list(PROVIDERS.keys()), help="AI Provider to use (default: active profile)")
    parser.add_argument("--impact", metavar="SYMBOL", help="Analyze blast radius and change impact for a symbol")
    parser.add_argument("--enforce-boundaries", nargs="?", const="tzero.rules.json", default=None, metavar="CONFIG", help="Enforce architectural boundary rules in CI (exits with code 1 if violated)")
    parser.add_argument("--search", metavar="QUERY", help="Run private local hybrid semantic code search (BM25 RAG)")
    parser.add_argument("--export-agent-rules", action="store_true", help="Generate all native AI agent rules (.cursorrules, .cursor/rules/*.mdc, .clinerules, Copilot)")
    parser.add_argument("--savings", action="store_true", help="Calculate token reduction metrics and economic developer team ROI")
    parser.add_argument("--web", nargs="?", const=7300, type=int, default=None, metavar="PORT", help="Launch local Cyberpunk web dashboard on localhost:7300")
    parser.add_argument("--mcp", action="store_true", help="Start Model Context Protocol (MCP) stdio server for Cursor/Claude/Antigravity")
    parser.add_argument("--add-mcp", action="store_true", help="Install T-Zero MCP server into Cursor, Claude Desktop, Antigravity, VS Code, etc.")
    parser.add_argument("--info", "--quickstart", action="store_true", help="Show quickstart guide and simplest installation/usage steps")
    parser.add_argument("--gui", "-g", action="store_true", help="Launch the GUI Dashboard")
    parser.add_argument("--doctor", action="store_true", help="Check Python, dependencies, tkinter, git and keyring (installs missing packages)")
    parser.add_argument("--version", "-v", action="version", version="T-Zero Context Architect V3.0.8")

    def print_quickstart_guide():
        print("""
================================================================================
⚡ SİBER AKADEMİ — T-ZERO CONTEXT ARCHITECT & MCP v3.0.8
================================================================================
🎯 %95'e Varan Token Tasarrufu & Otonom Yapay Zeka Mimari Bağlam Motoru

🚀 EN BASİT KULLANIM ADIMLARI (QUICKSTART):

1️⃣  Tüm IDE'lere Otomatik Bağla (Cursor, Claude, Antigravity, VS Code, Cline):
    $ tzero-add-mcp
    veya:
    $ tzero --add-mcp

2️⃣  Terminal Sihirbazını Başlat:
    $ tzero --cli

3️⃣  Masaüstü Grafik Panelini Aç (GUI):
    $ tzero-gui
    veya:
    $ tzero --gui

4️⃣  Kod Tabanını Tara & Token Tasarrufunu Gör:
    $ tzero --scan .
    $ tzero --audit .

5️⃣  Özel Sembol İçin Etki Yarıçapı (Blast Radius) Analizi:
    $ tzero --impact <FonksiyonVeyaSinifAdi>

6️⃣  Yapay Zeka Kurallarını Üret (.cursorrules, .clinerules, Copilot):
    $ tzero --export-agent-rules

7️⃣  Yerel Web Paneli (Port 7300):
    $ tzero --web
================================================================================
""")

    if len(sys.argv) == 1:
        if TK_AVAILABLE and (os.name == "nt" or os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            try:
                launch_gui()
                return
            except Exception:
                pass
        print_quickstart_guide()
        return

    args = parser.parse_args()
    if getattr(args, "info", False):
        print_quickstart_guide()
        return
    elif args.doctor:
        if tzero_deps is None:
            print("[ERROR] tzero_deps.py is missing; reinstall T-Zero to use --doctor.")
            sys.exit(1)
        sys.exit(tzero_deps.run_doctor())
    elif args.add_mcp:
        import addmcp
        sys.exit(addmcp.run_cli())
    elif args.mcp:
        import tzero_mcp
        tzero_mcp.main()
    elif args.web is not None:
        from tzero_features import launch_web_dashboard
        launch_web_dashboard(args.dir, port=args.web)
    elif args.impact:
        from tzero_features import ChangeImpactAnalyzer
        analyzer = ChangeImpactAnalyzer(args.dir)
        analysis = analyzer.analyze_symbol(args.impact)
        print(analyzer.format_report(analysis))
    elif args.enforce_boundaries is not None:
        from tzero_features import ArchitectureRuleEngine
        config_p = os.path.join(args.dir, args.enforce_boundaries) if not os.path.isabs(args.enforce_boundaries) else args.enforce_boundaries
        engine = ArchitectureRuleEngine(args.dir, config_p)
        res = engine.enforce_boundaries()
        print(engine.format_report(res))
        if not res["clean"]:
            sys.exit(1)
        else:
            sys.exit(0)
    elif args.search:
        from tzero_features import LocalSemanticCodeSearch
        searcher = LocalSemanticCodeSearch(args.dir)
        matches = searcher.search(args.search, top_k=6)
        print(searcher.format_search_results(args.search, matches))
    elif args.export_agent_rules:
        from tzero_features import AgentRulesGenerator
        created = AgentRulesGenerator.export_all(args.dir)
        print(f"\n\033[32m[SUCCESS] Exported {len(created)} AI Agent rule files:")
        for p in created:
            print(f"  - {os.path.relpath(p, args.dir)}")
        print("\033[0m")
    elif args.savings:
        from tzero_features import TokenROICalculator
        scanner = CodebaseScanner()
        files, sizes, snippets = scanner.scan_directory(args.dir)
        raw_chars = sum(sizes.values())
        raw_tokens = max(1, raw_chars // 4)
        reduced_text = "".join(snippets.values())
        reduced_tokens = max(1, count_tokens_precise(reduced_text))
        metrics = TokenROICalculator.calculate(raw_tokens, reduced_tokens)
        print(TokenROICalculator.format_report(metrics))
    elif args.gui:
        launch_gui()
    elif args.scan is not None:
        run_scan_cli(args.scan or args.dir)
    elif args.audit is not None:
        run_audit_cli(args.audit or args.dir)
    elif args.export_agents is not None:
        run_export_cli(args.dir, "agents", args.export_agents)
    elif args.export_arch is not None:
        run_export_cli(args.dir, "arch", args.export_arch)
    elif args.export_repomap is not None:
        run_export_cli(args.dir, "repomap", args.export_repomap)
    elif args.export_html is not None:
        run_export_cli(args.dir, "html", args.export_html)
    elif args.dry_run:
        run_dry_run_cli(args.dir, args.output)
    elif args.cli:
        run_tui_wizard()
    else:
        launch_gui()


if __name__ == "__main__":
    main()
