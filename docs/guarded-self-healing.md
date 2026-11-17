# Guarded Self-Healing & AI Safety Architecture

The `TZeroAlgorithm` self-healing and AI safety engine provides a deterministic, zero-spend protection layer designed to mitigate:
1. Unauthorized or dangerous terminal command execution by autonomous agents.
2. Unintended, stale, or out-of-boundary filesystem mutations.
3. Accidental secret/credential disclosures in error traces, logs, and diagnostics.
4. AI agent hallucinations, phantom symbol references, and ungrounded technical claims.

---

## 1. Multi-Layer Defense Capabilities

### A. Terminal Execution & Process Safety
- **Default-Deny Agent Policy:** Agent-invoked shell commands are denied by default across MCP and orchestrator entry points. A host operator must opt in explicitly via `TZERO_ALLOW_AGENT_SHELL=1`.
- **Operator vs. Agent Privilege Separation:** Agent inputs cannot escalate execution privileges or alter security policies. Policies are configured exclusively via operator environment variables.
- **Structured Command Risk Assessment:** Every command string is categorized into risk tiers (`SAFE_READ_ONLY`, `WORKSPACE_MUTATION`, `NETWORK_OR_PACKAGE`, `DESTRUCTIVE`, `BLOCKED_OR_SUSPICIOUS`).
- **Argv Direct Process Execution (`shell=False`):** Safe commands that can be lexically tokenized are executed directly via argument lists with `shell=False`, preventing shell command injection (CWE-78).
- **Shell Chaining & Redirection Prevention:** Detects and blocks hidden sub-payloads using chaining (`&&`, `||`, `;`), redirection (`>`, `>>`, `<`), or command substitution (`$(...)`, `` `...` ``).
- **Zero-Spend Network & Package Blockade:** Blocks package managers (`pip`, `npm`, `poetry`, `cargo`, etc.) and network utilities (`curl`, `wget`, `ssh`, etc.) by default to avoid unintended costs, network dependencies, or external data exfiltration.

### B. Filesystem & Mutation Safety
- **Workspace Boundary Enforcement (`PathGuard`):** Prohibits mutations or inspections outside the workspace root (`work_dir`).
- **Directory Traversal & Symlink Escape Protection:** Path resolution verifies every directory component to ensure symlinks cannot escape the workspace root.
- **Protected Paths & Secret Files:** Blocks access or modification to sensitive targets such as `.env`, `.git/`, `.ssh/`, `.aws/`, private keys (`.pem`, `.key`), and certificates.
- **File Mutation Limits:** Enforces safety thresholds on file size ($\le 5\text{ MB}$) to prevent accidental truncation or clobbering of massive files.
- **Inspectable Unified Diffs:** Every proposed repair generates an inspectable unified diff before application.
- **Stale Patch Rejection:** Verifies SHA-256 hashes and original byte contents before replacement; if a file was modified concurrently or after proposal, the repair aborts.
- **Atomic Replacement:** Mutations write to a temporary file in the same directory (`.tzero-heal-*`), call `fsync`, and atomically swap via `os.replace`.
- **Multi-File Rollback Stack:** Tracks applied modifications in a transactional stack. If verification fails or an error occurs, modifications are rolled back in reverse order.
- **Anti-Cycling / Idempotence Guard:** Maintains a session cache of attempted patch hashes. If a patch fails verification once, it is never reapplied in a redundant cycle.
- **Pre- and Post-Repair AST Syntax Checks:** Proposes repairs only if Python's `ast.parse` validates the replacement syntax, and re-verifies AST integrity post-execution.

### C. Secret Redaction & Leak Shield
- **Diagnostic Sanitization (`SecretRedactor`):** All `stdout`, `stderr`, diagnostics, and execution traces are sanitized before being returned to agents or logs.
- **Pattern & Entropy Masking:** Detects known provider token formats (AWS keys, GitHub tokens, Bearer auth, private keys) and high-entropy candidate strings ($H \ge 4.75$), masking them with `[REDACTED_SECRET]`.
- **Sanitized Security Audit Log:** In-memory, thread-safe audit log (`GLOBAL_AUDIT_LOGGER`) records security verdicts without storing raw secrets.

### D. AI Grounding & Anti-Hallucination
- **Workspace Grounding Verification (`AIGroundingVerifier`):** Validates whether files, symbols, or lines claimed by the agent or extracted from error traces actually exist on disk.
- **AST Symbol Lookup:** Confirms whether claimed function or class definitions exist in the target file's AST before accepting them as repair targets.
- **Traceback Provenance Audit:** Classifies traceback frames into verified local workspace frames vs ungrounded/external frames.
- **Explicit Unknown / Unverified Status:** Refuses to guess or hallucinate repairs when ground truth cannot be established.
- **Strict Evidence Requirement:** A self-healing repair is only marked `resolved=True` if the verification command exits with code 0, post-repair AST parses without error, and file contents match expected bytes.
- **Flagging Unverified Claims:** Detects unsubstantiated assertions (e.g. claims of "100% bug-free" or "total zero hallucination") and marks them as unverified claims.

---

## 2. Programmatic Usage

```python
from tzero.tzero_jarvis.self_healing import SelfHealingExecutionEngine
from tzero.tzero_jarvis.agent_guard import CommandExecutionPolicy

# 1. Conservative local execution with policy enforcement
engine = SelfHealingExecutionEngine(
    work_dir="/path/to/project",
    enforce_agent_policy=True
)

# 2. Dry-run preview without mutating files
dry_result = engine.execute_and_heal("python -m unittest", dry_run=True)
print(dry_result.diagnostics)

# 3. Verified execution with atomic rollback on failure
result = engine.execute_and_heal("python -m unittest", max_retries=1)
if result.resolved:
    print("Repair verified and retained:", result.applied_patches)
else:
    print("Execution diagnostics:", result.diagnostics)
```

---

## 3. Security Boundaries & Known Limitations

- **Not an OS Sandbox:** T-Zero enforces process execution policies and path guards in Python user-space; it does not replace operating system sandboxes (e.g., Linux containers, cgroups, seccomp, or Windows AppContainer).
- **Subprocess Command Side Effects:** While file mutations performed by T-Zero can be rolled back, commands executed on the system can have arbitrary outside side effects (e.g. writing to external databases) that cannot be undone by this engine.
- **Concurrent Writers:** Same-directory atomic replacement prevents partial writes, but is not a hardware-level atomic compare-and-swap against external concurrent writers.
- **Dynamic Language Introspection:** Python code employing dynamic `eval()`, `exec()`, or runtime monkeypatching cannot be fully validated by static AST inspection alone.
- **Redaction Coverage:** The secret redactor employs regular expressions and Shannon entropy heuristics; it significantly reduces accidental leaks, but cannot guarantee detection of steganographic or deliberately obfuscated secrets.
- **No Guarantee of General Correctness:** Passing a single verification test command does not prove overall program correctness; it confirms only that the tested command completed with exit code 0.
