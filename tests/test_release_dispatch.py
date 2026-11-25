"""Release dispatch safety: no live network or credentials required."""

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("release_dispatch", ROOT / "scripts/dispatch_release.py")
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)
COMMIT = "a" * 40


def result(code=0, stdout="", stderr=""):
    return subprocess.CompletedProcess([], code, stdout, stderr)


class TestReleaseDispatch(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "pyproject.toml").write_text('[project]\nversion = "12.2.1"\n', encoding="utf-8")

    def test_existing_release_never_republishes_or_changes_tags(self):
        with patch.object(release, "gh", side_effect=[result(stdout=COMMIT), result(stdout="{}")]) as gh:
            answer = release.dispatch_release(self.root, "owner/repo", COMMIT)
        self.assertIn("already exists", answer["skipped"])
        self.assertEqual(gh.call_count, 2)

    def test_outdated_ci_cannot_publish_an_older_commit(self):
        with patch.object(release, "gh", return_value=result(stdout="b" * 40)) as gh:
            answer = release.dispatch_release(self.root, "owner/repo", COMMIT)
        self.assertIn("main advanced", answer["skipped"])
        gh.assert_called_once()

    def test_authentication_failure_is_not_treated_as_missing_release(self):
        with patch.object(release, "gh", side_effect=[
            result(stdout=COMMIT), result(1, stderr="gh: Forbidden (HTTP 403)")
        ]) as gh, self.assertRaisesRegex(RuntimeError, "Check existing release"):
            release.dispatch_release(self.root, "owner/repo", COMMIT)
        self.assertEqual(gh.call_count, 2)

    def test_all_publishers_use_the_immutable_release_tag(self):
        notes = self.root / "docs/releases/v12.2.1.md"
        notes.parent.mkdir(parents=True)
        notes.write_text("Tested release notes", encoding="utf-8")
        with patch.object(release, "gh", side_effect=[
            result(stdout=COMMIT), result(1, stderr="gh: Not Found (HTTP 404)"),
            *[result() for _ in range(7)],
        ]) as gh:
            answer = release.dispatch_release(self.root, "owner/repo", COMMIT)
        self.assertEqual(len(answer["dispatched"]), 6)
        create = gh.call_args_list[2].args
        self.assertEqual(create[create.index("--target") + 1], COMMIT)
        self.assertIn(str(notes), create)
        calls = [call.args for call in gh.call_args_list if call.args[:2] == ("workflow", "run")]
        self.assertEqual({call[2] for call in calls}, {
            "release.yml", "publish-npm.yml", "publish-pypi.yml", "publish-extension.yml",
            "publish-huggingface.yml", "rust-core.yml",
        })
        for call in calls:
            self.assertEqual(call[call.index("--ref") + 1], "v12.2.1")

    def test_one_dispatch_failure_still_attempts_remaining_publishers(self):
        with patch.object(release, "gh", side_effect=[
            result(stdout=COMMIT), result(1, stderr="HTTP 404"), result(),
            result(), result(1, stderr="dispatch denied"), *[result() for _ in range(4)],
        ]) as gh, self.assertRaisesRegex(RuntimeError, "publish-npm.yml"):
            release.dispatch_release(self.root, "owner/repo", COMMIT)
        self.assertEqual(gh.call_count, 9)

    def test_invalid_identifiers_make_no_github_calls(self):
        with patch.object(release, "gh") as gh:
            for repo, commit in (("--bad", COMMIT), ("owner/repo", "main")):
                with self.subTest(repository=repo, commit=commit), self.assertRaises(ValueError):
                    release.dispatch_release(self.root, repo, commit)
        gh.assert_not_called()
