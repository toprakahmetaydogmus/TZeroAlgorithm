# ⚡ T-Zero GitHub Action & Pre-Commit Integration Guide

Automate **100% Zero-Leak Security**, **Pre-Flight Reality-Lock (Anti-Hallucination)**, and **AST Context Pruning** in your CI/CD pipelines in seconds with **$0.00 cloud cost**.

---

## 🚀 1. GitHub Action CI Pipeline (10 Seconds)

Add a new workflow to your repository at `.github/workflows/tzero-gate.yml`:

```yaml
name: T-Zero Autonomous Review & Security Gate

on:
  pull_request:
    branches: [main, master, dev]
  push:
    branches: [main, master]

jobs:
  tzero-review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
        with:
          fetch-depth: 2 # Required for diff inspection

      - name: Run T-Zero Reality-Lock & Security Gate
        uses: toprakahmetaydogmus/TZeroAlgorithm@main
        with:
          mode: review
          audit-level: strict
```

### 🎯 What Happens on Every Pull Request:
1. **Zero-Leak Security Scan:** Deterministically audits added lines against Shannon Entropy ($H \ge 4.75$) and 50+ API key signatures (OpenAI, Anthropic, Gemini, AWS, Stripe, Groq, OpenRouter, Perplexity, NPM, etc.).
2. **Pre-Flight Reality-Lock:** Verifies that no ghost packages or hallucinated workspace symbols were introduced by AI coding tools or copy-paste.
3. **Blast Radius Computation:** Calculates downstream caller impact (0-100 score) on modified classes and functions.
4. **Step Summary Output:** Posts an automated status card directly to the GitHub Action run summary:

| Metric | Status | Policy |
| :--- | :---: | :---: |
| **Zero-Leak Security** | 🛡️ PASSED | 100% Offline / Zero-Leak |
| **Pre-Flight Reality-Lock** | 🧠 VERIFIED | Zero Hallucinated Imports |
| **AST Context Reduction** | ⚡ UP TO -95% | Token-Zero High Fidelity |

---

## 🔒 2. Pre-Commit Hook Integration

If you use the popular `pre-commit` framework in your repository, add T-Zero to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/toprakahmetaydogmus/TZeroAlgorithm
    rev: v10.6.0
    hooks:
      # Block commits with secrets, ghost packages, or hallucinations
      - id: tzero-review
      # (Optional) Full AST static smell analysis
      - id: tzero-audit
```

Run installation:
```bash
pre-commit install
```

Now, every `git commit` will automatically pass through the T-Zero Reality-Lock and Zero-Leak shield before hitting git history.

---

## 🛠 3. Local CLI Usage

Run manual review on uncommitted changes:
```bash
tzero review
```

Run manual review comparing with a target branch or commit:
```bash
tzero review origin/main
tzero review HEAD~1
```

Run live background watcher daemon while coding in Cursor / Claude / Windsurf:
```bash
tzero --watch
```

---

> Engineered with pride by **Toprak Ahmet Aydoğmuş** (15-Year-Old Solo Developer @ Siber Akademi).  
> 100% Free & Open-Source forever ($0.00 Cloud Cost). If you find T-Zero helpful, please give us a ⭐ on [GitHub](https://github.com/toprakahmetaydogmus/TZeroAlgorithm)!
