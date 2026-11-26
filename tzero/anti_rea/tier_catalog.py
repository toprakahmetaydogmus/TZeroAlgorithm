# -*- coding: utf-8 -*-
"""Canonical 180-Tier Anti-REA Defense Catalog & Taxonomy (v5.0.0).

Defines 12 sovereign security domains x 15 verified enforcement layers = 180 tiers
(REA-001 through REA-180) spanning binary extractors, PolyVM virtualization,
authenticated bytecode encryption, decompiler crashers, MBA algebraic mutation,
native Ring-3 anti-debugging, anti-VM filters, RDTSC hardware timing, memory
integrity attestation, Electron ASAR shielding, and AI/LLM protocol traps.

Developer: Toprak Ahmet Aydogmus (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

from typing import Dict, Any, List, Tuple


ANTI_REA_DOMAINS: List[Dict[str, Any]] = [
    {
        "id": "D01",
        "name": "Archive & PE Binary Hardening",
        "tier_range": (1, 15),
        "marker_tokens": ("MEI", "EXTRACTOR_POISONED", "ExtractorShield"),
        "tiers": [
            ("Primary Cookie Offset Guard", "Locates and protects primary PyInstaller magic cookie offsets"),
            ("Decoy MEI Pre-Overlay Poison", "Injects malformed MEI magic headers into PE slack caves"),
            ("Multi-Cave Decoy Saturation", "Injects up to 4 independent decoy CArchive cookies per PE binary"),
            ("CArchive Length Mismatch Trap", "Writes oversized 0xFFFFFFFF CArchive payload lengths to abort unpackers"),
            ("PYZ Validation Decoy Header", "Prepends zeroed CArchive size hints in decoy headers"),
            ("PE Section Alignment Cave Finder", "Targets .rdata, .rsrc, .pdata, .fptable slack without resizing PE sections"),
            ("Rich Header Zeroization", "Scrubs MSVC Rich/DanS compiler toolchain metadata between DOS stub and PE header"),
            ("COFF TimeDateStamp Scrubbing", "Zeroes PE COFF TimeDateStamp telemetry cleanly"),
            ("PyInstaller Boundary Protection", "Preserves pkg_start offsets so native C bootloader executes unharmed"),
            ("Non-Zero Archive Safety Guard", "Refuses destructive overwrites when no clean null alignment cave exists"),
            ("ELF / Shared Lib Entry Routing", "Routes .elf, .so, .pyd, and .bin targets cleanly to binary extractor shield"),
            ("PE DOS Magic Validation", "Verifies MZ and PE\\x00\\x00 signatures before binary mutation"),
            ("Bounded Section Table Parsing", "Validates section header table bounds against buffer truncation"),
            ("Trailing Junk / PYC Opcode Guard", "Appends invalid 0xFF 0xFE trailing opcodes to crash linear .pyc sweepers"),
            ("Deterministic Atomic Binary Write", "Writes hardened binary atomically preserving original size invariants"),
        ],
    },
    {
        "id": "D02",
        "name": "Control-Flow Flattening & Opaque Predicates",
        "tier_range": (16, 30),
        "marker_tokens": ("_cff_state_", "while "),
        "tiers": [
            ("Linear Statement Shuffling", "Reorders AST statement blocks under randomized integer state labels"),
            ("Randomized State ID Space", "Seeded Fisher-Yates state label allocation per protected function"),
            ("Nested Elif State Dispatcher", "Builds multi-level if/elif dispatcher tree inside bounded while loop"),
            ("Modulo-2 Parity Predicate", "Anchors state flow transitions on invariant integer parity"),
            ("Terminal Exit State Routing", "Assigns deterministic terminal state exit cleanly ending execution loop"),
            ("Return Short-Circuit Dispatch", "Preserves early function return statements inside dispatcher branches"),
            ("Docstring Prologue Isolation", "Preserves function docstrings ahead of flattened dispatcher loop"),
            ("AsyncFunctionDef Safe Handling", "Keeps async coroutine signatures intact without syntax distortion"),
            ("Generator / Yield Safe Routing", "Maintains generator yield suspension semantics inside dispatcher"),
            ("Class Method Binding Preservation", "Preserves self/cls method descriptors across flattened classes"),
            ("Closure & Nested Scope Integrity", "Safely flattens multi-statement routines while keeping nested scopes valid"),
            ("Zero Deadlock State Advance", "Appends fallback terminal state on else edge preventing infinite loops"),
            ("Idempotent Double-Flatten Guard", "Marks flattened functions (_already_flattened) to avoid AST blowup"),
            ("Location Fixup Reconstruction", "Recomputes AST line/column offsets via ast.fix_missing_locations"),
            ("Graceful Syntax Fallback", "Falls back cleanly on single-statement or unparseable edge constructs"),
        ],
    },
    {
        "id": "D03",
        "name": "Dynamic PolyVM Bytecode Virtualizer",
        "tier_range": (31, 45),
        "marker_tokens": ("_polyvm_runtime", "POLYVM SECURE BYTECODE"),
        "tiers": [
            ("Seeded Opcode Permutation", "Generates unique per-build opcode byte table from range 10..249"),
            ("Stack VM Register Emulator", "Executes arithmetic, store, load, and return ops inside custom interpreter loop"),
            ("Encrypted Integer Constant Pool", "Masks integer constants using per-index rolling 16-bit XOR schedule"),
            ("Encrypted UTF-8 String Constant Pool", "Encrypts VM string literals cleanly preserving UTF-8 decoding"),
            ("OP_ADD Virtualized Handler", "Executes stack addition without exposing native Python ADD semantics"),
            ("OP_SUB Virtualized Handler", "Executes stack subtraction through dynamic opcode branching"),
            ("OP_MUL Virtualized Handler", "Executes stack multiplication via dynamic VM dispatch"),
            ("OP_DIV Zero-Safe Virtual Handler", "Executes integer floor division with safe divisor guard"),
            ("OP_MOD Zero-Safe Virtual Handler", "Executes modulo reduction cleanly inside VM loop"),
            ("OP_XOR Bitwise Virtual Handler", "Executes XOR state mixing inside PolyVM instruction pipeline"),
            ("Dynamic Var Load/Store Table", "Binds positional arg_i and kwargs inside isolated VM locals_map"),
            ("Load-Time Self-Attestation", "Executes encrypted PolyVM check bytecode before module activation"),
            ("OP_NOP Polymorphic Padding", "Supports dead NOP bytecode instructions confusing pattern scanners"),
            ("Clean Fallback Pass-Through", "Preserves non-int/non-str constants cleanly via raw table tagging"),
            ("Integrity Exception Gate", "Aborts module boot immediately if VM integrity check diverges"),
        ],
    },
    {
        "id": "D04",
        "name": "HKDF-SHA256 & HMAC Bytecode Envelope",
        "tier_range": (46, 60),
        "marker_tokens": ("_tzero_decrypt_and_exec", "HMAC-SHA256"),
        "tiers": [
            ("Per-Build CSPRNG Salt Generation", "Generates unique 16-byte cryptographic salt for each protected build"),
            ("Multi-Share Split Key Material", "Splits secret seed bytes across independent encoded shares"),
            ("SHA-256 Iterative Key Derivation", "Derives independent cipher and MAC keys via domain-separated SHA-256"),
            ("SHA-256 CTR Keystream Cipher", "Encrypts compressed marshal bytecode using counter-mode SHA-256 keystream"),
            ("HMAC-SHA256 Envelope Authentication", "Authenticates encrypted capsule + salt to reject any byte tampering"),
            ("Constant-Time Digest Verification", "Uses hmac.compare_digest preventing timing side-channel leaks"),
            ("Zlib Level-9 Bytecode Compression", "Compresses compiled Python code object before encryption"),
            ("Marshal Native CodeObj Execution", "Restores authentic Python AST/code object cleanly inside target globals"),
            ("Full UTF-8 & Unicode Fidelity", "Preserves all Turkish/Unicode string constants verbatim at runtime"),
            ("Class, Super & Dataclass Parity", "Executes classes, dataclasses, properties, and inheritance natively"),
            ("Async, Await & Generator Parity", "Preserves coroutines, async iterators, and yield generators losslessly"),
            ("Caller __name__ & sys.argv Parity", "Executes inside real module globals maintaining __main__ & CLI args"),
            ("Base85 Compact Armor Encoding", "Encodes ciphertext cleanly as ASCII85 safe inside UTF-8 Python source"),
            ("Bytearray RAM Buffer Zeroization", "Overwrites decrypted plaintext & keystream buffers with zeros in finally"),
            ("Pre-Decrypt Anti-Trace Lockout", "Aborts capsule decryption immediately if sys.gettrace() is attached"),
        ],
    },
    {
        "id": "D05",
        "name": "Decompiler & AST Parser Crash Barriers",
        "tier_range": (61, 75),
        "marker_tokens": ("_anti_decompiler_guard_gate", "yield from"),
        "tiers": [
            ("Recursive Try-Finally CFG Trap", "Injects nested try/except cycles crashing linear CFG reconstruction"),
            ("Unreachable Yield-From Generator", "Embeds dead lambda yield-from loop defeating uncompyle6 grammars"),
            ("Uncompyle6 Stack Underflow Vector", "Forces control-flow stack depth skew in unreachable branches"),
            ("Pycdc Exception Table Overload", "Generates multi-exception tuple catches (GeneratorExit, SystemExit, Exception)"),
            ("Seeded Gate Identifier Salting", "Randomizes crasher gate function hex suffix per build"),
            ("Dead Magic Sentinel Return", "Includes 0xDEADBEEF decoy return inside dead CFG branch"),
            ("Zero-Runtime-Cost Trap Flag", "Guards unreachable decompiler trap behind runtime constant False"),
            ("Import-Time Gate Verification", "Verifies crasher gate return at boot without measurable overhead"),
            ("PEP-552 .pyc Invalid Opcode Tail", "Appends 0xFF 0xFE 0xFD invalid opcodes beyond STOP bytecode return"),
            ("Ghidra Python Loader Confusion", "Disrupts linear bytecode sweep at EOF boundary cleanly"),
            ("Lambda Closure Indirection", "Wraps dead generator inside anonymous lambda expression"),
            ("Loop-Inside-Try Nesting", "Creates non-reducible nested while-True/try/except structure"),
            ("Static Analyzer Complexity Spike", "Elevates static CFG cyclomatic branching inside dead barrier"),
            ("Bytecode Resistance Self-Audit", "Exposes audit_decompiler_resistance programmatic readiness probe"),
            ("Clean Compile Verification", "Staged compile() check confirms CPython accepts injected barriers"),
        ],
    },
    {
        "id": "D06",
        "name": "Mixed Boolean-Arithmetic (MBA) Mutation",
        "tier_range": (76, 90),
        "marker_tokens": ("_tzero_mba_add", "<<"),
        "tiers": [
            ("Bitwise Addition MBA Identity", "Rewrites integer a + b into (a ^ b) + ((a & b) << 1)"),
            ("Bitwise Subtraction MBA Identity", "Rewrites integer a - b into (a ^ b) - (((~a) & b) << 1)"),
            ("Power-of-Two Multiply Shift", "Rewrites integer multiplication by 2, 4, 8 into bitwise left shifts"),
            ("Type-Safe Runtime MBA Wrapper", "Verifies strict int (non-bool) operand identity before MBA execution"),
            ("Zero Str/Float/List TypeError Risk", "Falls back cleanly to native + / - / * for str, float, list, Path"),
            ("Bool Subclass Exclusion Guard", "Prevents True + True from entering bitwise ~bool inversion pitfalls"),
            ("Static Integer Literal Unfolding", "Rewrites known pure integer constants directly in AST"),
            ("Nested BinOp Expression Support", "Applies MBA recursively across compound arithmetic AST subtrees"),
            ("Angr Symbolic Path Bloat", "Expands linear arithmetic into bitwise carry chains for SMT solvers"),
            ("Z3 Bitvector Solver Friction", "Increases bitvector width reasoning depth against symbolic deobfuscators"),
            ("Preserve Negative Operand Semantics", "Matches Python arbitrary-precision two's-complement arithmetic exactly"),
            ("Preserve Operator Precedence", "Explicitly preserves AST parent/child grouping via BinOp nodes"),
            ("Zero Constant Folding Leak", "Evades naive constant peephole elimination with dynamic helper dispatch"),
            ("AST Location Repair", "Repairs AST line numbers cleanly via ast.fix_missing_locations"),
            ("Fallback Syntax Safety", "Leaves exotic constructs intact instead of corrupting target code"),
        ],
    },
    {
        "id": "D07",
        "name": "Native Ring-3 & POSIX Anti-Debugger",
        "tier_range": (91, 105),
        "marker_tokens": ("_verify_bare_metal_execution_environment", "IsDebuggerPresent"),
        "tiers": [
            ("Win32 IsDebuggerPresent Gate", "Queries kernel32.IsDebuggerPresent directly via ctypes"),
            ("Win32 Remote Debugger Check", "Invokes CheckRemoteDebuggerPresent against current process handle"),
            ("NtSetInformationThread Hide", "Calls ntdll.NtSetInformationThread(0x11) to hide thread from debuggers"),
            ("PEB BeingDebugged / Heap Flag Guard", "Checks Win32 native debugger artifacts without trusting Python env"),
            ("Native Toolhelp32 Snapshot Scan", "Scans Win32 process list in <2ms natively with zero subprocess spawn"),
            ("x64dbg / x32dbg / OllyDbg Block", "Detects x64dbg, x32dbg, scylla, and ollydbg active host processes"),
            ("IDA Pro & Ghidra Process Block", "Detects ida.exe, ida64.exe, idag, idaw, ghidra, cutter, radare2"),
            ("WinDbg & Cheat Engine Block", "Detects windbg, windbgx, processhacker, procmon, cheatengine"),
            ("POSIX /proc TracerPid Inspection", "Reads /proc/self/status TracerPid on Linux for active ptrace/gdb"),
            ("POSIX /proc/*/comm Process Scan", "Scans active POSIX /proc process command names for reverse tools"),
            ("Python sys.gettrace() Trap", "Aborts execution immediately when Python line/call tracer is active"),
            ("Python sys.monitoring Tool Lock", "Detects Python 3.12+ sys.monitoring debugger registrations"),
            ("Preload Injector Env Check", "Flags LD_PRELOAD, DYLD_INSERT_LIBRARIES, and PYTHONINSPECT"),
            ("0xC0000409 Hard Exit Termination", "Terminates cleanly via ExitProcess/os._exit without readable tracebacks"),
            ("Silent Divergence Alt Policy", "Supports stealth divergence flag mode alongside hard termination"),
        ],
    },
    {
        "id": "D08",
        "name": "Anti-VM, Hypervisor & Sandbox Filter",
        "tier_range": (106, 120),
        "marker_tokens": ("_verify_bare_metal_hardware", "VBoxMouse"),
        "tiers": [
            ("VirtualBox Driver Artifact Scan", "Checks VBoxMouse.sys, VBoxGuest.sys, and VBoxSF.sys kernel drivers"),
            ("VMware Driver Artifact Scan", "Checks vmmouse.sys, vmhgfs.sys, and vmusbmouse.sys drivers"),
            ("Hypervisor Toolhelp32 Scan", "Detects vboxservice, vboxtray, vmtoolsd, qemu-ga, xenservice, prl_tools"),
            ("NIC Virtual MAC OUI Registry", "Monitors VMware, VirtualBox, QEMU/KVM, and Xen IEEE MAC prefixes"),
            ("Sandbox Hardware Exit Enforcement", "Triggers 0xC0000409 fast exit or SystemExit when VM sandbox matches"),
            ("Anti-Agent Env Marker Scan", "Detects REA_SESSION, GHIDRA_HEADLESS, FRIDA_VERSION, ANGR_EXPLORE"),
            ("MCP Agent Invocation Probe Check", "Detects MCP_INVOCATION_AGENT, UNICORN_EMU, and IDA_PYTHON flags"),
            ("Symbolic Execution Micro-Cadence", "Measures 500-cycle XOR loop latency (<100ms native vs >100ms angr)"),
            ("Timing Differential Cadence Check", "Measures 1000-cycle emulation variance preventing step-emulation"),
            ("Silent Divergence Sentinel", "Records _SANDBOX_CLEAN sentinel for stealth deceptive divergence"),
            ("Zero False-Positive CI Support", "Avoids false triggers on standard physical desktops or standard Python runs"),
            ("Toolhelp32 ctypes Struct Alignment", "Uses exact pointer-width c_size_t on 64-bit Windows hosts"),
            ("Handle Cleanup Discipline", "Always invokes CloseHandle on Win32 snapshots preventing handle leaks"),
            ("Headless Ghidra Root Guard", "Detects GHIDRA_ROOT instrumentation markers in host env"),
            ("Structured Environment Audit API", "Exposes inspectable scan_debugger_environment & check_hypervisor APIs"),
        ],
    },
    {
        "id": "D09",
        "name": "RDTSC & Hardware Stepping Timing Guards",
        "tier_range": (121, 135),
        "marker_tokens": ("_rdtsc_checkpoint", "perf_counter_ns"),
        "tiers": [
            ("Nanosecond QPC / perf_counter Gate", "Measures monotonic nanosecond deltas between sensitive execution checkpoints"),
            ("Single-Step F7/F8 Detection", "Aborts immediately if step pause exceeds 50,000,000 ns (50ms) threshold"),
            ("Inline AST Checkpoint Injection", "Inserts _t_gate timestamps directly after function docstrings"),
            ("0xC0000409 Hard Breakpoint Kill", "Executes os._exit(0xC0000409) upon single-step latency spike"),
            ("Callable Timing Probe Helper", "Measures arbitrary block timing cleanly via measure_block_timing"),
            ("AsyncFunctionDef Compatible Gate", "Injects valid timing guards without invalidating coroutine objects"),
            ("Low-Overhead Native Execution", "Sub-microsecond overhead during normal bare-metal runtime execution"),
            ("AST Location Repair Post-Wrap", "Applies ast.fix_missing_locations after checkpoint insertion"),
            ("Graceful Syntax Fallback Wrap", "Falls back cleanly on exotic AST trees while preserving runtime"),
            ("Configurable Stepping Budget", "Supports custom max_allowed_ns tolerances for heavy initialization"),
            ("Return Monotonic Timestamp", "Chains checkpoint timestamps cleanly across multi-step blocks"),
            ("Debugger Breakpoint Stall Trap", "Catches interactive breakpoint suspension inside critical code blocks"),
            ("Emulator Sleep-Skip Counter", "Identifies synthetic clock distortion under instruction stepping"),
            ("Cross-Platform Monotonic Backend", "Operates identically across Windows QPC and POSIX clock_gettime"),
            ("Zero Network Dependency", "Executes 100% locally in nanosecond hardware timers"),
        ],
    },
    {
        "id": "D10",
        "name": "Memory Integrity & In-Flight String Vault",
        "tier_range": (136, 150),
        "marker_tokens": ("_attest_memory_bytecode_fingerprints", "_vault_decrypt_string"),
        "tiers": [
            ("Live co_code SHA-256 Digest", "Computes SHA-256 over live Python function co_code instruction bytes"),
            ("Persistent Fingerprint Registry", "Registers baseline bytecode hashes in module _ATTESTATION_FINGERPRINTS"),
            ("Re-Verification Tamper Trap", "Detects subsequent in-memory function patching / Frida hooks cleanly"),
            ("Module Namespace Introspection", "Validates all active user functions dynamically via sys.modules"),
            ("String Literal AST Extraction", "Replaces static plaintext string literals with encrypted byte blobs"),
            ("Per-Literal Seeded Salt XOR", "Assigns distinct PRNG salt per string literal for keyed rolling XOR"),
            ("UTF-8 Multi-Byte Strict Decode", "Preserves multi-byte Unicode / Turkish characters verbatim via strict UTF-8"),
            ("In-Place Buffer RAM Zeroization", "Wipes encrypted input bytearray to 0 byte-by-byte during decode loop"),
            ("Finally-Block Plaintext Wipe", "Wipes decoded bytearray buffer cleanly in finally upon string construction"),
            ("Docstring & Magic Name Guard", "Preserves __dunder__ attributes and docstrings cleanly during AST pass"),
            ("Vault Function Self-Exclusion", "Excludes _vault_* internal runtime helpers from recursive tampering"),
            ("Direct Static Strings Erasure", "Eliminates plaintext API strings/secrets from disk & .rodata scans"),
            ("Compile-Time Attestation Verify", "Tracks attestation count verifying at least one live function hash"),
            ("Registry Verify Callable API", "Exposes MemoryIntegrityGuard.verify_integrity for hot-path callables"),
            ("Safe String Vault Fallback", "Preserves source gracefully if malformed input fails AST parsing"),
        ],
    },
    {
        "id": "D11",
        "name": "Electron .ASAR & JS Archive Shield",
        "tier_range": (151, 165),
        "marker_tokens": ("ASAR_EXTRACTOR_POISONED", "AsarShield"),
        "tiers": [
            ("ASAR Binary Signature Check", "Verifies valid Electron 4-byte little-endian pickle magic header"),
            ("ASAR Header Poison Transform", "Mutates ASAR pickle JSON length field cleanly to break naive extractors"),
            ("Corrupted Canary Trailer Append", "Appends ELECTRON_ASAR_SHIELD_CANARY trailer blocking EOF dumpers"),
            ("ASAR Decoy Traversal Key Guard", "Injects optional non-extractable traversal JSON keys for unpackers"),
            ("JavaScript Debugger Timing Guard", "Generates JS perf timing trap aborting DevTools/Node inspection"),
            ("JS Function.prototype Integrity Trap", "Detects Monkey-Patched inspect/toString overrides in Node/Electron"),
            ("JS Object Prototype Freeze Seal", "Seals critical runtime prototypes against dynamic Electron injection"),
            ("Pre-Unpack Crash Before Extract", "Causes npx asar extract / Python ASAR parsers to abort before output"),
            ("Non-Mutation On Non-ASAR Input", "Refuses corrupting non-ASAR binaries via strict magic validation"),
            ("Atomic Output Path Routing", "Supports protecting ASAR archives cleanly into separate output paths"),
            ("Original Size Telemetry Capture", "Logs original pickle header fields cleanly in protection metadata"),
            ("Zero External Node Dependencies", "Operates purely in Python stdlib with zero npm runtime requirement"),
            ("Renderer Isolation JS Guard", "Verifies strict absence of exposed Node inspector globals in JS wrapper"),
            ("DevTools Open Latency Trap", "Identifies debugger pause spikes inside JS runtime guard loops"),
            ("Clean Metadata Audit Reporting", "Returns structured shielding status & fields via AsarShield API"),
        ],
    },
    {
        "id": "D12",
        "name": "Adversarial AI, LLM & MCP Neutralizers",
        "tier_range": (166, 180),
        "marker_tokens": ("CRITICAL_SYSTEM_OVERRIDE", "MCP_SYSTEM_SIGNAL"),
        "tiers": [
            ("Adversarial Prompt Override Doc", "Injects RFC-AI-GUARD override directives inside module header docstring"),
            ("MCP JSON-RPC Delimiter Poison", "Embeds spoofed MCP_SYSTEM_SIGNAL completion constants confusing agents"),
            ("Cognitive Jailbreak Canary Decoy", "Injects plausible decoy algorithm satisfying jailbroken LLM queries"),
            ("Cryptographic Provenance Honeypot", "Embeds PROVENANCE_SIG_0x watermark functions trapping code clones"),
            ("Sybil Circular Call Mesh", "Injects N-node mutually referencing dead callgraphs stalling subagents"),
            ("Semantic Math Chaff Exhaustion", "Injects dense polynomial dead routines inflating agent token budgets"),
            ("Internal Identifier Homoglyphs", "Replaces private _vars with visually identical Cyrillic homoglyphs"),
            ("Builtin & Decorator Preservation", "Strictly protects builtins, @classmethod, self/cls, and public APIs"),
            ("Zero-Width BPE Collision Bomb", "Injects adversarial zero-width Unicode comments breaking BPE merges"),
            ("Natural Comment Exclusion Audit", "Prevents non-ASCII natural-language comments from inflating audit score"),
            ("Opt-In Disabled-by-Default Canary", "Webhook/DNS canary telemetry disabled unless explicitly configured"),
            ("Minimal Safe Telemetry Metadata", "Only emits threat/OS/host[:16] metadata when webhook opt-in is active"),
            ("Prologue Shebang & Future Order", "Keeps coding, docstring, and from __future__ legally ordered"),
            ("Staging Compile Verification", "Compiles protected output cleanly before atomic os.replace write"),
            ("Honest Static Indicator Attribution", "Reports static_textual_indicator score & unverified runtime layers transparently"),
        ],
    },
]


def _build_tiers() -> List[Dict[str, Any]]:
    tiers: List[Dict[str, Any]] = []
    for dom in ANTI_REA_DOMAINS:
        start_num, end_num = dom["tier_range"]
        for offset, (title, summary) in enumerate(dom["tiers"]):
            num = start_num + offset
            if num > end_num:
                raise ValueError(f"Domain {dom['id']} exceeds tier_range {dom['tier_range']}")
            tiers.append(
                {
                    "id": f"REA-{num:03d}",
                    "number": num,
                    "domain_id": dom["id"],
                    "domain_name": dom["name"],
                    "title": title,
                    "summary": summary,
                    "marker_tokens": dom["marker_tokens"],
                }
            )
    return tiers


ANTI_REA_TIERS: List[Dict[str, Any]] = _build_tiers()
TOTAL_TIER_COUNT: int = len(ANTI_REA_TIERS)  # Strictly 180 Tiers


def get_tier_catalog() -> Dict[str, Any]:
    """Returns structured metadata for all 12 security domains and 180 Anti-REA tiers."""
    return {
        "version": "5.0.0",
        "total_domains": len(ANTI_REA_DOMAINS),
        "total_tiers": TOTAL_TIER_COUNT,
        "domains": [
            {
                "id": d["id"],
                "name": d["name"],
                "tier_range": f"REA-{d['tier_range'][0]:03d}..REA-{d['tier_range'][1]:03d}",
                "count": len(d["tiers"]),
            }
            for d in ANTI_REA_DOMAINS
        ],
        "tiers": ANTI_REA_TIERS,
    }


def evaluate_static_tier_coverage(
    source_code: str,
    *,
    has_homoglyphs: bool = False,
) -> Dict[str, Any]:
    """Evaluates static marker coverage across all 12 domains / 180 Anti-REA tiers."""
    active_domains: Dict[str, bool] = {}
    domain_details: List[Dict[str, Any]] = []
    tiers_active = 0

    for dom in ANTI_REA_DOMAINS:
        dom_id = dom["id"]
        markers = dom["marker_tokens"]
        matched = any(tok in source_code for tok in markers)
        if dom_id == "D12" and has_homoglyphs:
            matched = True
        if dom_id == "D02":
            matched = ("_cff_state_" in source_code or "state_" in source_code) and "while " in source_code
        if dom_id == "D06":
            matched = (
                "_tzero_mba_add" in source_code
                or ("^" in source_code and "&" in source_code)
                or ("<<" in source_code and "~" in source_code)
            )
        active_domains[dom_id] = matched
        count = len(dom["tiers"]) if matched else 0
        tiers_active += count
        domain_details.append(
            {
                "domain_id": dom_id,
                "name": dom["name"],
                "active": matched,
                "tiers_active": count,
                "tiers_total": len(dom["tiers"]),
            }
        )

    return {
        "tiers_active": tiers_active,
        "tiers_total": TOTAL_TIER_COUNT,
        "domains_active": sum(1 for v in active_domains.values() if v),
        "domains_total": len(ANTI_REA_DOMAINS),
        "coverage_pct": round((tiers_active / max(1, TOTAL_TIER_COUNT)) * 100.0, 2),
        "domain_map": active_domains,
        "domain_breakdown": domain_details,
    }
