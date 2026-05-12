# flake8: noqa: E402
#!/usr/bin/env python3
"""Regression tests for ReadMine progress and resume behavior."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from ReadMine import DEFAULT_OUTPUT_LEVELS  # noqa: E402
from ReadMine import CONTENT_TYPES, DocumentationFetcher


class TestReadMineProgress(unittest.TestCase):
    """Ensure ReadMine skips completed items on rerun."""

    def test_process_tracks_items_and_skips_completed_outputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            base_dir = tmp_path / "Reading Now"
            progress_file = tmp_path / "progress.json"
            subjects_file = tmp_path / "subjects.txt"
            subjects_file.write_text("python\n")

            first_run = DocumentationFetcher(
                base_dir=base_dir,
                use_web=False,
                progress_file=progress_file,
                subjects_file=subjects_file,
            ).process()

            expected_items = len(DEFAULT_OUTPUT_LEVELS) * len(CONTENT_TYPES)
            self.assertEqual(first_run["generated"], expected_items)
            self.assertEqual(first_run["skipped"], 0)
            self.assertEqual(first_run["stub_generated"], expected_items)

            theory_file = base_dir / "python" / "beginner" / "theory.txt"
            theory_meta = base_dir / "python" / "beginner" / "theory.meta.json"
            original_content = theory_file.read_text()
            self.assertIn("Status: stub", original_content)
            self.assertTrue(theory_meta.exists())

            second_run = DocumentationFetcher(
                base_dir=base_dir,
                use_web=False,
                progress_file=progress_file,
                subjects_file=subjects_file,
            ).process()

            self.assertEqual(second_run["generated"], 0)
            self.assertEqual(second_run["skipped"], expected_items)
            self.assertEqual(theory_file.read_text(), original_content)

            progress = json.loads(progress_file.read_text())
            self.assertEqual(len(progress["completed_items"]), expected_items)
            self.assertEqual(progress["completed"], ["python"])
            self.assertEqual(
                len(progress["subjects"]["python"]["completed_items"]), expected_items
            )
            self.assertEqual(
                progress["items"]["python::beginner::theory"]["status"], "skipped"
            )


if __name__ == "__main__":
    unittest.main()
