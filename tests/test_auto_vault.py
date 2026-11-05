import unittest
from tzero_security import ZeroLeakEngine

class TestAutoVault(unittest.TestCase):
    def test_auto_migrate_openai_key(self):
        sample = 'client = OpenAI(api_key="sk-proj-YOUR_API_KEY_HERE_12345678901234567890123456789012")'
        # With realistic mock key
        raw_key = "sk-proj-99a8b7c6d5e4f3a2b1c099887766554433221100aa"
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

if __name__ == "__main__":
    unittest.main()
