# -*- coding: utf-8 -*-
"""T-Zero Automated Architecture Test Suite Generator & Validator.

Generates self-contained, zero-dependency `unittest` test suites from `tzero.rules.json`
enforcing layer boundaries, circular import prohibition, and zero-leak security
in standard CI/CD pipelines without external frameworks.

Author: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of T-Zero Context Architect v10.8.0 Master Edition.
"""

import ast
import fnmatch
import json
import os
import re
import sys
from typing import Dict, List, Any, Optional, Set, Tuple

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _should_skip_dir(dir_name: str) -> bool:
    """Returns True if the directory should be skipped during AST analysis."""
    skip_names = {
        ".git", ".svn", ".hg", "__pycache__", ".pytest_cache",
        "node_modules", "dist", "build", "venv", ".venv", "env",
        ".gemini", ".idea", ".vscode", "site-packages", ".egg-info",
        "installers", "benchmark-site"
    }
    return dir_name in skip_names or dir_name.endswith(".egg-info")


def _extract_ast_imports(filepath: str, rel_p: str, top_level_only: bool = False) -> Set[Tuple[str, int]]:
    """Extracts imported module names and their line numbers from a python file."""
    imports = set()
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            tree = ast.parse(f.read(), filename=filepath)

        if top_level_only:
            nodes_to_visit = []
            for item in tree.body:
                nodes_to_visit.append(item)
                if isinstance(item, (ast.If, ast.Try)):
                    nodes_to_visit.extend(ast.walk(item))
        else:
            nodes_to_visit = list(ast.walk(tree))

        for node in nodes_to_visit:
            line_no = getattr(node, "lineno", 1)
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.add((n.name, line_no))
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    base_parts = os.path.dirname(rel_p).replace("\\", "/").split("/") if os.path.dirname(rel_p) else []
                    if node.level <= len(base_parts):
                        prefix = ".".join(base_parts[:len(base_parts) - node.level + 1])
                        mod = f"{prefix}.{node.module}" if node.module else prefix
                    else:
                        mod = node.module or ""
                    if mod:
                        imports.add((mod, line_no))
                elif node.module:
                    imports.add((node.module, line_no))
    except Exception:
        pass
    return imports


class ArchitectureTestSuiteGenerator:
    """Generates and executes zero-dependency architectural guard test suites."""

    def __init__(self, project_dir: str = ".", rules_path: Optional[str] = None):
        self.project_dir = os.path.abspath(project_dir)
        self.rules_path = rules_path or os.path.join(self.project_dir, "tzero.rules.json")
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, Any]:
        """Loads rules from tzero.rules.json or returns sensible enterprise defaults."""
        if os.path.isfile(self.rules_path):
            try:
                with open(self.rules_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "version": "5.0.0",
            "project_name": os.path.basename(self.project_dir) or "Project",
            "layers": {
                "presentation": ["cli/**", "gui/**", "web/**"],
                "business": ["services/**", "core/**"],
                "persistence": ["models/**", "db/**", "utils/**"]
            },
            "forbidden_imports": [
                {
                    "from_layer": "persistence",
                    "cannot_import": ["presentation", "business"],
                    "reason": "Persistence layer must not depend on higher layers."
                },
                {
                    "from_layer": "business",
                    "cannot_import": ["presentation"],
                    "reason": "Business services must remain presentation-agnostic."
                }
            ],
            "security": {
                "zero_leak_enforced": True,
                "disallow_hardcoded_keys": True
            }
        }

    def generate_test_code(self) -> str:
        """Generates the full Python source code for the standalone architecture test suite."""
        project_name = self.rules.get("project_name", "T-Zero Project")
        layers_json = json.dumps(self.rules.get("layers", {}), indent=8)
        forbidden_json = json.dumps(self.rules.get("forbidden_imports", []), indent=8)
        security_config = self.rules.get("security", {})
        zero_leak = bool(security_config.get("zero_leak_enforced", True))

        code = f'''# -*- coding: utf-8 -*-
"""Auto-generated T-Zero Architectural Integrity Guard Test Suite.
Project: {project_name}
Generated by: T-Zero ArchitectureTestSuiteGenerator
Zero-Dependency: Runs in standard Python unittest / pytest environments.
"""

import ast
import fnmatch
import os
import re
import sys
import unittest
from typing import Dict, List, Set, Tuple, Any

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKIP_DIRS = {{
    ".git", ".svn", "__pycache__", "node_modules", "dist", "build",
    "venv", ".venv", "env", ".gemini", ".idea", ".vscode", "installers", "benchmark-site"
}}

LAYERS: Dict[str, List[str]] = {layers_json}

FORBIDDEN_IMPORTS: List[Dict[str, Any]] = {forbidden_json}

ZERO_LEAK_ENFORCED = {zero_leak}

SECRET_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{{20,}}"),
    re.compile(r"ghp_[a-zA-Z0-9]{{30,}}"),
    re.compile(r"AIza[0-9A-Za-z-_]{{35}}"),
    re.compile(r"AKIA[0-9A-Z]{{16}}"),
    re.compile(r"-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----")
]


def _matches_layer(file_rel: str, patterns: List[str]) -> bool:
    for p in patterns:
        p_clean = p.replace("\\\\", "/").rstrip("/*")
        if p.endswith("/*") or p.endswith("/**"):
            if file_rel.startswith(p_clean + "/") or file_rel == p_clean:
                return True
        elif file_rel == p_clean or os.path.basename(file_rel) == p_clean:
            return True
    return False


def _extract_ast_imports(filepath: str, rel_p: str, top_level_only: bool = False) -> Set[Tuple[str, int]]:
    imports = set()
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            tree = ast.parse(f.read(), filename=filepath)

        if top_level_only:
            nodes_to_visit = []
            for item in tree.body:
                nodes_to_visit.append(item)
                if isinstance(item, (ast.If, ast.Try)):
                    nodes_to_visit.extend(ast.walk(item))
        else:
            nodes_to_visit = list(ast.walk(tree))

        for node in nodes_to_visit:
            line_no = getattr(node, "lineno", 1)
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.add((n.name, line_no))
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    base_parts = os.path.dirname(rel_p).replace("\\\\", "/").split("/") if os.path.dirname(rel_p) else []
                    if node.level <= len(base_parts):
                        prefix = ".".join(base_parts[:len(base_parts) - node.level + 1])
                        mod = f"{{prefix}}.{{node.module}}" if node.module else prefix
                    else:
                        mod = node.module or ""
                    if mod:
                        imports.add((mod, line_no))
                elif node.module:
                    imports.add((node.module, line_no))
    except Exception:
        pass
    return imports


class TestArchitectureGuard(unittest.TestCase):
    """Verifies that codebase conforms 100% to declared architectural boundaries."""

    @classmethod
    def setUpClass(cls):
        cls.python_files: Dict[str, str] = {{}}  # rel_path -> full_path
        cls.import_graph: Dict[str, Set[Tuple[str, int]]] = {{}}  # rel_path -> set of (module, line)
        cls.top_import_graph: Dict[str, Set[str]] = {{}}  # mod_name -> set of top-level imported root mods

        for root, dirs, files in os.walk(WORKSPACE_ROOT):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.endswith(".egg-info")]
            for f in files:
                if f.endswith(".py"):
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, WORKSPACE_ROOT).replace("\\\\", "/")
                    cls.python_files[rel_p] = full_p
                    cls.import_graph[rel_p] = _extract_ast_imports(full_p, rel_p, top_level_only=False)

                    mod = os.path.splitext(f)[0]
                    top_imps = _extract_ast_imports(full_p, rel_p, top_level_only=True)
                    cls.top_import_graph[mod] = {{imp.split(".")[0] for imp, _ in top_imps}}

    def test_layer_boundaries_and_forbidden_imports(self):
        """Ensures that lower layers never import from upper or restricted layers."""
        violations = []
        for rule in FORBIDDEN_IMPORTS:
            from_layer = rule.get("from_layer")
            cannot_import = rule.get("cannot_import", [])
            reason = rule.get("reason", "Layer boundary violation")
            layer_patterns = LAYERS.get(from_layer, [])

            for rel_p, full_p in self.python_files.items():
                if not _matches_layer(rel_p, layer_patterns):
                    continue

                for full_imp, line_no in self.import_graph.get(rel_p, set()):
                    imp_segments = full_imp.split(".")
                    for forbidden_target in cannot_import:
                        clean_forbidden = forbidden_target.replace("/", ".").rstrip("/*")
                        is_violation = (
                            full_imp == clean_forbidden
                            or full_imp.startswith(clean_forbidden + ".")
                            or full_imp.endswith("." + clean_forbidden)
                            or clean_forbidden in imp_segments
                            or fnmatch.fnmatch(full_imp, forbidden_target)
                            or fnmatch.fnmatch(full_imp, f"{{clean_forbidden}}.*")
                        )
                        if is_violation:
                            violations.append(
                                f"File '{{rel_p}}:{{line_no}}' (layer: '{{from_layer}}') imports forbidden '{{full_imp}}'. "
                                f"Rule reason: {{reason}}"
                            )

        self.assertEqual(
            violations, [],
            f"Detected {{len(violations)}} architectural layer violations:\\n" + "\\n".join(violations)
        )

    def test_zero_circular_imports(self):
        """Ensures there are no circular dependency cycles among top-level modules."""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in self.top_import_graph.get(node, set()):
                if neighbor not in self.top_import_graph or neighbor == node:
                    continue
                if neighbor not in visited:
                    dfs(neighbor, path + [neighbor])
                elif neighbor in rec_stack:
                    if neighbor in path:
                        cycle = path[path.index(neighbor):] + [neighbor]
                        cycles.append(" -> ".join(cycle))
            rec_stack.remove(node)

        for m in list(self.top_import_graph.keys()):
            if m not in visited:
                dfs(m, [m])

        self.assertEqual(
            cycles, [],
            f"Detected {{len(cycles)}} circular import cycles:\\n" + "\\n".join(cycles)
        )

    def test_zero_leak_security_policy(self):
        """Ensures that no source files contain hardcoded secrets, private keys, or API tokens."""
        if not ZERO_LEAK_ENFORCED:
            self.skipTest("Zero-Leak policy is disabled in configuration.")

        secret_leaks = []
        for rel_p, full_p in self.python_files.items():
            if "test" in rel_p.lower():
                continue  # Skip test fixtures
            try:
                with open(full_p, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                for pat in SECRET_PATTERNS:
                    match = pat.search(content)
                    if match:
                        secret_leaks.append(f"Secret matched in '{{rel_p}}': {{match.group(0)[:8]}}...")
            except Exception:
                pass

        self.assertEqual(
            secret_leaks, [],
            f"Detected {{len(secret_leaks)}} secret leaks in source code:\\n" + "\\n".join(secret_leaks)
        )


if __name__ == "__main__":
    unittest.main()
'''
        return code

    def write_test_file(self, target_path: Optional[str] = None) -> str:
        """Writes the generated architecture test file to disk."""
        if not target_path:
            tests_dir = os.path.join(self.project_dir, "tests")
            os.makedirs(tests_dir, exist_ok=True)
            target_path = os.path.join(tests_dir, "test_architecture_guard.py")

        code = self.generate_test_code()
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(code)

        return target_path

    def run_live_audit(self) -> Dict[str, Any]:
        """Runs in-memory live validation of layer rules, circular imports, and zero-leak security."""
        layers = self.rules.get("layers", {})
        forbidden = self.rules.get("forbidden_imports", [])
        security = self.rules.get("security", {})

        python_files: Dict[str, str] = {}
        import_graph: Dict[str, Set[Tuple[str, int]]] = {}
        top_import_graph: Dict[str, Set[str]] = {}

        for root, dirs, files in os.walk(self.project_dir):
            dirs[:] = [d for d in dirs if not _should_skip_dir(d)]
            for f in files:
                if f.endswith(".py"):
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, self.project_dir).replace("\\", "/")
                    python_files[rel_p] = full_p
                    import_graph[rel_p] = _extract_ast_imports(full_p, rel_p, top_level_only=False)

                    mod = os.path.splitext(f)[0]
                    top_imps = _extract_ast_imports(full_p, rel_p, top_level_only=True)
                    top_import_graph[mod] = {imp.split(".")[0] for imp, _ in top_imps}

        # 1. Layer boundary violations
        layer_violations = []
        for rule in forbidden:
            from_layer = rule.get("from_layer")
            cannot_import = rule.get("cannot_import", [])
            reason = rule.get("reason", "Forbidden cross-layer coupling")
            layer_patterns = layers.get(from_layer, [])

            for rel_p, full_p in python_files.items():
                matches = False
                for p in layer_patterns:
                    p_clean = p.replace("\\", "/").rstrip("/*")
                    if p.endswith("/*") or p.endswith("/**"):
                        if rel_p.startswith(p_clean + "/") or rel_p == p_clean:
                            matches = True
                            break
                    elif rel_p == p_clean or os.path.basename(rel_p) == p_clean:
                        matches = True
                        break

                if not matches:
                    continue

                for full_imp, line_no in import_graph.get(rel_p, set()):
                    imp_segments = full_imp.split(".")
                    for forbidden_target in cannot_import:
                        clean_forbidden = forbidden_target.replace("/", ".").rstrip("/*")
                        is_violation = (
                            full_imp == clean_forbidden
                            or full_imp.startswith(clean_forbidden + ".")
                            or full_imp.endswith("." + clean_forbidden)
                            or clean_forbidden in imp_segments
                            or fnmatch.fnmatch(full_imp, forbidden_target)
                            or fnmatch.fnmatch(full_imp, f"{clean_forbidden}.*")
                        )
                        if is_violation:
                            layer_violations.append({
                                "file": rel_p,
                                "line": line_no,
                                "layer": from_layer,
                                "from_layer": from_layer,
                                "forbidden_target": forbidden_target,
                                "imported": full_imp,
                                "reason": reason
                            })

        # 2. Circular dependency check
        cycles: List[str] = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in top_import_graph.get(node, set()):
                if neighbor not in top_import_graph or neighbor == node:
                    continue
                if neighbor not in visited:
                    dfs(neighbor, path + [neighbor])
                elif neighbor in rec_stack:
                    if neighbor in path:
                        cycle = path[path.index(neighbor):] + [neighbor]
                        cycles.append(" -> ".join(cycle))
            rec_stack.remove(node)

        for m in list(top_import_graph.keys()):
            if m not in visited:
                dfs(m, [m])

        # 3. Zero leak check
        secret_leaks = []
        patterns = [
            re.compile(r"sk-[a-zA-Z0-9]{20,}"),
            re.compile(r"ghp_[a-zA-Z0-9]{30,}"),
            re.compile(r"AIza[0-9A-Za-z-_]{35}"),
            re.compile(r"AKIA[0-9A-Z]{16}")
        ]
        if security.get("zero_leak_enforced", True):
            for rel_p, full_p in python_files.items():
                if "test" in rel_p.lower():
                    continue
                try:
                    with open(full_p, "r", encoding="utf-8", errors="ignore") as fp:
                        content = fp.read()
                    for p in patterns:
                        m = p.search(content)
                        if m:
                            secret_leaks.append({"file": rel_p, "pattern": m.group(0)[:8] + "..."})
                except Exception:
                    pass

        passed = len(layer_violations) == 0 and len(cycles) == 0 and len(secret_leaks) == 0

        return {
            "success": passed,
            "scanned_files": len(python_files),
            "layers_count": len(layers),
            "layer_violations": layer_violations,
            "circular_cycles": cycles,
            "secret_leaks": secret_leaks
        }
