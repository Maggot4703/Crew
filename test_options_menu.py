import unittest
import tkinter as tk
from gui import CrewGUI

class TestOptionsMenu(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.app = CrewGUI(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_change_username_dialog(self):
        # Simulate opening the dialog and changing the username
        self.app.change_username_dialog()
        dialogs = [w for w in self.root.winfo_children() if isinstance(w, tk.Toplevel)]
        self.assertTrue(dialogs, "Change Username dialog did not open.")
        dialog = dialogs[0]
        entry = dialog.winfo_children()[1]
        entry.delete(0, tk.END)
        entry.insert(0, "TestUser")
        ok_btn = dialog.winfo_children()[2]
        ok_btn.invoke()
        self.assertEqual(self.app.logged_in_user["name"], "TestUser")

    def test_set_status_dialog(self):
        self.app.set_status_dialog()
        dialogs = [w for w in self.root.winfo_children() if isinstance(w, tk.Toplevel)]
        self.assertTrue(dialogs, "Set Status dialog did not open.")
        dialog = dialogs[0]
        entry = dialog.winfo_children()[1]
        entry.delete(0, tk.END)
        entry.insert(0, "Busy")
        ok_btn = dialog.winfo_children()[2]
        ok_btn.invoke()
        self.assertEqual(self.app.user_status["msg"], "Busy")

if __name__ == "__main__":
    unittest.main()
