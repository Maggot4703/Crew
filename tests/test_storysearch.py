# flake8: noqa: E402
"""
Test suite for storySearch.py module.

This module tests the story searching functionality including keyword,
character, and theme-based searches.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import storySearch


class TestStorySearch(unittest.TestCase):
    """Test suite for StorySearch class."""

    def setUp(self):
        """Set up test environment."""
        self.search_engine = storySearch.StorySearch(
            data_source=[
                {
                    "title": "Dragon Hunt",
                    "text": "A dragon threatens the valley.",
                    "characters": ["Gandalf", "Bilbo"],
                    "themes": ["adventure", "fantasy"],
                },
                {
                    "title": "Quiet Village",
                    "text": "A peaceful story about farming.",
                    "characters": ["Sam"],
                    "themes": ["slice of life"],
                },
            ]
        )

    def test_story_search_initialization(self):
        """Test StorySearch initialization."""
        # Test default initialization
        search_engine = storySearch.StorySearch()
        self.assertIsInstance(search_engine, storySearch.StorySearch)

        # Test initialization with data source
        search_engine_with_source = storySearch.StorySearch(data_source="test_data.csv")
        self.assertIsInstance(search_engine_with_source, storySearch.StorySearch)

    def test_find_by_keyword(self):
        """Test keyword search functionality."""
        result = self.search_engine.find_by_keyword("dragon")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Dragon Hunt")

    def test_find_by_character(self):
        """Test character search functionality."""
        result = self.search_engine.find_by_character("Gandalf")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Dragon Hunt")

    def test_find_by_theme(self):
        """Test theme search functionality."""
        result = self.search_engine.find_by_theme("adventure")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Dragon Hunt")

    def test_load_stories_method_exists(self):
        """Test that _load_stories method exists."""
        self.assertTrue(hasattr(self.search_engine, "_load_stories"))
        self.assertTrue(callable(getattr(self.search_engine, "_load_stories")))

    def test_search_methods_exist(self):
        """Test that all search methods exist and are callable."""
        methods = ["find_by_keyword", "find_by_character", "find_by_theme"]

        for method_name in methods:
            with self.subTest(method=method_name):
                self.assertTrue(hasattr(self.search_engine, method_name))
                method = getattr(self.search_engine, method_name)
                self.assertTrue(callable(method))

    def test_search_with_empty_parameters(self):
        """Test search methods with empty parameters."""
        keyword_result = self.search_engine.find_by_keyword("")
        character_result = self.search_engine.find_by_character("")
        theme_result = self.search_engine.find_by_theme("")

        self.assertIsInstance(keyword_result, list)
        self.assertIsInstance(character_result, list)
        self.assertIsInstance(theme_result, list)

    def test_search_with_none_parameters(self):
        """Test search methods with None parameters."""
        keyword_result = self.search_engine.find_by_keyword(None)
        character_result = self.search_engine.find_by_character(None)
        theme_result = self.search_engine.find_by_theme(None)

        self.assertIsInstance(keyword_result, list)
        self.assertIsInstance(character_result, list)
        self.assertIsInstance(theme_result, list)

    def test_search_case_sensitivity(self):
        """Test search methods with different case inputs."""
        test_cases = [
            ("dragon", "Dragon", "DRAGON"),
            ("gandalf", "Gandalf", "GANDALF"),
            ("adventure", "Adventure", "ADVENTURE"),
        ]

        methods = [
            (self.search_engine.find_by_keyword, "keyword"),
            (self.search_engine.find_by_character, "character"),
            (self.search_engine.find_by_theme, "theme"),
        ]

        for i, (method, method_name) in enumerate(methods):
            test_inputs = test_cases[i]
            for test_input in test_inputs:
                with self.subTest(method=method_name, input=test_input):
                    result = method(test_input)
                    self.assertIsInstance(result, list)

    def test_load_stories_with_different_sources(self):
        """Test _load_stories with different data sources."""
        test_sources = ["test_file.csv", "test_file.json", None, {"stories": []}, []]

        for source in test_sources:
            with self.subTest(source=source):
                search_engine = storySearch.StorySearch(data_source=source)
                self.assertIsInstance(search_engine, storySearch.StorySearch)

    def test_module_structure(self):
        """Test that module has expected structure."""
        self.assertTrue(hasattr(storySearch, "StorySearch"))

        self.assertTrue(isinstance(storySearch.StorySearch, type))

    def test_example_usage_pattern(self):
        """The documented example usage should still produce list results."""
        # Create a new instance like in main
        search_engine = storySearch.StorySearch()

        keyword_stories = search_engine.find_by_keyword("dragon")
        character_stories = search_engine.find_by_character("Gandalf")
        theme_stories = search_engine.find_by_theme("adventure")

        self.assertIsInstance(keyword_stories, list)
        self.assertIsInstance(character_stories, list)
        self.assertIsInstance(theme_stories, list)

    def test_search_with_special_characters(self):
        """Test search methods with special characters."""
        special_inputs = [
            "test@example.com",
            "test-name",
            "test_name",
            "test.name",
            "test name",
            "test123",
            "test!@#$%",
        ]

        for special_input in special_inputs:
            with self.subTest(input=special_input):
                keyword_result = self.search_engine.find_by_keyword(special_input)
                character_result = self.search_engine.find_by_character(special_input)
                theme_result = self.search_engine.find_by_theme(special_input)

                self.assertIsInstance(keyword_result, list)
                self.assertIsInstance(character_result, list)
                self.assertIsInstance(theme_result, list)

    def test_search_performance_basic(self):
        """Test basic performance characteristics of search methods."""
        import time

        start_time = time.time()

        for i in range(10):
            self.search_engine.find_by_keyword(f"test_{i}")
            self.search_engine.find_by_character(f"character_{i}")
            self.search_engine.find_by_theme(f"theme_{i}")

        elapsed_time = time.time() - start_time

        self.assertLess(elapsed_time, 10.0, "Search operations took too long")


if __name__ == "__main__":
    unittest.main()
