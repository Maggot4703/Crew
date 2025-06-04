#!/usr/bin/env python3
"""
Launcher script for Crew Manager GUI
"""
import tkinter as tk

from gui import CrewGUI

if __name__ == "__main__":
    root = tk.Tk()
    app = CrewGUI(root)
    root.mainloop()
