# 📢 Ready-To-Post Reddit Launch Materials

## Subreddit: `r/Cursor`

**Title:**
> I built an open-source MCP server that cuts Cursor context tokens by 85-95% using AST pruning (100% local, no API keys, $0)

**Body:**
```markdown
Hey Cursor developers!

Like many of you, I kept hitting Cursor Composer context degradation and rate limits on medium-to-large repositories (100+ files). When you ingest an entire project, 90% of the token payload consists of function execution bodies that the LLM does not need to understand your architecture.

To solve this, I spent the last several months engineering **T-Zero** (v11.11.0) — an open-source Model Context Protocol (MCP) server that deterministically prunes multi-language codebases down to their exact AST interfaces, type annotations, and docstrings before feeding them to Cursor.

### 📊 Real Benchmark on 481-File Repository:
- **Raw Codebase Context:** 10,998,573 tokens (causes instant truncation / extreme lag)
- **T-Zero 4-Tier AST Tree:** 1,319,828 tokens (**-88.0% token reduction**)
- **Focus File Skeleton (T-3):** **-94.6% token reduction**
- **AST Visitor Speed:** <400ms (100% offline via local Python AST parser)
- **Unit & E2E Tests:** 537 automated tests passing with 0 errors

### 🤖 New in v11.11.0 — AI Godfather Auto-Corrector:
- Catches AI coding hallucinations before code is committed.
- Statically validates imported symbols against your project's AST and auto-heals misspelled or imaginary functions.
- Injects missing stdlib modules and typing imports automatically.

### ⚡ Add to Cursor in 30 Seconds:
Add this to your Cursor MCP settings (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "tzero": {
      "command": "python",
      "args": ["-m", "tzero.tzero_mcp"]
    }
  }
}
```
*(Or install via pip: `pip install tzero-mcp` or npm: `npx tzero-mcp`)*

### 🔒 100% Zero-Leak Security & Privacy:
- Zero external LLM calls or cloud telemetry.
- Built-in Shannon Entropy scanner (H >= 4.75) detects and redacts hardcoded API keys and credentials locally.

I'm 15 years old and building this as a solo open-source engineer at Siber Akademi. Everything is 100% free under MIT.

If this saves your Cursor context budget, **I'd genuinely appreciate a star on GitHub ⭐** — we are on the road to our first 100 stars!

👉 **GitHub:** https://github.com/toprakahmetaydogmus/TZeroAlgorithm  
👉 **Live Benchmark:** https://tzero-indol.vercel.app  
👉 **PyPI:** https://pypi.org/project/tzero-mcp/  

```
---

## Subreddit: `r/ClaudeAI`

**Title:**
> Stop hitting Claude Desktop & Claude Code 200K token limits: Open-source local AST context pruning (-88% to -95%)

**Body:**
```markdown
If you use Claude Desktop or Claude Code with complex multi-module codebases, you know how fast the 200K token window fills up. Once context fills up, Claude begins suffering from "lost-in-the-middle" attention degradation or hits expensive per-prompt costs.

**T-Zero** (v11.11.0) is a 100% local, offline MCP server that parses your codebase into an AST and strips implementation bodies while keeping 100% of the type signatures, classes, docstrings, and imports across 12+ programming languages.

### 💡 Why AST Beats Naive File Dumping:
When Claude writes a new endpoint or fixes a bug, it doesn't need 200 lines of SQL query builder boilerplate from your database driver. It just needs:
1. Class inheritance structures
2. Typed function signatures & return types
3. Docstrings & interface contracts

Claude gets 100% of the architectural context needed to produce zero-defect code, while consuming **up to 95% fewer tokens**.

### ⚡ 1-Click Setup for Claude Desktop:
Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "tzero": {
      "command": "python",
      "args": ["-m", "tzero.tzero_mcp"]
    }
  }
}
```

- **Cost:** $0.00 (Zero paid APIs, runs 100% offline)
- **Security:** In-memory Shannon entropy scanner redacts API keys
- **License:** MIT Open Source

Check it out and drop a star if you find it useful! ⭐  
👉 **GitHub:** https://github.com/toprakahmetaydogmus/TZeroAlgorithm  
👉 **Web Playground:** https://tzero-indol.vercel.app

```
---

## Subreddit: `r/LocalLLaMA`

**Title:**
> T-Zero: 100% offline, zero-cloud AST codebase context pruner for local models (Ollama, LM Studio, Qwen 2.5 Coder, DeepSeek)

**Body:**
```markdown
When running local coding models (Qwen 2.5 Coder 7B/14B/32B, DeepSeek-Coder, Llama 3.1) on consumer GPUs, VRAM context window limits (8K–32K) make it impossible to feed full multi-file codebases into prompts.

**T-Zero** (v11.11.0) is a zero-cloud AST token reducer that fits whole multi-tier codebases into compact local context windows:
1. **Deterministic AST pruning:** Collapses function bodies to `...` while retaining full signatures and type annotations.
2. **PageRank Module Centrality:** Graph-theory ranking automatically prioritizes architectural backbone files when strict token caps are enforced.
3. **Shannon Entropy Zero-Leak:** Ensures no private keys or tokens leak into model prompts.
4. **Local BM25 Hybrid Search:** Instant semantic symbol lookup with 0 cloud embeddings.

- **Zero Cloud Calls:** 100% air-gapped stdio server.
- **Install:** `pip install tzero-mcp`
- **GitHub:** https://github.com/toprakahmetaydogmus/TZeroAlgorithm (Stars welcome! ⭐)

```
---

## Subreddit: `r/Turkey`

**Title:**
> 15 yaşındayım, Cursor ve Claude için geliştirdiğim açık kaynaklı context motoru v11.11.0 ile yayında! 🇹🇷

**Body:**
```markdown
Merhaba Türk yazılımcı topluluğu!

Ben Toprak Ahmet Aydoğmuş, 15 yaşındayım ve Siber Akademi bünyesinde bağımsız açık kaynaklı yazılımlar geliştiriyorum.

Yapay zeka kodlama araçlarıyla (Cursor, Claude Desktop, Antigravity, Windsurf) büyük projelerde çalışırken en büyük darboğaz **token sınırları ve yüksek context maliyetleri**. Tüm dosyaları yapay zekaya yüklediğinizde binlerce satır gereksiz gövde kodu yapay zekanın dikkatini dağıtıyor ve pencereyi tüketiyor.

Bu problemi çözmek için geliştirdiğim **T-Zero (Token Zero)** projesini v11.11.0 sürümüyle tamamen ücretsiz ve açık kaynak olarak yayınladım!

### 🌟 Temel Yetenekleri:
- Python, TypeScript, Go, Rust, Java vb. dillerde kodları AST (Abstract Syntax Tree) ile inceleyip fonksiyon gövdelerini buduyor ve token tüketimini **%85-%95 oranında azaltıyor**.
- Model Context Protocol (MCP) standardında çalıştığı için Cursor ve Claude Desktop'a tek tıkla ekleniyor.
- %100 yerel ve çevrimdışı çalışıyor; hiçbir harici ücretli API veya sunucuya bağlanmıyor ($0 maliyet).
- Yeni v11.11.0 sürümünde eklenen **AI Godfather Süpervizörü** sayesinde yapay zekanın uydurduğu (hallucinated) sahte fonksiyon çağrılarını ve eksik importları otomatik düzeltiyor.
- 537 otomatik testten %100 başarıyla geçmektedir.

Projeyi GitHub'da yıldızlayarak (Star ⭐) ilk 100 yıldız hedefimize ulaşmamıza destek olursanız çok sevinirim!

🔗 **GitHub:** https://github.com/toprakahmetaydogmus/TZeroAlgorithm  
🔗 **Web Benchmark:** https://tzero-indol.vercel.app  
🔗 **PyPI:** https://pypi.org/project/tzero-mcp/  

```
---
