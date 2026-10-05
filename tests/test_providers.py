# -*- coding: utf-8 -*-
"""Unit tests for multi-provider AI adapters."""

import unittest
from tzero_v3 import (
    PROVIDERS,
    NvidiaProvider,
    OpenAIProvider,
    GeminiProvider,
    OpenRouterProvider,
    AnthropicProvider,
    LocalOllamaProvider,
)


class TestProviders(unittest.TestCase):
    def test_registered_providers_count(self):
        self.assertGreaterEqual(len(PROVIDERS), 6)
        expected = ["NVIDIA NIM", "OpenAI", "Google Gemini", "OpenRouter", "Anthropic", "Local Ollama"]
        for exp in expected:
            self.assertIn(exp, PROVIDERS)

    def test_nvidia_provider(self):
        p = PROVIDERS["NVIDIA NIM"]
        self.assertEqual(p.name, "NVIDIA NIM")
        headers = p.get_headers("dummy-nv-key")
        self.assertEqual(headers["X-Nvidia-Api-Key"], "dummy-nv-key")
        self.assertIn("meta/llama-3.3-70b-instruct", p.get_models())
        self.assertTrue(p.get_endpoint_url(p.get_base_url()).endswith("/chat/completions"))

    def test_openai_provider(self):
        p = PROVIDERS["OpenAI"]
        self.assertEqual(p.name, "OpenAI")
        headers = p.get_headers("dummy-openai-key")
        self.assertEqual(headers["Authorization"], "Bearer dummy-openai-key")
        self.assertIn("gpt-4o", p.get_models())

    def test_anthropic_provider(self):
        p = PROVIDERS["Anthropic"]
        self.assertEqual(p.name, "Anthropic")
        headers = p.get_headers("dummy-anthropic-key")
        self.assertEqual(headers["x-api-key"], "dummy-anthropic-key")
        self.assertEqual(headers["anthropic-version"], "2023-06-01")

        # Test endpoint
        endpoint = p.get_endpoint_url("https://api.anthropic.com/v1")
        self.assertTrue(endpoint.endswith("/messages"))

        # Test payload format with system prompt extraction
        messages = [
            {"role": "system", "content": "You are an architect."},
            {"role": "user", "content": "Build context."}
        ]
        payload = p.format_payload("claude-3-7-sonnet-20250219", messages)
        self.assertEqual(payload["model"], "claude-3-7-sonnet-20250219")
        self.assertEqual(payload["system"], "You are an architect.")
        self.assertEqual(len(payload["messages"]), 1)
        self.assertEqual(payload["messages"][0]["role"], "user")

        # Test response parsing
        sample_resp = {
            "content": [
                {"type": "text", "text": "# Anthropic Output Markdown"}
            ]
        }
        parsed = p.parse_response(sample_resp)
        self.assertEqual(parsed, "# Anthropic Output Markdown")

    def test_local_ollama_provider(self):
        p = PROVIDERS["Local Ollama"]
        self.assertEqual(p.name, "Local Ollama")
        self.assertIn("11434", p.get_base_url())
        headers = p.get_headers("")
        self.assertEqual(headers["Content-Type"], "application/json")


if __name__ == "__main__":
    unittest.main()
