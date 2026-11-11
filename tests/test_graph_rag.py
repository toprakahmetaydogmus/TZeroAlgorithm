# -*- coding: utf-8 -*-
import os
import tempfile
import unittest

from tzero.tzero_graph_rag import VectorlessGraphRAG


class TestVectorlessGraphRAG(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.ws = self.tmpdir.name

        # Create mock codebase files
        with open(os.path.join(self.ws, "auth.py"), "w", encoding="utf-8") as f:
            f.write(
                "import os\n"
                "from db import DatabaseSession\n\n"
                "class TokenValidator:\n"
                "    def validate(self, token: str) -> bool:\n"
                "        return len(token) > 10\n\n"
                "def authenticate_user(user: str) -> bool:\n"
                "    return True\n"
            )

        with open(os.path.join(self.ws, "db.py"), "w", encoding="utf-8") as f:
            f.write(
                "class DatabaseSession:\n"
                "    def query(self):\n"
                "        pass\n"
            )

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_indexing_and_hybrid_retrieval(self):
        rag = VectorlessGraphRAG(self.ws)
        count = rag.index_workspace()
        self.assertGreater(count, 0)
        self.assertGreater(len(rag.chunks), 0)

        results = rag.query("authenticate token validator", top_k=3)
        self.assertGreater(len(results), 0)
        top_names = [r["name"] for r in results]
        self.assertTrue(
            any("TokenValidator" in n or "authenticate_user" in n for n in top_names),
            f"Expected auth symbols in top results, got {top_names}"
        )
        self.assertGreater(results[0]["hybrid_score"], 0.0)
        self.assertIn("centrality", results[0])


if __name__ == "__main__":
    unittest.main()

