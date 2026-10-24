# -*- coding: utf-8 -*-
"""End-to-end integration testing for T-Zero Master Edition.
Tests all 37 MCP tools, the polyglot engine across all languages, and the web dashboard server.
"""

import asyncio
import json
import os
import threading
import time
import unittest
import urllib.request
import urllib.parse

from tzero_polyglot import PolyglotTokenReducer
from tzero_dashboard import start_dashboard_server
import tzero_mcp


class TestPolyglotDeepFidelity(unittest.TestCase):
    def test_all_supported_languages(self):
        samples = {
            "test.py": ("def compute(x: int) -> int:\n    y = x * 2\n    return y\n", "def compute(x: int) -> int:"),
            "test.ts": ("export interface User {\n    id: string;\n    name: string;\n}\nexport class Service {\n    run() {\n        console.log('hi');\n    }\n}\n", "export interface User"),
            "test.rs": ("pub struct Config {\n    pub port: u16,\n}\nimpl Config {\n    pub fn new() -> Self {\n        Config { port: 8080 }\n    }\n}\n", "pub struct Config"),
            "test.go": ("package main\ntype Runner interface {\n    Run() error\n}\nfunc Start() {\n    println(\"start\")\n}\n", "type Runner interface"),
            "test.cpp": ("class Hardware {\npublic:\n    void Reset() {\n        do_reset();\n    }\n};\n", "class Hardware"),
            "test.sol": ("pragma solidity ^0.8.20;\ncontract Token {\n    mapping(address => uint256) public balances;\n    function mint() external {\n        balances[msg.sender] += 1;\n    }\n}\n", "contract Token"),
            "test.java": ("public class App {\n    public static void main(String[] args) {\n        System.out.println(1);\n    }\n}\n", "public class App"),
        }
        for fname, (code, expected_substr) in samples.items():
            reduced = PolyglotTokenReducer.reduce_code(code, fname, mode="ultra")
            self.assertIn(expected_substr, reduced, f"Failed for language sample: {fname}")
            # Verify body logic was pruned
            if fname == "test.py":
                self.assertNotIn("y = x * 2", reduced)
            elif fname == "test.rs":
                self.assertNotIn("Config { port: 8080 }", reduced)
            elif fname == "test.sol":
                self.assertNotIn("balances[msg.sender] += 1", reduced)


class TestDashboardServerLive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 8429
        cls.server = start_dashboard_server(port=cls.port, open_browser=False)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_get_dashboard_root(self):
        url = f"http://127.0.0.1:{self.port}/"
        with urllib.request.urlopen(url, timeout=3) as res:
            self.assertEqual(res.status, 200)
            body = res.read().decode("utf-8")
            self.assertIn("<!DOCTYPE html>", body)
            self.assertIn("T-Zero Developer Console", body)
            self.assertIn("causalCanvas", body)

    def test_get_api_stats(self):
        url = f"http://127.0.0.1:{self.port}/api/stats"
        with urllib.request.urlopen(url, timeout=3) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode("utf-8"))
            self.assertEqual(data["version"], "7.3.1")
            self.assertEqual(data["tools_count"], 47)
            self.assertIn("94.9", data["token_savings"])
            self.assertIn("Zero-Leak", data["security"])
            self.assertEqual(data["active_agents"], 5)

    def test_post_api_reduce(self):
        url = f"http://127.0.0.1:{self.port}/api/reduce"
        payload = json.dumps({
            "code": "pub async fn handle() {\n    let result = execute_task();\n    println!(\"{:?}\", result);\n}\n",
            "filename": "handler.rs",
            "mode": "ultra"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=3) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode("utf-8"))
            self.assertIn("reduced", data)
            self.assertIn("pub async fn handle()", data["reduced"])
            self.assertNotIn("execute_task()", data["reduced"])
            self.assertIn("savings", data)
            self.assertGreater(data["savings"], 10.0)


class TestAllMCPToolsExhaustive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = tzero_mcp.create_mcp_server()

    def call(self, tool_name, args):
        res = asyncio.run(self.server.call_tool(tool_name, args))
        content = getattr(res, "content", res)
        if isinstance(content, list) and len(content) > 0:
            return getattr(content[0], "text", str(content[0]))
        return str(content)

    def test_tool_01_to_10(self):
        # 1. get_project_context_tree
        res = self.call("get_project_context_tree", {"project_root": ".", "reduction_mode": "ultra"})
        self.assertIn("Context", res)

        # 2. query_module_dependencies
        res = self.call("query_module_dependencies", {"project_root": "."})
        self.assertTrue(len(res) > 10)

        # 3. query_architecture_boundaries
        res = self.call("query_architecture_boundaries", {"project_root": "."})
        self.assertTrue(len(res) > 10)

        # 4. generate_architecture_blueprint
        res = self.call("generate_architecture_blueprint", {"project_root": ".", "use_ai": False})
        self.assertIn("mermaid", res.lower())

        # 5. generate_repo_map
        res = self.call("generate_repo_map", {"project_root": "."})
        self.assertTrue(len(res) > 10)

        # 6. audit_codebase_quality
        res = self.call("audit_codebase_quality", {"project_root": ".", "file_path": "tzero_polyglot.py"})
        self.assertTrue(len(res) > 10)

        # 7. find_code_duplicity
        res = self.call("find_code_duplicity", {"project_root": "."})
        self.assertTrue(len(res) > 10)

        # 8. estimate_token_cost
        res = self.call("estimate_token_cost", {"project_root": "."})
        self.assertIn("$", res)

        # 9. analyze_change_impact
        res = self.call("analyze_change_impact", {"target_symbol": "TokenReducer", "project_root": "."})
        self.assertIn("Blast Radius", res)

        # 10. enforce_architecture_boundaries
        res = self.call("enforce_architecture_boundaries", {"project_root": "."})
        self.assertTrue(len(res) > 10)

    def test_tool_11_to_20(self):
        # 11. search_codebase_semantic
        res = self.call("search_codebase_semantic", {"query": "token reduction", "project_root": "."})
        self.assertTrue(len(res) > 10)

        # 12. export_agent_rules
        res = self.call("export_agent_rules", {"project_root": "."})
        self.assertTrue(len(res) > 10)

        # 13. get_token_savings_metrics
        res = self.call("get_token_savings_metrics", {"project_root": "."})
        self.assertIn("ROI", res)

        # 14. get_incremental_diff_context
        res = self.call("get_incremental_diff_context", {"base_ref": "HEAD~1", "project_root": "."})
        self.assertTrue(len(res) > 10)

        # 15. prune_code_snippet
        res = self.call("prune_code_snippet", {"code": "def func():\n    print('test')", "file_path_or_ext": "test.py"})
        self.assertIn("def func()", res)

        # 16. verify_zero_leak_security
        res = self.call("verify_zero_leak_security", {"code_snippet": "x = 42"})
        self.assertIn("ZERO-LEAK PASS", res)

        # 17. verify_hallucination_guard
        res = self.call("verify_hallucination_guard", {"proposed_code": "import os\nprint(os.path.join('a', 'b'))", "project_root": "."})
        self.assertTrue(len(res) > 10)

        # 18. get_smart_skeleton_context
        res = self.call("get_smart_skeleton_context", {"focus_file": "tzero_polyglot.py", "project_root": "."})
        self.assertTrue(len(res) > 10)

        # 19. rank_repository_pagerank
        res = self.call("rank_repository_pagerank", {"project_root": "."})
        self.assertTrue(len(res) > 10)

        # 20. trace_symbol_call_chain
        res = self.call("trace_symbol_call_chain", {"symbol_name": "TokenReducer", "project_root": "."})
        self.assertTrue(len(res) > 10)

    def test_tool_21_to_37(self):
        # 21. find_dead_code
        res = self.call("find_dead_code", {"project_root": "."})
        self.assertTrue(len(res) > 10)

        # 22. jarvis_compress_semantic_memory
        res = self.call("jarvis_compress_semantic_memory", {"text": "Developer implemented token reduction logic"})
        self.assertTrue(len(res) > 10)

        # 23. jarvis_decompress_semantic_memory
        res = self.call("jarvis_decompress_semantic_memory", {"token_or_code": "8421"})
        self.assertTrue(len(res) > 5)

        # 24. jarvis_orchestrate_goal
        res = self.call("jarvis_orchestrate_goal", {"goal": "Audit project security", "project_root": "."})
        self.assertIn("T-Zero Jarvis", res)

        # 25. jarvis_zero_key_query
        res = self.call("jarvis_zero_key_query", {"prompt": "Hello"})
        self.assertTrue(len(res) > 5)

        # 26. jarvis_query_knowledge_graph
        res = self.call("jarvis_query_knowledge_graph", {"query": "TZero"})
        self.assertTrue(len(res) > 10)

        # 27. jarvis_compress_document
        res = self.call("jarvis_compress_document", {"document_text": "Paragraph 1 about tokens. Paragraph 2 about AST."})
        self.assertTrue(len(res) > 10)

        # 28. jarvis_export_memory_store
        res = self.call("jarvis_export_memory_store", {"action": "stats"})
        self.assertTrue(len(res) > 10)

        # 29. jarvis_causal_chain_query
        res = self.call("jarvis_causal_chain_query", {"target_node_id": "root", "query_type": "timeline"})
        self.assertTrue(len(res) > 10)

        # 30. jarvis_self_healing_execute
        res = self.call("jarvis_self_healing_execute", {"command": "python -c \"print('healing check')\""})
        self.assertIn("healing check", res)

        # 31. jarvis_consolidate_memory
        res = self.call("jarvis_consolidate_memory", {"action": "summary"})
        self.assertTrue(len(res) > 10)

        # 32. jarvis_hybrid_search
        res = self.call("jarvis_hybrid_search", {"query": "context architect"})
        self.assertTrue(len(res) > 10)

        # 33. jarvis_swarm_orchestrate
        res = self.call("jarvis_swarm_orchestrate", {"mission_goal": "Verify swarm orchestration"})
        self.assertTrue(len(res) > 10)

        # 34. jarvis_export_graph_visualization
        res = self.call("jarvis_export_graph_visualization", {})
        self.assertTrue(len(res) > 10)

        # 35. jarvis_minhash_similarity
        res = self.call("jarvis_minhash_similarity", {"text_a": "token reduction", "text_b": "token optimization"})
        self.assertIn("MinHash", res)

        # 36. jarvis_bft_swarm_consensus
        res = self.call("jarvis_bft_swarm_consensus", {"mission_goal": "Validate consensus"})
        self.assertIn("PBFT", res)

        # 37. jarvis_latent_press_compress
        res = self.call("jarvis_latent_press_compress", {"context_text": "sample context text for compression " * 20})
        self.assertIn("LatentPress", res)


if __name__ == "__main__":
    unittest.main()
