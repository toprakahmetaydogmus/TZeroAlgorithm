# -*- coding: utf-8 -*-
"""Unit tests for Superdesign Orchestrator Module (tzero_superdesign.py)."""

import os
import sys
import shutil
import tempfile
import unittest

# Ensure root directory is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import tzero_superdesign as sd


class TestSuperdesignOrchestrator(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="tzero_sd_test_")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_generate_ui_specification(self):
        result = sd.superdesign_generate(
            prompt="Modern developer platform dashboard with analytics",
            design_type="ui",
            variations=2,
            workspace_path=self.test_dir,
        )
        self.assertTrue(result.get("success", False))
        self.assertEqual(result.get("design_type"), "ui")
        self.assertEqual(result.get("variations"), 2)
        self.assertIn("specifications", result)
        self.assertIn("files_to_create", result)
        self.assertEqual(len(result["files_to_create"]), 2)
        # Check that file paths are inside design_iterations
        for item in result["files_to_create"]:
            self.assertTrue(item["file_path"].endswith(".html"))
            self.assertIn("design_iterations", item["file_path"])

    def test_generate_component_and_framework(self):
        result = sd.superdesign_generate(
            prompt="Clean pricing card with tier comparison",
            design_type="component",
            framework="react",
            variations=1,
            workspace_path=self.test_dir,
        )
        self.assertTrue(result.get("success", False))
        self.assertEqual(result.get("framework"), "react")
        self.assertTrue(result["files_to_create"][0]["file_path"].endswith(".tsx") or result["files_to_create"][0]["file_path"].endswith(".jsx"))

    def test_generate_logo_svg(self):
        result = sd.superdesign_generate(
            prompt="Minimalist lightning bolt geometric logo",
            design_type="logo",
            variations=1,
            workspace_path=self.test_dir,
        )
        self.assertTrue(result.get("success", False))
        self.assertTrue(result["files_to_create"][0]["file_path"].endswith(".svg"))

    def test_generate_invalid_type(self):
        result = sd.superdesign_generate(
            prompt="Something",
            design_type="unsupported_type",
            workspace_path=self.test_dir,
        )
        self.assertFalse(result.get("success", True))
        self.assertIn("error", result)

    def test_iterate_design_existing(self):
        iter_dir = os.path.join(self.test_dir, "superdesign", "design_iterations")
        os.makedirs(iter_dir, exist_ok=True)
        test_file = os.path.join(iter_dir, "dashboard_v1.html")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html><html><body><h1>Old Dashboard</h1></body></html>")

        result = sd.superdesign_iterate(
            design_file=test_file,
            feedback="Increase card contrast and refine typography with Inter font",
            variations=1,
            workspace_path=self.test_dir,
        )
        self.assertTrue(result.get("success", False))
        self.assertIn("iteration_instructions", result)
        self.assertIn("feedback", result)
        self.assertTrue(len(result.get("target_files", [])) >= 1)

    def test_iterate_design_missing_file(self):
        result = sd.superdesign_iterate(
            design_file=os.path.join(self.test_dir, "nonexistent.html"),
            feedback="Improve colors",
            workspace_path=self.test_dir,
        )
        self.assertFalse(result.get("success", True))
        self.assertIn("error", result)

    def test_extract_design_system(self):
        result = sd.superdesign_extract_system(
            input_path_or_description="Modern slate dark theme with sky-400 accent and Inter font",
            system_name="tzero_tokens",
            workspace_path=self.test_dir,
        )
        self.assertTrue(result.get("success", False))
        self.assertIn("design_system", result)
        tokens = result["design_system"]
        self.assertIn("colors", tokens)
        self.assertIn("typography", tokens)
        self.assertIn("spacing", tokens)
        self.assertTrue(os.path.isfile(result["file_path"]))

    def test_list_and_gallery_generation(self):
        # Create dummy iteration and system files
        iter_dir = os.path.join(self.test_dir, "superdesign", "design_iterations")
        os.makedirs(iter_dir, exist_ok=True)
        sample_html = os.path.join(iter_dir, "dashboard_v1.html")
        with open(sample_html, "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html><html><head><title>Preview</title></head><body><h1>Card</h1></body></html>")

        # Test superdesign_list
        list_res = sd.superdesign_list(workspace_path=self.test_dir)
        self.assertTrue(list_res.get("success", False))
        self.assertTrue(len(list_res.get("iterations", [])) >= 1)

        # Test superdesign_gallery
        gallery_res = sd.superdesign_gallery(workspace_path=self.test_dir)
        self.assertTrue(gallery_res.get("success", False))
        self.assertTrue(os.path.isfile(gallery_res["gallery_file"]))
        with open(gallery_res["gallery_file"], "r", encoding="utf-8") as gf:
            content = gf.read()
            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("Superdesign Gallery", content)
            self.assertIn("dashboard_v1.html", content)

    def test_mcp_tools_registration(self):
        """Verifies that all 5 Superdesign tools are registered in create_mcp_server()."""
        import tzero_mcp
        server = tzero_mcp.create_mcp_server()
        # FastMCP or MCPServer tool inspection
        tool_names = set()
        if hasattr(server, "_tool_manager") and hasattr(server._tool_manager, "_tools"):
            tool_names = set(server._tool_manager._tools.keys())
        elif hasattr(server, "list_tools"):
            import asyncio
            tools = asyncio.run(server.list_tools())
            tool_names = {t.name for t in tools}

        expected_tools = {
            "superdesign_generate",
            "superdesign_iterate",
            "superdesign_extract_system",
            "superdesign_list",
            "superdesign_gallery",
        }
        for et in expected_tools:
            self.assertIn(et, tool_names, f"Expected MCP tool '{et}' to be registered on server")


if __name__ == "__main__":
    unittest.main()

