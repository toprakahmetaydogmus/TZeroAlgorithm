# -*- coding: utf-8 -*-
"""
Tests for T-Zero Autonomous Dynamic Subagent Decomposer & Swarm Orchestrator.
"""

import os
import sys
import subprocess
import unittest
from tzero.tzero_subagent_engine import (
    DynamicSubagentDecomposer,
    AutonomousSwarmCoordinator,
    get_autonomous_swarm_coordinator
)


class TestDynamicSubagents(unittest.TestCase):

    def setUp(self):
        self.decomposer = DynamicSubagentDecomposer()
        self.coordinator = get_autonomous_swarm_coordinator()

    def test_decomposer_builtin_domains(self):
        mission = "Audit codebase for secret leaks, check AST architecture, and run unit tests"
        subtasks = self.decomposer.decompose(mission)
        agent_names = [s.agent_name for s in subtasks]

        self.assertIn("SecuritySentinelAgent", agent_names)
        self.assertIn("ASTArchitectAgent", agent_names)
        self.assertIn("TestSynthesizerAgent", agent_names)
        self.assertIn("OrchestratorPrimeAgent", agent_names)

    def test_decomposer_custom_domain_synthesis(self):
        mission = "Migrate database schema and optimize realtime websocket streaming"
        subtasks = self.decomposer.decompose(mission)
        agent_names = [s.agent_name for s in subtasks]

        self.assertIn("DatabaseSchemaSpecialist", agent_names)
        self.assertIn("RealtimeProtocolSpecialist", agent_names)
        custom_tasks = [s for s in subtasks if s.is_dynamically_synthesized]
        self.assertGreaterEqual(len(custom_tasks), 1)

    def test_coordinator_execution(self):
        mission = "Perform security audit and AST boundary validation"
        dossier = self.coordinator.execute_mission(mission_goal=mission)

        self.assertEqual(dossier.mission_title, mission)
        self.assertIn(dossier.consensus, ("APPROVED", "WARNING", "BLOCKED"))
        self.assertGreaterEqual(dossier.subagents_engaged, 2)
        self.assertIn("flowchart TD", dossier.mermaid_topology)
        self.assertIn("T-Zero Swarm Executive Dossier", dossier.summary_markdown)

    def test_mcp_orchestrate_agent_swarm_dynamic_mode(self):
        from tzero import tzero_mcp
        server = tzero_mcp.create_mcp_server()
        import asyncio
        res = asyncio.run(server.call_tool(
            "orchestrate_agent_swarm",
            {
                "goal": "Audit security and verify architecture",
                "orchestration_mode": "dynamic_subagents"
            }
        ))
        res_text = res[0].text if isinstance(res, list) and hasattr(res[0], "text") else str(res)
        self.assertIn("T-Zero", res_text)
        self.assertIn("Dossier", res_text)

    def test_cli_subagent_invocation(self):
        proc = subprocess.run(
            [sys.executable, "tzero/tzero_v3.py", "subagent", "Audit security and test coverage"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("DYNAMIC SUBAGENT SWARM", proc.stdout)
        self.assertIn("Executive Consensus", proc.stdout)


if __name__ == "__main__":
    unittest.main()

