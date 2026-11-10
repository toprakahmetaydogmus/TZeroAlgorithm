# -*- coding: utf-8 -*-
"""Incremental multi-language SQLite snapshot & watcher tests."""

import os
import sqlite3
import tempfile
import unittest
from unittest import mock

from tzero_snapshot import SnapshotEngine


class TestIncrementalSnapshot(unittest.TestCase):
    def test_multilanguage_snapshot_and_sqlite_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = {
                "app.py": "def start_app(port: int) -> bool:\n    return port > 0\n",
                "api.ts": "export function fetchUser(id: string): string {\n    return id.trim();\n}\n",
                "buf.rs": "pub fn alloc_buf(cap: usize) -> usize {\n    cap * 2\n}\n",
                "worker.go": "package main\nfunc RunJob(id int) int {\n    return id + 1\n}\n",
            }
            for name, body in files.items():
                with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                    fh.write(body)

            snap = SnapshotEngine.create_snapshot(tmp)
            self.assertEqual(snap.file_count, 4)
            self.assertIn("app.py", snap.files)
            self.assertIn("api.ts", snap.files)
            self.assertIn("buf.rs", snap.files)
            self.assertIn("worker.go", snap.files)

            db_path = SnapshotEngine.get_sqlite_path(tmp)
            self.assertTrue(os.path.isfile(db_path))
            conn = sqlite3.connect(db_path)
            try:
                rows = conn.execute("SELECT rel_path FROM file_snapshots").fetchall()
                self.assertEqual(len(rows), 4)
            finally:
                conn.close()

    def test_incremental_update_reuses_untouched_files_and_deletes_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("a.py", "b.py", "c.ts", "d.go"):
                with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                    if name.endswith(".py"):
                        fh.write(f"def fn_{name[0]}():\n    return 1\n")
                    elif name.endswith(".ts"):
                        fh.write("export function fnC(): number {\n    return 1;\n}\n")
                    else:
                        fh.write("package main\nfunc fnD() int {\n    return 1\n}\n")

            SnapshotEngine.create_snapshot(tmp)

            # Mutate only b.py and delete d.go
            b_path = os.path.join(tmp, "b.py")
            with open(b_path, "w", encoding="utf-8") as fh:
                fh.write("def fn_b():\n    return 42\n\ndef fn_b2():\n    return 99\n")
            os.remove(os.path.join(tmp, "d.go"))

            with mock.patch.object(
                SnapshotEngine,
                "_parse_file_snapshot",
                wraps=SnapshotEngine._parse_file_snapshot,
            ) as spy_parse:
                updated, stats = SnapshotEngine.update_incremental(tmp)
                self.assertEqual(spy_parse.call_count, 1)
                self.assertEqual(stats["reparsed"], 1)
                self.assertEqual(stats["reused"], 2)
                self.assertEqual(stats["deleted"], 1)
                self.assertEqual(updated.file_count, 3)
                self.assertIn("fn_b2", updated.files["b.py"].functions)
                self.assertNotIn("d.go", updated.files)

    def test_is_valid_detects_change_beyond_first_15_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(20):
                with open(os.path.join(tmp, f"mod_{i:02d}.py"), "w", encoding="utf-8") as fh:
                    fh.write(f"def run_{i}():\n    return {i}\n")

            snap = SnapshotEngine.create_snapshot(tmp)
            self.assertTrue(SnapshotEngine.is_valid(snap, tmp))

            last_file = os.path.join(tmp, "mod_19.py")
            with open(last_file, "w", encoding="utf-8") as fh:
                fh.write("def run_19():\n    return 9999\n\ndef extra_fn():\n    return 1\n")

            self.assertFalse(SnapshotEngine.is_valid(snap, tmp))

    def test_watch_mode_incremental_snapshot_once(self):
        import tzero_v3
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "core.py"), "w", encoding="utf-8") as fh:
                fh.write("def compute(x: int) -> int:\n    return x * 2\n")
            with open(os.path.join(tmp, "web.ts"), "w", encoding="utf-8") as fh:
                fh.write("export function render(): string { return 'ok'; }\n")

            ok = tzero_v3.run_watch_mode(tmp, once_test=True)
            self.assertTrue(ok)
            self.assertTrue(os.path.isfile(os.path.join(tmp, ".tzero", "context.txt")))
            self.assertTrue(os.path.isfile(SnapshotEngine.get_sqlite_path(tmp)))


if __name__ == "__main__":
    unittest.main()
