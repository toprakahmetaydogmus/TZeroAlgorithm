# -*- coding: utf-8 -*-
"""
Tests for T-Zero Neural Cortex & AgentOS (v9.0.0-CORTEX)
Validates 100+ Capability Registry, 12 Autonomous Fleet Agents, AgentForge,
and HallucinationGuard pre-flight validation.
"""

import unittest
import os
import tempfile
from tzero_neural_cortex import (
    CapabilityRegistry,
    TZeroAgentFleet,
    AgentForge,
    HallucinationGuard,
    NeuralSwarmCoordinator,
    CapabilityCategory
)


class TestTZeroNeuralCortex(unittest.TestCase):

    def setUp(self):
        self.registry = CapabilityRegistry()
        self.fleet = TZeroAgentFleet()
        self.forge = AgentForge()
        self.guard = HallucinationGuard()
        self.coordinator = NeuralSwarmCoordinator()

    def test_capability_matrix_has_at_least_105_features(self):
        all_caps = self.registry.list_all()
        self.assertEqual(len(all_caps), 105, f"Expected 105 capabilities, found {len(all_caps)}")
        
        # Verify all 7 Pillars are well-represented
        categories = {cap.category for cap in all_caps}
        self.assertIn(CapabilityCategory.I_COMPILER_AST, categories)
        self.assertIn(CapabilityCategory.II_MATRYOSHKA_TOKEN, categories)
        self.assertIn(CapabilityCategory.III_SHADOW_WORKSPACE, categories)
        self.assertIn(CapabilityCategory.IV_RUNTIME_TELEMETRY, categories)
        self.assertIn(CapabilityCategory.V_ZERO_LATENCY_ORCH, categories)
        self.assertIn(CapabilityCategory.VI_COGNITIVE_MEMORY, categories)
        self.assertIn(CapabilityCategory.VII_HARDWARE_SECURITY, categories)

        # Check search by pillar
        p1_caps = self.registry.search(pillar_num=1)
        self.assertEqual(len(p1_caps), 15)

    def test_matryoshka_resolution_engine(self):
        from tzero_neural_cortex import MatryoshkaResolutionEngine
        sample_code = '''"""Core calculator service."""
import math

class Calculator:
    def add(self, a, b):
        return a + b

def multiply(x, y):
    return x * y
'''
        layers = MatryoshkaResolutionEngine.resolve_layers(sample_code, "calc.py")
        self.assertIn("L0", layers)
        self.assertIn("L1", layers)
        self.assertIn("L2", layers)
        self.assertIn("L3", layers)
        self.assertIn("Core calculator service", layers["L0"])
        self.assertIn("class Calculator", layers["L1"])
        self.assertIn("def add", layers["L2"])

    def test_shadow_workspace_cow_overlay(self):
        from tzero_neural_cortex import ShadowWorkspaceEngine
        with tempfile.TemporaryDirectory() as tmp_dir:
            shadow = ShadowWorkspaceEngine(workspace_root=tmp_dir)
            shadow.stage("hello.py", "print('hello from shadow')\n")
            self.assertIn("hello.py", shadow.list_staged())
            self.assertEqual(shadow.get_staged("hello.py"), "print('hello from shadow')\n")
            
            # Dry run diff
            diffs = shadow.dry_run_diff()
            self.assertIn("hello.py", diffs)
            
            # Commit atomic
            success, committed = shadow.commit_atomic()
            self.assertTrue(success)
            self.assertEqual(committed, ["hello.py"])
            self.assertTrue(os.path.exists(os.path.join(tmp_dir, "hello.py")))

    def test_agent_fleet_contains_12_specialized_agents(self):
        agents = self.fleet.list_agents()
        self.assertEqual(len(agents), 12, "Fleet should contain exactly 12 elite specialized agents")
        
        expected_names = [
            "SecuritySentinelAgent",
            "ASTArchitectAgent",
            "DeadCodePurgerAgent",
            "TestSynthesizerAgent",
            "PolyglotTranspilerAgent",
            "BugHunterAgent",
            "PerformanceProfilerAgent",
            "DocstringGeneratorAgent",
            "DependencyAuditorAgent",
            "RefactorModernizerAgent",
            "HallucinationValidatorAgent",
            "DevOpsReleaseAgent"
        ]
        for name in expected_names:
            agent = self.fleet.get_agent(name)
            self.assertIsNotNone(agent, f"Missing agent: {name}")
            report = agent.evaluate("Test mission goal", "context snippet")
            self.assertIn(report.verdict, ["APPROVED", "WARNING", "CRITICAL_ACTION_REQUIRED"])
            self.assertIsInstance(report.recommendations, list)

    def test_agent_forge_synthesizes_custom_subagent(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            manifest = self.forge.synthesize_subagent(
                role="GraphQLMigrationExpert",
                task="Migrate REST controllers to Apollo GraphQL schema",
                workspace_dir=tmp_dir,
                tier_level="T-2"
            )
            self.assertEqual(manifest["role"], "GraphQLMigrationExpert")
            self.assertIn("SKILL.md", manifest["generated_files"])
            self.assertIn("agent.json", manifest["generated_files"])
            self.assertTrue(os.path.exists(manifest["generated_files"]["SKILL.md"]))
            self.assertTrue(os.path.exists(manifest["generated_files"]["agent.json"]))

    def test_hallucination_guard_detects_nonexistent_methods(self):
        code_with_hallucination = """
import os
import sys

def process_data(data):
    # This method does not exist on os or math!
    return os.non_existent_fake_method_xyz12345(data)
"""
        result = self.guard.validate_code(code_with_hallucination)
        self.assertFalse(result.is_clean)
        self.assertGreater(len(result.hallucinations), 0)
        self.assertIn("non_existent_fake_method_xyz12345", result.hallucinations[0].symbol_name)

    def test_hallucination_guard_approves_valid_code(self):
        valid_code = """
import os
import math

def calculate(x):
    return math.sqrt(x) + len(os.getcwd())
"""
        result = self.guard.validate_code(valid_code)
        self.assertTrue(result.is_clean)
        self.assertEqual(len(result.hallucinations), 0)

    def test_neural_swarm_coordinator_executes_parallel_plan(self):
        plan = self.coordinator.create_mission_plan(
            mission_title="V9 Upgrade Gate",
            tasks=[
                {"id": "t1", "agent": "SecuritySentinelAgent", "scope": ["app.py"]},
                {"id": "t2", "agent": "ASTArchitectAgent", "scope": ["tzero_v3.py"]},
                {"id": "t3", "agent": "HallucinationValidatorAgent", "scope": ["tzero_neural_cortex.py"]}
            ]
        )
        self.assertEqual(len(plan.dag_nodes), 3)
        self.assertTrue(plan.is_conflict_free)
        execution_report = self.coordinator.execute_mission(plan)
        self.assertTrue(execution_report["success"])
        self.assertEqual(len(execution_report["agent_results"]), 3)


if __name__ == "__main__":
    unittest.main()
