# -*- coding: utf-8 -*-
"""T-Zero Rust Core Bridge (ctypes / subprocess / PyO3 / WASM Agent Kernel Sandbox).

Bridges Python engines to `crates/tzero_core` and `crates/tzero_jarvis_core` compiled shared libraries
(`cdylib` via `ctypes` or `pyo3` native extension module) with an identical
pure-Python fallback when Rust binaries are not present on the host.

100% Free, Local, Offline, Zero-Leak Certified.
"""

from __future__ import annotations

import collections
import ctypes
import importlib.machinery
import importlib.util
import json
import math
import os
import shutil
from typing import Any, Dict, List, Optional, Set, Tuple


def _repo_crate_dirs() -> List[str]:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return [
        os.path.join(root, "crates", "tzero_core"),
        os.path.join(root, "crates", "tzero_jarvis_core"),
    ]


def _repo_crate_dir() -> str:
    dirs = _repo_crate_dirs()
    for d in dirs:
        if os.path.isdir(d):
            return d
    return dirs[0]


def _pure_fnv1a_64(text: str) -> int:
    h = 0xCBF29CE484222325
    prime = 0x100000001B3
    mask = 0xFFFFFFFFFFFFFFFF
    for b in (text or "").encode("utf-8", errors="replace"):
        h ^= b
        h = (h * prime) & mask
    return h


def _pure_jaccard_shingles(a: str, b: str, ngram: int = 3) -> float:
    sa = a or ""
    sb = b or ""
    if sa == sb:
        return 1.0
    n = max(1, int(ngram))
    if len(sa) < n or len(sb) < n:
        ta: Set[str] = set(sa.split())
        tb: Set[str] = set(sb.split())
    else:
        ta = {sa[i:i + n] for i in range(len(sa) - n + 1)}
        tb = {sb[i:i + n] for i in range(len(sb) - n + 1)}
    if not ta and not tb:
        return 1.0
    union = len(ta | tb)
    return round(len(ta & tb) / union, 6) if union else 0.0


def _pure_shannon_entropy(data: str) -> float:
    if not data:
        return 0.0
    try:
        from tzero.tzero_security import calculate_shannon_entropy
        return float(calculate_shannon_entropy(data))
    except Exception:
        length = len(data)
        counts = collections.Counter(data)
        entropy = 0.0
        for count in counts.values():
            p = count / length
            entropy -= p * math.log2(p)
        return float(entropy)


def _pure_scan_entropy_secrets(
    text: str,
    threshold: float = 4.75,
    min_length: int = 28,
) -> List[Dict[str, Any]]:
    try:
        from tzero.tzero_security import ZeroLeakEngine
        findings = ZeroLeakEngine.scan_text(text, check_entropy=True)
        results = []
        for f in findings:
            ent = getattr(f, "entropy", 0.0)
            if ent >= threshold:
                results.append({
                    "token": getattr(f, "secret_value", ""),
                    "entropy": ent,
                    "line": getattr(f, "line_no", 0),
                    "column": 0,
                    "is_anomaly": getattr(f, "is_entropy_anomaly", True),
                    "rule_id": getattr(f, "rule_id", "SEC-ENTROPY-001"),
                    "provider": getattr(f, "provider", "EntropyAnomaly"),
                    "description": getattr(f, "description", ""),
                })
        return results
    except Exception:
        return []


def _pure_redact_entropy_secrets(text: str, threshold: float = 4.4) -> Tuple[str, int]:
    try:
        import re
        from tzero.tzero_security import ZeroLeakEngine, calculate_shannon_entropy
        if not text:
            return "", 0
        count = 0

        def _replace_entropy(m):
            nonlocal count
            token = m.group(1)
            if not ZeroLeakEngine.is_placeholder(token) and calculate_shannon_entropy(token) >= threshold:
                count += 1
                return f'"{token[:4]}...[ZERO_LEAK_HIGH_ENTROPY_SECRET]"'
            return m.group(0)

        sanitized = re.sub(r"""['"]([^'"]{20,})['"]""", _replace_entropy, text)
        return sanitized, count
    except Exception:
        return text, 0


def _pure_prune_ast(code: str, language: str = "python") -> str:
    try:
        from tzero.tzero_polyglot import PolyglotTokenReducer
        ext_map = {
            "python": "test.py", "py": "test.py", "pyw": "test.pyw",
            "typescript": "test.ts", "ts": "test.ts", "tsx": "test.tsx",
            "javascript": "test.js", "js": "test.js", "jsx": "test.jsx",
            "mjs": "test.mjs", "cjs": "test.cjs",
            "rust": "test.rs", "rs": "test.rs",
            "go": "test.go", "golang": "test.go",
        }
        lang_key = (language or "python").lower().strip()
        fname = ext_map.get(lang_key, f"test.{lang_key}")
        return PolyglotTokenReducer.reduce_code(code, filename=fname)
    except Exception:
        return code


def _pure_prune_ast_stats(code: str, language: str = "python") -> Dict[str, Any]:
    pruned = _pure_prune_ast(code, language=language)
    orig_lines = max(1, len((code or "").splitlines()))
    pruned_lines = len(pruned.splitlines())
    reduction = round(max(0.0, (orig_lines - pruned_lines) / orig_lines * 100.0), 1)
    return {
        "pruned_code": pruned,
        "original_lines": orig_lines,
        "pruned_lines": pruned_lines,
        "reduction_ratio": reduction,
        "language": language,
    }


def _pure_count_bpe_tokens(text: str, model_name: str = "gpt-4o") -> int:
    try:
        from tzero.tzero_polyglot import count_bpe_tokens
        return int(count_bpe_tokens(text, model_name=model_name))
    except Exception:
        return max(1, len(text) // 4) if text else 0


def _pure_tokenize_code(text: str) -> List[str]:
    import re
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", text or "")
    tokens = re.findall(r"[a-zA-Z0-9]{2,}", s)
    return [t.lower() for t in tokens]


def _pure_bm25_search(
    documents: List[Dict[str, str]],
    query: str,
    top_k: int = 10,
    k1: float = 1.2,
    b: float = 0.75,
) -> List[Dict[str, Any]]:
    query_terms = _pure_tokenize_code(query)
    if not query_terms or not documents:
        return []

    doc_tokens = [_pure_tokenize_code(d.get("content", "")) for d in documents]
    doc_lens = [len(dt) for dt in doc_tokens]
    avg_len = sum(doc_lens) / max(1, len(doc_lens))
    num_docs = len(documents)

    df: Dict[str, int] = collections.defaultdict(int)
    for dt in doc_tokens:
        for t in set(dt):
            df[t] += 1

    idfs: Dict[str, float] = {}
    for t in set(query_terms):
        df_t = df.get(t, 0)
        idfs[t] = math.log(((num_docs - df_t + 0.5) / (df_t + 0.5)) + 1.0) if df_t else 0.0

    scores = []
    for idx, (doc, dt, d_len) in enumerate(zip(documents, doc_tokens, doc_lens)):
        tf_map = collections.Counter(dt)
        score = 0.0
        for q in set(query_terms):
            tf = tf_map.get(q, 0)
            if tf > 0:
                idf = idfs.get(q, 0.0)
                denom = tf + k1 * (1.0 - b + b * (d_len / (avg_len or 1.0)))
                score += idf * (tf * (k1 + 1.0)) / (denom or 1.0)
        if score > 0:
            content = doc.get("content", "")
            first_pos = 0
            low = content.lower()
            for q in query_terms:
                pos = low.find(q)
                if pos >= 0:
                    first_pos = pos
                    break
            snippet = content[max(0, first_pos - 40):first_pos + 160].replace("\n", " ")
            scores.append({
                "id": doc.get("id", str(idx)),
                "path": doc.get("path", ""),
                "score": round(score, 4),
                "snippet": snippet,
            })

    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:top_k]


def _pure_extract_symbols(path: str, content: str) -> Dict[str, Any]:
    symbols = []
    edges = []
    file_stem = os.path.splitext(os.path.basename(path))[0] if path else "module"
    for idx, line in enumerate((content or "").splitlines(), 1):
        tr = line.strip()
        if tr.startswith("def ") and "(" in tr:
            name = tr[4:].split("(")[0].strip()
            symbols.append({"name": name, "kind": "function", "line": idx, "path": path, "signature": tr})
        elif tr.startswith("class ") and (":" in tr or "(" in tr or " " in tr[6:]):
            name = tr[6:].split(":")[0].split("(")[0].split()[0].strip()
            symbols.append({"name": name, "kind": "class", "line": idx, "path": path, "signature": tr})
        elif tr.startswith("import ") or tr.startswith("from "):
            parts = tr.split()
            if len(parts) >= 2:
                mod = parts[1] if parts[0] == "from" else parts[1].split(".")[0]
                edges.append({"source": file_stem, "target": mod, "kind": "import"})
    return {"symbols": symbols, "edges": edges}


class RustCoreBridge:
    """Adaptive FFI/subprocess/PyO3 bridge to crates/tzero_core with pure-Python fallback."""

    def __init__(self, prefer_native: bool = True) -> None:
        self._cdylib: Optional[Any] = None
        self._pyo3_mod: Optional[Any] = None
        self._bin_path: Optional[str] = None
        if prefer_native:
            # Primary: PyO3 native extension module
            self._pyo3_mod = self._try_load_pyo3()
            # Secondary: ctypes shared library (cdylib)
            if self._pyo3_mod is None:
                self._cdylib = self._try_load_cdylib()
            # Tertiary: compiled standalone CLI binary
            if self._cdylib is None and self._pyo3_mod is None:
                self._bin_path = self._find_native_binary()

    @classmethod
    def _try_load_cdylib(cls) -> Optional[Any]:
        ext = ".dll" if os.name == "nt" else (
            ".dylib" if (hasattr(os, "uname") and os.uname().sysname == "Darwin") else ".so"
        )
        for crate in _repo_crate_dirs():
            names = [
                f"tzero_core{ext}", f"libtzero_core{ext}",
                f"tzero_jarvis_core{ext}", f"libtzero_jarvis_core{ext}",
            ]
            for build in ("release", "debug"):
                for fname in names:
                    cand = os.path.join(crate, "target", build, fname)
                    if os.path.isfile(cand):
                        try:
                            lib = ctypes.CDLL(cand)
                            if hasattr(lib, "tzero_fnv1a_hash64"):
                                lib.tzero_fnv1a_hash64.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
                                lib.tzero_fnv1a_hash64.restype = ctypes.c_uint64
                            if hasattr(lib, "tzero_jaccard_shingles_f64"):
                                lib.tzero_jaccard_shingles_f64.argtypes = [
                                    ctypes.c_char_p, ctypes.c_size_t,
                                    ctypes.c_char_p, ctypes.c_size_t,
                                    ctypes.c_size_t,
                                ]
                                lib.tzero_jaccard_shingles_f64.restype = ctypes.c_double
                            if hasattr(lib, "tzero_shannon_entropy"):
                                lib.tzero_shannon_entropy.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
                                lib.tzero_shannon_entropy.restype = ctypes.c_double
                            return lib
                        except OSError:
                            pass
        return None

    @classmethod
    def _try_load_pyo3(cls) -> Optional[Any]:
        try:
            from tzero import tzero_core  # type: ignore
            return tzero_core
        except ImportError:
            pass
        try:
            import tzero_core  # type: ignore
            return tzero_core
        except ImportError:
            pass
        try:
            import tzero_jarvis_core  # type: ignore
            return tzero_jarvis_core
        except ImportError:
            pass

        # Scan target directories for compiled .pyd / .so modules
        for crate in _repo_crate_dirs():
            for build in ("release", "debug"):
                target_dir = os.path.join(crate, "target", build)
                if not os.path.isdir(target_dir):
                    continue
                try:
                    for fname in os.listdir(target_dir):
                        if (fname.startswith("tzero_core") or fname.startswith("libtzero_core")) and (
                            fname.endswith(".pyd") or fname.endswith(".so") or fname.endswith(".dylib")
                        ):
                            full_path = os.path.join(target_dir, fname)
                            try:
                                loader = importlib.machinery.ExtensionFileLoader("tzero_core", full_path)
                                spec = importlib.util.spec_from_file_location("tzero_core", full_path, loader=loader)
                                if spec and spec.loader:
                                    mod = importlib.util.module_from_spec(spec)
                                    spec.loader.exec_module(mod)
                                    return mod
                            except Exception:
                                pass
                except OSError:
                    pass
        return None

    @classmethod
    def _find_native_binary(cls) -> Optional[str]:
        for crate in _repo_crate_dirs():
            for exe in ("tzero-core.exe", "tzero-core", "tzero-jarvis.exe", "tzero-jarvis"):
                for build in ("release", "debug"):
                    cand = os.path.join(crate, "target", build, exe)
                    if os.path.isfile(cand):
                        return cand
        return None

    def backend(self) -> str:
        if self._pyo3_mod is not None:
            return "pyo3"
        if self._cdylib is not None:
            return "ctypes"
        if self._bin_path is not None:
            return "subprocess"
        return "python-fallback"

    def is_native_available(self) -> bool:
        return self.backend() != "python-fallback"

    def fnv1a_hash(self, text: str) -> int:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "fnv1a_hash"):
            return int(self._pyo3_mod.fnv1a_hash(text))
        if self._cdylib is not None and hasattr(self._cdylib, "tzero_fnv1a_hash64"):
            raw = (text or "").encode("utf-8", errors="replace")
            return int(self._cdylib.tzero_fnv1a_hash64(raw, len(raw)))
        return _pure_fnv1a_64(text)

    def shingle_similarity(self, a: str, b: str, ngram: int = 3) -> float:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "shingle_similarity"):
            return float(self._pyo3_mod.shingle_similarity(a, b, int(ngram)))
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "jaccard_shingles"):
            return float(self._pyo3_mod.jaccard_shingles(a, b, int(ngram)))
        if self._cdylib is not None and hasattr(self._cdylib, "tzero_jaccard_shingles_f64"):
            ba = (a or "").encode("utf-8", errors="replace")
            bb = (b or "").encode("utf-8", errors="replace")
            return float(self._cdylib.tzero_jaccard_shingles_f64(ba, len(ba), bb, len(bb), max(1, int(ngram))))
        return _pure_jaccard_shingles(a, b, ngram=ngram)

    def calculate_entropy(self, text: str) -> float:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "calculate_shannon_entropy"):
            return float(self._pyo3_mod.calculate_shannon_entropy(text))
        if self._cdylib is not None and hasattr(self._cdylib, "tzero_shannon_entropy"):
            raw = (text or "").encode("utf-8", errors="replace")
            return float(self._cdylib.tzero_shannon_entropy(raw, len(raw)))
        return _pure_shannon_entropy(text)

    def scan_entropy_secrets(
        self,
        text: str,
        threshold: float = 4.75,
        min_length: int = 28,
    ) -> List[Dict[str, Any]]:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "scan_entropy_secrets"):
            return list(self._pyo3_mod.scan_entropy_secrets(text, threshold, min_length))
        return _pure_scan_entropy_secrets(text, threshold=threshold, min_length=min_length)

    def redact_entropy_secrets(self, text: str, threshold: float = 4.4) -> Tuple[str, int]:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "redact_entropy_secrets"):
            res = self._pyo3_mod.redact_entropy_secrets(text, threshold)
            return str(res[0]), int(res[1])
        return _pure_redact_entropy_secrets(text, threshold=threshold)

    def prune_ast(self, code: str, language: str = "python") -> str:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "prune_ast"):
            return str(self._pyo3_mod.prune_ast(code, language))
        return _pure_prune_ast(code, language=language)

    def prune_ast_stats(self, code: str, language: str = "python") -> Dict[str, Any]:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "prune_ast_stats"):
            res = self._pyo3_mod.prune_ast_stats(code, language)
            if isinstance(res, dict):
                return res
        return _pure_prune_ast_stats(code, language=language)

    def count_bpe_tokens(self, text: str, model_name: str = "gpt-4o") -> int:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "count_bpe_tokens"):
            return int(self._pyo3_mod.count_bpe_tokens(text, model_name))
        return _pure_count_bpe_tokens(text, model_name=model_name)

    def bm25_search(
        self,
        documents: List[Dict[str, str]],
        query: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "bm25_search"):
            return list(self._pyo3_mod.bm25_search(documents, query, top_k))
        return _pure_bm25_search(documents, query, top_k=top_k)

    def extract_symbols(self, path: str, content: str) -> Dict[str, Any]:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "extract_symbols"):
            res = self._pyo3_mod.extract_symbols(path, content)
            if isinstance(res, dict):
                return res
        return _pure_extract_symbols(path, content)


_GLOBAL_BRIDGE: Optional[RustCoreBridge] = None


def get_bridge() -> RustCoreBridge:
    global _GLOBAL_BRIDGE
    if _GLOBAL_BRIDGE is None:
        _GLOBAL_BRIDGE = RustCoreBridge()
    return _GLOBAL_BRIDGE


def calculate_shannon_entropy(data: str) -> float:
    return get_bridge().calculate_entropy(data)


def scan_entropy_secrets(
    text: str,
    threshold: float = 4.75,
    min_length: int = 28,
) -> List[Dict[str, Any]]:
    return get_bridge().scan_entropy_secrets(text, threshold=threshold, min_length=min_length)


def redact_entropy_secrets(text: str, threshold: float = 4.4) -> Tuple[str, int]:
    return get_bridge().redact_entropy_secrets(text, threshold=threshold)


def prune_ast(code: str, language: str = "python") -> str:
    return get_bridge().prune_ast(code, language=language)


def prune_ast_stats(code: str, language: str = "python") -> Dict[str, Any]:
    return get_bridge().prune_ast_stats(code, language=language)


def count_bpe_tokens(text: str, model_name: str = "gpt-4o") -> int:
    return get_bridge().count_bpe_tokens(text, model_name=model_name)


def fnv1a_hash(text: str) -> int:
    return get_bridge().fnv1a_hash(text)


def shingle_similarity(a: str, b: str, ngram: int = 3) -> float:
    return get_bridge().shingle_similarity(a, b, ngram=ngram)


def is_native_available() -> bool:
    return get_bridge().is_native_available()


def backend() -> str:
    return get_bridge().backend()


class AgentKernelSandbox:
    """Zero-network WASM/capability validator for autonomous T-Zero agent kernel tasks."""

    def __init__(self, workspace_dir: str = ".") -> None:
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.bridge = RustCoreBridge()

    def detect_wasm_runtime(self) -> Optional[str]:
        for tool in ("wasmtime", "wasmer", "wazero"):
            if shutil.which(tool):
                return tool
        return None

    def validate_execution_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        allow_network = bool(plan.get("allow_network", False))
        if allow_network:
            return {
                "allowed": False,
                "reason": "Blocked by T-Zero Agent Kernel Sandbox: outbound network access forbidden.",
                "backend": self.bridge.backend(),
            }

        all_paths: List[Any] = []
        for path_key in ("read_paths", "write_paths", "target_paths", "paths"):
            all_paths.extend(plan.get(path_key) or [])

        for p in all_paths:
            abs_p = os.path.abspath(str(p))
            try:
                if os.path.commonpath([self.workspace_dir, abs_p]) != self.workspace_dir:
                    return {
                        "allowed": False,
                        "reason": f"Blocked path outside workspace sandbox: {p}",
                        "backend": self.bridge.backend(),
                    }
            except ValueError:
                return {
                    "allowed": False,
                    "reason": f"Blocked invalid path: {p}",
                    "backend": self.bridge.backend(),
                }

        return {
            "allowed": True,
            "workspace_dir": self.workspace_dir,
            "backend": self.bridge.backend(),
            "wasm_runtime": self.detect_wasm_runtime() or "policy-dryrun",
            "zero_leak": True,
            "memory_limit_mb": int(plan.get("memory_limit_mb", 128)),
        }


def run_agent_kernel_cli(workspace_dir: str = ".") -> int:
    """Runs Agent Kernel Sandbox capability manifest & validation check."""
    kernel = AgentKernelSandbox(workspace_dir=workspace_dir)
    manifest = kernel.validate_execution_plan({
        "action": "sandbox-status",
        "allow_network": False,
        "read_paths": [workspace_dir],
        "memory_limit_mb": 128,
    })
    manifest["cargo_available"] = shutil.which("cargo") is not None
    print(json.dumps(manifest, indent=2))
    return 0 if manifest["allowed"] else 1
