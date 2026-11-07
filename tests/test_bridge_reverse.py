# -*- coding: utf-8 -*-
"""
Tests for T-Zero Reverse Polyglot Schema Transpiler (TS/Rust/Go -> Python @dataclass / Pydantic).
Siber Akademi - 100% Free & Zero-Leak Test Suite.
"""

import unittest
import sys
import os
import subprocess

from tzero_bridge import PolyglotTypeBridge


class TestReversePolyglotBridge(unittest.TestCase):
    """Verifies bidirectional reverse transpilation into valid Python models."""

    def test_reverse_transpile_typescript(self):
        ts_code = """
        export interface UserProfile {
            id: string;
            username: string;
            email?: string;
            isActive: boolean;
            age?: number;
            tags: string[];
            metadata?: Record<string, any>;
        }
        """
        py_code = PolyglotTypeBridge.reverse_transpile(ts_code, source_lang="ts", model_flavor="dataclass")
        self.assertIn("@dataclass", py_code)
        self.assertIn("class UserProfile:", py_code)
        self.assertIn("id: str", py_code)
        self.assertIn("username: str", py_code)
        self.assertIn("is_active: bool", py_code)
        self.assertIn("tags: List[str]", py_code)
        self.assertIn("email: Optional[str] = None", py_code)
        self.assertIn("age: Optional[int] = None", py_code)
        self.assertIn("metadata: Optional[Dict[str, Any]] = None", py_code)

    def test_reverse_transpile_pydantic_flavor(self):
        ts_code = """
        interface ServiceConfig {
            host: string;
            port: number;
            timeoutSeconds?: number;
        }
        """
        py_code = PolyglotTypeBridge.reverse_transpile(ts_code, source_lang="ts", model_flavor="pydantic")
        self.assertIn("class ServiceConfig(BaseModel):", py_code)
        self.assertIn("host: str", py_code)
        self.assertIn("port: int", py_code)
        self.assertIn("timeout_seconds: Optional[int] = None", py_code)

    def test_reverse_transpile_rust_struct(self):
        rust_code = """
        pub struct WorkerNode {
            pub node_id: String,
            pub ip_addr: String,
            pub cpu_cores: u32,
            pub is_leader: bool,
            pub error_count: Option<u64>,
            pub cluster_tags: Vec<String>,
        }
        """
        py_code = PolyglotTypeBridge.reverse_transpile(rust_code, source_lang="rust", model_flavor="dataclass")
        self.assertIn("class WorkerNode:", py_code)
        self.assertIn("node_id: str", py_code)
        self.assertIn("ip_addr: str", py_code)
        self.assertIn("cpu_cores: int", py_code)
        self.assertIn("is_leader: bool", py_code)
        self.assertIn("cluster_tags: List[str]", py_code)
        self.assertIn("error_count: Optional[int] = None", py_code)

    def test_reverse_transpile_go_struct(self):
        go_code = """
        type DatabasePool struct {
            DriverName string `json:"driver_name"`
            MaxOpenConns int `json:"max_open_conns"`
            SSLMode bool `json:"ssl_mode"`
            ConnectionURI *string `json:"connection_uri,omitempty"`
        }
        """
        py_code = PolyglotTypeBridge.reverse_transpile(go_code, source_lang="go", model_flavor="dataclass")
        self.assertIn("class DatabasePool:", py_code)
        self.assertIn("driver_name: str", py_code)
        self.assertIn("max_open_conns: int", py_code)
        self.assertIn("ssl_mode: bool", py_code)
        self.assertIn("connection_uri: Optional[str] = None", py_code)

    def test_cli_bridge_reverse_flag(self):
        cmd = [
            sys.executable,
            "tzero_v3.py",
            "--bridge-reverse",
            "interface AuthToken { token: string; exp: number; revoked?: boolean; }",
            "--from-lang",
            "ts"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(res.returncode, 0)
        self.assertIn("T-ZERO REVERSE POLYGLOT SCHEMA TRANSPILER", res.stdout)
        self.assertIn("class AuthToken:", res.stdout)
        self.assertIn("token: str", res.stdout)
        self.assertIn("revoked: Optional[bool] = None", res.stdout)


if __name__ == "__main__":
    unittest.main()

