# T-Zero Algorithm

[![PyPI](https://img.shields.io/pypi/v/tzero-mcp)](https://pypi.org/project/tzero-mcp/)
[![npm](https://img.shields.io/npm/v/tzero-mcp)](https://www.npmjs.com/package/tzero-mcp)
[![VS Code](https://img.shields.io/visual-studio-marketplace/v/siber-akademi.tzero-vscode)](https://marketplace.visualstudio.com/items?itemName=siber-akademi.tzero-vscode)
[![M8ven](https://m8ven.ai/badge/mcp/toprakahmetaydogmus/tzeroalgorithm?variant=verified)](https://m8ven.ai/mcp/toprakahmetaydogmus/tzeroalgorithm)
[![CI](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/actions/workflows/ci.yml/badge.svg)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

[English](README.md) · [Türkçe](README.tr.md) · [Privacy policy](PRIVACY.md)

T-Zero builds code context for AI coding assistants. It extracts signatures, imports, and dependencies from a local workspace and exposes them through a CLI and an MCP server.

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

## Capabilities

- Extract code structure and dependencies for context building.
- Search local code and inspect the effect of changing a symbol.
- Scan for potential secrets and architecture violations.
- Build AST snapshots and context packs with stable prefixes.
- Inspect API contract changes and export SARIF reports.
- Run a stdio language server with hover information and code actions.
- Import SCIP indexes and exchange repository manifests for cross-repository analysis.

The default MCP catalog exposes 21 tools, including `search_tools` for discovery. Set `TZERO_MCP_TOOL_MODE=all` to expose all 58 tools at startup. Individual tools describe whether they read or modify files.

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
