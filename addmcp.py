# -*- coding: utf-8 -*-
"""Install the bundled T-Zero MCP server into detected IDE configurations.

Supports both a clean Dark GUI and a headless CLI (--all, --list, --targets).
Automatically copies the standalone TZeroMCP runtime or configures the Python script,
guaranteeing zero configuration headaches on any computer.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple


APP_VERSION = "3.0.3"
SERVER_NAME = "tzero"
SERVER_FILENAME = "TZeroMCP.exe"


def _attach_windows_console() -> None:
    """If run from CMD or PowerShell on Windows with --noconsole, attach parent console."""
    if os.name == "nt":
        try:
            import ctypes
            if ctypes.windll.kernel32.AttachConsole(-1):
                if sys.stdout is None or getattr(sys.stdout, "closed", True):
                    sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
                if sys.stderr is None or getattr(sys.stderr, "closed", True):
                    sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")
        except Exception:
            pass


@dataclass(frozen=True)
class ClientTarget:
    key: str
    name: str
    config_path: Path
    root_key: str
    detected: bool


def _get_antigravity_config_path(home: Path) -> Path:
    """Resolves primary Google Antigravity MCP config path."""
    config_in_config = home / ".gemini" / "config" / "mcp_config.json"
    if config_in_config.exists() or (home / ".gemini" / "config").exists():
        return config_in_config
    return home / ".gemini" / "antigravity" / "mcp_config.json"


def _get_claude_desktop_config_path(app_data: Path, local_app_data: Path) -> Tuple[Path, bool]:
    """Resolves Claude Desktop configuration path, handling both MSIX packages and standard AppData."""
    # 1. Standard AppData Roaming
    standard_cfg = app_data / "Claude" / "claude_desktop_config.json"
    if standard_cfg.exists():
        return standard_cfg, True

    # 2. Windows Store / MSIX Package sandboxed Roaming
    packages_dir = local_app_data / "Packages"
    if packages_dir.is_dir():
        for claude_pkg in packages_dir.glob("Claude_*"):
            candidate = claude_pkg / "LocalCache" / "Roaming" / "Claude" / "claude_desktop_config.json"
            if candidate.exists() or (claude_pkg / "LocalCache" / "Roaming" / "Claude").is_dir():
                return candidate, True

    detected = any([
        (app_data / "Claude").exists(),
        (local_app_data / "Programs" / "Claude" / "Claude.exe").exists(),
        bool(list(packages_dir.glob("Claude_*"))) if packages_dir.is_dir() else False,
    ])
    return standard_cfg, detected


def build_client_targets(
    home: Optional[Path] = None,
    app_data: Optional[Path] = None,
    local_app_data: Optional[Path] = None,
    which: Callable[[str], Optional[str]] = shutil.which,
) -> List[ClientTarget]:
    """Return known per-user MCP configs and whether their client is installed."""
    home = Path(home or Path.home())
    app_data = Path(app_data or os.environ.get("APPDATA", home / "AppData/Roaming"))
    local_app_data = Path(
        local_app_data or os.environ.get("LOCALAPPDATA", home / "AppData/Local")
    )
    vscode_user = app_data / "Code" / "User"
    vscode_extensions = home / ".vscode" / "extensions"

    def any_path_exists(*paths: Path) -> bool:
        return any(path.exists() for path in paths)

    def extension_installed(prefix: str) -> bool:
        return bool(list(vscode_extensions.glob(f"{prefix}-*")))

    antigravity_config = _get_antigravity_config_path(home)
    claude_config, claude_detected = _get_claude_desktop_config_path(app_data, local_app_data)

    return [
        ClientTarget(
            "cursor",
            "Cursor",
            home / ".cursor" / "mcp.json",
            "mcpServers",
            any_path_exists(
                home / ".cursor",
                app_data / "Cursor",
                local_app_data / "Programs" / "Cursor" / "Cursor.exe",
            ),
        ),
        ClientTarget(
            "vscode",
            "Visual Studio Code / Copilot",
            home / ".copilot" / "mcp-config.json",
            "mcpServers",
            any_path_exists(
                app_data / "Code",
                local_app_data / "Programs" / "Microsoft VS Code" / "Code.exe",
            )
            or which("code") is not None,
        ),
        ClientTarget(
            "claude-desktop",
            "Claude Desktop",
            claude_config,
            "mcpServers",
            claude_detected,
        ),
        ClientTarget(
            "antigravity",
            "Google Antigravity",
            antigravity_config,
            "mcpServers",
            any_path_exists(
                home / ".gemini" / "config",
                home / ".gemini" / "antigravity",
                local_app_data / "Programs" / "Antigravity" / "Antigravity.exe",
            ),
        ),
        ClientTarget(
            "claude-code",
            "Claude Code",
            home / ".claude.json",
            "mcpServers",
            home.joinpath(".claude.json").exists() or which("claude") is not None,
        ),
        ClientTarget(
            "cline",
            "Cline",
            vscode_user
            / "globalStorage"
            / "saoudrizwan.claude-dev"
            / "settings"
            / "cline_mcp_settings.json",
            "mcpServers",
            (vscode_user / "globalStorage" / "saoudrizwan.claude-dev").exists()
            or extension_installed("saoudrizwan.claude-dev"),
        ),
        ClientTarget(
            "roo-code",
            "Roo Code",
            vscode_user
            / "globalStorage"
            / "rooveterinaryinc.roo-cline"
            / "settings"
            / "mcp_settings.json",
            "mcpServers",
            (vscode_user / "globalStorage" / "rooveterinaryinc.roo-cline").exists()
            or extension_installed("rooveterinaryinc.roo-cline"),
        ),
        ClientTarget(
            "windsurf",
            "Windsurf",
            home / ".codeium" / "windsurf" / "mcp_config.json",
            "mcpServers",
            any_path_exists(
                home / ".codeium" / "windsurf",
                app_data / "Windsurf",
                local_app_data / "Programs" / "Windsurf" / "Windsurf.exe",
            )
            or which("windsurf") is not None,
        ),
        ClientTarget(
            "gemini-cli",
            "Gemini CLI",
            home / ".gemini" / "settings.json",
            "mcpServers",
            home.joinpath(".gemini", "settings.json").exists()
            or which("gemini") is not None,
        ),
    ]


def server_entry(target: ClientTarget, server_path: Path) -> Dict[str, object]:
    """Generates the MCP configuration dictionary block for the target."""
    if server_path.suffix.lower() == ".py":
        entry: Dict[str, object] = {
            "command": sys.executable,
            "args": [str(server_path.resolve())],
        }
    else:
        entry: Dict[str, object] = {
            "command": str(server_path.resolve()),
            "args": [],
        }
    if target.root_key == "servers":
        entry["type"] = "stdio"
    return entry


def _backup_path(path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    return path.with_name(f"{path.name}.backup-{timestamp}")


def merge_server_config(
    target: ClientTarget, server_path: Path, server_name: str = SERVER_NAME
) -> Dict[str, object]:
    """Safely merge one server entry, keeping the rest of the client's config."""
    config: Dict[str, object] = {}
    if target.config_path.exists():
        with target.config_path.open("r", encoding="utf-8-sig") as config_file:
            loaded = json.load(config_file)
        if not isinstance(loaded, dict):
            raise ValueError("Configuration root must be a JSON object")
        config = loaded

    servers = config.get(target.root_key, {})
    if not isinstance(servers, dict):
        raise ValueError(f"'{target.root_key}' must be a JSON object")

    entry = server_entry(target, server_path)
    if servers.get(server_name) == entry:
        return {"status": "unchanged", "backup": None}

    backup = None
    if target.config_path.exists():
        backup = _backup_path(target.config_path)
        shutil.copy2(target.config_path, backup)

    updated_servers = dict(servers)
    updated_servers[server_name] = entry
    config[target.root_key] = updated_servers
    target.config_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=str(target.config_path.parent),
            prefix=f".{target.config_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            json.dump(config, temporary_file, indent=2, ensure_ascii=False)
            temporary_file.write("\n")
            temporary_path = Path(temporary_file.name)
        os.replace(temporary_path, target.config_path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

    # If this is Google Antigravity or Claude Desktop, sync alternate config paths if present
    if target.key == "antigravity":
        _sync_alternate_antigravity_config(target, server_path, server_name)
    elif target.key == "claude-desktop":
        _sync_alternate_claude_desktop_config(target, server_path, server_name)

    return {"status": "installed", "backup": backup}


def _sync_alternate_antigravity_config(
    target: ClientTarget, server_path: Path, server_name: str
) -> None:
    """Keep ~/.gemini/config/mcp_config.json and ~/.gemini/antigravity/mcp_config.json in sync."""
    try:
        home = Path.home()
        alt_paths = [
            home / ".gemini" / "config" / "mcp_config.json",
            home / ".gemini" / "antigravity" / "mcp_config.json",
        ]
        entry = server_entry(target, server_path)
        for alt_path in alt_paths:
            if alt_path.resolve() == target.config_path.resolve():
                continue
            if alt_path.parent.exists():
                cfg: Dict[str, object] = {}
                if alt_path.exists():
                    try:
                        with alt_path.open("r", encoding="utf-8-sig") as fp:
                            cfg = json.load(fp)
                    except Exception:
                        continue
                if not isinstance(cfg, dict):
                    cfg = {}
                servers = cfg.setdefault("mcpServers", {})
                if isinstance(servers, dict) and servers.get(server_name) != entry:
                    servers[server_name] = entry
                    alt_path.parent.mkdir(parents=True, exist_ok=True)
                    with alt_path.open("w", encoding="utf-8") as fp:
                        json.dump(cfg, fp, indent=2, ensure_ascii=False)
                        fp.write("\n")
    except Exception:
        pass


def _sync_alternate_claude_desktop_config(
    target: ClientTarget, server_path: Path, server_name: str
) -> None:
    """Keep standard AppData and Windows Store / MSIX Claude configs in sync."""
    try:
        home = Path.home()
        app_data = Path(os.environ.get("APPDATA", home / "AppData/Roaming"))
        local_app_data = Path(os.environ.get("LOCALAPPDATA", home / "AppData/Local"))
        entry = server_entry(target, server_path)
        candidates = [app_data / "Claude" / "claude_desktop_config.json"]
        packages_dir = local_app_data / "Packages"
        if packages_dir.is_dir():
            for claude_pkg in packages_dir.glob("Claude_*"):
                candidates.append(
                    claude_pkg / "LocalCache" / "Roaming" / "Claude" / "claude_desktop_config.json"
                )
        for alt_path in candidates:
            if alt_path.resolve() == target.config_path.resolve():
                continue
            if alt_path.exists() or alt_path.parent.is_dir():
                cfg: Dict[str, object] = {}
                if alt_path.exists():
                    try:
                        with alt_path.open("r", encoding="utf-8-sig") as fp:
                            cfg = json.load(fp)
                    except Exception:
                        continue
                if not isinstance(cfg, dict):
                    cfg = {}
                servers = cfg.setdefault("mcpServers", {})
                if isinstance(servers, dict) and servers.get(server_name) != entry:
                    servers[server_name] = entry
                    alt_path.parent.mkdir(parents=True, exist_ok=True)
                    with alt_path.open("w", encoding="utf-8") as fp:
                        json.dump(cfg, fp, indent=2, ensure_ascii=False)
                        fp.write("\n")
    except Exception:
        pass


def _resource_path(filename: str) -> Path:
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    path = bundle_root / filename
    if path.is_file():
        return path
    for cand in [
        bundle_root / "dist" / filename,
        Path.cwd() / "dist" / filename,
        Path.cwd() / filename,
        Path(__file__).resolve().parent / "dist" / filename,
    ]:
        if cand.is_file():
            return cand
    return path


def _install_server_binary(
    source: Path, local_app_data: Optional[Path] = None
) -> Path:
    if not source.is_file():
        raise FileNotFoundError(f"Bundled MCP server not found: {source}")

    local_app_data = Path(
        local_app_data or os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")
    )
    destination = local_app_data / "TZeroAlgorithm" / SERVER_FILENAME
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists() and _sha256(source) == _sha256(destination):
        return destination

    if destination.exists():
        shutil.copy2(destination, _backup_path(destination))

    temporary_path = destination.with_name(f".{destination.name}.tmp")
    try:
        shutil.copy2(source, temporary_path)
        os.replace(temporary_path, destination)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    return destination


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_and_install_server() -> Path:
    """Finds TZeroMCP binary or falls back to tzero_mcp.py script."""
    # 1. Check for bundled or built binary
    primary = _resource_path(SERVER_FILENAME)
    if primary.is_file():
        try:
            return _install_server_binary(primary)
        except Exception:
            return primary

    # 2. Candidate folders
    root = Path(__file__).resolve().parent
    for cand in [
        root / "dist" / SERVER_FILENAME,
        Path.cwd() / "dist" / SERVER_FILENAME,
        Path.cwd() / SERVER_FILENAME,
        root / SERVER_FILENAME,
    ]:
        if cand.is_file():
            try:
                return _install_server_binary(cand)
            except Exception:
                return cand

    # 3. Python script fallback
    for script_cand in [
        root / "tzero_mcp.py",
        Path.cwd() / "tzero_mcp.py",
    ]:
        if script_cand.is_file():
            return script_cand.resolve()

    raise FileNotFoundError(
        f"Neither '{SERVER_FILENAME}' nor 'tzero_mcp.py' could be found."
    )


def install_targets(
    targets: List[ClientTarget],
    log_fn: Optional[Callable[[str], None]] = None,
    server_path: Optional[Path] = None,
) -> Tuple[int, int]:
    """Installs server to specified client targets, returning (successes, failures)."""
    if log_fn is None:
        log_fn = lambda msg: print(f"[T-Zero MCP] {msg}")

    if server_path is None:
        server_path = resolve_and_install_server()

    log_fn(f"Runtime resolved: {server_path}")
    successes = 0
    failures = 0
    for target in targets:
        try:
            result = merge_server_config(target, server_path)
            status = str(result["status"]).capitalize()
            log_fn(f"{status}: {target.name} -> {target.config_path}")
            if result.get("backup"):
                log_fn(f"Backup created: {result['backup']}")
            successes += 1
        except Exception as error:
            failures += 1
            log_fn(f"Failed for {target.name}: {error}")

    return successes, failures


class AddMCPApp:
    def __init__(self, root: object):
        import tkinter as tk
        from tkinter import ttk
        self.root = root  # type: ignore
        self.targets = build_client_targets()
        self.check_vars: Dict[str, tk.BooleanVar] = {}
        self.root.title("T-Zero MCP Installer")
        self.root.geometry("720x650")
        self.root.minsize(600, 540)
        self.root.configure(bg="#11151c")

        icon_path = _resource_path("siber_akademi.ico")
        if icon_path.is_file():
            try:
                self.root.iconbitmap(str(icon_path))
            except Exception:
                pass

        self._create_widgets()

    def _create_widgets(self) -> None:
        import tkinter as tk
        from tkinter import ttk

        container = tk.Frame(self.root, bg="#11151c", padx=24, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="SIBER AKADEMI  /  T-ZERO MCP",
            bg="#11151c",
            fg="#22d3ee",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")
        tk.Label(
            container,
            text="Install the bundled local MCP server in supported IDE configurations.",
            bg="#11151c",
            fg="#cbd5e1",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(5, 14))

        self.detected_label = tk.Label(
            container,
            text="Detected clients are selected by default. Existing config files are backed up before changes.",
            bg="#11151c",
            fg="#94a3b8",
            font=("Segoe UI", 9),
            wraplength=660,
            justify="left",
        )
        self.detected_label.pack(anchor="w", pady=(0, 8))

        list_frame = tk.Frame(container, bg="#1a202b", padx=12, pady=8)
        list_frame.pack(fill=tk.BOTH, expand=True)
        for target in self.targets:
            state = "Detected" if target.detected else "Not detected"
            variable = tk.BooleanVar(value=target.detected)
            self.check_vars[target.key] = variable
            row = tk.Frame(list_frame, bg="#1a202b")
            row.pack(fill=tk.X, pady=2)
            tk.Checkbutton(
                row,
                text=target.name,
                variable=variable,
                bg="#1a202b",
                fg="#f1f5f9",
                activebackground="#1a202b",
                activeforeground="#f1f5f9",
                selectcolor="#0f172a",
                font=("Segoe UI", 10),
            ).pack(side=tk.LEFT)
            tk.Label(
                row,
                text=state,
                bg="#1a202b",
                fg="#4ade80" if target.detected else "#64748b",
                font=("Segoe UI", 9),
            ).pack(side=tk.RIGHT, padx=6)

        self.log_text = tk.Text(
            container,
            height=7,
            bg="#080b10",
            fg="#a5f3fc",
            insertbackground="#f8fafc",
            relief=tk.FLAT,
            font=("Consolas", 9),
            state=tk.DISABLED,
        )
        self.log_text.pack(fill=tk.BOTH, expand=False, pady=(12, 8))

        buttons = tk.Frame(container, bg="#11151c")
        buttons.pack(fill=tk.X)
        ttk.Button(buttons, text="Select all", command=self._select_all).pack(side=tk.LEFT)
        self.install_button = ttk.Button(
            buttons, text="Install to selected IDEs", command=self.install_selected
        )
        self.install_button.pack(side=tk.RIGHT)

        tk.Label(
            container,
            text="Zero configuration required. Restart IDEs after installation.",
            bg="#11151c",
            fg="#94a3b8",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(10, 0))

    def _select_all(self) -> None:
        for variable in self.check_vars.values():
            variable.set(True)

    def _log(self, message: str) -> None:
        import tkinter as tk
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def install_selected(self) -> None:
        import tkinter as tk
        from tkinter import messagebox

        selected = [
            target for target in self.targets if self.check_vars[target.key].get()
        ]
        if not selected:
            messagebox.showwarning("T-Zero MCP Installer", "Select at least one client.")
            return

        self.install_button.configure(state=tk.DISABLED)
        try:
            successes, failures = install_targets(selected, log_fn=self._log)
            message = f"Configured {successes} client(s)."
            if failures:
                message += f" {failures} client(s) were skipped; see log."
            messagebox.showinfo("T-Zero MCP Installer", message)
        except Exception as error:
            self._log(f"Installer failed: {error}")
            messagebox.showerror("T-Zero MCP Installer", f"Installer failed: {error}")
        finally:
            self.install_button.configure(state=tk.NORMAL)


def run_cli() -> int:
    """Executes the CLI interface when called from command line or with flags."""
    _attach_windows_console()

    parser = argparse.ArgumentParser(
        prog="addmcp",
        description="T-Zero MCP 1-Click Installer for Cursor, Claude Desktop, Antigravity, VS Code, Windsurf, etc."
    )
    parser.add_argument(
        "--all", "-a", action="store_true",
        help="Install into all detected IDEs without GUI."
    )
    parser.add_argument(
        "--targets", "-t", metavar="KEYS",
        help="Comma-separated list of target keys to install to (e.g. cursor,claude-desktop,antigravity)."
    )
    parser.add_argument(
        "--list", "-l", action="store_true",
        help="List all supported and detected IDE targets."
    )
    parser.add_argument(
        "--gui", "-g", action="store_true",
        help="Explicitly launch the GUI installer window."
    )
    parser.add_argument(
        "--version", "-v", action="version",
        version=f"T-Zero MCP Installer {APP_VERSION}"
    )

    args, unknown = parser.parse_known_args()
    all_targets = build_client_targets()

    if args.list:
        print(f"\n[T-Zero MCP Installer v{APP_VERSION}] Available IDE Targets:\n")
        for t in all_targets:
            state = "DETECTED" if t.detected else "not found"
            print(f"  [{state:^9}] {t.key:<15} : {t.name} ({t.config_path})")
        print()
        return 0

    if args.all or args.targets:
        if args.all:
            selected = [t for t in all_targets if t.detected]
            if not selected:
                print("[T-Zero MCP] No installed IDE clients detected automatically.")
                selected = all_targets
        else:
            keys = [k.strip().lower() for k in args.targets.split(",")]
            selected = [t for t in all_targets if t.key.lower() in keys]

        if not selected:
            print("[T-Zero MCP] No valid targets matched.")
            return 1

        print(f"\n[T-Zero MCP Installer v{APP_VERSION}] Installing to {len(selected)} target(s)...")
        successes, failures = install_targets(selected, log_fn=lambda m: print(f"  -> {m}"))
        print(f"[T-Zero MCP] Completed: {successes} configured, {failures} failed.\n")
        return 0 if failures == 0 else 1

    # Default action: launch GUI if display available, otherwise list targets
    try:
        import tkinter as tk
        root = tk.Tk()
        AddMCPApp(root)
        root.mainloop()
        return 0
    except Exception as e:
        print(f"[T-Zero MCP] GUI unavailable ({e}). Defaulting to automatic CLI install:")
        selected = [t for t in all_targets if t.detected]
        if not selected:
            selected = all_targets
        successes, failures = install_targets(selected, log_fn=lambda m: print(f"  -> {m}"))
        return 0 if failures == 0 else 1


def main() -> None:
    sys.exit(run_cli())


if __name__ == "__main__":
    main()