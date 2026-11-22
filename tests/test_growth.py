# -*- coding: utf-8 -*-
"""Unit tests for T-Zero $0.00 viral growth and marketing automation engine."""

import unittest
from pathlib import Path
from tzero.tzero_growth import (
    render_progress_bar,
    generate_reddit_posts,
    generate_show_hn,
    generate_twitter_thread,
    generate_product_hunt,
    generate_awesome_lists_prs,
    export_all_marketing_materials,
    get_live_github_stars,
)


class TestTZeroGrowthEngine(unittest.TestCase):
    def test_progress_bar(self):
        bar = render_progress_bar(16, 100, length=20)
        self.assertIn("16/100 Stars", bar)
        self.assertIn("16.0%", bar)

    def test_reddit_posts_generation(self):
        posts = generate_reddit_posts()
        self.assertIn("r/Cursor", posts)
        self.assertIn("r/ClaudeAI", posts)
        self.assertIn("r/LocalLLaMA", posts)
        self.assertIn("r/Turkey", posts)
        for sub, data in posts.items():
            self.assertTrue(len(data["title"]) > 10)
            self.assertTrue(len(data["body"]) > 100)
            self.assertIn("github.com/toprakahmetaydogmus/TZeroAlgorithm", data["body"])

    def test_show_hn_generation(self):
        hn = generate_show_hn()
        self.assertTrue(hn["title"].startswith("Show HN:"))
        self.assertIn("Toprak", hn["first_comment"])
        self.assertIn("software engineer", hn["first_comment"])

    def test_twitter_thread(self):
        tweets = generate_twitter_thread()
        self.assertEqual(len(tweets), 7)
        self.assertTrue(tweets[0].startswith("1/7"))
        self.assertTrue(tweets[6].startswith("7/7"))
        self.assertIn("github.com/toprakahmetaydogmus/TZeroAlgorithm", tweets[6])

    def test_product_hunt(self):
        ph = generate_product_hunt()
        self.assertIn("name", ph)
        self.assertIn("tagline", ph)
        self.assertIn("maker_comment", ph)
        self.assertTrue(len(ph["tagline"]) < 80)

    def test_awesome_lists(self):
        awesome = generate_awesome_lists_prs()
        self.assertIn("awesome-mcp-servers", awesome)
        self.assertIn("awesome-cursorrules", awesome)

    def test_export_all_materials(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_p = Path(tmp_dir)
            export_all_marketing_materials(out_p)
            self.assertTrue((out_p / "REDDIT_POSTS.md").is_file())
            self.assertTrue((out_p / "HACKER_NEWS_SHOW_HN.md").is_file())
            self.assertTrue((out_p / "TWITTER_THREAD.md").is_file())
            self.assertTrue((out_p / "PRODUCT_HUNT_LAUNCH.md").is_file())
            self.assertTrue((out_p / "AWESOME_LISTS_PRS.md").is_file())

    def test_live_stars_fallback(self):
        stars = get_live_github_stars()
        self.assertIsInstance(stars, int)
        self.assertGreaterEqual(stars, 16)


if __name__ == "__main__":
    unittest.main()

