import unittest
from gui import CrewGUI
from tkinter import Tk

class TestTTS(unittest.TestCase):

    def setUp(self):
        self.root = Tk()
        self.gui = CrewGUI(self.root)

    def test_read_status(self):
        try:
            self.gui.status_var.set("Test status message")
            self.gui._read_status()
        except Exception as e:
            self.fail(f"_read_status raised an exception: {e}")

    def test_read_all_details(self):
        try:
            self.gui.details_text = Tk.Text(self.root)
            self.gui.details_text.insert("1.0", "Test details message")
            self.gui._read_all_details()
        except Exception as e:
            self.fail(f"_read_all_details raised an exception: {e}")

    def test_read_filter_text(self):
        try:
            self.gui.filter_var = Tk.StringVar(value="Test filter message")
            self.gui._read_filter_text()
        except Exception as e:
            self.fail(f"_read_filter_text raised an exception: {e}")

    def test_show_speech_settings(self):
        try:
            self.gui._show_speech_settings()
        except Exception as e:
            self.fail(f"_show_speech_settings raised an exception: {e}")

if __name__ == "__main__":
    unittest.main()