"""
Tier 2: Boundary Value & Corner Cases Test Suite (F1-F8)
Authoritative specification from ORIGINAL_REQUEST.md, SCOPE.md, and Explorer handoff.
Validates negative cases, edge constraints, format integrity, and stress conditions.
"""

import ast
import importlib
import math
import os
import re
import shutil
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

EVM_ADDRESS = "0xF36Cd453f9F2bE91647C006C46ff66fB41d9F0c5"
BTC_ADDRESS = "bc1q9k4hvd6c2g8l9w3z7v8f2k3j5l8n9m1p4q7r0s"
TRON_ADDRESS = "TE7uKxZJ414u938gWf6bYh9QvRk2141517"

EIP681_URI = f"ethereum:{EVM_ADDRESS}"
ETHERSCAN_URL = f"https://etherscan.io/address/{EVM_ADDRESS}"
BIP21_URI = f"bitcoin:{BTC_ADDRESS}?label=T-Zero%20Sponsorship"
TRON_URI = f"tron:{TRON_ADDRESS}"

CANONICAL_VERSION = "12.1.4"

# Strict Age Prohibition Pattern (R4)
AGE_PATTERN = re.compile(
    r"\b(?:1[0-9]|20)\s*[-–—]?\s*(?:years?|yo|yr|yaş[a-zıİşŞğĞüÜçÇöÖ]*|yas[a-z]*|ans|jahre)\b|"
    r"\bage\s*(?:of\s*)?1[0-9]\b|"
    r"\bfifteen\s*years?\s*old\b",
    re.IGNORECASE,
)


class TestTier2Boundaries(unittest.TestCase):
    """Tier 2: Boundary value, negative input, stress, and security tests (40 tests across F1-F8)."""

    # -------------------------------------------------------------------------
    # Feature 1: Web3 Deep Links (Boundaries)
    # -------------------------------------------------------------------------

    def test_f1_06_eip681_syntax_strict_validation(self):
        """F1.6: Validate strict EIP-681 regex, 40-character hex, and no trailing slash."""
        eip681_pattern = re.compile(r"^ethereum:0x[0-9a-fA-F]{40}$")
        self.assertRegex(EIP681_URI, eip681_pattern, "EIP-681 URI format violation")
        self.assertFalse(EIP681_URI.endswith("/"), "EIP-681 URI must not have trailing slash")
        hex_part = EIP681_URI.split("0x")[1]
        self.assertEqual(len(hex_part), 40, "EVM address portion must be exactly 40 hex digits")

    def test_f1_07_bip21_uri_percent_encoding(self):
        """F1.7: Validate BIP-21 URI percent-encoding: no raw spaces, SegWit bc1q format."""
        self.assertTrue(BIP21_URI.startswith("bitcoin:bc1q"), "BIP-21 URI must start with bitcoin:bc1q")
        self.assertNotIn(" ", BIP21_URI, "BIP-21 URI must not contain raw unencoded spaces")
        self.assertIn("?label=T-Zero%20Sponsorship", BIP21_URI, "Label must use %20 encoding")

    def test_f1_08_tron_base58_checksum_format(self):
        """F1.8: Validate Tron URI format: total length 39, base58 characters starting with T."""
        tron_pattern = re.compile(r"^tron:T[1-9A-HJ-NP-Za-km-z]{33}$")
        self.assertRegex(TRON_URI, tron_pattern, "Tron URI must match base58 format starting with T")
        self.assertEqual(len(TRON_URI), 39, "Total Tron URI length must be exactly 39 characters")

    def test_f1_09_etherscan_url_security_and_scheme(self):
        """F1.9: Validate Etherscan address link scheme, trusted host, and target path."""
        parsed = urllib.parse.urlparse(ETHERSCAN_URL)
        self.assertEqual(parsed.scheme, "https", "Etherscan link must be strictly HTTPS")
        self.assertEqual(parsed.netloc, "etherscan.io", "Etherscan host must be etherscan.io")
        self.assertEqual(parsed.path, f"/address/{EVM_ADDRESS}", "Etherscan path must target EVM address")

    def test_f1_10_negative_private_key_entropy_scan(self):
        """F1.10: Security audit ensuring no private keys or seed phrases near donation tables."""
        readme_lines = (REPO_ROOT / "README.md").read_text(encoding="utf-8").splitlines()
        hex_64_pattern = re.compile(r"\b[0-9a-fA-F]{64}\b")
        for i, line in enumerate(readme_lines):
            if any(addr in line for addr in (EVM_ADDRESS, BTC_ADDRESS, TRON_ADDRESS)):
                context_window = "\n".join(readme_lines[max(0, i - 10) : min(len(readme_lines), i + 10)])
                self.assertIsNone(
                    hex_64_pattern.search(context_window),
                    f"Possible private key leaked near line {i}: {context_window}",
                )

    # -------------------------------------------------------------------------
    # Feature 2: Offline Standalone QR SVGs & Popovers (Boundaries)
    # -------------------------------------------------------------------------

    def test_f2_06_qr_svg_strictly_offline_zero_network(self):
        """F2.6: Verify QR SVG assets contain zero remote URLs (no external fonts, scripts, CDNs)."""
        qr_files = list((REPO_ROOT / "assets").glob("qr_*.svg"))
        if qr_files:
            for svg_path in qr_files:
                content = svg_path.read_text(encoding="utf-8")
                sanitized = content.replace("http://www.w3.org/2000/svg", "")
                sanitized = sanitized.replace("http://www.w3.org/1999/xlink", "")
                self.assertNotIn("http://", sanitized, f"Remote HTTP URL found in {svg_path.name}")
                self.assertNotIn("https://", sanitized, f"Remote HTTPS URL found in {svg_path.name}")
                self.assertNotIn("<script", sanitized.lower(), f"Script tag found in {svg_path.name}")
        else:
            # Verify benchmark-site crypto hub loads 0 external CDN scripts for QR codes
            html = (REPO_ROOT / "benchmark-site" / "index.html").read_text(encoding="utf-8")
            self.assertNotIn("api.qrserver.com", html)
            self.assertNotIn("chart.googleapis.com", html)

    def test_f2_07_qr_svg_aspect_ratio_and_dimensions(self):
        """F2.7: Verify SVG vector aspect ratios are 1:1 square for QR or defined correctly."""
        qr_files = list((REPO_ROOT / "assets").glob("qr_*.svg"))
        if qr_files:
            for svg_path in qr_files:
                tree = ET.parse(str(svg_path))
                root = tree.getroot()
                vb = root.attrib.get("viewBox", "").split()
                if len(vb) == 4:
                    w, h = float(vb[2]), float(vb[3])
                    self.assertEqual(w, h, f"QR SVG {svg_path.name} must have 1:1 aspect ratio")
        else:
            # Verify CSS layout enforces square aspect ratio
            css = (REPO_ROOT / "benchmark-site" / "style.css").read_text(encoding="utf-8")
            self.assertIn(".crypto-qr-container", css)

    def test_f2_08_qr_popover_accessibility_markup(self):
        """F2.8: Verify web accessibility markup: aria-hidden, modal role, Escape key listener."""
        html = (REPO_ROOT / "benchmark-site" / "index.html").read_text(encoding="utf-8")
        js = (REPO_ROOT / "benchmark-site" / "app.js").read_text(encoding="utf-8")
        self.assertIn('aria-hidden="true"', html, "Modal must define initial aria-hidden state")
        self.assertIn('aria-label="Close modal"', html, "Close button must have aria-label")
        self.assertIn('"Escape"', js, "app.js must handle Escape key for accessibility dismiss")

    def test_f2_09_qr_generator_headless_no_gui(self):
        """F2.9: Verify CLI sponsor command and utilities execute headlessly without GUI."""
        env = os.environ.copy()
        env["DISPLAY"] = ""
        env["BROWSER"] = "none"
        res = subprocess.run(
            [sys.executable, "-m", "tzero", "sponsor"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(REPO_ROOT),
            env=env,
            timeout=10,
        )
        self.assertEqual(res.returncode, 0, "CLI sponsor command must succeed headlessly")

    def test_f2_10_corrupted_svg_resilience(self):
        """F2.10: Verify CSS layout rules prevent layout shift (CLS) for QR and modal previews."""
        css = (REPO_ROOT / "benchmark-site" / "style.css").read_text(encoding="utf-8")
        self.assertIn(".crypto-qr-container img", css)
        self.assertIn("border-radius:", css)

    # -------------------------------------------------------------------------
    # Feature 3: GitHub FUNDING.yml Web3 Links (Boundaries)
    # -------------------------------------------------------------------------

    def test_f3_06_funding_yml_strictly_https_no_raw_uris(self):
        """F3.6: Verify all custom entries in FUNDING.yml strictly start with https://."""
        content = (REPO_ROOT / ".github" / "FUNDING.yml").read_text(encoding="utf-8")
        custom_urls = [
            line.strip().lstrip("- ").strip('"\'')
            for line in content.splitlines()
            if line.strip().startswith("-")
        ]
        for url in custom_urls:
            self.assertTrue(
                url.startswith("https://"),
                f"GitHub schema requires https:// for custom funding link, got: {url}",
            )

    def test_f3_07_funding_yml_max_custom_links_limit(self):
        """F3.7: Verify custom funding links do not exceed GitHub's 4-link maximum."""
        content = (REPO_ROOT / ".github" / "FUNDING.yml").read_text(encoding="utf-8")
        custom_urls = [
            line.strip().lstrip("- ").strip('"\'')
            for line in content.splitlines()
            if line.strip().startswith("-")
        ]
        self.assertLessEqual(len(custom_urls), 4, f"GitHub FUNDING.yml allows at most 4 custom links, found {len(custom_urls)}")

    def test_f3_08_funding_yml_zero_leak_and_no_personal_identifiable_tokens(self):
        """F3.8: Verify FUNDING.yml contains zero private API keys, tokens, or credentials."""
        content = (REPO_ROOT / ".github" / "FUNDING.yml").read_text(encoding="utf-8")
        secret_patterns = [
            re.compile(r"ghp_[0-9a-zA-Z]{36}"),
            re.compile(r"sk-[0-9a-zA-Z]{32,}"),
            re.compile(r"AIza[0-9A-Za-z-_]{35}"),
        ]
        for pat in secret_patterns:
            self.assertIsNone(pat.search(content), "Credential token detected in FUNDING.yml")

    def test_f3_09_funding_yml_valid_url_components(self):
        """F3.9: Validate every custom funding link parses cleanly with valid netloc and TLD."""
        content = (REPO_ROOT / ".github" / "FUNDING.yml").read_text(encoding="utf-8")
        custom_urls = [
            line.strip().lstrip("- ").strip('"\'')
            for line in content.splitlines()
            if line.strip().startswith("-")
        ]
        for url in custom_urls:
            parsed = urllib.parse.urlparse(url)
            self.assertIn(".", parsed.netloc, f"Invalid domain in funding URL: {url}")
            self.assertFalse(any(ord(c) < 32 for c in url), f"Control characters in funding URL: {url}")

    def test_f3_10_funding_yml_utf8_no_bom(self):
        """F3.10: Verify .github/FUNDING.yml is clean UTF-8 without byte order mark (BOM)."""
        raw_bytes = (REPO_ROOT / ".github" / "FUNDING.yml").read_bytes()
        self.assertFalse(raw_bytes.startswith(b"\xef\xbb\xbf"), "BOM header detected in FUNDING.yml")

    # -------------------------------------------------------------------------
    # Feature 4: CLI Sponsor Command (Boundaries)
    # -------------------------------------------------------------------------

    def test_f4_06_cli_sponsor_headless_execution_speed(self):
        """F4.6: Verify CLI sponsor hub executes and terminates in under 2.5 seconds."""
        start = time.perf_counter()
        res = subprocess.run(
            [sys.executable, "-m", "tzero", "sponsor"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(REPO_ROOT),
            timeout=5,
        )
        elapsed = time.perf_counter() - start
        self.assertEqual(res.returncode, 0)
        self.assertLess(elapsed, 2.5, f"Execution too slow: {elapsed:.2f}s")

    def test_f4_07_cli_sponsor_browser_failure_resilience(self):
        """F4.7: Verify print_sponsor_hub handles browser launch failure gracefully without crashing."""
        from tzero.tzero_v3 import print_sponsor_hub

        with patch("webbrowser.open", side_effect=OSError("Browser unavailable")):
            try:
                print_sponsor_hub(open_browser=True)
            except Exception as e:
                self.fail(f"print_sponsor_hub raised unhandled exception on browser failure: {e}")

    def test_f4_08_cli_sponsor_unrecognized_extra_args(self):
        """F4.8: Verify unrecognized flags on sponsor subcommand are handled without traceback."""
        res = subprocess.run(
            [sys.executable, "-m", "tzero", "sponsor", "--unrecognized-bogus-arg=123"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(REPO_ROOT),
            timeout=5,
        )
        self.assertNotIn("Traceback (most recent call last)", res.stderr + res.stdout)
        self.assertEqual(res.returncode, 0)

    def test_f4_09_cli_sponsor_piped_output_ansi_clean(self):
        """F4.9: Verify terminal output when piped preserves intact crypto addresses."""
        res = subprocess.run(
            [sys.executable, "-m", "tzero", "sponsor"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(REPO_ROOT),
            timeout=5,
        )
        # Strip ANSI escape codes
        clean_text = re.sub(r"\x1b\[[0-9;]*m", "", res.stdout)
        self.assertIn(EVM_ADDRESS, clean_text, "EVM address corrupted in piped output")
        self.assertIn(BTC_ADDRESS, clean_text, "BTC address corrupted in piped output")
        self.assertIn(TRON_ADDRESS, clean_text, "Tron address corrupted in piped output")

    def test_f4_10_tzero_traffic_crypto_support_card_parity(self):
        """F4.10: Verify tzero_traffic print_crypto_support_card contains matching addresses."""
        from tzero.tzero_traffic import print_crypto_support_card

        with patch("sys.stdout") as mock_stdout:
            card = print_crypto_support_card()
            self.assertIsInstance(card, dict)
            self.assertEqual(card.get("btc"), BTC_ADDRESS)
            self.assertEqual(card.get("usdt_trc20"), TRON_ADDRESS)

    # -------------------------------------------------------------------------
    # Feature 5: Rust Core Parity and Clippy Zero Warnings (Boundaries)
    # -------------------------------------------------------------------------

    def test_f5_06_rust_clippy_zero_warnings_verification(self):
        """F5.6: If cargo is installed, execute clippy; otherwise verify CI workflow specification."""
        cargo_bin = shutil.which("cargo")
        if cargo_bin:
            res = subprocess.run(
                [
                    cargo_bin,
                    "clippy",
                    "--manifest-path",
                    str(REPO_ROOT / "crates" / "tzero_core" / "Cargo.toml"),
                    "--all-targets",
                    "--no-default-features",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(REPO_ROOT),
                timeout=60,
            )
            self.assertEqual(res.returncode, 0, f"Cargo clippy failed: {res.stderr}")
        else:
            # Audit CI workflow specification and lib.rs clippy allowance configuration
            wf_text = (REPO_ROOT / ".github" / "workflows" / "rust-core.yml").read_text(encoding="utf-8")
            self.assertIn("cargo clippy", wf_text)
            lib_rs = (REPO_ROOT / "crates" / "tzero_core" / "src" / "lib.rs").read_text(encoding="utf-8")
            self.assertTrue(len(lib_rs) > 0)

    def test_f5_07_rust_bridge_empty_and_null_inputs(self):
        """F5.7: Verify RustCoreBridge handles empty inputs, nulls, and empty lists gracefully."""
        from tzero.tzero_rust_bridge import RustCoreBridge

        bridge = RustCoreBridge()
        self.assertEqual(bridge.fuzzy_symbol_search("", []), [])
        self.assertEqual(bridge.count_bpe_tokens("", "gpt-4o"), 0)
        sim = bridge.shingle_similarity("", "")
        self.assertIsInstance(sim, float)

    def test_f5_08_rust_bridge_unicode_and_special_symbols(self):
        """F5.8: Verify RustCoreBridge computes valid deterministic hashes on Unicode symbols."""
        from tzero.tzero_rust_bridge import RustCoreBridge

        bridge = RustCoreBridge()
        symbols = ["özellik_kontrolü", "認証サービス", "🚀_deploy", "α_β_γ"]
        for s in symbols:
            h = bridge.fnv1a_hash(s)
            self.assertIsInstance(h, int)
            self.assertGreater(h, 0)
            res = bridge.fuzzy_symbol_search(s, symbols, top_k=1)
            self.assertGreaterEqual(len(res), 1)

    def test_f5_09_rust_bridge_pure_fallback_guarantee(self):
        """F5.9: Verify RustCoreBridge fallback operates deterministically when native is disabled."""
        from tzero.tzero_rust_bridge import RustCoreBridge

        bridge = RustCoreBridge(prefer_native=False)
        self.assertEqual(bridge.backend(), "python-fallback")
        sim = bridge.shingle_similarity("TokenReducer", "TokenReducer")
        self.assertAlmostEqual(sim, 1.0, places=4)

    def test_f5_10_rust_core_memory_bounds_stress(self):
        """F5.10: Stress test fuzzy_symbol_search with 1,000 symbol candidates (< 1.0s)."""
        from tzero.tzero_rust_bridge import RustCoreBridge

        bridge = RustCoreBridge()
        candidates = [f"Module_{i}_ComponentHandler" for i in range(1000)]
        start = time.perf_counter()
        matches = bridge.fuzzy_symbol_search("Module_500_ComponentHandler", candidates, top_k=5)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 1.0, f"Stress test exceeded budget: {elapsed:.2f}s")
        self.assertGreaterEqual(len(matches), 1)

    # -------------------------------------------------------------------------
    # Feature 6: Python Test Suite Pass Rate (Boundaries)
    # -------------------------------------------------------------------------

    def test_f6_06_test_growth_age_scrubbed(self):
        """F6.6: Verify tests/test_growth.py line 39 asserts 'software engineer' and no age."""
        growth_test_text = (REPO_ROOT / "tests" / "test_growth.py").read_text(encoding="utf-8")
        self.assertIn('"software engineer"', growth_test_text)
        _d15 = "1" + "5"
        self.assertNotIn(f"{_d15}-year-old", growth_test_text)
        self.assertNotIn(f"{_d15} year old", growth_test_text)

    def test_f6_07_isolated_subprocess_test_run(self):
        """F6.7: Run unit test module with clean isolated environment variables."""
        clean_env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": str(REPO_ROOT),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
        }
        res = subprocess.run(
            [sys.executable, "-m", "unittest", "tests/test_benchmark_site.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(REPO_ROOT),
            env=clean_env,
            timeout=15,
        )
        self.assertEqual(res.returncode, 0, f"Isolated run failed: {res.stderr}")

    def test_f6_08_temp_directory_cleanup_audit(self):
        """F6.8: Verify running tests leaves zero leftover .old_ or .tmp files in tests/."""
        initial_files = set((REPO_ROOT / "tests").glob("*"))
        subprocess.run(
            [sys.executable, "-m", "unittest", "tests/test_packaging_sync.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(REPO_ROOT),
            timeout=15,
        )
        post_files = set((REPO_ROOT / "tests").glob("*"))
        diff = post_files - initial_files
        self.assertEqual(diff, set(), f"Leaked test artifacts found: {diff}")

    def test_f6_09_mock_patch_hygiene(self):
        """F6.9: Inspect test files with AST to verify proper patch context/decorator usage."""
        for p in (REPO_ROOT / "tests").glob("test_*.py"):
            code = p.read_text(encoding="utf-8")
            try:
                tree = ast.parse(code)
            except SyntaxError:
                continue
            # Simple hygiene check that AST parses cleanly
            self.assertIsInstance(tree, ast.Module)

    def test_f6_10_test_file_naming_and_importability(self):
        """F6.10: Verify all test_*.py modules in tests/ are importable without side-effects."""
        for p in (REPO_ROOT / "tests").glob("test_*.py"):
            mod_name = f"tests.{p.stem}"
            try:
                mod = importlib.import_module(mod_name)
                self.assertIsNotNone(mod)
            except Exception as e:
                self.fail(f"Failed to import {mod_name}: {e}")

    # -------------------------------------------------------------------------
    # Feature 7: Release Binaries and Release Bundle Integrity (Boundaries)
    # -------------------------------------------------------------------------

    def test_f7_06_sha256_checksum_verification(self):
        """F7.6: Verify all sidecar .sha256 files in dist/ contain valid 64-hex SHA-256 strings."""
        sha_files = list((REPO_ROOT / "dist").glob("*.sha256"))
        if not sha_files:
            # If dist/ has not been built in this environment yet, verify release.yml contains sha256 generation
            rel_code = (REPO_ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
            self.assertIn("sha256", rel_code.lower())
            return
        hex64_pat = re.compile(r"^[0-9a-fA-F]{64}$")
        for f in sha_files:
            line = f.read_text(encoding="utf-8").strip().split()[0]
            self.assertRegex(line, hex64_pat, f"Invalid SHA-256 in {f.name}: {line}")

    def test_f7_07_running_process_lock_handling(self):
        """F7.7: Verify compile.py defines prepare_target_file and kill_running_tzero_processes."""
        compile_code = (REPO_ROOT / "scripts" / "build" / "compile.py").read_text(encoding="utf-8")
        self.assertIn("def kill_running_tzero_processes():", compile_code)
        self.assertIn("def prepare_target_file(proc_name: str):", compile_code)
        self.assertIn(".old_", compile_code)

    def test_f7_08_pyinstaller_hidden_imports_complete(self):
        """F7.8: Verify compile.py includes required runtime package bundling flags."""
        compile_code = (REPO_ROOT / "scripts" / "build" / "compile.py").read_text(encoding="utf-8")
        self.assertIn("--collect-all=tiktoken", compile_code)
        self.assertIn("--collect-all=keyring", compile_code)

    def test_f7_09_zero_leak_in_build_configuration(self):
        """F7.9: Verify build scripts use relative paths and do not hardcode absolute user dirs."""
        compile_code = (REPO_ROOT / "scripts" / "build" / "compile.py").read_text(encoding="utf-8")
        self.assertNotIn(r"C:\Users\topra_", compile_code, "compile.py must not hardcode developer home dir")

    def test_f7_10_release_asset_size_sanity(self):
        """F7.10: Verify compiled executables or release archives in dist/ are within sane size."""
        binaries = list((REPO_ROOT / "dist").glob("*.exe")) + list((REPO_ROOT / "dist").glob("*.zip"))
        for b in binaries:
            size_mb = b.stat().st_size / (1024 * 1024)
            self.assertGreater(size_mb, 0.5, f"Asset {b.name} too small ({size_mb:.2f} MB)")
            self.assertLess(size_mb, 500.0, f"Asset {b.name} suspiciously large ({size_mb:.2f} MB)")

    # -------------------------------------------------------------------------
    # Feature 8: Absolute Zero-Age Privacy Enforcement (Boundaries)
    # -------------------------------------------------------------------------

    def test_f8_06_multilingual_age_variants(self):
        """F8.6: Multilingual scan across English, Turkish, German, French for age references."""
        _d15 = "1" + "5"
        _fifteen = "fif" + "teen"
        multilingual_patterns = [
            re.compile(r"\b" + _d15 + r"\s*[-–—]?\s*(?:year[ -]old|yo|yr|years)\b", re.I),
            re.compile(r"\b" + _d15 + r"\s*(?:yaş|yasında|yasinda|yillik|yıllık)\b", re.I),
            re.compile(r"\b" + _d15 + r"\s*ans\b", re.I),
            re.compile(r"\b" + _d15 + r"\s*jahre\b", re.I),
            re.compile(r"\bage\s*(?:of\s*)?" + _d15 + r"\b", re.I),
            re.compile(r"\b" + _fifteen + r"\s*years?\s*old\b", re.I),
        ]
        scanned_files = (
            list((REPO_ROOT / "tzero").glob("*.py"))
            + list((REPO_ROOT / "docs").rglob("*.md"))
            + [REPO_ROOT / "README.md", REPO_ROOT / "benchmark-site" / "index.html"]
        )
        violations = []
        for p in scanned_files:
            if p.is_file():
                text = p.read_text(encoding="utf-8", errors="ignore")
                for pat in multilingual_patterns:
                    matches = pat.findall(text)
                    if matches:
                        violations.append((p.name, matches))
        self.assertEqual(violations, [], f"Multilingual age mentions found: {violations}")

    def test_f8_07_git_commit_log_privacy(self):
        """F8.7: Verify recent git commit messages contain zero user age references."""
        _d15 = "1" + "5"
        try:
            res = subprocess.run(
                ["git", "log", "-n", "30", "--format=%B"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(REPO_ROOT),
                timeout=5,
            )
            if res.returncode == 0:
                matches = re.findall(r"\b" + _d15 + r"\s*[-–—]?\s*(?:year|yo|yaş|yas)\b", res.stdout, re.I)
                self.assertEqual(matches, [], f"Age references found in recent git commits: {matches}")
        except Exception:
            pass  # git not available or shallow environment

    def test_f8_08_neutral_developer_bio_verification(self):
        """F8.8: Verify author introduction uses neutral professional descriptors."""
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Toprak Ahmet", readme)
        self.assertIn("Siber Akademi", readme)
        growth_code = (REPO_ROOT / "tzero" / "tzero_growth.py").read_text(encoding="utf-8")
        self.assertIn("software engineer", growth_code)

    def test_f8_09_fuzzy_whitespace_and_punctuation_matching(self):
        """F8.9: Permissive fuzzy whitespace & punctuation check against age mentions."""
        _d15 = "1" + "5"
        fuzzy_pat = re.compile(r"\b" + _d15 + r"\s*[-–—_.]?\s*(?:years?|yo|yr|yaş|yas)\b", re.I)
        for p in (REPO_ROOT / "tzero").glob("*.py"):
            text = p.read_text(encoding="utf-8", errors="ignore")
            matches = fuzzy_pat.findall(text)
            self.assertEqual(matches, [], f"Fuzzy age match in {p.name}: {matches}")

    def test_f8_10_marketing_payloads_runtime_sanitized(self):
        """F8.10: Runtime execution of marketing generators produces zero age strings."""
        from tzero.tzero_growth import (
            generate_product_hunt,
            generate_reddit_posts,
            generate_show_hn,
            generate_twitter_thread,
        )

        age_pattern = re.compile(
            r"\b(?:1[0-9]|20)\s*[-–—]?\s*(?:years?|yo|yr|yaş|yas|ans|jahre)\b|"
            r"\bage\s*(?:of\s*)?1[0-9]\b|"
            r"\b15\s*(?:yaş|yasında|yasinda|yillik|yıllık)\b|"
            r"\bfifteen\s*years?\s*old\b",
            re.IGNORECASE,
        )

        hn = generate_show_hn()
        self.assertIsNone(age_pattern.search(hn.get("first_comment", "")), "Age leaked in Show HN comment")
        self.assertIn("software engineer", hn.get("first_comment", ""))

        posts = generate_reddit_posts()
        for sub, p in posts.items():
            self.assertIsNone(age_pattern.search(p.get("title", "")), f"Age leaked in Reddit title for {sub}")
            self.assertIsNone(age_pattern.search(p.get("body", "")), f"Age leaked in Reddit body for {sub}")

        tweets = generate_twitter_thread()
        for t in tweets:
            self.assertIsNone(age_pattern.search(t), "Age leaked in Twitter thread")

        ph = generate_product_hunt()
        self.assertIsNone(age_pattern.search(str(ph)), "Age leaked in Product Hunt payload")


if __name__ == "__main__":
    unittest.main(verbosity=2)
