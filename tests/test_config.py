# -*- coding: utf-8 -*-
"""Unit tests for configuration manager and keyring security."""

import os
import shutil
import tempfile
import unittest

from tzero.tzero_v3 import ConfigManager, KeyringSecretsBackupManager, DEFAULT_CONFIG_DIR


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

    def test_auto_migration_deprecated_models(self):
        # Write config with deprecated model
        import json
        legacy_data = {
            "version": "3.0.0",
            "active_profile": "default",
            "profiles": {
                "default": {
                    "provider": "NVIDIA NIM",
                    "model": "meta/llama-3.3-70b-instruct"
                }
            }
        }
        with open(self.config_mgr.config_path, "w", encoding="utf-8") as f:
            json.dump(legacy_data, f)

        # Reload should auto-migrate to deepseek-ai/deepseek-v4.1-flash
        self.config_mgr.load()
        active = self.config_mgr.get_profile()
        self.assertEqual(active["model"], "deepseek-ai/deepseek-v4.1-flash")


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

    def test_pbkdf2_backup_and_restore_roundtrip(self):
        import unittest.mock
        saved_rounds = KeyringSecretsBackupManager.PBKDF2_ROUNDS
        KeyringSecretsBackupManager.PBKDF2_ROUNDS = 2000
        mock_store = {"OpenAI": "sk-realtestkey12345", "Anthropic": "sk-ant-test67890"}
        try:
            with unittest.mock.patch("keyring.get_password", side_effect=lambda s, p: mock_store.get(p)):
                restored_store = {}
                with unittest.mock.patch("keyring.set_password", side_effect=lambda s, p, v: restored_store.__setitem__(p, v)):
                    ok = KeyringSecretsBackupManager.backup_credentials(self.backup_path, "master_pass_123")
                    self.assertTrue(ok)
                    self.assertTrue(os.path.exists(self.backup_path))
                    with open(self.backup_path, "rb") as f:
                        data = f.read()
                    self.assertTrue(data.startswith(KeyringSecretsBackupManager.MAGIC_HEADER))

                    # Restore with correct passphrase
                    restore_ok = KeyringSecretsBackupManager.restore_credentials(self.backup_path, "master_pass_123")
                    self.assertTrue(restore_ok)
                    self.assertEqual(restored_store, mock_store)

                    # Restore with wrong passphrase should fail authentication
                    fail_ok = KeyringSecretsBackupManager.restore_credentials(self.backup_path, "wrong_pass")
                    self.assertFalse(fail_ok)
        finally:
            KeyringSecretsBackupManager.PBKDF2_ROUNDS = saved_rounds

    def test_legacy_xor_fallback_restore(self):
        import json
        import unittest.mock
        legacy_data = json.dumps({"NVIDIA NIM": "nv-secret-12345"}).encode("utf-8")
        passphrase = "legacy_passphrase"
        key_bytes = passphrase.encode("utf-8")
        encrypted = bytearray(legacy_data)
        for i in range(len(encrypted)):
            encrypted[i] ^= key_bytes[i % len(key_bytes)]

        with open(self.backup_path, "wb") as f:
            f.write(encrypted)

        restored = {}
        with unittest.mock.patch("keyring.set_password", side_effect=lambda s, p, v: restored.__setitem__(p, v)):
            ok = KeyringSecretsBackupManager.restore_credentials(self.backup_path, passphrase)
            self.assertTrue(ok)
            self.assertEqual(restored, {"NVIDIA NIM": "nv-secret-12345"})


if __name__ == "__main__":
    unittest.main()
