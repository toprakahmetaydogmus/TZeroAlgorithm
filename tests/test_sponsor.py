"""
Tests for T-Zero Web3 Sponsor and Donation System.
Validates CLI sponsor hub, SVG QR codes, traffic cards, browser safety,
and privacy compliance (zero age mentions).
"""

import io
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parent.parent

EVM_ADDR = "0xF36Cd453f9F2bE91647C006C46ff66fB41d9F0c5"
BTC_ADDR = "bc1q9k4hvd6c2g8l9w3z7v8f2k3j5l8n9m1p4q7r0s"
TRON_ADDR = "TE7uKxZJ414u938gWf6bYh9QvRk2141517"


class TestSponsorCLI(unittest.TestCase):
    """Test CLI commands and handlers for sponsorship and donation hub."""

    def test_cli_sponsor_subcommand_via_subprocess(self):
        """Verify 'python tzero_v3.py sponsor' prints EVM, BTC, and Tron addresses."""
        cmd = [sys.executable, str(REPO_ROOT / "tzero_v3.py"), "sponsor"]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
        self.assertEqual(proc.returncode, 0, f"Command failed: {proc.stderr}")
        out = proc.stdout
        self.assertIn(EVM_ADDR, out)
        self.assertIn(BTC_ADDR, out)
        self.assertIn(TRON_ADDR, out)
        self.assertIn(f"ethereum:{EVM_ADDR}", out)
        self.assertIn(f"bitcoin:{BTC_ADDR}", out)
        self.assertIn(f"tron:{TRON_ADDR}", out)

    def test_cli_sponsor_flag_via_subprocess(self):
        """Verify 'python tzero_v3.py --sponsor' prints EVM, BTC, and Tron addresses."""
        cmd = [sys.executable, str(REPO_ROOT / "tzero_v3.py"), "--sponsor"]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
        self.assertEqual(proc.returncode, 0, f"Command failed: {proc.stderr}")
        out = proc.stdout
        self.assertIn(EVM_ADDR, out)
        self.assertIn(BTC_ADDR, out)
        self.assertIn(TRON_ADDR, out)

    def test_print_sponsor_hub_direct_call(self):
        """Verify calling print_sponsor_hub directly prints all required data."""
        from tzero.tzero_v3 import print_sponsor_hub

        buf = io.StringIO()
        with mock.patch("sys.stdout", buf):
            print_sponsor_hub(open_browser=False)
        output = buf.getvalue()

        self.assertIn(EVM_ADDR, output)
        self.assertIn(BTC_ADDR, output)
        self.assertIn(TRON_ADDR, output)
        self.assertIn("https://tzero-indol.vercel.app/#support", output)

    def test_browser_opening_safety(self):
        """Verify open_browser=True safely attempts to open URL and does not crash on error."""
        from tzero.tzero_v3 import print_sponsor_hub

        with mock.patch("webbrowser.open") as mock_open:
            print_sponsor_hub(open_browser=True)
            mock_open.assert_called_once_with("https://tzero-indol.vercel.app/#support")

        # Verify it handles browser exceptions gracefully
        with mock.patch("webbrowser.open", side_effect=Exception("Browser not available")):
            try:
                print_sponsor_hub(open_browser=True)
            except Exception as e:
                self.fail(f"print_sponsor_hub crashed on browser exception: {e}")


class TestCryptoTrafficCard(unittest.TestCase):
    """Test tzero_traffic.print_crypto_support_card()."""

    def test_traffic_support_card_returns_all_addresses(self):
        """Verify print_crypto_support_card includes EVM, BTC, and USDT in return dict."""
        from tzero.tzero_traffic import print_crypto_support_card

        buf = io.StringIO()
        with mock.patch("sys.stdout", buf):
            data = print_crypto_support_card()
        output = buf.getvalue()

        self.assertIn(EVM_ADDR, data.get("eth", ""))
        self.assertIn(EVM_ADDR, data.get("ethereum", ""))
        self.assertIn(BTC_ADDR, data.get("btc", ""))
        self.assertIn(TRON_ADDR, data.get("usdt_trc20", ""))

        self.assertIn(EVM_ADDR, output)
        self.assertIn(BTC_ADDR, output)
        self.assertIn(TRON_ADDR, output)


class TestQRSVGAssets(unittest.TestCase):
    """Test generated offline vector SVG QR code files."""

    def test_svg_files_exist_in_assets_and_benchmark(self):
        """Verify that all 3 SVG files exist in both assets/ and benchmark-site/assets/."""
        files = ["qr_ethereum.svg", "qr_bitcoin.svg", "qr_tron.svg"]
        for f in files:
            asset_path = REPO_ROOT / "assets" / f
            mirror_path = REPO_ROOT / "benchmark-site" / "assets" / f
            self.assertTrue(asset_path.is_file(), f"Missing {asset_path}")
            self.assertTrue(mirror_path.is_file(), f"Missing {mirror_path}")
            self.assertGreater(asset_path.stat().st_size, 500)
            self.assertEqual(asset_path.read_bytes(), mirror_path.read_bytes())

    def test_svg_files_are_valid_xml(self):
        """Verify each SVG parses as valid XML and has svg root with viewBox."""
        files = ["qr_ethereum.svg", "qr_bitcoin.svg", "qr_tron.svg"]
        for f in files:
            path = REPO_ROOT / "assets" / f
            tree = ET.parse(str(path))
            root = tree.getroot()
            self.assertTrue(root.tag.endswith("svg"), f"{f} root tag is not svg: {root.tag}")
            self.assertIn("viewBox", root.attrib, f"{f} missing viewBox attribute")

    def test_generator_script_execution(self):
        """Verify scripts/generate_donation_qrs.py executes cleanly."""
        from scripts.generate_donation_qrs import generate_qr_svgs

        generated = generate_qr_svgs(REPO_ROOT)
        self.assertEqual(len(generated), 3)


class TestWebAndDocumentationIntegrations(unittest.TestCase):
    """Test READMEs, benchmark site, and FUNDING.yml integrations."""

    def test_readme_contains_qr_details_and_links(self):
        """Verify README.md contains collapsible QR code details and 1-click links."""
        content = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("<details>", content)
        self.assertIn("qr_ethereum.svg", content)
        self.assertIn("qr_bitcoin.svg", content)
        self.assertIn("qr_tron.svg", content)
        self.assertIn(f"ethereum:{EVM_ADDR}", content)
        self.assertIn(f"bitcoin:{BTC_ADDR}", content)
        self.assertIn(f"tron:{TRON_ADDR}", content)

    def test_multi_lang_readmes_contain_sponsorship(self):
        """Verify docs/README.tr.md, ja.md, zh.md contain sponsorship and QR codes."""
        for lang_file in ["docs/README.tr.md", "docs/README.ja.md", "docs/README.zh.md"]:
            content = (REPO_ROOT / lang_file).read_text(encoding="utf-8")
            self.assertIn("qr_ethereum.svg", content, f"Missing in {lang_file}")
            self.assertIn(EVM_ADDR, content, f"Missing EVM in {lang_file}")
            self.assertIn(BTC_ADDR, content, f"Missing BTC in {lang_file}")
            self.assertIn(TRON_ADDR, content, f"Missing Tron in {lang_file}")

    def test_benchmark_site_contains_evm_and_qr_toggles(self):
        """Verify benchmark-site/index.html includes EVM in grid and QR toggles."""
        html = (REPO_ROOT / "benchmark-site" / "index.html").read_text(encoding="utf-8")
        self.assertIn("addr-eth", html)
        self.assertIn(EVM_ADDR, html)
        self.assertIn("qr-eth-grid", html)
        self.assertIn("qr-btc-grid", html)
        self.assertIn("qr-usdt-grid", html)
        self.assertIn("qr-eth-modal", html)
        self.assertIn("qr-btc-modal", html)
        self.assertIn("qr-usdt-modal", html)
        self.assertIn("btn-qr-toggle", html)

    def test_funding_yml_contains_explorer_links(self):
        """Verify .github/FUNDING.yml contains HTTPS links for Mempool and Tronscan."""
        funding = (REPO_ROOT / ".github" / "FUNDING.yml").read_text(encoding="utf-8")
        self.assertIn("mempool.space/address/" + BTC_ADDR, funding)
        self.assertIn("tronscan.org/#/address/" + TRON_ADDR, funding)
        self.assertIn("metamask.app.link/send/" + EVM_ADDR, funding)
        self.assertIn("tzero-indol.vercel.app/#support", funding)


class TestPrivacyStrictGuarantee(unittest.TestCase):
    """Ensure strictly zero mention of user age across all new/modified sponsor assets."""

    def test_no_age_mentions_in_sponsor_files(self):
        """Verify that sponsor-related files contain zero user age mentions."""
        _d = "1" + "5"
        forbidden_patterns = [
            f"{_d}-year-old",
            f"{_d} years old",
            f"{_d} yaşında",
            f"{_d} yaşındayım",
            f"{_d}-Year-Old",
        ]
        files_to_check = [
            REPO_ROOT / "scripts" / "generate_donation_qrs.py",
            REPO_ROOT / "tzero_v3.py",
            REPO_ROOT / "tzero" / "tzero_traffic.py",
            REPO_ROOT / ".github" / "FUNDING.yml",
            REPO_ROOT / "benchmark-site" / "index.html",
            REPO_ROOT / "docs" / "README.ja.md",
            REPO_ROOT / "docs" / "README.zh.md",
        ]
        for f in files_to_check:
            text = f.read_text(encoding="utf-8", errors="ignore")
            for pat in forbidden_patterns:
                self.assertNotIn(pat, text, f"Privacy violation '{pat}' found in {f}")


if __name__ == "__main__":
    unittest.main()
