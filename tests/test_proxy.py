# -*- coding: utf-8 -*-
import json
import unittest
import urllib.request

from tzero_proxy import LiveContextPruner, start_context_proxy


class TestLiveContextProxy(unittest.TestCase):
    def test_prune_payload_code_blocks(self):
        big_python_code = "\n".join(
            f"def compute_step_{i}(x: int) -> int:\n    result = x * {i}\n    return result"
            for i in range(25)
        )
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "user", "content": f"Here is the code:\n```python\n{big_python_code}\n```\nWhat does it do?"}
            ]
        }

        pruned, saved = LiveContextPruner.prune_payload(payload, threshold_lines=10)
        self.assertGreater(saved, 0)
        new_content = pruned["messages"][0]["content"]
        self.assertIn("compute_step_0", new_content)
        self.assertLess(len(new_content), len(payload["messages"][0]["content"]))

    def test_live_proxy_server(self):
        server = start_context_proxy(host="127.0.0.1", port=7355)
        try:
            big_code = "\n".join(f"def task_{i}():\n    return {i}" for i in range(20))
            req_data = json.dumps({
                "messages": [{"role": "user", "content": f"```python\n{big_code}\n```"}]
            }).encode("utf-8")

            req = urllib.request.Request(
                "http://127.0.0.1:7355/v1/chat/completions",
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                body = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(body["status"], "pruned")
                self.assertGreater(body["estimated_tokens_saved"], 0)
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()

