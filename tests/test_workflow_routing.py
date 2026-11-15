"""Regression coverage for the compatibility workflow's real MCP dispatch."""

import asyncio
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tzero.tzero_mcp import create_mcp_server


def text_of(result):
    if isinstance(result, tuple):
        result = result[0]
    return getattr(result, "content", result)[0].text


class TestWorkflowRouting(unittest.TestCase):
    def test_dedicated_operations_match_workflow_routes(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "example.py").write_text(
                "import os\n\ndef example():\n    return os.name\n", encoding="utf-8"
            )
            for mode in ("canonical", "all"):
                with self.subTest(mode=mode), patch.dict(os.environ, {"TZERO_MCP_TOOL_MODE": mode}):
                    server = create_mcp_server()
                    cases = [
                        ("dependencies", "", {}, "analyze_code_dependencies", {"project_root": directory}),
                        ("impact", "example", {}, "analyze_change_impact", {"project_root": directory, "target_symbol": "example"}),
                        ("search", "example", {"limit": 2}, "search_codebase", {"project_root": directory, "query": "example", "top_k": 2}),
                        ("prune", "def example():\n    return 1\n", {}, "prune_code_snippet", {"code": "def example():\n    return 1\n", "file_name_or_lang": "snippet.py"}),
                        ("rules", "", {}, "manage_architecture_rules", {"project_root": directory}),
                        ("enforce", "", {}, "enforce_architecture_rules", {"project_root": directory, "strict_mode": False}),
                    ]
                    for action, query, options, name, arguments in cases:
                        with self.subTest(action=action):
                            route = asyncio.run(server.call_tool("execute_codebase_workflow", {
                                "action": action, "target": directory, "query": query, "options": options,
                            }))
                            direct = asyncio.run(server.call_tool(name, arguments))
                            self.assertEqual(text_of(route), text_of(direct))

    def test_workflow_discloses_possible_writes_and_network(self):
        server = create_mcp_server()
        tools = asyncio.run(server.list_tools())
        workflow = next(tool for tool in tools if tool.name == "execute_codebase_workflow")
        hints = workflow.annotations.model_dump(by_alias=True)
        self.assertTrue(hints["destructiveHint"])
        self.assertTrue(hints["openWorldHint"])
        self.assertFalse(hints["idempotentHint"])

    def test_benchmark_with_export_disabled_does_not_claim_a_general_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            server = create_mcp_server()
            result = asyncio.run(server.call_tool("prove_zero_hallucination", {
                "workspace_dir": directory, "export_docs": False,
            }))
            text = text_of(result)
            self.assertIn("only", text.lower())
            self.assertNotIn("PROVEN ZERO", text)
            self.assertFalse(Path(directory, "docs").exists())

    def test_exported_benchmark_reports_only_tested_results(self):
        with tempfile.TemporaryDirectory() as directory:
            original = os.getcwd()
            try:
                os.chdir(directory)
                server = create_mcp_server()
                result = asyncio.run(server.call_tool("prove_zero_hallucination", {
                    "workspace_dir": directory, "export_docs": True,
                }))
                report = Path(directory, "docs", "ZERO_HALLUCINATION_PROOF.md").read_text(encoding="utf-8")
                self.assertEqual(report.strip(), text_of(result).strip())
                self.assertIn("do not establish", report)
                self.assertTrue(Path(directory, "docs", "zero_hallucination_proof.json").is_file())
            finally:
                os.chdir(original)
