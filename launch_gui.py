#!/usr/bin/env python3
"""
Simple script to launch the Crew GUI
"""
import tkinter as tk

from gui import CrewGUI


def main():
    """Launch the Crew GUI application"""
    try:
        print("Creating root window...")
        root = tk.Tk()

        print("Initializing CrewGUI...")
        app = CrewGUI(root)

        print("Starting main loop...")
        root.mainloop()

        print("GUI closed")

    except Exception as e:
        print(f"Error launching GUI: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
