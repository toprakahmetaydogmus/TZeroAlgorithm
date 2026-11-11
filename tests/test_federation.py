# -*- coding: utf-8 -*-
"""TDD tests for T-Zero cryptographic cross-repo federation (tzero_federation.py)."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

from tzero import tzero_federation


class TestFederationSyncEngine(unittest.TestCase):
    def test_export_and_verify_manifest_strips_bodies_and_secrets(self):
        fake_key = "sk" + "-proj-" + "aa11bb22cc33dd44ee55ff667788990011223344"
        with tempfile.TemporaryDirectory() as ws:
            with open(os.path.join(ws, "gateway.py"), "w", encoding="utf-8") as f:
                f.write(
                    "class OrderGateway:\n"
                    "    def dispatch_order(self, order_id: str, total_cents: int) -> bool:\n"
                    f'        api_key_internal = "{fake_key}"\n'
                    "        internal_secret_math = total_cents * 987654\n"
                    "        return bool(order_id and api_key_internal and internal_secret_math)\n"
                )
            with open(os.path.join(ws, "client.ts"), "w", encoding="utf-8") as f:
                f.write(
                    "export interface Receipt {\n"
                    "    id: string;\n"
                    "    amount: number;\n"
                    "}\n"
                    "export function submitReceipt(r: Receipt): boolean {\n"
                    "    const hiddenSalt = '987654321internal';\n"
                    "    return r.id.length > 0 && hiddenSalt.length > 0;\n"
                    "}\n"
                )

            manifest = tzero_federation.FederationSyncEngine.export_manifest(ws, repo_name="billing-core")
            self.assertEqual(manifest["repo_name"], "billing-core")
            self.assertTrue(tzero_federation.FederationSyncEngine.verify_manifest(manifest))

            serialized = json.dumps(manifest)
            self.assertIn("OrderGateway", serialized)
            self.assertIn("dispatch_order", serialized)
            self.assertIn("submitReceipt", serialized)
            self.assertNotIn(fake_key, serialized)
            self.assertNotIn("internal_secret_math", serialized)
            self.assertNotIn("987654321internal", serialized)

            # Tampering breaks SHA-256 signature
            manifest["modules"][0]["skeleton"] += "\n# tampered"
            self.assertFalse(tzero_federation.FederationSyncEngine.verify_manifest(manifest))

    def test_import_peer_manifest_and_cli_roundtrip(self):
        with tempfile.TemporaryDirectory() as peer_ws, tempfile.TemporaryDirectory() as host_ws:
            with open(os.path.join(peer_ws, "auth.py"), "w", encoding="utf-8") as f:
                f.write("def verify_jwt(token: str) -> dict:\n    return {'sub': token}\n")

            bundle_p = os.path.join(host_ws, "peer_auth.json")
            proc_exp = subprocess.run(
                [sys.executable, "tzero/tzero_v3.py", "federation", "export", "--dir", peer_ws, "--federation-out", bundle_p, "--federation-name", "auth-svc"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("auth-svc", proc_exp.stdout)
            self.assertTrue(os.path.isfile(bundle_p))

            imp_res = tzero_federation.FederationSyncEngine.import_manifest(host_ws, bundle_p)
            self.assertTrue(imp_res["verified"])
            self.assertEqual(imp_res["repo_name"], "auth-svc")
            peers = tzero_federation.FederationSyncEngine.list_peers(host_ws)
            self.assertEqual(len(peers), 1)
            self.assertEqual(peers[0]["repo_name"], "auth-svc")

            # Missing target file for import/verify must fail cleanly (exit 1)
            self.assertEqual(tzero_federation.run_federation_cli("import", workspace_dir=host_ws, target_file=None), 1)
            self.assertEqual(tzero_federation.run_federation_cli("verify", workspace_dir=host_ws, target_file=None), 1)

    def test_analyze_cross_repo_impact_with_verified_and_tampered_peers_and_scip(self):
        with tempfile.TemporaryDirectory() as host_ws, tempfile.TemporaryDirectory() as peer_ws:
            with open(os.path.join(host_ws, "server.py"), "w", encoding="utf-8") as f:
                f.write(
                    "from auth import TokenValidator\n"
                    "def handle_req(token: str):\n"
                    "    validator = TokenValidator()\n"
                    "    return validator.validate(token)\n"
                )

            with open(os.path.join(peer_ws, "auth_service.py"), "w", encoding="utf-8") as f:
                f.write(
                    "class TokenValidator:\n"
                    "    def validate(self, token: str) -> bool:\n"
                    "        return len(token) > 10\n"
                )
            peer_manifest = tzero_federation.FederationSyncEngine.export_manifest(peer_ws, repo_name="auth-peer")
            valid_peer_p = os.path.join(host_ws, ".tzero", "federation", "auth-peer.json")
            os.makedirs(os.path.dirname(valid_peer_p), exist_ok=True)
            with open(valid_peer_p, "w", encoding="utf-8") as f:
                json.dump(peer_manifest, f, indent=2)

            tampered_manifest = {
                "schema_version": "1.0",
                "repo_name": "tampered-peer",
                "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                "module_count": 1,
                "modules": [{
                    "rel_path": "fake.py",
                    "lang": "python",
                    "skeleton_tokens": 5,
                    "skeleton": "class TokenValidator:\n    pass\n",
                }],
            }
            tampered_p = os.path.join(host_ws, ".tzero", "federation", "tampered-peer.json")
            with open(tampered_p, "w", encoding="utf-8") as f:
                json.dump(tampered_manifest, f, indent=2)

            scip_payload = {
                "documents": [{
                    "relative_path": "server.py",
                    "occurrences": [{"range": [0, 18, 32], "symbol": "TokenValidator", "symbol_roles": 0}],
                }]
            }
            scip_p = os.path.join(host_ws, "index.scip.json")
            with open(scip_p, "w", encoding="utf-8") as f:
                json.dump(scip_payload, f)

            res = tzero_federation.FederationSyncEngine.analyze_cross_repo_impact(
                workspace_dir=host_ws,
                symbol_name="TokenValidator",
                scip_path=scip_p,
            )

            self.assertEqual(res["symbol"], "TokenValidator")
            self.assertEqual(len(res["local_hits"]), 1)
            self.assertEqual(res["local_hits"][0]["file"], "server.py")
            self.assertGreaterEqual(res["local_hits"][0]["matches"], 2)
            self.assertIn(1, res["local_hits"][0]["lines"])

            self.assertEqual(len(res["impacted_peers"]), 1)
            self.assertEqual(res["impacted_peers"][0]["repo_name"], "auth-peer")
            self.assertEqual(res["impacted_peers"][0]["rel_path"], "auth_service.py")

            self.assertIn("tampered-peer", res["unverified_peers"])

            self.assertIsNotNone(res["scip_trace"])
            self.assertEqual(res["scip_trace"]["format"], "scip")

            self.assertEqual(res["total_impacted_files"], 2)

    def test_cli_federation_impact_action(self):
        with tempfile.TemporaryDirectory() as ws:
            with open(os.path.join(ws, "main.py"), "w", encoding="utf-8") as f:
                f.write("def calculate_tax():\n    return 42\n")

            proc_err = subprocess.run(
                [sys.executable, "tzero/tzero_v3.py", "federation", "impact", "--dir", ws],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc_err.returncode, 1)
            self.assertIn("Symbol name required", proc_err.stderr)

            proc_ok = subprocess.run(
                [sys.executable, "tzero/tzero_v3.py", "federation", "impact", "--dir", ws, "--federation-symbol", "calculate_tax"],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(proc_ok.stdout)
            self.assertEqual(data["symbol"], "calculate_tax")
            self.assertEqual(len(data["local_hits"]), 1)
            self.assertEqual(data["total_impacted_files"], 1)


if __name__ == "__main__":
    unittest.main()

