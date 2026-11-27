# -*- coding: utf-8 -*-
"""Regression tests for Issue #47: no implicit cloud fallbacks & accurate privacy disclosures."""

import pathlib
import threading
import types
import unittest
from unittest import mock

from tzero import tzero_v3
from tzero.tzero_jarvis.zero_key_router import ZeroKeyAIRouter

ROOT = pathlib.Path(__file__).resolve().parent.parent


class _DummyText:
    def __init__(self, value: str = ""):
        self._value = value

    def get(self, *_args):
        return self._value


class _DummyVar:
    def __init__(self, value: str):
        self._value = value

    def get(self):
        return self._value


class _DummyApp:
    """Minimal harness mirroring App.async_generate_payload dependencies without Tk."""

    def __init__(self, provider_name: str = "NVIDIA NIM", target_dir: str = "."):
        self.provider_var = _DummyVar(provider_name)
        self.model_var = _DummyVar("deepseek-ai/deepseek-v4.1-flash")
        self.git_checkboxes = {}
        self.manual_changes = []
        self.file_snippets = {"sample.py": "def ok() -> int:\n    return 1"}
        self.template_engine = types.SimpleNamespace(render=lambda _v: "tree")
        self.extra_prompt_text = _DummyText("")
        self.dir_entry = _DummyText(target_dir)
        self.cancel_event = threading.Event()
        self.logs = []
        self.toasts = []
        self.success_payloads = []
        self.failed_errors = []

    def safe_after(self, _delay, fn):
        fn()

    def log(self, msg):
        self.logs.append(msg)

    def show_toast(self, msg, level="info"):
        self.toasts.append((msg, level))

    def _update_prog_sync(self, _val, _msg):
        pass

    def on_gen_success(self, content):
        self.success_payloads.append(content)

    def on_gen_cancelled(self):
        pass

    def on_gen_fail(self, err):
        self.failed_errors.append(err)


class TestNoImplicitCloudFallback(unittest.TestCase):
    def test_architecture_export_with_missing_key_never_calls_cloud(self):
        with mock.patch("tzero.tzero_v3._config_mgr.get_profile", return_value={"provider": "NVIDIA NIM", "model": "deepseek-ai/deepseek-v4.1-flash"}), \
                mock.patch("tzero.tzero_v3._config_mgr.get_credential", return_value=""), \
                mock.patch("tzero.tzero_v3.requests.post", side_effect=AssertionError("Must not call remote cloud without key")), \
                mock.patch("urllib.request.urlopen", side_effect=AssertionError("Must not open network sockets")):
            out = tzero_v3.ContextExportManager.generate_architecture_blueprint(
                project_name="SampleRepo",
                files=["a.py"],
                deps={"a.py": []},
                snippets={"a.py": "def foo(): pass"},
                use_ai=True,
                api_key="",
            )
        self.assertIn("SampleRepo", out)

    def test_desktop_generator_without_key_stays_local(self):
        app = _DummyApp(provider_name="NVIDIA NIM", target_dir=str(ROOT / "tzero"))
        with mock.patch("tzero.tzero_v3._config_mgr.get_credential", return_value=""), \
                mock.patch("tzero.tzero_v3.requests.post", side_effect=AssertionError("Must not call remote cloud without key")), \
                mock.patch("urllib.request.urlopen", side_effect=AssertionError("Must not open network sockets")), \
                mock.patch("tzero.tzero_v3.generate_offline_context", return_value="# Local AST Output") as offline_mock:
            tzero_v3.AutoReadmeGUI.async_generate_payload(app, "https://integrate.api.nvidia.com/v1", "", ["a.py"])
        offline_mock.assert_called_once()
        self.assertEqual(app.success_payloads, ["# Local AST Output"])
        self.assertEqual(app.failed_errors, [])

    def test_desktop_generator_provider_error_falls_back_locally_not_to_pollinations(self):
        app = _DummyApp(provider_name="OpenAI", target_dir=str(ROOT / "tzero"))
        called_urls = []

        def fake_post(url, **_kwargs):
            called_urls.append(url)
            raise RuntimeError("HTTP 500 upstream outage")

        with mock.patch("tzero.tzero_v3.requests.post", side_effect=fake_post), \
                mock.patch("urllib.request.urlopen", side_effect=AssertionError("Must not call urllib fallback")), \
                mock.patch("tzero.tzero_v3.generate_offline_context", return_value="# Local Fallback Context") as offline_mock:
            tzero_v3.AutoReadmeGUI.async_generate_payload(app, "https://api.openai.com/v1", "sk-test-key-00000000", ["a.py"])

        self.assertEqual(len(called_urls), 1)
        self.assertIn("api.openai.com", called_urls[0])
        self.assertFalse(any("pollinations.ai" in u for u in called_urls))
        offline_mock.assert_called_once()
        self.assertEqual(app.success_payloads, ["# Local Fallback Context"])

    def test_legacy_ollama_query_never_calls_pollinations(self):
        with mock.patch.object(ZeroKeyAIRouter, "check_ollama_available", return_value=False), \
                mock.patch("urllib.request.urlopen", side_effect=AssertionError("Must not fall back to cloud")), \
                mock.patch("tzero.tzero_v3.requests.post", side_effect=AssertionError("Must not fall back to cloud")):
            res = ZeroKeyAIRouter.query_intelligence("Explain AST")
        self.assertEqual(res.get("provider"), "unavailable")


class TestPrivacyAndClaimsTransparency(unittest.TestCase):
    def test_privacy_doc_discloses_removed_pollinations_fallbacks(self):
        privacy = (ROOT / "PRIVACY.md").read_text(encoding="utf-8")
        self.assertIn("Pollinations", privacy)
        self.assertIn("DuckDuckGo", privacy)
        self.assertIn("GHSA-pm3r-rxg9-cj5j", privacy)
        self.assertNotIn("can still retry through Pollinations", privacy)

    def test_top_level_docs_qualify_local_vs_network(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        ai_insp = (ROOT / "AI_INSPECTION.md").read_text(encoding="utf-8")
        llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
        self.assertIn("PRIVACY.md", readme)
        self.assertIn("PRIVACY.md", ai_insp)
        self.assertIn("PRIVACY.md", llms)
        self.assertNotIn("legacy Pollinations fallback", readme)
        self.assertNotIn("100% Offline & Local", ai_insp)
        self.assertNotIn("runs air-gapped", llms)


if __name__ == "__main__":
    unittest.main()
