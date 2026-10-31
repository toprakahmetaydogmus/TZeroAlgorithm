# -*- coding: utf-8 -*-
"""Unit tests for T-Zero Model Context Protocol (MCP) server tools and prompts."""

import os
import unittest
import tempfile
import asyncio
import tzero_mcp


def tool_result_text(result):
    if isinstance(result, tuple):
        result = result[0]
    content = getattr(result, "content", result)
    return content[0].text


class TestMCPServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._old_tool_mode = os.environ.get("TZERO_MCP_TOOL_MODE")
        os.environ["TZERO_MCP_TOOL_MODE"] = "all"
        cls.server = tzero_mcp.create_mcp_server()

    @classmethod
    def tearDownClass(cls):
        if cls._old_tool_mode is not None:
            os.environ["TZERO_MCP_TOOL_MODE"] = cls._old_tool_mode
        else:
            os.environ.pop("TZERO_MCP_TOOL_MODE", None)

    def run_async(self, coro):
        return asyncio.run(coro)

    def test_mcp_tools_and_prompts_registration(self):
        """Verifies that all 47 specialized MCP tools and grounding prompt are properly registered."""
        tools = self.run_async(self.server.list_tools())
        tool_names = [t.name for t in tools]
        self.assertEqual(len(tool_names), 49)
        self.assertIn("execute_codebase_workflow", tool_names)
        expected_tools = [
            "execute_codebase_workflow",
            "get_project_context_tree",
            "query_module_dependencies",
            "query_architecture_boundaries",
            "generate_architecture_blueprint",
            "generate_repo_map",
            "audit_codebase_quality",
            "find_code_duplicity",
            "estimate_token_cost",
            "analyze_change_impact",
            "enforce_architecture_boundaries",
            "search_codebase_semantic",
            "export_agent_rules",
            "get_token_savings_metrics",
            "get_incremental_diff_context",
            "prune_code_snippet",
            "verify_zero_leak_security",
            "verify_hallucination_guard",
            "get_smart_skeleton_context",
            "rank_repository_pagerank",
            "trace_symbol_call_chain",
            "find_dead_code",
            "jarvis_compress_semantic_memory",
            "jarvis_decompress_semantic_memory",
            "jarvis_orchestrate_goal",
            "jarvis_zero_key_query",
            "jarvis_query_knowledge_graph",
            "jarvis_compress_document",
            "jarvis_export_memory_store",
            "jarvis_causal_chain_query",
            "jarvis_self_healing_execute",
            "jarvis_consolidate_memory",
            "jarvis_hybrid_search",
            "jarvis_swarm_orchestrate",
            "jarvis_export_graph_visualization",
            "jarvis_minhash_similarity",
            "jarvis_bft_swarm_consensus",
            "jarvis_latent_press_compress",
            "prune_schema_definition",
            "generate_smart_micro_patch",
            "generate_zero_waste_prompt_context",
            "compress_stream_tokens",
            "install_git_security_guard",
            "suggest_reusable_helpers",
            "superdesign_generate",
            "superdesign_iterate",
            "superdesign_extract_system",
            "superdesign_list",
            "superdesign_gallery",
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
            output = tool_result_text(res)
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
            out_ws = tool_result_text(res_ws)
            self.assertIn("Workspace Dependency Topology", out_ws)
            self.assertIn("json", out_ws)

            # Single file query
            res_file = self.run_async(self.server.call_tool(
                "query_module_dependencies",
                {"project_root": temp_dir, "file_path": "a.py"}
            ))
            out_file = tool_result_text(res_file)
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
            out = tool_result_text(res)
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
            out = tool_result_text(res)
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
            out = tool_result_text(res)
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
            out = tool_result_text(res)
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
            out = tool_result_text(res)
            self.assertIn("Code Duplicity Report", out)
            self.assertIn("mod1.py", out)
            self.assertIn("mod2.py", out)

    def test_tool_suggest_reusable_helpers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            util_f = os.path.join(temp_dir, "my_utils.py")
            with open(util_f, "w", encoding="utf-8") as f:
                f.write(
                    "def format_iso_timestamp(ts: int) -> str:\n"
                    "    \"\"\"Converts timestamp to ISO 8601 string.\"\"\"\n"
                    "    return str(ts)\n"
                )

            res = self.run_async(self.server.call_tool(
                "suggest_reusable_helpers",
                {"project_root": temp_dir, "query": "timestamp format"}
            ))
            out = tool_result_text(res)
            self.assertIn("Reusable Repository Helpers", out)
            self.assertIn("format_iso_timestamp", out)
            self.assertIn("from my_utils import format_iso_timestamp", out)

            # Test reinvention guard
            res_guard = self.run_async(self.server.call_tool(
                "suggest_reusable_helpers",
                {
                    "project_root": temp_dir,
                    "code_snippet": "def format_timestamp(ts):\n    \"\"\"Converts timestamp to string\"\"\"\n    pass\n"
                }
            ))
            out_guard = tool_result_text(res_guard)
            self.assertIn("Anti-Reinvention Guard Alert", out_guard)
            self.assertIn("format_iso_timestamp", out_guard)

    def test_tool_estimate_token_cost(self):
        res = self.run_async(self.server.call_tool(
            "estimate_token_cost",
            {"text": "Sample text for token and pricing estimation."}
        ))
        out = tool_result_text(res)
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

    def test_tool_analyze_change_impact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            f1 = os.path.join(temp_dir, "lib.py")
            f2 = os.path.join(temp_dir, "caller.py")
            with open(f1, "w", encoding="utf-8") as fp:
                fp.write("def target_func(): pass\n")
            with open(f2, "w", encoding="utf-8") as fp:
                fp.write("import lib\nlib.target_func()\n")

            res = self.run_async(self.server.call_tool(
                "analyze_change_impact",
                {"target_symbol": "target_func", "project_root": temp_dir}
            ))
            out = tool_result_text(res)
            self.assertIn("Change Impact & Blast Radius", out)
            self.assertIn("caller.py", out)

    def test_tool_enforce_architecture_boundaries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            rules_p = os.path.join(temp_dir, "tzero.rules.json")
            with open(rules_p, "w", encoding="utf-8") as fp:
                fp.write('{"layers":{"core":["core/*"]},"forbidden_imports":[{"from_layer":"core","cannot_import":["ui"],"reason":"test"}]}')
            os.makedirs(os.path.join(temp_dir, "core"), exist_ok=True)
            with open(os.path.join(temp_dir, "core", "test.py"), "w", encoding="utf-8") as fp:
                fp.write("import ui\n")

            res = self.run_async(self.server.call_tool(
                "enforce_architecture_boundaries",
                {"project_root": temp_dir, "rules_file": "tzero.rules.json"}
            ))
            out = tool_result_text(res)
            self.assertIn("ARCH VIOLATION", out)

    def test_tool_search_codebase_semantic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            f = os.path.join(temp_dir, "auth_service.py")
            with open(f, "w", encoding="utf-8") as fp:
                fp.write("def authenticate_user(token):\n    '''Validates jwt security token.'''\n    return True\n")

            res = self.run_async(self.server.call_tool(
                "search_codebase_semantic",
                {"query": "jwt token authenticate", "project_root": temp_dir, "top_k": 3}
            ))
            out = tool_result_text(res)
            self.assertIn("Semantic Code Search", out)
            self.assertIn("auth_service.py", out)

    def test_tool_export_agent_rules(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            res = self.run_async(self.server.call_tool(
                "export_agent_rules",
                {"project_root": temp_dir, "target": "all"}
            ))
            out = tool_result_text(res)
            self.assertIn("Generated AI Agent rule files", out)
            self.assertTrue(os.path.exists(os.path.join(temp_dir, ".cursorrules")))
            self.assertTrue(os.path.exists(os.path.join(temp_dir, ".clinerules")))

    def test_tool_get_token_savings_metrics(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            f = os.path.join(temp_dir, "sample.py")
            with open(f, "w", encoding="utf-8") as fp:
                fp.write("def foo():\n    pass\n")

            res = self.run_async(self.server.call_tool(
                "get_token_savings_metrics",
                {"project_root": temp_dir, "team_size": 3}
            ))
            out = tool_result_text(res)
            self.assertIn("T-Zero Token Reduction & Economic ROI Report", out)
            self.assertIn("Monthly Team Cost", out)

    def test_tool_get_incremental_diff_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            res = self.run_async(self.server.call_tool(
                "get_incremental_diff_context",
                {"project_root": temp_dir, "base_ref": "HEAD~1"}
            ))
            out = tool_result_text(res)
            self.assertIn("No Git Changes Detected", out)

    def test_tool_prune_code_snippet(self):
        sample_code = """
import os
import sys

class Worker:
    def execute(self):
        # Long body
""" + "\n".join([f"        x_{i} = {i} * 2" for i in range(100)]) + """
        return True
"""
        res = self.run_async(self.server.call_tool(
            "prune_code_snippet",
            {"code": sample_code, "file_path_or_ext": "worker.py", "reduction_mode": "ultra"}
        ))
        out = tool_result_text(res)
        self.assertIn("T-Zero Code Pruning Result", out)
        self.assertIn("class Worker", out)
        self.assertIn("reduction", out)
        self.assertNotIn("x_50", out)

    def test_tool_verify_zero_leak_security(self):
        # 1. Clean snippet
        res_clean = self.run_async(self.server.call_tool(
            "verify_zero_leak_security",
            {"code_snippet": "def hello():\n    return 'clean'\n"}
        ))
        self.assertIn("ZERO-LEAK PASS", tool_result_text(res_clean))

        # 2. Leaking snippet
        fake_test_key = "sk-" + "dummytestkey1234567890abcdef1234567890abcdef"
        res_leak = self.run_async(self.server.call_tool(
            "verify_zero_leak_security",
            {"code_snippet": f'OPENAI_API_KEY = "{fake_test_key}"'}
        ))
        self.assertIn("Zero-Leak Security Alert", tool_result_text(res_leak))

    def test_tool_query_module_dependencies_polyglot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ts_file = os.path.join(temp_dir, "service.ts")
            with open(ts_file, "w", encoding="utf-8") as f:
                f.write("import { Injectable } from '@nestjs/common';\nimport * as fs from 'fs';\n")

            res = self.run_async(self.server.call_tool(
                "query_module_dependencies",
                {"project_root": temp_dir, "file_path": "service.ts"}
            ))
            out = tool_result_text(res)
            self.assertIn("Dependency Analysis for `service.ts`", out)
            self.assertIn("@nestjs/common", out)
            self.assertIn("fs", out)

    def test_mcp_resources_registration(self):
        resources = self.run_async(self.server.list_resources())
        uris = [str(r.uri) for r in resources]
        self.assertIn("tzero://architecture", uris)
        self.assertIn("tzero://boundaries", uris)
        self.assertIn("tzero://token-roi", uris)


    def test_tool_jarvis_semantic_memory_tools(self):
        sample_text = "Toprak dün akşam laboratuvarda ESP32 kartı üzerinde nRF24L01 modülünü SPI portuna bağlayarak test etti."
        res_compress = self.run_async(self.server.call_tool(
            "jarvis_compress_semantic_memory",
            {"text": sample_text}
        ))
        out_comp = tool_result_text(res_compress)
        self.assertIn("T-Zero Jarvis 3-Layer Semantic Memory Compression", out_comp)
        self.assertIn("reduction", out_comp)
        self.assertIn("<|tzero:mem:", out_comp)

        # Decompress tool test
        res_decomp = self.run_async(self.server.call_tool(
            "jarvis_decompress_semantic_memory",
            {"token_or_code": "8421"}
        ))
        out_decomp = tool_result_text(res_decomp)
        self.assertIn("T-Zero Jarvis Semantic Memory Resolution", out_decomp)
        self.assertIn("Toprak", out_decomp)
        self.assertIn("ESP32", out_decomp)

    def test_tool_jarvis_orchestration_tools(self):
        # 1. Orchestrate goal
        res_orch = self.run_async(self.server.call_tool(
            "jarvis_orchestrate_goal",
            {"goal": "ESP32 SPI haberleşmesini test et ve güvenliği doğrula.", "project_root": "."}
        ))
        out_orch = tool_result_text(res_orch)
        self.assertIn("T-Zero Jarvis Autonomous Goal Orchestration", out_orch)
        self.assertIn("COMPLETED", out_orch)
        self.assertIn("0.00$", out_orch)

        # 2. Zero-key query
        res_query = self.run_async(self.server.call_tool(
            "jarvis_zero_key_query",
            {"prompt": "T-Zero ve Jarvis mimarisini özetle."}
        ))
        out_query = tool_result_text(res_query)
        self.assertIn("T-Zero Jarvis Zero-Cost Intelligence", out_query)
        self.assertIn("0.00$", out_query)

    def test_tool_jarvis_universal_tools(self):
        # 1. Query Knowledge Graph
        res_graph = self.run_async(self.server.call_tool(
            "jarvis_query_knowledge_graph",
            {"query": "ESP32"}
        ))
        out_graph = tool_result_text(res_graph)
        self.assertIn("T-Zero Knowledge Graph Search Results", out_graph)
        self.assertIn("8421", out_graph)

        # 2. Compress Document
        doc = (
            "Toprak dün akşam laboratuvarda ESP32 kartı üzerinde nRF24L01 modülünü SPI portuna bağlayarak test etti.\n\n"
            "Geliştirici ekibi Kubernetes kümesinde PostgreSQL veritabanını devreye aldı."
        )
        res_doc = self.run_async(self.server.call_tool(
            "jarvis_compress_document",
            {"document_text": doc}
        ))
        out_doc = tool_result_text(res_doc)
        self.assertIn("T-Zero Universal Document Memory Compression", out_doc)
        self.assertIn("Net Token Savings", out_doc)

        # 3. Export Memory Store
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_store = tmp.name

        try:
            res_store = self.run_async(self.server.call_tool(
                "jarvis_export_memory_store",
                {"action": "save", "file_path": tmp_store}
            ))
            out_store = tool_result_text(res_store)
            self.assertIn("T-Zero Memory Store Exported", out_store)
            self.assertTrue(os.path.exists(tmp_store))
        finally:
            if os.path.exists(tmp_store):
                os.remove(tmp_store)

    def test_tool_jarvis_master_upgrades(self):
        # 1. Causal Chain Query
        res_causal = self.run_async(self.server.call_tool(
            "jarvis_causal_chain_query",
            {"target_node_id": "test_err_node", "query_type": "timeline"}
        ))
        out_causal = tool_result_text(res_causal)
        self.assertIn("T-Zero Chronological Timeline", out_causal)

        # 2. Self-Healing Execute
        res_heal = self.run_async(self.server.call_tool(
            "jarvis_self_healing_execute",
            {"command": "python -c \"print('MCP Self-Healing Test OK')\""}
        ))
        out_heal = tool_result_text(res_heal)
        self.assertIn("Self-Healing Execution Result", out_heal)
        self.assertIn("MCP Self-Healing Test OK", out_heal)

        # 3. Consolidate Memory
        res_cons = self.run_async(self.server.call_tool(
            "jarvis_consolidate_memory",
            {"action": "summary"}
        ))
        out_cons = tool_result_text(res_cons)
        self.assertIn("T-Zero Memory Consolidation State", out_cons)

        # 4. Hybrid Search
        res_search = self.run_async(self.server.call_tool(
            "jarvis_hybrid_search",
            {"query": "ESP32", "top_k": 5}
        ))
        out_search = tool_result_text(res_search)
        self.assertIn("Zero-Vector-DB Hybrid Search Results", out_search)

        # 5. Swarm Orchestrate
        res_swarm = self.run_async(self.server.call_tool(
            "jarvis_swarm_orchestrate",
            {"mission_goal": "ESP32 SPI güvenli bağlantı testi", "context": "Lab"}
        ))
        out_swarm = tool_result_text(res_swarm)
        self.assertIn("Autonomous Swarm Mission Consensus", out_swarm)
        self.assertIn("JARVIS Prime", out_swarm)

        # 6. Export Graph Visualization
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            tmp_html = tmp.name

        try:
            res_viz = self.run_async(self.server.call_tool(
                "jarvis_export_graph_visualization",
                {"output_path": tmp_html}
            ))
            out_viz = tool_result_text(res_viz)
            self.assertIn("Cyberpunk Knowledge & Causal Graph Exported", out_viz)
            self.assertTrue(os.path.exists(tmp_html))
        finally:
            if os.path.exists(tmp_html):
                os.remove(tmp_html)

    def test_jarvis_research_breakthrough_tools(self):
        """Verifies Tools 35, 36, and 37 (MinHash, PBFT Swarm, LatentPress)."""
        # 1. MinHash Similarity Tool
        res_minhash = self.run_async(self.server.call_tool(
            "jarvis_minhash_similarity",
            {
                "text_a": "Toprak ESP32 mikrodenetleyicisine nRF24L01 modülünü SPI veriyolu üzerinden bağladı",
                "text_b": "Toprak ESP32 kartına nRF24L01 telsiz modülünü SPI hattı ile entegre etti"
            }
        ))
        out_minhash = tool_result_text(res_minhash)
        self.assertIn("MinHash LSH Analysis", out_minhash)
        self.assertIn("Estimated Jaccard Similarity", out_minhash)

        # 2. PBFT Swarm Consensus Tool
        res_pbft = self.run_async(self.server.call_tool(
            "jarvis_bft_swarm_consensus",
            {
                "mission_goal": "ESP32 SPI haberleşme protokolünü doğrula",
                "context": "Donanım laboratuvarı"
            }
        ))
        out_pbft = tool_result_text(res_pbft)
        self.assertIn("Byzantine Fault-Tolerant (PBFT) Swarm Certificate", out_pbft)
        self.assertIn("Consensus Verdict", out_pbft)

        # 3. LatentPress Compression Tool
        long_context = "Toprak ESP32 mikrodenetleyicisine nRF24L01 bağladı.\n" * 5
        res_lp = self.run_async(self.server.call_tool(
            "jarvis_latent_press_compress",
            {
                "context_text": long_context,
                "near_dup_threshold": 0.65
            }
        ))
        out_lp = tool_result_text(res_lp)
        self.assertIn("LatentPress (LCLM) Context Compression", out_lp)
        self.assertIn("Compression Ratio", out_lp)

    def test_tool_prune_schema_definition(self):
        res = self.run_async(self.server.call_tool(
            "prune_schema_definition",
            {
                "content": "CREATE TABLE ledger (id INT PRIMARY KEY, amount NUMERIC);\nINSERT INTO ledger VALUES (1, 500);",
                "schema_type_or_filename": "schema.sql"
            }
        ))
        out = tool_result_text(res)
        self.assertIn("Infrastructure Schema Reduction", out)
        self.assertIn("CREATE TABLE ledger", out)

    def test_tool_generate_smart_micro_patch(self):
        diff_text = """
diff --git a/core.py b/core.py
--- a/core.py
+++ b/core.py
@@ -10,3 +10,3 @@ def run():
-    val = 10
+    val = 20
"""
        res = self.run_async(self.server.call_tool(
            "generate_smart_micro_patch",
            {"diff_content": diff_text}
        ))
        out = tool_result_text(res)
        self.assertIn("T-Zero AST Smart Micro-Patch", out)
        self.assertIn("[core.py]", out)

    def test_tool_generate_zero_waste_prompt_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_a = os.path.join(temp_dir, "entry.py")
            with open(file_a, "w", encoding="utf-8") as f:
                f.write("def helper():\n    return 1\ndef main():\n    return helper()\n")
            res = self.run_async(self.server.call_tool(
                "generate_zero_waste_prompt_context",
                {"target_dir": temp_dir, "entrypoints": ["entry.py"]}
            ))
            out = tool_result_text(res)
            self.assertIn("T-ZERO ZERO-WASTE PROMPT CONTEXT", out)
            self.assertIn("def helper():", out)

    def test_tool_compress_stream_tokens(self):
        code = "def heavy_work():\n    # useless comment\n    return 42\n"
        res = self.run_async(self.server.call_tool(
            "compress_stream_tokens",
            {"content": code, "filename_hint": "script.py", "tier": "T-3"}
        ))
        out = tool_result_text(res)
        self.assertIn("def heavy_work", out)

    def test_tool_install_git_security_guard(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            os.makedirs(os.path.join(temp_dir, ".git"), exist_ok=True)
            res = self.run_async(self.server.call_tool(
                "install_git_security_guard",
                {"repo_dir": temp_dir}
            ))
            out = tool_result_text(res)
            self.assertIn("Pre-Commit Guard", out)

    def test_canonical_tools_execution(self):
        """Verifies that all 14 canonical tools execute properly via call_tool."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sample_file = os.path.join(temp_dir, "calc.py")
            with open(sample_file, "w", encoding="utf-8") as fp:
                fp.write("def add(a: int, b: int) -> int:\n    return a + b\n")

            # 1. build_project_context
            res = self.run_async(self.server.call_tool("build_project_context", {"project_root": temp_dir, "context_type": "tree"}))
            self.assertIn("Architecture Overview", tool_result_text(res))

            # 2. prune_code_snippet
            res = self.run_async(self.server.call_tool("prune_code_snippet", {"code": "def foo():\n    x = 1\n    return x\n", "file_name_or_lang": "foo.py"}))
            self.assertIn("def foo()", tool_result_text(res))

            # 3. manage_architecture_rules (CRUD)
            res_q = self.run_async(self.server.call_tool("manage_architecture_rules", {"action": "query", "project_root": temp_dir}))
            self.assertIn("Architecture", tool_result_text(res_q))

            res_u = self.run_async(self.server.call_tool("manage_architecture_rules", {
                "action": "update", "project_root": temp_dir, "rule_name": "custom_layer", "rule_definition": '{"layers": {"api": ["api/*"]}}'
            }))
            self.assertIn("successfully updated", tool_result_text(res_u))

            res_d = self.run_async(self.server.call_tool("manage_architecture_rules", {
                "action": "delete", "project_root": temp_dir, "rule_name": "custom_layer"
            }))
            self.assertIn("successfully removed", tool_result_text(res_d))

            res_r = self.run_async(self.server.call_tool("manage_architecture_rules", {"action": "reset", "project_root": temp_dir}))
            self.assertIn("reset to enterprise defaults", tool_result_text(res_r))

            # 4. enforce_architecture_rules
            res = self.run_async(self.server.call_tool("enforce_architecture_rules", {"project_root": temp_dir}))
            self.assertTrue("ARCH PASS" in tool_result_text(res) or "T-002" in tool_result_text(res) or "architectural" in tool_result_text(res).lower())

            # 5. generate_architecture_blueprint
            res = self.run_async(self.server.call_tool("generate_architecture_blueprint", {"project_root": temp_dir}))
            self.assertIn("mermaid", tool_result_text(res).lower())

            # 6. analyze_code_dependencies
            res = self.run_async(self.server.call_tool("analyze_code_dependencies", {"project_root": temp_dir, "analysis_type": "dependencies"}))
            self.assertIn("Workspace Dependency Topology", tool_result_text(res))

            # 7. analyze_change_impact
            res = self.run_async(self.server.call_tool("analyze_change_impact", {"target_symbol": "add", "project_root": temp_dir}))
            self.assertIn("Blast Radius", tool_result_text(res))

            # 8. search_codebase
            res = self.run_async(self.server.call_tool("search_codebase", {"query": "add", "project_root": temp_dir}))
            self.assertTrue("Search" in tool_result_text(res) or "Found Matches" in tool_result_text(res))

            # 9. audit_code_quality
            res = self.run_async(self.server.call_tool("audit_code_quality", {"project_root": temp_dir, "check_type": "all"}))
            self.assertIn("Code Quality & Security Audit", tool_result_text(res))

            # 10. verify_security_guard
            res = self.run_async(self.server.call_tool("verify_security_guard", {"action": "scan", "project_root": temp_dir}))
            self.assertIn("Zero-Leak", tool_result_text(res))

            # 11. estimate_token_cost
            res = self.run_async(self.server.call_tool("estimate_token_cost", {"text": "print('hello')", "project_root": temp_dir}))
            self.assertIn("API Cost Estimation", tool_result_text(res))

            # 12. query_memory_store
            res = self.run_async(self.server.call_tool("query_memory_store", {"query": "test", "query_mode": "semantic"}))
            self.assertTrue(len(tool_result_text(res)) > 0)

            # 13. manage_memory_store (CRUD)
            res_l = self.run_async(self.server.call_tool("manage_memory_store", {"operation": "list"}))
            self.assertIn("T-Zero Persistent Memory Stores", tool_result_text(res_l))

            res_c = self.run_async(self.server.call_tool("manage_memory_store", {"operation": "compress", "content": "TZero compresses AST."}))
            self.assertIn("Semantic Memory Compression", tool_result_text(res_c))

            res_con = self.run_async(self.server.call_tool("manage_memory_store", {"operation": "consolidate"}))
            self.assertIn("Consolidation", tool_result_text(res_con))

            res_exp = self.run_async(self.server.call_tool("manage_memory_store", {"operation": "export", "content": os.path.join(temp_dir, "mem.json")}))
            self.assertIn("Exported", tool_result_text(res_exp))

            res_rst = self.run_async(self.server.call_tool("manage_memory_store", {"operation": "reset"}))
            self.assertIn("cleared and reset", tool_result_text(res_rst))

            # 14. orchestrate_agent_swarm
            res = self.run_async(self.server.call_tool("orchestrate_agent_swarm", {"goal": "help", "orchestration_mode": "goal_execute"}))
            self.assertIn("T-Zero", tool_result_text(res))

    def test_legacy_mode_environment_variable(self):
        """Verifies that default registers 15 canonical/auto tools, and TZERO_MCP_TOOL_MODE=all registers 48 tools."""
        # Clean env to test true default behavior
        old_val = os.environ.pop("TZERO_MCP_TOOL_MODE", None)
        try:
            default_server = tzero_mcp.create_mcp_server()
            tools_def = self.run_async(default_server.list_tools())
            tool_names = [t.name for t in tools_def]
            self.assertEqual(len(tool_names), 15)
            self.assertIn("execute_codebase_workflow", tool_names)
            self.assertIn("build_project_context", tool_names)
            self.assertIn("manage_memory_store", tool_names)

            os.environ["TZERO_MCP_TOOL_MODE"] = "all"
            full_server = tzero_mcp.create_mcp_server()
            tools_all = self.run_async(full_server.list_tools())
            self.assertEqual(len(tools_all), 49)
            self.assertIn("execute_codebase_workflow", [t.name for t in tools_all])
        finally:
            if old_val is not None:
                os.environ["TZERO_MCP_TOOL_MODE"] = old_val
            else:
                os.environ.pop("TZERO_MCP_TOOL_MODE", None)

    def test_execute_codebase_workflow_actions(self):
        """Verifies that the execute_codebase_workflow omni-tool routes and executes all actions cleanly."""
        # Test 1: Action = 'auto'
        res = self.run_async(self.server.call_tool("execute_codebase_workflow", {"action": "auto", "target": "."}))
        text = tool_result_text(res)
        self.assertIn("T-Zero Autonomous Codebase Intelligence Report", text)
        self.assertIn("Zero-Leak Security Audit", text)
        self.assertIn("System Architecture & Topology", text)

        # Test 2: Action = 'security'
        res_sec = self.run_async(self.server.call_tool("execute_codebase_workflow", {"action": "security", "target": "."}))
        self.assertIn("Zero-Leak", tool_result_text(res_sec))

        # Test 3: Action = 'blueprint'
        res_bp = self.run_async(self.server.call_tool("execute_codebase_workflow", {"action": "blueprint", "target": "."}))
        self.assertIn("Architecture", tool_result_text(res_bp))

        # Test 4: Unknown action error handling
        res_err = self.run_async(self.server.call_tool("execute_codebase_workflow", {"action": "invalid_unknown_action"}))
        self.assertIn("Unknown action", tool_result_text(res_err))

    def test_mcp_prompts_comprehensive(self):
        """Verifies that all 7 MCP prompts are registered and produce correct workflow directives."""
        prompts = self.run_async(self.server.list_prompts())
        prompt_names = [p.name for p in prompts]
        expected_prompts = [
            "tzero_grounding",
            "tzero_refactor",
            "tzero_code_review",
            "tzero_architecture_audit",
            "tzero_security_audit",
            "tzero_token_optimizer",
            "jarvis_workspace_copilot"
        ]
        for ep in expected_prompts:
            self.assertIn(ep, prompt_names, f"Expected prompt '{ep}' to be registered")

        # 1. Test tzero_refactor
        p_ref = self.run_async(self.server.get_prompt("tzero_refactor", {"symbol": "TestClass", "project_root": "."}))
        text_ref = p_ref.messages[0].content.text
        self.assertIn("surgical refactor of 'TestClass'", text_ref)
        self.assertIn("analyze_change_impact", text_ref)
        self.assertIn("verify_hallucination_guard", text_ref)

        # 2. Test tzero_code_review
        p_cr = self.run_async(self.server.get_prompt("tzero_code_review", {"git_ref": "HEAD~2", "project_root": "."}))
        text_cr = p_cr.messages[0].content.text
        self.assertIn("reviewing git diff against 'HEAD~2'", text_cr)
        self.assertIn("get_incremental_diff_context", text_cr)
        self.assertIn("verify_zero_leak_security", text_cr)

        # 3. Test tzero_architecture_audit
        p_arch = self.run_async(self.server.get_prompt("tzero_architecture_audit", {"project_root": "."}))
        text_arch = p_arch.messages[0].content.text
        self.assertIn("auditing system architecture", text_arch)
        self.assertIn("enforce_architecture_rules", text_arch)
        self.assertIn("generate_architecture_blueprint", text_arch)

        # 4. Test tzero_security_audit
        p_sec = self.run_async(self.server.get_prompt("tzero_security_audit", {"project_root": "."}))
        text_sec = p_sec.messages[0].content.text
        self.assertIn("100% Zero-Leak security audit", text_sec)
        self.assertIn("verify_security_guard", text_sec)

        # 5. Test tzero_token_optimizer
        p_opt = self.run_async(self.server.get_prompt("tzero_token_optimizer", {"project_root": "."}))
        text_opt = p_opt.messages[0].content.text
        self.assertIn("optimizing token consumption", text_opt)
        self.assertIn("build_project_context", text_opt)
        self.assertIn("estimate_token_cost", text_opt)

        # 6. Test jarvis_workspace_copilot
        p_jarvis = self.run_async(self.server.get_prompt("jarvis_workspace_copilot", {"goal": "Optimize repository", "project_root": "."}))
        text_jarvis = p_jarvis.messages[0].content.text
        self.assertIn("CO-PILOT EXECUTION DIRECTIVES", text_jarvis)


if __name__ == "__main__":
    unittest.main()


