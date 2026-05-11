#!/usr/bin/python3
"""
Test module for traveller5_scraper functionality.
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Add the parent directory to the path to import from the main module
sys.path.insert(0, str(Path(__file__).parent.parent))

from Crew import get_project_info, get_version
from traveller5_scraper import Traveller5Scraper


class TestTraveller5Scraper(unittest.TestCase):
    """Test cases for Traveller5 scraper functionality."""

    def test_version_info(self):
        """Test that version information is available."""
        version = get_version()
        self.assertIsInstance(version, str)
        self.assertTrue(len(version) > 0)

    def test_project_info(self):
        """Test that project information is available."""
        info = get_project_info()
        self.assertIsInstance(info, dict)
        self.assertIn("name", info)
        self.assertIn("version", info)
        self.assertIn("author", info)

    def test_scraper_returns_structured_data(self):
        """Scraper helpers should return structured ship and world dictionaries."""
        scraper = Traveller5Scraper(base_url="https://example.com")
        ship = scraper.scrape_ship_data("Scout Courier")
        world = scraper.scrape_world_info("Regina", sector="Spinward Marches")

        self.assertEqual(ship["name"], "Scout Courier")
        self.assertIn("tonnage", ship)
        self.assertIn("url", ship)
        self.assertEqual(world["name"], "Regina")
        self.assertEqual(world["sector"], "Spinward Marches")
        self.assertIn("uwp", world)

    def test_save_data_to_json_writes_file(self):
        """Scraped data should be writable as formatted JSON."""
        scraper = Traveller5Scraper()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "world.json"
            scraper.save_data_to_json({"name": "Regina"}, str(path))
            self.assertTrue(path.exists())
            self.assertIn('"name": "Regina"', path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
