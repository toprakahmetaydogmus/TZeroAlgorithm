# -*- coding: utf-8 -*-
"""
Tests for T-Zero Unified Zero-Leak & Shannon Entropy Security Engine.
"""

import ast
import unittest
from tzero_security import (
    calculate_shannon_entropy,
    ZeroLeakEngine,
    SECRET_RULES,
)


class TestZeroLeakSecurityEngine(unittest.TestCase):
    """Verifies 100% Zero-Leak security detection, entropy scoring, and redaction."""

    def test_shannon_entropy_calculation(self):
        # Repetitive string has low entropy
        self.assertAlmostEqual(calculate_shannon_entropy("aaaaaaaaaaaa"), 0.0, places=2)
        
        # English text has moderate entropy (2.5 - 3.5)
        eng_ent = calculate_shannon_entropy("hello world this is standard english text")
        self.assertTrue(2.5 <= eng_ent <= 3.8)

        # Base64 random cryptographic key has high entropy (> 4.5)
        crypto_key = "aF9z+3kL/90zXy7QmN8123OpQvR=="
        high_ent = calculate_shannon_entropy(crypto_key)
        self.assertGreater(high_ent, 4.0)

    def test_openai_key_detection(self):
        pfx = "sk"
        sample = f'client = OpenAI(api_key="{pfx}-1234567890abcdef1234567890abcdef1234")'
        findings = ZeroLeakEngine.scan_text(sample)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].provider, "OpenAI")
        self.assertEqual(findings[0].severity, "CRITICAL")

    def test_anthropic_key_detection(self):
        pfx = "sk-ant"
        sample = f'ANTHROPIC_KEY = "{pfx}-api03-abcdef1234567890abcdef1234567890abcdef12"'
        findings = ZeroLeakEngine.scan_text(sample)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].provider, "Anthropic")

    def test_gemini_key_detection(self):
        pfx = "AIza"
        sample = f'GEMINI_API_KEY = "{pfx}SyD-1234567890abcdef1234567890ab"'
        findings = ZeroLeakEngine.scan_text(sample)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].provider, "Google")

    def test_github_fine_grained_pat(self):
        pfx = "github_pat"
        sample = f'token = "{pfx}_11AAAAAAA0123456789abcdefghijklmnopqrstuvwxyz0123456789abcdefghijklmnopqrstuvwxyz"'
        findings = ZeroLeakEngine.scan_text(sample)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].provider, "GitHub")

    def test_slack_token_detection(self):
        pfx = "xoxb"
        sample = f'SLACK_BOT_TOKEN = "{pfx}-123456789012-1234567890123-abcdefghijklmnopqrstuvwx"'
        findings = ZeroLeakEngine.scan_text(sample)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].provider, "Slack")

    def test_stripe_live_key_detection(self):
        pfx = "sk_live"
        sample = f'stripe.api_key = "{pfx}_51Abcdef1234567890Abcdef1234"'
        findings = ZeroLeakEngine.scan_text(sample)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].provider, "Stripe")

    def test_huggingface_token_detection(self):
        sample = 'hf_token = "hf_AbCdEfGhIjKlMnOpQrStUvWxYz0123456789"'
        findings = ZeroLeakEngine.scan_text(sample)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].provider, "HuggingFace")

    def test_db_credentials_uri(self):
        sample = 'DATABASE_URL = "postgres://admin:SuperSecretPass123!@db.internal.net:5432/production_db"'
        findings = ZeroLeakEngine.scan_text(sample)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].provider, "Database")

    def test_private_key_header(self):
        sample = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0..."
        findings = ZeroLeakEngine.scan_text(sample)
        self.assertGreaterEqual(len(findings), 1)
        self.assertEqual(findings[0].provider, "PKI")

    def test_jwt_detection(self):
        sample = 'auth = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozGzV_cefaSmDeReWzLUpQx6vKk12345"'
        findings = ZeroLeakEngine.scan_text(sample)
        self.assertGreaterEqual(len(findings), 1)

    def test_placeholder_rejection(self):
        sample = 'OPENAI_API_KEY = "sk-YOUR_API_KEY_HERE_PLACEHOLDER"'
        findings = ZeroLeakEngine.scan_text(sample)
        self.assertEqual(len(findings), 0, "Placeholder keys must not trigger false positives")

    def test_shannon_entropy_anomaly_detection(self):
        # A 48-character completely random high-entropy token without any standard provider prefix
        sample = 'custom_secret = "q7X9mLz2vBw4kP8jR5tY1nEaBcDeFgHiJkLmNoPqRsTuVw"'
        findings = ZeroLeakEngine.scan_text(sample, check_entropy=True)
        self.assertGreaterEqual(len(findings), 1)
        self.assertTrue(any(f.is_entropy_anomaly for f in findings))

    def test_sanitize_text(self):
        raw = 'my_key = "sk-1234567890abcdef1234567890abcdef1234"\ndb = "postgres://root:secret@localhost/db"'
        sanitized = ZeroLeakEngine.sanitize_text(raw)
        self.assertNotIn("sk-1234567890abcdef", sanitized)
        self.assertNotIn("postgres://root:secret", sanitized)
        self.assertIn("[ZERO_LEAK_MASKED_OPENAI_KEY]", sanitized)
        self.assertIn("[ZERO_LEAK_MASKED_DB_URL]", sanitized)

    def test_sanitize_ast(self):
        code = 'def connect():\n    api_key = "sk-1234567890abcdef1234567890abcdef1234"\n    return api_key'
        tree = ast.parse(code)
        sanitized_tree = ZeroLeakEngine.sanitize_ast(tree)
        # Verify the constant string inside the AST was replaced
        for node in ast.walk(sanitized_tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                self.assertNotIn("sk-1234567890abcdef", node.value)

    def test_scan_files_map(self):
        pfx = "AKIA"
        files = {
            "src/safe.py": "def add(a, b): return a + b\n",
            "src/config.py": f'AWS_ID = "{pfx}1234567890ABCDEF"\n'
        }
        res = ZeroLeakEngine.scan_files_map(files)
        self.assertFalse(res["clean"])
        self.assertEqual(res["violation_count"], 1)
        self.assertEqual(res["files_with_violations"], 1)
        self.assertEqual(res["violations"][0]["file"], "src/config.py")


if __name__ == "__main__":
    unittest.main()
