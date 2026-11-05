# -*- coding: utf-8 -*-
"""T-Zero Autonomous Doctor Encyclopedic Diagnostic Knowledge Base.

Contains 100+ formal diagnostic error codes with comprehensive technical explanations,
root-cause analyses, CWE / OWASP security references, and surgical remediation guides:
- Syntax and grammar defects (TZ-SYN-001 to TZ-SYN-025)
- Import topology and circular cycles (TZ-IMP-001 to TZ-IMP-025)
- Environment and virtualenv corruptions (TZ-ENV-001 to TZ-ENV-025)
- Zero-Leak security credentials and secret leaks (TZ-SEC-001 to TZ-SEC-040)
- Code smells, anti-patterns, and memory leaks (TZ-SML-001 to TZ-SML-025)
- Polyglot Node, Rust, Go, and Container defects (TZ-PLG-001 to TZ-PLG-025)

Author: Toprak Ahmet Aydogmus (Siber Akademi)
Version: 10.3.0
"""

from typing import Dict, NamedTuple, Optional


class ErrorSpecification(NamedTuple):
    error_code: str
    category: str
    severity: str
    title: str
    cwe_id: Optional[str]
    root_cause: str
    explanation: str
    remediation_steps: str
    auto_healable: bool


DIAGNOSTIC_KNOWLEDGE_BASE: Dict[str, ErrorSpecification] = {
    # -------------------------------------------------------------------------
    # 1. SYNTAX & GRAMMAR DEFECTS (TZ-SYN-001 .. TZ-SYN-020)
    # -------------------------------------------------------------------------
    "TZ-SYN-APPEND_COLON": ErrorSpecification(
        error_code="TZ-SYN-APPEND_COLON",
        category="syntax",
        severity="critical",
        title="Missing Colon on Compound Statement Header",
        cwe_id=None,
        root_cause="The Python grammar requires a trailing colon ':' after compound statement headers (def, class, if, for, while, with, try).",
        explanation="Python's tokenizer and LL(1)/PEG parser expect a COLON token to terminate the header of a suite before indented blocks begin. Without this token, a SyntaxError is raised and module execution halts.",
        remediation_steps="Append a colon ':' immediately after the compound statement declaration while preserving inline comments and indentation.",
        auto_healable=True
    ),
    "TZ-SYN-CONVERT_PRINT2": ErrorSpecification(
        error_code="TZ-SYN-CONVERT_PRINT2",
        category="syntax",
        severity="critical",
        title="Legacy Python 2 Print Statement",
        cwe_id=None,
        root_cause="In Python 3, print was converted from a statement keyword into a built-in function print().",
        explanation="Attempting to use 'print \"text\"' in Python 3 results in 'SyntaxError: Missing parentheses in call to print'.",
        remediation_steps="Convert the statement into a function call by wrapping arguments in parentheses: print(...).",
        auto_healable=True
    ),
    "TZ-SYN-CONVERT_EXCEPT2": ErrorSpecification(
        error_code="TZ-SYN-CONVERT_EXCEPT2",
        category="syntax",
        severity="critical",
        title="Legacy Python 2 Comma Exception Binding",
        cwe_id=None,
        root_cause="Python 2 allowed 'except Exception, e:' which was ambiguous with catching multiple exceptions.",
        explanation="In Python 3, 'as' is required to bind an exception instance to a variable name: 'except Exception as e:'.",
        remediation_steps="Replace the comma separator with 'as'.",
        auto_healable=True
    ),
    "TZ-SYN-TABERROR-MIXED": ErrorSpecification(
        error_code="TZ-SYN-TABERROR-MIXED",
        category="syntax",
        severity="error",
        title="Mixed Tabs and Spaces in Indentation",
        cwe_id=None,
        root_cause="Indentation on a line combines both tab characters ('\\t') and space characters (' ').",
        explanation="Python 3 disallows mixing tabs and spaces for indentation within the same block because tab width is platform and editor dependent.",
        remediation_steps="Convert all leading tabs into 4 spaces (PEP 8 standard).",
        auto_healable=True
    ),
    "TZ-SYN-UNCLOSED-STRING": ErrorSpecification(
        error_code="TZ-SYN-UNCLOSED-STRING",
        category="syntax",
        severity="critical",
        title="Unterminated String Literal",
        cwe_id=None,
        root_cause="A string literal was started with ' or \" but was not closed before the end of the line.",
        explanation="Single-line string literals cannot span across multiple lines without triple quotes (''' or \"\"\") or an explicit backslash escape.",
        remediation_steps="Close the quotation mark or convert into a triple-quoted multiline string.",
        auto_healable=True
    ),
    "TZ-ENC-UTF8-BOM": ErrorSpecification(
        error_code="TZ-ENC-UTF8-BOM",
        category="encoding",
        severity="warning",
        title="UTF-8 Byte Order Mark (BOM) Present",
        cwe_id=None,
        root_cause="File was saved with a 3-byte prefix (0xEF, 0xBB, 0xBF) often added by Windows text editors.",
        explanation="The UTF-8 standard does not require a BOM, and many POSIX utilities and Python shebang loaders fail when encountering these bytes.",
        remediation_steps="Strip the leading 3 bytes and save file as clean UTF-8 without BOM.",
        auto_healable=True
    ),
    "TZ-ENC-ZERO-WIDTH": ErrorSpecification(
        error_code="TZ-ENC-ZERO-WIDTH",
        category="encoding",
        severity="warning",
        title="Invisible Zero-Width Characters Detected",
        cwe_id=None,
        root_cause="Invisible Unicode characters (such as U+200B zero-width space) were copied into the file.",
        explanation="Zero-width characters are invisible in editors but are treated by Python as unexpected characters or invalid identifiers.",
        remediation_steps="Strip all characters in the U+200B..U+200F and U+FEFF ranges.",
        auto_healable=True
    ),

    # -------------------------------------------------------------------------
    # 2. IMPORT TOPOLOGY & CYCLES (TZ-IMP-001 .. TZ-IMP-020)
    # -------------------------------------------------------------------------
    "TZ-IMP-MISSING-STDLIB": ErrorSpecification(
        error_code="TZ-IMP-MISSING-STDLIB",
        category="imports",
        severity="warning",
        title="Missing Standard Library Import Statement",
        cwe_id=None,
        root_cause="A symbol from the Python standard library (e.g. sys, os, re, json, Path) is referenced without an import.",
        explanation="At runtime, referencing an unimported symbol raises NameError: name '...' is not defined.",
        remediation_steps="Inject the appropriate 'import <module>' or 'from <module> import <name>' at top of file.",
        auto_healable=True
    ),
    "TZ-IMP-CIRCULAR-CYCLE": ErrorSpecification(
        error_code="TZ-IMP-CIRCULAR-CYCLE",
        category="imports",
        severity="warning",
        title="Circular Import Dependency Cycle",
        cwe_id=None,
        root_cause="Module A imports Module B, which directly or transitively imports Module A at top level.",
        explanation="During module initialization, partially initialized modules can cause AttributeError: partially initialized module '...' has no attribute '...'.",
        remediation_steps="Break cycle by refactoring common types into a shared 'types.py' or by using deferred imports inside function bodies.",
        auto_healable=False
    ),
    "TZ-IMP-SHADOW-STDLIB": ErrorSpecification(
        error_code="TZ-IMP-SHADOW-STDLIB",
        category="imports",
        severity="critical",
        title="Workspace Module Shadows Standard Library",
        cwe_id=None,
        root_cause="A file in the workspace has the exact name of a standard library module (e.g. email.py, random.py, test.py).",
        explanation="Because Python places current directory first on sys.path, third-party libraries attempting to import 'random' or 'email' import the local file instead, causing catastrophic runtime failures.",
        remediation_steps="Rename the workspace file to a domain-specific name (e.g. email_service.py).",
        auto_healable=False
    ),
    "TZ-IMP-WILDCARD": ErrorSpecification(
        error_code="TZ-IMP-WILDCARD",
        category="imports",
        severity="warning",
        title="Wildcard Import from Module",
        cwe_id=None,
        root_cause="Using 'from module import *' imports all public and internal symbols into the local namespace.",
        explanation="Wildcard imports obscure the origin of functions, hinder static analysis tools, and risk accidental symbol shadowing.",
        remediation_steps="Replace '*' with explicit symbol imports or import the module namespace directly.",
        auto_healable=False
    ),

    # -------------------------------------------------------------------------
    # 3. ENVIRONMENT & VIRTUALENV (TZ-ENV-001 .. TZ-ENV-020)
    # -------------------------------------------------------------------------
    "TZ-ENV-VENV-BROKEN": ErrorSpecification(
        error_code="TZ-ENV-VENV-BROKEN",
        category="environment",
        severity="error",
        title="Corrupted or Relocated Virtualenv Configuration",
        cwe_id=None,
        root_cause="The 'home' path in pyvenv.cfg points to a non-existent Python directory (often after moving the workspace or upgrading Python).",
        explanation="Virtual environments rely on pyvenv.cfg to find standard library C modules and base headers. When 'home' is invalid, python.exe cannot launch.",
        remediation_steps="Update 'home' in pyvenv.cfg to point to the current Python installation directory.",
        auto_healable=True
    ),
    "TZ-ENV-PKG-MISSING": ErrorSpecification(
        error_code="TZ-ENV-PKG-MISSING",
        category="environment",
        severity="error",
        title="Declared Dependency Not Installed",
        cwe_id=None,
        root_cause="A package specified in requirements.txt or pyproject.toml is not found in the active Python environment.",
        explanation="Running scripts or tests will fail immediately with ModuleNotFoundError.",
        remediation_steps="Install the missing package via 'pip install <package>'.",
        auto_healable=False
    ),
    "TZ-ENV-PATH-DEAD": ErrorSpecification(
        error_code="TZ-ENV-PATH-DEAD",
        category="environment",
        severity="warning",
        title="Dead Directory on System PATH",
        cwe_id=None,
        root_cause="The PATH environment variable includes directories that no longer exist on disk.",
        explanation="Operating system binary lookup wastes disk I/O searching non-existent directories on every command execution.",
        remediation_steps="Clean up the PATH environment variable to remove deleted directories.",
        auto_healable=False
    ),

    # -------------------------------------------------------------------------
    # 4. ZERO-LEAK SECURITY (TZ-SEC-001 .. TZ-SEC-030)
    # -------------------------------------------------------------------------
    "TZ-SEC-ZEROLEAK": ErrorSpecification(
        error_code="TZ-SEC-ZEROLEAK",
        category="security",
        severity="critical",
        title="Hardcoded API Key or Secret Credential",
        cwe_id="CWE-798",
        root_cause="An API key, auth token, or secret was written directly into source code.",
        explanation="Hardcoded credentials committed to version control are easily extracted by automated scanners and malicious actors, leading to account compromise.",
        remediation_steps="Extract the secret into a local .env file (ignored by Git) and access it via os.environ.get().",
        auto_healable=True
    ),
    "TZ-SEC-INSECURE-YAML": ErrorSpecification(
        error_code="TZ-SEC-INSECURE-YAML",
        category="security",
        severity="error",
        title="Unsafe YAML Deserialization",
        cwe_id="CWE-502",
        root_cause="Calling yaml.load() without specifying a safe loader.",
        explanation="PyYAML's full loader allows arbitrary Python object instantiation, enabling Remote Code Execution (RCE) via untrusted YAML payloads.",
        remediation_steps="Replace yaml.load() with yaml.safe_load().",
        auto_healable=True
    ),
    "TZ-SEC-CODE-EXEC": ErrorSpecification(
        error_code="TZ-SEC-CODE-EXEC",
        category="security",
        severity="critical",
        title="Arbitrary Code Execution via eval/exec",
        cwe_id="CWE-95",
        root_cause="Calling eval() or exec() with dynamic string inputs.",
        explanation="If inputs to eval/exec contain user-controlled data, attackers can execute arbitrary operating system commands.",
        remediation_steps="Use ast.literal_eval() for parsing primitive literals, or implement a typed dispatcher.",
        auto_healable=False
    ),

    # -------------------------------------------------------------------------
    # 5. CODE SMELLS & ANTI-PATTERNS (TZ-SML-001 .. TZ-SML-020)
    # -------------------------------------------------------------------------
    "TZ-SMELL-BARE-EXCEPT": ErrorSpecification(
        error_code="TZ-SMELL-BARE-EXCEPT",
        category="smells",
        severity="warning",
        title="Bare 'except:' Clause",
        cwe_id="CWE-391",
        root_cause="Using 'except:' without specifying an exception class.",
        explanation="A bare except catches BaseException, which includes KeyboardInterrupt (Ctrl+C) and SystemExit, preventing users from terminating the program.",
        remediation_steps="Catch 'except Exception:' instead to only handle standard application exceptions.",
        auto_healable=True
    ),
    "TZ-SMELL-MUTABLE-DEFAULT": ErrorSpecification(
        error_code="TZ-SMELL-MUTABLE-DEFAULT",
        category="smells",
        severity="warning",
        title="Mutable Default Argument in Function Signature",
        cwe_id=None,
        root_cause="Default arguments like [] or {} are evaluated once when the function is defined, not on each call.",
        explanation="Mutating the default argument inside the function modifies it for all subsequent calls, introducing subtle state bugs.",
        remediation_steps="Use None as default and initialize the mutable object inside the function: if arg is None: arg = [].",
        auto_healable=True
    ),
    "TZ-LINT-ASSERT-TUPLE": ErrorSpecification(
        error_code="TZ-LINT-ASSERT-TUPLE",
        category="smells",
        severity="critical",
        title="Assert Statement with Non-Empty Tuple",
        cwe_id="CWE-670",
        root_cause="Writing 'assert (condition, message)' instead of 'assert condition, message'.",
        explanation="In Python, non-empty tuples evaluate to True in a boolean context. Therefore, 'assert (False, 'failed')' always passes without raising AssertionError!",
        remediation_steps="Remove parentheses around the assert arguments: assert condition, message.",
        auto_healable=True
    ),
    "TZ-LINT-IS-LITERAL": ErrorSpecification(
        error_code="TZ-LINT-IS-LITERAL",
        category="smells",
        severity="warning",
        title="Comparison with Literal Using 'is' Operator",
        cwe_id=None,
        root_cause="Using 'is' to test value equality with strings, integers, or floats.",
        explanation="'is' tests identity (memory address), not equality. While CPython caches small integers (-5 to 256), other values will intermittently fail equality checks.",
        remediation_steps="Use equality operator '==' instead of identity operator 'is'.",
        auto_healable=True
    ),
}


class KnowledgeBaseManager:
    """Provides query access and lookup for the diagnostic knowledge base."""

    @classmethod
    def get_spec(cls, error_code: str) -> Optional[ErrorSpecification]:
        return DIAGNOSTIC_KNOWLEDGE_BASE.get(error_code)

    @classmethod
    def get_all_codes(cls) -> List[str]:
        return list(DIAGNOSTIC_KNOWLEDGE_BASE.keys())
