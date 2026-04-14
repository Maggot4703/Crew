import unittest
import tkinter as tk
import os
import sys
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from gui import CrewGUI

class TestGUIRecordMenu(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.gui = CrewGUI(self.root)

    def tearDown(self):
        if self.root:
            self.root.destroy()

    def test_record_menu_exists(self):
        found = False
        for i in range(self.gui.menu_bar.index('end') + 1):
            try:
                menu_ref = self.gui.menu_bar.entrycget(i, 'menu')
                if menu_ref:
                    submenu = self.gui.menu_bar.nametowidget(menu_ref)
                    # Check if this is the record menu by checking for a known entry label
                    for j in range(submenu.index('end') + 1):
                        entry_label = submenu.entrycget(j, 'label')
                        if entry_label and 'Start Recording' in entry_label:
                            found = True
                            break
                if found:
                    break
            except Exception:
                continue
        self.assertTrue(found, "Record menu not found in menu bar.")

    def test_start_stop_recording(self):
        # Patch subprocess.Popen to avoid real recording
        with patch('subprocess.Popen') as mock_popen:
            mock_proc = MagicMock()
            # Simulate communicate() returning a tuple (stdout, stderr)
            mock_proc.communicate.return_value = (b"", b"")
            mock_popen.return_value = mock_proc
            self.gui._start_recording()
            self.assertIsNotNone(self.gui._recording_process)
            self.gui._stop_recording()
            self.assertIsNone(self.gui._recording_process)

    def test_play_recording_no_file(self):
        self.gui._last_recording_path = None
        with patch('os.path.exists', return_value=False):
            with patch.object(self.gui, 'update_status') as mock_status:
                self.gui._play_recording()
                mock_status.assert_called_with('No recording available to play.', error=True)

    def test_save_recording_no_file(self):
        self.gui._last_recording_path = None
        with patch('os.path.exists', return_value=False):
            with patch.object(self.gui, 'update_status') as mock_status:
                self.gui._save_recording_as()
                mock_status.assert_called_with('No recording available to save.', error=True)

if __name__ == "__main__":
    unittest.main()
