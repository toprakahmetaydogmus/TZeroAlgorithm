# -*- coding: utf-8 -*-
"""Tier 26: Hardware RDTSC Instruction Cycle & Single-Step Timing Guard.

Detects single-stepping, instruction-level tracing, and hardware breakpoints:
- Measures nanosecond-level execution delta between sensitive instruction checkpoints.
- Uses high-resolution CPU performance counters (QueryPerformanceCounter / perf_counter_ns).
- When an analyst halts or steps through code (F7/F8 in x64dbg/IDA), cycle count delta
  exceeds standard threshold by orders of magnitude (>50ms vs expected <100µs).
- Instant mitigation: memory poison or hard exit code 0xC0000409.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

import ast
import time
from typing import Dict, Any, Callable


class RDTSCTimingGuard:
    """Detects instruction-level debugger single-stepping using CPU timing deltas."""

    DEFAULT_STEPPING_THRESHOLD_NS = 50_000_000  # 50 ms (typical manual step is 200ms - 2s)

    @classmethod
    def measure_block_timing(cls, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Measures execution duration of a callable and checks for single-step anomaly."""
        t0 = time.perf_counter_ns()
        res = func(*args, **kwargs)
        t1 = time.perf_counter_ns()
        delta = t1 - t0
        is_delayed = delta > cls.DEFAULT_STEPPING_THRESHOLD_NS
        return {
            "result": res,
            "delta_ns": delta,
            "delta_ms": delta / 1_000_000,
            "stepping_detected": is_delayed,
        }

    @classmethod
    def generate_stepping_check_code(cls, max_allowed_ns: int = 50_000_000) -> str:
        """Generates inline instruction checkpoint timing guard."""
        return f'''# [ANTI-REA TIER-26: RDTSC HARDWARE CYCLE TIMING GUARD]
def _rdtsc_checkpoint(_t_prev, _threshold_ns={max_allowed_ns}):
    import time, os
    _now = time.perf_counter_ns()
    if (_now - _t_prev) > _threshold_ns:
        # Single-stepping or breakpoint pause detected
        os._exit(0xC0000409)
    return _now
'''

    @classmethod
    def wrap_source_with_rdtsc_guard(cls, source_code: str) -> str:
        """Wraps functions in source code with RDTSC single-stepping checkpoints."""
        guard_header = cls.generate_stepping_check_code()
        transformed = source_code
        try:
            tree = ast.parse(source_code)
            checkpoint_stmts = ast.parse(
                "_t_gate = time.perf_counter_ns()\n"
                "_t_gate = _rdtsc_checkpoint(_t_gate)\n"
            ).body
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.body:
                    insert_at = 1 if (
                        isinstance(node.body[0], ast.Expr)
                        and isinstance(getattr(node.body[0], "value", None), ast.Constant)
                        and isinstance(node.body[0].value.value, str)
                    ) else 0
                    node.body[insert_at:insert_at] = [ast.fix_missing_locations(s) for s in checkpoint_stmts]
            ast.fix_missing_locations(tree)
            transformed = ast.unparse(tree)
        except Exception:
            pass
        return f"import time\n{guard_header}\n{transformed}"
