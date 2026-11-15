# Security Policy — T-Zero Context Architect

The T-Zero team and Siber Akademi take security and privacy with absolute seriousness.
T-Zero is engineered with an uncompromising **100% Zero-Leak** architecture, ensuring that source code, AST structures, and developer credentials never leak into untrusted external networks.

---

## Supported Versions

We provide security updates and patches for the following versions:

| Version | Supported          | Security Status |
| ------- | ------------------ | --------------- |
| 11.12.x | :white_check_mark: | Active (Current release) |
| 11.11.x | :white_check_mark: | Supported       |
| 11.10.x | :white_check_mark: | Supported       |
| < 11.0  | :x:                | End of Life     |

---

## 🔒 100% Zero-Leak Architectural Guarantees

T-Zero is intentionally designed to be **safe by construction**:

1. **Local & Offline Execution:**
   - 100% of AST parsing, type signature extraction, and token reduction runs on your local CPU.
   - Zero telemetry, zero usage tracking, zero external cloud dependencies.
2. **Built-in Shannon Entropy Secret Scrubber:**
   - Evaluates token entropy ($H \ge 4.75$) alongside high-precision regular expressions to identify API keys, private keys, JWTs, and database passwords.
   - Hardcoded secrets are scrubbed and replaced before context is emitted to LLM tools.
3. **Pre-Flight Reality-Lock & Hallucination Guard:**
   - Statically verifies all imported symbols and caller contracts against local workspace AST before code execution or write.
4. **Architectural Boundary Enforcement:**
   - Validates layered boundary rules (e.g. `tzero.rules.json`) to prevent circular dependencies and structural erosion in CI pipelines.

---

## Reporting a Vulnerability

If you discover a security vulnerability or credential leak vector in T-Zero:

1. **Do NOT open a public GitHub issue.**
2. Report the vulnerability privately via **GitHub Security Advisories**:
   [https://github.com/toprakahmetaydogmus/TZeroAlgorithm/security/advisories/new](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/security/advisories/new)
3. Alternatively, email the lead maintainer directly:
   - **Contact:** Toprak Ahmet Aydoğmuş (Lead Developer, Siber Akademi)
   - **Email:** `siberakademi@org.tr`
   - **Subject:** `[SECURITY] T-Zero Vulnerability Report`

### What to Include in Your Report:
- Detailed description of the vulnerability and attack vector
- Steps to reproduce or proof-of-concept (PoC) code
- Affected version(s) and operating system / environment
- Any potential impact on developer environments or credential exposure

### Response Timeline:
- **Initial Response:** Within 24 hours of receiving the report.
- **Triage & Assessment:** Within 48 hours.
- **Patch Release:** Security fixes are prioritized and released via patch versions within 72 hours.
- **Public Disclosure:** Coordinated disclosure only after the patch is published and users have had reasonable time to upgrade.

Thank you for helping keep T-Zero and the open-source developer ecosystem secure!
