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
    sys.stderr.write(message + "\n")
    sys.stderr.flush()


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

    still_bad = [d.spec for d in problems if check_dependency(d)[0] != "ok"]
    if still_bad:
        _err("[T-Zero] Still unavailable after install: " + ", ".join(still_bad))
        return False
    _err("[T-Zero] Dependencies ready.")
    return True


def _line(level: str, text: str) -> str:
    return f"  [{level:^4}] {text}"


def run_doctor() -> int:
    """Checks the environment, fixing missing packages when allowed. Returns a process exit code."""
    print("T-Zero Doctor: environment check\n")
    failures = 0

    py = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= MIN_PYTHON:
        print(_line("OK", f"Python {py}"))
    else:
        failures += 1
        print(_line("FAIL", f"Python {py}: version {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required"))

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

    print()
    if failures:
        print(f"{failures} problem(s) found. See the FAIL lines above.")
        return 1
    print("All required checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(run_doctor())
