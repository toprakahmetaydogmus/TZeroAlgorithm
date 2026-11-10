# -*- coding: utf-8 -*-
"""TDD tests for T-Zero stdio JSON-RPC Language Server (tzero_lsp.py)."""

import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

import tzero_lsp


class TestTZeroLSP(unittest.TestCase):
    def test_lsp_diagnostics_for_secret_and_arch_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            rules = {
                "layers": {"core": ["core/**"], "cli": ["cli/**"]},
                "forbidden_imports": [
                    {"from_layer": "core", "cannot_import": ["cli"], "reason": "Core isolated from CLI"}
                ],
            }
            with open(os.path.join(tmp, "tzero.rules.json"), "w", encoding="utf-8") as f:
                json.dump(rules, f)
            os.makedirs(os.path.join(tmp, "core"), exist_ok=True)
            os.makedirs(os.path.join(tmp, "cli"), exist_ok=True)
            with open(os.path.join(tmp, "cli", "screen.py"), "w", encoding="utf-8") as f:
                f.write("def render(): pass\n")

            lsp_srv = tzero_lsp.TZeroLSPServer(workspace_dir=tmp)
            core_file = os.path.join(tmp, "core", "engine.py")
            uri = pathlib.Path(core_file).as_uri()
            fake_key = "sk" + "-proj-" + "11aa22bb33cc44dd55ee66ff77889900aabbccdd"
            bad_code = (
                "from cli import screen\n\n"
                f'TOKEN = "{fake_key}"\n'
                "def compute(x: int) -> int:\n"
                "    return x + 1\n"
            )

            msgs = lsp_srv.handle_message({
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {"textDocument": {"uri": uri, "text": bad_code}},
            })
            self.assertEqual(len(msgs), 1)
            self.assertEqual(msgs[0]["method"], "textDocument/publishDiagnostics")
            diags = msgs[0]["params"]["diagnostics"]
            codes = {d["code"] for d in diags}
            self.assertIn("zero-leak", codes)
            self.assertIn("arch-boundary", codes)

            # Fix both issues on didChange -> zero error diagnostics
            clean_code = "def compute(x: int) -> int:\n    return x + 1\n"
            msgs2 = lsp_srv.handle_message({
                "jsonrpc": "2.0",
                "method": "textDocument/didChange",
                "params": {
                    "textDocument": {"uri": uri, "version": 2},
                    "contentChanges": [{"text": clean_code}],
                },
            })
            self.assertEqual(msgs2[0]["params"]["diagnostics"], [])

    def test_lsp_stdio_framing_roundtrip_initialize_codelens_shutdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            py_path = os.path.join(tmp, "demo.py")
            src = "def alpha(a: int, b: int) -> int:\n    x = a + b\n    return x * 2\n"
            with open(py_path, "w", encoding="utf-8") as f:
                f.write(src)
            uri = pathlib.Path(py_path).as_uri()

            requests = [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"rootUri": pathlib.Path(tmp).as_uri()}},
                {"jsonrpc": "2.0", "method": "textDocument/didOpen", "params": {"textDocument": {"uri": uri, "text": src}}},
                {"jsonrpc": "2.0", "id": 2, "method": "textDocument/codeLens", "params": {"textDocument": {"uri": uri}}},
                {"jsonrpc": "2.0", "id": 3, "method": "shutdown", "params": None},
                {"jsonrpc": "2.0", "method": "exit"},
            ]
            in_bytes = b"".join(tzero_lsp.encode_lsp_frame(r) for r in requests)
            in_buf = io.BytesIO(in_bytes)
            out_buf = io.BytesIO()

            lsp_srv = tzero_lsp.TZeroLSPServer(workspace_dir=tmp)
            lsp_srv.serve_stdio(in_stream=in_buf, out_stream=out_buf)

            out_buf.seek(0)
            responses = []
            while True:
                pkt = tzero_lsp.read_lsp_frame(out_buf)
                if pkt is None:
                    break
                responses.append(pkt)

            by_id = {r["id"]: r for r in responses if "id" in r}
            self.assertIn(1, by_id)
            self.assertIn("capabilities", by_id[1]["result"])
            self.assertIn(2, by_id)
            lenses = by_id[2]["result"]
            self.assertGreaterEqual(len(lenses), 1)
            self.assertIn("tok", lenses[0]["command"]["title"])
            self.assertIn(3, by_id)

    def test_nested_class_methods_codelens(self):
        code = (
            "class DataWorker:\n"
            "    def process(self, x: int) -> int:\n"
            "        return x * 2\n\n"
            "    async def fetch(self) -> str:\n"
            "        return 'data'\n\n"
            "def outer():\n"
            "    def closure():\n"
            "        pass\n"
            "    return 1\n"
        )
        srv = tzero_lsp.TZeroLSPServer()
        lenses = srv.compute_code_lenses("file:///workspace/worker.py", code)
        # Should emit lenses for: DataWorker, process, fetch, outer (NOT closure)
        self.assertEqual(len(lenses), 4)
        lines_hit = [l["range"]["start"]["line"] for l in lenses]
        self.assertEqual(lines_hit, sorted(lines_hit))
        # Verify method lines are included
        self.assertIn(0, lines_hit)  # DataWorker
        self.assertIn(1, lines_hit)  # process
        self.assertIn(4, lines_hit)  # fetch
        self.assertIn(7, lines_hit)  # outer

    def test_lsp_hover_symbol_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            srv = tzero_lsp.TZeroLSPServer(workspace_dir=tmp)
            code = (
                "class Calculator:\n"
                "    def add(self, a: int, b: int) -> int:\n"
                "        val = a + b\n"
                "        return val\n"
            )
            uri = "file:///workspace/calc.py"
            # Line 1 is inside 'add' method
            hover = srv.compute_hover(uri, code, line=1, character=8)
            self.assertIsNotNone(hover)
            self.assertIn("contents", hover)
            md = hover["contents"]["value"]
            self.assertIn("add", md)
            self.assertIn("tok", md)
            self.assertIn("Statements", md)
            self.assertIn("References", md)
            self.assertEqual(hover["range"]["start"]["line"], 1)

            # Line outside any function/class should return None
            empty_hover = srv.compute_hover(uri, code, line=20, character=0)
            self.assertIsNone(empty_hover)

    def test_lsp_codeaction_quickfix_for_secret(self):
        fake_key = "sk" + "-proj-" + "11aa22bb33cc44dd55ee66ff77889900aabbccdd"
        code = (
            f'TOKEN = "{fake_key}"\n'
            "def run():\n"
            "    pass\n"
        )
        srv = tzero_lsp.TZeroLSPServer()
        uri = "file:///workspace/app.py"
        actions = srv.compute_code_actions(uri, code)
        self.assertGreaterEqual(len(actions), 1)
        qa = actions[0]
        self.assertEqual(qa.get("kind"), "quickfix")
        self.assertTrue(qa.get("isPreferred"))
        changes = qa.get("edit", {}).get("changes", {}).get(uri, [])
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["newText"], 'TOKEN = os.environ.get("TOKEN", "")')

    def test_subprocess_lsp_stdio_full_roundtrip(self):
        fake_key = "sk" + "-proj-" + "11aa22bb33cc44dd55ee66ff77889900aabbccdd"
        src = (
            f'API_KEY = "{fake_key}"\n'
            "def calculate(x: int) -> int:\n"
            "    res = x * 2\n"
            "    return res\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "main.py")
            with open(p, "w", encoding="utf-8") as f:
                f.write(src)
            uri = pathlib.Path(p).as_uri()

            cmd = [sys.executable, "tzero_v3.py", "lsp", "--dir", tmp]
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
            )

            try:
                # 1. initialize
                req1 = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"rootUri": pathlib.Path(tmp).as_uri()}}
                proc.stdin.write(tzero_lsp.encode_lsp_frame(req1))
                proc.stdin.flush()
                resp1 = tzero_lsp.read_lsp_frame(proc.stdout)
                self.assertIsNotNone(resp1)
                caps = resp1["result"]["capabilities"]
                self.assertTrue(caps.get("hoverProvider"))
                self.assertTrue(caps.get("codeActionProvider"))

                # 2. didOpen -> publishDiagnostics
                req2 = {"jsonrpc": "2.0", "method": "textDocument/didOpen", "params": {"textDocument": {"uri": uri, "text": src}}}
                proc.stdin.write(tzero_lsp.encode_lsp_frame(req2))
                proc.stdin.flush()
                resp2 = tzero_lsp.read_lsp_frame(proc.stdout)
                self.assertIsNotNone(resp2)
                self.assertEqual(resp2["method"], "textDocument/publishDiagnostics")
                diags = resp2["params"]["diagnostics"]

                # 3. hover on calculate
                req3 = {"jsonrpc": "2.0", "id": 2, "method": "textDocument/hover", "params": {"textDocument": {"uri": uri}, "position": {"line": 1, "character": 4}}}
                proc.stdin.write(tzero_lsp.encode_lsp_frame(req3))
                proc.stdin.flush()
                resp3 = tzero_lsp.read_lsp_frame(proc.stdout)
                self.assertIsNotNone(resp3)
                hover_res = resp3.get("result")
                self.assertIsNotNone(hover_res)
                self.assertIn("calculate", hover_res["contents"]["value"])

                # 4. codeAction for secret
                req4 = {"jsonrpc": "2.0", "id": 3, "method": "textDocument/codeAction", "params": {"textDocument": {"uri": uri}, "context": {"diagnostics": diags}}}
                proc.stdin.write(tzero_lsp.encode_lsp_frame(req4))
                proc.stdin.flush()
                resp4 = tzero_lsp.read_lsp_frame(proc.stdout)
                self.assertIsNotNone(resp4)
                ca_list = resp4.get("result") or []
                self.assertGreaterEqual(len(ca_list), 1)
                self.assertEqual(ca_list[0]["edit"]["changes"][uri][0]["newText"], 'API_KEY = os.environ.get("API_KEY", "")')

                # 5. shutdown and exit
                req5 = {"jsonrpc": "2.0", "id": 4, "method": "shutdown", "params": None}
                proc.stdin.write(tzero_lsp.encode_lsp_frame(req5))
                proc.stdin.flush()
                resp5 = tzero_lsp.read_lsp_frame(proc.stdout)
                self.assertIsNotNone(resp5)

                req6 = {"jsonrpc": "2.0", "method": "exit"}
                proc.stdin.write(tzero_lsp.encode_lsp_frame(req6))
                proc.stdin.flush()

                proc.wait(timeout=5)
                self.assertEqual(proc.returncode, 0)
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait()
                if proc.stdin and not proc.stdin.closed:
                    proc.stdin.close()
                if proc.stdout and not proc.stdout.closed:
                    proc.stdout.close()
                if proc.stderr and not proc.stderr.closed:
                    proc.stderr.close()


if __name__ == "__main__":
    unittest.main()

