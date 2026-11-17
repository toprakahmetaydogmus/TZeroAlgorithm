# Guarded self-healing

`SelfHealingExecutionEngine` runs a trusted command locally and diagnoses Python
tracebacks. For an explicit missing-colon syntax error, it can propose a
single-line change inside the workspace. The proposal includes a unified diff
and is parsed with Python's AST before application. `execute_and_heal` reruns the
command and keeps the change only if that command succeeds. If verification
fails, it restores the original bytes unless the file changed during the run.
Unsupported failures are reported without guessing or installing packages.
Writes use same-directory atomic replacement and check for observed concurrent
changes before replacement. These checks are not an atomic compare-and-swap;
avoid concurrent writers while healing.

```python
from tzero.tzero_jarvis.self_healing import SelfHealingExecutionEngine

engine = SelfHealingExecutionEngine(work_dir="/path/to/project")
result = engine.execute_and_heal("python -m unittest", max_retries=1)
print(result.to_dict())
```

For inspection without changing files, call `propose_repair(path, error_type,
error_line, stderr)` and inspect its `diff`. The legacy
`auto_repair_python_file` method applies a syntax-checked proposal directly;
it does not run a verification command.

Commands run with the host shell and are not sandboxed. Only run trusted,
repeatable commands: their side effects are not rolled back. Verification is
limited to the command supplied; passing it does not prove correctness. The
current engine makes at most one repair attempt and does not fix arbitrary
runtime failures, install dependencies, or contact a model API.
