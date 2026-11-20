# T-Zero: Local-first AST codebase context pruner for local models (Ollama, LM Studio, Qwen 2.5 Coder, DeepSeek) [Disclosure: Project Author]

**Affiliation Disclosure:** I am the author of T-Zero, an open-source project maintained at Siber Akademi. The software is 100% free under the MIT license with no paid tier; local MCP mode does not require telemetry or external APIs.

---

### Why AST Pruning Matters for Local LLMs
When running local coding models (Qwen 2.5 Coder 7B/14B/32B, DeepSeek-Coder, Llama 3.1) on consumer hardware (e.g., RTX 3060/4060/4090):
- **VRAM and context limits:** Even with models supporting 32K or 128K context, processing large context windows in llama.cpp / vLLM causes massive KV cache consumption and noticeable prompt processing latency.
- **Attention degradation:** Dumping entire 100+ line execution bodies into the prompt forces the local model's attention mechanism to sift through implementation details rather than architectural contracts.

### How T-Zero Solves This
**T-Zero** (v11.15.5) parses your multi-file codebase into an AST locally and extracts the exact architectural skeleton:
1. **Signature Preservation:** Retains class definitions, inheritance chains, typed function signatures, argument defaults, and docstrings.
2. **Body Pruning:** Replaces method execution blocks with `...`, reducing prompt footprint by 85% to 95%.
3. **Graph-Theory PageRank:** When a strict token budget (e.g. 8K tokens) is provided, T-Zero ranks modules by in-degree/out-degree centrality so core interfaces are prioritized over leaf utilities.
4. **Local BM25 Hybrid Search:** Instant symbol search and call-chain tracing without running a separate vector database or local embedding model.
5. **Shannon Entropy Zero-Leak:** Scans tokens in memory to prevent accidental exposure of local `.env` keys or tokens.

### Example Benchmark Metrics:
- **Tested Project:** 465 files, ~89,000 LOC
- **Raw token count:** 10,910,525 tokens
- **T-Zero AST Tree:** 1,309,263 tokens (-88.0% reduction)
- **Focused Skeleton Mode:** up to -94.6% reduction
- **Measurement note:** Timing depends on repository size and selected operation; reproduce it with the included benchmark command

### Limitations & Trade-Offs (Being Honest):
- AST pruning is designed for **architectural understanding, cross-file navigation, type checking, and interface generation**.
- If the model needs to edit the internal implementation of a specific function, you should pass that individual file in full (Tier-3 mode), while keeping all upstream/downstream dependencies skeletonized.

### Quick Start:
```bash
# Via pip
pip install tzero-mcp

# Generate compact AST context tree for local prompt:
tzero --tree . --out tree.txt

# Or run as local stdio MCP server for Ollama / LM Studio / Cursor:
tzero-mcp --stdio
```

- GitHub: https://github.com/toprakahmetaydogmus/TZeroAlgorithm
- Live Benchmark: https://tzero-indol.vercel.app
- WinGet: `winget install SiberAkademi.TZero`

Looking forward to hearing feedback from the local model community on how this performs on your local coding setups!

