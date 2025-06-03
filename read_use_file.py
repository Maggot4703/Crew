#!/usr/bin/env python3
"""
This script reads out the contents of a selected "use-" file using text-to-speech.
"""

import glob
import os
import re
import sys
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

# Check if pyttsx3 is installed, if not, guide the user to install it
try:
    import pyttsx3
except ImportError:
    print("pyttsx3 library is not installed. Installing it now...")
    import subprocess
    import os
    
    # Get the path to the virtual environment's Python interpreter if available
    venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv', 'bin', 'python')
    if os.path.exists(venv_python):
        python_executable = venv_python
    else:
        python_executable = sys.executable
    
    try:
        subprocess.check_call([python_executable, "-m", "pip", "install", "pyttsx3"])
        import pyttsx3
        print("pyttsx3 installed successfully!")
    except (subprocess.CalledProcessError, ImportError) as e:
        print(f"Failed to install pyttsx3: {e}")
        print("Please install it manually: pip install pyttsx3")
        print("If using a virtual environment: source .venv/bin/activate && pip install pyttsx3")
        sys.exit(1)


class UseFileReader:
    def __init__(self, root):
        self.root = root
        self.root.title("Use File Reader")
        self.root.geometry("800x600")

        # Initialize file paths list
        self.file_paths = []

        self.setup_ui()
        self.load_files()

        # Initialize TTS engine
        self.engine = pyttsx3.init()
        self.reading_thread = None
        self.stop_reading = False

        # Default voice settings
        self.engine.setProperty("rate", 150)
        self.engine.setProperty("volume", 1.0)

        # Set female voice if available
        self.setup_female_voice()

    def setup_ui(self):
        """Set up the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # File selection area
        top_frame = ttk.LabelFrame(main_frame, text="Select a Use File", padding="10")
        top_frame.pack(fill=tk.X, pady=5)

        files_frame = ttk.Frame(top_frame)
        files_frame.pack(fill=tk.X, expand=True)

        scrollbar = ttk.Scrollbar(files_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox = tk.Listbox(files_frame, height=5)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.file_listbox.yview)

        self.file_listbox.bind("<Double-1>", lambda e: self.load_selected_file())

        # Preview frame
        preview_frame = ttk.LabelFrame(main_frame, text="File Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.preview_text = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD)
        self.preview_text.pack(fill=tk.BOTH, expand=True)

        # Controls frame
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=5)

        # Voice settings
        settings_frame = ttk.Frame(controls_frame)
        settings_frame.pack(fill=tk.X, pady=5)

        ttk.Label(settings_frame, text="Speed:").pack(side=tk.LEFT, padx=5)
        self.rate_scale = ttk.Scale(
            settings_frame, from_=50, to=300, value=150, command=self.change_rate
        )
        self.rate_scale.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ttk.Label(settings_frame, text="Volume:").pack(side=tk.LEFT, padx=5)
        self.volume_scale = ttk.Scale(
            settings_frame, from_=0.0, to=1.0, value=1.0, command=self.change_volume
        )
        self.volume_scale.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        self.load_button = ttk.Button(
            button_frame, text="Load Selected", command=self.load_selected_file
        )
        self.load_button.pack(side=tk.LEFT, padx=5)

        self.read_button = ttk.Button(
            button_frame, text="Read Aloud", command=self.read_aloud
        )
        self.read_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            button_frame,
            text="Stop Reading",
            command=self.stop_reading_aloud,
            state=tk.DISABLED,
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.refresh_button = ttk.Button(
            button_frame, text="Refresh Files", command=self.load_files
        )
        self.refresh_button.pack(side=tk.RIGHT, padx=5)

        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def change_rate(self, value):
        """Change the TTS speech rate."""
        self.engine.setProperty("rate", float(value))

    def change_volume(self, value):
        """Change the TTS volume."""
        self.engine.setProperty("volume", float(value))

    def setup_female_voice(self):
        """Set up a female voice if available"""
        try:
            # Get all available voices
            voices = self.engine.getProperty("voices")

            # Find an English voice to use as base
            english_voice = None
            for voice in voices:
                if "english" in voice.id.lower():
                    english_voice = voice
                    break

            if english_voice:
                # Configure for female voice using espeak variant
                # In espeak, adding '+f3' to the voice ID makes it female
                fem_voice = english_voice.id + "+f3"
                self.engine.setProperty("voice", fem_voice)
                self.status_var.set("Using female voice")
        except Exception as e:
            # If anything goes wrong, just use the default voice
            print(f"Could not set female voice: {e}")
            self.status_var.set("Using default voice")

    def load_files(self):
        """Load all use- files from the directory and subdirectories."""
        self.file_listbox.delete(0, tk.END)

        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Get all use-*.txt files
        use_files = []
        filenames_seen = set()

        for root, _, _ in os.walk(current_dir):
            files = glob.glob(os.path.join(root, "use-*.txt"))
            for file_path in files:
                filename = os.path.basename(file_path)
                if filename not in filenames_seen:
                    use_files.append(file_path)
                    filenames_seen.add(filename)

        # Sort files by name
        use_files.sort()

        # Store file paths for later retrieval
        self.file_paths = []

        for file_path in use_files:
            # Display filename in listbox, store full path in our list
            filename = os.path.basename(file_path)
            self.file_listbox.insert(tk.END, filename)
            self.file_paths.append(file_path)

        if self.file_listbox.size() > 0:
            self.file_listbox.selection_set(0)
            self.status_var.set(f"Loaded {self.file_listbox.size()} use files")
        else:
            self.status_var.set("No use files found")

    def get_selected_file_path(self):
        """Get the full path of the selected file."""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file first.")
            return None

        idx = selection[0]
        return self.file_paths[idx]

    def load_selected_file(self):
        """Load the content of the selected file into the preview area."""
        file_path = self.get_selected_file_path()
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, content)

            filename = os.path.basename(file_path)
            self.status_var.set(f"Loaded {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")

    def preprocess_text_for_speech(self, text):
        """Preprocess text to make it more suitable for TTS."""
        # Remove markdown headers (#)
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

        # Remove code blocks
        text = re.sub(r"```.*?```", " Code block omitted. ", text, flags=re.DOTALL)

        # Remove inline code
        text = re.sub(r"`.*?`", " Code omitted. ", text)

        # Replace bullet points
        text = re.sub(r"^[\*\-\+]\s+", "• ", text, flags=re.MULTILINE)

        # Handle numbered lists
        text = re.sub(r"^\d+\.\s+", "Number. ", text, flags=re.MULTILINE)

        # Replace URLs with placeholders
        text = re.sub(r"https?://\S+", " URL link. ", text)

        return text.strip()

    def read_aloud(self):
        """Read the content of the selected file aloud."""
        file_path = self.get_selected_file_path()
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            # Preprocess content for better TTS
            processed_content = self.preprocess_text_for_speech(content)

            # Disable the read button and enable the stop button
            self.read_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)

            # Reset stop flag
            self.stop_reading = False

            # Start reading in a separate thread
            self.reading_thread = threading.Thread(
                target=self._read_text, args=(processed_content,)
            )
            self.reading_thread.daemon = True
            self.reading_thread.start()

            filename = os.path.basename(file_path)
            self.status_var.set(f"Reading {filename}...")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file: {e}")

    def _read_text(self, text):
        """Background thread for text-to-speech."""
        try:
            # Break text into manageable chunks for better TTS handling
            chunks = self._chunk_text(text)

            for chunk in chunks:
                if self.stop_reading:
                    break
                self.engine.say(chunk)
                self.engine.runAndWait()
                if self.stop_reading:
                    break
        except Exception as e:
            print(f"Error during TTS: {e}")
        finally:
            # Re-enable buttons when done
            self.root.after(0, self._reading_finished)

    def _chunk_text(self, text, max_length=1000):
        """Split text into smaller chunks for better TTS handling."""
        words = text.split()
        chunks = []
        current_chunk = []

        for word in words:
            current_chunk.append(word)
            if len(" ".join(current_chunk)) > max_length:
                chunks.append(" ".join(current_chunk))
                current_chunk = []

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _reading_finished(self):
        """Called when TTS reading is complete."""
        self.read_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("Reading finished")

    def stop_reading_aloud(self):
        """Stop the current TTS reading."""
        self.stop_reading = True
        self.engine.stop()

        # Re-enable the read button
        self.read_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("Reading stopped")


def main():
    """Main function to run the application."""
    root = tk.Tk()
    app = UseFileReader(root)
    root.mainloop()


if __name__ == "__main__":
    main()
