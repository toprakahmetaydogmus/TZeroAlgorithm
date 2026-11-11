# T-Zero Algorithm

[![PyPI](https://img.shields.io/pypi/v/tzero-mcp)](https://pypi.org/project/tzero-mcp/)
[![npm](https://img.shields.io/npm/v/tzero-mcp)](https://www.npmjs.com/package/tzero-mcp)
[![VS Code](https://img.shields.io/visual-studio-marketplace/v/siber-akademi.tzero-vscode)](https://marketplace.visualstudio.com/items?itemName=siber-akademi.tzero-vscode)
[![M8ven](https://m8ven.ai/badge/mcp/toprakahmetaydogmus/tzeroalgorithm?variant=verified)](https://m8ven.ai/mcp/toprakahmetaydogmus/tzeroalgorithm)
[![Glama](https://img.shields.io/badge/registry-Glama-635bff)](https://glama.ai/mcp/servers/toprakahmetaydogmus/TZeroAlgorithm)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776ab)](pyproject.toml)
[![CI](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/actions/workflows/ci.yml/badge.svg)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

[English](README.md) · [Türkçe](README.tr.md) · [Privacy policy](PRIVACY.md)

**Directories and demos**

[![MCP Servers](https://mcpservers.org/badge.svg)](https://mcpservers.org/servers/toprakahmetaydogmus/tzeroalgorithm)
[![AI Agents Listing](https://img.shields.io/badge/AI%20Agents-Listing-6366f1)](https://aiagentslisting.com/mcp/t-zero-algorithm)
[![MCP Observatory](https://img.shields.io/badge/MCP%20Observatory-Listing-0f766e)](https://mcpobservatory.com/servers/github%3Atoprakahmetaydogmus/TZeroAlgorithm)
[![Skillful](https://img.shields.io/badge/Skillful-Directory-2d6a4f)](https://skillful.sh/mcp/tzero-mcp)
[![Hugging Face Space](https://img.shields.io/badge/Hugging%20Face-Space-ffca28?logo=huggingface)](https://huggingface.co/spaces/toprakke4/tzero-token-reducer)
[![Vercel Hub](https://img.shields.io/badge/Vercel-Project%20Hub-000000?logo=vercel)](https://tzero-indol.vercel.app)
[![Smithery status](https://img.shields.io/badge/Smithery-legacy%20listing%20unavailable-lightgrey)](https://www.smithery.ai/future)

Smithery's former T-Zero listing and badge URLs currently return 404. Its directory changed in October 2026, and a current T-Zero listing has not been verified. The Smithery status badge links to the provider's notice.

T-Zero builds code context for AI coding assistants. It extracts signatures, imports, and dependencies from a local workspace and exposes them through a CLI and an MCP server.

## Why use it?

A coding assistant often needs the public shape of related modules before it needs every implementation detail. T-Zero can reduce that context to declarations and relationships, then send the resulting text through the CLI or an MCP tool. You choose what to inspect and when to request full source.

- **Python AST pruning** parses Python and retains structural signatures while reducing function bodies. Other supported languages use language-specific reducers and, when configured, optional parser adapters.
- **Context selection** can keep a focus file in full and represent related files as smaller skeletons. Snapshot and dependency tools help locate the relevant context.
- **Budgeted packing** orders context for a target token budget. Cache-aligned mode places stable context before changing task details.
- **Local safeguards** include secret scanning, architectural checks, and a language server with diagnostics and code actions. Inspect results before applying changes.

## Install

Install the Python package with Python 3.11 or newer.

```sh
python -m pip install --upgrade tzero-mcp
```

Alternatively, start the MCP server with Node.js installed.

```sh
npx -y tzero-mcp@latest
```

Windows executables are available on the [releases page](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases). Download `TZeroAlgorithm.exe` for the application, `TZeroMCP.exe` for the MCP server, or `AddMCP.exe` for client configuration. Compare each download's SHA-256 hash with its accompanying checksum before running it.

## First use

Run a scan inside the project you want to inspect.

```sh
tzero --scan . --format json
tzero --doctor --deep
```

The deep diagnostic checks local subsystems. Run `tzero init` to configure supported coding assistants. For manual MCP configuration, add this server entry to your client's configuration file.

```json
{
  "mcpServers": {
    "tzero": {
      "command": "tzero-mcp",
      "args": []
    }
  }
}
```

## Token reduction and measurements

T-Zero reduces source context by preserving useful structure while omitting portions of implementation. Python is parsed with the standard-library `ast` module. The polyglot reducer also supports JavaScript, TypeScript, Rust, Go, C/C++, Java, C#, Solidity, Ruby, PHP, Swift, Kotlin, Dart, Scala, and Elixir. The result depends on the parser or reducer used and the source provided. A reduced skeleton may omit details necessary to complete a task, so inspect it and retrieve full code when needed.

For example, the default Python reducer changes this input:

```python
def greet(name: str) -> str:
    message = "Hello, " + name
    return message
```

into this structural summary:

```python
def greet(name: str) -> str: ...
```

The function signature remains visible. Its implementation is omitted, so this output is for context rather than execution.

The bundled **core benchmark** uses three synthetic Python tasks. Each comparison includes a full target implementation and either the full dependency source or its AST skeleton. The following values were reproduced locally on 11 November 2026 using `tiktoken` and its `cl100k_base` encoding.

| Task | Full context | Reduced context | Reduction |
| --- | ---: | ---: | ---: |
| TASK-01 | 502 tokens | 375 tokens | 25.3% |
| TASK-02 | 322 tokens | 239 tokens | 25.8% |
| TASK-03 | 332 tokens | 283 tokens | 14.8% |
| **Total** | **1,156 tokens** | **897 tokens** | **22.4%** |

The benchmark reports **21.9%** as the arithmetic mean of the three per-task reductions. The total row uses `(1,156 − 897) / 1,156`, so its weighted reduction is 22.4%. These examples do not establish a repository-wide savings rate, measure model accuracy, or predict savings for a different tokenizer or codebase.

Reproduce the sample from the root of a source checkout. `tiktoken` is optional and available from PyPI. When it or the encoding is unavailable, the benchmark falls back to a character-based estimate instead of exact BPE counts. The first load of an uncached encoding may require a download.

```sh
python -m pip install tiktoken
python tzero_task_benchmark.py
```

The benchmark's pass checks inspect syntax and method names against the pruned fixture. They are not a substitute for running an application's tests. For your own repository, use `tzero --scan . --format json` and compare the reported raw and reduced counts. The JSON scan estimates raw tokens from file bytes divided by four and reduced tokens from character counts divided by four. These are estimates and are not the BPE measurements in the table.

To produce a context pack with a target budget, run this from your project directory:

```sh
tzero --pack 16000 --focus path/to/file.py --cache-aligned --pack-out context.txt
```

Review `context.txt` before giving it to an assistant. The file can contain source code and other project information.

## Capabilities

- Extract code structure and dependencies for context building.
- Search local code and inspect the effect of changing a symbol.
- Scan for potential secrets and architecture violations.
- Build AST snapshots and context packs with stable prefixes.
- Inspect API contract changes and export SARIF reports.
- Run a stdio language server with hover information and code actions.
- Import SCIP indexes and exchange repository manifests for cross-repository analysis.

The default MCP catalog exposes 21 tools, including `search_tools` for discovery. Set `TZERO_MCP_TOOL_MODE=all` to expose all 58 tools at startup. Individual tools describe whether they read or modify files.

### CLI and integrations

| Command | Purpose |
| --- | --- |
| `tzero --scan . --format json` | Inspect a workspace and report context metrics. |
| `tzero --pipe example.py` | Read source from standard input and reduce it using the filename hint. |
| `tzero --snapshot .` | Create an AST snapshot for incremental work. |
| `tzero --lsp` | Run the stdio language server for editor integrations. |
| `tzero --hook-install all` | Configure supported AI-client lifecycle hooks. This writes configuration files. |
| `tzero --contracts HEAD~1 --contracts-sarif report.sarif` | Compare public contracts against a Git ref and write a SARIF report. |
| `tzero --federation impact --federation-symbol SYMBOL` | Inspect cross-repository impact for a symbol. |
| `tzero --doctor --deep` | Run the offline subsystem checks. |

The VS Code/Cursor extension adds commands for the language server, hooks, and federation. The dashboard provides a local browser interface. The PC-Fixer server provides separate diagnostic and repair tools, some of which can change files or system state.

Use `tzero --help` to see supported flags and arguments. This source version is 10.9.0. Package registries may offer an earlier version until publication completes.

## Limits and privacy

Context reduction depends on the language, repository, and selected mode. Python extraction uses the standard library AST. Other languages may use structural heuristics. Inspect generated context before relying on it for a change.

Secret detection can miss credentials or flag harmless text. Review findings before applying repairs. Some tools modify files or system state.

Local analysis does not require a cloud model. A connected MCP client may send returned source excerpts to its configured provider. Optional network features, dependency installation, and initial tokenizer downloads can contact external services. See the [privacy policy](PRIVACY.md).

## Development

```sh
python -m pip install -e .
python -m unittest discover -s tests -p "test_*.py"
python scripts/sync_release_metadata.py --check
node --test installers/npm/test/package.test.js
node --test extensions/vscode/test/extension.test.js
```

## Feedback

Open an [issue](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/issues) with your operating system, version, command, expected result, and a small reproducible example. Remove credentials, personal paths, and private source before posting.

Maintained by Toprak Ahmet Aydoğmuş. Licensed under [MIT](LICENSE).
