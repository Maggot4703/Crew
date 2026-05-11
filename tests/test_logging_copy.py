import logging
import os
from unittest import mock

import pytest

from Crew import log_progress_md
from utils import logger

# Test log_progress_md by checking the logger is called


def test_log_progress_md_appends(caplog):
    """Test that log_progress_md logs to the logger."""
    with caplog.at_level(logging.INFO):
        log_progress_md("Test message 1")
        log_progress_md("Test message 2")

    # Check that both messages were logged
    assert any(
        "Test message 1" in record.message for record in caplog.records
    ), f"Records: {[r.message for r in caplog.records]}"
    assert any("Test message 2" in record.message for record in caplog.records)
    # Check that the [PROGRESS] prefix is added
    assert any("[PROGRESS]" in record.message for record in caplog.records)


# Test error handling
def test_log_progress_md_error():
    """Test that log_progress_md works without errors."""
    # Just verify it can be called without raising exceptions
    log_progress_md("Test message")
    log_progress_md("Another test")
