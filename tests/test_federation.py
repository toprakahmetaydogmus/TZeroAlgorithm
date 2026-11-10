# -*- coding: utf-8 -*-
"""TDD tests for T-Zero cryptographic cross-repo federation (tzero_federation.py)."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

import tzero_federation


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
                [sys.executable, "tzero_v3.py", "federation", "export", "--dir", peer_ws, "--federation-out", bundle_p, "--federation-name", "auth-svc"],
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


if __name__ == "__main__":
    unittest.main()
