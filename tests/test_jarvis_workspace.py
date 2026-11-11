# -*- coding: utf-8 -*-
"""
Tests for T-Zero Jarvis Master Workspace Orchestrator & Executive Governance Engine
-----------------------------------------------------------------------------------
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
"""

import os
import sys
import json
import shutil
import tempfile
import unittest

# Ensure root directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from tzero.tzero_jarvis.workspace_orchestrator import (
    WorkspaceProfiler,
    WorkspaceProfile,
    WorkspaceGovernanceSynthesizer,
    WorkspaceOrchestrator
)
from tzero.tzero_jarvis.orchestrator import JarvisOrchestrator
from tzero.tzero_features import AgentRulesGenerator


class TestWorkspaceProfiler(unittest.TestCase):
    """Verifies polyglot stack detection and workspace profiling."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_profile_python_project(self):
        # Setup Python structure
        with open(os.path.join(self.temp_dir, "pyproject.toml"), "w", encoding="utf-8") as f:
            f.write('[project]\nname = "test-py"\ndependencies = ["fastapi", "pytest"]\n')
        with open(os.path.join(self.temp_dir, "main.py"), "w", encoding="utf-8") as f:
            f.write('from fastapi import FastAPI\napp = FastAPI()\n')

        profiler = WorkspaceProfiler(self.temp_dir)
        profile = profiler.profile()

        self.assertEqual(profile.primary_language, "Python")
        self.assertIn("FastAPI", profile.frameworks)
        self.assertGreaterEqual(profile.total_files, 2)
        self.assertTrue(profile.default_test_command)

    def test_profile_typescript_node_project(self):
        # Setup Node / TS structure
        pkg = {
            "name": "mock-next-app",
            "dependencies": {"next": "^14.0.0", "react": "^18.0.0"},
            "devDependencies": {"typescript": "^5.0.0", "jest": "^29.0.0"},
            "scripts": {"test": "jest", "build": "next build", "lint": "next lint"}
        }
        with open(os.path.join(self.temp_dir, "package.json"), "w", encoding="utf-8") as f:
            json.dump(pkg, f)
        with open(os.path.join(self.temp_dir, "index.tsx"), "w", encoding="utf-8") as f:
            f.write('export default function Home() { return <div>Hello</div>; }\n')

        profiler = WorkspaceProfiler(self.temp_dir)
        profile = profiler.profile()

        self.assertIn(profile.primary_language, ("TypeScript", "TypeScript (React)"))
        self.assertIn("Next.js", profile.frameworks)
        self.assertIn("npm", profile.package_managers)
        self.assertEqual(profile.default_test_command, "npm test")

    def test_profile_rust_project(self):
        with open(os.path.join(self.temp_dir, "Cargo.toml"), "w", encoding="utf-8") as f:
            f.write('[package]\nname = "mock_rust"\nversion = "0.1.0"\n[dependencies]\naxum = "0.7"\ntokio = "1.0"\n')
        os.makedirs(os.path.join(self.temp_dir, "src"), exist_ok=True)
        with open(os.path.join(self.temp_dir, "src", "main.rs"), "w", encoding="utf-8") as f:
            f.write('fn main() { println!("Hello"); }\n')

        profiler = WorkspaceProfiler(self.temp_dir)
        profile = profiler.profile()

        self.assertEqual(profile.primary_language, "Rust")
        self.assertIn("Axum", profile.frameworks)
        self.assertIn("cargo", profile.package_managers)
        self.assertEqual(profile.default_test_command, "cargo test")

    def test_profile_go_project(self):
        with open(os.path.join(self.temp_dir, "go.mod"), "w", encoding="utf-8") as f:
            f.write('module example.com/mockgo\ngo 1.22\nrequire github.com/gin-gonic/gin v1.9.1\n')
        with open(os.path.join(self.temp_dir, "main.go"), "w", encoding="utf-8") as f:
            f.write('package main\nfunc main() {}\n')

        profiler = WorkspaceProfiler(self.temp_dir)
        profile = profiler.profile()

        self.assertEqual(profile.primary_language, "Go")
        self.assertIn("Gin", profile.frameworks)
        self.assertEqual(profile.default_test_command, "go test ./...")


class TestWorkspaceGovernanceSynthesizer(unittest.TestCase):
    """Verifies generation of specialized .md and rule contracts."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        with open(os.path.join(self.temp_dir, "app.py"), "w", encoding="utf-8") as f:
            f.write("def run(): pass\n")
        self.profiler = WorkspaceProfiler(self.temp_dir)
        self.profile = self.profiler.profile()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_synthesize_all_rules(self):
        rules = WorkspaceGovernanceSynthesizer.synthesize_all(self.profile)

        # Must include all critical governance files
        expected_keys = [
            ".cursorrules",
            "AGENT.md",
            "AGENTS.md",
            ".clinerules",
            ".windsurfrules",
            "CLAUDE.md",
            os.path.join(".github", "copilot-instructions.md"),
            "ARCHITECTURE.md",
            "tzero.rules.json"
        ]
        for k in expected_keys:
            self.assertIn(k, rules, f"Missing rule file: {k}")

        # Check content quality
        self.assertIn("ZERO-LEAK SECURITY MANDATE", rules[".cursorrules"])
        self.assertIn("MASTER AGENT DIRECTIVE", rules["AGENT.md"])
        self.assertIn("flowchart TD", rules["ARCHITECTURE.md"])
        self.assertIn("tzero_grounding", rules["AGENT.md"] or rules["ARCHITECTURE.md"] or rules[".cursorrules"])


class TestWorkspaceOrchestrator(unittest.TestCase):
    """Verifies the Master Workspace Orchestrator operations."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        # Mock mini python app
        os.makedirs(os.path.join(self.temp_dir, "tests"), exist_ok=True)
        with open(os.path.join(self.temp_dir, "service.py"), "w", encoding="utf-8") as f:
            f.write("def calculate_total(a, b): return a + b\n")
        with open(os.path.join(self.temp_dir, "tests", "test_service.py"), "w", encoding="utf-8") as f:
            f.write("import unittest\nfrom service import calculate_total\nclass T(unittest.TestCase):\n  def test_c(self):\n    self.assertEqual(calculate_total(1, 2), 3)\n")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_orchestrate_workspace_full_flow(self):
        orch = WorkspaceOrchestrator(workspace_root=self.temp_dir)
        result = orch.orchestrate_workspace(auto_apply_rules=True, run_swarm=True, run_diagnostics=False)

        self.assertEqual(result["status"], "SUCCESS")
        self.assertGreaterEqual(len(result["applied_rule_files"]), 8)
        self.assertIn("WORKSPACE_ORCHESTRATION.md", result["applied_rule_files"])
        self.assertIn(".cursorrules", result["applied_rule_files"])
        self.assertIn("AGENT.md", result["applied_rule_files"])
        self.assertIn("ARCHITECTURE.md", result["applied_rule_files"])

        # Verify files were actually written to disk
        self.assertTrue(os.path.isfile(os.path.join(self.temp_dir, ".cursorrules")))
        self.assertTrue(os.path.isfile(os.path.join(self.temp_dir, "AGENT.md")))
        self.assertTrue(os.path.isfile(os.path.join(self.temp_dir, "WORKSPACE_ORCHESTRATION.md")))
        self.assertTrue(os.path.isfile(os.path.join(self.temp_dir, "ARCHITECTURE.md")))

        # Check swarm consensus
        self.assertIn("consensus_verdict", result["swarm_consensus"])

    def test_jarvis_orchestrator_integration(self):
        jarvis = JarvisOrchestrator(workspace_root=self.temp_dir)
        
        # Profile workspace
        prof_dict = jarvis.profile_workspace()
        self.assertEqual(prof_dict["primary_language"], "Python")

        # Tune rules
        tuned = jarvis.tune_workspace_rules(auto_apply=True)
        self.assertGreaterEqual(len(tuned["applied_files"]), 8)

        # Orchestrate goal with workspace keyword
        goal_res = jarvis.orchestrate_goal("Audit and orchestrate workspace agent rules")
        self.assertTrue(goal_res.success)
        stages = [s["stage"] for s in goal_res.steps]
        self.assertIn("WORKSPACE_ORCHESTRATION", stages)


    def test_jarvis_planning_and_capabilities(self):
        jarvis = JarvisOrchestrator(workspace_root=self.temp_dir)
        
        # Test capabilities presentation
        caps = jarvis.present_capabilities()
        self.assertIn("T-ZERO JARVIS MASTER WORKSPACE ORCHESTRATOR", caps)
        self.assertIn("Neler Yapabilirim?", caps)
        self.assertIn("get_project_context_tree", caps)

        # Test executive plan generation
        plan = jarvis.generate_plan("Refactor authentication module")
        self.assertIn("phases", plan)
        self.assertEqual(len(plan["phases"]), 4)
        self.assertIn("Faz 1:", plan["markdown"])
        self.assertIn("get_project_context_tree", plan["markdown"])

    def test_mcp_tool_jarvis_orchestrate_goal_planning_mode(self):
        from tzero import tzero_mcp
        import asyncio
        server = tzero_mcp.create_mcp_server()

        # 1. Plan request via goal="plan"
        res_plan = asyncio.run(server.call_tool(
            "jarvis_orchestrate_goal",
            {"goal": "plan", "project_root": self.temp_dir}
        ))
        res_text = res_plan[0].text if isinstance(res_plan, list) else str(res_plan)
        self.assertIn("T-ZERO JARVIS MASTER WORKSPACE ORCHESTRATOR", res_text)
        self.assertIn("Faz 1:", res_text)

        # 2. What can you do request
        res_what = asyncio.run(server.call_tool(
            "jarvis_orchestrate_goal",
            {"goal": "ne yapabilirsin", "project_root": self.temp_dir}
        ))
        res_what_text = res_what[0].text if isinstance(res_what, list) else str(res_what)
        self.assertIn("Neler Yapabilirim?", res_what_text)

        # 3. Test prompt jarvis_workspace_copilot
        prompts = asyncio.run(server.list_prompts())
        p_names = [p.name for p in prompts]
        self.assertIn("jarvis_workspace_copilot", p_names)


class TestAgentRulesGeneratorExtended(unittest.TestCase):
    """Verifies AgentRulesGenerator in tzero_features now outputs AGENT.md and ARCHITECTURE.md."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_all_creates_agent_and_arch(self):
        created = AgentRulesGenerator.export_all(self.temp_dir)
        self.assertGreaterEqual(len(created), 8)
        
        # Verify AGENT.md exists
        agent_p = os.path.join(self.temp_dir, "AGENT.md")
        self.assertTrue(os.path.isfile(agent_p))

        # Verify ARCHITECTURE.md exists
        arch_p = os.path.join(self.temp_dir, "ARCHITECTURE.md")
        self.assertTrue(os.path.isfile(arch_p))


if __name__ == "__main__":
    unittest.main()
