<<<<<<< HEAD
import tkinter as tk
from gui import CrewGUI

def main():
=======
import sys
import tkinter as tk
import tkinter as tk
from pathlib import Path
from gui import CrewGUI  # Import CrewGUI from gui.py


def main():
    """Main function to initialize and run the GUI application."""
    root = tk.Tk()
    root.title("Crew GUI")
    # Version information can be displayed in the GUI if needed

    # Set application icon if available
    icon_path = Path("/home/me/BACKUP/PROJECTS/Crew/input/Cars1.png")
    if icon_path.exists() and icon_path.suffix == ".ico":
        root.iconbitmap(str(icon_path))  # Set application icon if available

    # Create and show the main window
    window = CrewGUI(root)
    root.mainloop()

    # Start the event loop
    root.mainloop()

import tkinter as tk
from gui import CrewGUI

def main():
>>>>>>> chunk-playback
    root = tk.Tk()
    app = CrewGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()