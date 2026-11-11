# -*- coding: utf-8 -*-
"""
Siber Akademi — T-Zero Multi-Agent Swarm Blackboard & In-Memory Working Memory.
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: MIT

Provides thread-safe inter-agent blackboard communication, symbol-level reservation locks,
shared architectural invariants, and zero-token AST context caching for multi-agent swarms.
100% Free, Zero External Dependencies, 100% Zero-Leak Certified.
"""

import os
import sys
import time
import json
import threading
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Set


@dataclass
class BlackboardEntry:
    entry_id: str
    author_agent: str
    topic: str
    payload: Any
    timestamp: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)


@dataclass
class SymbolLock:
    symbol_name: str
    file_path: str
    agent_id: str
    acquired_at: float = field(default_factory=time.time)


@dataclass
class SharedInvariant:
    invariant_id: str
    source_agent: str
    description: str
    severity: str = "HIGH"  # CRITICAL, HIGH, MEDIUM, LOW
    created_at: float = field(default_factory=time.time)


class MultiAgentBlackboard:
    """Thread-safe, high-speed shared working memory for autonomous agent swarms."""

    _instance: Optional["MultiAgentBlackboard"] = None
    _lock = threading.Lock()

    def __init__(self, workspace_root: str = "."):
        self.workspace_root = os.path.abspath(workspace_root)
        self._entries: List[BlackboardEntry] = []
        self._symbol_locks: Dict[str, SymbolLock] = {}  # key: "file:symbol"
        self._invariants: Dict[str, SharedInvariant] = {}
        self._ast_cache: Dict[str, str] = {}  # file_path -> compressed AST text
        self._mutex = threading.RLock()

    @classmethod
    def get_instance(cls, workspace_root: str = ".") -> "MultiAgentBlackboard":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(workspace_root=workspace_root)
            return cls._instance

    @classmethod
    def reset_instance(cls):
        with cls._lock:
            cls._instance = None

    # -------------------------------------------------------------------------
    # Symbol Locking & Concurrency Control
    # -------------------------------------------------------------------------
    def claim_symbol(self, agent_id: str, file_path: str, symbol_name: str) -> bool:
        """Claims exclusive modification lock for an AST symbol. Returns True if granted."""
        norm_path = os.path.normpath(file_path)
        key = f"{norm_path}::{symbol_name}"
        with self._mutex:
            existing = self._symbol_locks.get(key)
            if existing is not None:
                if existing.agent_id == agent_id:
                    return True  # Reentrant acquisition
                return False  # Locked by another agent
            self._symbol_locks[key] = SymbolLock(
                symbol_name=symbol_name,
                file_path=norm_path,
                agent_id=agent_id
            )
            return True

    def release_symbol(self, agent_id: str, file_path: str, symbol_name: str) -> bool:
        """Releases modification lock for an AST symbol. Returns True if successfully released."""
        norm_path = os.path.normpath(file_path)
        key = f"{norm_path}::{symbol_name}"
        with self._mutex:
            existing = self._symbol_locks.get(key)
            if existing is None:
                return True
            if existing.agent_id != agent_id:
                return False  # Cannot release another agent's lock
            del self._symbol_locks[key]
            return True

    def get_active_locks(self) -> List[SymbolLock]:
        """Returns list of currently held symbol locks."""
        with self._mutex:
            return list(self._symbol_locks.values())

    # -------------------------------------------------------------------------
    # Shared Invariants & Architectural Rules
    # -------------------------------------------------------------------------
    def post_invariant(self, source_agent: str, description: str, severity: str = "HIGH") -> str:
        """Publishes an invariant rule that all swarming agents must respect."""
        rule_hash = hashlib.sha256(f"{source_agent}::{description}".encode()).hexdigest()[:8]
        inv_id = f"INV-{rule_hash.upper()}"
        with self._mutex:
            self._invariants[inv_id] = SharedInvariant(
                invariant_id=inv_id,
                source_agent=source_agent,
                description=description,
                severity=severity.upper()
            )
        return inv_id

    def get_invariants(self) -> List[SharedInvariant]:
        """Retrieves all shared invariants posted on the blackboard."""
        with self._mutex:
            return list(self._invariants.values())

    # -------------------------------------------------------------------------
    # Discoveries & Knowledge Feeds
    # -------------------------------------------------------------------------
    def post_discovery(self, author_agent: str, topic: str, payload: Any, tags: Optional[List[str]] = None) -> str:
        """Appends a new discovery or progress update to the shared blackboard."""
        e_hash = hashlib.sha256(f"{author_agent}::{topic}::{time.time()}".encode()).hexdigest()[:10]
        entry = BlackboardEntry(
            entry_id=f"ENT-{e_hash}",
            author_agent=author_agent,
            topic=topic,
            payload=payload,
            tags=tags or []
        )
        with self._mutex:
            self._entries.append(entry)
        return entry.entry_id

    def query_discoveries(self, topic: Optional[str] = None, tag: Optional[str] = None) -> List[BlackboardEntry]:
        """Queries discoveries filtered by topic or tag."""
        with self._mutex:
            results = self._entries
            if topic:
                results = [e for e in results if e.topic.lower() == topic.lower()]
            if tag:
                results = [e for e in results if tag.lower() in [t.lower() for t in e.tags]]
            return list(results)

    # -------------------------------------------------------------------------
    # Zero-Token AST Context Caching
    # -------------------------------------------------------------------------
    def cache_ast_summary(self, file_path: str, summary: str):
        """Caches compressed AST signature so other subagents don't re-parse."""
        norm_path = os.path.normpath(file_path)
        with self._mutex:
            self._ast_cache[norm_path] = summary

    def get_ast_summary(self, file_path: str) -> Optional[str]:
        """Retrieves cached AST signature for file if present."""
        norm_path = os.path.normpath(file_path)
        with self._mutex:
            return self._ast_cache.get(norm_path)

    # -------------------------------------------------------------------------
    # Persistence & Reporting
    # -------------------------------------------------------------------------
    def export_status_markdown(self) -> str:
        """Produces comprehensive Markdown report of blackboard state for LLM context."""
        with self._mutex:
            lines = [
                "### 📋 T-Zero Multi-Agent Blackboard State",
                f"- **Active Symbol Locks:** {len(self._symbol_locks)}",
                f"- **Shared Invariants:** {len(self._invariants)}",
                f"- **Knowledge Entries:** {len(self._entries)}",
                f"- **Cached AST Profiles:** {len(self._ast_cache)}",
                ""
            ]

            if self._invariants:
                lines.append("#### 🛡️ Active Shared Invariants:")
                for inv in self._invariants.values():
                    lines.append(f"- **[{inv.severity}] {inv.invariant_id}** (`{inv.source_agent}`): {inv.description}")
                lines.append("")

            if self._symbol_locks:
                lines.append("#### 🔒 Reserved Symbol Locks:")
                for lock in self._symbol_locks.values():
                    lines.append(f"- `{lock.symbol_name}` in `{lock.file_path}` held by **{lock.agent_id}**")
                lines.append("")

            if self._entries:
                lines.append("#### 💡 Recent Swarm Discoveries:")
                for e in self._entries[-5:]:
                    lines.append(f"- **{e.author_agent}** on `{e.topic}`: {str(e.payload)[:100]}")

            return "\n".join(lines)

    def persist_to_disk(self, file_path: Optional[str] = None):
        """Persists state to JSON file."""
        if file_path is None:
            tzero_dir = os.path.join(self.workspace_root, ".tzero")
            os.makedirs(tzero_dir, exist_ok=True)
            file_path = os.path.join(tzero_dir, "blackboard.json")

        with self._mutex:
            data = {
                "version": "10.8.0",
                "timestamp": time.time(),
                "symbol_locks": {k: asdict(v) for k, v in self._symbol_locks.items()},
                "invariants": {k: asdict(v) for k, v in self._invariants.items()},
                "entries": [asdict(e) for e in self._entries],
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def load_from_disk(self, file_path: Optional[str] = None) -> bool:
        """Loads state from JSON file if available."""
        if file_path is None:
            file_path = os.path.join(self.workspace_root, ".tzero", "blackboard.json")

        if not os.path.isfile(file_path):
            return False

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            with self._mutex:
                self._symbol_locks = {
                    k: SymbolLock(**v) for k, v in data.get("symbol_locks", {}).items()
                }
                self._invariants = {
                    k: SharedInvariant(**v) for k, v in data.get("invariants", {}).items()
                }
                self._entries = [
                    BlackboardEntry(**v) for v in data.get("entries", [])
                ]
            return True
        except Exception:
            return False


def get_shared_blackboard(workspace_root: str = ".") -> MultiAgentBlackboard:
    """Convenience accessor for the singleton MultiAgentBlackboard."""
    return MultiAgentBlackboard.get_instance(workspace_root=workspace_root)

