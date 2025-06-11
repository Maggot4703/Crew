#!/usr/bin/python3
"""
Test module for cache functionality.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

import shutil
import time
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open

from cache import Cache
from Crew import get_version
from errors import ConfigError


class TestCache(unittest.TestCase):
    """Test suite for Cache class."""

    def setUp(self):
        """Set up test environment."""
        self.test_cache_dir = tempfile.mkdtemp()
        self.cache = Cache(cache_dir=self.test_cache_dir)

    def tearDown(self):
        """Clean up test environment."""
        if Path(self.test_cache_dir).exists():
            shutil.rmtree(self.test_cache_dir)

    def test_cache_initialization(self):
        """Test cache initialization creates directory."""
        self.assertTrue(Path(self.test_cache_dir).exists())
        self.assertTrue(Path(self.test_cache_dir).is_dir())
        self.assertEqual(self.cache.cache_dir, Path(self.test_cache_dir))
        self.assertIsInstance(self.cache.cache, dict)
        self.assertIsInstance(self.cache.ttl, dict)
        self.assertIsInstance(self.cache.default_ttl, timedelta)

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        test_key = "test_key"
        test_value = {"data": "test_value", "number": 42}

        # Set value
        self.cache.set(test_key, test_value)

        # Get value
        retrieved_value = self.cache.get(test_key)
        self.assertEqual(retrieved_value, test_value)

    def test_cache_get_nonexistent_key(self):
        """Test getting non-existent cache key returns None."""
        result = self.cache.get("nonexistent_key")
        self.assertIsNone(result)

    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration."""
        test_key = "expiring_key"
        test_value = "expiring_value"
        short_ttl = timedelta(milliseconds=100)

        # Set with short TTL
        self.cache.set(test_key, test_value, ttl=short_ttl)

        # Should be available immediately
        self.assertEqual(self.cache.get(test_key), test_value)

        # Wait for expiration
        time.sleep(0.2)

        # Should be None after expiration
        self.assertIsNone(self.cache.get(test_key))

    def test_cache_persistence(self):
        """Test cache persistence to file."""
        test_key = "persistent_key"
        test_value = "persistent_value"

        # Set value and persist
        self.cache.set(test_key, test_value)
        self.cache.save()

        # Create new cache instance and load
        new_cache = Cache(cache_dir=self.test_cache_dir)
        new_cache.load()

        # Check if the value is the same
        self.assertEqual(new_cache.get(test_key), test_value)

    def test_cache_error_handling(self):
        """Test cache error handling for invalid JSON."""
        test_key = "invalid_json_key"
        invalid_json_value = "{this is: 'not a valid' json}"

        # Set invalid JSON value
        self.cache.set(test_key, invalid_json_value)
        self.cache.save()

        # Create new cache instance and load
        new_cache = Cache(cache_dir=self.test_cache_dir)

        # Loading should not raise an exception
        try:
            new_cache.load()
        except Exception as e:
            self.fail(f"Loading cache with invalid JSON raised an exception: {e}")

        # The value should be retrievable, albeit as a string
        self.assertEqual(new_cache.get(test_key), invalid_json_value)

    def test_cache_custom_ttl(self):
        """Test cache with custom TTL."""
        test_key = "custom_ttl_key"
        test_value = "custom_ttl_value"
        custom_ttl = timedelta(hours=1)

        self.cache.set(test_key, test_value, ttl=custom_ttl)

        # Check TTL is set correctly
        expected_expiry = datetime.now() + custom_ttl
        actual_expiry = self.cache.ttl[test_key]

        # Allow for small time differences
        self.assertAlmostEqual(
            expected_expiry.timestamp(),
            actual_expiry.timestamp(),
            delta=1,  # 1 second tolerance
        )

    def test_cache_invalidate(self):
        """Test cache invalidation."""
        test_key = "invalidate_key"
        test_value = "invalidate_value"

        # Set and verify
        self.cache.set(test_key, test_value)
        self.assertEqual(self.cache.get(test_key), test_value)

        # Invalidate
        self.cache.invalidate(test_key)

        # Should be None after invalidation
        self.assertIsNone(self.cache.get(test_key))
        self.assertNotIn(test_key, self.cache.cache)
        self.assertNotIn(test_key, self.cache.ttl)

    def test_cache_clear_all(self):
        """Test clearing all cache items."""
        # Set multiple items
        for i in range(3):
            self.cache.set(f"key_{i}", f"value_{i}")

        # Verify items exist
        for i in range(3):
            self.assertEqual(self.cache.get(f"key_{i}"), f"value_{i}")

        # Clear all
        self.cache.clear()

        # Verify all items are gone
        for i in range(3):
            self.assertIsNone(self.cache.get(f"key_{i}"))

        self.assertEqual(len(self.cache.cache), 0)
        self.assertEqual(len(self.cache.ttl), 0)

    def test_cache_clear_specific_key(self):
        """Test clearing specific cache key."""
        # Set multiple items
        self.cache.set("keep_key", "keep_value")
        self.cache.set("remove_key", "remove_value")

        # Clear specific key
        self.cache.clear("remove_key")

        # Verify correct item removed
        self.assertEqual(self.cache.get("keep_key"), "keep_value")
        self.assertIsNone(self.cache.get("remove_key"))

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_save_to_disk_success(self, mock_json_dump, mock_file):
        """Test successful saving to disk."""
        test_key = "disk_key"
        test_value = "disk_value"

        self.cache.set(test_key, test_value)

        # Verify file operations
        expected_file = Path(self.test_cache_dir) / f"{test_key}.cache"
        mock_file.assert_called_with(expected_file, "w")
        mock_json_dump.assert_called_once()

    def test_cache_data_types(self):
        """Test caching various data types."""
        test_cases = [
            ("string", "hello world"),
            ("integer", 42),
            ("float", 3.14),
            ("list", [1, 2, 3, "four"]),
            ("dict", {"key": "value", "nested": {"a": 1}}),
            ("tuple", (1, 2, 3)),
            ("boolean", True),
            ("none", None),
        ]

        for key, value in test_cases:
            with self.subTest(key=key, value=value):
                self.cache.set(key, value)
                retrieved = self.cache.get(key)
                self.assertEqual(retrieved, value)

    def test_default_ttl_used(self):
        """Test that default TTL is used when not specified."""
        test_key = "default_ttl_key"
        test_value = "default_ttl_value"

        self.cache.set(test_key, test_value)

        # Check TTL is approximately default
        expected_expiry = datetime.now() + self.cache.default_ttl
        actual_expiry = self.cache.ttl[test_key]

        self.assertAlmostEqual(
            expected_expiry.timestamp(),
            actual_expiry.timestamp(),
            delta=1,  # 1 second tolerance
        )


if __name__ == "__main__":
    unittest.main()
