import unittest
import tkinter as tk
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from gui import CrewGUI

class TestGUIPreprocessing(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during testing
        self.gui = CrewGUI(self.root)

    def tearDown(self):
        if self.root:
            self.root.destroy()

    def test_clean_text(self):
        text = "**bold** `code` normal"
        cleaned_text = self.gui._clean_text(text)
        self.assertEqual(cleaned_text, "bold code normal")

    def test_chunk_text(self):
        # Use a string with spaces so chunk_text splits on words as intended
        text = ("a " * 700).strip()  # 700 words, 1399 chars
        chunks = self.gui.chunk_text(text, max_length=600)
        # Each chunk should be less than or equal to 600 chars
        self.assertTrue(all(len(chunk) <= 600 for chunk in chunks))
        self.assertGreater(len(chunks), 1)
        self.assertEqual("".join(chunk.replace(" ","") for chunk in chunks), "a"*700)

    # def test_send_to_tts_engine(self):
    #     text = "Hello, this is a test."
    #     try:
    #         self.gui._send_to_tts_engine(text)
    #     except Exception as e:
    #         self.fail(f"_send_to_tts_engine raised an exception: {e}")

if __name__ == "__main__":
    unittest.main()