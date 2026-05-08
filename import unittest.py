"""Minimal smoke test proving the stdlib ``unittest`` module is available."""

from __future__ import annotations

import unittest


class UnittestImportSmokeTest(unittest.TestCase):
    def test_unittest_import_available(self) -> None:
        self.assertTrue(hasattr(unittest, "TestCase"))


if __name__ == "__main__":
    unittest.main()
