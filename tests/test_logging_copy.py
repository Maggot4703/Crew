
import os
import pytest
from unittest import mock
from Crew import log_progress_md

# Test log_progress_md by patching open and checking file writes

def test_log_progress_md_appends(monkeypatch, tmp_path):
    log_file = tmp_path / "progress.md"
    messages = []
    def fake_open(file, mode, encoding=None):
        class DummyFile:
            def write(self, entry):
                messages.append(entry)
            def __enter__(self): return self
            def __exit__(self, *a): pass
        assert "a" in mode
        return DummyFile()
    monkeypatch.setattr("builtins.open", fake_open)
    log_progress_md("Test message 1")
    log_progress_md("Test message 2")
    assert any("Test message 1" in m for m in messages)
    assert any("Test message 2" in m for m in messages)
    assert all("###" in m for m in messages)  # Timestamp header present

# Test error handling (simulate file write error)
def test_log_progress_md_error(monkeypatch):
    def fake_open(*a, **kw):
        raise IOError("fail")
    monkeypatch.setattr("builtins.open", fake_open)
    with mock.patch("Crew.Crew.logger") as logger:
        log_progress_md("Should fail")
        logger.error.assert_called()
