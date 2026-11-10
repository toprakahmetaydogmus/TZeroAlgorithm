# -*- coding: utf-8 -*-
"""TDD tests for SCIP / LSIF cross-language index importer (tzero_scip.py)."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

import tzero_scip


class TestSCIPImporter(unittest.TestCase):
    def test_import_scip_json_builds_definitions_and_references(self):
        scip_payload = {
            "metadata": {"tool_info": {"name": "scip-typescript", "version": "0.3.18"}},
            "documents": [
                {
                    "relative_path": "src/auth.ts",
                    "symbols": [
                        {"symbol": "scip-ts npm demo src/`auth.ts`/TokenValidator#", "documentation": ["Validates tokens"]}
                    ],
                    "occurrences": [
                        {"range": [4, 13, 27], "symbol": "scip-ts npm demo src/`auth.ts`/TokenValidator#", "symbol_roles": 1}
                    ],
                },
                {
                    "relative_path": "src/router.ts",
                    "symbols": [],
                    "occurrences": [
                        {"range": [12, 8, 22], "symbol": "scip-ts npm demo src/`auth.ts`/TokenValidator#", "symbol_roles": 0}
                    ],
                },
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            idx_path = os.path.join(tmp, "index.scip.json")
            with open(idx_path, "w", encoding="utf-8") as f:
                json.dump(scip_payload, f)

            graph = tzero_scip.ScipIndexImporter.load(idx_path)
            self.assertEqual(graph.document_count, 2)
            self.assertEqual(graph.format_name, "scip")
            trace = graph.trace_symbol("TokenValidator")
            self.assertEqual(len(trace["definitions"]), 1)
            self.assertEqual(trace["definitions"][0]["file"], "src/auth.ts")
            self.assertEqual(len(trace["references"]), 1)
            self.assertEqual(trace["references"][0]["file"], "src/router.ts")
            exported = graph.export_tzero_graph()
            self.assertIn("src/auth.ts", exported["edges"].get("src/router.ts", []))

    def test_import_lsif_ndjson_format(self):
        lines = [
            json.dumps({"id": 1, "type": "vertex", "label": "document", "uri": "file:///repo/core.py"}),
            json.dumps({"id": 2, "type": "vertex", "label": "document", "uri": "file:///repo/app.py"}),
            json.dumps({"id": 3, "type": "vertex", "label": "moniker", "identifier": "py/core/Engine"}),
            json.dumps({"id": 4, "type": "vertex", "label": "range", "start": {"line": 10, "character": 4}}),
            json.dumps({"id": 5, "type": "vertex", "label": "range", "start": {"line": 22, "character": 2}}),
            json.dumps({"id": 6, "type": "vertex", "label": "definitionResult"}),
            json.dumps({"id": 7, "type": "vertex", "label": "referenceResult"}),
            json.dumps({"id": 8, "type": "edge", "label": "contains", "outV": 1, "inVs": [4]}),
            json.dumps({"id": 9, "type": "edge", "label": "contains", "outV": 2, "inVs": [5]}),
            json.dumps({"id": 10, "type": "edge", "label": "moniker", "outV": 4, "inV": 3}),
            json.dumps({"id": 11, "type": "edge", "label": "moniker", "outV": 5, "inV": 3}),
            json.dumps({"id": 12, "type": "edge", "label": "textDocument/definition", "outV": 4, "inV": 6}),
            json.dumps({"id": 13, "type": "edge", "label": "item", "outV": 6, "inVs": [4]}),
            json.dumps({"id": 14, "type": "edge", "label": "textDocument/references", "outV": 4, "inV": 7}),
            json.dumps({"id": 15, "type": "edge", "label": "item", "outV": 7, "inVs": [5]}),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            lsif_path = os.path.join(tmp, "dump.lsif")
            with open(lsif_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            graph = tzero_scip.ScipIndexImporter.load(lsif_path)
            self.assertEqual(graph.format_name, "lsif")
            trace = graph.trace_symbol("Engine")
            self.assertGreaterEqual(len(trace["definitions"]), 1)
            self.assertEqual(trace["definitions"][0]["file"], "repo/core.py")
            self.assertEqual(trace["references"][0]["file"], "repo/app.py")

    def test_cli_scip_import_flag(self):
        payload = {
            "documents": [{
                "relative_path": "lib.rs",
                "occurrences": [{"range": [1, 0, 5], "symbol": "rust demo lib#Store#", "symbol_roles": 1}],
            }]
        }
        with tempfile.TemporaryDirectory() as tmp:
            idx = os.path.join(tmp, "index.scip.json")
            with open(idx, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            proc = subprocess.run(
                [sys.executable, "tzero_v3.py", "--scip-import", idx, "--scip-symbol", "Store"],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(proc.stdout)
            self.assertEqual(data["definitions"][0]["file"], "lib.rs")


if __name__ == "__main__":
    unittest.main()
