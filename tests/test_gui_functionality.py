import unittest
from gui import GUI

class TestGUIPreprocessing(unittest.TestCase):
    def setUp(self):
        self.gui = GUI()

    def test_clean_text(self):
        text = "**bold** `code` normal"
        cleaned_text = self.gui._clean_text(text)
        self.assertEqual(cleaned_text, "bold code normal")

    def test_chunk_text(self):
        text = "a" * 1200
        chunks = self.gui._chunk_text(text, chunk_size=500)
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0], "a" * 500)
        self.assertEqual(chunks[1], "a" * 500)
        self.assertEqual(chunks[2], "a" * 200)

    def test_send_to_tts_engine(self):
        text = "Hello, this is a test."
        try:
            self.gui._send_to_tts_engine(text)
        except Exception as e:
            self.fail(f"_send_to_tts_engine raised an exception: {e}")

if __name__ == "__main__":
    unittest.main()