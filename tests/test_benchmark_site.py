# tests/test_benchmark_site.py
"""
Unit and integration tests for the live Vercel Benchmark Hub (benchmark-site/)
and the synchronization script (scripts/update_benchmark_site.py).
"""

import unittest
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = REPO_ROOT / "benchmark-site"
INDEX_HTML = SITE_DIR / "index.html"
APP_JS = SITE_DIR / "app.js"
STYLE_CSS = SITE_DIR / "style.css"
UPDATE_SCRIPT = REPO_ROOT / "scripts" / "update_benchmark_site.py"
DIST_DIR = REPO_ROOT / "dist"


def _canonical_version() -> str:
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    return m.group(1) if m else "12.2.0"


CANONICAL_VERSION = _canonical_version()


class TestBenchmarkSite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html_content = INDEX_HTML.read_text(encoding="utf-8")
        cls.js_content = APP_JS.read_text(encoding="utf-8")
        cls.css_content = STYLE_CSS.read_text(encoding="utf-8")

    def test_no_old_version_references(self):
        """Ensure no obsolete v11.15.5, v11.11.0, or v12.1.4 references remain in index.html."""
        for legacy in ("v11.15.5", "11.15.5", "v11.11.0", "11.11.0", "12.1.4"):
            self.assertNotIn(legacy, self.html_content)

    def test_version_12_1_0_present_in_key_metadata(self):
        """Verify canonical version is set in title, meta, json-ld, and hero badges."""
        v = CANONICAL_VERSION
        self.assertIn(f"T-Zero v{v}", self.html_content)
        self.assertIn(f'"softwareVersion": "{v}"', self.html_content)
        self.assertIn(f"style.css?v={v}", self.html_content)
        self.assertIn(f"app.js?v={v}", self.html_content)
        self.assertIn(f"PyPI v{v}", self.html_content)
        self.assertIn(f"T-ZERO v{v}", self.html_content)
        self.assertIn("anti_rea_lab.html", self.html_content)

    def test_six_download_assets_verified_with_sha256(self):
        """Verify all 6 official downloads with valid URLs, sizes, and 64-char SHA-256 hashes."""
        v = CANONICAL_VERSION
        expected_names = [
            f"TZero-v{v}-Windows-x64.zip",
            "TZeroAlgorithm.exe",
            "TZeroCLI.exe",
            "TZeroMCP.exe",
            "AddMCP.exe",
            f"tzero-vscode-{v}.vsix",
        ]

        for name in expected_names:
            self.assertIn(name, self.html_content)
            expected_url = f"https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/download/v{v}/{name}"
            self.assertIn(expected_url, self.html_content)
            match = re.search(rf'data-name="{re.escape(name)}"[\s\S]*?data-sha="([0-9a-f]{{64}})"', self.html_content)
            self.assertIsNotNone(match, f"Missing 64-char lowercase SHA-256 for {name}")
            sha_file = DIST_DIR / f"{name}.sha256"
            if sha_file.is_file():
                disk_sha = sha_file.read_text(encoding="utf-8").strip().split()[0].lower()
                self.assertEqual(match.group(1), disk_sha, f"SHA-256 drift for {name}")

    def test_live_release_banner_structure(self):
        """Verify the dynamic latest release banner is present in index.html with appropriate hook IDs."""
        self.assertIn('id="latest-release-banner"', self.html_content)
        self.assertIn('id="live-release-tag"', self.html_content)
        self.assertIn('id="live-release-date"', self.html_content)
        self.assertIn('id="live-release-assets"', self.html_content)
        self.assertIn('id="live-release-link"', self.html_content)
        self.assertIn('id="live-release-body"', self.html_content)

    def test_crypto_donation_hub_and_modal(self):
        """Verify USDT TRC20, BTC, and EVM addresses in both the support card and interactive modal."""
        usdt_addr = "TE7uKxZJ414u938gWf6bYh9QvRk2141517"
        btc_addr = "bc1q9k4hvd6c2g8l9w3z7v8f2k3j5l8n9m1p4q7r0s"
        evm_addr = "0xF36Cd453f9F2bE91647C006C46ff66fB41d9F0c5"

        self.assertIn(usdt_addr, self.html_content)
        self.assertIn(btc_addr, self.html_content)
        self.assertIn(evm_addr, self.html_content)
        self.assertIn('id="support"', self.html_content)
        self.assertIn('id="support-modal"', self.html_content)
        self.assertIn('id="nav-support-btn"', self.html_content)
        self.assertIn('btn-copy-crypto', self.html_content)

    def test_app_js_syntax_and_functions(self):
        """Verify app.js includes release data fetching, star tracking, 15-min TTL, and modal hooks."""
        self.assertIn("initLatestRelease", self.js_content)
        self.assertIn("initGitHubStars", self.js_content)
        self.assertIn("initViralShare", self.js_content)
        self.assertIn("initSupportModal", self.js_content)
        self.assertIn("openSupportModal", self.js_content)
        self.assertIn("closeSupportModal", self.js_content)
        self.assertIn("live-release-body", self.js_content)
        self.assertIn("escapeHtml", self.js_content)
        self.assertIn("btn.href = asset.browser_download_url", self.js_content)
        self.assertIn(".crypto-code, .modal-crypto-code", self.js_content)
        # Check no duplicate fetch function exists
        self.assertNotIn("fetchLiveReleaseMetadata", self.js_content)
        # Check 15-minute TTL caching
        self.assertIn("15 * 60 * 1000", self.js_content)
        # Check fallback to canonical version
        self.assertIn(f"v{CANONICAL_VERSION}", self.js_content)
        # Check registration in DOMContentLoaded
        self.assertIn('safeInit(initLatestRelease, "LatestRelease")', self.js_content)
        self.assertIn('safeInit(initGitHubStars, "GitHubStars")', self.js_content)
        self.assertIn('safeInit(initViralShare, "ViralShare")', self.js_content)
        self.assertIn('safeInit(initSupportModal, "SupportModal")', self.js_content)

    def test_style_css_rules(self):
        """Verify CSS contains styles for latest release banner, crypto support, and modal."""
        self.assertIn(".latest-release-banner", self.css_content)
        self.assertIn(".rel-banner-body", self.css_content)
        self.assertIn(".support-crypto-card", self.css_content)
        self.assertIn(".modal-overlay", self.css_content)
        self.assertIn(".btn-support-pill", self.css_content)
        self.assertIn(".badge-usdt", self.css_content)
        self.assertIn(".badge-btc", self.css_content)

    def test_all_local_assets_exist(self):
        """Verify that every local file referenced in index.html exists in benchmark-site/."""
        links = re.findall(r'(?:src|href)=["\']([^"\'#?:][^"\'#?]*)["\']', self.html_content)
        missing = []
        for link in links:
            if (
                link.startswith("http")
                or link.startswith("//")
                or link.startswith("data:")
                or ":" in link
            ):
                continue
            clean_link = link.split("?")[0]
            target_path = SITE_DIR / clean_link
            if not target_path.exists():
                missing.append(clean_link)
        self.assertEqual(missing, [], f"Missing referenced files in benchmark-site: {missing}")

    def test_update_script_idempotent(self):
        """Verify scripts/update_benchmark_site.py runs cleanly in isolation and leaves no drift."""
        with tempfile.TemporaryDirectory() as tmp:
            temp_site = Path(tmp) / "benchmark-site"
            shutil.copytree(SITE_DIR, temp_site)
            res = subprocess.run(
                [sys.executable, str(UPDATE_SCRIPT), "--site-dir", str(temp_site)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(res.returncode, 0, f"Script failed: {res.stderr}")
            self.assertIn("Updated index.html successfully", res.stdout)
            chk = subprocess.run(
                [sys.executable, str(UPDATE_SCRIPT), "--site-dir", str(temp_site), "--check"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(chk.returncode, 0, f"Check after update failed: {chk.stdout}")


if __name__ == "__main__":
    unittest.main()
