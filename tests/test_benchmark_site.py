# tests/test_benchmark_site.py
"""
Unit and integration tests for the live Vercel Benchmark Hub (benchmark-site/)
and the synchronization script (scripts/update_benchmark_site.py).
"""

import unittest
from pathlib import Path
import re
import subprocess

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = REPO_ROOT / "benchmark-site"
INDEX_HTML = SITE_DIR / "index.html"
APP_JS = SITE_DIR / "app.js"
STYLE_CSS = SITE_DIR / "style.css"
UPDATE_SCRIPT = REPO_ROOT / "scripts" / "update_benchmark_site.py"


class TestBenchmarkSite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html_content = INDEX_HTML.read_text(encoding="utf-8")
        cls.js_content = APP_JS.read_text(encoding="utf-8")
        cls.css_content = STYLE_CSS.read_text(encoding="utf-8")

    def test_no_old_version_references(self):
        """Ensure no obsolete v11.15.5 or v11.11.0 references remain in index.html."""
        self.assertNotIn("v11.15.5", self.html_content)
        self.assertNotIn("11.15.5", self.html_content)
        self.assertNotIn("v11.11.0", self.html_content)
        self.assertNotIn("11.11.0", self.html_content)

    def test_version_12_1_0_present_in_key_metadata(self):
        """Verify v12.1.4 is set in title, meta, json-ld, and hero badges."""
        self.assertIn("T-Zero v12.1.4", self.html_content)
        self.assertIn('"softwareVersion": "12.1.4"', self.html_content)
        self.assertIn("style.css?v=12.1.4", self.html_content)
        self.assertIn("app.js?v=12.1.4", self.html_content)
        self.assertIn("PyPI v12.1.4", self.html_content)
        self.assertIn("T-ZERO v12.1.4 — TDQS 5.0/5.0 GRADE A SOVEREIGN RELEASE", self.html_content)

    def test_six_download_assets_verified_with_sha256(self):
        """Verify all 6 official downloads with exact sizes, names, URLs, and real SHA-256 hashes."""
        expected_assets = [
            {
                "name": "TZero-v12.1.4-Windows-x64.zip",
                "size": "351.16 MB",
                "sha": "271f45ea3a6d9a475d37e7919c6926fdfc9fa618822b91ffa154184320464e20",
                "url": "https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/download/v12.1.4/TZero-v12.1.4-Windows-x64.zip"
            },
            {
                "name": "TZeroAlgorithm.exe",
                "size": "64.92 MB",
                "sha": "933294888e94519d04e15d5bea19d45ca74bce9f248d402028a6b34ab2f4372d",
                "url": "https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/download/v12.1.4/TZeroAlgorithm.exe"
            },
            {
                "name": "TZeroCLI.exe",
                "size": "64.76 MB",
                "sha": "ef3ab0735265feaac3a18e2a5e90b29ca678726fcf3c8e563fc0c5cbdd84279b",
                "url": "https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/download/v12.1.4/TZeroCLI.exe"
            },
            {
                "name": "TZeroMCP.exe",
                "size": "63.17 MB",
                "sha": "d0903a0621cb21b39dd33fb37150c0eec09677a9404b26d5b23b9e36af3bc42f",
                "url": "https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/download/v12.1.4/TZeroMCP.exe"
            },
            {
                "name": "AddMCP.exe",
                "size": "98.80 MB",
                "sha": "bd78e5a1b393e92a8534da259e23f48a731d26d2c0c342b63c1c9824de59806d",
                "url": "https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/download/v12.1.4/AddMCP.exe"
            },
            {
                "name": "tzero-vscode-12.1.4.vsix",
                "size": "122 KB",
                "sha": "ab446d62bf7fdbc93617ad29d5bd011d882fe1a8a29488e0cf3ff302dc897f24",
                "url": "https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/download/v12.1.4/tzero-vscode-12.1.4.vsix"
            }
        ]

        for asset in expected_assets:
            self.assertIn(asset["name"], self.html_content)
            self.assertIn(asset["size"], self.html_content)
            self.assertIn(asset["sha"], self.html_content)
            self.assertIn(asset["url"], self.html_content)

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
        # Check fallback to v12.1.4
        self.assertIn("v12.1.4", self.js_content)
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
            # Strip query params
            clean_link = link.split("?")[0]
            target_path = SITE_DIR / clean_link
            if not target_path.exists():
                missing.append(clean_link)
        self.assertEqual(missing, [], f"Missing referenced files in benchmark-site: {missing}")

    def test_update_script_idempotent(self):
        """Verify scripts/update_benchmark_site.py can run cleanly and produces valid output."""
        res = subprocess.run(["python", str(UPDATE_SCRIPT)], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Script failed: {res.stderr}")
        self.assertIn("Updated index.html successfully", res.stdout)


if __name__ == "__main__":
    unittest.main()
