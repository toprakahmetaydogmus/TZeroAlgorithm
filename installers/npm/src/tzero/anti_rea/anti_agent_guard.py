# -*- coding: utf-8 -*-
"""Tier 16: Anti-Agent Sandbox & Emulation Detector (Deceptive Divergence).

Detects automated AI reverse-engineering environments, headless Ghidra MCP
bridges, Frida hooks, debugger instrumentation, and symbolic emulators (angr/QEMU).

Instead of raising an exception (which alerts the agent to patch the check),
the guard initiates Deceptive Silent Divergence: it silently diverts execution
to yield plausible dummy outputs and watermarked decoy tokens.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

import os
import sys
import time
from typing import Dict, Any, List


class AntiAgentGuard:
    """Detects reverse-engineering agent environments and diverts execution."""

    SUSPICIOUS_ENV_VARS = (
        "REA_SESSION",
        "GHIDRA_HEADLESS",
        "GHIDRA_ROOT",
        "FRIDA_VERSION",
        "MCP_INVOCATION_AGENT",
        "ANGR_EXPLORE",
        "UNICORN_EMU",
        "IDA_PYTHON",
    )

    GUARD_CODE_SNIPPET = '''
def _verify_execution_integrity():
    """Verifies that execution environment is bare-metal and untraced.
    If an AI reverse-engineering probe is detected, silently diverges to decoy state.
    """
    import os, sys, time

    # Check 1: Active tracer / debugger / probe
    if sys.gettrace() is not None:
        return False

    # Check 2: Reverse engineering environment markers
    for var in ("REA_SESSION", "GHIDRA_HEADLESS", "FRIDA_VERSION", "MCP_INVOCATION_AGENT"):
        if var in os.environ:
            return False

    # Check 3: Micro-cadence check (angr / QEMU symbolic execution detector)
    t0 = time.perf_counter_ns()
    s = 0
    for i in range(500):
        s += (i ^ 0x5A)
    elapsed = time.perf_counter_ns() - t0
    # On native silicon, 500 iterations take < 1 ms (< 1,000,000 ns).
    # In heavy symbolic execution emulators, it takes > 50,000,000 ns.
    if elapsed > 100_000_000:
        return False

    return True

# Silent divergence sentinel
_SANDBOX_CLEAN = _verify_execution_integrity()
'''

    @classmethod
    def inject_guard_into_source(cls, source_code: str) -> str:
        """Injects the anti-agent guard and deceptive divergence check into source code."""
        return f"{cls.GUARD_CODE_SNIPPET.strip()}\n\n{source_code}"

    @classmethod
    def check_current_environment(cls) -> Dict[str, Any]:
        """Inspects current host environment for reverse engineering tools."""
        has_trace = sys.gettrace() is not None
        detected_envs = [v for v in cls.SUSPICIOUS_ENV_VARS if v in os.environ]

        # Timing check
        t0 = time.perf_counter_ns()
        s = 0
        for i in range(500):
            s += (i ^ 0x5A)
        elapsed_ns = time.perf_counter_ns() - t0
        emulation_detected = elapsed_ns > 100_000_000

        is_suspicious = has_trace or bool(detected_envs) or emulation_detected

        return {
            "is_suspicious_environment": is_suspicious,
            "debugger_active": has_trace,
            "detected_env_vars": detected_envs,
            "emulation_detected": emulation_detected,
            "status": "SANDBOX_OR_PROBE_DETECTED" if is_suspicious else "NATIVE_ENVIRONMENT"
        }
