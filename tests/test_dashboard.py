# -*- coding: utf-8 -*-
import unittest
import urllib.request
import json
import threading
import time
from tzero_dashboard import start_dashboard_server

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
            self.assertIn("48 MCP TOOLS OPERATIONAL", body)

    def test_get_api_stats(self):
        url = f"http://localhost:{self.test_port}/api/stats"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["version"], "10.0.0")
            self.assertEqual(data["tools_count"], 49)

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
        payload = json.dumps({"file": "siber_akademi_icon.py", "max_mutants": 1}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertIn("score", data)
            self.assertIn("markdown", data)

if __name__ == "__main__":
    unittest.main()
