---
name: tzero-audit
description: >-
  Run AST static code analysis, code smells check, cyclomatic complexity report, and 100% Zero-Leak security audit for hardcoded secrets.
  Activate when the user types "/tzero-audit" or asks to audit code quality.
---

# /tzero-audit — AST Code Quality & Zero-Leak Security Audit

Perform a comprehensive AST quality audit and verify 100% Zero-Leak security:
1. **Code Smells:** Functions >50 lines, classes >300 lines, high complexity.
2. **Dead Code:** Unused imports and unreferenced private functions.
3. **Security (Zero-Leak):** High-entropy strings, hardcoded API keys, tokens, and credentials.

## Execution
Call the `audit_codebase_quality` MCP tool on the target path (default: `.`).
