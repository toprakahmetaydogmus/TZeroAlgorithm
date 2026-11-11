# -*- coding: utf-8 -*-
"""Packaging, module inclusion, and single-source version sync verification tests."""

import json
import pathlib
import re
import tomllib
import unittest

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent


class TestPackagingAndVersionSync(unittest.TestCase):
    def test_tzero_sources_are_grouped_under_the_package(self):
        data = tomllib.loads((ROOT_DIR / "pyproject.toml").read_text(encoding="utf-8"))
        packages = set(data["tool"]["setuptools"]["packages"])
        self.assertEqual(packages, {"tzero", "tzero.tzero_fixer", "tzero.tzero_jarvis"})
        self.assertEqual(list(ROOT_DIR.glob("tzero_*.py")), [])
        self.assertTrue((ROOT_DIR / "tzero" / "tzero_v3.py").is_file())

    def test_pyproject_scripts_and_clean_dependencies(self):
        data = tomllib.loads((ROOT_DIR / "pyproject.toml").read_text(encoding="utf-8"))
        deps = " ".join(data["project"]["dependencies"]).lower()
        self.assertNotIn("typer", deps)
        scripts = data["project"]["scripts"]
        self.assertEqual(scripts.get("tzero-tui"), "tzero.tzero_tui:main")
        self.assertEqual(scripts.get("pc-fixer-mcp"), "pc_fixer_mcp:main")
        self.assertIn("space", data["project"]["optional-dependencies"])

    def test_all_release_manifests_share_canonical_version(self):
        pyproject = tomllib.loads((ROOT_DIR / "pyproject.toml").read_text(encoding="utf-8"))
        canonical = pyproject["project"]["version"]
        self.assertEqual(canonical, "10.9.0")

        server = json.loads((ROOT_DIR / "server.json").read_text(encoding="utf-8"))
        self.assertEqual(server["version"], canonical)
        self.assertEqual(server["packages"][0]["version"], canonical)

        smithery = json.loads((ROOT_DIR / "smithery.json").read_text(encoding="utf-8"))
        self.assertEqual(smithery["version"], canonical)

        glama = json.loads((ROOT_DIR / "glama.json").read_text(encoding="utf-8"))
        self.assertEqual(glama["version"], canonical)

        npm_pkg = json.loads((ROOT_DIR / "installers" / "npm" / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(npm_pkg["version"], canonical)

        vs_pkg = json.loads((ROOT_DIR / "extensions" / "vscode" / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(vs_pkg["version"], canonical)

        for rb_path in (ROOT_DIR / "Formula" / "tzero.rb", ROOT_DIR / "installers" / "brew" / "tzero.rb"):
            rb_text = rb_path.read_text(encoding="utf-8")
            m = re.search(r'version\s+"([^"]+)"', rb_text)
            self.assertIsNotNone(m, f"Version missing in {rb_path}")
            self.assertEqual(m.group(1), canonical, f"Version mismatch in {rb_path}")
            self.assertIn(f"v{canonical}.tar.gz", rb_text)

        import addmcp
        from tzero import tzero_mcp
        from tzero import tzero_task_benchmark
        self.assertEqual(tzero_mcp.SERVER_VERSION, canonical)
        self.assertEqual(addmcp.APP_VERSION, canonical)
        self.assertEqual(tzero_task_benchmark.TaskBenchmarkReport().version, canonical)

    def test_dockerignore_excludes_bloat_and_private_artifacts(self):
        lines = {
            line.strip()
            for line in (ROOT_DIR / ".dockerignore").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        }
        for pat in ("tzero-showcase/", "extensions/", ".tzero/", ".tzero_cache.db", "scratch/"):
            self.assertIn(pat, lines, f"Missing {pat} from .dockerignore")

    def test_no_dead_duplicate_packages_and_sorted_vsix_publisher(self):
        self.assertFalse((ROOT_DIR / "vscode-extension").exists(), "Legacy vscode-extension/ should be removed")
        ps_text = (ROOT_DIR / "scripts" / "publish_vscode.ps1").read_text(encoding="utf-8")
        self.assertIn("LastWriteTime", ps_text)


if __name__ == "__main__":
    unittest.main()
