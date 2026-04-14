import tkinter as tk
from tkinter import ttk, messagebox

def show_dialog():
    win = tk.Toplevel(root)
    win.title("Test Dialog")
    win.geometry("350x200")
    win.grab_set()
    win.focus_set()
    tk.Label(win, text="Select an option:").pack(anchor="w", padx=10, pady=(10,0))
    options = ["Mic 1", "Mic 2", "Mic 3"]
    selected = tk.StringVar(value=options[0])
    combo = ttk.Combobox(win, values=options, textvariable=selected, state="readonly")
    combo.pack(fill="x", padx=10, pady=10)
    def on_ok():
        messagebox.showinfo("Selected", f"You selected: {selected.get()}", parent=win)
        win.destroy()
    tk.Button(win, text="OK", command=on_ok).pack(pady=10)
    win.transient(root)
    win.wait_window()

root = tk.Tk()
root.title("Tkinter Test Main Window")
root.geometry("400x200")
tk.Button(root, text="Open Dialog", command=show_dialog).pack(pady=40)
root.mainloop()
