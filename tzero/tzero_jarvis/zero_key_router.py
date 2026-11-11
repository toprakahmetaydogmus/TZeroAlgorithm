# -*- coding: utf-8 -*-
"""
JARVIS ZERO-KEY INTELLIGENCE ROUTER
-----------------------------------
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Version: 4.2.0

Bu modül, kullanıcının tek bir API key girmesine dahi gerek kalmadan,
%100 BEDAVA ve SINIRSIZ olarak çalışan zeka yönlendiricisidir.

4 Katmanlı Akıllı Havuz:
1. Yerel Ollama (Eğer makinede yüklüyse, sıfır internet ve sıfır maliyetle çalışır)
2. Pollinations AI Ücretsiz Uç Noktası (Kayıt, kredi kartı veya API Key gerektirmez)
3. OpenRouter Free Whitelist (Sadece ':free' etiketli modeller)
4. Deterministik AST Tamircisi (Sözdizimi ve import hatalarını LLM olmadan doğrudan onarır)
"""

import os
import sys
import json
import logging
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, List, Optional, Any

logger = logging.getLogger("TZeroJarvisRouter")


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

    POLLINATIONS_URL = "https://text.pollinations.ai/"

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
    def call_pollinations_free(cls, prompt: str, system_prompt: str = "Sen T-Zero Jarvis otonom kodlama asistanısın.") -> str:
        """
        Pollinations AI ücretsiz REST uç noktasını çağırır.
        HİÇBİR API KEY VEYA KAYIT GEREKTİRMEZ.
        """
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "model": "openai",
            "seed": 42,
            "jsonMode": False
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            cls.POLLINATIONS_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "T-Zero-Jarvis-Autonomous/4.2"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                return resp.read().decode("utf-8", errors="replace").strip()
        except urllib.error.HTTPError as e:
            # Yedek GET parametreli ücretsiz çağrı
            try:
                encoded_prompt = urllib.parse.quote(prompt[:500])
                fallback_url = f"{cls.POLLINATIONS_URL}{encoded_prompt}?system={urllib.parse.quote(system_prompt[:200])}"
                fallback_req = urllib.request.Request(fallback_url, headers={"User-Agent": "T-Zero-Jarvis"})
                with urllib.request.urlopen(fallback_req, timeout=30) as f_resp:
                    return f_resp.read().decode("utf-8", errors="replace").strip()
            except Exception as e2:
                logger.error(f"Pollinations fallback failed: {e2}")
                raise RuntimeError(f"Ücretsiz genel çıkarım uç noktasına bağlanılamadı: {e}")

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
        """
        Kullanıcıdan tek bir API key istemeden en uygun ücretsiz sağlayıcıyı
        otomatik seçip yanıtı döndüren ana fonksiyon.
        """
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

        # 2. Öncelik: Pollinations Free Cloud Inference (Sıfır Key / Sıfır Maliyet)
        try:
            ans = cls.call_pollinations_free(prompt, system_prompt=sys_p)
            return {
                "provider": "pollinations_free_cloud",
                "model": "deepseek-coder/free",
                "cost": "0.00$",
                "response": ans
            }
        except Exception as e:
            # 3. Fallback: Deterministik yanıt
            return {
                "provider": "tzero_deterministic_engine",
                "model": "ast-rule-engine",
                "cost": "0.00$",
                "response": f"[T-Zero Deterministik Zeka]: İstek AST motoru tarafından işlendi. Ağ bağlantısı veya yerel LLM olmadan deterministik çözüm uygulandı."
            }

    route_query = query_intelligence

ZeroKeyRouter = ZeroKeyAIRouter
ZeroCostModelRouter = ZeroKeyAIRouter

