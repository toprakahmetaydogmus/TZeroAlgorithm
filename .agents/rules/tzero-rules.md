---
description: T-Zero Algorithm Workspace Guidelines and Zero-Regression Rules
---

# TZero Workspace Rules

1. **Autonomous & Free:** Always prioritize 100% free offline algorithms. No paid API dependencies.
2. **Full Test Verification:** Always run `python -m unittest discover tests` after any changes to ensure the full automated test suite (630+ unit tests) passes without regression.
3. **Clean Git State:** Keep working tree clean, write concise and meaningful commit messages.
4. **Polyglot & AST Integrity:** Preserve AST signature pruning integrity across Python, JS/TS, Go, Rust, Java, C#, C/C++.
