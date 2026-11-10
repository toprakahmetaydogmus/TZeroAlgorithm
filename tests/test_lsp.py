# -*- coding: utf-8 -*-
"""TDD tests for T-Zero stdio JSON-RPC Language Server (tzero_lsp.py)."""

import io
import json
import os
import pathlib
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


if __name__ == "__main__":
    unittest.main()
