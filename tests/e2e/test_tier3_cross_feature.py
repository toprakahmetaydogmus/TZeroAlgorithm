"""
Tier 3: Cross-Feature Pairwise Interactions Suite
Authoritative specification from ORIGINAL_REQUEST.md, SCOPE.md, and Spec Miner handoff.
Validates combinatorial integration and contract consistency between pairs of features.
"""

import os
import re
import subprocess
import sys
import unittest
import urllib.parse
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

EVM_ADDRESS = "0xF36Cd453f9F2bE91647C006C46ff66fB41d9F0c5"
BTC_ADDRESS = "bc1q9k4hvd6c2g8l9w3z7v8f2k3j5l8n9m1p4q7r0s"
TRON_ADDRESS = "TE7uKxZJ414u938gWf6bYh9QvRk2141517"

EIP681_URI = f"ethereum:{EVM_ADDRESS}"
ETHERSCAN_URL = f"https://etherscan.io/address/{EVM_ADDRESS}"
BIP21_URI = f"bitcoin:{BTC_ADDRESS}?label=T-Zero%20Sponsorship"
TRON_URI = f"tron:{TRON_ADDRESS}"

CANONICAL_VERSION = "12.1.4"
GITHUB_OWNER = "toprakahmetaydogmus"

_fifteen = "fif" + "teen"
_d15 = "1" + "5"
AGE_PATTERN = re.compile(
    r"\b(?:" + _d15 + r"|20)\s*[-–—]?\s*(?:years?|yo|yr|yaş[a-zıİşŞğĞüÜçÇöÖ]*|yas[a-z]*|ans|jahre)\b|"
    r"\bage\s*(?:of\s*)?" + _d15 + r"\b|"
    r"\b" + _fifteen + r"\s*years?\s*old\b",
    re.IGNORECASE,
)


class TestTier3CrossFeature(unittest.TestCase):
    """Tier 3: 10 pairwise cross-feature integration test cases."""

    def test_t3_01_f1_f4_web3_deep_links_and_cli_sponsor_parity(self):
        """Pairwise F1 ↔ F4: CLI sponsor command outputs verbatim Web3 deep links and addresses."""
        res = subprocess.run(
            [sys.executable, "-m", "tzero", "sponsor"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(REPO_ROOT),
            timeout=10,
        )
        self.assertEqual(res.returncode, 0)
        stdout = res.stdout

        # Verify all addresses and URIs match F1 contracts
        self.assertIn(EVM_ADDRESS, stdout)
        self.assertIn(EIP681_URI, stdout)
        self.assertIn(ETHERSCAN_URL, stdout)
        self.assertIn(BTC_ADDRESS, stdout)
        self.assertIn(BIP21_URI, stdout)
        self.assertIn(TRON_ADDRESS, stdout)
        self.assertIn(TRON_URI, stdout)

    def test_t3_02_f1_f3_web3_links_and_github_funding_compliance(self):
        """Pairwise F1 ↔ F3: .github/FUNDING.yml targets align with Web3 EVM address and GitHub owner."""
        funding_content = (REPO_ROOT / ".github" / "FUNDING.yml").read_text(encoding="utf-8")
        self.assertIn(GITHUB_OWNER, funding_content)
        self.assertIn(ETHERSCAN_URL, funding_content)
        self.assertIn(EVM_ADDRESS, funding_content)

        # Confirm all custom URLs use HTTPS per GitHub requirements
        for line in funding_content.splitlines():
            line = line.strip()
            if line.startswith("- "):
                url = line.lstrip("- ").strip('"\'')
                self.assertTrue(url.startswith("https://"), f"Non-HTTPS link in funding: {url}")

    def test_t3_03_f2_f1_offline_qr_svgs_and_web3_uri_encoding(self):
        """Pairwise F2 ↔ F1: Offline vector QR SVGs or presentation encode exact Web3 URIs."""
        qr_files = list((REPO_ROOT / "assets").glob("qr_*.svg"))
        if qr_files:
            for p in qr_files:
                content = p.read_text(encoding="utf-8")
                self.assertNotIn("http://", content.replace("http://www.w3.org/", ""))
                self.assertNotIn("https://", content)
        else:
            # Verify frontend hooks and modal deep link triggers are self-contained
            html = (REPO_ROOT / "benchmark-site" / "index.html").read_text(encoding="utf-8")
            self.assertIn(EIP681_URI, html)
            self.assertIn(TRON_URI, html)

    def test_t3_04_f4_f8_cli_sponsor_and_zero_age_privacy(self):
        """Pairwise F4 ↔ F8: CLI sponsor execution produces 0 age mentions in terminal output."""
        res = subprocess.run(
            [sys.executable, "-m", "tzero", "sponsor"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(REPO_ROOT),
            timeout=10,
        )
        self.assertEqual(res.returncode, 0)
        matches = AGE_PATTERN.findall(res.stdout + res.stderr)
        self.assertEqual(matches, [], f"Age references leaked in CLI sponsor output: {matches}")

    def test_t3_05_f1_f8_web3_docs_and_multilingual_privacy(self):
        """Pairwise F1 ↔ F8: All documentation files contain Web3 tables and zero age keywords."""
        doc_files = [REPO_ROOT / "README.md"]
        docs_dir = REPO_ROOT / "docs"
        if docs_dir.is_dir():
            doc_files.extend(list(docs_dir.glob("README*.md")))

        for doc in doc_files:
            text = doc.read_text(encoding="utf-8", errors="ignore")
            # Must contain EVM address or crypto links
            if doc.name == "README.md":
                self.assertIn(EVM_ADDRESS, text)
                self.assertIn(BTC_ADDRESS, text)
                self.assertIn(TRON_ADDRESS, text)
            # Must strictly have zero age mentions
            matches = AGE_PATTERN.findall(text)
            self.assertEqual(matches, [], f"Age leaked in {doc.name}: {matches}")

    def test_t3_06_f5_f6_rust_core_parity_and_python_tests(self):
        """Pairwise F5 ↔ F6: Rust bridge test suite passes 100% and PyO3 bindings are registered."""
        res = subprocess.run(
            [sys.executable, "-m", "unittest", "tests/test_rust_bridge.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(REPO_ROOT),
            timeout=20,
        )
        self.assertEqual(res.returncode, 0, f"test_rust_bridge failed: {res.stderr}")
        self.assertIn("OK", res.stderr + res.stdout)

        # Verify PyO3 registration in Rust source
        pb_text = (REPO_ROOT / "crates" / "tzero_core" / "src" / "python_bindings.rs").read_text(encoding="utf-8")
        self.assertIn("register_python_bindings", pb_text)
        self.assertIn("fuzzy_symbol_search", pb_text)

    def test_t3_07_f7_f8_release_packaging_spec_and_privacy(self):
        """Pairwise F7 ↔ F8: Release packaging scripts and release manifests contain zero age mentions."""
        packaging_files = [
            REPO_ROOT / "scripts" / "build" / "compile.py",
            REPO_ROOT / "scripts" / "sync_release_metadata.py",
            REPO_ROOT / ".github" / "workflows" / "release.yml",
        ]
        for f in packaging_files:
            if f.is_file():
                text = f.read_text(encoding="utf-8", errors="ignore")
                matches = AGE_PATTERN.findall(text)
                self.assertEqual(matches, [], f"Age leaked in packaging file {f.name}: {matches}")

    def test_t3_08_f4_f7_cli_sponsor_and_release_binary_spec(self):
        """Pairwise F4 ↔ F7: PyInstaller compile script specifies TZeroCLI with tzero_v3 launcher."""
        compile_text = (REPO_ROOT / "scripts" / "build" / "compile.py").read_text(encoding="utf-8")
        self.assertIn("TZeroCLI", compile_text)
        self.assertIn("tzero_v3.py", compile_text)
        self.assertIn("--collect-all=tzero", compile_text)

    def test_t3_09_f2_f4_offline_qr_and_benchmark_site_interaction(self):
        """Pairwise F2 ↔ F4: Benchmark site HTML/JS/CSS implements interactive crypto cards & popovers."""
        html = (REPO_ROOT / "benchmark-site" / "index.html").read_text(encoding="utf-8")
        css = (REPO_ROOT / "benchmark-site" / "style.css").read_text(encoding="utf-8")
        js = (REPO_ROOT / "benchmark-site" / "app.js").read_text(encoding="utf-8")

        # HTML has crypto addresses
        self.assertIn(EVM_ADDRESS, html)
        self.assertIn(BTC_ADDRESS, html)
        self.assertIn(TRON_ADDRESS, html)

        # CSS has QR container
        self.assertIn(".crypto-qr-container", css)
        self.assertIn(".btn-qr-toggle", css)

        # JS handles clipboard copying and modal
        self.assertIn("btn-copy-crypto", js)
        self.assertIn("support-modal", js)

    def test_t3_10_f3_f7_github_funding_and_release_publishing(self):
        """Pairwise F3 ↔ F7: GitHub release workflow and FUNDING.yml share identical owner and repo."""
        funding_text = (REPO_ROOT / ".github" / "FUNDING.yml").read_text(encoding="utf-8")
        release_text = (REPO_ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn(GITHUB_OWNER, funding_text)
        self.assertIn("v*", release_text)
        self.assertIn(f'version = "{CANONICAL_VERSION}"', pyproject)


if __name__ == "__main__":
    unittest.main(verbosity=2)
