"""
Unit tests for Crew GUI recording menu and recording logic.
Covers:
- Menu presence
- Start/stop recording logic (with device and process mocks)
- Play/save recording error handling
"""

import os
import sys
import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from gui import CrewGUI


class TestGUIRecordMenu(unittest.TestCase):
    def _find_widgets_by_type(self, root_widget, widget_types):
        found = []
        for child in root_widget.winfo_children():
            if isinstance(child, widget_types):
                found.append(child)
            found.extend(self._find_widgets_by_type(child, widget_types))
        return found

    def test_crew_chat_window_buttons(self):
        """Test that Crew Chat window contains the 5-button interface with correct labels and tooltips."""
        chat_win = self.gui.open_crew_chat_window()
        self.assertIsNotNone(chat_win, "open_crew_chat_window() returned None")
        if chat_win is not None:
            buttons = self._find_widgets_by_type(chat_win, (tk.Button, tk.Checkbutton))
            button_labels = [b.cget("text") for b in buttons]
            expected_labels = {"SET", "START/STOP", "SAVE/LOAD", "Rec/Play", "?"}
            found_labels = set(button_labels)
            self.assertTrue(
                expected_labels.issubset(found_labels),
                f"Missing chat control buttons: {expected_labels - found_labels}",
            )
            for b in buttons:
                tooltip = getattr(b, "tooltip", None)
                self.assertIsNotNone(
                    tooltip, f"Button '{b.cget('text')}' missing tooltip"
                )

    def test_chatbot_dialog_buttons(self):
        """Test that Chatbot dialog contains the 5-button interface with correct labels and tooltips."""
        dialog = self.gui.open_chatbot_dialog()
        self.assertIsNotNone(dialog, "open_chatbot_dialog() returned None")
        if dialog is not None:
            buttons = self._find_widgets_by_type(dialog, (tk.Button, tk.Checkbutton))
            button_labels = [b.cget("text") for b in buttons]
            expected_labels = {"SET", "START/STOP", "SAVE/LOAD", "Rec/Play", "?"}
            found_labels = set(button_labels)
            self.assertTrue(
                expected_labels.issubset(found_labels),
                f"Missing chatbot control buttons: {expected_labels - found_labels}",
            )
            for b in buttons:
                tooltip = getattr(b, "tooltip", None)
                self.assertIsNotNone(
                    tooltip, f"Button '{b.cget('text')}' missing tooltip"
                )

    def test_unified_menu_structure(self):
        """Test that the unified 'Talk' and 'Chat' menus are present in the menu bar."""
        menu_labels = []
        for i in range(self.gui.menu_bar.index("end") + 1):
            menu_labels.append(self.gui.menu_bar.entryconfigure(i)["label"][-1])
        # Accept both with and without emoji for 'Talk' menu
        talk_labels = [lbl for lbl in menu_labels if "Talk" in lbl]
        chat_labels = [lbl for lbl in menu_labels if "Chat" in lbl]
        self.assertTrue(talk_labels, "'Talk' menu not found in menu bar.")
        self.assertTrue(chat_labels, "'Chat' menu not found in menu bar.")

    def test_chatbot_send_updates_history(self):
        """Sending a chatbot message should append both user and bot output."""
        dialog = self.gui.open_chatbot_dialog()
        dialog.user_entry.insert(0, "/about")
        dialog.send_button.invoke()
        dialog.update()
        dialog.after(100)
        dialog.update()
        text = dialog.chat_display.get("1.0", tk.END)
        self.assertIn("You: /about", text)
        self.assertIn("Bot:", text)

    def test_tts_voice_profiles_include_language_details(self):
        class DummyVoice:
            def __init__(self, voice_id, name, languages):
                self.id = voice_id
                self.name = name
                self.languages = languages

        voices = [DummyVoice("voice-f1", "English Female", [b"\x05en-us"])]
        self.gui.tts_engine = MagicMock()
        self.gui.tts_engine.getProperty.side_effect = lambda key: (
            voices if key == "voices" else None
        )

        profiles = self.gui._get_tts_voice_profiles()

        self.assertEqual(profiles[0]["id"], "voice-f1")
        self.assertEqual(profiles[0]["gender"], "female")
        self.assertIn("en-us", profiles[0]["label"].lower())

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.gui = CrewGUI(self.root)

    def tearDown(self):
        if self.root:
            self.root.destroy()

    def test_record_menu_exists(self):
        found = False
        for i in range(self.gui.menu_bar.index("end") + 1):
            try:
                menu_ref = self.gui.menu_bar.entrycget(i, "menu")
                if menu_ref:
                    submenu = self.gui.menu_bar.nametowidget(menu_ref)
                    # Check if this is the record menu by checking for a known entry label
                    for j in range(submenu.index("end") + 1):
                        entry_label = submenu.entrycget(j, "label")
                        if entry_label and "Start Recording" in entry_label:
                            found = True
                            break
                if found:
                    break
            except Exception:
                continue
        self.assertTrue(found, "Record menu not found in menu bar.")

    def test_start_stop_recording(self):
        # Patch audio_manager, pyaudio, and speech_recognition to simulate device lookup and recording
        with patch("audio_manager.start_recording") as mock_start_recording, patch(
            "audio_manager.stop_recording"
        ) as mock_stop_recording, patch("pyaudio.PyAudio") as mock_pyaudio, patch(
            "speech_recognition.Microphone.list_microphone_names"
        ) as mock_list_mics:
            # Setup mocks for device lookup
            mock_proc = MagicMock()
            mock_path = "/tmp/fake_recording.wav"
            mock_start_recording.return_value = (mock_path, mock_proc)
            mock_stop_recording.return_value = None
            mock_list_mics.return_value = ["Fake Mic"]
            mock_pa_instance = MagicMock()
            mock_pyaudio.return_value = mock_pa_instance
            mock_pa_instance.get_device_count.return_value = 1
            mock_pa_instance.get_device_info_by_index.return_value = {
                "name": "Fake Mic",
                "maxInputChannels": 1,
                "defaultSampleRate": 16000,
            }
            # Patch menu entryconfig and update_status to avoid GUI dependencies
            self.gui._record_menu = MagicMock()
            self.gui._record_menu.entryconfig.return_value = None
            self.gui.update_status = MagicMock()
            # Patch messagebox to avoid GUI popups
            with patch("tkinter.messagebox.showerror"), patch(
                "tkinter.messagebox.showwarning"
            ):
                # Directly call the new testable method
                self.gui._start_recording_with_device("Fake Mic")
                self.assertIsNotNone(self.gui._recording_process)
                self.gui._stop_recording()
                self.assertIsNone(self.gui._recording_process)

    def test_play_recording_no_file(self):
        self.gui._last_recording_path = None
        with patch("os.path.exists", return_value=False):
            with patch.object(self.gui, "update_status") as mock_status:
                self.gui._play_recording()
                mock_status.assert_called_with(
                    "No recording available to play.", error=True
                )

    def test_save_recording_no_file(self):
        self.gui._last_recording_path = None
        with patch("os.path.exists", return_value=False):
            with patch.object(self.gui, "update_status") as mock_status:
                self.gui._save_recording_as()
                mock_status.assert_called_with(
                    "No recording available to save.", error=True
                )


if __name__ == "__main__":
    unittest.main()
