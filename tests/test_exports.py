"""
Test Suite for ContextExportManager and Token Cost Calculator
"""
import unittest
import os
import tempfile
from tzero_v3 import ContextExportManager, calculate_token_cost, PROVIDER_COST_PER_MILLION

class TestExportsAndCost(unittest.TestCase):
    def test_token_cost_calculation(self):
        # OpenAI $2.50 / M
        cost_openai = calculate_token_cost(1_000_000, "OpenAI")
        self.assertAlmostEqual(cost_openai, 2.50)
        
        # Local Ollama is always $0.00
        cost_ollama = calculate_token_cost(500_000, "Ollama (Local)")
        self.assertEqual(cost_ollama, 0.0)

    def test_agents_blueprint_generation(self):
        blueprint = ContextExportManager.generate_agents_blueprint(
            project_name="TestProject",
            files_tree="├── main.py",
            snippets={"main.py": "def hello(): pass"},
            extra_rules="Follow clean architecture."
        )
        self.assertIn("# 🤖 AGENTS & AI ASSISTANT BLUEPRINT: TestProject", blueprint)
        self.assertIn("Follow clean architecture.", blueprint)
        self.assertIn("Zero-Leak", blueprint)

    def test_architecture_blueprint_generation(self):
        arch = ContextExportManager.generate_architecture_blueprint(
            project_name="TestProject",
            files=["main.py", "utils.py"],
            deps={"main.py": ["utils"]}
        )
        self.assertIn("# 🏛️ Architecture & System Blueprint: TestProject", arch)
        self.assertIn("```mermaid", arch)

    def test_repo_map_generation(self):
        rmap = ContextExportManager.generate_repo_map(
            project_name="TestProject",
            files=["app.py"],
            snippets={"app.py": "class Server: pass"}
        )
        self.assertIn("=== REPO MAP: TestProject (1 files) ===", rmap)
        self.assertIn("class Server: pass", rmap)

    def test_styled_html_generation(self):
        html = ContextExportManager.generate_styled_html(
            project_name="TestProject",
            markdown_content="# Header\n\n```python\nprint(1)\n```"
        )
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<h1>Header</h1>", html)
        self.assertIn("<code class=\"lang-python\">", html)

if __name__ == "__main__":
    unittest.main()
