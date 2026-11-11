# -*- coding: utf-8 -*-
import unittest
import urllib.request
import json
import threading
import time
from tzero.tzero_dashboard import start_dashboard_server

class TestTZeroDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_port = 8425
        cls.server = start_dashboard_server(port=cls.test_port, open_browser=False)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_get_dashboard_html(self):
        url = f"http://localhost:{self.test_port}/"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode("utf-8")
            self.assertIn("T-Zero Developer Console", body)
            self.assertIn("11.0.0", body)
            self.assertIn("MCP TOOLS OPERATIONAL", body)
            for endpoint in (
                "/api/stats",
                "/api/debt/analyze",
                "/api/budget/optimize",
                "/api/golden/verify",
                "/api/contracts/compare",
                "/api/mutation/test",
                "/api/bridge/reverse",
                "/api/merge/heal",
                "/api/blackboard",
                "/api/federation/peers",
                "/api/federation/impact",
                "/api/hooks/preview",
                "/api/scip/summary",
            ):
                self.assertIn(endpoint, body, f"Dashboard UI missing panel wiring for {endpoint}")
            self.assertIn("12 Live Endpoints", body)
            for tab_id in ("tab-federation", "tab-hooks", "tab-scip"):
                self.assertIn(tab_id, body)

    def test_get_api_stats(self):
        url = f"http://localhost:{self.test_port}/api/stats"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["version"], "11.0.0")
            self.assertGreaterEqual(data["tools_count"], 57)
            self.assertGreater(data["raw_tokens"], 0)
            self.assertGreaterEqual(data["pruned_tokens"], 0)
            self.assertIn("savings_pct", data)
            self.assertIn("%", data["token_savings"])

    def test_post_api_reduce(self):
        url = f"http://localhost:{self.test_port}/api/reduce"
        payload = json.dumps({"filename": "main.rs", "code": "pub fn hello() { println!(\"Hi\"); }"}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("reduced", data)
            self.assertIn("pub fn hello()", data["reduced"])

    def test_post_api_superdesign(self):
        url = f"http://localhost:{self.test_port}/api/superdesign/generate"
        payload = json.dumps({"design_type": "component", "prompt": "metric card"}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertIn("files_to_create", data["data"])

    def test_get_api_blackboard(self):
        url = f"http://localhost:{self.test_port}/api/blackboard"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertIn("markdown", data)
            self.assertIn("T-Zero Multi-Agent Blackboard State", data["markdown"])

    def test_post_api_bridge_reverse(self):
        url = f"http://localhost:{self.test_port}/api/bridge/reverse"
        payload = json.dumps({
            "code": "interface User { id: number; name: string; }",
            "lang": "ts",
            "flavor": "dataclass"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertIn("class User:", data["python_code"])

    def test_post_api_merge_heal(self):
        url = f"http://localhost:{self.test_port}/api/merge/heal"
        conflict_code = (
            "<<<<<<< HEAD\n"
            "def foo():\n"
            "    return 1\n"
            "=======\n"
            "def bar():\n"
            "    return 2\n"
            ">>>>>>> branch\n"
        )
        payload = json.dumps({"code": conflict_code}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertIn("def foo():", data["merged_code"])
            self.assertIn("def bar():", data["merged_code"])

    def test_post_api_mutation_test(self):
        url = f"http://localhost:{self.test_port}/api/mutation/test"
        # Test on a small file with 0 or 1 mutants
        payload = json.dumps({"file": "tzero/siber_akademi_icon.py", "max_mutants": 1}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertIn("score", data)
            self.assertIn("markdown", data)

    def test_post_api_contracts_compare(self):
        url = f"http://localhost:{self.test_port}/api/contracts/compare"
        payload = json.dumps({
            "old_code": "def query(term: str) -> list:\n    return []\n",
            "new_code": "def query(term: str, limit: int = 10) -> list:\n    return []\n",
            "file_path": "search.py"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertEqual(data.get("semver_bump"), "MINOR")
            self.assertFalse(data.get("is_breaking"))
            self.assertIn("markdown", data)

    def test_post_api_debt_analyze(self):
        url = f"http://localhost:{self.test_port}/api/debt/analyze"
        payload = json.dumps({"path": "tests/test_debt.py"}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertEqual(data.get("type"), "file")
            self.assertIn("maintainability_index", data)
            self.assertIn("rating", data)

    def test_post_api_budget_optimize(self):
        url = f"http://localhost:{self.test_port}/api/budget/optimize"
        payload = json.dumps({"path": "tests", "target_tokens": 10000, "model": "gpt-4o"}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertEqual(data.get("target_model"), "gpt-4o")
            self.assertIn("tier_applied", data)
            self.assertIn("markdown", data)

    def test_post_api_golden_verify(self):
        url = f"http://localhost:{self.test_port}/api/golden/verify"
        payload = json.dumps({"path": "tests"}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("markdown", data)

    def test_get_api_federation_peers(self):
        url = f"http://localhost:{self.test_port}/api/federation/peers"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertIsInstance(data.get("peers"), list)

    def test_get_api_hooks_preview(self):
        url = f"http://localhost:{self.test_port}/api/hooks/preview"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            hooks = data.get("config", {}).get("hooks", {})
            self.assertIn("PreToolUse", hooks)
            self.assertIn("PostToolUse", hooks)

    def test_post_api_federation_impact(self):
        url = f"http://localhost:{self.test_port}/api/federation/impact"
        empty_req = urllib.request.Request(
            url,
            data=json.dumps({"symbol": ""}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(empty_req) as resp:
            self.assertEqual(resp.status, 200)
            err_data = json.loads(resp.read().decode("utf-8"))
            self.assertFalse(err_data.get("success"))
            self.assertEqual(err_data.get("error"), "symbol required")

        ok_req = urllib.request.Request(
            url,
            data=json.dumps({"symbol": "PolyglotTokenReducer"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(ok_req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertEqual(data.get("symbol"), "PolyglotTokenReducer")
            self.assertIsInstance(data.get("local_hits"), list)
            self.assertGreater(len(data["local_hits"]), 0)
            self.assertIn("total_impacted_files", data)

    def test_post_api_scip_summary(self):
        import os
        import tempfile

        url = f"http://localhost:{self.test_port}/api/scip/summary"
        missing_req = urllib.request.Request(
            url,
            data=json.dumps({"path": "nonexistent_scip_index_999.scip"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(missing_req) as resp:
            self.assertEqual(resp.status, 200)
            err_data = json.loads(resp.read().decode("utf-8"))
            self.assertFalse(err_data.get("success"))
            self.assertIn("error", err_data)

        with tempfile.TemporaryDirectory() as tmpdir:
            scip_file = os.path.join(tmpdir, "index.scip.json")
            with open(scip_file, "w", encoding="utf-8") as f:
                json.dump({
                    "documents": [
                        {"relative_path": "a.py", "occurrences": [{"symbol": "py a.py/foo.", "range": [1, 0], "symbol_roles": 1}]},
                        {"relative_path": "b.py", "occurrences": [{"symbol": "py a.py/foo.", "range": [3, 4], "symbol_roles": 0}]},
                    ]
                }, f)

            ok_req = urllib.request.Request(
                url,
                data=json.dumps({"path": scip_file}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(ok_req) as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(data.get("success"))
                self.assertEqual(data.get("format"), "scip")
                self.assertEqual(data.get("documents"), 2)
                self.assertGreaterEqual(data.get("symbols_indexed", 0), 1)
                self.assertEqual(data.get("edges"), {"b.py": ["a.py"]})

if __name__ == "__main__":
    unittest.main()
