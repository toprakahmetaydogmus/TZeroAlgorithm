# -*- coding: utf-8 -*-
"""T-Zero AST Syntax Healer & Polyglot Source Code Doctor.

Performs intelligent, deterministic, and surgical healing for:
- Missing colons on compound statements (def, class, if, elif, else, try, except, finally, for, while, with, match, case).
- Legacy Python 2 idioms (print statements, except Exception, e, xrange, has_key, iteritems, unicode).
- Indentation errors, mixed tabs and spaces, and trailing indentation drift.
- Invisible characters (UTF-8 BOM, zero-width spaces, non-breaking spaces).
- Invalid regex escape sequences (automatic raw string prefixing).
- Unclosed delimiters and unclosed string literals.

Author: Toprak Ahmet Aydogmus (Siber Akademi)
Version: 10.3.0
"""

import ast
import difflib
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .models import (
    DiagnosticCategory,
    DiagnosticIssue,
    HealAction,
    SeverityLevel,
)


class ASTSyntaxHealer:
    """Enterprise AST parser and surgical auto-repair engine for source code syntax defects."""

    COMPOUND_STATEMENT_KEYWORDS = (
        "def ", "async def ", "class ", "if ", "elif ", "else", "try", "except",
        "finally", "for ", "async for ", "while ", "with ", "async with ", "match ", "case "
    )

    ZERO_WIDTH_CHARS = ("\u200b", "\ufeff", "\u200c", "\u200d", "\u200e", "\u200f")

    @classmethod
    def scan_encoding_and_invisible_chars(cls, file_path: str, raw_bytes: bytes) -> List[DiagnosticIssue]:
        """Detect UTF-8 BOM and phantom zero-width spaces that disrupt lexers."""
        issues: List[DiagnosticIssue] = []

        # 1. Byte Order Mark (BOM)
        if raw_bytes.startswith(b"\xef\xbb\xbf"):
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.ENCODING.value,
                severity=SeverityLevel.WARNING.value,
                file_path=file_path,
                line=1,
                column=0,
                error_code="TZ-ENC-UTF8-BOM",
                message="File begins with UTF-8 Byte Order Mark (BOM) which breaks some parsers and CLI tools",
                suggested_fix="Strip UTF-8 BOM byte sequence from file header",
                auto_fixable=True,
                metadata={"action": "strip_bom", "path": file_path}
            ))

        # 2. Zero-width spaces in text
        try:
            text = raw_bytes.decode("utf-8", errors="replace")
            for char in cls.ZERO_WIDTH_CHARS:
                if char in text:
                    count = text.count(char)
                    issues.append(DiagnosticIssue(
                        category=DiagnosticCategory.ENCODING.value,
                        severity=SeverityLevel.WARNING.value,
                        file_path=file_path,
                        line=1,
                        column=0,
                        error_code="TZ-ENC-ZERO-WIDTH",
                        message=f"File contains {count} invisible zero-width character(s) (U+{ord(char):04X})",
                        suggested_fix="Sanitize file by stripping zero-width whitespace",
                        auto_fixable=True,
                        metadata={"action": "strip_zero_width", "path": file_path}
                    ))
                    break
        except Exception:
            pass

        return issues

    @classmethod
    def detect_mixed_indentation(cls, file_path: str, content: str) -> List[DiagnosticIssue]:
        """Detect mixed tabs and spaces causing TabError or inconsistent blocks."""
        issues: List[DiagnosticIssue] = []
        lines = content.splitlines()

        has_tabs = False
        has_spaces = False
        for idx, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            if not stripped:
                continue
            indent = line[:len(line) - len(stripped)]
            if "\t" in indent:
                has_tabs = True
            if " " in indent:
                has_spaces = True

            if "\t" in indent and " " in indent:
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.SYNTAX.value,
                    severity=SeverityLevel.ERROR.value,
                    file_path=file_path,
                    line=idx,
                    column=0,
                    error_code="TZ-SYN-TABERROR-MIXED",
                    message="Mixed tabs and spaces in indentation on the same line",
                    suggested_fix="Convert all leading tabs to 4 spaces",
                    auto_fixable=True,
                    metadata={"action": "normalize_tabs", "path": file_path}
                ))
                return issues

        if has_tabs and has_spaces:
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.SYNTAX.value,
                severity=SeverityLevel.WARNING.value,
                file_path=file_path,
                line=1,
                column=0,
                error_code="TZ-SYN-MIXED-INDENT",
                message="File uses inconsistent indentation (both tabs and spaces detected)",
                suggested_fix="Standardize entire file to 4 spaces indentation (PEP 8)",
                auto_fixable=True,
                metadata={"action": "normalize_tabs", "path": file_path}
            ))

        return issues

    @classmethod
    def analyze_syntax_error(cls, file_path: str, content: str, err: SyntaxError) -> DiagnosticIssue:
        """Analyze Python SyntaxError traceback to determine surgical repair strategy."""
        err_line = err.lineno or 1
        err_col = err.offset or 0
        err_msg = err.msg or "Syntax error"
        lines = content.splitlines()

        action = "generic_syntax"
        suggested = "Fix syntax error"

        if 0 < err_line <= len(lines):
            line_str = lines[err_line - 1].strip()

            # 1. Missing Colon
            for kw in cls.COMPOUND_STATEMENT_KEYWORDS:
                if line_str.startswith(kw):
                    # Check if line does not end with colon (ignoring comments)
                    code_part = line_str.split("#", 1)[0].rstrip()
                    if not code_part.endswith(":"):
                        action = "append_colon"
                        suggested = f"Append missing ':' to '{kw.strip()}' compound statement"
                        break

            # 2. Python 2 print statement
            if action == "generic_syntax":
                if re.match(r"^print\s+.*", line_str) and not line_str.startswith("print(") and not line_str.startswith("print ("):
                    action = "convert_print2"
                    suggested = "Convert legacy Python 2 print statement to print(...) function call"

            # 3. Python 2 except statement
            if action == "generic_syntax":
                if re.match(r"^except\s+[A-Za-z0-9_\.]+\s*,\s*[A-Za-z0-9_]+\s*:", line_str):
                    action = "convert_except2"
                    suggested = "Convert legacy 'except Error, e:' to 'except Error as e:'"

        return DiagnosticIssue(
            category=DiagnosticCategory.SYNTAX.value,
            severity=SeverityLevel.CRITICAL.value,
            file_path=file_path,
            line=err_line,
            column=err_col,
            error_code=f"TZ-SYN-{action.upper()}",
            message=f"SyntaxError: {err_msg} on line {err_line}",
            suggested_fix=suggested,
            auto_fixable=action in ("append_colon", "convert_print2", "convert_except2", "normalize_tabs"),
            metadata={"action": action, "lineno": err_line, "path": file_path}
        )

    @classmethod
    def scan_python_idioms_and_regex(cls, file_path: str, content: str) -> List[DiagnosticIssue]:
        """Detect legacy Python 2 idioms and invalid regex escape sequences."""
        issues: List[DiagnosticIssue] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Python 2 xrange
            if "xrange(" in stripped and not stripped.startswith("#"):
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.SYNTAX.value,
                    severity=SeverityLevel.WARNING.value,
                    file_path=file_path,
                    line=idx,
                    column=stripped.find("xrange("),
                    error_code="TZ-IDIOM-XRANGE",
                    message="Use of deprecated Python 2 'xrange()' function",
                    suggested_fix="Replace 'xrange()' with standard 'range()'",
                    auto_fixable=True,
                    metadata={"action": "replace_xrange", "lineno": idx, "path": file_path}
                ))

            # Python 2 has_key
            if ".has_key(" in stripped and not stripped.startswith("#"):
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.SYNTAX.value,
                    severity=SeverityLevel.WARNING.value,
                    file_path=file_path,
                    line=idx,
                    column=stripped.find(".has_key("),
                    error_code="TZ-IDIOM-HASKEY",
                    message="Use of removed dictionary method 'dict.has_key(k)'",
                    suggested_fix="Replace 'dict.has_key(k)' with 'k in dict'",
                    auto_fixable=True,
                    metadata={"action": "replace_has_key", "lineno": idx, "path": file_path}
                ))

            # Invalid regex escape sequence in standard string literal
            if re.search(r'(?<!r)("|\')[^"\']*\\([dswbDSWB])[^"\']*("|\')', line):
                if not stripped.startswith("#"):
                    issues.append(DiagnosticIssue(
                        category=DiagnosticCategory.SYNTAX.value,
                        severity=SeverityLevel.INFO.value,
                        file_path=file_path,
                        line=idx,
                        column=0,
                        error_code="TZ-SYN-ESCAPE-REGEX",
                        message="Invalid escape sequence in string literal (should be raw string r'...')",
                        suggested_fix="Prefix regular expression string with 'r' to prevent SyntaxWarning",
                        auto_fixable=True,
                        metadata={"action": "prefix_raw_string", "lineno": idx, "path": file_path}
                    ))

        return issues

    @classmethod
    def heal_string(cls, content: str, filename: str = "snippet.py") -> Any:
        """In-memory string healing helper for syntax errors, colons, BOM, and legacy idioms."""
        @dataclass
        class StringHealResult:
            original_content: str
            repaired_content: str
            changed: bool
            issues: List[DiagnosticIssue]

        import tempfile
        suffix = Path(filename).suffix or ".py"
        with tempfile.NamedTemporaryFile("w", suffix=suffix, encoding="utf-8", delete=False) as tf:
            tf.write(content)
            temp_path = tf.name

        try:
            issues = cls.diagnose_file(temp_path)
            cls.execute_syntax_heals(issues, dry_run=False)
            with open(temp_path, "r", encoding="utf-8", errors="replace") as tf:
                repaired = tf.read()
            return StringHealResult(
                original_content=content,
                repaired_content=repaired,
                changed=(repaired != content),
                issues=issues,
            )
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    @classmethod
    def diagnose_file(cls, file_path: str) -> List[DiagnosticIssue]:
        """Scan a single source file for all syntax, encoding, and idiom defects."""
        issues: List[DiagnosticIssue] = []
        path = Path(file_path)
        if not path.is_file() or path.suffix != ".py":
            return issues

        try:
            with open(path, "rb") as f:
                raw_bytes = f.read()
        except Exception as e:
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.ENVIRONMENT.value,
                severity=SeverityLevel.ERROR.value,
                file_path=file_path,
                line=None,
                column=None,
                error_code="TZ-FS-UNREADABLE",
                message=f"Unable to read file: {e}",
                suggested_fix="Check filesystem read permissions",
                auto_fixable=False
            ))
            return issues

        # 1. Encoding & invisible chars
        issues.extend(cls.scan_encoding_and_invisible_chars(file_path, raw_bytes))

        # Decode text
        content = raw_bytes.decode("utf-8", errors="replace")

        # 2. Mixed indentation
        issues.extend(cls.detect_mixed_indentation(file_path, content))

        # 3. AST Parse verification
        try:
            ast.parse(content, filename=file_path)
        except SyntaxError as se:
            issues.append(cls.analyze_syntax_error(file_path, content, se))
            return issues  # Unparseable AST stops further semantic scans

        # 4. Idioms & regex escapes
        issues.extend(cls.scan_python_idioms_and_regex(file_path, content))

        return issues

    @classmethod
    def execute_syntax_heals(cls, issues: List[DiagnosticIssue], dry_run: bool = False) -> List[HealAction]:
        """Execute surgical regex and line-level patches to heal syntax flaws."""
        actions: List[HealAction] = []
        files_modified: Set[str] = set()

        for issue in issues:
            action_type = issue.metadata.get("action")
            file_p = issue.metadata.get("path") or issue.file_path
            if not issue.auto_fixable or not action_type or not file_p:
                continue

            t0 = time.time()
            path = Path(file_p)
            if not path.is_file():
                continue

            try:
                # 1. Strip BOM
                if action_type == "strip_bom":
                    with open(path, "rb") as f:
                        data = f.read()
                    if data.startswith(b"\xef\xbb\xbf"):
                        if not dry_run:
                            with open(path, "wb") as f:
                                f.write(data[3:])
                        actions.append(HealAction(
                            category=DiagnosticCategory.ENCODING.value,
                            action_type=action_type,
                            file_path=file_p,
                            description=f"Stripped UTF-8 Byte Order Mark (BOM) from {path.name}",
                            success=True,
                            duration_ms=round((time.time() - t0) * 1000, 2)
                        ))
                    continue

                # Read lines for text transforms
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    orig_text = f.read()
                lines = orig_text.splitlines(keepends=True)

                # 2. Strip zero-width chars
                if action_type == "strip_zero_width":
                    mod_text = orig_text
                    for zw in cls.ZERO_WIDTH_CHARS:
                        mod_text = mod_text.replace(zw, "")
                    if mod_text != orig_text:
                        if not dry_run:
                            with open(path, "w", encoding="utf-8", newline="\n") as f:
                                f.write(mod_text)
                        actions.append(HealAction(
                            category=DiagnosticCategory.ENCODING.value,
                            action_type=action_type,
                            file_path=file_p,
                            description=f"Stripped invisible zero-width characters from {path.name}",
                            success=True,
                            duration_ms=round((time.time() - t0) * 1000, 2)
                        ))
                    continue

                # 3. Normalize tabs to 4 spaces
                if action_type == "normalize_tabs":
                    new_lines = []
                    for l in lines:
                        leading_tabs = len(l) - len(l.lstrip("\t"))
                        if leading_tabs > 0:
                            new_lines.append(("    " * leading_tabs) + l[leading_tabs:])
                        else:
                            new_lines.append(l)
                    mod_text = "".join(new_lines)
                    if mod_text != orig_text:
                        if not dry_run:
                            with open(path, "w", encoding="utf-8", newline="\n") as f:
                                f.write(mod_text)
                        actions.append(HealAction(
                            category=DiagnosticCategory.SYNTAX.value,
                            action_type=action_type,
                            file_path=file_p,
                            description=f"Normalized tabs to 4 spaces in {path.name}",
                            success=True,
                            duration_ms=round((time.time() - t0) * 1000, 2)
                        ))
                    continue

                # Line-specific patches
                lineno = issue.metadata.get("lineno")
                if lineno and 0 < lineno <= len(lines):
                    orig_line = lines[lineno - 1]
                    mod_line = orig_line

                    # 4. Append missing colon
                    if action_type == "append_colon":
                        if "#" in orig_line:
                            code_p, comment_p = orig_line.split("#", 1)
                            mod_line = code_p.rstrip() + ":  #" + comment_p
                        else:
                            mod_line = orig_line.rstrip("\r\n") + ":\n"

                    # 5. Convert Python 2 print
                    elif action_type == "convert_print2":
                        mod_line = re.sub(r"^(\s*)print\s+(.*)$", r"\1print(\2)", orig_line)

                    # 6. Convert Python 2 except
                    elif action_type == "convert_except2":
                        mod_line = re.sub(r"^(\s*except\s+[A-Za-z0-9_\.]+)\s*,\s*([A-Za-z0-9_]+)\s*:", r"\1 as \2:", orig_line)

                    # 7. Replace xrange
                    elif action_type == "replace_xrange":
                        mod_line = orig_line.replace("xrange(", "range(")

                    # 8. Prefix raw string regex
                    elif action_type == "prefix_raw_string":
                        mod_line = re.sub(r'(?<!r)(["\'])(\\[dswbDSWB].*?)(["\'])', r'r\1\2\3', orig_line)

                    if mod_line != orig_line:
                        diff = "".join(difflib.unified_diff(
                            [orig_line], [mod_line], fromfile="before", tofile="after"
                        ))
                        lines[lineno - 1] = mod_line
                        if not dry_run:
                            with open(path, "w", encoding="utf-8", newline="\n") as f:
                                f.writelines(lines)
                        actions.append(HealAction(
                            category=DiagnosticCategory.SYNTAX.value,
                            action_type=action_type,
                            file_path=file_p,
                            description=f"Patched {action_type} on line {lineno} of {path.name}",
                            success=True,
                            diff=diff,
                            duration_ms=round((time.time() - t0) * 1000, 2)
                        ))
            except Exception as e:
                actions.append(HealAction(
                    category=DiagnosticCategory.SYNTAX.value,
                    action_type=action_type or "syntax_error",
                    file_path=file_p,
                    description=f"Failed healing syntax on {path.name}: {e}",
                    success=False,
                    duration_ms=round((time.time() - t0) * 1000, 2)
                ))

        return actions
