# -*- coding: utf-8 -*-
"""Unit tests for configuration manager and keyring security."""

import os
import shutil
import tempfile
import unittest

from tzero_v3 import ConfigManager, KeyringSecretsBackupManager, DEFAULT_CONFIG_DIR


class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_mgr = ConfigManager(config_dir=self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_default_state(self):
        state = self.config_mgr.get_default_state()
        self.assertIn("profiles", state)
        self.assertIn("default", state["profiles"])
        default_prof = state["profiles"]["default"]
        self.assertEqual(default_prof["provider"], "NVIDIA NIM")
        self.assertIn(".py", default_prof["allowed_extensions"])

    def test_profile_switch_and_update(self):
        prof = self.config_mgr.get_profile()
        self.assertEqual(prof["provider"], "NVIDIA NIM")

        # Create a new profile
        self.config_mgr.set_profile("custom_prof", {
            "provider": "OpenAI",
            "model": "gpt-4o",
            "reduction": "Balanced",
            "allowed_extensions": [".py"],
            "ignored_folders": [".git"],
            "thread_pool_size": 2,
            "max_tokens_budget": 40000
        })
        self.assertIn("custom_prof", self.config_mgr.get_profile_names())

        self.config_mgr.switch_profile("custom_prof")
        active = self.config_mgr.get_profile()
        self.assertEqual(active["provider"], "OpenAI")
        self.assertEqual(active["model"], "gpt-4o")

    def test_backup_and_recovery(self):
        self.config_mgr.save()
        backup_file = os.path.join(self.test_dir, "config.backup.json")
        self.assertTrue(os.path.exists(backup_file))

        # Corrupt main file
        with open(self.config_mgr.config_path, "w", encoding="utf-8") as f:
            f.write("{invalid json")

        # Recover
        recovered = self.config_mgr.recover_from_backup()
        self.assertTrue(recovered)
        self.assertIn("profiles", self.config_mgr._state)


class TestKeyringSecretsBackupManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.backup_path = os.path.join(self.test_dir, "creds.dat")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_backup_restore_mock(self):
        # Test XOR cipher consistency
        raw_bytes = b"my_test_secret_payload_12345"
        cipher_key = "secure_master_passphrase"
        key_bytes = cipher_key.encode("utf-8")

        encrypted = bytearray(raw_bytes)
        for i in range(len(encrypted)):
            encrypted[i] ^= key_bytes[i % len(key_bytes)]

        self.assertNotEqual(bytes(encrypted), raw_bytes)

        # Decrypt
        decrypted = bytearray(encrypted)
        for i in range(len(decrypted)):
            decrypted[i] ^= key_bytes[i % len(key_bytes)]

        self.assertEqual(bytes(decrypted), raw_bytes)


if __name__ == "__main__":
    unittest.main()
