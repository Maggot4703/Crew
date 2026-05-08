#!/usr/bin/env python3
"""Feature-level tests for the upgraded ReadMine flow."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from ReadMine import (  # noqa: E402
    CONTENT_TYPES,
    LEVELS,
    DocumentationFetcher,
    SubjectRequest,
    build_source_candidates,
    format_readmine_summary,
    parse_subject_line,
)


class FailingFetcher(DocumentationFetcher):
    """Inject one deterministic failure to exercise status tracking."""

    def create_content(self, subject, level, ctype):
        if level == "advanced" and ctype == "examples":
            raise RuntimeError("simulated failure")
        return super().create_content(subject, level, ctype)


class TestReadMineFeatures(unittest.TestCase):
    def test_parse_subject_line_supports_metadata_sources_tags_and_urls(self):
        request = parse_subject_line(
            "JSON | source=python-docs,mdn | tags=data,serialization | "
            "difficulty=medium | https://example.com/json"
        )

        self.assertEqual(request.name, "JSON")
        self.assertEqual(request.source_preferences, ("python-docs", "mdn"))
        self.assertEqual(request.tags, ("data", "serialization"))
        self.assertEqual(request.urls, ("https://example.com/json",))
        self.assertEqual(request.metadata["difficulty"], "medium")

    def test_build_source_candidates_prefers_direct_docs(self):
        request = SubjectRequest(name="JSON")

        candidates = build_source_candidates(request)

        urls = [candidate.url for candidate in candidates]
        self.assertIn("https://docs.python.org/3/library/json.html", urls)
        self.assertIn("https://developer.mozilla.org/en-US/docs/Glossary/JSON", urls)
        self.assertTrue(all("search" not in url for url in urls))

    def test_process_records_failed_items_and_stub_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            base_dir = tmp_path / "Reading Now"
            progress_file = tmp_path / "progress.json"
            subjects_file = tmp_path / "subjects.txt"
            subjects_file.write_text("CSS | tags=frontend\n", encoding="utf-8")

            summary = FailingFetcher(
                base_dir=base_dir,
                progress_file=progress_file,
                subjects_file=subjects_file,
                use_web=False,
            ).process()

            expected_items = len(LEVELS) * len(CONTENT_TYPES)
            self.assertEqual(summary["generated"], expected_items - 1)
            self.assertEqual(summary["failed"], 1)
            self.assertEqual(summary["stub_generated"], expected_items - 1)

            metadata_path = base_dir / "CSS" / "beginner" / "theory.meta.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(metadata["status"], "generated")
            self.assertTrue(metadata["used_stub"])

            progress = json.loads(progress_file.read_text(encoding="utf-8"))
            failed_item = progress["items"]["css::advanced::examples"]
            self.assertEqual(failed_item["status"], "failed")
            self.assertEqual(failed_item["error"], "simulated failure")

    def test_process_normalizes_legacy_subject_progress_entries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            base_dir = tmp_path / "Reading Now"
            progress_file = tmp_path / "progress.json"
            subjects_file = tmp_path / "subjects.txt"
            subjects_file.write_text("CSS\n", encoding="utf-8")
            progress_file.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "completed": [],
                        "completed_items": [],
                        "subjects": {
                            "CSS": {
                                "completed_items": ["css::beginner::theory"],
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            summary = DocumentationFetcher(
                base_dir=base_dir,
                progress_file=progress_file,
                subjects_file=subjects_file,
                use_web=False,
            ).process()

            self.assertEqual(summary["failed"], 0)
            progress = json.loads(progress_file.read_text(encoding="utf-8"))
            subject_progress = progress["subjects"]["CSS"]
            self.assertIn("items", subject_progress)
            self.assertIn("failed_items", subject_progress)
            self.assertIn("css::beginner::theory", subject_progress["items"])

    def test_format_readmine_summary_is_concise_and_informative(self):
        message = format_readmine_summary(
            {
                "subjects_total": 2,
                "generated": 9,
                "skipped": 3,
                "failed": 1,
                "stub_generated": 4,
                "fetched_generated": 5,
                "output_dir": "/tmp/Reading Now",
            }
        )

        self.assertIn("2 subject(s)", message)
        self.assertIn("9 generated (5 fetched, 4 stub)", message)
        self.assertIn("3 skipped, 1 failed", message)
        self.assertIn("/tmp/Reading Now", message)


if __name__ == "__main__":
    unittest.main()
