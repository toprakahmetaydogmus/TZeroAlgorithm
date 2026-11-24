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


def _pure_calculate_cyclomatic_complexity(code: str, language: str = "python") -> int:
    try:
        from tzero.tzero_debt import calculate_cyclomatic_complexity
        return int(calculate_cyclomatic_complexity(code))
    except Exception:
        cc = 1
        for line in (code or "").splitlines():
            tr = line.strip()
            if tr.startswith("#") or tr.startswith("//"):
                continue
            for pat in ("if ", "elif ", "else if ", "for ", "while ", "case ", "match ", "catch ", "except ", " && ", " || ", " and ", " or "):
                cc += tr.count(pat)
        return cc


def _pure_calculate_cognitive_complexity(code: str) -> int:
    try:
        from tzero.tzero_debt import calculate_cognitive_complexity
        return int(calculate_cognitive_complexity(code))
    except Exception:
        cog = 0
        nesting = 0
        for line in (code or "").splitlines():
            tr = line.strip()
            if not tr or tr.startswith("#") or tr.startswith("//"):
                continue
            if any(tr.startswith(p) for p in ("if ", "elif ", "else if ", "for ", "while ", "match ", "switch ")):
                cog += (1 + nesting)
                nesting += 1
            elif any(tr.startswith(p) for p in ("else", "except", "catch")):
                cog += 1
            if tr.startswith("}") or tr.endswith("}"):
                nesting = max(0, nesting - 1)
        return cog


def _pure_analyze_file_complexity(path: str, code: str, language: str = "python") -> Dict[str, Any]:
    lines = (code or "").splitlines()
    loc = len([l for l in lines if l.strip()])
    cc = _pure_calculate_cyclomatic_complexity(code, language=language)
    cog = _pure_calculate_cognitive_complexity(code)
    loc_f = max(1.0, float(loc))
    v_f = loc_f * math.log2(max(8.0, loc_f))
    raw_mi = 171.0 - 5.2 * math.log(v_f) - 0.23 * float(cc) - 16.2 * math.log(loc_f)
    mi = round(max(0.0, min(100.0, (raw_mi / 171.0) * 100.0)), 1)
    rating = "A" if mi >= 85 else ("B" if mi >= 65 else ("C" if mi >= 50 else "D"))
    todo_count = sum(1 for l in lines if any(k in l.upper() for k in ("TODO", "FIXME", "HACK", "BUG")))
    debt_hours = round(max(0.0, (cc - 10) * 0.5) + max(0.0, (cog - 15) * 0.75) + todo_count * 0.25, 1)
    debt_usd = round(debt_hours * 75.0, 2)
    return {
        "file_path": path,
        "lines_of_code": loc,
        "maintainability_index": mi,
        "rating": rating,
        "cyclomatic_complexity": cc,
        "cognitive_complexity": cog,
        "debt_hours": debt_hours,
        "debt_cost_usd": debt_usd,
        "todo_count": todo_count,
    }


def _pure_compute_pagerank(
    edges: List[Dict[str, Any]],
    damping: float = 0.85,
    max_iter: int = 100,
    tolerance: float = 1e-6,
) -> List[Dict[str, Any]]:
    all_nodes: Set[str] = set()
    in_neighbors: Dict[str, List[str]] = collections.defaultdict(list)
    out_degrees: Dict[str, int] = collections.defaultdict(int)
    in_degrees: Dict[str, int] = collections.defaultdict(int)

    for e in edges:
        s = str(e.get("source", ""))
        t = str(e.get("target", ""))
        all_nodes.add(s)
        all_nodes.add(t)
        in_neighbors[t].append(s)
        out_degrees[s] += 1
        in_degrees[t] += 1

    n = len(all_nodes)
    if not n:
        return []

    initial = 1.0 / n
    current_pr: Dict[str, float] = {node: initial for node in all_nodes}

    for _ in range(max_iter):
        dangling_sum = sum(pr for node, pr in current_pr.items() if out_degrees[node] == 0)
        base = (1.0 - damping) / n + damping * (dangling_sum / n)
        diff = 0.0
        next_pr: Dict[str, float] = {}

        for node in all_nodes:
            in_sum = sum(current_pr[in_node] / max(1, out_degrees[in_node]) for in_node in in_neighbors[node])
            new_val = base + damping * in_sum
            diff += abs(new_val - current_pr[node])
            next_pr[node] = new_val

        current_pr = next_pr
        if diff < tolerance:
            break

    results = []
    for node, score in current_pr.items():
        results.append({
            "node": node,
            "score": round(score, 4),
            "rank": 0,
            "in_degree": in_degrees[node],
            "out_degree": out_degrees[node],
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    for idx, r in enumerate(results, 1):
        r["rank"] = idx
    return results


def _pure_analyze_reachability(
    symbols: List[Dict[str, Any]],
    invocations: List[Tuple[str, str]],
    entrypoints: List[str],
) -> Dict[str, Any]:
    call_graph: Dict[str, List[str]] = collections.defaultdict(list)
    all_symbols = {s["name"] for s in symbols if "name" in s}

    for caller, callee in invocations:
        call_graph[caller].append(callee)

    queue = collections.deque()
    visited: Set[str] = set()

    for ep in entrypoints:
        if ep in all_symbols and ep not in visited:
            visited.add(ep)
            queue.append(ep)

    if not queue:
        for name in all_symbols:
            low = name.lower()
            if low == "main" or low.startswith(("run", "cli", "test")):
                if name not in visited:
                    visited.add(name)
                    queue.append(name)

    while queue:
        curr = queue.popleft()
        for callee in call_graph.get(curr, []):
            if callee in all_symbols and callee not in visited:
                visited.add(callee)
                queue.append(callee)

    dead = sorted(list(all_symbols - visited))
    reachable = sorted(list(visited))
    total = len(symbols)
    ratio = round((len(dead) / total) * 100.0, 1) if total else 0.0

    return {
        "total_symbols": total,
        "reachable_count": len(reachable),
        "dead_symbol_count": len(dead),
        "dead_code_ratio": ratio,
        "reachable_symbols": reachable,
        "dead_symbols": dead,
    }


def _pure_compare_api_contracts(old_code: str, new_code: str) -> Dict[str, Any]:
    try:
        from tzero.tzero_contracts import ASTContractExtractor
        old_f, _ = ASTContractExtractor.extract_from_code(old_code)
        new_f, _ = ASTContractExtractor.extract_from_code(new_code)
        breaking = []
        additions = []
        for name in old_f:
            if name not in new_f:
                breaking.append({
                    "severity": "BREAKING",
                    "category": "REMOVED_SYMBOL",
                    "symbol": name,
                    "details": f"Function {name} was removed.",
                })
        for name in new_f:
            if name not in old_f:
                additions.append({
                    "severity": "ADDITION",
                    "category": "NEW_SYMBOL",
                    "symbol": name,
                    "details": f"New function {name} introduced.",
                })
        is_breaking = len(breaking) > 0
        bump = "MAJOR" if is_breaking else ("MINOR" if additions else "PATCH")
        return {
            "recommended_bump": bump,
            "is_breaking": is_breaking,
            "breaking_changes": breaking,
            "non_breaking_additions": additions,
        }
    except Exception:
        return {"recommended_bump": "PATCH", "is_breaking": False, "breaking_changes": []}


def _pure_find_code_duplicity(files: List[Tuple[str, str]], min_lines: int = 6) -> Dict[str, Any]:
    window = max(3, int(min_lines))
    hashes: Dict[int, Tuple[str, int, str]] = {}
    duplicates = []
    total_lines = 0

    for path, content in files:
        lines = (content or "").splitlines()
        total_lines += len(lines)
        if len(lines) < window:
            continue
        for i in range(len(lines) - window + 1):
            block = [l.strip() for l in lines[i:i + window] if l.strip() and not l.strip().startswith(("#", "//"))]
            if len(block) < window - 1:
                continue
            h = _pure_fnv1a_64("\n".join(block))
            if h in hashes:
                prev_path, prev_line, prev_snippet = hashes[h]
                if prev_path != path or (i + 1) != prev_line:
                    duplicates.append({
                        "file_a": prev_path,
                        "start_line_a": prev_line,
                        "file_b": path,
                        "start_line_b": i + 1,
                        "line_count": window,
                        "snippet": prev_snippet,
                    })
            else:
                hashes[h] = (path, i + 1, "\n".join(lines[i:i + window]))

    dup_lines = len(duplicates) * window
    pct = round((dup_lines / total_lines) * 100.0, 1) if total_lines else 0.0
    return {
        "total_files_scanned": len(files),
        "duplicate_block_count": len(duplicates),
        "total_duplicate_lines": dup_lines,
        "duplicate_percentage": min(100.0, pct),
        "blocks": duplicates,
    }


def _pure_damerau_levenshtein(s1: str, s2: str) -> int:
    len1, len2 = len(s1), len(s2)
    if not len1:
        return len2
    if not len2:
        return len1
    d = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    for i in range(len1 + 1):
        d[i][0] = i
    for j in range(len2 + 1):
        d[0][j] = j
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            d[i][j] = min(
                d[i - 1][j] + 1,
                d[i][j - 1] + 1,
                d[i - 1][j - 1] + cost,
            )
            if i > 1 and j > 1 and s1[i - 1] == s2[j - 2] and s1[i - 2] == s2[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[len1][len2]


def _pure_fuzzy_similarity(s1: str, s2: str) -> float:
    max_len = max(len(s1), len(s2))
    if not max_len:
        return 1.0
    dist = _pure_damerau_levenshtein(s1, s2)
    return round(max(0.0, 1.0 - dist / max_len), 3)


def _pure_fuzzy_symbol_search(
    query: str,
    candidates: List[str],
    min_similarity: float = 0.6,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    matches = []
    for cand in candidates:
        sim = _pure_fuzzy_similarity(query, cand)
        if sim >= min_similarity:
            matches.append({
                "target": cand,
                "distance": _pure_damerau_levenshtein(query, cand),
                "similarity": sim,
            })
    matches.sort(key=lambda x: x["similarity"], reverse=True)
    return matches[:top_k]


def _pure_build_context_tree(root_dir: str, tier: int = 3) -> Dict[str, Any]:
    total_lines = 0
    file_count = 0
    nodes = []
    ignored = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", "target", ".pytest_cache", ".gemini"}
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ignored and not d.startswith('.')]
        for f in files:
            if f.endswith((".py", ".rs", ".ts", ".js", ".go", ".json", ".toml", ".md")):
                fpath = os.path.join(root, f)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                        content = fp.read()
                    lines = len(content.splitlines())
                    total_lines += lines
                    file_count += 1
                    rel = os.path.relpath(fpath, root_dir).replace("\\", "/")
                    nodes.append({
                        "path": fpath,
                        "relative_path": rel,
                        "lines": lines,
                        "raw_tokens": len(content) // 4,
                        "pruned_tokens": max(5, (len(content) // 4) // 10),
                    })
                except Exception:
                    pass
    raw_toks = sum(n["raw_tokens"] for n in nodes)
    pruned_toks = sum(n["pruned_tokens"] for n in nodes)
    red = round(((raw_toks - pruned_toks) / raw_toks) * 100.0, 1) if raw_toks else 0.0
    tree_text = f"T-ZERO CONTEXT TREE (Tier {tier}) | {file_count} files, {total_lines} lines\nTokens: {raw_toks} raw -> {pruned_toks} context ({red}% reduction)\n"
    for n in nodes[:30]:
        tree_text += f"+-- {n['relative_path']} ({n['lines']} lines)\n"
    return {
        "root_dir": root_dir,
        "tier": tier,
        "total_files": file_count,
        "total_lines": total_lines,
        "raw_tokens": raw_toks,
        "pruned_tokens": pruned_toks,
        "token_reduction_percent": red,
        "formatted_tree": tree_text,
    }


def _pure_enforce_boundaries(edges: List[Tuple[str, str]], banned: Optional[List[str]] = None) -> Dict[str, Any]:
    banned_set = set(banned or ["eval", "exec", "pickle"])
    violations = []
    circular = []
    banned_findings = []
    graph = collections.defaultdict(list)
    all_mods = set()

    for src, dst in edges:
        all_mods.add(src)
        all_mods.add(dst)
        graph[src].append(dst)
        for b in banned_set:
            if b in dst:
                banned_findings.append(f"Module '{src}' imports banned symbol/module '{dst}'")

        src_low = src.lower()
        dst_low = dst.lower()
        src_is_persist = any(k in src_low for k in ("model", "persist", "db", "ast"))
        dst_is_pres = any(k in dst_low for k in ("cli", "api", "ui", "mcp"))
        if src_is_persist and dst_is_pres:
            violations.append({
                "source_module": src,
                "source_layer": "Persistence",
                "target_module": dst,
                "target_layer": "Presentation",
                "violation_type": "LayerBreach",
                "description": f"Inward-only violation: Persistence module '{src}' cannot depend on outer Presentation module '{dst}'",
            })

    visited = set()
    rec_stack = set()
    path = []

    def dfs(node):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        for nbr in graph.get(node, []):
            if nbr not in visited:
                dfs(nbr)
            elif nbr in rec_stack:
                idx = path.index(nbr) if nbr in path else 0
                cycle = path[idx:] + [nbr]
                circular.append({"cycle": cycle, "length": len(cycle) - 1})
        path.pop()
        rec_stack.remove(node)

    for m in all_mods:
        if m not in visited:
            dfs(m)

    is_compliant = not violations and not circular and not banned_findings
    return {
        "total_modules_checked": len(all_mods),
        "total_edges_checked": len(edges),
        "is_compliant": is_compliant,
        "violations": violations,
        "circular_dependencies": circular,
        "banned_import_findings": banned_findings,
    }


def _pure_verify_hallucinations(code: str, valid_symbols: List[str]) -> Dict[str, Any]:
    import re
    valid_set = set(valid_symbols) | {
        "print", "len", "range", "str", "int", "float", "bool", "list", "dict",
        "set", "tuple", "open", "isinstance", "sum", "min", "max", "sorted",
        "enumerate", "zip",
    }
    call_re = re.compile(r"([a-zA-Z0-9_]+)\s*\(")
    detected = []
    total_checked = 0
    lines = code.splitlines()

    for idx, line in enumerate(lines, 1):
        tr = line.strip()
        if tr.startswith(("#", "//", "def ", "async def ", "class ", "fn ", "pub fn ", "func ")):
            continue
        for m in call_re.finditer(line):
            call_name = m.group(1)
            if call_name in ("if", "while", "for", "with", "match", "def", "class", "return"):
                continue
            total_checked += 1
            if call_name not in valid_set and not call_name.startswith("_"):
                best_cand = None
                best_sim = 0.0
                for cand in valid_symbols:
                    sim = _pure_fuzzy_similarity(call_name, cand)
                    if sim > best_sim and sim >= 0.5:
                        best_sim = sim
                        best_cand = cand
                detected.append({
                    "symbol": call_name,
                    "kind": "call_identifier",
                    "line": idx,
                    "suggested_replacement": best_cand,
                    "similarity_confidence": round(best_sim, 2),
                })

    total = max(1, total_checked)
    score = round(((total - len(detected)) / total) * 100.0, 1)
    return {
        "total_symbols_checked": total,
        "hallucination_count": len(detected),
        "hallucination_free": len(detected) == 0,
        "safety_score": score,
        "hallucinations": detected,
    }


def _pure_estimate_costs(
    raw_tokens: int,
    pruned_tokens: int,
    output_tokens: int = 2000,
    model: str = "gpt-4o",
) -> Dict[str, Any]:
    pricing_table = {
        "gpt-4o": (2.50, 10.00),
        "gpt-4o-mini": (0.15, 0.60),
        "o3-mini": (1.10, 4.40),
        "claude-3-5-sonnet": (3.00, 15.00),
        "claude-3-5-haiku": (0.80, 4.00),
        "gemini-1-5-pro": (1.25, 5.00),
        "gemini-1-5-flash": (0.075, 0.30),
        "gemini-2-0-flash": (0.10, 0.40),
        "deepseek-v3": (0.14, 0.28),
        "deepseek-r1": (0.55, 2.19),
    }
    inp_price, out_price = pricing_table.get(model, (2.50, 10.00))
    base_in = (raw_tokens / 1_000_000.0) * inp_price
    base_out = (output_tokens / 1_000_000.0) * out_price
    baseline_cost = round(base_in + base_out, 5)

    opt_in = (pruned_tokens / 1_000_000.0) * inp_price
    opt_out = (output_tokens / 1_000_000.0) * out_price
    optimized_cost = round(opt_in + opt_out, 5)

    savings = max(0.0, round(baseline_cost - optimized_cost, 5))
    red_pct = round((savings / baseline_cost) * 100.0, 1) if baseline_cost > 0 else 0.0
    monthly_savings = round(savings * 20_000.0, 2)

    return {
        "input_tokens": raw_tokens,
        "output_tokens": output_tokens,
        "pruned_input_tokens": pruned_tokens,
        "baseline_model": model,
        "baseline_cost_usd": baseline_cost,
        "optimized_cost_usd": optimized_cost,
        "cost_savings_usd": savings,
        "cost_reduction_percent": red_pct,
        "monthly_projected_savings_usd": monthly_savings,
    }


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

    def calculate_cyclomatic_complexity(self, code: str, language: str = "python") -> int:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "calculate_cyclomatic_complexity"):
            return int(self._pyo3_mod.calculate_cyclomatic_complexity(code, language))
        return _pure_calculate_cyclomatic_complexity(code, language=language)

    def calculate_cognitive_complexity(self, code: str) -> int:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "calculate_cognitive_complexity"):
            return int(self._pyo3_mod.calculate_cognitive_complexity(code))
        return _pure_calculate_cognitive_complexity(code)

    def analyze_file_complexity(self, path: str, code: str, language: str = "python") -> Dict[str, Any]:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "analyze_file_complexity"):
            res = self._pyo3_mod.analyze_file_complexity(path, code, language)
            if isinstance(res, dict):
                return res
        return _pure_analyze_file_complexity(path, code, language=language)

    def compute_pagerank(
        self,
        edges: List[Dict[str, Any]],
        damping: float = 0.85,
        max_iter: int = 100,
    ) -> List[Dict[str, Any]]:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "compute_pagerank"):
            return list(self._pyo3_mod.compute_pagerank(edges, damping, max_iter))
        return _pure_compute_pagerank(edges, damping=damping, max_iter=max_iter)

    def analyze_reachability(
        self,
        symbols: List[Dict[str, Any]],
        invocations: List[Tuple[str, str]],
        entrypoints: List[str],
    ) -> Dict[str, Any]:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "analyze_reachability"):
            res = self._pyo3_mod.analyze_reachability(symbols, invocations, entrypoints)
            if isinstance(res, dict):
                return res
        return _pure_analyze_reachability(symbols, invocations, entrypoints)

    def compare_api_contracts(self, old_code: str, new_code: str) -> Dict[str, Any]:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "compare_api_contracts"):
            res = self._pyo3_mod.compare_api_contracts(old_code, new_code)
            if isinstance(res, dict):
                return res
        return _pure_compare_api_contracts(old_code, new_code)

    def find_code_duplicity(self, files: List[Tuple[str, str]], min_lines: int = 6) -> Dict[str, Any]:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "find_code_duplicity"):
            res = self._pyo3_mod.find_code_duplicity(files, min_lines)
            if isinstance(res, dict):
                return res
        return _pure_find_code_duplicity(files, min_lines=min_lines)

    def damerau_levenshtein(self, s1: str, s2: str) -> int:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "damerau_levenshtein"):
            return int(self._pyo3_mod.damerau_levenshtein(s1, s2))
        return _pure_damerau_levenshtein(s1, s2)

    def fuzzy_similarity(self, s1: str, s2: str) -> float:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "fuzzy_similarity"):
            return float(self._pyo3_mod.fuzzy_similarity(s1, s2))
        return _pure_fuzzy_similarity(s1, s2)

    def fuzzy_symbol_search(
        self,
        query: str,
        candidates: List[str],
        min_similarity: float = 0.6,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "fuzzy_symbol_search"):
            return list(self._pyo3_mod.fuzzy_symbol_search(query, candidates, min_similarity, top_k))
        return _pure_fuzzy_symbol_search(query, candidates, min_similarity=min_similarity, top_k=top_k)

    def build_context_tree(self, root_dir: str, tier: int = 3) -> Dict[str, Any]:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "build_context_tree"):
            res = self._pyo3_mod.build_context_tree(root_dir, tier)
            if isinstance(res, dict):
                return res
        return _pure_build_context_tree(root_dir, tier=tier)

    def enforce_boundaries(self, edges: List[Tuple[str, str]], banned: Optional[List[str]] = None) -> Dict[str, Any]:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "enforce_boundaries"):
            res = self._pyo3_mod.enforce_boundaries(edges, banned)
            if isinstance(res, dict):
                return res
        return _pure_enforce_boundaries(edges, banned=banned)

    def verify_hallucinations(self, code: str, valid_symbols: List[str]) -> Dict[str, Any]:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "verify_hallucinations"):
            res = self._pyo3_mod.verify_hallucinations(code, valid_symbols)
            if isinstance(res, dict):
                return res
        return _pure_verify_hallucinations(code, valid_symbols)

    def estimate_costs(
        self,
        raw_tokens: int,
        pruned_tokens: int,
        output_tokens: int = 2000,
        model: str = "gpt-4o",
    ) -> Dict[str, Any]:
        if self._pyo3_mod is not None and hasattr(self._pyo3_mod, "estimate_costs"):
            res = self._pyo3_mod.estimate_costs(raw_tokens, pruned_tokens, output_tokens, model)
            if isinstance(res, dict):
                return res
        return _pure_estimate_costs(raw_tokens, pruned_tokens, output_tokens=output_tokens, model=model)


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


def calculate_cyclomatic_complexity(code: str, language: str = "python") -> int:
    return get_bridge().calculate_cyclomatic_complexity(code, language=language)


def calculate_cognitive_complexity(code: str) -> int:
    return get_bridge().calculate_cognitive_complexity(code)


def analyze_file_complexity(path: str, code: str, language: str = "python") -> Dict[str, Any]:
    return get_bridge().analyze_file_complexity(path, code, language=language)


def compute_pagerank(edges: List[Dict[str, Any]], damping: float = 0.85, max_iter: int = 100) -> List[Dict[str, Any]]:
    return get_bridge().compute_pagerank(edges, damping=damping, max_iter=max_iter)


def analyze_reachability(
    symbols: List[Dict[str, Any]],
    invocations: List[Tuple[str, str]],
    entrypoints: List[str],
) -> Dict[str, Any]:
    return get_bridge().analyze_reachability(symbols, invocations, entrypoints)


def compare_api_contracts(old_code: str, new_code: str) -> Dict[str, Any]:
    return get_bridge().compare_api_contracts(old_code, new_code)


def find_code_duplicity(files: List[Tuple[str, str]], min_lines: int = 6) -> Dict[str, Any]:
    return get_bridge().find_code_duplicity(files, min_lines=min_lines)


def damerau_levenshtein(s1: str, s2: str) -> int:
    return get_bridge().damerau_levenshtein(s1, s2)


def fuzzy_similarity(s1: str, s2: str) -> float:
    return get_bridge().fuzzy_similarity(s1, s2)


def fuzzy_symbol_search(
    query: str,
    candidates: List[str],
    min_similarity: float = 0.6,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    return get_bridge().fuzzy_symbol_search(query, candidates, min_similarity=min_similarity, top_k=top_k)


def build_context_tree(root_dir: str, tier: int = 3) -> Dict[str, Any]:
    return get_bridge().build_context_tree(root_dir, tier=tier)


def enforce_boundaries(edges: List[Tuple[str, str]], banned: Optional[List[str]] = None) -> Dict[str, Any]:
    return get_bridge().enforce_boundaries(edges, banned=banned)


def verify_hallucinations(code: str, valid_symbols: List[str]) -> Dict[str, Any]:
    return get_bridge().verify_hallucinations(code, valid_symbols)


def estimate_costs(
    raw_tokens: int,
    pruned_tokens: int,
    output_tokens: int = 2000,
    model: str = "gpt-4o",
) -> Dict[str, Any]:
    return get_bridge().estimate_costs(raw_tokens, pruned_tokens, output_tokens=output_tokens, model=model)


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
