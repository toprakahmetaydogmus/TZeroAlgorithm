# -*- coding: utf-8 -*-
"""Verification tests for multi-OS CI workflow completeness, Dependabot, CodeQL, and Release workflows."""

import pathlib
import unittest
import yaml

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent


class TestCIWorkflow(unittest.TestCase):
    def test_github_actions_covers_multi_os_node_and_sync_gates(self):
        ci_path = ROOT_DIR / ".github" / "workflows" / "ci.yml"
        self.assertTrue(ci_path.exists(), "ci.yml must exist")
        ci_text = ci_path.read_text(encoding="utf-8")
        ci_data = yaml.safe_load(ci_text)

        self.assertEqual(ci_data.get("name"), "CI")
        self.assertIn("ubuntu-24.04", ci_text)
        self.assertIn("windows-latest", ci_text)
        self.assertIn("macos-latest", ci_text)
        self.assertIn("setup-node", ci_text)
        self.assertIn("node --test installers/npm/test/package.test.js", ci_text)
        self.assertIn("node --test extensions/vscode/test/extension.test.js", ci_text)
        self.assertIn("scripts/sync_release_metadata.py --check", ci_text)
        self.assertIn("tests/audit_secrets.py", ci_text)

    def test_dependabot_covers_all_ecosystems_weekly(self):
        dep_path = ROOT_DIR / ".github" / "dependabot.yml"
        self.assertTrue(dep_path.exists(), "dependabot.yml must exist")
        dep_data = yaml.safe_load(dep_path.read_text(encoding="utf-8"))

        self.assertEqual(dep_data.get("version"), 2)
        updates = dep_data.get("updates", [])
        ecosystems = {u.get("package-ecosystem") for u in updates}
        self.assertIn("github-actions", ecosystems)
        self.assertIn("pip", ecosystems)
        self.assertIn("npm", ecosystems)
        self.assertIn("cargo", ecosystems)

        for u in updates:
            self.assertEqual(u.get("schedule", {}).get("interval"), "weekly")

    def test_codeql_workflow_covers_python_and_js_ts(self):
        codeql_path = ROOT_DIR / ".github" / "workflows" / "codeql.yml"
        self.assertTrue(codeql_path.exists(), "codeql.yml must exist")
        codeql_data = yaml.safe_load(codeql_path.read_text(encoding="utf-8"))

        matrix = codeql_data["jobs"]["analyze"]["strategy"]["matrix"]["include"]
        languages = {item["language"] for item in matrix}
        self.assertIn("python", languages)
        self.assertIn("javascript-typescript", languages)

    def test_publish_extension_workflow_handles_both_registries(self):
        ext_path = ROOT_DIR / ".github" / "workflows" / "publish-extension.yml"
        self.assertTrue(ext_path.exists(), "publish-extension.yml must exist")
        ext_text = ext_path.read_text(encoding="utf-8")
        ext_data = yaml.safe_load(ext_text)

        self.assertIn("VSCE_PAT", ext_text)
        self.assertIn("OVSX_PAT", ext_text)
        self.assertIn("continue-on-error", ext_text)

    def test_publish_npm_workflow_handles_npm_token(self):
        npm_path = ROOT_DIR / ".github" / "workflows" / "publish-npm.yml"
        self.assertTrue(npm_path.exists(), "publish-npm.yml must exist")
        npm_text = npm_path.read_text(encoding="utf-8")

        self.assertIn("NPM_TOKEN", npm_text)
        self.assertIn("registry.npmjs.org", npm_text)
        self.assertIn("continue-on-error", npm_text)

    def test_publish_pypi_workflow_handles_pypi_token(self):
        pypi_path = ROOT_DIR / ".github" / "workflows" / "publish-pypi.yml"
        self.assertTrue(pypi_path.exists(), "publish-pypi.yml must exist")
        pypi_text = pypi_path.read_text(encoding="utf-8")

        self.assertIn("pypa/gh-action-pypi-publish", pypi_text)
        self.assertIn("PYPI_API_TOKEN", pypi_text)
        self.assertIn("continue-on-error", pypi_text)

    def test_release_workflow_triggers_on_version_tags(self):
        rel_path = ROOT_DIR / ".github" / "workflows" / "release.yml"
        self.assertTrue(rel_path.exists(), "release.yml must exist")
        rel_text = rel_path.read_text(encoding="utf-8")
        rel_data = yaml.safe_load(rel_text)

        on_block = rel_data.get("on") or rel_data.get(True, {})
        tags = on_block.get("push", {}).get("tags", [])
        self.assertTrue(any("v*" in str(t) or "v[0-9]*" in str(t) for t in tags))
        self.assertIn("compile.py", rel_text)
        self.assertIn("softprops/action-gh-release", rel_text)

    def test_all_github_yaml_files_are_valid(self):
        for path in (ROOT_DIR / ".github").rglob("*.yml"):
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.assertIsInstance(data, dict, f"{path} did not parse to a valid dict")


if __name__ == "__main__":
    unittest.main()
