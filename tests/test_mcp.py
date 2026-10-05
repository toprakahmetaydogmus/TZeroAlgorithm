# -*- coding: utf-8 -*-
"""Unit tests for T-Zero Model Context Protocol (MCP) server tools and prompts."""

import os
import unittest
import tempfile
import asyncio
import tzero_mcp


class TestMCPServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = tzero_mcp.create_mcp_server()

    def run_async(self, coro):
        return asyncio.run(coro)

    def test_mcp_tools_and_prompts_registration(self):
        """Verifies that all 8 MCP tools and grounding prompt are properly registered."""
        tools = self.run_async(self.server.list_tools())
        tool_names = [t.name for t in tools]
        expected_tools = [
            "get_project_context_tree",
            "query_module_dependencies",
            "query_architecture_boundaries",
            "generate_architecture_blueprint",
            "generate_repo_map",
            "audit_codebase_quality",
            "find_code_duplicity",
            "estimate_token_cost"
        ]
        for exp in expected_tools:
            self.assertIn(exp, tool_names)

        prompts = self.run_async(self.server.list_prompts())
        prompt_names = [p.name for p in prompts]
        self.assertIn("tzero_grounding", prompt_names)

    def test_tool_get_project_context_tree(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_a = os.path.join(temp_dir, "app.py")
            with open(file_a, "w", encoding="utf-8") as f:
                f.write("import os\n\ndef run():\n    '''Run app'''\n    pass\n")

            res = self.run_async(self.server.call_tool(
                "get_project_context_tree",
                {"project_root": temp_dir, "reduction_mode": "ultra", "include_file_contents": True}
            ))
            output = res.content[0].text
            self.assertIn("T-Zero Context Tree", output)
            self.assertIn("app.py", output)
            self.assertIn("Architecture Overview", output)

    def test_tool_query_module_dependencies(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_a = os.path.join(temp_dir, "a.py")
            file_b = os.path.join(temp_dir, "b.py")
            with open(file_a, "w", encoding="utf-8") as f:
                f.write("import json\nimport sys\n")
            with open(file_b, "w", encoding="utf-8") as f:
                f.write("import a\n")

            # Workspace query
            res_ws = self.run_async(self.server.call_tool(
                "query_module_dependencies",
                {"project_root": temp_dir}
            ))
            out_ws = res_ws.content[0].text
            self.assertIn("Workspace Dependency Topology", out_ws)
            self.assertIn("json", out_ws)

            # Single file query
            res_file = self.run_async(self.server.call_tool(
                "query_module_dependencies",
                {"project_root": temp_dir, "file_path": "a.py"}
            ))
            out_file = res_file.content[0].text
            self.assertIn("Dependency Analysis for `a.py`", out_file)
            self.assertIn("json", out_file)
            self.assertIn("b.py", out_file)

    def test_tool_query_architecture_boundaries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fpath = os.path.join(temp_dir, "server.py")
            with open(fpath, "w", encoding="utf-8") as f:
                f.write("class Server:\n    pass\n")

            res = self.run_async(self.server.call_tool(
                "query_architecture_boundaries",
                {"project_root": temp_dir, "extra_guidance": "Follow strict clean code."}
            ))
            out = res.content[0].text
            self.assertIn("AGENTS & AI ASSISTANT BLUEPRINT", out)
            self.assertIn("Follow strict clean code.", out)
            self.assertIn("Zero-Leak", out)

    def test_tool_generate_architecture_blueprint(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fpath = os.path.join(temp_dir, "core.py")
            with open(fpath, "w", encoding="utf-8") as f:
                f.write("import os\n")

            res = self.run_async(self.server.call_tool(
                "generate_architecture_blueprint",
                {"project_root": temp_dir}
            ))
            out = res.content[0].text
            self.assertIn("Architecture & System Blueprint", out)
            self.assertIn("```mermaid", out)

    def test_tool_generate_repo_map(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fpath = os.path.join(temp_dir, "math_utils.py")
            with open(fpath, "w", encoding="utf-8") as f:
                f.write("def add(x, y):\n    return x + y\n")

            res = self.run_async(self.server.call_tool(
                "generate_repo_map",
                {"project_root": temp_dir, "max_tokens": 1000}
            ))
            out = res.content[0].text
            self.assertIn("REPO MAP", out)
            self.assertIn("math_utils.py", out)

    def test_tool_audit_codebase_quality(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            clean_file = os.path.join(temp_dir, "clean.py")
            with open(clean_file, "w", encoding="utf-8") as f:
                f.write("'''Clean docstring module.'''\n\ndef good_function():\n    '''Good docstring.'''\n    return 42\n")

            res = self.run_async(self.server.call_tool(
                "audit_codebase_quality",
                {"project_root": temp_dir}
            ))
            out = res.content[0].text
            self.assertIn("Code Quality & Security Audit", out)
            self.assertIn("Zero-Leak Verified", out)

    def test_tool_find_code_duplicity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            dup_block = "a = 1\nb = 2\nc = 3\nd = 4\ne = 5\nf = 6\ng = 7\n"
            f1 = os.path.join(temp_dir, "mod1.py")
            f2 = os.path.join(temp_dir, "mod2.py")
            with open(f1, "w", encoding="utf-8") as f:
                f.write(dup_block)
            with open(f2, "w", encoding="utf-8") as f:
                f.write(dup_block)

            res = self.run_async(self.server.call_tool(
                "find_code_duplicity",
                {"project_root": temp_dir, "min_lines": 6}
            ))
            out = res.content[0].text
            self.assertIn("Code Duplicity Report", out)
            self.assertIn("mod1.py", out)
            self.assertIn("mod2.py", out)

    def test_tool_estimate_token_cost(self):
        res = self.run_async(self.server.call_tool(
            "estimate_token_cost",
            {"text": "Sample text for token and pricing estimation."}
        ))
        out = res.content[0].text
        self.assertIn("Token & API Cost Estimation", out)
        self.assertIn("OpenAI (GPT-4o)", out)
        self.assertIn("Anthropic (Claude 3.7 Sonnet)", out)
        self.assertIn("Ollama (Local Private)", out)
        self.assertIn("FREE ($0.00)", out)

    def test_prompt_tzero_grounding(self):
        res = self.run_async(self.server.get_prompt(
            "tzero_grounding",
            {"project_root": "C:/my_project"}
        ))
        text = res.messages[0].content.text
        self.assertIn("C:/my_project", text)
        self.assertIn("MANDATORY OPERATIONAL DIRECTIVES", text)
        self.assertIn("Zero-Leak", text)


if __name__ == "__main__":
    unittest.main()
