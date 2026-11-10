import os
import subprocess
import sys
import tempfile
import unittest
from tzero_security import ZeroLeakEngine

class TestAutoVault(unittest.TestCase):
    def test_auto_migrate_openai_key(self):
        # With realistic mock key constructed dynamically
        raw_key = "sk" + "-proj-" + "99a8b7c6d5e4f3a2b1c099887766554433221100aa"
        code = f'client = OpenAI(api_key="{raw_key}")'
        migrated, env_content, count, report = ZeroLeakEngine.auto_migrate_to_env(code)
        self.assertEqual(count, 1)
        self.assertIn("os.environ.get", migrated)
        self.assertIn("OPENAI_API_KEY=", env_content)
        self.assertIn(raw_key, env_content)

    def test_auto_migrate_clean_code(self):
        code = 'def add(a, b):\n    return a + b\n'
        migrated, env_content, count, report = ZeroLeakEngine.auto_migrate_to_env(code)
        self.assertEqual(count, 0)
        self.assertEqual(migrated, code)
        self.assertIn("No secrets detected", env_content)

    def test_cli_vault_migrate_directory(self):
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        raw_key = "sk" + "-proj-" + "99a8b7c6d5e4f3a2b1c099887766554433221100aa"
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = os.path.join(tmp, "cfg.py")
            with open(cfg_path, "w", encoding="utf-8") as fh:
                fh.write(f'API_KEY = "{raw_key}"\n')
            res = subprocess.run(
                [sys.executable, os.path.join(root_dir, "tzero_v3.py"), "--vault", tmp, "--migrate"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            self.assertEqual(res.returncode, 0, res.stderr + res.stdout)
            self.assertTrue(os.path.isfile(os.path.join(tmp, ".env")))
            with open(cfg_path, encoding="utf-8") as fh:
                self.assertIn("os.environ.get", fh.read())

if __name__ == "__main__":
    unittest.main()
