# -*- coding: utf-8 -*-
"""Unit tests for T-Zero CLI 1-click viral share link hub."""

import io
import unittest
from unittest.mock import patch

from tzero.tzero_v3 import print_viral_share_hub


class TestTZeroShareHub(unittest.TestCase):
    def test_print_viral_share_hub_output(self):
        f = io.StringIO()
        with patch("sys.stdout", f):
            print_viral_share_hub()
        out = f.getvalue()
        self.assertIn("T-ZERO 1-CLICK COMMUNITY SHARE & VIRAL LAUNCH HUB", out)
        self.assertIn("twitter.com/intent/tweet", out)
        self.assertIn("reddit.com/submit", out)
        self.assertIn("news.ycombinator.com/submitlink", out)
        self.assertIn("linkedin.com/sharing", out)
        self.assertIn("api.whatsapp.com/send", out)
        self.assertIn("github.com/toprakahmetaydogmus/TZeroAlgorithm", out)
        self.assertIn("Toprak%20Ahmet%20Aydo%C4%9Fmu%C5%9F", out)


if __name__ == "__main__":
    unittest.main()
