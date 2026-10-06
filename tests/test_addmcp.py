"""Safety tests for the Windows MCP installer configuration merger."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

from addmcp import (
    ClientTarget,
    _install_server_binary,
    build_client_targets,
    install_targets,
    merge_server_config,
    server_entry,
)


class TestMergeServerConfig(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.server = self.root / "TZeroMCP.exe"
        self.server.write_bytes(b"test executable")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_preserves_existing_servers_and_backs_up_file(self):
        config_path = self.root / "mcp.json"
        original = {
            "mcpServers": {
                "other": {"command": "other-server", "args": []}
            },
            "custom": True,
        }
        config_path.write_text(json.dumps(original), encoding="utf-8")
        target = ClientTarget("test", "Test Client", config_path, "mcpServers", True)

        result = merge_server_config(target, self.server)

        updated = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(updated["mcpServers"]["other"], original["mcpServers"]["other"])
        self.assertTrue(updated["custom"])
        self.assertEqual(updated["mcpServers"]["tzero"]["command"], str(self.server.resolve()))
        self.assertEqual(result["status"], "installed")
        self.assertTrue(Path(result["backup"]).is_file())
        self.assertEqual(json.loads(Path(result["backup"]).read_text(encoding="utf-8")), original)

    def test_is_idempotent(self):
        target = ClientTarget(
            "test", "Test Client", self.root / "mcp.json", "mcpServers", True
        )
        merge_server_config(target, self.server)
        result = merge_server_config(target, self.server)
        backups = list(self.root.glob("mcp.json.backup-*"))

        self.assertEqual(result["status"], "unchanged")
        self.assertEqual(len(backups), 0)

    def test_vscode_user_config_uses_servers_schema(self):
        target = ClientTarget(
            "vscode", "VS Code", self.root / "mcp.json", "servers", True
        )
        merge_server_config(target, self.server)
        config = json.loads(target.config_path.read_text(encoding="utf-8"))

        self.assertEqual(config["servers"]["tzero"]["type"], "stdio")
        self.assertEqual(config["servers"]["tzero"]["command"], str(self.server.resolve()))

    def test_server_entry_for_python_script(self):
        script_path = self.root / "tzero_mcp.py"
        script_path.write_text("# dummy", encoding="utf-8")
        target = ClientTarget("cursor", "Cursor", self.root / "mcp.json", "mcpServers", True)

        entry = server_entry(target, script_path)
        self.assertEqual(entry["command"], sys.executable)
        self.assertEqual(entry["args"], [str(script_path.resolve())])

    def test_install_targets_helper(self):
        config_path = self.root / "mcp.json"
        target = ClientTarget("cursor", "Cursor", config_path, "mcpServers", True)
        logs = []

        successes, failures = install_targets(
            [target], log_fn=logs.append, server_path=self.server
        )
        self.assertEqual(successes, 1)
        self.assertEqual(failures, 0)
        self.assertTrue(config_path.exists())

    def test_malformed_json_is_not_overwritten(self):
        config_path = self.root / "mcp.json"
        config_path.write_text("{broken", encoding="utf-8")
        target = ClientTarget("test", "Test Client", config_path, "mcpServers", True)

        with self.assertRaises(json.JSONDecodeError):
            merge_server_config(target, self.server)

        self.assertEqual(config_path.read_text(encoding="utf-8"), "{broken")
        self.assertEqual(list(self.root.glob("mcp.json.backup-*")), [])


class TestClientDetection(unittest.TestCase):
    def test_installs_and_updates_server_binary_with_backup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundle = root / "bundle" / "TZeroMCP.exe"
            local_app_data = root / "local"
            bundle.parent.mkdir()
            bundle.write_bytes(b"server v1")

            installed = _install_server_binary(bundle, local_app_data)
            self.assertEqual(installed.read_bytes(), b"server v1")

            bundle.write_bytes(b"server v2")
            updated = _install_server_binary(bundle, local_app_data)
            backups = list(updated.parent.glob("TZeroMCP.exe.backup-*"))

            self.assertEqual(updated.read_bytes(), b"server v2")
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), b"server v1")

    def test_detects_clients_from_user_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            home = root / "home"
            app_data = root / "roaming"
            local_app_data = root / "local"
            (home / ".cursor").mkdir(parents=True)
            (app_data / "Code" / "User").mkdir(parents=True)
            (home / ".gemini" / "antigravity").mkdir(parents=True)
            (app_data / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev").mkdir(parents=True)

            targets = build_client_targets(
                home=home,
                app_data=app_data,
                local_app_data=local_app_data,
                which=lambda command: None,
            )
            detected = {target.key for target in targets if target.detected}

            self.assertTrue({"cursor", "vscode", "antigravity", "cline"}.issubset(detected))
            self.assertNotIn("windsurf", detected)


    def test_installs_antigravity_skill(self):
        from addmcp import _install_antigravity_skill
        from unittest import mock
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            with mock.patch("pathlib.Path.home", return_value=home):
                _install_antigravity_skill()
                skill_path = home / ".gemini" / "config" / "skills" / "tzero" / "SKILL.md"
                self.assertTrue(skill_path.is_file())
                self.assertIn("name: tzero", skill_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()