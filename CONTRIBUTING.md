# Contributing to T-Zero

Thank you for your interest in contributing to **T-Zero**! We welcome community contributions, bug reports, and performance optimizations from engineers worldwide.

---

## 🛠 Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/toprakahmetaydogmus/TZeroAlgorithm.git
   cd TZeroAlgorithm
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies and editable package:**
   ```bash
   pip install -e ".[test,build]"
   ```

---

## 🧪 Verification Pipeline Before Submitting a PR

Before opening a pull request, ensure all verification gates pass locally:

1. **Syntax Check:**
   ```bash
   python -m py_compile $(git diff --name-only HEAD | grep '\.py$')
   ```

2. **Run Zero-Leak Secret Audit:**
   ```bash
   python tests/audit_secrets.py
   # Must return: Total secret audit findings: 0
   ```

3. **Run Unit Tests:**
   ```bash
   python -m unittest discover tests -v
   ```

4. **Run Empirical Task Benchmark:**
   ```bash
   python tzero_task_benchmark.py
   ```

---

## 📐 Code Style & Architecture Guidelines

- **Determinism First:** All AST parsing, BM25 searching, and token reduction must run 100% locally with zero external network telemetry.
- **Inward Dependencies:** Core modules (`tzero_packer`, `tzero_guard`) must not depend on outer presentation layers (`tzero_tui`, `tzero_gui`).
- **No Plaintext Secrets:** Never commit API keys, connection URIs, or high-entropy tokens.
- **Air-Gapped Compliance:** Respect `TZERO_NO_AUTO_INSTALL=1` across all scripts.

---

## 💬 Community & Discussions

- **GitHub Issues:** [Bug Reports & Feature Requests](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/issues)
- **Hugging Face Space:** [Interactive Web Demo](https://huggingface.co/spaces/toprakke4/tzero-token-reducer)
- **Maintainer:** Toprak Ahmet Aydoğmuş (`siberakademi@org.tr`)
