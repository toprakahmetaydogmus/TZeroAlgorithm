# 📢 Hacker News Show HN Launch

**Submission Title:**
> Show HN: T-Zero – Local AST context pruning for LLMs with 88-95% token reduction

**Target URL:**
`https://github.com/toprakahmetaydogmus/TZeroAlgorithm`

**First Comment (by Author):**
```markdown
Hi HN! I'm Toprak (Toprak Ahmet Aydoğmuş), a 15-year-old software engineer from Turkey. I built T-Zero to solve a fundamental efficiency problem in AI-assisted software engineering: prompt context bloat.

### The Problem:
When developers feed large repositories into Cursor, Claude Desktop, or Claude Code, they either:
1. Rely on vector embeddings (RAG), which frequently misses cross-file caller/callee contracts and exact type signatures, or
2. Dump entire source files into the context window, burning hundreds of thousands of tokens, triggering rate limits, and degrading model attention ("lost in the middle").

### The AST Pruning Approach:
T-Zero parses multi-language source trees into Abstract Syntax Trees (AST) and deterministically extracts interface contracts (class hierarchies, method signatures, argument types, return types, docstrings, imports) while pruning execution bodies.

On our benchmark repository of 481 files (~86,000 lines of code):
- Raw Codebase: 10,998,573 tokens ($32.99 per single Claude 3.5 Sonnet context fill)
- T-Zero 4-Tier AST Tree: 1,319,828 tokens (-88.0% reduction)
- Focus Skeleton (T-3): -94.6% reduction
- Processing Latency: <400ms locally

### Security & Privacy:
- **100% Zero-Leak:** Calculates in-memory Shannon entropy (H >= 4.75) alongside regex patterns to detect and redact API keys, JWTs, and private keys locally before any context is emitted.
- **Zero Cloud Telemetry:** Operates 100% offline via local stdio MCP protocol.

The codebase is open source under MIT: https://github.com/toprakahmetaydogmus/TZeroAlgorithm
Web Playground: https://tzero-indol.vercel.app

I would love to hear thoughts, critique, and feedback on our AST pruning heuristics and MCP server architecture!

```
