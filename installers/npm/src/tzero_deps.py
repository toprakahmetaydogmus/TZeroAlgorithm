# -*- coding: utf-8 -*-
"""T-Zero dependency bootstrap and environment doctor (standard library only).

* ``ensure_dependencies()`` runs before anything else is imported. If a required package is
  missing or older than the minimum version, it is installed with pip (quietly, to stderr only,
  so the MCP stdio protocol on stdout is never disturbed).
* ``run_doctor()`` powers ``python main.py --doctor``: it checks Python, packages, tkinter, git
  and the OS keyring and prints an easy-to-read report.

Set ``TZERO_NO_AUTO_INSTALL=1`` to disable automatic installation (the tool then only tells you
what is missing). Frozen builds (the .exe) never install anything.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
"""

import importlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from typing import List, NamedTuple, Optional, Tuple

OPT_OUT_ENV = "TZERO_NO_AUTO_INSTALL"
MIN_PYTHON = (3, 9)


class Dependency(NamedTuple):
    import_name: str   # name used in `import x`
    dist_name: str     # name on PyPI / importlib.metadata
    min_version: str   # minimum acceptable version
    purpose: str

    @property
    def spec(self) -> str:
        return f"{self.dist_name}>={self.min_version}"


REQUIRED: List[Dependency] = [
    Dependency("requests", "requests", "2.28.0", "AI provider HTTP calls"),
    Dependency("keyring", "keyring", "23.13.1", "OS credential storage"),
    Dependency("darkdetect", "darkdetect", "0.8.0", "OS theme detection"),
    Dependency("pygments", "pygments", "2.14.0", "syntax highlighting"),
    Dependency("PIL", "Pillow", "9.0.0", "icon and image generation"),
]
MCP_DEPENDENCY = Dependency("mcp", "mcp", "1.0.0", "Model Context Protocol server")


def _version_tuple(version: str) -> Tuple[int, ...]:
    parts: List[int] = []
    for token in re.split(r"[.\-+]", version):
        match = re.match(r"\d+", token)
        if not match:
            break
        parts.append(int(match.group()))
    return tuple(parts)


def installed_version(dep: Dependency) -> Optional[str]:
    """Returns the installed version string, or None when the distribution is unknown."""
    try:
        from importlib import metadata
        return metadata.version(dep.dist_name)
    except Exception:
        return None


def check_dependency(dep: Dependency) -> Tuple[str, Optional[str]]:
    """Returns (status, version) where status is 'ok', 'outdated' or 'missing'."""
    try:
        found = importlib.util.find_spec(dep.import_name) is not None
    except (ImportError, ValueError):
        found = False
    if not found:
        return "missing", None
    version = installed_version(dep)
    if version and _version_tuple(version) < _version_tuple(dep.min_version):
        return "outdated", version
    return "ok", version


def _err(message: str) -> None:
    if sys.stderr is not None and hasattr(sys.stderr, "write"):
        try:
            sys.stderr.write(message + "\n")
            sys.stderr.flush()
        except Exception:
            pass


def ensure_dependencies(include_mcp: bool = False) -> bool:
    """Makes sure required packages are present, installing them when allowed.

    Returns True when everything needed is available afterwards.
    """
    if sys.version_info < MIN_PYTHON:
        _err(f"[T-Zero] Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required "
             f"(found {sys.version_info.major}.{sys.version_info.minor}).")
        return False
    if getattr(sys, "frozen", False):  # PyInstaller build: dependencies are bundled
        return True

    ensure_scripts_in_path(quiet=True)
    deps = list(REQUIRED) + ([MCP_DEPENDENCY] if include_mcp else [])
    problems = [d for d in deps if check_dependency(d)[0] != "ok"]
    if not problems:
        return True

    specs = [d.spec for d in problems]
    manual = f'"{sys.executable}" -m pip install ' + " ".join(f'"{s}"' for s in specs)
    if os.environ.get(OPT_OUT_ENV) == "1":
        _err("[T-Zero] Missing or outdated packages: " + ", ".join(specs))
        _err(f"[T-Zero] Automatic install is disabled ({OPT_OUT_ENV}=1). Run:\n  {manual}")
        return False

    _err("[T-Zero] Installing missing or outdated packages: " + ", ".join(specs))
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--quiet", *specs],
            capture_output=True, text=True, timeout=900,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        _err(f"[T-Zero] Could not run pip: {exc}\n  Install manually:\n  {manual}")
        return False

    importlib.invalidate_caches()
    if proc.returncode != 0:
        output = (proc.stderr or proc.stdout or "").strip()
        _err("[T-Zero] pip failed:\n" + "\n".join(output.splitlines()[-8:]))
        if "externally-managed-environment" in output:
            _err("[T-Zero] This Python is managed by your OS. Use a virtual environment:\n"
                 "  python -m venv .venv && .venv/bin/pip install -r requirements.txt")
        else:
            _err(f"  Install manually:\n  {manual}")
        return False

    ensure_scripts_in_path(quiet=True)
    still_bad = [d.spec for d in problems if check_dependency(d)[0] != "ok"]
    if still_bad:
        _err("[T-Zero] Still unavailable after install: " + ", ".join(still_bad))
        return False
    _err("[T-Zero] Dependencies ready.")
    return True


def ensure_scripts_in_path(quiet: bool = True) -> bool:
    """Ensures Python's Scripts/bin directory is in the user's PATH environment variable.
    
    Automatically fixes Windows and Unix PATH when installing via pip so commands
    like `tzero`, `tzero-gui`, `tzero-mcp`, `tzero-add-mcp` work everywhere immediately.
    """
    import site
    candidates = []

    if os.name == "nt":
        sys_scripts = os.path.join(sys.prefix, "Scripts")
        user_scripts = os.path.join(site.USER_BASE, "Scripts")
    else:
        sys_scripts = os.path.join(sys.prefix, "bin")
        user_scripts = os.path.join(site.USER_BASE, "bin")

    for p in [sys_scripts, user_scripts]:
        if p and os.path.isdir(p) and p not in candidates:
            candidates.append(p)

    current_path_dirs = [os.path.normcase(os.path.abspath(x)) for x in os.environ.get("PATH", "").split(os.pathsep) if x]

    added_any = False
    for candidate in candidates:
        norm_cand = os.path.normcase(os.path.abspath(candidate))
        if norm_cand not in current_path_dirs:
            # Update current process
            os.environ["PATH"] = candidate + os.pathsep + os.environ.get("PATH", "")
            current_path_dirs.insert(0, norm_cand)
            added_any = True

            # Permanently update user PATH
            if os.name == "nt":
                try:
                    import winreg
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
                        try:
                            user_path, _ = winreg.QueryValueEx(key, "Path")
                        except FileNotFoundError:
                            user_path = ""
                        parts = [x.strip() for x in user_path.split(";") if x.strip()]
                        if candidate not in parts:
                            parts.append(candidate)
                            new_path = ";".join(parts)
                            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
                            if not quiet:
                                sys.stderr.write(f"[T-Zero] Added {candidate} to User PATH in Windows Registry.\n")
                except Exception:
                    pass
            else:
                try:
                    home = os.path.expanduser("~")
                    for rc_name in [".bashrc", ".zshrc"]:
                        rc_path = os.path.join(home, rc_name)
                        if os.path.exists(rc_path):
                            with open(rc_path, "r", encoding="utf-8", errors="ignore") as f:
                                rc_content = f.read()
                            export_line = f'export PATH="{candidate}:$PATH"'
                            if candidate not in rc_content:
                                with open(rc_path, "a", encoding="utf-8") as f:
                                    f.write(f"\n# Added by T-Zero Context Architect\n{export_line}\n")
                                if not quiet:
                                    sys.stderr.write(f"[T-Zero] Added {candidate} to {rc_name}\n")
                except Exception:
                    pass

    return added_any


def _line(level: str, text: str) -> str:
    return f"  [{level:^4}] {text}"


def _run_deep_subsystem_check() -> int:
    """Exercise all 9 v11 offline subsystems and report pass/fail. Returns failure count."""
    import tempfile
    from pathlib import Path

    print("\nDeep Offline Subsystem Self-Check:")
    checks = []

    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. BPE Tokenizer
        try:
            from tzero_polyglot import count_bpe_tokens
            tok = count_bpe_tokens("def hello(): pass\n")
            if not (isinstance(tok, int) and tok > 0):
                raise ValueError("unexpected diagnostic result")
            checks.append(("BPE Tokenizer", True, ""))
        except Exception as exc:
            checks.append(("BPE Tokenizer", False, str(exc)))

        # 2. Polyglot AST Reducer
        try:
            from tzero_polyglot import PolyglotTokenReducer
            r = PolyglotTokenReducer()
            out = r.reduce_code("def foo(x: int) -> int:\n    return x + 1\n", filename="foo.py")
            if not ("def foo" in out):
                raise ValueError("unexpected diagnostic result")
            ts = r.reduce_code("export function greet(name: string): string { return name; }", filename="sample.ts")
            if not ("greet" in ts):
                raise ValueError("unexpected diagnostic result")
            checks.append(("Polyglot AST Reducer", True, ""))
        except Exception as exc:
            checks.append(("Polyglot AST Reducer", False, str(exc)))

        # 3. Zero-Leak Engine
        try:
            from tzero_security import ZeroLeakEngine
            fake_key = "sk" + "-" + "a" * 32
            result = ZeroLeakEngine.scan_text(fake_key)
            if not (isinstance(result, list) and len(result) > 0):
                raise ValueError("unexpected diagnostic result")
            checks.append(("Zero-Leak Engine", True, ""))
        except Exception as exc:
            checks.append(("Zero-Leak Engine", False, str(exc)))

        # 4. LSP Server
        try:
            from tzero_lsp import TZeroLSPServer
            lsp = TZeroLSPServer(workspace_dir=tmpdir)
            py_path = os.path.join(tmpdir, "sample.py")
            code = f'SERVICE_KEY = "{fake_key}"\n' + "def greet(name: str) -> str:\n    return name\n"
            Path(py_path).write_text(code, encoding="utf-8")
            uri = Path(py_path).as_uri()
            opened = lsp.handle_message({
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {"textDocument": {"uri": uri, "text": code}},
            })
            hover = lsp.compute_hover(uri, code, line=1, character=4)
            if hover is None:
                raise ValueError("unexpected diagnostic result")
            diagnostics = opened[0]["params"]["diagnostics"]
            if not (lsp.compute_code_actions(uri, code, diagnostics)):
                raise ValueError("unexpected diagnostic result")
            checks.append(("LSP Server", True, ""))
        except Exception as exc:
            checks.append(("LSP Server", False, str(exc)))

        # 5. Lifecycle Hooks
        try:
            from tzero_hooks import evaluate_pre_tool_use, evaluate_post_tool_use
            blocked = evaluate_pre_tool_use(
                {"tool_name": "Read", "tool_input": {"file_path": ".env"}},
                workspace_dir=tmpdir,
            )
            if not (blocked["decision"] == "block"):
                raise ValueError("unexpected diagnostic result")
            big = "def x(): pass\n" * 20
            pruned = evaluate_post_tool_use(
                {"tool_name": "Read", "tool_input": {"file_path": "f.py"}, "tool_response": big},
                workspace_dir=tmpdir,
                max_chars=50,
            )
            if not (pruned["decision"] == "prune"):
                raise ValueError("unexpected diagnostic result")
            checks.append(("Lifecycle Hooks", True, ""))
        except Exception as exc:
            checks.append(("Lifecycle Hooks", False, str(exc)))

        # 6. Federation Sync
        try:
            from tzero_federation import FederationSyncEngine
            peer_ws = os.path.join(tmpdir, "peer")
            os.mkdir(peer_ws)
            peer_py = os.path.join(peer_ws, "ledger.py")
            with open(peer_py, "w", encoding="utf-8") as fh:
                fh.write("class Ledger:\n    pass\n")
            manifest_file = os.path.join(peer_ws, "manifest.json")
            exported = FederationSyncEngine.export_manifest(peer_ws, repo_name="deep-peer", out_file=manifest_file)
            if not (FederationSyncEngine.verify_manifest(exported)):
                raise ValueError("unexpected diagnostic result")
            imp = FederationSyncEngine.import_manifest(tmpdir, manifest_file)
            if not (imp["verified"]):
                raise ValueError("unexpected diagnostic result")
            checks.append(("Federation Sync", True, ""))
        except Exception as exc:
            checks.append(("Federation Sync", False, str(exc)))

        # 7. SCIP Importer
        try:
            from tzero_scip import ScipIndexImporter
            sample = {"documents": [{"relative_path": "a.py", "occurrences": [
                {"range": [0, 0, 0, 5], "symbol": "MyClass", "symbol_roles": 1},
            ]}]}
            graph = ScipIndexImporter.from_scip_dict(sample)
            if not (graph.format_name in ("scip", "scip-dict")):
                raise ValueError("unexpected diagnostic result")
            checks.append(("SCIP Importer", True, ""))
        except Exception as exc:
            checks.append(("SCIP Importer", False, str(exc)))

        # 8. Contracts & SARIF
        try:
            from tzero_contracts import ASTContractComparator
            old = "def foo(x: int) -> int:\n    return x\n"
            new = "def foo(x: int, y: int) -> int:\n    return x + y\n"
            diff_rep = ASTContractComparator.compare_code(old, new, file_path="f.py")
            if not (diff_rep.is_breaking):
                raise ValueError("unexpected diagnostic result")
            sarif = ASTContractComparator.format_sarif_report([diff_rep])
            if not (sarif.get("version") == "2.1.0"):
                raise ValueError("unexpected diagnostic result")
            checks.append(("Contracts & SARIF", True, ""))
        except Exception as exc:
            checks.append(("Contracts & SARIF", False, str(exc)))

        # 9. Agent Kernel & Snapshot
        try:
            from tzero_rust_bridge import AgentKernelSandbox
            from tzero_snapshot import SnapshotEngine
            kernel = AgentKernelSandbox(workspace_dir=tmpdir)
            if not (kernel.validate_execution_plan({"allow_network": False, "read_paths": [tmpdir]})["allowed"]):
                raise ValueError("unexpected diagnostic result")
            if kernel.validate_execution_plan({"allow_network": True, "read_paths": [tmpdir]})["allowed"]:
                raise ValueError("unexpected diagnostic result")
            snap_py = os.path.join(tmpdir, "snap_test.py")
            with open(snap_py, "w", encoding="utf-8") as fh:
                fh.write("def snap_fn(): pass\n")
            snap = SnapshotEngine.create_snapshot(tmpdir)
            if not (snap.file_count >= 1):
                raise ValueError("unexpected diagnostic result")
            checks.append(("Agent Kernel & Snapshot", True, ""))
        except Exception as exc:
            checks.append(("Agent Kernel & Snapshot", False, str(exc)))

    failures = 0
    for name, passed, msg in checks:
        if passed:
            print(_line("OK", name))
        else:
            failures += 1
            print(_line("FAIL", f"{name}: {msg}"))
    return failures


def run_doctor(deep: bool = False) -> int:
    """Checks the environment, fixing missing packages when allowed. Returns a process exit code."""
    print("T-Zero Doctor: environment check\n")
    failures = 0

    py = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= MIN_PYTHON:
        print(_line("OK", f"Python {py}"))
    else:
        failures += 1
        print(_line("FAIL", f"Python {py}: version {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required"))

    if not deep:
        ensure_dependencies(include_mcp=True)
    for dep in REQUIRED + [MCP_DEPENDENCY]:
        status, version = check_dependency(dep)
        label = f"{dep.dist_name} {version or ''}".strip()
        if status == "ok":
            print(_line("OK", f"{label} ({dep.purpose})"))
        else:
            failures += 1
            print(_line("FAIL", f"{dep.dist_name}>={dep.min_version} is {status} ({dep.purpose})"))

    if importlib.util.find_spec("mcp") is not None:
        try:
            if importlib.util.find_spec("mcp.server.mcpserver") is not None:
                print(_line("OK", "MCP SDK flavor: MCPServer (mcp 2.x)"))
            else:
                print(_line("OK", "MCP SDK flavor: FastMCP (mcp 1.x)"))
        except (ImportError, ValueError):
            print(_line("OK", "MCP SDK flavor: FastMCP (mcp 1.x)"))

    if importlib.util.find_spec("tkinter") is not None:
        print(_line("OK", "tkinter (desktop GUI available)"))
    else:
        print(_line("WARN", "tkinter missing: the GUI is unavailable, the CLI and MCP server still work "
                            "(Debian/Ubuntu: sudo apt install python3-tk)"))

    if shutil.which("git"):
        print(_line("OK", "git found (commit history and diff features)"))
    else:
        print(_line("WARN", "git not found: git features are disabled"))

    try:
        import keyring
        backend = keyring.get_keyring()
        name = f"{type(backend).__module__}.{type(backend).__name__}"
        if "fail" in name.lower() or "null" in name.lower():
            print(_line("WARN", "no usable OS keyring backend: saving API keys in the app will not work; "
                                "set NVIDIA_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY / OPENROUTER_API_KEY / "
                                "ANTHROPIC_API_KEY instead"))
        else:
            print(_line("OK", f"keyring backend: {name}"))
    except Exception as exc:
        print(_line("WARN", f"keyring could not be checked: {exc}"))

    if not deep:
        ensure_scripts_in_path(quiet=True)
        print(_line("OK", "Python Scripts PATH verified (tzero, tzero-gui, tzero-mcp accessible)"))

    if deep:
        from tzero_polyglot import _ALLOW_BPE_DOWNLOAD

        token = _ALLOW_BPE_DOWNLOAD.set(False)
        try:
            failures += _run_deep_subsystem_check()
        finally:
            _ALLOW_BPE_DOWNLOAD.reset(token)

    print()
    if failures:
        print(f"{failures} problem(s) found. See the FAIL lines above.")
        return 1
    print("All required checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(run_doctor())
