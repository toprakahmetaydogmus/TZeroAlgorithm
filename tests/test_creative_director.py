# -*- coding: utf-8 -*-
"""Unit tests for T-Zero Jarvis Multi-Modal Creative Director & Prompt Engine."""

import os
import sys
import subprocess
import unittest

from tzero.tzero_jarvis.creative_director import (
    JarvisCreativeDirector,
    VideoPromptSpec,
    PhotoPromptSpec,
    StoryboardScene
)


class TestJarvisCreativeDirector(unittest.TestCase):
    def test_generate_video_prompt(self):
        spec = JarvisCreativeDirector.generate_video_prompt(
            topic="Autonomous AI Swarm",
            style="cyberpunk",
            duration=8
        )
        self.assertIsInstance(spec, VideoPromptSpec)
        self.assertIn("Autonomous AI Swarm", spec.prompt)
        self.assertIn("Camera Direction:", spec.prompt)
        self.assertEqual(spec.duration_seconds, 8)
        self.assertIn("Sora", spec.tool)

    def test_generate_photo_prompt(self):
        spec = JarvisCreativeDirector.generate_photo_prompt(
            subject="Cybernetic Security Core",
            style="cinematic",
            aspect_ratio="16:9"
        )
        self.assertIsInstance(spec, PhotoPromptSpec)
        self.assertIn("Cybernetic Security Core", spec.prompt)
        self.assertIn("--ar 16:9", spec.parameters)
        self.assertIn("--v 6.1", spec.parameters)

    def test_generate_launch_storyboard(self):
        scenes = JarvisCreativeDirector.generate_launch_storyboard(
            product_name="T-Zero",
            core_feature="Deterministic AST Context Compressor"
        )
        self.assertEqual(len(scenes), 5)
        for i, sc in enumerate(scenes, 1):
            self.assertIsInstance(sc, StoryboardScene)
            self.assertEqual(sc.scene_number, i)
            self.assertTrue(len(sc.voiceover_script) > 0)
            self.assertTrue(len(sc.video_prompt) > 0)

    def test_synthesize_from_code(self):
        sample_code = """
import os
import hashlib

class ZeroLeakSecurityVault:
    \"\"\"Protects workspace against API secret leaks.\"\"\"
    def encrypt_secret(self, secret: str) -> str:
        return hashlib.sha256(secret.encode()).hexdigest()
"""
        res = JarvisCreativeDirector.synthesize_from_code(sample_code, file_name="vault.py")
        self.assertEqual(res["file_name"], "vault.py")
        self.assertIn("Zero-Leak", res["detected_theme"])
        self.assertIn("ZeroLeakSecurityVault", res["extracted_symbols"])
        self.assertIn("video_spec", res)
        self.assertIn("photo_spec", res)
        self.assertEqual(len(res["storyboard_scenes"]), 5)

    def test_cli_creative_flag(self):
        res = subprocess.run(
            [sys.executable, "-m", "tzero.tzero_v3", "--creative", "Quantum Compiler"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("T-Zero Jarvis Creative Director", res.stdout)
        self.assertIn("Cinematic Video Prompt", res.stdout)
        self.assertIn("Viral Launch Storyboard", res.stdout)


if __name__ == "__main__":
    unittest.main()
