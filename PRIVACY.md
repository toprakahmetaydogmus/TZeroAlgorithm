# Privacy and network behavior

AST parsing, AST pruning, and lexical search read workspace data on the machine
running T-Zero. MCP tools can return source excerpts, paths, and diagnostic
results to the connected client. A remote model configured in that client can
receive those results according to the client's settings and privacy policy.

| Operation | Network and data |
| --- | --- |
| AI-assisted architecture or documentation generation | When explicitly enabled (`use_ai=True` or remote provider selected), can send prompts, paths, dependency relationships, and code excerpts only to the user-selected provider (OpenAI, Anthropic, Google Gemini, NVIDIA NIM, OpenRouter, or local Ollama). Missing credentials or provider errors fall back locally to deterministic AST output. |
| Legacy `jarvis_zero_key_query` | Sends the prompt and system instruction to Ollama on the same machine. The Ollama service and selected model determine any further processing. If local inference fails, T-Zero reports that it is unavailable. |
| Web search | Sends the query to DuckDuckGo only when explicitly invoked via the web-search helper. |
| Public project metrics and version lookups | May query GitHub, npm, or PyPI when displaying community counters, running `tzero share`, or loading live badges. |
| Package installation, tokenizer data, hosted demos | Package managers, the tokenizer's first uncached fetch, and hosted demos can contact their respective services. Runtime dependency checks print a manual command if packages are missing and do not install automatically unless requested. |

All Pollinations integration (`FreePollinationsProvider` / `https://text.pollinations.ai/`) and all automatic cloud fallbacks have been completely removed from the codebase (`jarvis_zero_key_query`, `ContextExportManager.generate_architecture_blueprint`, `PROVIDERS`, and the desktop GUI generator). For sensitive workspaces, use local AST generation and leave AI-assisted generation disabled.

## Local state changes

Saving API credentials in the app uses the configured OS keyring. Depending on
the tool, explicitly requested repair and setup actions can write files, run local
system commands, or change configuration. Dependency checks leave shell startup
files and the Windows user PATH unchanged.
The explicit `python -m tzero.tzero_deps --add-to-path` command appends the
installed T-Zero launcher directory to the requesting user's PATH through the
Windows user registry or their Bash or Zsh startup file.

The repository includes optional protection tooling for generated applications
with anti-debugging, encrypted bytecode execution, and a webhook alert option.
The webhook is disabled by default. When enabled for a generated application, it
can send detection events and host or process metadata to the configured URL.

## npm 12.3.0 advisory

[GHSA-pm3r-rxg9-cj5j](https://github.com/advisories/GHSA-pm3r-rxg9-cj5j) covers
`tzero-mcp@12.3.0` on npm and lists no patched version. Follow GitHub's advisory
if you installed or ran that package.
