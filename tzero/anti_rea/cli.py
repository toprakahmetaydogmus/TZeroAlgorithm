# -*- coding: utf-8 -*-
"""Command-Line Interface for Anti-REA.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

import sys
import argparse
import json
from pathlib import Path

from .engine import AntiREAEngine
from .auditor import AIResistanceAuditor
from .extractor_shield import ExtractorShield
from .traps import AdversarialTrapGenerator


def main():
    """Main CLI entry point for anti-rea."""
    parser = argparse.ArgumentParser(
        prog="anti-rea",
        description="Anti-REA: Military-grade defense engine against AI reverse engineering (morluto/rea, Ghidra MCP) and jailbroken LLMs."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: protect
    protect_parser = subparsers.add_parser("protect", help="Hardens Python source file with Anti-REA defense matrix.")
    protect_parser.add_argument("path", help="Path to Python file to protect.")
    protect_parser.add_argument("-o", "--output", help="Output path (default: overwrite original).")
    protect_parser.add_argument("--no-flatten", action="store_true", help="Disable control-flow flattening.")
    protect_parser.add_argument("--no-chaff", action="store_true", help="Disable semantic token chaff.")
    protect_parser.add_argument("--no-vm", action="store_true", help="Disable dynamic PolyVM container.")
    protect_parser.add_argument("--no-jailbreak-decoy", action="store_true", help="Disable cognitive jailbreak decoys.")
    protect_parser.add_argument("--seed", type=int, default=42, help="Random seed for polymorphic passes.")

    # Command: shield-exe
    shield_parser = subparsers.add_parser("shield-exe", help="Shields compiled PyInstaller .exe against pyinstxtractor.")
    shield_parser.add_argument("exe_path", help="Path to executable binary.")
    shield_parser.add_argument("-o", "--output", help="Output path for shielded binary.")

    # Command: audit
    audit_parser = subparsers.add_parser("audit", help="Audits target file for resistance against AI reverse engineering (0-100).")
    audit_parser.add_argument("path", help="Path to file to audit.")
    audit_parser.add_argument("--json", action="store_true", help="Output raw JSON.")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "protect":
        res = AntiREAEngine.protect_file(
            args.path,
            output_path=args.output,
            flatten=not args.no_flatten,
            token_chaff=not args.no_chaff,
            vm_container=not args.no_vm,
            jailbreak_decoy=not args.no_jailbreak_decoy,
            seed=args.seed
        )
        if res.get("success"):
            print(f"[OK] Successfully applied Anti-REA Armor to: {res['output_file']}")
            print(f"     AI Resistance Score: {res['score_before']}/100 -> {res['score_after']}/100 [{res['rating']}]")
        else:
            print(f"[FAIL] Error protecting file: {res.get('error')}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "shield-exe":
        res = ExtractorShield.shield_file(args.exe_path, output_path=args.output)
        if res.get("shielded"):
            print(f"[OK] Shielded executable against pyinstxtractor: {res.get('output_path', args.exe_path)}")
            print(f"     Decoy archive traps injected: {res.get('decoy_traps_injected', 0)}")
        else:
            print(f"[INFO] {res.get('reason', 'Already shielded or not a PyInstaller binary.')}")

    elif args.command == "audit":
        audit = AIResistanceAuditor.audit_file(args.path)
        if args.json:
            print(json.dumps(audit, indent=2))
        else:
            print("================================================================================")
            print("  SHIELD AUDIT REPORT: AI REVERSE-ENGINEERING RESISTANCE (TDQS-REA)")
            print("================================================================================")
            print(f"Target File:       {audit.get('file', args.path)}")
            print(f"AI Score:          {audit.get('score', 0)} / 100 [{audit.get('rating', 'UNKNOWN')}]")
            print(f"Jailbreak Immune:  {'YES (Impregnable)' if audit.get('jailbreak_ai_immune') else 'NO'}")
            print(f"Status:            {audit.get('status', 'N/A')}")
            print("\nActive Defenses:")
            for k, v in audit.get("defenses_active", {}).items():
                print(f"  [{'✔' if v else ' '}] {k}")
            if audit.get("findings"):
                print("\nRecommendations:")
                for f in audit["findings"]:
                    print(f"  • {f}")
            print("================================================================================")


if __name__ == "__main__":
    main()
