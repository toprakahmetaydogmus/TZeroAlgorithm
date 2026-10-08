# Changelog

## [3.0.10] - 2026-10-08

### Fixed

- Resolve the source project root when the desktop app is launched from its `dist` or `build` folder.
- Ignore numbered virtual environments such as `.venv-1` during workspace scans.
- Show helpful instructions when the file explorer has not been scanned, has no supported source files, or has no search matches.

### Improved

- Clarify that compiled `.exe` files are not source files and direct users to scan the project source folder.

## [3.0.9] - 2026-10-08

### Fixed

- Preserve complete multiline Python function, async function, class, and import headers in Ultra reduction.
- Keep a line-based fallback when Python source cannot be parsed.
- Make the desktop header search open the code explorer and filter indexed files; `Ctrl+K` focuses search.

### Improved

- Refresh the default dashboard with a warm ivory, midnight, and champagne palette and more readable typography.
- Update package, CLI, MCP, installer, and GitHub Action references to version 3.0.9.
