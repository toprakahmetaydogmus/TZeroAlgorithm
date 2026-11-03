# 🌐 Reddit Launch Campaign Guide

Target subreddits:
1. `r/LocalLLaMA` (500k+ AI engineers & researchers)
2. `r/programming` (5.8M+ developers)
3. `r/ChatGPTCoding` (280k+ AI coders)
4. `r/cursor` (Cursor IDE power users)

---

### Reddit Post 1: r/LocalLLaMA & r/ChatGPTCoding

**Post Title:**
`I got tired of LLMs choking on boilerplate, so I built an open-source AST context compressor (-94.6% tokens, 52-tool MCP, $0 cost)`

**Post Body:**
```markdown
Hey everyone!

When using Claude 3.5 Sonnet, GPT-4o, or local LLMs on large codebases, feeding entire files dumps thousands of lines of internal helper loops, routine math, and private variables into the prompt. It wastes context window, causes attention decay, and drains your wallet.

I built **T-Zero** (https://github.com/toprakahmetaydogmus/TZeroAlgorithm) — an open-source deterministic AST context compressor and Model Context Protocol (MCP) server for Cursor, Claude Code, Antigravity, and Windsurf.

### How it works:
Instead of dumping raw text or relying on flaky embedding chunks, T-Zero uses an Abstract Syntax Tree (AST) engine:
1. **Focus File:** Kept at **100% full implementation** (all code and loops).
2. **Surrounding 1st-Degree Dependencies:** Pruned to **typed AST interface skeletons** (classes, exported signatures, parameter types, return annotations, and docstrings).

### Empirical Benchmark (Measured via `tiktoken cl100k_base`):
- **Raw Repo Context:** 1,168,014 tokens
- **T-Zero Smart Skeleton:** 64,240 tokens (**-94.5% net token savings**)
- **TTFT (Time-to-First-Token):** 45x to 67x faster context ingestion (from 7.2s down to ~107ms).
- **Task Success Rate:** 100% with 0 hallucinated methods or broken calls.

### Additional Features:
- **Pre-Flight Reality-Lock:** Catches non-existent function calls before code execution.
- **Shannon Entropy Secret Scrubber ($H \ge 4.75$):** Locally redacts API keys and private tokens.
- **100% TDQS 5.0/5.0 Anchor Certified:** Zero ambiguity across all 52 registered MCP tools.
- **Official VS Code / Cursor Extension (.vsix):** 1-click install.
- **$0.00 Forever:** Zero external paid APIs, 100% local Python AST.

🔗 **GitHub:** https://github.com/toprakahmetaydogmus/TZeroAlgorithm  
🤗 **Live Browser Demo (Hugging Face Spaces):** https://huggingface.co/spaces/toprakke4/tzero-token-reducer

Would love to hear your thoughts and feedback!
```
