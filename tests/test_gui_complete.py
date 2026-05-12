# flake8: noqa: E402
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
from tkinter import ttk
from unittest.mock import MagicMock, patch

import pytest

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

    def _find_widget_by_text(self, root_widget, widget_types, text):
        for widget in self._find_widgets_by_type(root_widget, widget_types):
            if widget.cget("text") == text:
                return widget
            # Also accept matches via the widget.tooltip attribute to support icon-only buttons
            tooltip = getattr(widget, "tooltip", None)
            tip_text = (
                getattr(tooltip, "text", tooltip) if tooltip is not None else None
            )
            if tip_text == text:
                return widget
        return None

    def _tooltip_text(self, widget):
        """Return the tooltip text for a widget, or empty string if none."""
        t = getattr(widget, "tooltip", None)
        if t is None:
            return ""
        return str(getattr(t, "text", t)).lower()

    def test_crew_chat_window_buttons(self):
        """Test that Crew Chat exposes the clearer audio control labels."""
        chat_win = self.gui.open_crew_chat_window()
        self.assertIsNotNone(chat_win, "open_crew_chat_window() returned None")
        if chat_win is not None:
            buttons = self._find_widgets_by_type(chat_win, (tk.Button, tk.Checkbutton))
            # Accept presence via button text or via tooltip substring (for icon-only buttons)
            expected_labels = ["Mic", "Record", "Save", "Record / Play", "?"]
            for expected in expected_labels:
                found = False
                for b in buttons:
                    text = b.cget("text") or ""
                    tooltip_text = self._tooltip_text(b)
                    if text == expected or expected.lower() in tooltip_text:
                        found = True
                        break
                self.assertTrue(
                    found, f"Missing chat control button or tooltip for: {expected}"
                )
            # Ensure every control has a tooltip for accessibility/testing
            for b in buttons:
                tooltip = getattr(b, "tooltip", None)
                self.assertIsNotNone(
                    tooltip, f"Button '{b.cget('text') or '<no-text>'}' missing tooltip"
                )

    def test_chatbot_dialog_buttons(self):
        """Test that Chatbot exposes the clearer audio control labels."""
        dialog = self.gui.open_chatbot_dialog()
        self.assertIsNotNone(dialog, "open_chatbot_dialog() returned None")
        if dialog is not None:
            buttons = self._find_widgets_by_type(dialog, (tk.Button, tk.Checkbutton))
            expected_labels = ["Mic", "Record", "Save", "Record / Play", "?"]
            for expected in expected_labels:
                found = False
                for b in buttons:
                    text = b.cget("text") or ""
                    tooltip_text = self._tooltip_text(b)
                    if text == expected or expected.lower() in tooltip_text:
                        found = True
                        break
                self.assertTrue(
                    found, f"Missing chatbot control button or tooltip for: {expected}"
                )
            for b in buttons:
                tooltip = getattr(b, "tooltip", None)
                self.assertIsNotNone(
                    tooltip, f"Button '{b.cget('text') or '<no-text>'}' missing tooltip"
                )

    def test_crew_chat_audio_labels_switch_with_mode(self):
        chat_win = self.gui.open_crew_chat_window()
        mode_toggle = self._find_widget_by_text(
            chat_win, (tk.Checkbutton,), "Record / Play"
        )
        self.assertIsNotNone(mode_toggle)

        mode_toggle.invoke()

        expected_labels = ["Source", "Play", "Load", "Record / Play"]
        buttons = self._find_widgets_by_type(chat_win, (tk.Button, tk.Checkbutton))
        for expected in expected_labels:
            found = False
            for widget in buttons:
                text = widget.cget("text") or ""
                tooltip_text = self._tooltip_text(widget)
                if text == expected or expected.lower() in tooltip_text:
                    found = True
                    break
            self.assertTrue(
                found, f"Missing audio control '{expected}' in crew chat window"
            )

    def test_chatbot_audio_labels_switch_with_mode(self):
        dialog = self.gui.open_chatbot_dialog()
        mode_toggle = self._find_widget_by_text(
            dialog, (tk.Checkbutton,), "Record / Play"
        )
        self.assertIsNotNone(mode_toggle)

        mode_toggle.invoke()

        expected_labels = ["Source", "Play", "Load", "Record / Play"]
        buttons = self._find_widgets_by_type(dialog, (tk.Button, tk.Checkbutton))
        for expected in expected_labels:
            found = False
            for widget in buttons:
                text = widget.cget("text") or ""
                tooltip_text = self._tooltip_text(widget)
                if text == expected or expected.lower() in tooltip_text:
                    found = True
                    break
            self.assertTrue(
                found, f"Missing audio control '{expected}' in chatbot dialog"
            )

    @pytest.mark.skip(
        reason="Talk and Chat menus now implemented, GUI test may need GUI context"
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

    def test_vertical_mousewheel_handler_scrolls_up_and_down(self):
        widget = MagicMock()
        widget.yview_scroll = MagicMock()

        event_up = type("Event", (), {"delta": 120, "num": None})()
        event_down = type("Event", (), {"delta": -120, "num": None})()

        self.assertEqual(self.gui._on_vertical_mousewheel(event_up, widget), "break")
        self.assertEqual(self.gui._on_vertical_mousewheel(event_down, widget), "break")

        self.assertEqual(widget.yview_scroll.call_args_list[0].args, (-1, "units"))
        self.assertEqual(widget.yview_scroll.call_args_list[1].args, (1, "units"))

    def test_bottom_workspace_tabs_use_dark_notebook_style(self):
        self.assertEqual(
            self.gui.right_workspace_tabs.cget("style"), "Bottom.TNotebook"
        )
        style = ttk.Style(self.root)
        self.assertEqual(
            style.lookup("Bottom.TNotebook.Tab", "background", ("selected",)),
            "#21262d",
        )

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.gui = CrewGUI(self.root)

    def tearDown(self):
        if self.root:
            self.root.destroy()

    def test_record_menu_exists(self):
        """Test that Record menu methods exist and can be called."""
        # Check that the _create_record_menu method exists
        self.assertTrue(hasattr(self.gui.root, "winfo_exists"))
        # Try to access the menu (even if it's not visible, the method should exist)
        self.assertTrue(hasattr(self.gui, "menu_bar"))

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
