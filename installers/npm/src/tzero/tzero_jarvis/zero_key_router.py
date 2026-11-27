# -*- coding: utf-8 -*-
"""
JARVIS ZERO-KEY INTELLIGENCE ROUTER
-----------------------------------
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Version: 4.2.0

Runs keyless inference through a local Ollama API and exposes a separate web
search helper.
"""

import json
import urllib.request
from typing import Any, Dict, Optional


class ZeroCostSecurityGuard:
    """Ücretli hiçbir modelin çağrılmamasını garanti eden güvenlik kalkanı."""
    
    FORBIDDEN_MODELS = {
        "gpt-4o", "gpt-4", "claude-3-5-sonnet", "claude-3-opus",
        "gemini-1.5-pro", "super-vl", "nemotron 3.5 super vl"
    }

    @classmethod
    def assert_free(cls, model_name: str):
        m_low = model_name.lower()
        for forbidden in cls.FORBIDDEN_MODELS:
            if forbidden in m_low:
                raise PermissionError(
                    f"[SIFIR MALİYET KALKANI]: '{model_name}' ücretli bir modeldir! "
                    f"T-Zero Jarvis ekosistemi %100 BEDAVA garantisiyle çalışır. Çağrı iptal edildi."
                )


class ZeroKeyAIRouter:
    """API Key gerektirmeyen, hatasız ve yedekli yapay zeka motoru."""

    @classmethod
    def check_ollama_available(cls) -> bool:
        """Yerel makinede Ollama'nın çalışıp çalışmadığını yoklar."""
        try:
            req = urllib.request.Request("http://127.0.0.1:11434/api/tags", headers={"User-Agent": "T-Zero-Jarvis"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    @classmethod
    def call_ollama(cls, prompt: str, model: str = "qwen2.5:3b") -> str:
        """Yerel Ollama servisi üzerinden tamamen internetsiz çıkarım yapar."""
        url = "http://127.0.0.1:11434/api/generate"
        payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "")

    @classmethod
    def search_duckduckgo_free(cls, query: str, max_results: int = 4) -> str:
        """API anahtarı olmadan canlı internet araması yapar."""
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                if not results:
                    return f"'{query}' için sonuç bulunamadı."
                out = []
                for idx, r in enumerate(results, 1):
                    out.append(f"{idx}. {r.get('title', '')}\n   {r.get('href', '')}\n   {r.get('body', '')}")
                return "\n\n".join(out)
        except Exception as e:
            return f"Web arama servisi ulaşılamadı ({e})"

    @classmethod
    def query_intelligence(cls, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Return an Ollama completion or report that local inference is unavailable."""
        sys_p = system_prompt or "Sen Siber Akademi T-Zero Jarvis otonom yazılım mühendisisin."

        # 1. Öncelik: Yerel Ollama (Maksimum Gizlilik & Sıfır İnternet)
        if cls.check_ollama_available():
            try:
                ans = cls.call_ollama(f"{sys_p}\n\nKullanıcı: {prompt}")
                if ans.strip():
                    return {
                        "provider": "ollama_local",
                        "model": "local-qwen/llama",
                        "cost": "0.00$",
                        "response": ans
                    }
            except Exception:
                pass

        return {
            "provider": "unavailable",
            "model": "",
            "cost": "0.00$",
            "response": "Local Ollama is unavailable or returned no response.",
        }

    route_query = query_intelligence

ZeroKeyRouter = ZeroKeyAIRouter
ZeroCostModelRouter = ZeroKeyAIRouter

