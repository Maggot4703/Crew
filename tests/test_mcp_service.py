"""
Test module for mcp_service.py

This module tests the Model Context Protocol (MCP) service functionality
including data gathering from DataFrames, MCP formatting, and JSON encoding.
"""

import json
import os
import sys
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

# Add the parent directory to the path to import the module under test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_service import (
    CustomEncoder,
    format_data_as_mcp,
    gather_context_data_from_dataframe,
    get_mcp_context_for_npcs,
)


class TestCustomEncoder(unittest.TestCase):
    """Test the CustomEncoder class for JSON serialization."""

    def setUp(self):
        """Set up test fixtures."""
        self.encoder = CustomEncoder()

    def test_encode_nan_values(self):
        """Test that NaN values are handled properly in JSON."""
        data = {"value": float("nan")}
        result = json.dumps(data, cls=CustomEncoder)
        parsed = json.loads(result)
        # NaN should be converted to None by CustomEncoder
        self.assertIsNone(parsed["value"])

    def test_encode_pandas_timestamp(self):
        """Test that pandas Timestamp objects are converted to strings."""
        timestamp = pd.Timestamp("2024-01-01 12:00:00")
        data = {"timestamp": timestamp}
        result = json.dumps(data, cls=CustomEncoder)
        parsed = json.loads(result)
        self.assertIsInstance(parsed["timestamp"], str)
        self.assertIn("2024-01-01", parsed["timestamp"])

    def test_encode_pandas_timedelta(self):
        """Test that pandas Timedelta objects are converted to strings."""
        timedelta = pd.Timedelta(days=1, hours=2)
        data = {"duration": timedelta}
        result = json.dumps(data, cls=CustomEncoder)
        parsed = json.loads(result)
        self.assertIsInstance(parsed["duration"], str)

    def test_encode_regular_values(self):
        """Test that regular values are encoded normally."""
        data = {
            "string": "test",
            "number": 42,
            "boolean": True,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
        }
        result = json.dumps(data, cls=CustomEncoder)
        parsed = json.loads(result)
        self.assertEqual(parsed, data)

    def test_nested_nan_handling(self):
        """Test NaN handling in nested structures."""
        data = {
            "level1": {"level2": {"nan_value": float("nan"), "normal_value": 42}},
            "list_with_nan": [1, float("nan"), 3],
        }

        json_str = json.dumps(data, cls=CustomEncoder)
        parsed = json.loads(json_str)

        self.assertIsNone(parsed["level1"]["level2"]["nan_value"])
        self.assertEqual(parsed["level1"]["level2"]["normal_value"], 42)
        self.assertIsNone(parsed["list_with_nan"][1])

    def test_multiple_pandas_types(self):
        """Test encoding of multiple pandas-specific types."""
        data = {
            "timestamp": pd.Timestamp("2024-01-01 12:00:00"),
            "timedelta": pd.Timedelta(days=5, hours=3),
            "period": pd.Period("2024-01"),
            "nan": float("nan"),
            "regular": "normal_string",
        }

        json_str = json.dumps(data, cls=CustomEncoder)
        parsed = json.loads(json_str)

        self.assertIsInstance(parsed["timestamp"], str)
        self.assertIsInstance(parsed["timedelta"], str)
        self.assertIsInstance(parsed["period"], str)
        self.assertIsNone(parsed["nan"])
        self.assertEqual(parsed["regular"], "normal_string")

    def test_encoder_with_complex_dataframe_output(self):
        """Test encoder with complex DataFrame conversion output."""
        # Create DataFrame with various pandas types
        df = pd.DataFrame(
            {
                "name": ["Alice", "Bob"],
                "start_date": [pd.Timestamp("2020-01-01"), pd.Timestamp("2021-01-01")],
                "duration": [pd.Timedelta(days=100), pd.Timedelta(days=200)],
                "score": [95.5, np.nan],
            }
        )

        # Convert to dict (simulating gather_context_data_from_dataframe)
        dict_data = df.to_dict(orient="records")

        # Encode with CustomEncoder
        json_str = json.dumps(dict_data, cls=CustomEncoder)
        parsed = json.loads(json_str)

        self.assertEqual(len(parsed), 2)
        self.assertIsInstance(parsed[0]["start_date"], str)
        self.assertIsInstance(parsed[0]["duration"], str)
        self.assertIsNone(parsed[1]["score"])  # NaN becomes None


class TestGatherContextDataFromDataFrame(unittest.TestCase):
    """Test the gather_context_data_from_dataframe function."""

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame()
        result = gather_context_data_from_dataframe(df)
        self.assertEqual(result, [])

    def test_normal_dataframe(self):
        """Test with normal DataFrame containing various data types."""
        data = {
            "NPC": ["Alice", "Bob", "Charlie"],
            "ROLE": ["Engineer", "Pilot", "Medic"],
            "AGE": [25, 30, 35],
            "ACTIVE": [True, False, True],
        }
        df = pd.DataFrame(data)
        result = gather_context_data_from_dataframe(df)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["NPC"], "Alice")
        self.assertEqual(result[0]["ROLE"], "Engineer")
        self.assertEqual(result[1]["AGE"], 30)
        self.assertFalse(result[1]["ACTIVE"])

    def test_dataframe_with_nan_values(self):
        """Test DataFrame containing NaN values."""
        data = {
            "NPC": ["Alice", "Bob"],
            "ROLE": ["Engineer", np.nan],
            "AGE": [25, None],
        }
        df = pd.DataFrame(data)
        result = gather_context_data_from_dataframe(df)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["NPC"], "Alice")
        self.assertTrue(pd.isna(result[1]["ROLE"]))

    @patch("mcp_service.logger")
    def test_dataframe_processing_error(self, mock_logger):
        """Test error handling during DataFrame processing."""
        # Create a mock DataFrame that raises an exception on to_dict
        mock_df = MagicMock()
        mock_df.to_dict.side_effect = Exception("Processing error")

        result = gather_context_data_from_dataframe(mock_df)

        self.assertEqual(result, [])
        mock_logger.error.assert_called_once()


class TestFormatDataAsMcp(unittest.TestCase):
    """Test the format_data_as_mcp function."""

    def test_empty_data_list(self):
        """Test with empty data list."""
        result = format_data_as_mcp([], "test_source")

        self.assertEqual(result["version"], "1.0.0")
        self.assertEqual(result["context_type"], "application_data_snapshot")
        self.assertEqual(result["payload"][0]["data_source_identifier"], "test_source")
        self.assertEqual(result["payload"][0]["item_count"], 0)
        self.assertEqual(result["payload"][0]["items"], [])

    def test_normal_data_list(self):
        """Test with normal data list."""
        data_items = [
            {"NPC": "Alice", "ROLE": "Engineer"},
            {"NPC": "Bob", "ROLE": "Pilot"},
        ]
        result = format_data_as_mcp(data_items, "npcs_data")

        self.assertEqual(result["version"], "1.0.0")
        self.assertEqual(result["payload"][0]["item_count"], 2)
        self.assertEqual(result["payload"][0]["items"], data_items)

    @patch("mcp_service.logger")
    def test_formatting_error(self, mock_logger):
        """Test error handling during MCP formatting."""
        # Force an error by patching pd.Timestamp.now()
        with patch("pandas.Timestamp.now", side_effect=Exception("Timestamp error")):
            result = format_data_as_mcp([{"test": "data"}], "test_source")

            self.assertEqual(result, {})
            mock_logger.error.assert_called_once()


class TestGetMcpContextForNpcs(unittest.TestCase):
    """Test the get_mcp_context_for_npcs function."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_npc_data = {
            "NPC": ["Alice", "Bob", "Charlie"],
            "ROLE": ["Engineer", "Pilot", "Medic"],
            "CLASS": ["Tech-5", "Navy-5", "Doctor-3"],
        }
        self.sample_df = pd.DataFrame(self.sample_npc_data)

    def test_normal_npc_dataframe(self):
        """Test with normal NPC DataFrame."""
        result = get_mcp_context_for_npcs(self.sample_df)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["version"], "1.0.0")
        self.assertEqual(result["payload"][0]["item_count"], 3)

        items = result["payload"][0]["items"]
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]["NPC"], "Alice")

    def test_empty_npc_dataframe(self):
        """Test with empty NPC DataFrame."""
        empty_df = pd.DataFrame()
        result = get_mcp_context_for_npcs(empty_df)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["payload"][0]["item_count"], 0)

    @patch("mcp_service.gather_context_data_from_dataframe")
    @patch("mcp_service.logger")
    def test_error_handling(self, mock_logger, mock_gather):
        """Test error handling in get_mcp_context_for_npcs."""
        # Mock gather_context_data_from_dataframe to return empty list
        mock_gather.return_value = []

        mock_df = MagicMock()
        mock_df.empty = False

        result = get_mcp_context_for_npcs(mock_df)

        # Should return a valid MCP structure with empty payload when gather fails
        self.assertIsInstance(result, dict)
        self.assertEqual(result["payload"][0]["item_count"], 0)
        self.assertEqual(result["payload"][0]["items"], [])


class TestMcpServiceIntegration(unittest.TestCase):
    """Integration tests for the MCP service module."""

    def test_end_to_end_workflow(self):
        """Test complete workflow from DataFrame to MCP JSON."""
        # Create test data
        npc_data = {
            "NPC": ["Test Engineer", "Test Pilot"],
            "ROLE": ["Engineer", "Pilot"],
            "AGE": [25, np.nan],  # Include NaN to test encoding
            "TIMESTAMP": [pd.Timestamp.now(), pd.Timestamp.now()],
        }
        df = pd.DataFrame(npc_data)

        # Process through complete workflow
        result = get_mcp_context_for_npcs(df)

        # Verify structure
        self.assertIsInstance(result, dict)
        self.assertIn("version", result)
        self.assertIn("payload", result)
        self.assertIn("metadata", result)

        # Verify data integrity
        items = result["payload"][0]["items"]
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["NPC"], "Test Engineer")

        # Verify JSON serialization works
        json_str = json.dumps(result, cls=CustomEncoder)
        self.assertIsInstance(json_str, str)

    def test_performance_with_large_dataset(self):
        """Test performance with larger dataset."""
        # Create larger dataset
        large_data = {
            "NPC": [f"NPC_{i}" for i in range(1000)],
            "ROLE": ["Engineer"] * 500 + ["Pilot"] * 500,
            "AGE": list(range(20, 70)) * 20,  # Cycle through ages
        }
        large_df = pd.DataFrame(large_data)

        # Process should complete without issues
        result = get_mcp_context_for_npcs(large_df)

        self.assertEqual(result["payload"][0]["item_count"], 1000)
        self.assertEqual(len(result["payload"][0]["items"]), 1000)

    def test_data_type_preservation(self):
        """Test that various data types are preserved through the workflow."""
        mixed_data = {
            "NPC": ["Alice", "Bob"],
            "ROLE": ["Engineer", "Pilot"],
            "AGE": [25, 30],
            "ACTIVE": [True, False],
            "SALARY": [50000.50, 75000.75],
            "START_DATE": [pd.Timestamp("2020-01-01"), pd.Timestamp("2021-06-15")],
        }
        df = pd.DataFrame(mixed_data)

        result = get_mcp_context_for_npcs(df)
        items = result["payload"][0]["items"]

        # Verify data types are handled properly
        self.assertEqual(items[0]["NPC"], "Alice")
        self.assertEqual(items[0]["AGE"], 25)
        self.assertTrue(items[0]["ACTIVE"])
        self.assertEqual(items[0]["SALARY"], 50000.50)

    def test_metadata_completeness(self):
        """Test that metadata is complete and properly formatted."""
        df = pd.DataFrame({"NPC": ["Test"], "ROLE": ["Tester"]})
        result = get_mcp_context_for_npcs(df)

        metadata = result["metadata"]
        self.assertIn("timestamp", metadata)
        self.assertIn("description", metadata)

        # Timestamp should be ISO format
        timestamp = metadata["timestamp"]
        self.assertIsInstance(timestamp, str)
        self.assertIn("T", timestamp)  # ISO format contains 'T'

        # Description should contain source identifier
        self.assertIn("npcs_csv_data", metadata["description"])
