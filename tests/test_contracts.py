# -*- coding: utf-8 -*-
"""Unit tests for T-Zero Public API Contract & SemVer Guardian (tzero_contracts.py)."""

import json
import subprocess
import sys
import unittest
from tzero_contracts import (
    ASTContractExtractor,
    ASTContractComparator,
    ContractDiffReport,
    ContractViolation,
    SemVerBump,
)


class TestASTContractExtractor(unittest.TestCase):
    def test_extract_function_contract(self):
        code = '''
def process_data(item: str, count: int = 1, *args, timeout: float = 5.0, **kwargs) -> bool:
    """Process input items."""
    return True
'''
        funcs, classes = ASTContractExtractor.extract_from_code(code)
        self.assertIn("process_data", funcs)
        fc = funcs["process_data"]
        self.assertEqual(fc.name, "process_data")
        self.assertEqual(fc.required_param_count, 1)  # only 'item' is required
        self.assertEqual(fc.return_annotation, "bool")
        self.assertEqual(fc.docstring, "Process input items.")
        self.assertFalse(fc.is_async)

        param_names = [p.name for p in fc.parameters]
        self.assertIn("item", param_names)
        self.assertIn("count", param_names)
        self.assertIn("*args", param_names)
        self.assertIn("timeout", param_names)
        self.assertIn("**kwargs", param_names)

    def test_extract_class_contract(self):
        code = '''
class DataEngine:
    """Data processing engine."""
    def __init__(self, name: str):
        self.name = name

    def compute(self, factor: int) -> int:
        return factor * 2

    def _internal_helper(self):
        pass
'''
        funcs, classes = ASTContractExtractor.extract_from_code(code)
        self.assertIn("DataEngine", classes)
        cc = classes["DataEngine"]
        self.assertEqual(cc.name, "DataEngine")
        self.assertIn("__init__", cc.methods)
        self.assertIn("compute", cc.methods)
        # Private method with single leading underscore should be skipped from public contract
        self.assertNotIn("_internal_helper", cc.methods)


class TestASTContractComparator(unittest.TestCase):
    def test_breaking_removed_function(self):
        old_code = "def calculate_tax(amount: float) -> float:\n    return amount * 0.2\n"
        new_code = "# calculate_tax removed\n"
        report = ASTContractComparator.compare_code(old_code, new_code, "tax.py")
        self.assertTrue(report.is_breaking)
        self.assertEqual(report.semver_bump, SemVerBump.MAJOR)
        self.assertEqual(len(report.breaking_changes), 1)
        self.assertEqual(report.breaking_changes[0].category, "REMOVED_FUNCTION")

    def test_breaking_removed_method(self):
        old_code = "class Worker:\n    def start(self):\n        pass\n    def stop(self):\n        pass\n"
        new_code = "class Worker:\n    def start(self):\n        pass\n"
        report = ASTContractComparator.compare_code(old_code, new_code, "worker.py")
        self.assertTrue(report.is_breaking)
        self.assertEqual(report.semver_bump, SemVerBump.MAJOR)
        self.assertEqual(report.breaking_changes[0].category, "REMOVED_METHOD")

    def test_breaking_added_required_param(self):
        old_code = "def send_email(to_addr: str) -> bool:\n    return True\n"
        new_code = "def send_email(to_addr: str, api_key: str) -> bool:\n    return True\n"
        report = ASTContractComparator.compare_code(old_code, new_code, "mailer.py")
        self.assertTrue(report.is_breaking)
        self.assertEqual(report.semver_bump, SemVerBump.MAJOR)
        self.assertEqual(report.breaking_changes[0].category, "REQUIRED_PARAMETER_ADDED")

    def test_minor_added_optional_param(self):
        old_code = "def send_email(to_addr: str) -> bool:\n    return True\n"
        new_code = "def send_email(to_addr: str, retries: int = 3) -> bool:\n    return True\n"
        report = ASTContractComparator.compare_code(old_code, new_code, "mailer.py")
        self.assertFalse(report.is_breaking)
        self.assertEqual(report.semver_bump, SemVerBump.MINOR)
        self.assertEqual(len(report.non_breaking_additions), 1)

    def test_minor_added_new_function(self):
        old_code = "def existing_fn():\n    pass\n"
        new_code = "def existing_fn():\n    pass\n\ndef new_feature():\n    pass\n"
        report = ASTContractComparator.compare_code(old_code, new_code, "features.py")
        self.assertFalse(report.is_breaking)
        self.assertEqual(report.semver_bump, SemVerBump.MINOR)
        self.assertEqual(report.non_breaking_additions[0].category, "ADDED_FUNCTION")

    def test_patch_internal_refactor(self):
        old_code = "def compute(x: int) -> int:\n    return x + 1\n"
        new_code = "def compute(x: int) -> int:\n    # Refactored for performance\n    res = x + 1\n    return res\n"
        report = ASTContractComparator.compare_code(old_code, new_code, "math_utils.py")
        self.assertFalse(report.is_breaking)
        self.assertEqual(report.semver_bump, SemVerBump.PATCH)
        self.assertEqual(len(report.breaking_changes), 0)
        self.assertEqual(len(report.non_breaking_additions), 0)

    def test_format_markdown_report(self):
        old_code = "def query(term: str) -> list:\n    return []\n"
        new_code = "def query(term: str, strict: bool = False) -> list:\n    return []\n"
        report = ASTContractComparator.compare_code(old_code, new_code, "search.py")
        md = ASTContractComparator.format_markdown_report([report])
        self.assertIn("T-Zero Public API Contract & SemVer Guardian", md)
        self.assertIn("MINOR (FEATURE)", md)
        self.assertIn("search.py", md)


class TestPolyglotContracts(unittest.TestCase):
    def test_typescript_contracts_extraction(self):
        code = '''
export function add(a: number, b?: number): number {
    return a + (b || 0);
}

export class Calculator {
    compute(factor: number): number {
        return factor * 2;
    }
}
'''
        funcs, classes = ASTContractExtractor.extract_polyglot_contracts(code, "calc.ts")
        self.assertIn("add", funcs)
        fc = funcs["add"]
        self.assertEqual(fc.required_param_count, 1)
        self.assertEqual(fc.return_annotation, "number")
        self.assertTrue(fc.parameters[1].has_default)

        self.assertIn("Calculator", classes)
        self.assertIn("compute", classes["Calculator"].methods)

    def test_typescript_breaking_param_added(self):
        old_code = "export function processData(input: string): boolean { return true; }"
        new_code = "export function processData(input: string, options: any): boolean { return true; }"
        report = ASTContractComparator.compare_code(old_code, new_code, "service.ts")
        self.assertTrue(report.is_breaking)
        self.assertEqual(report.semver_bump, SemVerBump.MAJOR)
        self.assertEqual(report.breaking_changes[0].category, "REQUIRED_PARAMETER_ADDED")

    def test_typescript_breaking_param_removed(self):
        old_code = "export function processData(input: string, token: string): boolean { return true; }"
        new_code = "export function processData(input: string): boolean { return true; }"
        report = ASTContractComparator.compare_code(old_code, new_code, "service.ts")
        self.assertTrue(report.is_breaking)
        self.assertEqual(report.semver_bump, SemVerBump.MAJOR)
        self.assertEqual(report.breaking_changes[0].category, "REMOVED_PARAMETER")

    def test_typescript_optional_param_added(self):
        old_code = "export function processData(input: string): boolean { return true; }"
        new_code = "export function processData(input: string, retries?: number): boolean { return true; }"
        report = ASTContractComparator.compare_code(old_code, new_code, "service.ts")
        self.assertFalse(report.is_breaking)
        self.assertEqual(report.semver_bump, SemVerBump.MINOR)
        self.assertEqual(report.non_breaking_additions[0].category, "OPTIONAL_PARAMETER_ADDED")

    def test_go_exported_and_unexported(self):
        code = '''
package server

func Exported(a string, b int) error {
    return nil
}

func helper(a string) {
}

func (s *Server) Handle(req string) bool {
    return true
}
'''
        funcs, classes = ASTContractExtractor.extract_polyglot_contracts(code, "server.go")
        self.assertIn("Exported", funcs)
        self.assertNotIn("helper", funcs)
        self.assertIn("Server", classes)
        self.assertIn("Handle", classes["Server"].methods)

    def test_go_return_type_changed(self):
        old_code = "func Query(id string) string { return id }"
        new_code = "func Query(id string) (string, error) { return id, nil }"
        report = ASTContractComparator.compare_code(old_code, new_code, "db.go")
        self.assertFalse(report.is_breaking)
        self.assertEqual(report.semver_bump, SemVerBump.PATCH)
        self.assertEqual(len(report.modifications), 1)
        self.assertEqual(report.modifications[0].category, "RETURN_TYPE_CHANGED")


class TestSARIFContractReport(unittest.TestCase):
    def test_sarif_210_structure(self):
        report = ContractDiffReport(
            file_path="src/api.ts",
            semver_bump=SemVerBump.MAJOR,
            breaking_changes=[
                ContractViolation(
                    severity="BREAKING",
                    category="REQUIRED_PARAMETER_ADDED",
                    symbol="fetchUser",
                    details="New required parameter 'authKey' added to 'fetchUser' without default value."
                )
            ],
            modifications=[
                ContractViolation(
                    severity="MODIFICATION",
                    category="RETURN_TYPE_CHANGED",
                    symbol="getUser",
                    details="Return type changed from 'User' to 'Promise<User>'."
                )
            ]
        )
        sarif = ASTContractComparator.format_sarif_report([report])
        self.assertEqual(sarif.get("$schema"), "https://json.schemastore.org/sarif-2.1.0.json")
        self.assertEqual(sarif.get("version"), "2.1.0")
        self.assertEqual(len(sarif.get("runs", [])), 1)
        driver = sarif["runs"][0]["tool"]["driver"]
        self.assertEqual(driver["name"], "T-Zero Contract Guardian")
        self.assertEqual(driver["version"], "10.9.0")
        rule_ids = {r["id"] for r in driver.get("rules", [])}
        self.assertIn("REQUIRED_PARAMETER_ADDED", rule_ids)
        self.assertIn("RETURN_TYPE_CHANGED", rule_ids)
        results = sarif["runs"][0]["results"]
        self.assertEqual(len(results), 2)
        err_res = [r for r in results if r["level"] == "error"][0]
        self.assertEqual(err_res["ruleId"], "REQUIRED_PARAMETER_ADDED")
        self.assertEqual(err_res["locations"][0]["physicalLocation"]["artifactLocation"]["uri"], "src/api.ts")
        warn_res = [r for r in results if r["level"] == "warning"][0]
        self.assertEqual(warn_res["ruleId"], "RETURN_TYPE_CHANGED")


class TestCLIContractsSARIF(unittest.TestCase):
    def test_cli_contracts_sarif_flag(self):
        res = subprocess.run(
            [sys.executable, "tzero_v3.py", "--contracts", "HEAD", "--contracts-sarif", "-"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data.get("version"), "2.1.0")
        self.assertEqual(data.get("$schema"), "https://json.schemastore.org/sarif-2.1.0.json")


if __name__ == "__main__":
    unittest.main()

