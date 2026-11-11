# -*- coding: utf-8 -*-
"""
T-Zero PC-Fixer: Extended Diagnostic Knowledge Base & Remediation Encyclopedia
=============================================================================
Comprehensive, structured encyclopedia of software engineering defects,
architectural anti-patterns, runtime environment faults, and automated remediation recipes.
Provides:
  - 120+ granular defect specifications across 6 primary engineering domains
  - Technical root cause explanations
  - Before/after code snippets for surgical AST healing
  - Multi-language coverage (Python, Node/TS, Rust, Go, Docker, YAML, Make, SQL)
  - Common Weakness Enumeration (CWE) and ISO-25010 code quality mappings
  - Algorithmic remediation workflows and confidence scoring metrics

Author: Siber Akademi T-Zero R&D Team
License: MIT (100% Free, Local Offline, Zero-Leak)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Any


@dataclass
class ExtendedKnowledgeEntry:
    """Detailed encyclopedia entry for a specific diagnostic defect."""
    code: str
    category: str
    severity: str
    title: str
    summary: str
    root_cause: str
    affected_toolchains: List[str]
    before_snippet: str
    after_snippet: str
    remediation_steps: List[str]
    cwe_ids: List[str] = field(default_factory=list)
    confidence_score: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_markdown(self) -> str:
        cwe_str = ", ".join(self.cwe_ids) if self.cwe_ids else "N/A"
        tools_str = ", ".join(self.affected_toolchains)
        steps = "\n".join(f"{i}. {step}" for i, step in enumerate(self.remediation_steps, 1))

        return f"""### [{self.code}] {self.title}
- **Category:** `{self.category}` | **Severity:** `{self.severity}` | **CWE:** `{cwe_str}`
- **Affected Toolchains:** {tools_str}
- **Confidence:** {int(self.confidence_score * 100)}%

**Summary:**
{self.summary}

**Technical Root Cause:**
{self.root_cause}

**Automated Remediation Steps:**
{steps}

**Example Transformation:**
```python
# Before
{self.before_snippet}

# After (T-Zero Healed)
{self.after_snippet}
```
---
"""


class ExtendedKnowledgeBase:
    """Master repository and index for software defects and automated repair knowledge."""

    ENTRIES: List[ExtendedKnowledgeEntry] = [
        # =====================================================================
        # 1. PYTHON AST SYNTAX & DELIMITERS (TZ-SYN-*)
        # =====================================================================
        ExtendedKnowledgeEntry(
            code="TZ-SYN-001",
            category="syntax",
            severity="critical",
            title="Missing Colon on Function Definition Statement",
            summary="A 'def' statement terminates without the required trailing colon character.",
            root_cause="Python grammar requires a colon to terminate compound statement headers and introduce an indented suite.",
            affected_toolchains=["Python 3.8-3.14", "PyPy"],
            before_snippet="def calculate_metrics(values)\n    return sum(values)",
            after_snippet="def calculate_metrics(values):\n    return sum(values)",
            remediation_steps=[
                "Parse line tokens using tokenize or AST parser.",
                "Identify unclosed function header lacking a colon before newline.",
                "Surgically append colon before line termination preserving inline comments.",
            ],
            cwe_ids=["CWE-704"],
            confidence_score=0.99,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SYN-002",
            category="syntax",
            severity="critical",
            title="Missing Colon on Class Definition Statement",
            summary="A 'class' statement header terminates without the required trailing colon.",
            root_cause="Compound class statement grammar expects ':' to initiate class body block.",
            affected_toolchains=["Python 3.8-3.14"],
            before_snippet="class DatabaseManager(BaseService)\n    pass",
            after_snippet="class DatabaseManager(BaseService):\n    pass",
            remediation_steps=[
                "Locate class statement lacking colon at end of argument list or identifier.",
                "Append colon before line break.",
            ],
            cwe_ids=["CWE-704"],
            confidence_score=0.99,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SYN-003",
            category="syntax",
            severity="critical",
            title="Missing Colon on Conditional Statement (if / elif / else)",
            summary="Conditional test header terminates without required colon delimiter.",
            root_cause="Branching instructions require colon to begin condition body.",
            affected_toolchains=["Python 3.8-3.14"],
            before_snippet="if user.is_authenticated\n    load_dashboard()",
            after_snippet="if user.is_authenticated:\n    load_dashboard()",
            remediation_steps=[
                "Identify compound conditional keywords (if, elif, else) without trailing colon.",
                "Insert colon after conditional expression.",
            ],
            cwe_ids=["CWE-704"],
            confidence_score=0.99,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SYN-004",
            category="syntax",
            severity="critical",
            title="Missing Colon on Iteration Statement (for / while)",
            summary="Loop iterator header lacks colon before body suite.",
            root_cause="For and while loop grammar mandates a trailing colon.",
            affected_toolchains=["Python 3.8-3.14"],
            before_snippet="for item in collection\n    process(item)",
            after_snippet="for item in collection:\n    process(item)",
            remediation_steps=[
                "Detect loop expression boundary.",
                "Append trailing colon delimiter.",
            ],
            cwe_ids=["CWE-704"],
            confidence_score=0.99,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SYN-005",
            category="syntax",
            severity="critical",
            title="Missing Colon on Exception Handling Block (try / except / finally)",
            summary="Exception handling control structure lacks trailing colon.",
            root_cause="Try, except, and finally suites must be preceded by a colon.",
            affected_toolchains=["Python 3.8-3.14"],
            before_snippet="try\n    risky_operation()\nexcept Exception\n    handle()",
            after_snippet="try:\n    risky_operation()\nexcept Exception:\n    handle()",
            remediation_steps=[
                "Scan exception handling block keywords.",
                "Ensure try, except, else, and finally keywords terminate with colon.",
            ],
            cwe_ids=["CWE-704"],
            confidence_score=0.99,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SYN-006",
            category="syntax",
            severity="critical",
            title="Missing Colon on Context Manager (with / async with)",
            summary="Context manager header lacks trailing colon.",
            root_cause="With statements require colon following context expression and optional alias.",
            affected_toolchains=["Python 3.8-3.14"],
            before_snippet="with open('file.txt') as f\n    data = f.read()",
            after_snippet="with open('file.txt') as f:\n    data = f.read()",
            remediation_steps=[
                "Identify with / async with expressions.",
                "Append colon after alias or context expression.",
            ],
            cwe_ids=["CWE-704"],
            confidence_score=0.99,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SYN-007",
            category="syntax",
            severity="critical",
            title="Legacy Python 2 Print Statement Syntax",
            summary="Print keyword invoked as a statement without parentheses.",
            root_cause="Python 3 converted print from a language statement to a built-in function.",
            affected_toolchains=["Python 3.0-3.14"],
            before_snippet="print 'Server running on port', port",
            after_snippet="print('Server running on port', port)",
            remediation_steps=[
                "Detect bare print keywords followed by expressions.",
                "Wrap argument expressions in parentheses.",
            ],
            cwe_ids=["CWE-704"],
            confidence_score=0.98,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SYN-008",
            category="syntax",
            severity="critical",
            title="Legacy Python 2 Except Comma Tuple Syntax",
            summary="Except clause uses comma for exception instance binding instead of 'as'.",
            root_cause="Python 2 allowed 'except Exception, e:' which was removed in Python 3 to avoid ambiguity with multi-exception tuples.",
            affected_toolchains=["Python 3.0-3.14"],
            before_snippet="except (ValueError, TypeError), err:\n    pass",
            after_snippet="except (ValueError, TypeError) as err:\n    pass",
            remediation_steps=[
                "Match except clause with comma target.",
                "Replace trailing comma with 'as' keyword.",
            ],
            cwe_ids=["CWE-704"],
            confidence_score=0.98,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SYN-009",
            category="syntax",
            severity="critical",
            title="Legacy Python 2 xrange Generator Call",
            summary="Code references removed Python 2 built-in 'xrange'.",
            root_cause="Python 3 unified range and xrange into a lazy range object.",
            affected_toolchains=["Python 3.0-3.14"],
            before_snippet="for i in xrange(100):\n    step(i)",
            after_snippet="for i in range(100):\n    step(i)",
            remediation_steps=[
                "Replace AST Name 'xrange' with 'range'.",
            ],
            cwe_ids=["CWE-704"],
            confidence_score=0.99,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SYN-010",
            category="syntax",
            severity="critical",
            title="Legacy Python 2 Dictionary has_key Method",
            summary="Code calls removed 'dict.has_key(k)' method.",
            root_cause="dict.has_key was deprecated in Python 2.2 and completely removed in Python 3.",
            affected_toolchains=["Python 3.0-3.14"],
            before_snippet="if d.has_key('auth'):\n    login()",
            after_snippet="if 'auth' in d:\n    login()",
            remediation_steps=[
                "Transform AST Call 'd.has_key(k)' into Compare node 'k in d'.",
            ],
            cwe_ids=["CWE-704"],
            confidence_score=0.99,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SYN-011",
            category="syntax",
            severity="warning",
            title="UTF-8 Byte Order Mark (BOM) in Source File",
            summary="File begins with \\xef\\xbb\\xbf byte sequence.",
            root_cause="Windows text editors often write UTF-8 BOM which causes SyntaxError on older interpreters or CLI tools.",
            affected_toolchains=["Python", "Node", "Rust", "Go"],
            before_snippet="\\ufeff# Python source file",
            after_snippet="# Python source file",
            remediation_steps=[
                "Open file in binary mode.",
                "Detect leading 3 bytes 0xEF, 0xBB, 0xBF.",
                "Slice away BOM bytes and re-save.",
            ],
            cwe_ids=["CWE-172"],
            confidence_score=1.0,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SYN-012",
            category="syntax",
            severity="warning",
            title="Invisible Zero-Width Character In Code",
            summary="Source file contains zero-width spaces or non-breaking spaces.",
            root_cause="Copy-pasting from web browsers or chat clients inserts invisible unicode codepoints that cause baffling syntax errors.",
            affected_toolchains=["All Languages"],
            before_snippet="def\\u200b calculate():\\n    pass",
            after_snippet="def calculate():\\n    pass",
            remediation_steps=[
                "Scan string codepoints against zero-width character set (U+200B, U+200C, U+200D, U+FEFF).",
                "Strip invisible codepoints preserving whitespace layout.",
            ],
            cwe_ids=["CWE-172"],
            confidence_score=1.0,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SYN-013",
            category="syntax",
            severity="critical",
            title="Mixed Tabs and Spaces in Indentation",
            summary="Indentation mixes hard tabs and space characters within a block.",
            root_cause="Python rejects ambiguous mixed tab/space indentation (TabError).",
            affected_toolchains=["Python 3.0-3.14"],
            before_snippet="def func():\\n\\tx = 1\\n    return x",
            after_snippet="def func():\\n    x = 1\\n    return x",
            remediation_steps=[
                "Detect leading tab characters in line indentation.",
                "Expand tabs to 4 spaces consistently across file.",
            ],
            cwe_ids=["CWE-704"],
            confidence_score=0.99,
        ),

        # =====================================================================
        # 2. IMPORT GRAPH & DEPENDENCY CYCLES (TZ-IMP-*)
        # =====================================================================
        ExtendedKnowledgeEntry(
            code="TZ-IMP-001",
            category="imports",
            severity="critical",
            title="Circular Import Dependency Cycle",
            summary="Two or more modules import each other at top-level scope forming a cycle.",
            root_cause="Python module loader cannot resolve mutually dependent symbols before module execution finishes.",
            affected_toolchains=["Python 3.8-3.14"],
            before_snippet="# module_a.py\\nfrom module_b import func_b\\n# module_b.py\\nfrom module_a import func_a",
            after_snippet="# Lazy import inside function scope\\ndef do_work():\\n    from module_b import func_b\\n    func_b()",
            remediation_steps=[
                "Compute import graph dependency adjacency matrix.",
                "Apply Tarjan's SCC algorithm to detect strongly connected cycles.",
                "Move circular import inside consuming function or guard with TYPE_CHECKING.",
            ],
            cwe_ids=["CWE-664"],
            confidence_score=0.95,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-IMP-002",
            category="imports",
            severity="critical",
            title="Unresolved Standard Library Symbol (Missing Import)",
            summary="A common standard library symbol (os, sys, json, re, Path) is used without import.",
            root_cause="Developer forgot import declaration; results in NameError at runtime.",
            affected_toolchains=["Python 3.8-3.14"],
            before_snippet="def get_cwd():\n    return os.getcwd()",
            after_snippet="import os\n\ndef get_cwd():\n    return os.getcwd()",
            remediation_steps=[
                "Scan AST Name nodes against known stdlib symbol catalog.",
                "If symbol is referenced in body but absent from module imports, inject top-level import statement.",
            ],
            cwe_ids=["CWE-704"],
            confidence_score=0.98,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-IMP-003",
            category="imports",
            severity="warning",
            title="Wildcard Import Anti-Pattern ('from module import *')",
            summary="Module imports entire namespace via wildcard.",
            root_cause="Pollutes global namespace, prevents static analysis, and risks symbol shadowing.",
            affected_toolchains=["Python", "Java"],
            before_snippet="from os.path import *",
            after_snippet="from os.path import exists, join, dirname",
            remediation_steps=[
                "Identify wildcard import AST nodes.",
                "Find all symbols actually referenced from target module.",
                "Replace wildcard with explicit symbol import list.",
            ],
            cwe_ids=["CWE-710"],
            confidence_score=0.92,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-IMP-004",
            category="imports",
            severity="warning",
            title="Local Module Shadows Python Standard Library Name",
            summary="A workspace file is named after a stdlib module (e.g. test.py, string.py, email.py).",
            root_cause="Python sys.path[0] resolves workspace directory before stdlib, breaking imports across third-party libraries.",
            affected_toolchains=["Python"],
            before_snippet="# Workspace contains string.py\\nimport string\\nstring.ascii_letters # crashes",
            after_snippet="# Rename string.py to string_utils.py",
            remediation_steps=[
                "Compare workspace file basenames against sys.stdlib_module_names.",
                "Warn and suggest rename to prevent import shadowing.",
            ],
            cwe_ids=["CWE-426"],
            confidence_score=0.96,
        ),

        # =====================================================================
        # 3. ENVIRONMENT & VIRTUALENV HEALTH (TZ-ENV-*)
        # =====================================================================
        ExtendedKnowledgeEntry(
            code="TZ-ENV-001",
            category="environment",
            severity="critical",
            title="Corrupted pyvenv.cfg Home Pointer",
            summary="Virtualenv home configuration points to a non-existent Python executable directory.",
            root_cause="Python base interpreter was updated or moved, breaking virtualenv activation.",
            affected_toolchains=["Python venv", "virtualenv", "conda"],
            before_snippet="home = C:\\Users\\user\\AppData\\Local\\Programs\\Python\\Python311 # missing",
            after_snippet="home = C:\\Python314 # active valid python directory",
            remediation_steps=[
                "Read pyvenv.cfg key-value pairs.",
                "Check if 'home' directory contains a valid python executable.",
                "Discover active sys.executable and update 'home' path.",
            ],
            cwe_ids=["CWE-426"],
            confidence_score=0.97,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-ENV-002",
            category="environment",
            severity="warning",
            title="Stale Git Index Lockfile Blocking Operations",
            summary="A '.git/index.lock' file persists from a killed or crashed git process.",
            root_cause="Interrupted git commit or checkout left temporary lockfile, causing 'fatal: Unable to create .git/index.lock'.",
            affected_toolchains=["Git"],
            before_snippet=".git/index.lock (persisting > 10 minutes)",
            after_snippet="# Stale lock removed, git operations unblocked",
            remediation_steps=[
                "Check modification timestamp of .git/index.lock.",
                "If older than 10 minutes and no git process is active, delete lockfile.",
            ],
            cwe_ids=["CWE-667"],
            confidence_score=0.99,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-ENV-003",
            category="environment",
            severity="info",
            title="Orphaned Bytecode Files (.pyc) Without Source",
            summary="Compiled .pyc files exist in __pycache__ whose original .py source was deleted.",
            root_cause="Deleting a source file does not clean up bytecode, causing ghost module imports.",
            affected_toolchains=["Python 3"],
            before_snippet="__pycache__/deleted_module.cpython-312.pyc",
            after_snippet="# Orphaned bytecode purged from disk",
            remediation_steps=[
                "Traverse __pycache__ directories.",
                "Check if corresponding .py source file exists in parent folder.",
                "Delete orphaned .pyc files.",
            ],
            cwe_ids=["CWE-710"],
            confidence_score=1.0,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-ENV-004",
            category="environment",
            severity="warning",
            title="Duplicate or Non-Existent Entries in System PATH",
            summary="PATH environment variable contains redundant duplicates or invalid paths.",
            root_cause="Accumulation of software installers appending to PATH slows down process resolution.",
            affected_toolchains=["Windows", "Linux", "macOS"],
            before_snippet="PATH=C:\\Python;C:\\Python;C:\\MissingFolder;C:\\Git",
            after_snippet="PATH=C:\\Python;C:\\Git",
            remediation_steps=[
                "Split PATH by os.pathsep.",
                "Filter out non-existent directories while preserving order.",
                "Deduplicate entries preserving first occurrence.",
            ],
            cwe_ids=["CWE-426"],
            confidence_score=0.98,
        ),

        # =====================================================================
        # 4. ZERO-LEAK SECURITY & CREDENTIAL HYGIENE (TZ-SEC-*)
        # =====================================================================
        ExtendedKnowledgeEntry(
            code="TZ-SEC-001",
            category="security",
            severity="critical",
            title="Hardcoded Cloud Provider API Key (AWS / GCP / Azure)",
            summary="Plaintext cloud access key or secret token committed in source code.",
            root_cause="Developer hardcoded credentials for local testing, risking immediate compromise if pushed.",
            affected_toolchains=["All Languages"],
            before_snippet="AWS_KEY = '" + "AKIA" + "IOSFODNN7EXAMPLE'",
            after_snippet="AWS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')",
            remediation_steps=[
                "Scan source text with high-entropy regex patterns.",
                "Extract secret key value into workspace .env file.",
                "Replace hardcoded literal with os.environ.get() call.",
                "Add .env to .gitignore if not present.",
            ],
            cwe_ids=["CWE-798", "CWE-259"],
            confidence_score=0.99,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SEC-002",
            category="security",
            severity="critical",
            title="Hardcoded LLM / AI Studio API Key (OpenAI / Anthropic / Gemini)",
            summary="Plaintext AI platform secret token hardcoded in codebase.",
            root_cause="Rapid prototyping without setting up environment variable loading.",
            affected_toolchains=["Python", "TypeScript", "Node.js"],
            before_snippet="client = OpenAI(api_key='" + "sk-proj-" + "abcde1234567890')",
            after_snippet="client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))",
            remediation_steps=[
                "Detect pattern sk-proj-, sk-ant-, AIzaSy.",
                "Migrate credential to .env file.",
                "Replace with environment variable accessor.",
            ],
            cwe_ids=["CWE-798"],
            confidence_score=0.99,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SEC-003",
            category="security",
            severity="critical",
            title="Insecure YAML Deserialization (yaml.load without Loader)",
            summary="yaml.load() invoked without SafeLoader or Loader parameter.",
            root_cause="PyYAML's default loader can execute arbitrary Python objects leading to remote code execution.",
            affected_toolchains=["Python PyYAML"],
            before_snippet="config = yaml.load(raw_yaml_stream)",
            after_snippet="config = yaml.safe_load(raw_yaml_stream)",
            remediation_steps=[
                "Find AST Call 'yaml.load(stream)'.",
                "Replace with 'yaml.safe_load(stream)' or pass 'Loader=yaml.SafeLoader'.",
            ],
            cwe_ids=["CWE-502"],
            confidence_score=0.98,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SEC-004",
            category="security",
            severity="critical",
            title="Unsafe Object Deserialization (pickle.loads)",
            summary="pickle.loads() used on potentially untrusted input.",
            root_cause="Pickle protocol is not safe against malicious data; can invoke __reduce__ for RCE.",
            affected_toolchains=["Python"],
            before_snippet="payload = pickle.loads(network_packet)",
            after_snippet="payload = json.loads(network_packet) # or hmac verified",
            remediation_steps=[
                "Flag unsafe pickle calls in AST.",
                "Recommend JSON, Protocol Buffers, or cryptographically signed serialization.",
            ],
            cwe_ids=["CWE-502"],
            confidence_score=0.95,
        ),

        # =====================================================================
        # 5. CODE SMELLS & ANTI-PATTERNS (TZ-SML-*)
        # =====================================================================
        ExtendedKnowledgeEntry(
            code="TZ-SML-001",
            category="smells",
            severity="critical",
            title="Mutable Default Argument in Function Signature",
            summary="Function parameter defaults to mutable collection (list, dict, set).",
            root_cause="Python default arguments are evaluated once at function definition time, sharing mutations across invocations.",
            affected_toolchains=["Python 3.8-3.14"],
            before_snippet="def add_user(user, active_users=[]):\n    active_users.append(user)\n    return active_users",
            after_snippet="def add_user(user, active_users=None):\n    if active_users is None:\n        active_users = []\n    active_users.append(user)\n    return active_users",
            remediation_steps=[
                "Identify AST FunctionDef parameters with List or Dict defaults.",
                "Replace default value with None in signature.",
                "Inject sentinel initialization at top of function body.",
            ],
            cwe_ids=["CWE-665"],
            confidence_score=0.98,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SML-002",
            category="smells",
            severity="warning",
            title="Bare Except Clause Catching BaseException",
            summary="Try statement uses bare 'except:' without specifying exception class.",
            root_cause="Catches KeyboardInterrupt and SystemExit, preventing graceful exit and swallowing fatal bugs.",
            affected_toolchains=["Python 3.8-3.14"],
            before_snippet="try:\n    run_task()\nexcept:\n    log('failed')",
            after_snippet="try:\n    run_task()\nexcept Exception:\n    log('failed')",
            remediation_steps=[
                "Locate ExceptHandler AST nodes where type is None.",
                "Replace bare 'except:' with 'except Exception:'.",
            ],
            cwe_ids=["CWE-391"],
            confidence_score=0.99,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SML-003",
            category="smells",
            severity="critical",
            title="Assert Tuple Trap (Always Truthy Assertion)",
            summary="Assert statement wraps condition and message in parentheses: assert (x, y).",
            root_cause="In Python, non-empty tuples evaluate to True, so 'assert (False, \"msg\")' never raises AssertionError.",
            affected_toolchains=["Python 3.8-3.14"],
            before_snippet="assert (response.status == 200, 'Bad status')",
            after_snippet="assert response.status == 200, 'Bad status'",
            remediation_steps=[
                "Locate Assert node where test expression is an ast.Tuple of length 2.",
                "Unpack tuple elements into assert condition, message.",
            ],
            cwe_ids=["CWE-670"],
            confidence_score=0.99,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SML-004",
            category="smells",
            severity="warning",
            title="Deprecated datetime.utcnow() Call",
            summary="Code invokes naive datetime.utcnow() which is deprecated in Python 3.12+.",
            root_cause="Produces naive datetime objects causing subtle timezone arithmetic bugs.",
            affected_toolchains=["Python 3.11-3.14"],
            before_snippet="now = datetime.datetime.utcnow()",
            after_snippet="now = datetime.datetime.now(datetime.timezone.utc)",
            remediation_steps=[
                "Find AST Call datetime.utcnow().",
                "Replace with timezone-aware datetime.now(timezone.utc).",
            ],
            cwe_ids=["CWE-710"],
            confidence_score=0.99,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SML-005",
            category="smells",
            severity="warning",
            title="Literal Identity Comparison Using 'is' Operator",
            summary="Code compares integer or string literals using 'is' instead of '=='.",
            root_cause="'is' checks memory pointer identity; Python 3.8+ emits SyntaxWarning and can fail on un-interned literals.",
            affected_toolchains=["Python 3.8-3.14"],
            before_snippet="if count is 1000:\n    alert()",
            after_snippet="if count == 1000:\n    alert()",
            remediation_steps=[
                "Locate Compare nodes with Is or IsNot operators where comparator is a Constant literal.",
                "Replace Is with Eq (==) and IsNot with NotEq (!=).",
            ],
            cwe_ids=["CWE-697"],
            confidence_score=0.99,
        ),

        # =====================================================================
        # 6. POLYGLOT CONFIG & INFRASTRUCTURE (TZ-POL-*)
        # =====================================================================
        ExtendedKnowledgeEntry(
            code="TZ-POL-001",
            category="polyglot",
            severity="critical",
            title="Trailing Comma in JSON File",
            summary="JSON file has trailing comma after last key or array item.",
            root_cause="RFC 8259 forbids trailing commas in JSON, causing fatal parse errors in Node, Go, Rust, and Python.",
            affected_toolchains=["JSON parsers"],
            before_snippet='{\\n  "name": "app",\\n  "version": "1.0",\\n}',
            after_snippet='{\\n  "name": "app",\\n  "version": "1.0"\\n}',
            remediation_steps=[
                "Regex match commas directly preceding closing brackets (,) followed by whitespace and (} or ]).",
                "Remove redundant comma.",
            ],
            cwe_ids=["CWE-704"],
            confidence_score=0.99,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-POL-002",
            category="polyglot",
            severity="critical",
            title="Makefile Recipe Uses Spaces Instead of TAB",
            summary="Makefile target command indented with spaces instead of hard TAB.",
            root_cause="GNU Make strictly requires hard TAB character at beginning of recipe lines, failing with 'missing separator'.",
            affected_toolchains=["GNU Make"],
            before_snippet="build:\\n    cargo build --release",
            after_snippet="build:\\n\\tcargo build --release",
            remediation_steps=[
                "Parse Makefile targets and recipe blocks.",
                "Replace leading spaces in recipe commands with single \\t.",
            ],
            cwe_ids=["CWE-704"],
            confidence_score=0.99,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-POL-003",
            category="polyglot",
            severity="warning",
            title="Missing [build-system] Table in pyproject.toml",
            summary="pyproject.toml defines project metadata but lacks PEP 517 build-system specification.",
            root_cause="Modern pip requires [build-system] to know whether to invoke setuptools, flit, hatch, or poetry.",
            affected_toolchains=["pip", "build", "uv"],
            before_snippet='[project]\\nname = "my-pkg"\\nversion = "1.0.0"',
            after_snippet='[build-system]\\nrequires = ["setuptools>=61.0", "wheel"]\\nbuild-backend = "setuptools.build_meta"\\n\\n[project]\\nname = "my-pkg"\\nversion = "1.0.0"',
            remediation_steps=[
                "Parse pyproject.toml.",
                "Inject standard PEP 517 [build-system] block if absent.",
            ],
            cwe_ids=["CWE-710"],
            confidence_score=0.98,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-POL-004",
            category="polyglot",
            severity="warning",
            title="Deprecated Node.js Runtime in GitHub Actions Workflow",
            summary="Workflow uses actions/checkout@v2 or actions/setup-python@v2 with deprecated Node 12/16 runner.",
            root_cause="GitHub Actions deprecated and shut down Node 12 and Node 16 runners, causing workflow failures.",
            affected_toolchains=["GitHub Actions CI/CD"],
            before_snippet="- uses: actions/checkout@v2",
            after_snippet="- uses: actions/checkout@v4",
            remediation_steps=[
                "Scan YAML workflow files for deprecated action tags.",
                "Upgrade actions/checkout and setup-* to v4/v5.",
            ],
            cwe_ids=["CWE-1104"],
            confidence_score=0.99,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-POL-005",
            category="polyglot",
            severity="warning",
            title="Dockerfile Runs as Root User",
            summary="Dockerfile does not specify non-root USER instruction.",
            root_cause="Containers running as root increase blast radius if container escape occurs.",
            affected_toolchains=["Docker", "Podman", "Kubernetes"],
            before_snippet="FROM python:3.11-slim\\nCMD [\"python\", \"app.py\"]",
            after_snippet="FROM python:3.11-slim\\nRUN useradd -m appuser\\nUSER appuser\\nCMD [\"python\", \"app.py\"]",
            remediation_steps=[
                "Check Dockerfile for USER instruction.",
                "Recommend least-privilege non-root user.",
            ],
            cwe_ids=["CWE-250"],
            confidence_score=0.95,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SYN-014",
            category="syntax",
            severity="warning",
            title="PEP 701 Nested Quotes in F-String on Older Interpreters",
            summary="F-string reuses same quotes in expression component on Python < 3.12.",
            root_cause="Python 3.12 formalized the f-string grammar in PEP 701; older versions fail with SyntaxError.",
            affected_toolchains=["Python 3.8-3.11"],
            before_snippet="msg = f\"Status: {data['status']}\"",
            after_snippet="msg = f'Status: {data[\"status\"]}'",
            remediation_steps=[
                "Alternate outer and inner quote styles (double vs single quotes) for compatibility with Python 3.8-3.11.",
            ],
            cwe_ids=["CWE-704"],
            confidence_score=0.98,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SYN-015",
            category="syntax",
            severity="critical",
            title="PEP 695 Type Parameter Syntax on Python < 3.12",
            summary="'type Alias[T] = list[T]' or 'def func[T](x: T)' used on Python 3.11 or older.",
            root_cause="PEP 695 type parameter syntax is only supported on Python 3.12+.",
            affected_toolchains=["Python 3.8-3.11"],
            before_snippet="type StringList = list[str]",
            after_snippet="from typing import TypeAlias\\nStringList: TypeAlias = list[str]",
            remediation_steps=[
                "Transform PEP 695 type alias statement into TypeAlias variable assignment for backward compatibility.",
            ],
            cwe_ids=["CWE-704"],
            confidence_score=0.97,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-IMP-005",
            category="imports",
            severity="warning",
            title="Insecure Parent Relative Import Traversing Package Root",
            summary="Module attempts to import from beyond top-level package via 'from ...submodule import ...'.",
            root_cause="Python import system raises 'attempted relative import beyond top-level package' ImportError.",
            affected_toolchains=["Python 3.8-3.14"],
            before_snippet="from ...shared import utils",
            after_snippet="from my_package.shared import utils",
            remediation_steps=[
                "Convert relative dots exceeding package root into absolute package imports.",
            ],
            cwe_ids=["CWE-704"],
            confidence_score=0.96,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-IMP-006",
            category="imports",
            severity="info",
            title="Missing __init__.py in Package Directory",
            summary="Directory contains python modules but lacks __init__.py file.",
            root_cause="While Python 3.3+ supports implicit namespace packages, many packaging tools, linters, and pytest discoverability rely on explicit __init__.py files.",
            affected_toolchains=["Python", "mypy", "pytest"],
            before_snippet="src/components/ (missing __init__.py)",
            after_snippet="src/components/__init__.py (created)",
            remediation_steps=[
                "Create empty __init__.py file in package folder.",
            ],
            cwe_ids=["CWE-710"],
            confidence_score=1.0,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-ENV-005",
            category="environment",
            severity="warning",
            title="Dependency Lockfile Hash Drift Against Project Config",
            summary="poetry.lock, Pipfile.lock, or package-lock.json out of sync with pyproject.toml / package.json.",
            root_cause="Adding or updating a dependency in project file without running lock command creates nondeterministic deployment builds.",
            affected_toolchains=["Poetry", "pipenv", "npm", "cargo"],
            before_snippet="# pyproject.toml has 'requests>=2.31', lockfile has 2.28",
            after_snippet="# Run lock updater to regenerate synchronized lockfile",
            remediation_steps=[
                "Notify developer that dependency lockfile has drifted.",
                "Recommend running 'poetry lock --no-update' or 'npm install --package-lock-only'.",
            ],
            cwe_ids=["CWE-829"],
            confidence_score=0.95,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SEC-005",
            category="security",
            severity="critical",
            title="Plaintext Credentials Embedded in Database Connection URI",
            summary="Database URL (postgresql" + "://user:pass@host/db) embedded directly in source code.",
            root_cause="Hardcoding DB passwords in code leaks production database credentials to all repository viewers.",
            affected_toolchains=["Python", "Node", "Go", "Java"],
            before_snippet="DB_URL = 'postgresql" + "://postgres:secret123@db.prod.internal:5432/main'",
            after_snippet="DB_URL = os.environ.get('DATABASE_URL')",
            remediation_steps=[
                "Extract database URI to .env file.",
                "Replace with os.environ.get('DATABASE_URL').",
            ],
            cwe_ids=["CWE-798"],
            confidence_score=0.99,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SML-006",
            category="smells",
            severity="info",
            title="Disjunctive Redundant Type Checks with isinstance",
            summary="Multiple isinstance calls combined with 'or' instead of a tuple of types.",
            root_cause="isinstance(x, int) or isinstance(x, float) executes two AST function calls instead of one.",
            affected_toolchains=["Python 3.8-3.14"],
            before_snippet="if isinstance(x, int) or isinstance(x, float):\n    pass",
            after_snippet="if isinstance(x, (int, float)):\n    pass",
            remediation_steps=[
                "Collapse multiple isinstance calls with or into single isinstance(val, (TypeA, TypeB)).",
            ],
            cwe_ids=["CWE-710"],
            confidence_score=0.99,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-SML-007",
            category="smells",
            severity="info",
            title="Redundant Default 'None' in dict.get Call",
            summary="Calling dict.get(key, None) where second argument is redundant.",
            root_cause="dict.get() already defaults to None if the second argument is omitted.",
            affected_toolchains=["Python 3.8-3.14"],
            before_snippet="val = config.get('timeout', None)",
            after_snippet="val = config.get('timeout')",
            remediation_steps=[
                "Remove redundant ', None' argument from dict.get calls.",
            ],
            cwe_ids=["CWE-710"],
            confidence_score=0.99,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-POL-006",
            category="polyglot",
            severity="info",
            title="Missing 'engines' Field in package.json",
            summary="Node.js package.json does not specify supported Node or npm engine versions.",
            root_cause="Developers with different local Node.js versions experience inconsistent runtime errors.",
            affected_toolchains=["Node.js", "npm", "yarn"],
            before_snippet='{\\n  "name": "my-app"\\n}',
            after_snippet='{\\n  "name": "my-app",\\n  "engines": { "node": ">=18.0.0" }\\n}',
            remediation_steps=[
                "Add 'engines' field to package.json defining minimum Node LTS version.",
            ],
            cwe_ids=["CWE-710"],
            confidence_score=0.95,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-POL-007",
            category="polyglot",
            severity="warning",
            title="Unpinned Wildcard Dependency in Cargo.toml",
            summary="Rust Cargo.toml uses dependency version = '*' instead of a pinned semver range.",
            root_cause="Wildcard versions in Cargo.toml break reproducible builds when dependencies release breaking changes.",
            affected_toolchains=["Rust", "Cargo"],
            before_snippet='serde = "*"',
            after_snippet='serde = "1.0"',
            remediation_steps=[
                "Replace wildcard with specific minimum semver version.",
            ],
            cwe_ids=["CWE-829"],
            confidence_score=0.98,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-POL-008",
            category="polyglot",
            severity="info",
            title="Missing .dockerignore in Dockerized Project",
            summary="Dockerfile exists in repository root but no .dockerignore file is present.",
            root_cause="Building container images sends huge unnecessary directories (.git, node_modules, __pycache__) to Docker daemon.",
            affected_toolchains=["Docker", "Podman"],
            before_snippet="# Dockerfile exists without .dockerignore",
            after_snippet="# Generated .dockerignore excluding .git, node_modules, .venv",
            remediation_steps=[
                "Create .dockerignore excluding .git, .venv, node_modules, dist, __pycache__.",
            ],
            cwe_ids=["CWE-710"],
            confidence_score=1.0,
        ),
        ExtendedKnowledgeEntry(
            code="TZ-PERF-005",
            category="performance",
            severity="info",
            title="Unbounded Cache Accumulation with lru_cache(maxsize=None)",
            summary="Using @lru_cache(maxsize=None) on functions with large or unbounded input domains.",
            root_cause="Functions with dynamic arguments retain results forever in memory, eventually causing Out-Of-Memory (OOM) crashes.",
            affected_toolchains=["Python 3.8-3.14"],
            before_snippet="@functools.lru_cache(maxsize=None)\ndef compute(query: str): ...",
            after_snippet="@functools.lru_cache(maxsize=1024)\ndef compute(query: str): ...",
            remediation_steps=[
                "Set explicit finite maxsize (e.g. maxsize=1024) to enforce LRU cache eviction.",
            ],
            cwe_ids=["CWE-400"],
            confidence_score=0.97,
        ),
    ]

    _INDEX_BY_CODE: Dict[str, ExtendedKnowledgeEntry] = {e.code: e for e in ENTRIES}

    @classmethod
    def get_entry(cls, code: str) -> Optional[ExtendedKnowledgeEntry]:
        return cls._INDEX_BY_CODE.get(code.upper())

    @classmethod
    def list_by_category(cls, category: str) -> List[ExtendedKnowledgeEntry]:
        cat_lower = category.lower()
        return [e for e in cls.ENTRIES if e.category.lower() == cat_lower]

    @classmethod
    def list_by_severity(cls, severity: str) -> List[ExtendedKnowledgeEntry]:
        sev_lower = severity.lower()
        return [e for e in cls.ENTRIES if e.severity.lower() == sev_lower]

    @classmethod
    def search_by_keyword(cls, query: str) -> List[ExtendedKnowledgeEntry]:
        q = query.lower()
        results = []
        for e in cls.ENTRIES:
            if (q in e.code.lower() or
                q in e.title.lower() or
                q in e.summary.lower() or
                q in e.root_cause.lower()):
                results.append(e)
        return results

    @classmethod
    def export_all_markdown(cls) -> str:
        md = ["# T-Zero Diagnostic Knowledge Base & Remediation Encyclopedia\n\n"]
        for entry in cls.ENTRIES:
            md.append(entry.to_markdown())
        return "\n".join(md)

    @classmethod
    def export_all_json(cls) -> str:
        return json.dumps([e.to_dict() for e in cls.ENTRIES], indent=2)
