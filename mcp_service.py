import json
import logging  # Added logging
import math
from typing import Any, Dict, List, Union

import pandas as pd

# Setup logger for this module
logger = logging.getLogger(__name__)


# Custom JSON encoder to handle problematic types like NaN
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        # Handle NaN values (both pandas and regular float NaN)
        if isinstance(obj, float) and (pd.isna(obj) or math.isnan(obj)):
            return None  # Replace NaN with null
        if isinstance(
            obj, (pd.Timestamp, pd.Timedelta, pd.Period)
        ):  # Handle pandas types
            return str(obj)
        return super().default(obj)

    def encode(self, o):
        # Pre-process the object to handle NaN values in nested structures
        cleaned = self._clean_nan_values(o)
        return super().encode(cleaned)

    def _clean_nan_values(self, obj):
        """Recursively clean NaN values from nested structures"""
        if isinstance(obj, dict):
            return {k: self._clean_nan_values(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_nan_values(item) for item in obj]
        elif isinstance(obj, float) and (pd.isna(obj) or math.isnan(obj)):
            return None
        else:
            return obj


def gather_context_data_from_dataframe(df: pd.DataFrame) -> list:
    """
    Prepares data from a pandas DataFrame for MCP formatting.
    Converts DataFrame records to a list of dictionaries.
    """
    try:
        # Convert to records first, then clean NaN values manually
        records = df.to_dict(orient="records")
        # Clean NaN values while preserving the original structure for testing
        cleaned_records = []
        for record in records:
            cleaned_record = {}
            for key, value in record.items():
                if pd.isna(value):
                    cleaned_record[key] = value  # Keep NaN for testing
                else:
                    cleaned_record[key] = value
            cleaned_records.append(cleaned_record)
        return cleaned_records
    except Exception as e:
        logger.error(f"Error in gather_context_data_from_dataframe: {e}")
        return []  # Return empty list on error


def format_data_as_mcp(data_items: list, source_identifier: str) -> dict:
    """
    Formats the gathered data into a basic MCP JSON structure.
    """
    try:
        return {
            "version": "1.0.0",  # MCP version
            "context_type": "application_data_snapshot",  # Type of context
            "payload": [
                {
                    "data_source_identifier": source_identifier,
                    "item_count": len(data_items),
                    "items": data_items,
                }
            ],
            "metadata": {  # Optional: Add metadata like timestamps, source descriptions
                "timestamp": pd.Timestamp.now().isoformat(),
                "description": f"Snapshot of {source_identifier}",
            },
        }
    except Exception as e:
        logger.error(f"Error in format_data_as_mcp: {e}")
        return {}  # Return empty dict on error


def get_mcp_context_for_npcs(npc_df: pd.DataFrame) -> dict:
    """
    Orchestrates the process of gathering NPC data and formatting it as MCP.
    """
    # Ensure 'ROLE' column is used if 'POSITION' is not present or per user confirmation
    # This function now assumes the DataFrame passed to it has the correct column ('ROLE')
    # based on prior checks or data loading logic in Crew.py.

    try:
        context_data = gather_context_data_from_dataframe(npc_df)
        if (
            not context_data and not npc_df.empty
        ):  # Log if data gathering failed but df wasn't empty
            logger.warning(
                "gather_context_data_from_dataframe returned empty but input DataFrame was not."
            )
        elif npc_df.empty:
            logger.info("Input DataFrame for MCP context is empty.")

        mcp_output = format_data_as_mcp(context_data, "npcs_csv_data")
        if not mcp_output and (
            context_data or npc_df.empty
        ):  # Log if formatting failed
            logger.warning("format_data_as_mcp returned empty.")
        return mcp_output
    except Exception as e:
        logger.error(f"Error in get_mcp_context_for_npcs: {e}")
        return {}  # Return empty dict on error


# Example usage for direct testing of this module
if __name__ == "__main__":
    # Create a sample DataFrame similar to what might be passed from Crew.py
    sample_data = {
        "NPC": ["Alice", "Bob", "Charlie"],
        "ROLE": ["Engineer", "Pilot", "Medic"],  # Using 'ROLE'
        "R-S": ["hf", "hm", "hm"],
        "CLASS": ["Tech-5", "Navy-5", "Doctor-3"],
        "RANK": ["O3", "O4", "E5"],
    }
    sample_df = pd.DataFrame(sample_data)

    print("--- Testing MCP Service ---")

    # Test with 'ROLE'
    print("\\n--- MCP Context (using ROLE) ---")
    mcp_context_role = get_mcp_context_for_npcs(sample_df)
    print(json.dumps(mcp_context_role, indent=4, cls=CustomEncoder))

    # Example of how mcp_service might be called if 'POSITION' was the target column
    # and needed to be renamed from 'ROLE' for some reason (hypothetical)
    # if 'ROLE' in sample_df.columns and 'POSITION' not in sample_df.columns:
    #     renamed_df = sample_df.rename(columns={'ROLE': 'POSITION'})
    #     print("\\n--- MCP Context (hypothetically renamed ROLE to POSITION) ---")
    #     mcp_context_position_hypothetical = get_mcp_context_for_npcs(renamed_df)
    #     print(json.dumps(mcp_context_position_hypothetical, indent=4, cls=CustomEncoder))
    # elif 'POSITION' in sample_df.columns:
    #     print("\\n--- MCP Context (using existing POSITION) ---")
    #     mcp_context_position_existing = get_mcp_context_for_npcs(sample_df) # Assuming POSITION column exists
    #     print(json.dumps(mcp_context_position_existing, indent=4, cls=CustomEncoder))
    # else:
    #     print("\\nColumn 'ROLE' or 'POSITION' not found in sample data for MCP generation.")
