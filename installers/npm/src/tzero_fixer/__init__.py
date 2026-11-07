# -*- coding: utf-8 -*-
"""T-Zero Autonomous PC-Fixer & Codebase Doctor Package.

Author: Toprak Ahmet Aydogmus (Siber Akademi)
Version: 10.5.0
"""

from .models import (
    SeverityLevel,
    DiagnosticCategory,
    SystemPlatform,
    DiagnosticIssue,
    HealAction,
    DiagnosticReport,
    HealReport,
    EnvironmentSnapshot,
    RollbackManifest,
    ToolStatus,
)
from .os_doctor import OSDoctor
from .venv_doctor import VenvDoctor
from .ast_syntax_healer import ASTSyntaxHealer
from .import_graph_healer import ImportGraphHealer
from .code_smells_healer import CodeSmellsHealer
from .security_zero_leak import SecurityZeroLeakDoctor
from .hardware_and_disk_doctor import HardwareAndDiskSurgeon
from .packaging_abi_surgeon import PackagingAbiSurgeon
from .git_advanced_surgeon import GitAdvancedSurgeon
from .polyglot_build_healer import PolyglotBuildHealer
from .cwe_remediator import SecurityCweRemediator
from .dead_code_eliminator import DeadCodeEliminator
from .async_io_modernizer import AsyncIoModernizer
from .mcp_server import PCFixerMcpServer
from .orchestrator import FixerOrchestrator

__version__ = "10.5.0"
__all__ = [
    "SeverityLevel",
    "DiagnosticCategory",
    "SystemPlatform",
    "DiagnosticIssue",
    "HealAction",
    "DiagnosticReport",
    "HealReport",
    "EnvironmentSnapshot",
    "RollbackManifest",
    "ToolStatus",
    "OSDoctor",
    "VenvDoctor",
    "ASTSyntaxHealer",
    "ImportGraphHealer",
    "CodeSmellsHealer",
    "SecurityZeroLeakDoctor",
    "HardwareAndDiskSurgeon",
    "PackagingAbiSurgeon",
    "GitAdvancedSurgeon",
    "PolyglotBuildHealer",
    "SecurityCweRemediator",
    "DeadCodeEliminator",
    "AsyncIoModernizer",
    "PCFixerMcpServer",
    "FixerOrchestrator",
]
