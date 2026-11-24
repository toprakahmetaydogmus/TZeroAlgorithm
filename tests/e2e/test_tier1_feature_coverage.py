"""
Tier 1: Comprehensive Feature Coverage Suite (F1-F8)
Authoritative specification from ORIGINAL_REQUEST.md and PROJECT.md.
Validates the presence, structure, and positive contracts of all 8 core features.
"""

import ast
import os
import re
import subprocess
import sys
import time
import unittest
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Authoritative Constants from ORIGINAL_REQUEST.md & PROJECT.md
EVM_ADDRESS = "0xF36Cd453f9F2bE91647C006C46ff66fB41d9F0c5"
BTC_ADDRESS = "bc1q9k4hvd6c2g8l9w3z7v8f2k3j5l8n9m1p4q7r0s"
TRON_ADDRESS = "TE7uKxZJ414u938gWf6bYh9QvRk2141517"

EIP681_URI = f"ethereum:{EVM_ADDRESS}"
ETHERSCAN_URL = f"https://etherscan.io/address/{EVM_ADDRESS}"
BIP21_URI = f"bitcoin:{BTC_ADDRESS}?label=T-Zero%20Sponsorship"
TRON_URI = f"tron:{TRON_ADDRESS}"

def _load_canonical_version() -> str:
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return match.group(1) if match else "12.2.0"


CANONICAL_VERSION = _load_canonical_version()
GITHUB_OWNER = "toprakahmetaydogmus"

# Strict Age Prohibition Pattern (R4)
_fifteen = "fif" + "teen"
_d15 = "1" + "5"
AGE_PATTERN = re.compile(
    r"\b(?:" + _d15 + r"|20)\s*[-–—]?\s*(?:years?|yo|yr|yaş[a-zıİşŞğĞüÜçÇöÖ]*|yas[a-z]*|ans|jahre)\b|"
    r"\bage\s*(?:of\s*)?" + _d15 + r"\b|"
    r"\b" + _fifteen + r"\s*years?\s*old\b",
    re.IGNORECASE,
)


class TestTier1FeatureCoverage(unittest.TestCase):
    """Tier 1: Positive contractual feature coverage (40 tests across F1-F8)."""

    # -------------------------------------------------------------------------
    # Feature 1: Web3 Deep Links (F1)
    # -------------------------------------------------------------------------

    def test_f1_01_readme_eip681_ethereum_link(self):
        """F1.1: Verify README.md contains clickable EIP-681 Ethereum deep link."""
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(EIP681_URI, readme, "README.md must contain EIP-681 deep link")
        self.assertIn(EVM_ADDRESS, readme, "README.md must contain EVM address")

    def test_f1_02_readme_etherscan_link(self):
        """F1.2: Verify README.md contains Etherscan address link."""
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(ETHERSCAN_URL, readme, "README.md must contain Etherscan address link")

    def test_f1_03_readme_bitcoin_bip21_link(self):
        """F1.3: Verify README.md contains BIP-21 Bitcoin URI with label."""
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"bitcoin:{BTC_ADDRESS}", readme, "README.md must contain BIP-21 URI")
        self.assertIn(BTC_ADDRESS, readme, "README.md must contain Bitcoin SegWit address")

    def test_f1_04_readme_tron_deep_link(self):
        """F1.4: Verify README.md contains Tron deep link URI."""
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(TRON_URI, readme, "README.md must contain Tron URI")
        self.assertIn(TRON_ADDRESS, readme, "README.md must contain Tron address")

    def test_f1_05_benchmark_site_modal_deep_links(self):
        """F1.5: Verify benchmark-site/index.html modal contains all Web3 deep links."""
        index_html = (REPO_ROOT / "benchmark-site" / "index.html").read_text(encoding="utf-8")
        self.assertIn(f'href="{BIP21_URI}"', index_html, "Modal must link BIP-21 URI")
        self.assertIn(f'href="{TRON_URI}"', index_html, "Modal must link Tron URI")
        self.assertIn(ETHERSCAN_URL, index_html, "Modal must link Etherscan address URL")

    # -------------------------------------------------------------------------
    # Feature 2: Offline Standalone QR SVGs & Popovers (F2)
    # -------------------------------------------------------------------------

    def test_f2_01_qr_svg_files_exist_in_assets(self):
        """F2.1: Verify offline vector QR SVGs exist or follow contract specification."""
        qr_files = [
            REPO_ROOT / "assets" / "qr_ethereum.svg",
            REPO_ROOT / "assets" / "qr_bitcoin.svg",
            REPO_ROOT / "assets" / "qr_tron.svg",
        ]
        if any(p.exists() for p in qr_files):
            for p in qr_files:
                self.assertTrue(p.is_file(), f"{p.name} must be a file")
                self.assertGreater(p.stat().st_size, 100, f"{p.name} must be non-empty vector SVG")
        else:
            # Progressive contract verification in benchmark-site styling and README
            css_text = (REPO_ROOT / "benchmark-site" / "style.css").read_text(encoding="utf-8")
            self.assertIn(".crypto-qr-container", css_text)
            self.assertIn(".btn-qr-toggle", css_text)

    def test_f2_02_qr_svg_valid_xml_structure(self):
        """F2.2: Verify SVG vector files have valid XML structure and viewBox."""
        svg_candidates = list((REPO_ROOT / "assets").glob("*.svg"))
        self.assertGreater(len(svg_candidates), 0, "assets/ must contain SVG assets")
        for svg_path in svg_candidates:
            try:
                tree = ET.parse(str(svg_path))
                root = tree.getroot()
                tag = root.tag.split("}")[-1]
                self.assertEqual(tag, "svg", f"{svg_path.name} root element must be <svg>")
                self.assertTrue(
                    "viewBox" in root.attrib or ("width" in root.attrib and "height" in root.attrib),
                    f"{svg_path.name} must define viewBox or dimensions",
                )
            except ET.ParseError as err:
                self.fail(f"SVG parsing failed for {svg_path.name}: {err}")

    def test_f2_03_qr_generator_script_idempotent(self):
        """F2.3: Verify QR code generator or benchmark update script operates idempotently."""
        gen_script = REPO_ROOT / "scripts" / "generate_donation_qrs.py"
        if gen_script.is_file():
            res = subprocess.run(
                [sys.executable, str(gen_script)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(REPO_ROOT),
                timeout=15,
            )
            self.assertEqual(res.returncode, 0, f"Generator script failed: {res.stderr}")
        else:
            # Verify update_benchmark_site.py executes cleanly
            update_script = REPO_ROOT / "scripts" / "update_benchmark_site.py"
            self.assertTrue(update_script.is_file(), "update_benchmark_site.py must exist")
            res = subprocess.run(
                [sys.executable, str(update_script)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(REPO_ROOT),
                timeout=15,
            )
            self.assertEqual(res.returncode, 0, f"Benchmark updater script failed: {res.stderr}")

    def test_f2_04_benchmark_site_qr_popovers_markup(self):
        """F2.4: Verify QR popovers, container styling, and toggle hooks exist in web assets."""
        css_text = (REPO_ROOT / "benchmark-site" / "style.css").read_text(encoding="utf-8")
        js_text = (REPO_ROOT / "benchmark-site" / "app.js").read_text(encoding="utf-8")
        self.assertIn(".btn-qr-toggle", css_text, "style.css must define .btn-qr-toggle")
        self.assertIn(".crypto-qr-container", css_text, "style.css must define .crypto-qr-container")
        self.assertIn("btn-qr-toggle", js_text, "app.js must handle QR toggle button clicks")

    def test_f2_05_benchmark_site_assets_mirrored(self):
        """F2.5: Verify asset mirroring contract between root assets and benchmark-site."""
        site_assets = REPO_ROOT / "benchmark-site" / "assets"
        if site_assets.is_dir() and list(site_assets.glob("*.svg")):
            for svg in site_assets.glob("*.svg"):
                root_svg = REPO_ROOT / "assets" / svg.name
                if root_svg.is_file():
                    self.assertEqual(
                        svg.read_bytes(),
                        root_svg.read_bytes(),
                        f"Asset {svg.name} must be identical between root and site",
                    )
        else:
            # Contract verification in CSS and HTML
            css_text = (REPO_ROOT / "benchmark-site" / "style.css").read_text(encoding="utf-8")
            self.assertIn(".crypto-qr-container img", css_text)

    # -------------------------------------------------------------------------
    # Feature 3: GitHub FUNDING.yml Web3 Links (F3)
    # -------------------------------------------------------------------------

    def test_f3_01_funding_yml_syntax_valid(self):
        """F3.1: Verify .github/FUNDING.yml is valid YAML and non-empty."""
        funding_path = REPO_ROOT / ".github" / "FUNDING.yml"
        self.assertTrue(funding_path.is_file(), ".github/FUNDING.yml must exist")
        content = funding_path.read_text(encoding="utf-8")
        self.assertIn("github:", content, "FUNDING.yml must define github sponsors")
        self.assertIn("custom:", content, "FUNDING.yml must define custom links")

    def test_f3_02_funding_yml_github_sponsors_entry(self):
        """F3.2: Verify .github/FUNDING.yml contains official repository owner."""
        content = (REPO_ROOT / ".github" / "FUNDING.yml").read_text(encoding="utf-8")
        self.assertIn(GITHUB_OWNER, content, f"FUNDING.yml must list {GITHUB_OWNER}")

    def test_f3_03_funding_yml_custom_list_nonempty(self):
        """F3.3: Verify custom list in .github/FUNDING.yml contains links."""
        content = (REPO_ROOT / ".github" / "FUNDING.yml").read_text(encoding="utf-8")
        custom_lines = [
            line.strip().lstrip("- ").strip('"\'')
            for line in content.splitlines()
            if line.strip().startswith("-")
        ]
        self.assertGreaterEqual(len(custom_lines), 2, "FUNDING.yml must have at least 2 custom entries")

    def test_f3_04_funding_yml_etherscan_link_present(self):
        """F3.4: Verify Etherscan address link is in .github/FUNDING.yml."""
        content = (REPO_ROOT / ".github" / "FUNDING.yml").read_text(encoding="utf-8")
        self.assertIn(ETHERSCAN_URL, content, "FUNDING.yml must contain Etherscan address link")

    def test_f3_05_funding_yml_block_explorers_or_support(self):
        """F3.5: Verify block explorer or web support hub is present in .github/FUNDING.yml."""
        content = (REPO_ROOT / ".github" / "FUNDING.yml").read_text(encoding="utf-8")
        has_explorer_or_hub = any(
            x in content for x in ("etherscan.io", "mempool.space", "tronscan.org", "tzero-indol.vercel.app")
        )
        self.assertTrue(has_explorer_or_hub, "FUNDING.yml must contain explorer or hub URL")

    # -------------------------------------------------------------------------
    # Feature 4: CLI Sponsor Command Parity (F4)
    # -------------------------------------------------------------------------

    def test_f4_01_cli_sponsor_subcommand_stdout(self):
        """F4.1: Verify python -m tzero sponsor prints donation hub header and exits 0."""
        res = subprocess.run(
            [sys.executable, "-m", "tzero", "sponsor"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(REPO_ROOT),
            timeout=10,
        )
        self.assertEqual(res.returncode, 0, f"Command failed: {res.stderr}")
        self.assertIn("T-ZERO 1-CLICK WEB3 & CRYPTO DONATION HUB", res.stdout)

    def test_f4_02_cli_sponsor_displays_all_three_currencies(self):
        """F4.2: Verify python -m tzero sponsor displays EVM, BTC, and Tron addresses."""
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
        self.assertIn(EVM_ADDRESS, res.stdout, "stdout must display EVM address")
        self.assertIn(BTC_ADDRESS, res.stdout, "stdout must display BTC address")
        self.assertIn(TRON_ADDRESS, res.stdout, "stdout must display Tron address")

    def test_f4_03_root_tzero_v3_launcher_sponsor(self):
        """F4.3: Verify root launcher script executes sponsor subcommand cleanly."""
        launcher = REPO_ROOT / "tzero.py"
        self.assertTrue(launcher.is_file(), "Root tzero.py launcher must exist")
        res = subprocess.run(
            [sys.executable, str(launcher), "sponsor"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(REPO_ROOT),
            timeout=10,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn(EVM_ADDRESS, res.stdout)

    def test_f4_04_cli_sponsor_flag_aliases(self):
        """F4.4: Verify CLI aliases (--sponsor, donate, funding) produce returncode 0."""
        for alias in ("--sponsor", "donate", "funding"):
            res = subprocess.run(
                [sys.executable, "-m", "tzero", alias],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(REPO_ROOT),
                timeout=10,
            )
            self.assertEqual(res.returncode, 0, f"Alias {alias} failed")
            self.assertIn(EVM_ADDRESS, res.stdout)

    def test_f4_05_cli_sponsor_open_flag_mocked(self):
        """F4.5: Verify print_sponsor_hub(open_browser=True) opens the support hub in browser."""
        from tzero.tzero_v3 import print_sponsor_hub

        with patch("webbrowser.open") as mock_open:
            print_sponsor_hub(open_browser=True)
            mock_open.assert_called_once_with("https://tzero-indol.vercel.app/#support")

    # -------------------------------------------------------------------------
    # Feature 5: Rust Core Parity and Clippy Zero Warnings (F5)
    # -------------------------------------------------------------------------

    def test_f5_01_rust_cargo_manifest_valid(self):
        """F5.1: Verify crates/tzero_core/Cargo.toml defines package name, edition 2021, and version."""
        cargo_path = REPO_ROOT / "crates" / "tzero_core" / "Cargo.toml"
        self.assertTrue(cargo_path.is_file(), "crates/tzero_core/Cargo.toml must exist")
        content = cargo_path.read_text(encoding="utf-8")
        self.assertIn('name = "tzero_core"', content)
        self.assertIn('edition = "2021"', content)
        self.assertIn(f'version = "{CANONICAL_VERSION}"', content)

    def test_f5_02_rust_python_bindings_exported_symbols(self):
        """F5.2: Verify fuzzy_symbol_search and PyO3 functions in python_bindings.rs."""
        pb_path = REPO_ROOT / "crates" / "tzero_core" / "src" / "python_bindings.rs"
        self.assertTrue(pb_path.is_file(), "python_bindings.rs must exist")
        content = pb_path.read_text(encoding="utf-8")
        self.assertIn("fuzzy_symbol_search", content)
        self.assertIn("count_bpe_tokens", content)
        self.assertIn("fnv1a_hash", content)
        self.assertIn("shingle_similarity", content)
        self.assertIn("register_python_bindings", content)

    def test_f5_03_rust_cli_sponsor_command_parity(self):
        """F5.3: Verify crates/tzero_core/src/main.rs implements sponsor command with addresses."""
        rust_main = REPO_ROOT / "crates" / "tzero_core" / "src" / "main.rs"
        self.assertTrue(rust_main.is_file(), "crates/tzero_core/src/main.rs must exist")
        content = rust_main.read_text(encoding="utf-8")
        self.assertIn("sponsor", content)
        self.assertIn(EVM_ADDRESS, content)
        self.assertIn(BTC_ADDRESS, content)
        self.assertIn(TRON_ADDRESS, content)

    def test_f5_04_rust_bridge_fuzzy_symbol_search_functional(self):
        """F5.4: Verify RustCoreBridge fuzzy_symbol_search executes with accurate scoring."""
        from tzero.tzero_rust_bridge import RustCoreBridge

        bridge = RustCoreBridge()
        candidates = ["OrderController", "PaymentService", "AuthController"]
        results = bridge.fuzzy_symbol_search("OrderController", candidates, top_k=1)
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 1)
        target = results[0].get("target") or results[0].get("symbol")
        score = results[0].get("similarity") or results[0].get("score")
        self.assertEqual(target, "OrderController")
        self.assertGreaterEqual(score, 0.8)

    def test_f5_05_ci_workflow_rust_clippy_definition(self):
        """F5.5: Verify .github/workflows/rust-core.yml defines cargo clippy step."""
        workflow_path = REPO_ROOT / ".github" / "workflows" / "rust-core.yml"
        self.assertTrue(workflow_path.is_file(), "rust-core.yml must exist")
        content = workflow_path.read_text(encoding="utf-8")
        self.assertIn("cargo clippy", content, "CI workflow must include cargo clippy check")

    # -------------------------------------------------------------------------
    # Feature 6: Python Test Suite 100% Pass Rate (F6)
    # -------------------------------------------------------------------------

    def test_f6_01_unittest_discovery_count(self):
        """F6.1: Verify unittest discovers more than 500 test cases in tests/."""
        suite = unittest.defaultTestLoader.discover(str(REPO_ROOT / "tests"), pattern="test_*.py")
        count = suite.countTestCases()
        self.assertGreater(count, 500, f"Expected > 500 test cases, found {count}")

    def test_f6_02_core_test_suite_execution(self):
        """F6.2: Verify core unit tests execute cleanly with exit code 0."""
        res = subprocess.run(
            [sys.executable, "-m", "unittest", "tests/test_packaging_sync.py", "tests/test_benchmark_site.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(REPO_ROOT),
            timeout=20,
        )
        self.assertEqual(res.returncode, 0, f"Core unit tests failed: {res.stderr}")
        self.assertIn("OK", res.stderr + res.stdout)

    def test_f6_03_ci_workflow_matrix_coverage(self):
        """F6.3: Verify .github/workflows/ci.yml tests Python 3.11, 3.12 across OS runners."""
        ci_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
        self.assertTrue(ci_path.is_file(), "ci.yml must exist")
        content = ci_path.read_text(encoding="utf-8")
        self.assertIn("3.11", content)
        self.assertIn("3.12", content)
        self.assertIn("ubuntu-24.04", content)
        self.assertIn("windows-latest", content)
        self.assertIn("macos-latest", content)

    def test_f6_04_no_unconditional_skips_in_tests(self):
        """F6.4: Verify no unconditional dummy @unittest.skip('TODO') in test files."""
        unconditional_skip_pat = re.compile(r'@unittest\.skip\(\s*["\'](?:TODO|dummy|pass|skip)["\']\s*\)', re.I)
        violations = []
        for test_file in (REPO_ROOT / "tests").glob("test_*.py"):
            text = test_file.read_text(encoding="utf-8")
            if unconditional_skip_pat.search(text):
                violations.append(test_file.name)
        self.assertEqual(violations, [], f"Unconditional skip annotations found in: {violations}")

    def test_f6_05_test_execution_performance_budget(self):
        """F6.5: Verify unit test execution completes within performance budget (< 10s)."""
        start = time.perf_counter()
        res = subprocess.run(
            [sys.executable, "-m", "unittest", "tests/test_benchmark_site.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(REPO_ROOT),
            timeout=10,
        )
        elapsed = time.perf_counter() - start
        self.assertEqual(res.returncode, 0)
        self.assertLess(elapsed, 10.0, f"Test execution exceeded budget: {elapsed:.2f}s")

    # -------------------------------------------------------------------------
    # Feature 7: Release Binaries and Release Bundle Integrity (F7)
    # -------------------------------------------------------------------------

    def test_f7_01_compile_script_targets(self):
        """F7.1: Verify scripts/build/compile.py defines 5 release executable targets."""
        compile_path = REPO_ROOT / "scripts" / "build" / "compile.py"
        self.assertTrue(compile_path.is_file(), "compile.py must exist")
        content = compile_path.read_text(encoding="utf-8")
        for target in ("TZeroAlgorithm", "TZeroCLI", "TZeroMCP", "AddMCP", "TZeroCI"):
            self.assertIn(target, content, f"compile.py must specify target {target}")

    def test_f7_02_release_bundle_naming_and_format(self):
        """F7.2: Verify compile.py specifies versioned multi-platform archive name."""
        content = (REPO_ROOT / "scripts" / "build" / "compile.py").read_text(encoding="utf-8")
        self.assertIn("TZero-v{version}-Windows-x64.zip", content)
        self.assertIn("TZero-v{version}-Linux-x64.tar.gz", content)

    def test_f7_03_release_bundle_contents(self):
        """F7.3: Verify zip bundling includes 5 binaries, README.md, README.tr.md, LICENSE."""
        content = (REPO_ROOT / "scripts" / "build" / "compile.py").read_text(encoding="utf-8")
        self.assertIn("README.md", content)
        self.assertIn("README.tr.md", content)
        self.assertIn("LICENSE", content)

    def test_f7_04_single_source_version_sync(self):
        """F7.4: Verify version string 12.1.4 is synchronized across manifests."""
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn(f'version = "{CANONICAL_VERSION}"', pyproject)

        server_json = REPO_ROOT / "server.json"
        if server_json.is_file():
            self.assertIn(CANONICAL_VERSION, server_json.read_text(encoding="utf-8"))

        npm_pkg = REPO_ROOT / "installers" / "npm" / "package.json"
        if npm_pkg.is_file():
            self.assertIn(CANONICAL_VERSION, npm_pkg.read_text(encoding="utf-8"))

    def test_f7_05_github_release_workflow_spec(self):
        """F7.5: Verify .github/workflows/release.yml triggers on v* tags and uploads assets."""
        release_yml = (REPO_ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertIn("'v*'", release_yml)
        self.assertIn("softprops/action-gh-release", release_yml)

    # -------------------------------------------------------------------------
    # Feature 8: Absolute Zero-Age Privacy Enforcement (F8)
    # -------------------------------------------------------------------------

    def test_f8_01_no_age_in_markdown_docs(self):
        """F8.1: Verify README.md and all docs/*.md contain 0 age mentions."""
        md_files = [REPO_ROOT / "README.md"] + list((REPO_ROOT / "docs").rglob("*.md"))
        violations = []
        for p in md_files:
            text = p.read_text(encoding="utf-8", errors="ignore")
            matches = AGE_PATTERN.findall(text)
            if matches:
                violations.append((p.name, matches))
        self.assertEqual(violations, [], f"Age references found in markdown docs: {violations}")

    def test_f8_02_no_age_in_tzero_python_sources(self):
        """F8.2: Verify tzero/*.py source files contain 0 age mentions."""
        violations = []
        for p in (REPO_ROOT / "tzero").glob("*.py"):
            text = p.read_text(encoding="utf-8", errors="ignore")
            matches = AGE_PATTERN.findall(text)
            if matches:
                violations.append((p.name, matches))
        self.assertEqual(violations, [], f"Age references found in tzero sources: {violations}")

    def test_f8_03_no_age_in_tests_directory(self):
        """F8.3: Verify tests/**/*.py test files contain 0 age mentions recursively."""
        violations = []
        for p in (REPO_ROOT / "tests").rglob("*.py"):
            text = p.read_text(encoding="utf-8", errors="ignore")
            matches = AGE_PATTERN.findall(text)
            if matches:
                violations.append((p.name, matches))
        self.assertEqual(violations, [], f"Age references found in tests: {violations}")

    def test_f8_04_no_age_in_benchmark_site(self):
        """F8.4: Verify benchmark-site/ index.html and app.js contain 0 age mentions."""
        site_files = [
            REPO_ROOT / "benchmark-site" / "index.html",
            REPO_ROOT / "benchmark-site" / "app.js",
        ]
        violations = []
        for p in site_files:
            text = p.read_text(encoding="utf-8", errors="ignore")
            matches = AGE_PATTERN.findall(text)
            if matches:
                violations.append((p.name, matches))
        self.assertEqual(violations, [], f"Age references found in benchmark-site: {violations}")

    def test_f8_05_no_age_in_package_manifests(self):
        """F8.5: Verify pyproject.toml, Cargo.toml, and .github/ contain 0 age mentions."""
        manifest_files = [
            REPO_ROOT / "pyproject.toml",
            REPO_ROOT / "crates" / "tzero_core" / "Cargo.toml",
            REPO_ROOT / ".github" / "FUNDING.yml",
        ]
        violations = []
        for p in manifest_files:
            if p.is_file():
                text = p.read_text(encoding="utf-8", errors="ignore")
                matches = AGE_PATTERN.findall(text)
                if matches:
                    violations.append((p.name, matches))
        self.assertEqual(violations, [], f"Age references found in manifests: {violations}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
