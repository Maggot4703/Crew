# flake8: noqa: E402
# test_traveller_agent.py
"""
Unit tests for TravellerAgent integration with Travellermap API and Traveller Wiki.
"""

import unittest

from traveller_agent import TravellerAgent


class TestTravellerAgent(unittest.TestCase):
    def setUp(self):
        self.agent = TravellerAgent()

    def test_get_world_info_regina(self):
        result = self.agent.get_world_info("Regina", "Spinward Marches")
        self.assertIn("world", result)
        self.assertEqual(result["world"].lower(), "regina")
        self.assertIn("map_data", result)
        self.assertIn("wiki_summary", result)
        print("Regina info:", result)

    def test_get_sector_info(self):
        result = self.agent.get_sector_info("Spinward Marches")
        self.assertIsInstance(result, dict)
        print("Spinward Marches sector info:", result)

    def test_search_wiki(self):
        result = self.agent.search_wiki("Regina")
        self.assertIsInstance(result, dict)
        print("Wiki search Regina:", result)


if __name__ == "__main__":
    unittest.main()
