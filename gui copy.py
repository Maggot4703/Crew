#!/usr/bin/python3

# region Imports - Core Libraries
import csv  # CSV file handling
import glob  # File pattern matching
import importlib.util  # Dynamic module importing
import json  # JSON file handling for caching
import logging  # Application logging
import os  # Operating system interface
import subprocess  # Process execution
import sys  # System-specific parameters
import threading  # Background thread support
import time  # Time-related functions for caching
import tkinter as tk  # Core GUI framework

# Remove deprecated tix import, use ttk tooltips instead
from pathlib import Path  # Cross-platform file handling
from queue import Queue  # Thread-safe task queue

# Try to import pandas for data handling
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print(
        "Warning: pandas not available. Some data import/export features may be limited."
    )

# region Imports - Core GUI and Data Management
from tkinter import filedialog, messagebox, ttk  # GUI components and dialogs
from typing import (  # Type hints for better code quality; Additional type hints
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
)

from config import Config  # Configuration management
from database_manager import DatabaseManager  # Data persistence layer

# Try to import CustomTkinter for modern styling
try:
    import customtkinter as ctk

    CTK_AVAILABLE = True
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
except ImportError:
    CTK_AVAILABLE = False
    print("CustomTkinter not available. Using standard tkinter styling.")

# TTS functionality
try:
    import pyttsx3  # Text-to-speech engine

    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("Warning: pyttsx3 not available. TTS functionality disabled.")

# endregion

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def auto_import_py_files() -> Tuple[List[str], List[Tuple[str, str]]]:
    try:
        # Get the current working directory
        workspace_root = Path.cwd()

        # Cache for performance - avoid re-scanning if called multiple times
        cache_file = workspace_root / ".auto_import_cache.json"
        current_time = time.time()

        # Check if we have a recent cache (less than 5 minutes old)
        if cache_file.exists():
            try:
                cache_age = current_time - cache_file.stat().st_mtime
                if cache_age < 300:  # 5 minutes
                    with open(cache_file, "r") as f:
                        cache_data = json.load(f)
                        if cache_data.get("workspace_root") == str(workspace_root):
                            logging.info("Using cached auto-import results")
                            return (
                                cache_data["imported_modules"],
                                cache_data["failed_imports"],
                            )
            except (json.JSONDecodeError, KeyError, OSError) as e: # Added exception logging
                logging.warning(f"Error reading auto-import cache: {e}. Proceeding with fresh scan.")
                # If cache is corrupted, continue with fresh scan
                pass

        # Find all .py files in the workspace
        py_files = []

        # Use more efficient file discovery
        for py_file in workspace_root.rglob("*.py"):
            py_files.append(str(py_file))

        # Remove duplicates and sort
        py_files = sorted(list(set(py_files)))

        imported_modules = []
        failed_imports = []

        # Enhanced skip patterns with more comprehensive exclusions
        skip_files = {
            "gui.py",
            "setup.py",
            "__init__.py",
            "output.txt.py",
            "globals.py",
            "Crew.py",
            "test_script_demo.py",
            "test_auto_import.py",
            "config.py",  # Configuration files may have side effects
            "settings.py",  # Settings files may have side effects
            "enhanced_features.py",
            "conftest.py",  # Pytest configuration
        }

        # Additional patterns to skip
        skip_patterns = {
            ".txt.py",
            "main.py",
            "run.py",
            "test_",
            "_test",
            "demo",
            "example",
            "sample",
            "prototype",
            "backup",
            "old",
            "temp",
            "tmp",
            "_backup",
        }

        # Enhanced directory exclusions
        skip_dirs = {
            "__pycache__",
            ".git",
            "venv",
            "env",
            "tests",
            "test",
            "tts_venv",  # Legacy TTS environment (removed, kept for compatibility)
            ".venv",  # Primary virtual environment
            "node_modules",  # Node.js modules
            "build",  # Build directories
            "dist",  # Distribution directories
            ".pytest_cache",  # Pytest cache
            ".mypy_cache",  # MyPy cache
            "site-packages",  # Python site packages
            "lib",  # Library directories
            "bin",  # Binary directories
            "include",  # Include directories
            "share",  # Share directories
        }

        # Pre-compile dangerous import patterns for better performance
        dangerous_patterns = [
            'if __name__ == "__main__"',
            "subprocess.call",
            "subprocess.run",
            "sys.argv",
            "argparse",
            "main()",
            "logging.basicconfig",
            "speak(",
            "sys.exit",
            "os.system",
            "plt.show",
            "plt.plot",
        ]

        files_processed = 0
        files_skipped = 0

        for py_file in py_files:
            try:
                py_path = Path(py_file)
                relative_path = py_path.relative_to(workspace_root)

                # Skip files in excluded directories
                if any(skip_dir in relative_path.parts for skip_dir in skip_dirs):
                    files_skipped += 1
                    continue

                # Skip excluded files
                if py_path.name in skip_files:
                    files_skipped += 1
                    continue

                # Skip files matching problematic patterns
                if any(pattern in py_path.name for pattern in skip_patterns):
                    files_skipped += 1
                    continue

                # Skip test files
                if py_path.name.startswith("test_") or "unittest" in py_path.name:
                    files_skipped += 1
                    continue

                # Additional safety check: skip files that look like scripts
                if py_path.name.lower() in {
                    "main.py",
                    "run.py",
                    "start.py",
                    "launch.py",
                }:
                    files_skipped += 1
                    continue

                # Enhanced safety check: read first chunk to detect script files
                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        # Read first 20 lines for better detection
                        first_chunk = "\n".join(f.readline().strip() for _ in range(20))

                    file_content_lower = first_chunk.lower()

                    # Skip files with dangerous patterns
                    if any(
                        pattern in file_content_lower for pattern in dangerous_patterns
                    ):
                        files_skipped += 1
                        logging.debug(
                            f"Skipping {py_path.name} - contains script patterns"
                        )
                        continue

                    # Skip files with immediate side effects
                    if "print(" in file_content_lower and any(
                        keyword in file_content_lower
                        for keyword in ["loaded", "starting", "running"]
                    ):
                        files_skipped += 1
                        logging.debug(
                            f"Skipping {py_path.name} - has immediate side effects"
                        )
                        continue

                except (IOError, UnicodeDecodeError):
                    # If we cant read the file, skip it for safety
                    files_skipped += 1
                    continue

                # Create safe module name from path
                module_name = str(relative_path.with_suffix(""))
                module_name = module_name.replace("/", ".").replace("\\", ".")

                # Handle files with spaces or special characters
                if " " in module_name or any(
                    char in module_name for char in (",", "-", "+")
                ):
                    safe_name = (
                        module_name.replace(" ", "_")
                        .replace(",", "_")
                        .replace("-", "_")
                        .replace("+", "_")
                    )
                    module_name = safe_name

                # Try to import the module with enhanced error handling
                try:
                    spec = importlib.util.spec_from_file_location(module_name, py_file)
                    if spec and spec.loader:
                        # Check if module is already loaded
                        if module_name in sys.modules:
                            imported_modules.append(f"{module_name} (cached)")
                            files_processed += 1
                            continue

                        # Import with timeout protection (if available)
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[module_name] = module

                        # Execute module with error containment
                        spec.loader.exec_module(module)
                        imported_modules.append(module_name)
                        files_processed += 1

                except (
                    ImportError,
                    ModuleNotFoundError,
                    SyntaxError,
                    AttributeError,
                ) as e:
                    # These are expected for some files
                    error_msg = f"Import error: {str(e)[:100]}"
                    failed_imports.append((str(relative_path), error_msg))
                    files_processed += 1
                    continue

                except Exception as e:
                    # Unexpected errors
                    error_msg = f"Unexpected error: {str(e)[:100]}"
                    failed_imports.append((str(relative_path), error_msg))
                    logging.warning(f"Failed to auto-import {py_file}: {e}")
                    files_processed += 1
                    continue

            except Exception as e:
                failed_imports.append((str(py_file), f"Path error: {str(e)[:100]}"))
                continue

        # Log comprehensive results
        total_files = files_processed + files_skipped
        if imported_modules:
            logging.info(f"Auto-imported {len(imported_modules)} modules successfully")

        if failed_imports:
            logging.info(
                f"Skipped {len(failed_imports)} modules (expected for script files)"
            )

        logging.info(
            f"Auto-import summary: {len(imported_modules)} imported, "
            f"{len(failed_imports)} failed, {files_skipped} skipped, "
            f"{total_files} total files processed"
        )

        # Cache the results for future use
        try:
            cache_data = {
                "workspace_root": str(workspace_root),
                "imported_modules": imported_modules,
                "failed_imports": failed_imports,
                "timestamp": current_time,
            }
            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)
        except Exception as cache_error:
            logging.debug(f"Could not cache auto-import results: {cache_error}")

        return imported_modules, failed_imports

    except Exception as e:
        logging.error(f"Auto-import process failed: {e}")
        return [], [(str(Path.cwd()), str(e))] # Ensure workspace_root is defined for the error case

class CrewGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root  # Assign self.root immediately
        try:
            self.root.title("Crew Manager") # Set title early

            # Define scripts directory and create it if it doesn't exist
            # Also create a sample script for testing if the directory is new
            self.scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
            if not os.path.exists(self.scripts_dir):
                try: # Try to create directory
                    os.makedirs(self.scripts_dir)
                    logging.info(f"Created scripts directory: {self.scripts_dir}")
                    
                    # After successful directory creation, try to create sample script
                    try:
                        sample_script_path = os.path.join(self.scripts_dir, "sample_script.py")
                        with open(sample_script_path, "w") as f:
                            f.write("# Sample script for CrewGUI\\n")
                            f.write("import time\\n")
                            f.write("print('Hello from sample_script.py!')\\n")
                            f.write("print('This script will run for a few seconds.')\\n")
                            f.write("for i in range(1, 4):\\n")
                            f.write("    print(f'Counting: {i}')\\n")
                            f.write("    time.sleep(1)\\n")
                            f.write("print('Sample script finished.')\\n")
                        logging.info(f"Created sample script: {sample_script_path}")
                    except Exception as e_script:
                        logging.error(f"Failed to create sample script in {self.scripts_dir}: {e_script}")
                        # Optionally, a very mild warning or just log for sample script failure. Currently just logging.

                except Exception as e_dir: # This catches failure of os.makedirs
                    logging.error(f"Failed to create scripts directory {self.scripts_dir}: {e_dir}")
                    messagebox.showwarning(
                        "Script Directory Error",
                        f"Could not create the 'scripts' directory at:\\n{self.scripts_dir}\\n\\nReason: {e_dir}\\n\\nThe 'Run Script' feature requires this directory. Please create it manually or check permissions."
                    )
            # If directory already exists, one might consider creating sample_script if it's missing,
            # but current logic only creates it if the directory itself is new.

            # Initialize TTS engine if available
            if TTS_AVAILABLE:
                self.tts_engine = pyttsx3.init()
            else:
                self.tts_engine = None

            # Create menu bar before other UI elements
            self.create_menu_bar()

            self.config = Config()
            self.setup_logging() # os is used here, but this line is commented out
            self.setup_state()
            self.create_main_layout()
            self.create_all_widgets()
            self.bind_events()

            # Auto-import all .py files in workspace after GUI is set up
            self.update_status("Auto-importing workspace modules...")
            self.imported_modules, self.failed_imports = auto_import_py_files()

            # Initialize background worker
            self.task_queue: Queue = Queue()
            self.worker_thread = threading.Thread(
                target=self._background_worker, daemon=True
            )
            self.worker_thread.start()

            # Load window state after widgets are created
            self.load_window_state()

            # Load default data file if exists
            self.load_default_data()

            # Update status with import results
            total_imported = (
                len(self.imported_modules) if hasattr(self, "imported_modules") else 0
            )
            total_failed = (
                len(self.failed_imports) if hasattr(self, "failed_imports") else 0
            )
            self.update_status(
                f"Ready - Auto-imported {total_imported} modules ({total_failed} failed)"
            )

        except Exception as e:
            logging.error(f"Failed to initialize GUI: {e}")
            messagebox.showerror("Error", f"Failed to initialize application: {e}")
            raise

    def _show_speech_settings(self) -> None:
        try:
            if not TTS_AVAILABLE or not self.tts_engine:
                messagebox.showinfo("TTS Not Available", "Text-to-speech functionality is not available.")
                return

            settings_window = tk.Toplevel(self.root)
            settings_window.title("Speech Settings")
            settings_window.geometry("400x300")
            settings_window.transient(self.root)
            settings_window.grab_set()

            # Voice selection
            ttk.Label(settings_window, text="Voice:").pack(pady=5)
            voice_var = tk.StringVar()
            voice_combo = ttk.Combobox(
                settings_window, textvariable=voice_var, state="readonly"
            )

            voices = self.tts_engine.getProperty("voices")
            voice_names = [voice.name for voice in voices]
            voice_combo["values"] = voice_names

            current_voice = self.tts_engine.getProperty("voice")
            for voice in voices:
                if voice.id == current_voice:
                    voice_var.set(voice.name)
                    break

            voice_combo.pack(pady=5, padx=20, fill="x")

            # Speed control
            ttk.Label(settings_window, text="Speed:").pack(pady=5)
            speed_var = tk.IntVar(value=self.tts_engine.getProperty("rate"))
            speed_scale = ttk.Scale(
                settings_window,
                from_=50,
                to=300,
                variable=speed_var,
                orient="horizontal",
            )
            speed_scale.pack(pady=5, padx=20, fill="x")

            # Volume control
            ttk.Label(settings_window, text="Volume:").pack(pady=5)
            volume_var = tk.DoubleVar(value=self.tts_engine.getProperty("volume"))
            volume_scale = ttk.Scale(
                settings_window,
                from_=0.0,
                to=1.0,
                variable=volume_var,
                orient="horizontal",
            )
            volume_scale.pack(pady=5, padx=20, fill="x")

            def apply_settings():
                try:
                    selected_voice = voice_var.get()
                    for voice in voices:
                        if voice.name == selected_voice:
                            self.tts_engine.setProperty("voice", voice.id)
                            break
                    self.tts_engine.setProperty("rate", speed_var.get())
                    self.tts_engine.setProperty("volume", volume_var.get())
                    settings_window.destroy()
                    self.update_status("Speech settings updated")
                except Exception as e:
                    logging.error(f"Error applying speech settings: {e}")
                    messagebox.showerror("Error", f"Failed to apply settings: {e}")

            # Buttons frame
            buttons_frame = ttk.Frame(settings_window)
            buttons_frame.pack(pady=20)
            ttk.Button(buttons_frame, text="Apply", command=apply_settings).pack(side="left", padx=5)
            ttk.Button(buttons_frame, text="Cancel", command=settings_window.destroy).pack(side="left", padx=5)

        except Exception as e:
            logging.error(f"Error showing speech settings: {e}")

    def create_menu_bar(self) -> None:
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open... (Ctrl+O)", command=self._on_open_file) # New combined open
        file_menu.add_separator()
        file_menu.add_command(label="Save... (Ctrl+S)", command=self._on_save_file) # New combined save
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Edit menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(
            label="Find (Ctrl+F)", command=lambda: self.filter_entry_widget.focus_set() if hasattr(self, 'filter_entry_widget') else None
        )
        edit_menu.add_command(label="Clear Filter (Esc)", command=self.clear_filter)

        # View menu
        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh (F5)", command=self._refresh_views)
        # view_menu.add_command(
        #     label="Show Imported Modules", command=self._show_imported_modules
        # )
        view_menu.add_separator()

        # Add column visibility submenu
        self.column_visibility_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Columns", menu=self.column_visibility_menu)

        # Add script selector submenu
        self.script_menu = tk.Menu(view_menu, tearoff=0, postcommand=self._update_script_menu)
        view_menu.add_cascade(
            label="Run Script", 
            menu=self.script_menu
            # Removed command=lambda from here
        )
        # view_menu.add_command(label="Refresh Scripts", command=self._update_script_menu) # Now part of self.script_menu

        # Add TTS menu if available
        if TTS_AVAILABLE:
            tts_menu = tk.Menu(self.menu_bar, tearoff=0)
            self.menu_bar.add_cascade(label="🔊 Speech", menu=tts_menu)
            tts_menu.add_command(label="Read Status", command=self._read_status)
            tts_menu.add_command(
                label="Read Selected Item", command=self._read_selected_item
            )
            tts_menu.add_separator()
            tts_menu.add_command(label="Stop Reading", command=self._stop_reading)
            tts_menu.add_separator()
            # Uncommented to enable speech settings in menu
            tts_menu.add_command(
                label="Speech Settings...", command=self._show_speech_settings
            )

    def bind_events(self) -> None:
        try:
            # Clear filter with Escape key
            self.root.bind("<Escape>", lambda event: self.clear_filter())

            # Focus filter field with Ctrl+F
            self.root.bind(
                "<Control-f>",
                lambda event: (
                    self.filter_var.focus_set() if hasattr(self, "filter_var") else None
                ),
            )

            # Refresh with F5
            self.root.bind(
                "<F5>",
                lambda event: (
                    self._refresh_views() if hasattr(self, "_refresh_views") else None
                ),
            )

        except Exception as e:
            logging.error(f"Error setting up event bindings: {e}")

    def load_window_state(self) -> None:
        try:
            # Restore window geometry
            if self.config.get("window_size"):
                self.root.geometry(self.config.get("window_size"))

            if self.config.get("min_window_size"):
                self.root.minsize(
                    *map(int, self.config.get("min_window_size").split("x"))
                )

            # Store column widths for later application after table is populated
            self._saved_column_widths = self.config.get("column_widths", {})

            # Restore column visibility preferences
            saved_visibility = self.config.get("column_visibility", {})
            if saved_visibility and hasattr(self, "column_visibility"):
                self.column_visibility.update(saved_visibility)

        except Exception as e:
            logging.error(f"Error loading window state: {e}")

    def save_window_state(self) -> None:
        try:
            self.config.set("window_size", self.root.geometry())

            # Save column widths
            column_widths = {}
            for col in self.data_table["columns"]:
                column_widths[col] = self.data_table.column(col, "width")
            self.config.set("column_widths", column_widths)

            # Save column visibility preferences
            if hasattr(self, "column_visibility"):
                self.config.set("column_visibility", self.column_visibility)

        except Exception as e:
            logging.error(f"Error saving window state: {e}")

    def _background_worker(self) -> None:
        while True:
            func, args, callback = self.task_queue.get()
            try:
                result = func(*args)
                if callback:
                    self.root.after(0, lambda r=result: callback(r))
            except Exception as e:
                logging.error(f"Background worker error: {e}")
                self.background_exception = e
                self.root.after(0, lambda: self.root.event_generate("<<TaskFailed>>"))
            self.task_queue.task_done()

    def run_in_background(
        self, func: Callable, *args, callback: Optional[Callable] = None
    ) -> None:
        self.task_queue.put((func, args, callback))

    def setup_logging(self) -> None:
        logging.basicConfig(
            level=logging.INFO, 
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("crew_gui.log"),
                logging.StreamHandler()
            ]
        )

    def setup_state(self) -> None:
        self.db = DatabaseManager()
        self.groups = {}  # Store groups data
        self.current_groups = {}
        self.group_preview = {}
        self.current_columns = []
        self.current_data = []
        self.headers = []  # Initialize empty headers
        self.column_visibility = {}  # Initialize column visibility tracking

    def create_main_layout(self) -> None:
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        self.main_frame = ttk.Frame(self.root, padding="5")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.paned_window = ttk.PanedWindow(self.main_frame, orient="horizontal")
        self.paned_window.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.left_frame = ttk.Frame(self.paned_window, width=280)
        self.left_frame.grid_propagate(False)
        self.right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.left_frame, weight=0)
        self.paned_window.add(self.right_frame, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)
        self.left_frame.grid_rowconfigure(0, weight=0)
        self.left_frame.grid_rowconfigure(1, weight=1)
        self.left_frame.grid_rowconfigure(2, weight=0)
        self.right_frame.grid_rowconfigure(0, weight=3)
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

    def create_all_widgets(self) -> None:
        try:
            self.create_control_section()
            self.create_group_section()
            self.create_filter_section()
            self.create_data_section()
            self.create_details_section()
            self.create_status_bar()
        except Exception as e:
            logging.error(f"Failed to create widgets: {e}")
            raise

    def create_status_bar(self) -> None:
        try:
            self.status_var = tk.StringVar(value="Ready")
            self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
            self.status_bar.grid(row=1, column=0, sticky="ew")
            self.status_bar.bind("<Enter>", self._show_status_tooltip)
            self.status_bar.bind("<Leave>", self._hide_status_tooltip)
        except Exception as e:
            logging.error(f"Failed to create status bar: {e}")

    def update_status(self, message: str) -> None:
        try:
            if hasattr(self, "status_var"):
                self.status_var.set(message)
        except Exception as e:
            logging.error(f"Error updating status: {e}")

    def _show_status_tooltip(self, event: tk.Event) -> None:
        msg = self.status_var.get()
        if len(msg) > 50:
            self.status_tooltip = tk.Toplevel(self.root)
            self.status_tooltip.wm_overrideredirect(True)
            x = event.x_root + 10
            y = event.y_root + 10
            self.status_tooltip.geometry(f"+{x}+{y}")
            tooltip_label = tk.Label(
                self.status_tooltip,
                text=msg,
                background="lightyellow",
                relief="solid",
                borderwidth=1,
                font=("TkDefaultFont", 9),
                wraplength=300,
            )
            tooltip_label.pack()

    def _hide_status_tooltip(self, event: tk.Event) -> None:
        if hasattr(self, "status_tooltip") and self.status_tooltip:
            try:
                self.status_tooltip.destroy()
                self.status_tooltip = None
            except tk.TclError:
                self.status_tooltip = None

    def create_control_section(self) -> None:
        try:
            control_frame = ttk.LabelFrame(
                self.left_frame, text="Controls", padding="5"
            )
            control_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
            ttk.Button(
                control_frame, text="Open...", command=self._on_open_file
            ).pack(fill="x", pady=2)
            ttk.Button(
                control_frame, text="Save...", command=self._on_save_file
            ).pack(fill="x", pady=2)
        except Exception as e:
            logging.error(f"Failed to create control section: {e}")
            raise

    def create_group_section(self) -> None:
        try:
            group_frame = ttk.LabelFrame(self.left_frame, text="Groups", padding="5")
            group_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
            self.group_list = ttk.Treeview(group_frame, selectmode="browse", height=10)
            self.group_list.pack(fill="both", expand=True)
            self.group_menu = tk.Menu(self.group_list, tearoff=0)
            self.group_menu.add_command(
                label="Delete", command=self._delete_selected_group
            )
            self.group_list.bind("<Button-3>", self._show_group_menu)
            scrollbar = ttk.Scrollbar(
                group_frame, orient="vertical", command=self.group_list.yview
            )
            scrollbar.pack(side="right", fill="y")
            self.group_list.configure(yscrollcommand=scrollbar.set)
        except Exception as e:
            logging.error(f"Failed to create group section: {e}")
            raise

    def _show_group_menu(self, event: tk.Event) -> None:
        try:
            item = self.group_list.identify_row(event.y)
            if item:
                self.group_list.selection_set(item)
                self.group_menu.post(event.x_root, event.y_root)
        except Exception as e:
            logging.error(f"Error showing group menu: {e}")

    def _delete_selected_group(self) -> None:
        try:
            selection = self.group_list.selection()
            if not selection:
                return
            item_id = selection[0]
            group_name = self.group_list.item(item_id)["text"]
            if messagebox.askyesno("Confirm Delete", f"Delete group '{group_name}'?"):
                self.group_list.delete(item_id)
        except Exception as e:
            logging.error(f"Error deleting group: {e}")
            messagebox.showerror("Error", f"Failed to delete group: {e}")

    def create_filter_section(self) -> None:
        try:
            filter_frame = ttk.LabelFrame(self.left_frame, text="Filters", padding="5")
            filter_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
            self.filter_frame = filter_frame
            self.filter_var = tk.StringVar(value="")
            self.column_var = tk.StringVar(value="All Columns")
            self.column_menu = ttk.Combobox(
                filter_frame, textvariable=self.column_var, state="readonly"
            )
            self.column_menu.pack(fill="x", pady=2)
            self.filter_entry_widget = ttk.Entry(filter_frame, textvariable=self.filter_var)
            self.filter_entry_widget.pack(fill="x", pady=2)
            ttk.Button(
                filter_frame, text="Apply Filter", command=self._on_apply_filter
            ).pack(fill="x", pady=2)
        except Exception as e:
            logging.error(f"Failed to create filter section: {e}")
            raise

    def create_data_section(self) -> None:
        try:
            data_frame = ttk.LabelFrame(self.right_frame, text="Data View", padding="5")
            data_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            table_frame = ttk.Frame(data_frame)
            table_frame.grid(row=0, column=0, sticky="nsew")
            data_frame.grid_rowconfigure(0, weight=1)
            data_frame.grid_columnconfigure(0, weight=1)
            table_frame.grid_rowconfigure(0, weight=1)
            table_frame.grid_columnconfigure(0, weight=1)
            self.data_table = ttk.Treeview(
                table_frame, show="headings", selectmode="browse"
            )
            y_scroll = ttk.Scrollbar(
                table_frame, orient="vertical", command=self.data_table.yview
            )
            x_scroll = ttk.Scrollbar(
                table_frame, orient="horizontal", command=self.data_table.xview
            )
            self.data_table.configure(
                yscrollcommand=y_scroll.set,
                xscrollcommand=x_scroll.set,
                style="Treeview",
            )
            self.data_table.bind("<Button-1>", self._on_column_click)
            self.data_table.grid(row=0, column=0, sticky="nsew")
            y_scroll.grid(row=0, column=1, sticky="ns")
            x_scroll.grid(row=1, column=0, sticky="ew")
            style = ttk.Style()
            style.configure("Treeview", rowheight=25)
            style.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"))

            # Add hook to apply saved column widths after table is populated
            def apply_saved_column_widths(event=None):
                if hasattr(self, "_saved_column_widths") and self._saved_column_widths:
                    # Ensure columns exist before trying to configure them
                    table_columns = self.data_table["columns"]
                    if not table_columns: # Table might not be fully populated yet
                        return

                    for col_id, width in self._saved_column_widths.items():
                        # Check if col_id is a valid column identifier for the current table
                        if col_id in table_columns:
                            self.data_table.column(col_id, width=width)
                        else:
                            logging.warning(f"Column ID {col_id} not found in table while applying saved widths.")
                    # Optionally, clear saved widths if they should only be applied once
                    # self._saved_column_widths = {}

            # Bind to table population event
            self.data_table.bind("<<TreeviewPopulated>>", apply_saved_column_widths)

        except Exception as e:
            logging.error(f"Failed to create data section: {e}")
            raise

    def create_details_section(self) -> None:
        try:
            details_frame = ttk.LabelFrame(
                self.right_frame, text="Details View", padding="5"
            )
            details_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
            text_frame = ttk.Frame(details_frame)
            text_frame.grid(row=0, column=0, sticky="nsew")

            # Configure frame weights for expansion
            details_frame.grid_rowconfigure(0, weight=1)
            details_frame.grid_columnconfigure(0, weight=1)
            text_frame.grid_rowconfigure(0, weight=1)
            text_frame.grid_columnconfigure(0, weight=1)

            # Create text widget for details display
            self.details_text = tk.Text(
                text_frame,
                wrap=tk.WORD,
                font=("Consolas", 10),  # Monospace font for structured data
                state=tk.NORMAL,  # Allow editing for TTS selection
                height=8,  # Reasonable default height
                background="white",
                foreground="black",
            )

            # Create vertical scrollbar for text widget
            details_scroll = ttk.Scrollbar(
                text_frame, orient="vertical", command=self.details_text.yview
            )

            # Configure text widget to use scrollbar
            self.details_text.configure(yscrollcommand=details_scroll.set)

            # Grid layout with scrollbar
            self.details_text.grid(row=0, column=0, sticky="nsew")
            details_scroll.grid(row=0, column=1, sticky="ns")

            # Set initial content
            self.details_text.insert(
                "1.0", "Select an item from the table above to view details here."
            )

            # Bind selection event for table to update details
            if hasattr(self, "data_table"):
                # Ensure the TreeviewSelect event is bound to the intermediary handler
                self.data_table.bind("<<TreeviewSelect>>", self._on_data_table_select)

            # Setup TTS functionality if available
            self._setup_details_tts()

        except Exception as e:
            logging.error(f"Failed to create details section: {e}")
            raise

    def _setup_details_tts(self) -> None:
        if not TTS_AVAILABLE:
            return
        try:
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="Read Selection", command=self._read_selection)
            context_menu.add_command(label="Read All", command=self._read_all_details)
            context_menu.add_separator()
            context_menu.add_command(label="Stop Reading", command=self._stop_reading)
            def show_context_menu(event):
                context_menu.tk_popup(event.x_root, event.y_root)
            self.details_text.bind("<Button-3>", show_context_menu)
        except Exception as e:
            logging.error(f"Error setting up details TTS: {e}")

    def _read_selection(self) -> None:
        if not TTS_AVAILABLE or not self.tts_engine:
            return
        try:
            if self.details_text.tag_ranges(tk.SEL):
                selected_text = self.details_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            else:
                current_line = self.details_text.index(tk.INSERT).split(".")[0]
                selected_text = self.details_text.get(f"{current_line}.0", f"{current_line}.end")
            if selected_text.strip():
                self.tts_engine.say(selected_text)
                self.tts_engine.runAndWait()
        except Exception as e:
            logging.error(f"TTS selection error: {e}")

    def _read_all_details(self) -> None:
        if not TTS_AVAILABLE or not self.tts_engine:
            return
        try:
            all_text = self.details_text.get("1.0", tk.END)
            if all_text.strip():
                self.tts_engine.say(all_text)
                self.tts_engine.runAndWait()
        except Exception as e:
            logging.error(f"TTS all details error: {e}")

    def _read_status(self) -> None:
        if not TTS_AVAILABLE or not self.tts_engine:
            return
        try:
            if hasattr(self, "status_var") and self.status_var:
                status_text = self.status_var.get()
                if status_text.strip():
                    self.tts_engine.say(status_text)
                    self.tts_engine.runAndWait()
        except Exception as e:
            logging.error(f"TTS status error: {e}")

    def _read_selected_item(self) -> None:
        if not TTS_AVAILABLE or not self.tts_engine:
            return
        try:
            if hasattr(self, "data_table"):
                selection = self.data_table.selection()
                if selection:
                    item_id = selection[0]
                    item_data = self.data_table.item(item_id)
                    values = item_data.get("values", [])
                    text = ", ".join(str(v) for v in values)
                    if text.strip():
                        self.tts_engine.say(text)
                        self.tts_engine.runAndWait()
        except Exception as e:
            logging.error(f"TTS selected item error: {e}")

    def _stop_reading(self) -> None:
        if not TTS_AVAILABLE or not self.tts_engine:
            return
        try:
            self.tts_engine.stop()
        except Exception as e:
            logging.error(f"Error stopping TTS: {e}")

    def _update_details_view(self, item_data: Optional[Dict[str, Any]]) -> None:
        try:
            if hasattr(self, "details_text"):
                self.details_text.config(state=tk.NORMAL)
                self.details_text.delete("1.0", tk.END)
                if item_data and "values" in item_data and self.headers:
                    values = item_data["values"]
                    # Show each column title and value
                    for header, value in zip(self.headers, values):
                        self.details_text.insert(tk.END, f"{header}: {value}\n")
                else:
                    self.details_text.insert("1.0", "Select an item from the table above to view details here.")
                self.details_text.config(state=tk.NORMAL)
        except Exception as e:
            logging.error(f"Error updating details view: {e}", exc_info=True)
            if hasattr(self, "details_text"):
                self.details_text.delete("1.0", tk.END)
                self.details_text.insert("1.0", f"Error displaying details: {e}")

    def _on_data_table_select(self, event: tk.Event) -> None:
        try:
            if not hasattr(self, "data_table"):
                return
            selection = self.data_table.selection()
            if selection:
                item_id = selection[0]
                item_data = self.data_table.item(item_id)
                self._update_details_view(item_data)
            else:
                self._update_details_view(None)
        except Exception as e:
            logging.error(f"Error handling data table selection: {e}")
            if hasattr(self, "details_text"):
                self.details_text.delete("1.0", tk.END)
                self.details_text.insert("1.0", "Error displaying details after selection.")

    def _update_script_menu(self) -> None:
        logging.info("Updating script menu as it is about to be displayed...")
        if not hasattr(self, 'script_menu') or not isinstance(self.script_menu, tk.Menu):
            logging.error(
                "self.script_menu is not initialized or is not a tk.Menu instance. "
                "The 'Run Script' submenu cannot be populated. "
                "Ensure create_menu_bar() correctly initializes self.script_menu and is called before _update_script_menu()."
            )
            return
        self.script_menu.delete(0, tk.END)
        try:
            if not hasattr(self, 'scripts_dir') or not self.scripts_dir:
                return
            elif not os.path.exists(self.scripts_dir):
                return
            script_files = []
            if hasattr(self, 'scripts_dir') and self.scripts_dir and os.path.exists(self.scripts_dir):
                script_files = [os.path.join(self.scripts_dir, f) for f in os.listdir(self.scripts_dir) if f.endswith('.py')]
            if not script_files:
                self.script_menu.add_command(label="(No scripts found)", state=tk.DISABLED)
            else:
                for script_path in sorted(script_files):
                    script_name = os.path.basename(script_path)
                    self.script_menu.add_command(
                        label=script_name,
                        command=lambda p=script_path: self._run_selected_script(p)
                    )
            self.script_menu.add_separator()
            self.script_menu.add_command(label="Refresh Scripts", command=self._update_script_menu)
            self.script_menu.add_command(
                label="Open Scripts Folder...",
                command=self._open_scripts_folder
            )
            if hasattr(self, 'scripts_dir') and self.scripts_dir and os.path.exists(self.scripts_dir):
                self.update_status(f"Scripts menu updated. Found {len(script_files)} scripts.")
        except Exception as e:
            logging.error(f"Error updating script menu: {e}", exc_info=True)
            messagebox.showerror("Script Menu Error", f"Could not update script menu: {e}")
            if hasattr(self, 'script_menu') and isinstance(self.script_menu, tk.Menu):
                self.script_menu.delete(0, tk.END)
                self.script_menu.add_command(label="(Error loading scripts)", state=tk.DISABLED)
                self.script_menu.add_separator()
                self.script_menu.add_command(label="Refresh Scripts", command=self._update_script_menu)
                self.script_menu.add_command(label="Open Scripts Folder...", command=self._open_scripts_folder)

    def _run_selected_script(self, script_path: str) -> None:
        try:
            script_name = os.path.basename(script_path)
            self.update_status(f"Running script: {script_name}...")
            def target():
                process = None
                try:
                    process = subprocess.Popen(['python', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=self.scripts_dir)
                    stdout, stderr = process.communicate()
                    if process.returncode == 0:
                        self.root.after(0, lambda: self.update_status(f"Script '{script_name}' finished."))
                        if stdout.strip():
                            self.root.after(0, lambda: messagebox.showinfo(f"{script_name} Output", stdout[:1000] + ("..." if len(stdout) > 1000 else "")))
                    else:
                        error_message = f"Script '{script_name}' failed."
                        if stderr:
                            error_message += f"\n\nError:\n{stderr[:500]}" + ("..." if len(stderr) > 500 else "")
                        elif stdout:
                            error_message += f"\n\nOutput:\n{stdout[:500]}" + ("..." if len(stdout) > 500 else "")
                        self.root.after(0, lambda: self.update_status(f"Script '{script_name}' failed.", error=True))
                        self.root.after(0, lambda: messagebox.showerror(f"{script_name} Error", error_message))
                except FileNotFoundError:
                    self.root.after(0, lambda: messagebox.showerror("Script Error", f"Could not find Python or script: {script_name}"))
                    self.root.after(0, lambda: self.update_status(f"Error running {script_name}: File not found.", error=True))
                except Exception as e_thread:
                    self.root.after(0, lambda: messagebox.showerror("Script Execution Error", f"Error running {script_name}:\n{e_thread}"))
                    self.root.after(0, lambda: self.update_status(f"Error running {script_name}.", error=True))
            threading.Thread(target=target, daemon=True).start()
        except Exception as e:
            logging.error(f"Error preparing to run script {script_path}: {e}")
            messagebox.showerror("Script Error", f"Could not run script {os.path.basename(script_path)}: {e}")
            self.update_status(f"Failed to start script {os.path.basename(script_path)}.", error=True)

    def _open_scripts_folder(self) -> None:
        if not hasattr(self, 'scripts_dir') or not self.scripts_dir:
            messagebox.showwarning("Error", "Scripts directory path is not configured.")
            logging.warning("Attempted to open scripts folder, but scripts_dir is not set.")
            return
        if not os.path.isdir(self.scripts_dir):
            messagebox.showwarning(
                "Error", 
                f"Scripts directory does not exist:\n{self.scripts_dir}\n\nIt should be created automatically. You can try refreshing scripts or restarting the application."
            )
            logging.warning(f"Attempted to open non-existent scripts folder: {self.scripts_dir}")
            return
        try:
            subprocess.run(['xdg-open', self.scripts_dir], check=True)
            self.update_status(f"Opened scripts folder: {self.scripts_dir}")
            logging.info(f"Opened scripts folder: {self.scripts_dir}")
        except FileNotFoundError:
            messagebox.showerror("Error", "Could not open folder. The 'xdg-open' command was not found on your system.")
            logging.error("Failed to open scripts folder: 'xdg-open' command not found.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to open scripts folder. The command 'xdg-open' exited with an error: {e}")
            logging.error(f"Failed to open scripts folder {self.scripts_dir} using xdg-open: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred while trying to open the scripts folder: {e}")
            logging.error(f"Unexpected error opening scripts folder {self.scripts_dir}: {e}")

    def _on_data_loaded(self, result: Tuple[List[List[Any]], List[str]]) -> None:
        try:
            data, headers = result
            self.current_data = data
            self.headers = headers
            self._update_data_view(data)
            self._update_column_menu()
            self.update_status(f"Loaded {len(data)} records")
        except Exception as e:
            logging.error(f"Error processing loaded data: {e}")
            messagebox.showerror("Error", f"Failed to process loaded data: {e}")

    def _on_text_loaded_callback(self, content: str) -> None:
        try:
            # Ensure content is a string; if not, it might be an error indicator or unexpected type
            if not isinstance(content, str):
                logging.error(f"Failed to load text content. Received type: {type(content)}")
                messagebox.showerror("Error", "Failed to load text content: Invalid data received.")
                self.update_status("Failed to load text.", error=True)
                if hasattr(self, 'details_text'):
                    self.details_text.delete("1.0", tk.END)
                    self.details_text.insert("1.0", "Error displaying content: Invalid data received.")
                return

            if hasattr(self, 'details_text'):
                self.details_text.delete("1.0", tk.END)
                self.details_text.insert("1.0", content)
                status_message = "Text content loaded."
                if hasattr(self, 'current_file_path') and self.current_file_path:
                    status_message += f" ({os.path.basename(self.current_file_path)})"
                self.update_status(status_message)
                if hasattr(self, 'data_table'):
                    self.data_table.delete(*self.data_table.get_children())
                self.current_data = None
                self.headers = []
                if hasattr(self, '_update_column_menu'):
                    self._update_column_menu()
            else:
                logging.error("Details text widget ('details_text') not found when trying to load text.")
                messagebox.showerror("GUI Error", "Details view component is missing. Cannot display text.")
                self.update_status("Error: Could not display text.", error=True)
        except Exception as e:
            logging.error(f"Error in _on_text_loaded_callback: {e}")
            messagebox.showerror("Error", f"An error occurred while displaying the text content: {e}")
            self.update_status("Error displaying text.", error=True)
            if hasattr(self, 'details_text'):
                try:
                    self.details_text.delete("1.0", tk.END)
                    self.details_text.insert("1.0", f"Error displaying content: {e}")
                except Exception as e_inner:
                    logging.error(f"Further error trying to update details_text with error message: {e_inner}")

    def _on_column_click(self, event: tk.Event) -> None:
        try:
            region = self.data_table.identify_region(event.x, event.y)
            if region == "heading":
                column_id_str = self.data_table.identify_column(event.x)
                # column_id_str is like '#1', '#2', etc. We need the actual header text.
                # The Treeview column identifiers are usually the header texts themselves if set during setup.
                # Or, they can be numeric strings if not explicitly set.
                # Let's assume header texts are used as column identifiers.
                # If not, this needs adjustment based on how columns are added.
                
                # Find the header text corresponding to the clicked column
                # This is a bit indirect. A better way would be to store header texts with their column IDs.
                clicked_header = ""
                for col_header in self.data_table["columns"]:
                    # Check if the x-coordinate of the event is within the column's bounds
                    # This is a more robust way to identify the clicked column header
                    x, y, width, height = self.data_table.bbox(item=None, column=col_header)
                    if x <= event.x < x + width:
                        clicked_header = col_header
                        break
                
                if not clicked_header:
                    logging.warning("Could not identify clicked column header.")
                    return

                # Get current items from the Treeview
                items = [(self.data_table.set(item_id, clicked_header), item_id) for item_id in self.data_table.get_children('')]

                # Determine sort direction
                if not hasattr(self, "_last_sort_column") or self._last_sort_column != clicked_header:
                    self._last_sort_column = clicked_header
                    self._last_sort_reverse = False
                else:
                    self._last_sort_reverse = not self._last_sort_reverse

                # Sort items
                # Attempt to sort numerically if possible, otherwise sort as strings
                try:
                    items.sort(key=lambda x: float(x[0]), reverse=self._last_sort_reverse)
                except ValueError:
                    items.sort(key=lambda x: str(x[0]).lower(), reverse=self._last_sort_reverse)


                # Re-insert items in sorted order
                for index, (value, item_id) in enumerate(items):
                    self.data_table.move(item_id, '', index)

                # Update column header to show sort direction (optional visual cue)
                for col_header in self.data_table["columns"]:
                    current_heading = self.data_table.heading(col_header, "text")
                    # Remove old sort indicators
                    current_heading = current_heading.replace(" \u25B2", "").replace(" \u25BC", "")
                    if col_header == clicked_header:
                        indicator = " \u25B2" if not self._last_sort_reverse else " \u25BC" # Up/Down arrows
                        self.data_table.heading(col_header, text=current_heading + indicator)
                    else:
                        self.data_table.heading(col_header, text=current_heading)


        except Exception as e:
            logging.error(f"Error handling column click: {e}")

    def _apply_filter(
        self, data: List[List[Any]], filter_text: str, column_name: str = "All Columns"
    ) -> List[List[Any]]:
        filter_text = filter_text.lower().strip()
        if not filter_text:
            return data # No filter text, return original data

        filtered_data = []
        
        # Determine the index of the column to filter
        column_index = -1
        if column_name != "All Columns":
            try:
                column_index = self.headers.index(column_name)
            except ValueError:
                logging.warning(f"Filter column '{column_name}' not found in headers.")
                return data # Column not found, return original data

        for row in data:
            if column_index != -1: # Filter specific column
                if column_index < len(row): # Ensure row has this column
                    cell_value = str(row[column_index]).lower()
                    if filter_text in cell_value:
                        filtered_data.append(row)
            else: # Filter all columns
                for cell in row:
                    if filter_text in str(cell).lower():
                        filtered_data.append(row)
                        break # Found in one cell, add row and move to next row
        return filtered_data

    def _update_groups_view(self) -> None:
        """Populates the groups list with unique group names from the data."""
        self.logger.debug("Updating groups view")
        try:
            if self.data_handler and hasattr(self.data_handler, 'get_all_data'):
                all_data = self.data_handler.get_all_data()
                if not all_data:
                    self.logger.warning("No data available to update groups view.")
                    self.groups_list.delete(0, tk.END)
                    return

                groups = sorted(list(set(item.get("group", "Uncategorized") for item in all_data if item.get("group"))))
                if not groups:
                    groups = ["Uncategorized"] # Ensure there's at least one entry if data exists but no groups
                
                self.groups_list.delete(0, tk.END)
                for group_name in groups:
                    self.groups_list.insert(tk.END, group_name)
                self.logger.info(f"Groups view updated with {len(groups)} groups.")
            else:
                self.logger.error("Data handler not available or does not have get_all_data method.")
                self.groups_list.delete(0, tk.END)
        except Exception as e:
            self.logger.error(f"Error updating groups view: {e}")
            self.show_status_message(f"Error updating groups: {e}", error=True)
            # Optionally, re-raise if it's critical, or handle more gracefully
            # raise

    def _on_group_select(self, event=None) -> None:
        """Handles group selection events to filter the data table."""
        self.logger.debug("Group selection changed")
        try:
            selected_indices = self.groups_list.curselection()
            if not selected_indices:
                self.logger.debug("No group selected, clearing filter.")
                # self._apply_filter(filter_text="", filter_column=None) # Clear filter if no group selected
                # Or, display all items if that's the desired behavior
                self.populate_data_table(self.data_handler.get_all_data() if self.data_handler else [])
                self.show_status_message("Filter cleared. Showing all items.")
                return

            selected_group = self.groups_list.get(selected_indices[0])
            self.logger.info(f"Group selected: {selected_group}")

            if selected_group == "Uncategorized" and not any(item.get("group") for item in self.data_handler.get_all_data()):
                 # If "Uncategorized" is selected and there are no actual groups, show all data
                self.populate_data_table(self.data_handler.get_all_data())
                self.show_status_message("Showing all items (no specific groups defined).")
                return
            
            # Apply filter using the group name. Assuming "group" is a column in your data.
            # The _apply_filter method might need adjustment if it doesn't directly support this.
            # For now, let's assume direct filtering by the "group" key.
            if self.data_handler:
                all_data = self.data_handler.get_all_data()
                if selected_group == "Uncategorized":
                    # Items with no group or group explicitly set to "Uncategorized"
                    # This logic might need refinement based on how "Uncategorized" is handled in data
                    filtered_data = [item for item in all_data if not item.get("group") or item.get("group") == "Uncategorized"]
                else:
                    filtered_data = [item for item in all_data if item.get("group") == selected_group]
                
                self.populate_data_table(filtered_data)
                self.show_status_message(f"Filtered by group: {selected_group}. {len(filtered_data)} items found.")
                self._clear_filter_input() # Clear the text filter input
            else:
                self.logger.warning("Data handler not available for group filtering.")
        except Exception as e:
            self.logger.error(f"Error in _on_group_select: {e}")
            self.show_status_message(f"Error selecting group: {e}", error=True)
            # raise # Consider if re-raising is appropriate

    def _on_data_select(self, event: tk.Event = None) -> None:
        """Handles data selection events to update the details view."""
        try:
            if not hasattr(self, "data_table"):
                return

            selected_item_id = self.data_table.focus()  # Get the ID of the selected/focused item
            if selected_item_id:
                item_data = self.data_table.item(selected_item_id)
                # item_data is a dictionary like {'text': 'iid', 'image': '', 'values': [], 'open': 0, 'tags': ''}
                # We need to pass this dictionary to _update_details_view
                self._update_details_view(item_data)
            else:
                # No item selected, clear details view or show a default message
                self._update_details_view(None) 
        except Exception as e:
            logging.error(f"Error in _on_data_select: {e}")
            # Optionally, update status or show an error message
            if hasattr(self, "details_text"):
                self.details_text.delete("1.0", tk.END)
                self.details_text.insert("1.0", "Error displaying details after selection.")

    def _on_apply_filter(self) -> None:
        try:
            filter_text = self.filter_var.get()
            column_name = self.column_var.get() # This is the header text of the column

            # self.current_data should hold the original, unfiltered data
            if not hasattr(self, 'current_data') or not self.current_data:
                logging.warning("No data loaded to filter.")
                return

            # Apply the filter
            # The _apply_filter method expects List[List[Any]]
            # Ensure self.current_data matches this structure
            filtered_data = self._apply_filter(self.current_data, filter_text, column_name)
            
            # Update the data view with filtered data
            self._update_data_view(filtered_data) # This method should handle repopulating the Treeview
            self.update_status(f"Filtered data. Displaying {len(filtered_data)} records.")

        except Exception as e:
            logging.error(f"Error applying filter: {e}")
            messagebox.showerror("Error", f"Failed to apply filter: {e}")

    def clear_filter(self) -> None:
        try:
            # Clear filter inputs
            self.filter_var.set("")
            self.column_var.set("All Columns")

            # Clear group selection if its a filter group
            selection = self.group_list.selection()
            if selection:
                item_id = selection[0]
                group_name = self.group_list.item(item_id)["text"]
                if group_name.startswith("Filter"):
                    self.group_list.selection_remove(item_id)
                    # Show full data
                    self._update_data_view(self.current_data)
                else:
                    # Keep non-filter group selected
                    if group_name in self.groups:
                        self._update_data_view(self.groups[group_name])
            else:
                # Show full data
                self._update_data_view(self.current_data)

            self.update_status("Filters cleared")

        except Exception as e:
            logging.error(f"Error clearing filter: {e}")

    def _refresh_views(self) -> None:
        try:
            # Update status
            self.update_status("Refreshing views...")

            # Refresh data view with current data
            if hasattr(self, "current_data") and self.current_data:
                self._update_data_view(self.current_data)

            # Refresh groups view
            if hasattr(self, "groups") and self.groups:
                self._update_groups_view()

            # Update script menu
            # if hasattr(self, "_update_script_menu"):
            #     self._update_script_menu()

            # Update column menu
            if hasattr(self, "_update_column_menu"):
                self._update_column_menu()

            self.update_status("Views refreshed")

        except Exception as e:
            logging.error(f"Error refreshing views: {e}")
            self.update_status(f"Error refreshing views: {e}")

    def _update_data_view(self, data: List[Any] = None) -> None:
        try:
            self.data_table.delete(*self.data_table.get_children())

            data = data if data is not None else self.current_data
            if not data:
                return

            # Configure columns
            columns = [f"col{i}" for i in range(len(self.headers))]
            self.data_table["columns"] = columns

            # Hide the first empty column
            self.data_table["show"] = "headings"

            # Set column headers
            for col, header in zip(columns, self.headers):
                self.data_table.heading(col, text=str(header))
                self.data_table.column(col, width=100)  # Fixed width

            # Add the data rows
            for i, row in enumerate(data):
                self.data_table.insert("", "end", iid=str(i), values=row)

            # Update column menu with current headers
            self._update_column_menu()

            # Apply current column visibility settings
            self._apply_column_visibility()

        except Exception as e:
            logging.error(f"Error updating data view: {e}")
            raise

    def _update_column_menu(self) -> None:
        try:
            if not hasattr(self, "column_visibility_menu") or not hasattr(
                self, "headers"
            ):
                return

            # Clear existing menu items
            self.column_visibility_menu.delete(0, "end")

            # Initialize column visibility tracking if needed
            if not hasattr(self, "column_visibility"):
                self.column_visibility = {}

            # Add menu items for each column
            for i, header in enumerate(self.headers):
                # Default to visible if not already tracked
                if header not in self.column_visibility:
                    self.column_visibility[header] = True

                # Create checkable menu item
                var = tk.BooleanVar(value=self.column_visibility[header])
                self.column_visibility_menu.add_checkbutton(
                    label=header,
                    variable=var,
                    command=lambda h=header, v=var: self._toggle_column_visibility(
                        h, v
                    ),
                )

        except Exception as e:
            logging.error(f"Error updating column menu: {e}")

    def _apply_column_visibility(self) -> None:
        try:
            if (
                not hasattr(self, "data_table")
                or not hasattr(self, "column_visibility")
                or not hasattr(self, "headers")
            ):
                return

            # Get current table columns
            columns = self.data_table["columns"]
            if not columns:
                return

            # Apply visibility settings
            for i, header in enumerate(self.headers):
                if i < len(columns):
                    col_id = columns[i]
                    if (
                        header in self.column_visibility
                        and not self.column_visibility[header]
                    ):
                        self.data_table.column(
                            col_id, width=0, minwidth=0
                        )  # Hide column
                    else:
                        self.data_table.column(
                            col_id, width=100, minwidth=50
                        )  # Show column

        except Exception as e:
            logging.error(f"Error applying column visibility: {e}")

    def _toggle_column_visibility(self, header: str, var: tk.BooleanVar) -> None:
        try:
            if not hasattr(self, "column_visibility"):
                self.column_visibility = {}

            # Update visibility state
            self.column_visibility[header] = var.get()

            # Apply the visibility change
            self._apply_column_visibility()

        except Exception as e:
            logging.error(f"Error toggling column visibility for {header}: {e}")

    def _on_treeview_configure(
        self, event: tk.Event, original_widths: Dict[int, int]
    ) -> None:
        try:
            if not hasattr(self, "last_width"):
                self.last_width = event.width
                return

            # Only adjust if width actually changed
            if event.width == self.last_width:
                return

            self.last_width = event.width
            available_width = event.width - 20  # Account for scrollbar and borders

            # Calculate total of original widths
            total_original = sum(original_widths.values())

            if total_original > 0:
                # Scale each column proportionally
                scale_factor = available_width / total_original
                min_col_width = 50

                for i, original_width in enumerate(original_widths.values()):
                    # Calculate new width, ensuring it's not less than min_col_width
                    new_width = max(int(original_width * scale_factor), min_col_width)
                    # Apply new width to column (assuming self.data_table exists and has columns)
                    if hasattr(self, "data_table") and i < len(self.data_table["columns"]):
                        col_id = self.data_table["columns"][i]
                        self.data_table.column(col_id, width=new_width)

        except Exception as e:
            logging.error(f"Error handling treeview configure: {e}")
            # Dont raise - we dont want to crash on resize events

    # Event handler methods for menu operations
    # def _on_load_data(self) -> None:
    #     # This method will be replaced or refactored by _on_open_file
    #     try:
    #         # ... (original _on_load_data content, to be reviewed/merged)
    #         file_path = filedialog.askopenfilename(
    #             defaultextension=".csv",
    #             filetypes=[
    #                 ("CSV files", "*.csv"),
    #                 ("Excel files", "*.xlsx *.xls"),
    #                 ("All files", "*.*"),
    #             ],
    #         )
    #         if file_path:
    #             self.current_file_path = file_path
    #             self.run_in_background(
    #                 self._load_data_background, file_path, callback=self._on_data_loaded
    #             )
    #     except Exception as e:
    #         logging.error(f"Error in _on_load_data: {e}")
    #         messagebox.showerror("Error", f"Failed to open data file: {e}")

    # def _on_import_data(self) -> None: # This will be superseded by _on_open_file
    #     # ... (original _on_import_data content, to be reviewed/merged)
    #     pass

    # def _on_import_data(self) -> None: # This will be superseded by _on_open_file
    #     # ... (original _on_import_data content, to be reviewed/merged)
    #     pass

    # def _on_load_text_content(self) -> None: # This will be superseded by _on_open_file
    #     # ... (original _on_load_text_content content, to be reviewed/merged)
    #     try:
    #         file_path = filedialog.askopenfilename(
    #             defaultextension=".txt",
    #             filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
    #         )
    #         if file_path:
    #             self.current_text_file_path = file_path # Store path if needed
    #             self.run_in_background(
    #                 self._load_text_background, file_path, callback=self._on_text_loaded
    #             )
    #     except Exception as e:
    #         logging.error(f"Error loading text content: {e}")
    #         messagebox.showerror("Error", f"Failed to load text content: {e}")

    # def _on_save(self) -> None: # This will be superseded by _on_save_file
    #     # ... (original _on_save content, to be reviewed/merged)
    #     pass

    # def _on_export(self) -> None: # This will be superseded by _on_save_file
    #     # ... (original _on_export content, to be reviewed/merged)
    #     pass

    def _on_open_file(self) -> None:
        """Handles opening different file types."""
        try:
            file_types = [
                ("Supported Files", ("*.csv", "*.xlsx", "*.xls", "*.txt", "*.py", "*.md")),
                ("Data Files", ("*.csv", "*.xlsx", "*.xls")),
                ("Text Files", ("*.txt", "*.py", "*.md")),
                ("All Files", "*.*"),
            ]
            file_path = filedialog.askopenfilename(
                defaultextension=".txt", # Default to .txt if no specific type chosen
                filetypes=file_types,
            )

            if file_path:
                self.current_file_path = file_path
                _, file_extension = os.path.splitext(file_path)
                file_extension = file_extension.lower()

                if file_extension in [".csv", ".xlsx", ".xls"]:
                    self.update_status(f"Opening data file: {os.path.basename(file_path)}...")
                    # Clear previous data/text specific states
                    self.current_data = None
                    self.headers = []
                    if hasattr(self, 'details_text'):
                        self.details_text.delete("1.0", tk.END) # Clear details view
                    self.run_in_background(
                        self._load_data_background, file_path, callback=self._on_data_loaded
                    )
                elif file_extension in [".txt", ".py", ".md"]: # Added .md
                    self.update_status(f"Opening text file: {os.path.basename(file_path)}...")
                    # Clear previous data/text specific states
                    self.current_data = None
                    self.headers = []
                    if hasattr(self, 'data_table'):
                        self.data_table.delete(*self.data_table.get_children()) # Clear data table
                    self.run_in_background(
                        self._load_text_background, file_path, callback=self._on_text_loaded_callback # Corrected callback
                    )
                else: # Ensure this 'else' has the same indentation as the 'elif above
                    self.update_status(f"Unsupported file type: {file_extension}", error=True)
                    messagebox.showwarning(
                        "Unsupported File Type",
                        f"The file type '{file_extension}' is not directly supported for automatic display. You can try opening it as 'All Files'.",
                    )
        except Exception as e:
            logging.error(f"Error in _on_open_file: {e}")
            messagebox.showerror("Error", f"Failed to open file: {e}")

    def _on_save_file(self) -> None:
        """Handles saving data or text content based on active view."""
        try:
            content_to_save = None  # Will be 'data' or 'text'
            save_action = None

            # Check if Data View has substantial content
            if hasattr(self, 'current_data') and self.current_data and hasattr(self, 'headers'):
                # Make sure current_data is not just empty lists or similar
                if any(self.current_data): 
                    content_to_save = 'data'

            # If no substantial data content, check Details View
            if not content_to_save and hasattr(self, 'details_text'):
                details_content = self.details_text.get("1.0", tk.END).strip()
                # Avoid saving placeholder or error text
                placeholders = [
                    "Select an item from the table above to view details here.",
                    "Error displaying details after selection.",
                    "No details available for this item.",
                    "Error displaying details:" # Partial match for error messages
                ]
                if details_content and not any(details_content.startswith(p) for p in placeholders) and details_content != "Error displaying details.":
                    content_to_save = 'text'
                    current_text_content = self.details_text.get("1.0", tk.END) # Get full content with EOL

            if content_to_save == 'data':
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[
                        ("CSV files", "*.csv"),
                        ("Excel files", "*.xlsx"),
                        ("All files", "*.*"),
                    ],
                    title="Save Data As"
                )
                if file_path:
                    _, file_extension = os.path.splitext(file_path)
                    file_extension = file_extension.lower()
                    if file_extension == ".csv":
                        self.update_status(f"Saving data to CSV: {os.path.basename(file_path)}...")
                        self.run_in_background(self._save_csv_background, file_path, self.current_data, self.headers)
                    elif file_extension == ".xlsx":
                        self.update_status(f"Exporting data to Excel: {os.path.basename(file_path)}...")
                        self.run_in_background(self._export_to_excel_background, file_path, self.current_data, self.headers)
                    else:
                        messagebox.showwarning("Unsupported Type", f"Cannot save data to '{file_extension}'. Please use .csv or .xlsx.")
                        self.update_status(f"Save cancelled for {os.path.basename(file_path)}", error=True)

            elif content_to_save == 'text':
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[
                        ("Text files", "*.txt"),
                        ("Python files", "*.py"),
                        ("Markdown files", "*.md"),
                        ("All files", "*.*"),
                    ],
                    title="Save Text As"
                )
                if file_path:
                    self.update_status(f"Saving text to: {os.path.basename(file_path)}...")
                    self.run_in_background(self._save_text_content_background, file_path, current_text_content)
            
            else:
                messagebox.showinfo("Nothing to Save", "There is no active content to save.")
                self.update_status("Nothing to save.")

        except Exception as e:
            logging.error(f"Error in _on_save_file: {e}")
            messagebox.showerror("Save Error", f"An unexpected error occurred during save: {e}")
            self.update_status("Save operation failed", error=True)

    def _save_text_content_background(self, file_path: str, content: str) -> None:
        """Saves text content to a file in a background thread."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.root.after(0, lambda: self.update_status(f"Text content saved to {os.path.basename(file_path)}"))
            self.root.after(0, lambda: setattr(self, 'current_file_path', file_path)) # Update current file path
            # Optionally, if you maintain a separate current_text_file_path:
            # self.root.after(0, lambda: setattr(self, 'current_text_file_path', file_path))
        except Exception as e:
            logging.error(f"Error saving text content to {file_path}: {e}")
            self.root.after(0, lambda: messagebox.showerror("Save Error", f"Failed to save text file: {e}"))
            self.root.after(0, lambda: self.update_status(f"Error saving text to {os.path.basename(file_path)}", error=True))

    def _save_csv_background(self, file_path: str, data: List[List[Any]], headers: List[str]) -> None:
        """Saves data to a CSV file in a background thread."""
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if headers:
                    writer.writerow(headers)
                writer.writerows(data)
            self.root.after(0, lambda: self.update_status(f"Data saved to CSV: {os.path.basename(file_path)}"))
            self.root.after(0, lambda: setattr(self, 'current_file_path', file_path)) # Update current file path
        except Exception as e:
            logging.error(f"Error saving CSV to {file_path}: {e}")
            self.root.after(0, lambda: messagebox.showerror("Save Error", f"Failed to save CSV file: {e}"))
            self.root.after(0, lambda: self.update_status(f"Error saving CSV to {os.path.basename(file_path)}", error=True))

    def _export_to_excel_background(self, file_path: str, data: List[List[Any]], headers: List[str]) -> None:
        """Exports data to an Excel file in a background thread."""
        try:
            if not PANDAS_AVAILABLE:
                self.root.after(0, lambda: messagebox.showerror("Export Error", "Pandas library is not available for Excel export."))
                self.root.after(0, lambda: self.update_status("Excel export failed: Pandas missing", error=True))
                return

            df = pd.DataFrame(data, columns=headers if headers else None)
            df.to_excel(file_path, index=False)
            self.root.after(0, lambda: self.update_status(f"Data exported to Excel: {os.path.basename(file_path)}"))
            self.root.after(0, lambda: setattr(self, 'current_file_path', file_path)) # Update current file path
        except Exception as e:
            logging.error(f"Error exporting to Excel: {e}")
            self.root.after(0, lambda: messagebox.showerror("Export Error", f"Failed to export Excel file: {e}"))
            self.root.after(0, lambda: self.update_status(f"Error exporting Excel to {os.path.basename(file_path)}", error=True))

    def _load_data_background(
        self, file_path: str
    ) -> None:
        """Load data from a file in a background thread."""
        try:
            logger.info(f"Attempting to load data from {file_path}")
            if not PANDAS_AVAILABLE:
                raise ImportError("Pandas library is not available. Please install it to load data.")
            _, file_extension = os.path.splitext(file_path)
            file_extension = file_extension.lower()
            if file_extension == ".csv":
                try:
                    data = pd.read_csv(file_path)
                except Exception as e:
                    logger.error(f"Error reading CSV file {file_path}: {e}")
                    raise ValueError(f"Failed to read CSV file: {e}") from e
            elif file_extension in [".xlsx", ".xls"]:
                try:
                    data = pd.read_excel(file_path, engine=None)
                except Exception as e_default:
                    logger.warning(f"Failed to load Excel {file_path} with default engine: {e_default}")
                    if file_extension == ".xlsx":
                        try:
                            logger.info(f"Trying to load Excel {file_path} with openpyxl engine")
                            data = pd.read_excel(file_path, engine="openpyxl")
                        except Exception as e_openpyxl:
                            logger.error(f"Error reading Excel file {file_path} with openpyxl: {e_openpyxl}")
                            raise ValueError(f"Failed to read Excel file (openpyxl): {e_openpyxl}") from e_openpyxl
                    elif file_extension == ".xls":
                        try:
                            logger.info(f"Trying to load Excel {file_path} with xlrd engine")
                            data = pd.read_excel(file_path, engine="xlrd")
                        except Exception as e_xlrd:
                            logger.error(f"Error reading Excel file {file_path} with xlrd: {e_xlrd}")
                            raise ValueError(f"Failed to read Excel file (xlrd): {e_xlrd}") from e_xlrd
                    else:
                        raise ValueError(f"Unsupported Excel file extension: {file_extension}")
            elif file_extension == ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]
                    if not lines:
                        data = pd.DataFrame()
                    else:
                        data = pd.DataFrame(lines, columns=["text_data"])
                logger.info(f"Successfully loaded text file {file_path} into a DataFrame.")
            else:
                logger.error(f"Unsupported file type: {file_extension} for file {file_path}")
                raise ValueError(f"Unsupported file type: {file_extension}")
            self.data_frame = data
            self.root.event_generate("<<DataLoaded>>")
            logger.info(f"Successfully loaded data from {file_path}")
            # Return data and headers for the callback
            if self.data_frame is not None:
                data_list = self.data_frame.values.tolist()
                headers_list = self.data_frame.columns.tolist()
                return data_list, headers_list
            return None, None
        except Exception as e:
            logger.exception(f"An error occurred during data loading from {file_path}")
            self.background_exception = e
            self.root.event_generate("<<TaskFailed>>")

    def _load_text_background(self, file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logging.error(f"Error loading text from {file_path}: {e}")
            raise

    def _export_to_excel(self, file_path: str, data: List[List[Any]]) -> None:
        try:
            if not PANDAS_AVAILABLE:
                raise ImportError("pandas required for Excel export")
            if data and hasattr(self, "headers"):
                df = pd.DataFrame(data, columns=self.headers)
                df.to_excel(file_path, index=False)
                self.root.after(0, lambda: self.update_status(f"Exported to {file_path}"))
            else:
                raise ValueError("No data to export")
        except Exception as e:
            logging.error(f"Error exporting to Excel: {e}")
            self.root.after(0, lambda: messagebox.showerror("Export Error", str(e)))

    def _save_to_file(self, file_path: str, data: List[List[Any]]) -> None:
        try:
            self.update_status(f"Saving to {file_path}...")
            if PANDAS_AVAILABLE and file_path.endswith(".xlsx"):
                df = pd.DataFrame(data, columns=self.headers if hasattr(self, 'headers') else None)
                df.to_excel(file_path, index=False)
            elif file_path.endswith(".csv"):
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    if hasattr(self, 'headers'):
                        writer.writerow(self.headers)
                    writer.writerows(data)
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    if hasattr(self, 'headers'):
                        f.write(",".join(map(str, self.headers)) + "\n")
                    for row in data:
                        f.write(",".join(map(str, row)) + "\n")
            self.update_status(f"Saved to {file_path}")
        except Exception as e:
            logging.error(f"Error saving to file {file_path}: {e}")
            err_msg = str(e)
            self.root.after(0, lambda err=err_msg: messagebox.showerror("Save Error", err))
            self.update_status(f"Error saving to {file_path}")
    
    def load_default_data(self) -> None:
        """Placeholder for loading default data."""
        logging.info("load_default_data called, but not implemented yet.")
        # Example:
        # default_data_path = "default_data.csv"
        # if os.path.exists(default_data_path):
        #     self.update_status(f"Loading default data from {default_data_path}...")
        #     self.run_in_background(
        #         self._load_data_background, default_data_path, callback=self._on_data_loaded
        #     )
        # else:
        #     self.update_status("No default data file found.")
        pass


# Add a main execution block to launch the GUI directly if this file is run
def main():
    """Main entry point for launching the Crew GUI application."""
    try:
        root = tk.Tk()
        app = CrewGUI(root)
        root.mainloop()
    except Exception as e:
        logging.critical(f"Failed to launch Crew GUI: {e}", exc_info=True)
        try:
            messagebox.showerror("Fatal Error", f"Could not start the application: {e}")
        except tk.TclError:
            print(f"FATAL ERROR: Could not start the application: {e}")

if __name__ == "__main__":
    main()
