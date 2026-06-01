from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from qa_dashboard_snapshot import write_summary


class DashboardQaOutputTests(unittest.TestCase):
    def test_write_summary_uses_explicit_output_without_touching_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            snapshot_dir = root / "snapshot"
            snapshot_dir.mkdir()
            output_path = root / "qa" / "dashboard_qa_summary.json"
            summary = {
                "snapshot": "snapshot",
                "all_checks_passed": True,
                "checks": {"example": {"ok": True}},
            }

            written_path = write_summary(summary, snapshot_dir, output_path)

            self.assertEqual(written_path, output_path)
            self.assertTrue(output_path.exists())
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8")), summary)
            self.assertFalse((snapshot_dir / "dashboard_qa_summary.json").exists())

    def test_write_summary_preserves_default_snapshot_output(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            snapshot_dir = Path(raw_root) / "snapshot"
            snapshot_dir.mkdir()
            summary = {"snapshot": "snapshot", "all_checks_passed": True}

            written_path = write_summary(summary, snapshot_dir)

            self.assertEqual(written_path, snapshot_dir / "dashboard_qa_summary.json")
            self.assertEqual(json.loads(written_path.read_text(encoding="utf-8")), summary)


if __name__ == "__main__":
    unittest.main()
