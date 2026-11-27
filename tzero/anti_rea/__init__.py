# -*- coding: utf-8 -*-
"""Anti-REA: Military-Grade AI Reverse Engineering & Anti-Debugger Defense Engine.

World-class, 24-tier anti-reverse-engineering defense matrix against autonomous
AI agents (morluto/rea, Ghidra MCP, pyinstxtractor, IDA LLM) and uncensored/jailbroken LLMs.
Includes native Ring-3 anti-debugging against x64dbg, IDA Pro, WinDbg, and Cheat Engine,
opt-in tamper alert webhook, in-flight string vault, and Electron asar shielding.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

__version__ = "5.0.0"
__author__ = "Toprak Ahmet Aydoğmuş"
__license__ = "MIT"

from .engine import AntiREAEngine
from .traps import AdversarialTrapGenerator
from .extractor_shield import ExtractorShield
from .flattener import ControlFlowFlattener
from .token_bomb import TokenBombGenerator
from .confusables import HomoglyphDesynchronizer
from .honeypot import HoneypotGenerator
from .mcp_poison import MCPProtocolPoisoner
from .sybil_network import SybilNetworkGenerator
from .timing_guard import TimingGuard
from .auditor import AIResistanceAuditor
from .vm_obfuscator import DynamicVMObfuscator
from .bytecode_trap import BytecodeTrap
from .jailbreak_decoy import CognitiveJailbreakDecoy
from .anti_agent_guard import AntiAgentGuard
from .algebraic_mutator import AlgebraicMutator
from .integrity_guard import MemoryIntegrityGuard
from .bpe_disrupter import BPETokenDisrupter
from .native_bridge import NativeBridge
from .anti_debugger import AntiDebugger
from .canary_beacon import CanaryBeacon
from .string_vault import StringVault
from .asar_shield import AsarShield
from .anti_vm import AntiVMGuard
from .rdtsc_guard import RDTSCTimingGuard
from .crypto_loader import CryptoBytecodeEnvelope
from .tier_catalog import (
    ANTI_REA_DOMAINS,
    ANTI_REA_TIERS,
    TOTAL_TIER_COUNT,
    get_tier_catalog,
    evaluate_static_tier_coverage,
)

__all__ = [
    "AntiREAEngine",
    "AdversarialTrapGenerator",
    "ExtractorShield",
    "ControlFlowFlattener",
    "TokenBombGenerator",
    "HomoglyphDesynchronizer",
    "HoneypotGenerator",
    "MCPProtocolPoisoner",
    "SybilNetworkGenerator",
    "TimingGuard",
    "AIResistanceAuditor",
    "DynamicVMObfuscator",
    "BytecodeTrap",
    "CognitiveJailbreakDecoy",
    "AntiAgentGuard",
    "AlgebraicMutator",
    "MemoryIntegrityGuard",
    "BPETokenDisrupter",
    "NativeBridge",
    "AntiDebugger",
    "CanaryBeacon",
    "StringVault",
    "AsarShield",
    "AntiVMGuard",
    "RDTSCTimingGuard",
    "CryptoBytecodeEnvelope",
    "ANTI_REA_DOMAINS",
    "ANTI_REA_TIERS",
    "TOTAL_TIER_COUNT",
    "get_tier_catalog",
    "evaluate_static_tier_coverage",
]
