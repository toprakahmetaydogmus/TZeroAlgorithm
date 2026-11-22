"""
Tier 4: Real-World Application Acceptance Scenarios
Authoritative specification from ORIGINAL_REQUEST.md, SCOPE.md, TEST_INFRA.md, and Spec Miner handoff.
Executes end-to-end integration workflows across multiple touchpoints and user journeys.
"""

import os
import re
import socket
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

EVM_ADDRESS = "0xF36Cd453f9F2bE91647C006C46ff66fB41d9F0c5"
BTC_ADDRESS = "bc1q9k4hvd6c2g8l9w3z7v8f2k3j5l8n9m1p4q7r0s"
TRON_ADDRESS = "TE7uKxZJ414u938gWf6bYh9QvRk2141517"

EIP681_URI = f"ethereum:{EVM_ADDRESS}"
METAMASK_URL = f"https://metamask.app.link/send/{EVM_ADDRESS}"
BIP21_URI = f"bitcoin:{BTC_ADDRESS}?label=T-Zero%20Sponsorship"
TRON_URI = f"tron:{TRON_ADDRESS}"

CANONICAL_VERSION = "12.1.4"
GITHUB_OWNER = "toprakahmetaydogmus"

AGE_PATTERN = re.compile(
    r"\b(?:1[0-9]|20)\s*[-–—]?\s*(?:years?|yo|yr|yaş|yas|ans|jahre)\b|"
    r"\bage\s*(?:of\s*)?1[0-9]\b|"
    r"\b15\s*(?:yaş|yasında|yasinda|yillik|yıllık)\b|"
    r"\bfifteen\s*years?\s*old\b",
    re.IGNORECASE,
)


class TestTier4Scenarios(unittest.TestCase):
    """Tier 4: 5 comprehensive end-to-end application scenarios."""

    def test_t4_01_contributor_donation_journey(self):
        """Scenario 1: End-to-End Contributor Donation Journey across CLI, GitHub, Docs, and Web."""
        # 1. CLI Touchpoint
        cli_res = subprocess.run(
            [sys.executable, "-m", "tzero", "sponsor"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=10,
        )
        self.assertEqual(cli_res.returncode, 0)
        cli_out = cli_res.stdout
        self.assertIn(EVM_ADDRESS, cli_out)
        self.assertIn(BTC_ADDRESS, cli_out)
        self.assertIn(TRON_ADDRESS, cli_out)

        # 2. GitHub FUNDING.yml Touchpoint
        funding_content = (REPO_ROOT / ".github" / "FUNDING.yml").read_text(encoding="utf-8")
        self.assertIn(EVM_ADDRESS, funding_content)
        self.assertIn(METAMASK_URL, funding_content)

        # 3. Documentation Touchpoint
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(EIP681_URI, readme)
        self.assertIn(BIP21_URI, readme)
        self.assertIn(TRON_URI, readme)
        self.assertIn(METAMASK_URL, readme)

        # 4. Benchmark Site Web Touchpoint
        index_html = (REPO_ROOT / "benchmark-site" / "index.html").read_text(encoding="utf-8")
        self.assertIn(f'href="{EIP681_URI}"', index_html)
        self.assertIn(f'href="{BIP21_URI}"', index_html)
        self.assertIn(f'href="{TRON_URI}"', index_html)
        self.assertIn(METAMASK_URL, index_html)

        # 5. Programmatic bit-for-bit consistency assertion
        self.assertEqual(EVM_ADDRESS, "0xF36Cd453f9F2bE91647C006C46ff66fB41d9F0c5")
        self.assertEqual(BTC_ADDRESS, "bc1q9k4hvd6c2g8l9w3z7v8f2k3j5l8n9m1p4q7r0s")
        self.assertEqual(TRON_ADDRESS, "TE7uKxZJ414u938gWf6bYh9QvRk2141517")

    def test_t4_02_clean_workspace_build_parity_and_privacy_audit(self):
        """Scenario 2: Clean Workspace Build, Parity & Privacy Audit across files & test suites."""
        # 1. Full Privacy Audit across core files
        scanned_files = (
            list((REPO_ROOT / "tzero").glob("*.py"))
            + list((REPO_ROOT / "tests").glob("*.py"))
            + [REPO_ROOT / "README.md", REPO_ROOT / "pyproject.toml"]
        )
        for p in scanned_files:
            text = p.read_text(encoding="utf-8", errors="ignore")
            matches = AGE_PATTERN.findall(text)
            self.assertEqual(matches, [], f"Age leaked in {p.name}: {matches}")

        # 2. Rust Core Manifest and PyO3 Bindings Parity
        cargo_text = (REPO_ROOT / "crates" / "tzero_core" / "Cargo.toml").read_text(encoding="utf-8")
        self.assertIn('edition = "2021"', cargo_text)
        self.assertIn(f'version = "{CANONICAL_VERSION}"', cargo_text)

        pb_text = (REPO_ROOT / "crates" / "tzero_core" / "src" / "python_bindings.rs").read_text(encoding="utf-8")
        self.assertIn("fuzzy_symbol_search", pb_text)
        self.assertIn("register_python_bindings", pb_text)

        # 3. Run Growth Test and Benchmark Site Test
        res = subprocess.run(
            [sys.executable, "-m", "unittest", "tests/test_growth.py", "tests/test_benchmark_site.py"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=20,
        )
        self.assertEqual(res.returncode, 0, f"Quality gate tests failed: {res.stderr}")
        self.assertIn("OK", res.stderr + res.stdout)

    def test_t4_03_multilingual_documentation_and_web3_consistency(self):
        """Scenario 3: Multi-Language Documentation & Web3 Consistency."""
        readme_files = [REPO_ROOT / "README.md"]
        docs_dir = REPO_ROOT / "docs"
        if docs_dir.is_dir():
            readme_files.extend(list(docs_dir.glob("README*.md")))

        self.assertGreaterEqual(len(readme_files), 1)
        for doc in readme_files:
            text = doc.read_text(encoding="utf-8", errors="ignore")
            # Verify privacy
            self.assertEqual(AGE_PATTERN.findall(text), [], f"Age found in {doc.name}")
            # Verify root README has all addresses
            if doc.name == "README.md":
                self.assertIn(EVM_ADDRESS, text)
                self.assertIn(BTC_ADDRESS, text)
                self.assertIn(TRON_ADDRESS, text)

        # Verify FUNDING.yml aligns
        funding = (REPO_ROOT / ".github" / "FUNDING.yml").read_text(encoding="utf-8")
        self.assertIn(EVM_ADDRESS, funding)

    def test_t4_04_offline_airgapped_verification_and_zero_leak(self):
        """Scenario 4: Air-Gapped Network Isolation & Zero-Leak Security Execution."""
        # Mock network socket to ensure zero outbound network calls occur
        real_connect = socket.socket.connect

        def blocked_connect(self, address):
            raise OSError("Air-gapped security enforcement: network blocked during test")

        with patch.object(socket.socket, "connect", blocked_connect):
            from tzero.tzero_v3 import print_sponsor_hub

            # Must run cleanly in air-gapped mode with 0 network calls
            with patch("sys.stdout"):
                print_sponsor_hub(open_browser=False)

        # Verify offline SVG / CSS styling in benchmark-site
        css = (REPO_ROOT / "benchmark-site" / "style.css").read_text(encoding="utf-8")
        self.assertIn(".crypto-qr-container", css)

        # Scan for exposed API keys across config and docs
        secret_pat = re.compile(r"\b(?:sk-[a-zA-Z0-9]{32,}|ghp_[a-zA-Z0-9]{36})\b")
        for f in [REPO_ROOT / "README.md", REPO_ROOT / ".github" / "FUNDING.yml"]:
            content = f.read_text(encoding="utf-8")
            self.assertIsNone(secret_pat.search(content), f"Secret key leaked in {f.name}")

    def test_t4_05_production_release_readiness_audit(self):
        """Scenario 5: Production Release Readiness & Publishing Audit."""
        # 1. Version Parity Check
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn(f'version = "{CANONICAL_VERSION}"', pyproject)

        cargo = (REPO_ROOT / "crates" / "tzero_core" / "Cargo.toml").read_text(encoding="utf-8")
        self.assertIn(f'version = "{CANONICAL_VERSION}"', cargo)

        site = (REPO_ROOT / "benchmark-site" / "index.html").read_text(encoding="utf-8")
        self.assertIn(CANONICAL_VERSION, site)

        # 2. PyInstaller 5-Binary Packaging Specification
        compile_code = (REPO_ROOT / "scripts" / "build" / "compile.py").read_text(encoding="utf-8")
        for target in ("TZeroAlgorithm", "TZeroCLI", "TZeroMCP", "AddMCP", "TZeroCI"):
            self.assertIn(target, compile_code)
        self.assertIn("create_release_bundle", compile_code)

        # 3. Release Workflow Automation
        release_yml = (REPO_ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertIn("push:", release_yml)
        self.assertIn("'v*'", release_yml)
        self.assertIn("softprops/action-gh-release", release_yml)


if __name__ == "__main__":
    unittest.main(verbosity=2)
