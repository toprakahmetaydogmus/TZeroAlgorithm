import ast
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import tzero_mcp
from tzero_fixer.mcp_server import PCFixerMcpServer
from tzero_pc_fixer import PCFixerMcpServer as BundledPCFixer


ROOT = Path(__file__).resolve().parents[1]
HINTS = {"readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint"}


class TestM8venCompliance(unittest.IsolatedAsyncioTestCase):
    def assert_hints(self, annotations):
        self.assertIsNotNone(annotations)
        self.assertTrue(HINTS <= annotations.keys())
        self.assertTrue(all(type(value) is bool for value in (annotations[key] for key in HINTS)))

    async def test_runtime_tool_annotations(self):
        for mode, expected_count in (("canonical", 21), ("all", 58)):
            with self.subTest(mode=mode), patch.dict(os.environ, {"TZERO_MCP_TOOL_MODE": mode}):
                tools = await tzero_mcp.create_mcp_server().list_tools()
                self.assertEqual(len(tools), expected_count)
                for tool in tools:
                    with self.subTest(tool=tool.name):
                        self.assert_hints(tool.annotations.model_dump(by_alias=True) if tool.annotations else None)

    async def test_canonical_tool_write_boundaries(self):
        with patch.dict(os.environ, {"TZERO_MCP_TOOL_MODE": "canonical"}):
            tools = await tzero_mcp.create_mcp_server().list_tools()
        annotations = {tool.name: tool.annotations.model_dump(by_alias=True) for tool in tools}
        for name in ("generate_architectural_passport", "transpile_model_bridge"):
            self.assertIs(annotations[name]["readOnlyHint"], True)
        for name in ("build_ast_snapshot", "diagnose_and_heal_system"):
            self.assertIs(annotations[name]["readOnlyHint"], False)

    def test_static_catalog_and_fixer_annotations(self):
        source = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
        catalog = next(
            ast.literal_eval(node.value)
            for node in source.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "MCP_TOOLS_CATALOG"
                    for target in node.targets)
        )
        self.assertEqual(len(catalog), 10)
        for tool in catalog:
            with self.subTest(tool=tool["name"]):
                self.assert_hints(tool.get("annotations"))
                self.assertEqual(tool["annotations"]["readOnlyHint"], tool["name"] != "export_agent_rules")

        standalone = {tool["name"]: tool.get("annotations") for tool in PCFixerMcpServer.TOOLS}
        bundled = {tool["name"]: tool.get("annotations") for tool in BundledPCFixer.TOOLS}
        self.assertEqual(len(standalone), 7)
        self.assertEqual(standalone, bundled)
        for name, annotations in standalone.items():
            with self.subTest(tool=name):
                self.assert_hints(annotations)

        self.assertIs(standalone["pc_fixer_cwe_audit"]["readOnlyHint"], True)
        self.assertIs(standalone["pc_fixer_kill_port_process"]["destructiveHint"], True)
        for name in ("pc_fixer_rollback", "pc_fixer_clean_git_locks"):
            self.assertIs(standalone[name]["readOnlyHint"], False)

    def test_registry_documentation(self):
        self.assertTrue((ROOT / "PRIVACY.md").is_file())
        for filename in ("README.md", "README.tr.md"):
            with self.subTest(readme=filename):
                readme = (ROOT / filename).read_text(encoding="utf-8")
                self.assertEqual(readme.count("m8ven.ai/badge/mcp/toprakahmetaydogmus/tzeroalgorithm"), 1)
                self.assertIn("](PRIVACY.md)", readme)
