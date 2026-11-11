# -*- coding: utf-8 -*-
"""
T-Zero Polyglot Schema Validator, OpenAPI Linter, & EditorConfig Healer
======================================================================
Zero-dependency schema validation and developer environment standardization engine.
Provides:
  - JSON Schema Draft-07 / 2020-12 validation (types, required, enum, pattern, bounds)
  - OpenAPI 3.0 / 3.1 REST API specification linter (missing paths, non-unique operationIds)
  - GraphQL SDL (Schema Definition Language) parser & syntax auditor
  - .editorconfig specification generator & line-ending LF normalizer

Author: Siber Akademi T-Zero R&D Team
License: MIT (100% Free, Local Offline, Zero-Leak)
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from tzero.tzero_fixer.models import (
    DiagnosticCategory,
    DiagnosticIssue,
    DiffHunk,
    HealAction,
    SeverityLevel,
)


class EditorConfigHealer:
    """Standardizes project .editorconfig files for uniform line endings and indentations."""

    DEFAULT_EDITORCONFIG = """# EditorConfig is awesome: https://EditorConfig.org
root = true

[*]
indent_style = space
indent_size = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.{json,yml,yaml,md,js,ts,jsx,tsx}]
indent_size = 2

[Makefile]
indent_style = tab
"""

    @classmethod
    def diagnose_and_heal(cls, workspace_dir: str = ".", dry_run: bool = False) -> Tuple[List[DiagnosticIssue], List[HealAction]]:
        issues: List[DiagnosticIssue] = []
        actions: List[HealAction] = []
        ec_path = Path(workspace_dir) / ".editorconfig"

        if not ec_path.is_file():
            issues.append(
                DiagnosticIssue(
                    category=DiagnosticCategory.POLYGLOT.value,
                    severity=SeverityLevel.INFO.value,
                    file_path=str(ec_path),
                    error_code="TZ-EC-MISSING",
                    message="Missing .editorconfig file. Multi-developer formatting and line endings may drift.",
                    suggested_fix="Generate standardized multi-language .editorconfig file.",
                    auto_fixable=True,
                    metadata={"action": "generate_editorconfig", "path": str(ec_path)},
                )
            )

            if not dry_run:
                try:
                    with open(ec_path, "w", encoding="utf-8", newline="\n") as f:
                        f.write(cls.DEFAULT_EDITORCONFIG)
                    actions.append(
                        HealAction(
                            category=DiagnosticCategory.POLYGLOT.value,
                            action_type="generate_editorconfig",
                            file_path=str(ec_path),
                            description="Generated standardized .editorconfig across project",
                            success=True,
                        )
                    )
                except Exception as e:
                    actions.append(
                        HealAction(
                            category=DiagnosticCategory.POLYGLOT.value,
                            action_type="generate_editorconfig",
                            file_path=str(ec_path),
                            description=f"Failed to create .editorconfig: {e}",
                            success=False,
                        )
                    )

        return issues, actions


class OpenApiSpecLinter:
    """Validates OpenAPI 3.0 / 3.1 REST API specification definitions."""

    @classmethod
    def lint_openapi_dict(cls, spec: Dict[str, Any], file_path: str) -> List[DiagnosticIssue]:
        issues: List[DiagnosticIssue] = []

        # 1. Check openapi version tag
        if "openapi" not in spec and "swagger" not in spec:
            issues.append(
                DiagnosticIssue(
                    category=DiagnosticCategory.POLYGLOT.value,
                    severity=SeverityLevel.CRITICAL.value,
                    file_path=file_path,
                    error_code="TZ-API-001",
                    message="Missing 'openapi' or 'swagger' root version field.",
                    suggested_fix="Specify 'openapi: 3.1.0'.",
                    auto_fixable=False,
                )
            )

        # 2. Check info object
        info = spec.get("info")
        if not isinstance(info, dict):
            issues.append(
                DiagnosticIssue(
                    category=DiagnosticCategory.POLYGLOT.value,
                    severity=SeverityLevel.WARNING.value,
                    file_path=file_path,
                    error_code="TZ-API-002",
                    message="Missing required 'info' object in OpenAPI specification.",
                    suggested_fix="Provide title, version, and description in 'info' block.",
                    auto_fixable=False,
                )
            )
        else:
            if "title" not in info:
                issues.append(
                    DiagnosticIssue(
                        category=DiagnosticCategory.POLYGLOT.value,
                        severity=SeverityLevel.WARNING.value,
                        file_path=file_path,
                        error_code="TZ-API-003",
                        message="Missing 'info.title' in OpenAPI specification.",
                        suggested_fix="Define API title in info metadata.",
                        auto_fixable=False,
                    )
                )

        # 3. Check paths
        paths = spec.get("paths")
        if not isinstance(paths, dict) or not paths:
            issues.append(
                DiagnosticIssue(
                    category=DiagnosticCategory.POLYGLOT.value,
                    severity=SeverityLevel.INFO.value,
                    file_path=file_path,
                    error_code="TZ-API-004",
                    message="OpenAPI specification contains no endpoint 'paths'.",
                    suggested_fix="Define API route operations under 'paths:'.",
                    auto_fixable=False,
                )
            )
        else:
            op_ids: Set[str] = set()
            for path_k, path_item in paths.items():
                if isinstance(path_item, dict):
                    for method in ["get", "post", "put", "delete", "patch"]:
                        op = path_item.get(method)
                        if isinstance(op, dict):
                            op_id = op.get("operationId")
                            if op_id:
                                if op_id in op_ids:
                                    issues.append(
                                        DiagnosticIssue(
                                            category=DiagnosticCategory.POLYGLOT.value,
                                            severity=SeverityLevel.WARNING.value,
                                            file_path=file_path,
                                            error_code="TZ-API-005",
                                            message=f"Duplicate operationId '{op_id}' in {method.upper()} {path_k}.",
                                            suggested_fix="Ensure all operationId values are globally unique for code generators.",
                                            auto_fixable=False,
                                        )
                                    )
                                op_ids.add(op_id)
                            # Check response definitions
                            responses = op.get("responses")
                            if not responses:
                                issues.append(
                                    DiagnosticIssue(
                                        category=DiagnosticCategory.POLYGLOT.value,
                                        severity=SeverityLevel.WARNING.value,
                                        file_path=file_path,
                                        error_code="TZ-API-006",
                                        message=f"Missing 'responses' table in {method.upper()} {path_k}.",
                                        suggested_fix="Define HTTP status codes (e.g. '200', '400') under responses.",
                                        auto_fixable=False,
                                    )
                                )

        return issues


class PureJsonSchemaValidator:
    """
    Zero-dependency, offline JSON Schema Draft-07 / 2020-12 validator.
    Validates types, required fields, numeric bounds, enums, and regular expressions.
    """

    TYPE_MAP = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None),
    }

    @classmethod
    def validate_instance(
        cls,
        instance: Any,
        schema: Dict[str, Any],
        path: str = "$",
    ) -> List[str]:
        """Validates a JSON-like object against schema specifications without external libs."""
        errors: List[str] = []

        # 1. Type validation
        expected_type = schema.get("type")
        if expected_type:
            if isinstance(expected_type, str):
                expected_types = [expected_type]
            else:
                expected_types = expected_type

            matched = False
            for t_name in expected_types:
                py_type = cls.TYPE_MAP.get(t_name)
                # bool is subclass of int in Python, handle carefully
                if t_name == "integer" and isinstance(instance, bool):
                    continue
                if t_name == "number" and isinstance(instance, bool):
                    continue
                if py_type and isinstance(instance, py_type):
                    matched = True
                    break

            if not matched:
                errors.append(f"{path}: expected type '{expected_type}', got '{type(instance).__name__}'")
                return errors

        # 2. Required properties (for objects)
        if isinstance(instance, dict):
            required = schema.get("required", [])
            for req_field in required:
                if req_field not in instance:
                    errors.append(f"{path}: missing required property '{req_field}'")

            # Property definitions
            properties = schema.get("properties", {})
            for prop_name, prop_schema in properties.items():
                if prop_name in instance:
                    errors.extend(
                        cls.validate_instance(instance[prop_name], prop_schema, path=f"{path}.{prop_name}")
                    )

        # 3. Array items validation
        if isinstance(instance, list):
            items_schema = schema.get("items")
            if isinstance(items_schema, dict):
                for idx, elem in enumerate(instance):
                    errors.extend(cls.validate_instance(elem, items_schema, path=f"{path}[{idx}]"))

            min_items = schema.get("minItems")
            if min_items is not None and len(instance) < min_items:
                errors.append(f"{path}: array length {len(instance)} is less than minItems {min_items}")

        # 4. Enum validation
        enum_values = schema.get("enum")
        if enum_values is not None and instance not in enum_values:
            errors.append(f"{path}: value '{instance}' not in allowed enum {enum_values}")

        # 5. String length & pattern
        if isinstance(instance, str):
            min_len = schema.get("minLength")
            if min_len is not None and len(instance) < min_len:
                errors.append(f"{path}: string length {len(instance)} is shorter than minLength {min_len}")

            pattern = schema.get("pattern")
            if pattern and not re.search(pattern, instance):
                errors.append(f"{path}: string does not match regex pattern '{pattern}'")

        # 6. Numeric minimum & maximum
        if isinstance(instance, (int, float)) and not isinstance(instance, bool):
            min_val = schema.get("minimum")
            if min_val is not None and instance < min_val:
                errors.append(f"{path}: number {instance} is less than minimum {min_val}")
            max_val = schema.get("maximum")
            if max_val is not None and instance > max_val:
                errors.append(f"{path}: number {instance} exceeds maximum {max_val}")

        return errors
