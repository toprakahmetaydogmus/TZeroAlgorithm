# -*- coding: utf-8 -*-
"""Verification tests for multi-OS CI workflow completeness, Dependabot, CodeQL, and Release workflows."""

import pathlib
import unittest

try:
    import yaml
except ImportError:
    yaml = None

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent


class TestCIWorkflow(unittest.TestCase):
    def test_github_actions_covers_multi_os_node_and_sync_gates(self):
        ci_path = ROOT_DIR / ".github" / "workflows" / "ci.yml"
        self.assertTrue(ci_path.exists(), "ci.yml must exist")
        ci_text = ci_path.read_text(encoding="utf-8")
        if yaml:
            ci_data = yaml.safe_load(ci_text)
            self.assertEqual(ci_data.get("name"), "CI")
        else:
            self.assertIn("name: CI", ci_text)

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
        dep_text = dep_path.read_text(encoding="utf-8")
        if yaml:
            dep_data = yaml.safe_load(dep_text)
            self.assertEqual(dep_data.get("version"), 2)
            updates = dep_data.get("updates", [])
            ecosystems = {u.get("package-ecosystem") for u in updates}
            self.assertIn("github-actions", ecosystems)
            self.assertIn("pip", ecosystems)
            self.assertIn("npm", ecosystems)
            self.assertIn("cargo", ecosystems)
            for u in updates:
                self.assertEqual(u.get("schedule", {}).get("interval"), "weekly")
        else:
            self.assertIn('package-ecosystem: "github-actions"', dep_text)
            self.assertIn('package-ecosystem: "pip"', dep_text)
            self.assertIn('package-ecosystem: "npm"', dep_text)
            self.assertIn('package-ecosystem: "cargo"', dep_text)
            self.assertIn('interval: "weekly"', dep_text)

    def test_codeql_workflow_covers_python_and_js_ts(self):
        codeql_path = ROOT_DIR / ".github" / "workflows" / "codeql.yml"
        self.assertTrue(codeql_path.exists(), "codeql.yml must exist")
        codeql_text = codeql_path.read_text(encoding="utf-8")
        if yaml:
            codeql_data = yaml.safe_load(codeql_text)
            matrix = codeql_data["jobs"]["analyze"]["strategy"]["matrix"]["include"]
            languages = {item["language"] for item in matrix}
            self.assertIn("python", languages)
            self.assertIn("javascript-typescript", languages)
        else:
            self.assertIn("language: python", codeql_text)
            self.assertIn("language: javascript-typescript", codeql_text)

    def test_publish_extension_workflow_handles_both_registries(self):
        ext_path = ROOT_DIR / ".github" / "workflows" / "publish-extension.yml"
        self.assertTrue(ext_path.exists(), "publish-extension.yml must exist")
        ext_text = ext_path.read_text(encoding="utf-8")

        self.assertIn("VSCE_PAT", ext_text)
        self.assertIn("OVSX_PAT", ext_text)
        self.assertIn("continue-on-error", ext_text)
        self.assertIn("inputs.publish_openvsx", ext_text)
        self.assertIn("inputs.publish_vscode", ext_text)

    def test_ci_workflow_runs_for_dependabot_and_bots(self):
        ci_path = ROOT_DIR / ".github" / "workflows" / "ci.yml"
        ci_text = ci_path.read_text(encoding="utf-8")
        self.assertNotIn("github.actor != 'dependabot'", ci_text, "CI should not exclude dependabot PRs")
        self.assertNotIn("endsWith(github.actor, '[bot]')", ci_text, "CI should not exclude bot PRs")

    def test_funding_yaml_exists_and_valid(self):
        funding_path = ROOT_DIR / ".github" / "FUNDING.yml"
        self.assertTrue(funding_path.exists(), "FUNDING.yml must exist")
        funding_text = funding_path.read_text(encoding="utf-8")
        if yaml:
            data = yaml.safe_load(funding_text)
            self.assertIn("github", data)
            self.assertIn("toprakahmetaydogmus", data["github"])
        else:
            self.assertIn("github:", funding_text)
            self.assertIn("toprakahmetaydogmus", funding_text)

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
        self.assertIn("PYPI_TOKEN", pypi_text)
        self.assertIn("continue-on-error", pypi_text)

    def test_release_workflow_triggers_on_version_tags(self):
        rel_path = ROOT_DIR / ".github" / "workflows" / "release.yml"
        self.assertTrue(rel_path.exists(), "release.yml must exist")
        rel_text = rel_path.read_text(encoding="utf-8")
        if yaml:
            rel_data = yaml.safe_load(rel_text)
            on_block = rel_data.get("on") or rel_data.get(True, {})
            tags = on_block.get("push", {}).get("tags", [])
            self.assertTrue(any("v*" in str(t) or "v[0-9]*" in str(t) for t in tags))
        else:
            self.assertTrue("v*" in rel_text or "v[0-9]*" in rel_text)

        self.assertIn("compile.py", rel_text)
        self.assertIn("softprops/action-gh-release", rel_text)
        self.assertIn("TZeroCI.exe", rel_text)
        self.assertIn("dist/*.tgz", rel_text)

    def test_all_release_workflows_trigger_on_published_releases(self):
        workflows = [
            ROOT_DIR / ".github" / "workflows" / "release.yml",
            ROOT_DIR / ".github" / "workflows" / "publish-pypi.yml",
            ROOT_DIR / ".github" / "workflows" / "publish-npm.yml",
            ROOT_DIR / ".github" / "workflows" / "publish-extension.yml",
        ]
        for wf_path in workflows:
            self.assertTrue(wf_path.exists(), f"{wf_path.name} must exist")
            text = wf_path.read_text(encoding="utf-8")
            self.assertIn("release:", text, f"{wf_path.name} must have release trigger")
            self.assertIn("published", text, f"{wf_path.name} must trigger on published release")

    def test_siber_akademi_icon_root_wrapper_importable(self):
        icon_path = ROOT_DIR / "siber_akademi_icon.py"
        self.assertTrue(icon_path.exists(), "Root siber_akademi_icon.py must exist")
        import siber_akademi_icon
        self.assertTrue(hasattr(siber_akademi_icon, "get_icon_file_path"))
        self.assertTrue(hasattr(siber_akademi_icon, "apply_window_icon"))
        self.assertTrue(hasattr(siber_akademi_icon, "SIBER_AKADEMI_ICO_BASE64"))

    def test_all_github_yaml_files_are_valid(self):
        for path in (ROOT_DIR / ".github").rglob("*.yml"):
            content = path.read_text(encoding="utf-8")
            self.assertTrue(len(content) > 0, f"{path} is empty")
            if yaml:
                data = yaml.safe_load(content)
                self.assertIsInstance(data, dict, f"{path} did not parse to a valid dict")

    def test_no_workflow_uses_secrets_in_if_conditional(self):
        for path in (ROOT_DIR / ".github" / "workflows").glob("*.yml"):
            content = path.read_text(encoding="utf-8")
            # GitHub rejects workflow if: conditions that reference secrets directly
            for line_no, line in enumerate(content.splitlines(), start=1):
                stripped = line.strip()
                if stripped.startswith("if:") and "secrets." in stripped:
                    self.fail(f"Invalid GitHub Actions syntax in {path.name}:{line_no}: secrets cannot be referenced in if: conditions. Line: {line}")


if __name__ == "__main__":
    unittest.main()
