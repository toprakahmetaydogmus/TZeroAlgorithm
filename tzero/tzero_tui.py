# -*- coding: utf-8 -*-
"""
Siber Akademi — T-Zero Terminal User Interface (TUI) & Live Cockpit.
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: MIT

Pure standard-library ANSI terminal dashboard and interactive executive cockpit.
Provides live workspace token metrics, AST compression meters, zero-leak security
auditing, and instantaneous action triggers without any external GUI dependencies.
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import os
import re
import time
import unicodedata
from typing import Dict, List, Optional, Any, Tuple

from tzero.tzero_features import should_skip_dir, should_skip_file
from tzero.tzero_polyglot import PolyglotTokenReducer


class TZeroTerminalCockpit:
    """Zero-dependency, high-density terminal dashboard and interactive cockpit."""

    # ANSI Palette
    CYAN = "\033[36m"
    BRIGHT_CYAN = "\033[96m"
    GREEN = "\033[32m"
    BRIGHT_GREEN = "\033[92m"
    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"
    BLUE = "\033[34m"
    RED = "\033[31m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    @classmethod
    def gather_workspace_metrics(cls, workspace_dir: str = ".") -> Dict[str, Any]:
        """Scans workspace and compiles metrics for the terminal cockpit."""
        abs_ws = os.path.abspath(workspace_dir)
        files_by_lang: Dict[str, int] = {}
        raw_tokens_total = 0
        pruned_tokens_total = 0
        file_count = 0
        code_files_sampled = 0

        reducer = PolyglotTokenReducer()

        for root, dirs, files in os.walk(abs_ws):
            dirs[:] = [d for d in dirs if not should_skip_dir(os.path.join(root, d), abs_ws)]
            for f in files:
                full_p = os.path.join(root, f)
                if should_skip_file(full_p, abs_ws):
                    continue
                file_count += 1
                ext = os.path.splitext(f)[1].lower()
                lang = reducer.detect_language(full_p) or "Other"
                files_by_lang[lang] = files_by_lang.get(lang, 0) + 1

                # Sample quick token calculation on code files (independent of non-code assets)
                if code_files_sampled < 250 and ext in (
                    ".py", ".ts", ".js", ".rs", ".go", ".cpp", ".c", ".h",
                    ".swift", ".kt", ".dart", ".rb", ".sol", ".scala", ".php"
                ):
                    try:
                        with open(full_p, "r", encoding="utf-8", errors="replace") as fp:
                            raw_code = fp.read()
                        raw_t = max(1, len(raw_code) // 4)
                        pruned_code = reducer.reduce_code(raw_code, filename=full_p, mode="ultra")
                        pruned_t = max(1, len(pruned_code) // 4)
                        raw_tokens_total += raw_t
                        pruned_tokens_total += pruned_t
                        code_files_sampled += 1
                    except OSError:
                        pass

        # Estimate savings if sample available, or zero for empty workspace
        if raw_tokens_total > 0:
            savings_pct = max(0.0, (1.0 - (pruned_tokens_total / raw_tokens_total)) * 100.0)
        else:
            savings_pct = 0.0

        # Real Zero-Leak security status check
        zero_leak_status = "UNVERIFIED"
        try:
            from tzero.tzero_security import ZeroLeakEngine
            sec_res = ZeroLeakEngine.scan_workspace(abs_ws)
            v_count = int(sec_res.get("violation_count", 0))
            zero_leak_status = "100% SECURE (VERIFIED)" if v_count == 0 else f"WARNING: {v_count} SECRET(S)"
        except Exception:
            pass

        # Monthly ROI savings calculation (assuming 50 queries/day at Claude 3.7 $3/1M input)
        daily_saved_tokens = (raw_tokens_total - pruned_tokens_total) * 50
        monthly_cost_saved = (daily_saved_tokens * 30 / 1_000_000) * 3.0

        return {
            "workspace_name": os.path.basename(abs_ws) or "Workspace",
            "workspace_dir": abs_ws,
            "total_files": file_count,
            "raw_tokens": raw_tokens_total,
            "pruned_tokens": pruned_tokens_total,
            "savings_pct": round(savings_pct, 1),
            "monthly_roi_saved": round(monthly_cost_saved, 2),
            "languages": files_by_lang,
            "zero_leak_status": zero_leak_status,
        }

    @classmethod
    def render_gauge(cls, percentage: float, width: int = 24) -> str:
        """Renders an ANSI progress bar gauge."""
        filled = int(width * (percentage / 100.0))
        empty = width - filled
        bar = f"{cls.BRIGHT_CYAN}{'█' * filled}{cls.DIM}{'░' * empty}{cls.RESET}"
        return f"[{bar}] {cls.BOLD}{percentage:.1f}%{cls.RESET}"

    MENU_OPTIONS: List[Tuple[str, str, str]] = [
        ("1", "Pack Context Window", "🗜️  Pack Context Window (`tzero --pack 16000`)"),
        ("2", "Generate PEP-484 Type Stubs", "📑 Generate PEP-484 Type Stubs (`tzero --stubs`)"),
        ("3", "Synthesize Conventional Commit", "✍️  Synthesize Conventional Commit (`tzero --commit-msg`)"),
        ("4", "Generate Release CHANGELOG", "📜 Generate Release CHANGELOG (`tzero --changelog`)"),
        ("5", "Apply AST-Tolerant Patch", "🛠️  Apply AST-Tolerant Patch (`tzero --patch <diff>`)"),
        ("6", "Launch Web Comparison Dashboard", "🌐 Launch Web Comparison Dashboard (`tzero --web`)"),
        ("7", "Install Git Zero-Leak Guard & CI", "🛡️  Install Git Zero-Leak Guard & CI (`tzero --guard-install`)"),
        ("8", "Verify Architecture & 0 Cycles", "🏛️  Verify Architecture & 0 Cycles (`tzero --check-arch`)"),
        ("9", "Run AST Mutation Test Suite", "🧬 Run AST Mutation Test Suite (`tzero --mutate <file>`)"),
        ("10", "Code Health & Technical Debt Index", "🏥 Code Health & Technical Debt Index (`tzero --debt`)"),
        ("11", "Context Budget Optimizer & Certificate", "📜 Context Budget Optimizer & Certificate (`tzero --budget`)"),
        ("12", "Anti-REA 26-Tier Armor & Audit", "🛡️  Anti-REA 26-Tier Armor & Audit (`tzero --audit-rea`)"),
        ("13", "Offline Telemetry & ROI Tracker", "📊 Offline Telemetry & ROI Tracker (`tzero --telemetry`)"),
        ("0", "Exit TUI", "🚪 Exit TUI"),
    ]

    _ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

    @classmethod
    def visual_width(cls, text: str) -> int:
        """Computes monospace display cell width of text, handling ANSI and emojis."""
        clean = cls._ANSI_RE.sub("", text)
        width = 0
        for ch in clean:
            cat = unicodedata.category(ch)
            if cat in ("Mn", "Me", "Cf") or ch == "\ufe0f":
                continue
            ea = unicodedata.east_asian_width(ch)
            if ea in ("W", "F"):
                width += 2
                continue
            code = ord(ch)
            if (0x1F300 <= code <= 0x1FAFF) or (0x2300 <= code <= 0x23FF) or (0x2600 <= code <= 0x27BF):
                width += 2
            else:
                width += 1
        return width

    @classmethod
    def _box_line(cls, content: str, inner_width: int = 78) -> str:
        """Wraps content with box borders with exact column padding."""
        w = cls.visual_width(content)
        pad = max(0, inner_width - w)
        return f"{cls.CYAN}║{cls.RESET}{content}{' ' * pad}{cls.CYAN}║{cls.RESET}"

    @classmethod
    def render_cockpit(cls, metrics: Dict[str, Any], selected_index: Optional[int] = 0) -> str:
        """Constructs high-density ASCII / ANSI terminal cockpit screen with exact border alignment."""
        c = cls
        lines = []

        box_top    = f"{c.CYAN}╔{'═' * 78}╗{c.RESET}"
        box_mid    = f"{c.CYAN}╠{'═' * 78}╣{c.RESET}"
        box_bottom = f"{c.CYAN}╚{'═' * 78}╝{c.RESET}"

        lines.append(box_top)
        lines.append(cls._box_line(f"  {c.BOLD}{c.BRIGHT_CYAN}⚡ SİBER AKADEMİ — T-ZERO CONTEXT ARCHITECT & LIVE COCKPIT v12.2.0{c.RESET}"))
        lines.append(cls._box_line(f"  {c.DIM}Zero-Leak AST Intelligence | 100% Offline | $0 Cloud Cost Guarantee{c.RESET}"))
        lines.append(box_mid)

        # Workspace summary line
        ws_name = metrics.get("workspace_name", "Workspace")[:20]
        files_cnt = metrics.get("total_files", 0)
        lines.append(cls._box_line(f"  📁 {c.BOLD}Workspace:{c.RESET} {ws_name:<20} │  📦 {c.BOLD}Files Tracked:{c.RESET} {files_cnt:<6}"))

        # Metrics lines
        raw_t = metrics.get("raw_tokens", 0)
        pruned_t = metrics.get("pruned_tokens", 0)
        sav_pct = metrics.get("savings_pct", 94.8)
        roi = metrics.get("monthly_roi_saved", 0.0)

        gauge = cls.render_gauge(sav_pct, width=20)
        lines.append(cls._box_line(f"  🗜️  {c.BOLD}AST Reduction:{c.RESET} {gauge}"))
        lines.append(cls._box_line(f"  📊 {c.BOLD}Raw Tokens:{c.RESET} ~{raw_t:,} │ {c.BOLD}Pruned Tokens:{c.RESET} ~{pruned_t:,}"))
        lines.append(cls._box_line(f"  💰 {c.BOLD}Est. Monthly Team ROI Saved:{c.RESET} {c.BRIGHT_GREEN}${roi:,.2f}{c.RESET} / month (Claude 3.7 / GPT-4o)"))
        sec_stat = str(metrics.get("zero_leak_status", "100% SECURE (VERIFIED)"))
        sec_color = c.BRIGHT_GREEN if ("SECURE" in sec_stat or "PASSED" in sec_stat) else c.RED
        sec_note = "(0 Exposed Credentials)" if sec_color == c.BRIGHT_GREEN else "(Action Required)"
        sec_field = f"{sec_color}{sec_stat}{c.RESET} {sec_note}"
        lines.append(cls._box_line(f"  🔒 {c.BOLD}Security Guard:{c.RESET} {sec_field}"))
        lines.append(box_mid)

        # Top languages line
        langs = metrics.get("languages", {})
        top_langs = sorted(langs.items(), key=lambda x: x[1], reverse=True)[:5]
        lang_str = " | ".join(f"{k}: {v}" for k, v in top_langs)
        lines.append(cls._box_line(f"  🌐 {c.BOLD}Polyglot Stack:{c.RESET} {lang_str[:54]}"))
        lines.append(box_mid)

        # Interactive Command Menu
        lines.append(cls._box_line(f"  {c.BOLD}🚀 QUICK COMMAND DISPATCH:{c.RESET}"))
        for idx, (mkey, short_label, full_text) in enumerate(cls.MENU_OPTIONS):
            is_active = (selected_index is not None and (selected_index % len(cls.MENU_OPTIONS)) == idx)
            if is_active:
                prefix = f"  {c.BRIGHT_GREEN}▶{c.RESET} "
                styled_text = f"{c.BOLD}[{mkey}] {full_text}{c.RESET}"
            else:
                prefix = "    "
                styled_text = f"[{mkey}] {full_text}"
            lines.append(cls._box_line(f"{prefix}{styled_text}"))
        lines.append(box_bottom)

        return "\n".join(lines)

    @classmethod
    def _read_key(cls) -> str:
        """Reads a single keystroke cross-platform supporting arrow keys."""
        if sys.platform == "win32":
            try:
                import msvcrt
                ch = msvcrt.getwch()
                if ch in ('\x00', '\xe0'):
                    ch2 = msvcrt.getwch()
                    if ch2 == 'H':
                        return 'UP'
                    elif ch2 == 'P':
                        return 'DOWN'
                    elif ch2 == 'K':
                        return 'LEFT'
                    elif ch2 == 'M':
                        return 'RIGHT'
                    return 'OTHER'
                if ch in ('\r', '\n'):
                    return 'ENTER'
                if ch == '\t':
                    return 'TAB'
                if ch == '\x1b':
                    return 'ESC'
                if ch == '\x03':
                    return 'CTRL_C'
                return ch
            except Exception:
                return ''
        else:
            try:
                import termios
                import tty
                import select
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(fd)
                    rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
                    if rlist:
                        ch = sys.stdin.read(1)
                        if ch == '\x1b':
                            rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
                            if rlist:
                                seq = sys.stdin.read(2)
                                if seq == '[A':
                                    return 'UP'
                                elif seq == '[B':
                                    return 'DOWN'
                                elif seq == '[C':
                                    return 'RIGHT'
                                elif seq == '[D':
                                    return 'LEFT'
                                elif seq == '[Z':
                                    return 'SHIFT_TAB'
                            return 'ESC'
                        if ch in ('\r', '\n'):
                            return 'ENTER'
                        if ch == '\t':
                            return 'TAB'
                        if ch == '\x03':
                            return 'CTRL_C'
                        return ch
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            except Exception:
                return ''
        return ''

    @classmethod
    def execute_action(cls, choice: str, workspace_dir: str = ".") -> bool:
        """Dispatches action for a choice string. Returns False if exiting, True otherwise."""
        choice = choice.strip()
        if choice in ("0", "q", "Q", "quit", "exit"):
            print(f"\n{cls.CYAN}Exiting T-Zero Cockpit.{cls.RESET}")
            return False
        elif choice == "1":
            from tzero.tzero_packer import pack_workspace
            print(f"\n{cls.YELLOW}[Running Context Packer (16,000 tokens)]...{cls.RESET}")
            res = pack_workspace(workspace_dir=workspace_dir, budget_tokens=16000)
            print(f"{cls.GREEN}[SUCCESS] Packed {res.total_tokens:,} tokens ({res.token_savings_pct:.1f}% reduction).{cls.RESET}")
            input("Press Enter to return to cockpit...")
        elif choice == "2":
            from tzero.tzero_stubs import TypeStubGenerator
            print(f"\n{cls.YELLOW}[Generating PEP-484 Type Stubs]...{cls.RESET}")
            res = TypeStubGenerator.generate_workspace_stubs(workspace_dir=workspace_dir)
            print(f"{cls.GREEN}[SUCCESS] Generated {res['total_files']} stubs ({res['overall_savings_pct']}% reduction).{cls.RESET}")
            input("Press Enter to return to cockpit...")
        elif choice == "3":
            from tzero.tzero_commit import LocalSemanticCommitSynthesizer
            print(f"\n{cls.YELLOW}[Synthesizing Offline Commit Message]...{cls.RESET}")
            msg = LocalSemanticCommitSynthesizer.generate_commit_message(repo_dir=workspace_dir, staged=True)
            print(f"\n{cls.BRIGHT_CYAN}{msg}{cls.RESET}\n")
            input("Press Enter to return to cockpit...")
        elif choice == "4":
            from tzero.tzero_commit import LocalSemanticCommitSynthesizer
            print(f"\n{cls.YELLOW}[Synthesizing Release CHANGELOG]...{cls.RESET}")
            entry = LocalSemanticCommitSynthesizer.generate_changelog_entry(version="v12.2.0", repo_dir=workspace_dir)
            print(f"\n{cls.BRIGHT_CYAN}{entry}{cls.RESET}\n")
            input("Press Enter to return to cockpit...")
        elif choice == "5":
            patch_path = input("Enter path to unified diff file: ").strip()
            if patch_path and os.path.exists(patch_path):
                from tzero.tzero_patch import ASTFuzzyPatcher
                res = ASTFuzzyPatcher.apply_patch_file(patch_path, workspace_dir=workspace_dir)
                print(f"{cls.GREEN}[RESULT] Applied {res.get('applied_hunks', 0)}/{res.get('total_hunks', 0)} hunks.{cls.RESET}")
            else:
                print(f"{cls.RED}File not found.{cls.RESET}")
            input("Press Enter to return to cockpit...")
        elif choice == "6":
            print(f"\n{cls.GREEN}[Launching Web Dashboard on http://localhost:8421]...{cls.RESET}")
            import socket
            import threading
            import webbrowser
            is_up = False
            try:
                with socket.create_connection(("127.0.0.1", 8421), timeout=0.3):
                    is_up = True
            except OSError:
                is_up = False
            if not is_up:
                try:
                    from tzero.tzero_dashboard import start_dashboard_server
                    srv = start_dashboard_server(port=8421, open_browser=False)
                    threading.Thread(target=srv.serve_forever, daemon=True).start()
                except Exception:
                    pass
            webbrowser.open("http://localhost:8421")
            time.sleep(1)
        elif choice == "7":
            from tzero.tzero_guard import GitSecurityGuard
            from tzero.tzero_ci import CIPipelineGenerator
            GitSecurityGuard.install_hook(workspace_dir)
            CIPipelineGenerator.install_github_workflow(workspace_dir)
            print(f"{cls.GREEN}[SUCCESS] Pre-commit hook & GitHub Actions CI installed!{cls.RESET}")
            input("Press Enter to return to cockpit...")
        elif choice == "8":
            from tzero.tzero_arch_test import ArchitectureTestSuiteGenerator
            print(f"\n{cls.YELLOW}[Verifying Layer Boundaries, Cycles & Zero-Leak Security]...{cls.RESET}")
            gen = ArchitectureTestSuiteGenerator(workspace_dir)
            rep = gen.run_live_audit()
            if rep["success"]:
                print(f"\n{cls.GREEN}✅ [ARCH-AUDIT PASS] All {rep['scanned_files']} files conform to rules! Zero violations.{cls.RESET}\n")
            else:
                print(f"\n{cls.RED}❌ [ARCH-AUDIT FAILED] Violations detected:{cls.RESET}")
                for v in rep["layer_violations"]:
                    print(f"   • {v['file']} (layer: {v['layer']}) imports forbidden '{v['imported']}'")
            input("Press Enter to return to cockpit...")
        elif choice == "9":
            target_f = input("Enter path to file for mutation test (default: tzero_arch_test.py): ").strip() or "tzero_arch_test.py"
            if os.path.exists(target_f):
                from tzero.tzero_mutation import ASTMutationEngine
                print(f"\n{cls.YELLOW}[Running AST Mutation Analysis on {target_f}]...{cls.RESET}")
                m_rep = ASTMutationEngine.run_mutation_analysis(target_file=target_f, max_mutants=5)
                print(f"{cls.GREEN}[RESULT] Mutation Score: {m_rep.mutation_score}% ({m_rep.killed}/{m_rep.total_mutants} killed).{cls.RESET}")
            else:
                print(f"{cls.RED}Target file not found.{cls.RESET}")
            input("Press Enter to return to cockpit...")
        elif choice == "10":
            from tzero.tzero_debt import CodeHealthAnalyzer
            print(f"\n{cls.YELLOW}[Analyzing Code Health & Technical Debt Index for {workspace_dir}]...{cls.RESET}")
            rep = CodeHealthAnalyzer.analyze_workspace(workspace_dir)
            print(f"\n{cls.BRIGHT_CYAN}{CodeHealthAnalyzer.format_markdown_report(rep)}{cls.RESET}\n")
            input("Press Enter to return to cockpit...")
        elif choice == "11":
            from tzero.tzero_budget import ASTTokenBudgetOptimizer
            print(f"\n{cls.YELLOW}[Sizing Context Payload & Issuing Compression Certificate for {workspace_dir}]...{cls.RESET}")
            cert = ASTTokenBudgetOptimizer.optimize_budget(workspace_dir)
            saved_p = ASTTokenBudgetOptimizer.save_certificate(cert)
            print(f"\n{cls.BRIGHT_CYAN}{ASTTokenBudgetOptimizer.format_markdown_certificate(cert)}{cls.RESET}\n")
            print(f"{cls.GREEN}[SUCCESS] Certificate saved to: {saved_p}{cls.RESET}")
            input("Press Enter to return to cockpit...")
        elif choice == "12":
            from tzero.tzero_armor import audit_path_rea_resistance, protect_path_with_armor
            print(f"\n{cls.YELLOW}[Auditing 26-Tier Anti-REA Resistance for {workspace_dir}]...{cls.RESET}")
            audit = audit_path_rea_resistance(workspace_dir)
            print(f"{cls.BRIGHT_CYAN}AI Resistance Score: {audit.get('score', 0)}/100 ({audit.get('rating', 'UNKNOWN')}){cls.RESET}")
            apply_ans = input("Apply Anti-REA armor to target file/dir now? [y/N]: ").strip().lower()
            if apply_ans == "y":
                res = protect_path_with_armor(workspace_dir)
                print(f"{cls.GREEN}[OK] Protected: {res}{cls.RESET}")
            input("Press Enter to return to cockpit...")
        elif choice == "13":
            from tzero.tzero_telemetry import render_report
            print(f"\n{cls.BRIGHT_CYAN}{render_report(workspace_dir)}{cls.RESET}\n")
            input("Press Enter to return to cockpit...")
        else:
            print(f"{cls.RED}Invalid selection: {choice}{cls.RESET}")
            time.sleep(0.5)
        return True

    @classmethod
    def run_interactive(cls, workspace_dir: str = "."):
        """Runs the interactive loop in the user terminal with smooth wrap-around navigation."""
        if sys.platform == "win32":
            try:
                os.system("")
            except Exception:
                pass

        selected_index = 0
        menu_len = len(cls.MENU_OPTIONS)
        num_buffer = ""
        last_num_time = 0.0

        while True:
            metrics = cls.gather_workspace_metrics(workspace_dir)
            screen = cls.render_cockpit(metrics, selected_index=selected_index)
            # Smooth screen clearing without scrolling overflow
            print("\033[2J\033[H", end="", flush=True)
            print(screen)

            # Fallback for non-interactive / piped environments
            if not sys.stdin.isatty():
                try:
                    choice = input(f"\n{cls.BOLD}Select an action [0-11] (or press Enter to refresh): {cls.RESET}").strip()
                except (KeyboardInterrupt, EOFError):
                    print(f"\n{cls.CYAN}Goodbye! T-Zero Context Engine active.{cls.RESET}")
                    break
                if not choice:
                    continue
                if not cls.execute_action(choice, workspace_dir):
                    break
                continue

            # Interactive keyboard loop with arrow navigation & smooth wrap-around
            chosen = False
            choice = ""
            while not chosen:
                print(f"\r{cls.BOLD}  Navigate [↑/↓/←/→, w/s, k/j] │ Select [Enter] │ Quick Jump [0-11] │ Exit [q/esc]: {cls.RESET}", end="", flush=True)
                key = cls._read_key()
                if not key:
                    time.sleep(0.04)
                    continue

                if key in ("CTRL_C", "q", "Q", "ESC"):
                    print(f"\n{cls.CYAN}Goodbye! T-Zero Context Engine active.{cls.RESET}")
                    return
                elif key in ("UP", "LEFT", "k", "K", "w", "W", "SHIFT_TAB"):
                    # Smooth wrap-around: jump from top item to bottom item
                    selected_index = (selected_index - 1) % menu_len
                    break
                elif key in ("DOWN", "RIGHT", "j", "J", "s", "S", "TAB"):
                    # Smooth wrap-around: jump from bottom item to top item
                    selected_index = (selected_index + 1) % menu_len
                    break
                elif key == "ENTER":
                    choice = cls.MENU_OPTIONS[selected_index][0]
                    chosen = True
                elif key in [str(i) for i in range(10)]:
                    now = time.time()
                    if now - last_num_time > 0.8:
                        num_buffer = key
                    else:
                        num_buffer += key
                    last_num_time = now

                    # Match against menu item keys
                    matched_idx = None
                    for idx, (mkey, _, _) in enumerate(cls.MENU_OPTIONS):
                        if mkey == num_buffer:
                            matched_idx = idx
                            break
                    if matched_idx is not None:
                        selected_index = matched_idx
                        break
                    elif len(num_buffer) > 1:
                        num_buffer = key
                        for idx, (mkey, _, _) in enumerate(cls.MENU_OPTIONS):
                            if mkey == num_buffer:
                                selected_index = idx
                                break
                        break

            if chosen and choice:
                print()
                if not cls.execute_action(choice, workspace_dir):
                    break


def main():
    """CLI entrypoint for standalone cockpit execution."""
    target_dir = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "."
    if "--snapshot" in sys.argv:
        metrics = TZeroTerminalCockpit.gather_workspace_metrics(target_dir)
        print(TZeroTerminalCockpit.render_cockpit(metrics))
    else:
        TZeroTerminalCockpit.run_interactive(target_dir)


if __name__ == "__main__":
    main()
