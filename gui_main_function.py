import tkinter as tk
from gui import CrewGUI

def main():
    root = tk.Tk()
    app = CrewGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()