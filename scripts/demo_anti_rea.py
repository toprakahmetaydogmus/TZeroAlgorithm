# -*- coding: utf-8 -*-
"""Interactive Terminal Demonstration: Unprotected vs Anti-REA Protected Executable.

Simulates reverse-engineering attacks against unshielded vs shielded targets.

Usage:
  python scripts/demo_anti_rea.py
"""

import sys
import time

# Colors
C_RESET = "\033[0m"
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_CYAN = "\033[96m"
C_BOLD = "\033[1m"


def slow_print(text, delay=0.015, color=""):
    print(color, end="")
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print(C_RESET)


def main():
    print(f"\n{C_BOLD}{C_CYAN}{'='*72}")
    print(" SIBER AKADEMI T-ZERO: ANTI-REA (26-TIER DEFENSE) TERMINAL DEMO")
    print(f"{'='*72}{C_RESET}\n")

    time.sleep(0.4)
    print(f"{C_BOLD}[SCENARIO 1] ATTACK ON STANDARD (UNPROTECTED) PYINSTALLER BINARY{C_RESET}")
    print("-" * 72)
    slow_print("[*] Target: dist/myapp_unprotected.exe", 0.01, C_CYAN)
    slow_print("[*] Launching: pyinstxtractor.py dist/myapp_unprotected.exe", 0.01, C_YELLOW)
    time.sleep(0.3)
    slow_print("[+] PyInstaller magic cookie 'MEIPASS2' detected at offset 0x004F8A0.", 0.01, C_YELLOW)
    slow_print("[+] Reading archive header length (184,290 bytes)...", 0.01, C_YELLOW)
    slow_print("[+] Extracting 148 embedded .pyc bytecode modules to disk...", 0.01, C_YELLOW)
    time.sleep(0.4)
    slow_print("[!] Decompiling core_logic.pyc with uncompyle6 / REA LLM Agent...", 0.01, C_RED)
    slow_print("[!] DISASTER: 100% of proprietary code, API tokens, and weights recovered!", 0.01, C_RED)
    slow_print("    Result: VULNERABLE — REVERSED IN 0.32 SECONDS.\n", 0.01, C_RED)

    time.sleep(0.8)
    print(f"{C_BOLD}[SCENARIO 2] ATTACK ON ANTI-REA v4.1.0 ARMORED BINARY{C_RESET}")
    print("-" * 72)
    slow_print("[*] Target: dist/TZeroAlgorithm.exe (Armored with 26-Tier Anti-REA)", 0.01, C_CYAN)
    slow_print("[*] Launching: pyinstxtractor.py dist/TZeroAlgorithm.exe", 0.01, C_YELLOW)
    time.sleep(0.3)
    slow_print("[*] Extractor inspecting PE overlay padding...", 0.01, C_YELLOW)
    time.sleep(0.4)
    slow_print(">>> [DEFENSE TRIGGERED] Tier 1: ExtractorShield Decoy Header Encountered!", 0.01, C_GREEN)
    slow_print("    pyinstxtractor Error: EOFError: Unexpected EOF while reading archive table.", 0.01, C_RED)
    slow_print("    [BLOCKED] pyinstxtractor crashed without extracting a single file.", 0.01, C_GREEN)
    
    time.sleep(0.5)
    slow_print("\n[*] Attacker fallback: Attaching x64dbg & IDA Pro debugger (F8 Single-Step)...", 0.01, C_YELLOW)
    time.sleep(0.4)
    slow_print(">>> [DEFENSE TRIGGERED] Tier 26: RDTSC Instruction Cycle Delta Variance > 50ms!", 0.01, C_GREEN)
    slow_print(">>> [DEFENSE TRIGGERED] Tier 21: Ring-3 IsDebuggerPresent & NtGlobalFlag (0x70) detected!", 0.01, C_GREEN)
    slow_print("    Process Hard Terminated: ExitCode 0xC0000409 (STATUS_STACK_BUFFER_OVERRUN)", 0.01, C_RED)
    slow_print("    [BLOCKED] Debugger disconnected. Zero instructions stepped.", 0.01, C_GREEN)

    time.sleep(0.5)
    slow_print("\n[*] Attacker fallback: Autonomous AI Agent (morluto/rea) AST Ingestion...", 0.01, C_YELLOW)
    time.sleep(0.4)
    slow_print(">>> [DEFENSE TRIGGERED] Tier 15: Cognitive Honeypot & Infinite Recursion AST Trap!", 0.01, C_GREEN)
    slow_print(">>> [DEFENSE TRIGGERED] Tier 23: In-Flight String Vault (Zero plaintext in RAM)!", 0.01, C_GREEN)
    slow_print("    Agent Result: ContextExhaustionError: Recursion loop exceeded token limit.", 0.01, C_RED)

    print(f"\n{C_BOLD}{C_GREEN}{'='*72}")
    print(" VERDICT: 100% DEFENSE SUCCESS — ALL EXPLOIT VECTORS NEUTRALIZED")
    print(" SECURITY RATING: MILITARY_GRADE_IMPREGNABLE")
    print(f"{'='*72}{C_RESET}\n")


if __name__ == "__main__":
    main()
