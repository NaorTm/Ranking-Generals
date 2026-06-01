from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from path_safety import assert_safe_output_path, safe_rmtree


class PathSafetyTests(unittest.TestCase):
    def test_allows_nested_output_snapshot_paths(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            repo_root = Path(raw_root)
            target = repo_root / "outputs_release_candidate" / "verification"

            self.assertEqual(assert_safe_output_path(target, repo_root), target.resolve())

    def test_accepts_string_paths(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            repo_root = Path(raw_root)
            target = repo_root / "outputs_release_candidate"

            self.assertEqual(assert_safe_output_path(str(target), str(repo_root)), target.resolve())

    def test_rejects_repository_root(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            repo_root = Path(raw_root)

            with self.assertRaisesRegex(ValueError, "repository root"):
                assert_safe_output_path(repo_root, repo_root)

    def test_rejects_generic_outputs_root(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            repo_root = Path(raw_root)

            with self.assertRaisesRegex(ValueError, "generic outputs root"):
                assert_safe_output_path(repo_root / "outputs", repo_root)

    def test_rejects_non_output_paths_inside_repo(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            repo_root = Path(raw_root)

            with self.assertRaisesRegex(ValueError, "non-output path"):
                assert_safe_output_path(repo_root / "docs", repo_root)

    def test_rejects_paths_outside_repo(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            repo_root = Path(raw_root) / "repo"
            repo_root.mkdir()
            outside = repo_root.parent / "outputs_escape"

            with self.assertRaisesRegex(ValueError, "outside repository root"):
                assert_safe_output_path(outside, repo_root)

    def test_safe_rmtree_removes_only_allowed_output_tree(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            repo_root = Path(raw_root)
            target = repo_root / "outputs_smoke"
            target.mkdir()
            (target / "result.csv").write_text("id,value\n1,ok\n", encoding="utf-8")

            safe_rmtree(target, repo_root)

            self.assertFalse(target.exists())

    def test_safe_rmtree_rejects_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            repo_root = Path(raw_root)
            target = repo_root / "outputs_smoke.txt"
            target.write_text("not a directory", encoding="utf-8")

            with self.assertRaises(NotADirectoryError):
                safe_rmtree(target, repo_root)

    def test_safe_rmtree_supports_missing_ok(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            repo_root = Path(raw_root)

            safe_rmtree(repo_root / "outputs_missing", repo_root, missing_ok=True)


if __name__ == "__main__":
    unittest.main()
