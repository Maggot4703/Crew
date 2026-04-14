"""
Test suite for TTSManager module (tts_manager.py).
Covers initialization, speech, and settings management.
"""

import unittest
from tts_manager import TTSManager

class TestTTSManager(unittest.TestCase):
    def setUp(self):
        self.manager = TTSManager()

    def test_is_available(self):
        # is_available is a property, not a method
        self.assertIsInstance(self.manager.is_available, bool)

    def test_speak_text(self):
        # Should not raise error (actual speech may not be testable in CI)
        try:
            self.manager.speak_text("Hello", background=True)
        except Exception as e:
            self.fail(f"speak_text() raised {e}")

    # Add more tests for pause, resume, stop, and settings as needed

if __name__ == "__main__":
    unittest.main()
