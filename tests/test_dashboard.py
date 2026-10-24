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
            self.assertIn("47 MCP TOOLS OPERATIONAL", body)

    def test_get_api_stats(self):
        url = f"http://localhost:{self.test_port}/api/stats"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["version"], "7.3.1")
            self.assertEqual(data["tools_count"], 47)

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

if __name__ == "__main__":
    unittest.main()
