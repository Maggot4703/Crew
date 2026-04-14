#!/usr/bin/env python3
import pyttsx3
import unittest
import sys
from pathlib import Path
from unittest.mock import MagicMock
from tkinter import Tk

# Add project root to sys.path to allow importing gui module
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from gui import CrewGUI

class TestTTSFunctionality(unittest.TestCase):
    def setUp(self):
        self.engine = pyttsx3.init()

    def test_pause_resume(self):
        try:
            self.engine.pause = MagicMock()
            self.engine.resume = MagicMock()

            self.engine.pause()
            self.engine.resume()

            self.engine.pause.assert_called_once()
            self.engine.resume.assert_called_once()
        except Exception as e:
            self.fail(f"Pause/Resume functionality failed: {e}")

    def test_error_handling(self):
        try:
            self.engine.say = MagicMock(side_effect=Exception("Test error"))
            with self.assertRaises(Exception):
                self.engine.say("This should raise an error.")
        except Exception as e:
            self.fail(f"Error handling test failed: {e}")

=======
import sys
from pathlib import Path
from gui import CrewGUI
from tkinter import Tk

# Add project root to sys.path to allow importing gui module
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

try:
    import gui  # Assuming gui.py is in the project root
except ImportError as e:
    gui = None
    gui_import_error = e

class TestTTSFunctionality(unittest.TestCase):
    def setUp(self):
        self.engine = pyttsx3.init()

    def test_pause_resume(self):
        try:
            self.engine.pause = MagicMock()
            self.engine.resume = MagicMock()

            self.engine.pause()
            self.engine.resume()

            self.engine.pause.assert_called_once()
            self.engine.resume.assert_called_once()
        except Exception as e:
            self.fail(f"Pause/Resume functionality failed: {e}")

    def test_error_handling(self):
        try:
            self.engine.say = MagicMock(side_effect=Exception("Test error"))
            with self.assertRaises(Exception):
                self.engine.say("This should raise an error.")
        except Exception as e:
            self.fail(f"Error handling test failed: {e}")

    def test_clean_text(self):
        try:
            app = gui.CrewGUI(self.root)
            cleaned_text = app._clean_text("\nHello World\n")
            self.assertEqual(cleaned_text, "Hello World")
        except Exception as e:
            self.fail(f"Text preprocessing test failed: {e}")

    def test_tts_testing_feature(self):
        try:
            app = gui.CrewGUI(self.root)
            app.tts_engine = MagicMock()
            app.tts_engine.say = MagicMock()
            app.tts_engine.runAndWait = MagicMock()

            app._test_tts()

            app.tts_engine.say.assert_called_once_with("This is a test of the text-to-speech functionality.")
            app.tts_engine.runAndWait.assert_called_once()
        except Exception as e:
            self.fail(f"TTS testing feature test failed: {e}")

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

>>>>>>> chunk-playback
if __name__ == "__main__":
    print("Testing female voice...")
    engine = pyttsx3.init()

    # Get voice properties
    voices = engine.getProperty("voices")

    # Find an English voice
    english_voice = None
    for voice in voices:
        if "english" in voice.id.lower():
            english_voice = voice
            print(f"Found English voice: {voice.id}")
            break

    if english_voice:
        # Configure for female voice using espeak variant
        # In espeak, adding '+f3' to the voice ID makes it female
        fem_voice = english_voice.id + "+f3"
        engine.setProperty("voice", fem_voice)
        print(f"Set female voice: {fem_voice}")

        # Test the voice
        engine.say("This is a test of the female voice in text to speech.")
        print("Running engine...")
        engine.runAndWait()
    else:
        print("No English voice found")

    print("Test completed.")
    unittest.main()
