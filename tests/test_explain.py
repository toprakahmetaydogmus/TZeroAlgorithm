# -*- coding: utf-8 -*-
"""Unit tests for T-Zero Architectural Passport Generator (tzero explain)."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from tzero_explain import ArchitecturalPassportGenerator, ModulePassport, SymbolPassport


class TestArchitecturalPassportGenerator(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="tzero_explain_test_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_explain_valid_module(self):
        code = '''"""Sample service module."""
import os
import sys

class DataProcessor:
    """Processes datasets."""
    def process(self, data: str) -> bool:
        if not data:
            return False
        return True

def run_service(name: str) -> None:
    """Service entry point."""
    print(name)
'''
        file_path = Path(self.test_dir) / "sample_service.py"
        file_path.write_text(code, encoding="utf-8")

        passport = ArchitecturalPassportGenerator.explain_file(str(file_path))
        self.assertIsInstance(passport, ModulePassport)
        self.assertEqual(passport.module_name, "sample_service")
        self.assertEqual(passport.role, "business_service")
        self.assertGreater(passport.raw_tokens, 0)
        self.assertGreater(passport.passport_tokens, 0)
        self.assertGreaterEqual(passport.token_savings_pct, 0.0)
        self.assertIn("class DataProcessor", passport.markdown_passport)
        self.assertIn("def run_service", passport.markdown_passport)

    def test_explain_realistic_large_file(self):
        # 80-line class should have massive savings
        lines = ['"""Large enterprise service module."""']
        lines.append("class OrderManagementEngine:")
        for i in range(40):
            lines.append(f"    def process_order_step_{i}(self, order_id: str, count_{i}: int) -> bool:")
            lines.append(f"        if count_{i} < 0:")
            lines.append(f"            return False")
            lines.append(f"        return True")
        file_path = Path(self.test_dir) / "large_service.py"
        file_path.write_text("\n".join(lines), encoding="utf-8")

        passport = ArchitecturalPassportGenerator.explain_file(str(file_path))
        self.assertGreater(passport.token_savings_pct, 60.0)

    def test_explain_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            ArchitecturalPassportGenerator.explain_file("non_existent_file_xyz.py")


    def test_explain_non_python_typescript(self):
        with tempfile.TemporaryDirectory() as tmp:
            ts_path = os.path.join(tmp, "service.ts")
            with open(ts_path, "w", encoding="utf-8") as fh:
                fh.write(
                    "export interface UserConfig {\n"
                    "    id: number;\n"
                    "    name: string;\n"
                    "}\n\n"
                    "export class TokenService {\n"
                    "    reduce(input: string): string {\n"
                    "        return input.trim();\n"
                    "    }\n"
                    "}\n\n"
                    "export function computeRatio(raw: number, pruned: number): number {\n"
                    "    return raw > 0 ? (1 - pruned / raw) * 100 : 0;\n"
                    "}\n"
                )
            passport = ArchitecturalPassportGenerator.explain_file(ts_path)
            self.assertGreaterEqual(len(passport.symbols), 2)
            sym_names = [s.name for s in passport.symbols]
            self.assertIn("TokenService", sym_names)
            self.assertIn("computeRatio", sym_names)
            self.assertIn("TokenService", passport.markdown_passport)
            self.assertIn("```typescript", passport.markdown_passport)


if __name__ == "__main__":
    unittest.main()
