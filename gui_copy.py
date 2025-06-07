#!/usr/bin/python3

# region Imports - Core Libraries
import csv  # CSV file handling
import glob  # File pattern matching
import importlib.util  # Dynamic module importing
import json  # JSON file handling for caching
import logging  # Application logging
import os  # Operating system interface
import re  # Needed for TTS text preprocessing
import subprocess  # Process execution
import sys  # System-specific parameters
import threading  # Background thread support
import time  # Time-related functions for caching
import tkinter as tk  # Core GUI framework
from tkinter import filedialog  # File dialog functionality

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
        try:
            self.root = root  # Assign self.root immediately
            self.root.title("Crew Manager")  # Set title early

            # Initialize TTS engine if available
            if TTS_AVAILABLE:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty("rate", 150)  # Adjust rate
                self.tts_engine.setProperty("volume", 0.8)  # Reduce volume slightly
                self.tts_engine.setProperty("voice", "english")  # Default to English voice
            else:
                self.tts_engine = None

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
            tts_menu.add_command(label="Read Selection (Ctrl+Shift+R)", command=self._read_selected_item)
            tts_menu.add_command(label="Read All Details (Ctrl+Shift+A)", command=self._read_all_details)
            tts_menu.add_command(label="Read Status (Ctrl+Shift+S)", command=self._read_status)
            tts_menu.add_command(label="Read Item Type (Ctrl+Shift+T)", command=self._read_item_type)
            tts_menu.add_separator()
            tts_menu.add_command(label="Stop Reading", command=self._stop_reading)
            tts_menu.add_separator()
            tts_menu.add_command(label="Save Speech to File...", command=self._save_speech_to_file)
            tts_menu.add_command(label="Speech Settings...", command=self._show_speech_settings)

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

            # TTS keyboard shortcuts
            if TTS_AVAILABLE:
                self.root.bind("<Control-Shift-R>", lambda event: self._read_selected_item())
                self.root.bind("<Control-Shift-A>", lambda event: self._read_all_details())
                self.root.bind("<Control-Shift-S>", lambda event: self._read_status())
                self.root.bind("<Control-Shift-T>", lambda event: self._read_item_type())

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
            task: Tuple[Callable, tuple, Optional[Callable]] = self.task_queue.get()
            func, args, callback = task
            try:
                result = func(*args)
                if callback:
                    self.root.after(0, callback, result)
            except Exception as e:
                logging.error(f"Background task failed: {e}")
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
                logging.FileHandler("crew_gui.log"), # Log to a file
                logging.StreamHandler() # Also log to console
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
        # Configure root window
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        # Main container
        self.main_frame = ttk.Frame(self.root, padding="5")
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        # Configure root window weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Configure main frame weights
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Create PanedWindow for resizable divider between left and right sections
        self.paned_window = ttk.PanedWindow(self.main_frame, orient="horizontal")
        self.paned_window.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Left panel with fixed narrow width
        self.left_frame = ttk.Frame(self.paned_window, width=280)
        self.left_frame.grid_propagate(False)  # Prevent frame from shrinking

        # Right panel
        self.right_frame = ttk.Frame(self.paned_window)

        # Add frames to paned window
        self.paned_window.add(self.left_frame, weight=0)  # Left: narrow, not expandable
        self.paned_window.add(self.right_frame, weight=1)  # Right: expandable

        # Split left panel into Controls/Groups/Filters
        self.paned_left = ttk.PanedWindow(self.left_frame, orient="vertical")
        self.paned_left.grid(row=0, column=0, sticky="nsew")
        # Ensure the left_frame fills the area for its PanedWindow
        self.left_frame.grid_rowconfigure(0, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

        # Split right panel into Data/Details
        self.paned_right = ttk.PanedWindow(self.right_frame, orient="vertical")
        self.paned_right.grid(row=0, column=0, sticky="nsew")
        # Ensure the right_frame fills the area for its PanedWindow
        self.right_frame.grid_rowconfigure(0, weight=1)
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
            # Create frame with border effect
            status_frame = ttk.Frame(self.root, relief=tk.GROOVE, borderwidth=1)
            status_frame.grid(row=1, column=0, sticky="ew", padx=2, pady=(2, 2))

            # Status message
            self.status_var = tk.StringVar(value="Ready")
            self.status_bar = ttk.Label(
                status_frame,
                textvariable=self.status_var,
                padding=(5, 2),
                anchor=tk.W,  # Left align text
            )
            self.status_bar.pack(fill=tk.X, expand=True)

            # Configure status bar layout
            self.root.grid_rowconfigure(1, weight=0)
            self.root.grid_columnconfigure(0, weight=1)

            # Add tooltip
            self.status_tooltip = None
            self.status_bar.bind("<Enter>", self._show_status_tooltip)
            self.status_bar.bind("<Leave>", self._hide_status_tooltip)

        except Exception as e:
            logging.error(f"Failed to create status bar: {e}")
            raise

    def update_status(self, message: str) -> None:
        try:
            if not message:
                message = "Ready"
            self.status_var.set(message)
            self.root.update_idletasks()
        except Exception as e:
            logging.error(f"Failed to update status: {e}")

    def _show_status_tooltip(self, event: tk.Event) -> None:
        msg = self.status_var.get()
        if len(msg) > 50:  # Only show for long messages
            # Create a simple tooltip using a Toplevel window
            self.status_tooltip = tk.Toplevel(self.root)
            self.status_tooltip.wm_overrideredirect(True)

            # Position tooltip near the cursor
            x = event.x_root + 10
            y = event.y_root + 10
            self.status_tooltip.geometry(f"+{x}+{y}")

            # Create tooltip content
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
                # Tooltip already destroyed
                self.status_tooltip = None

    def create_control_section(self) -> None:
        try:
            control_frame = ttk.LabelFrame(self.paned_left, text="Controls", padding="5")
            self.paned_left.add(control_frame, weight=0)

            # Add control buttons
            ttk.Button(
                control_frame, text="Open...", command=self._on_open_file  # Updated
            ).pack(fill="x", pady=2)
            ttk.Button(
                control_frame, text="Save...", command=self._on_save_file  # Updated
            ).pack(fill="x", pady=2)
        except Exception as e:
            logging.error(f"Failed to create control section: {e}")
            raise

    def create_group_section(self) -> None:
        try:
            group_frame = ttk.LabelFrame(self.paned_left, text="Groups", padding="5")
            self.paned_left.add(group_frame, weight=1)

            # Group list
            self.group_list = ttk.Treeview(group_frame, selectmode="browse", height=10)
            self.group_list.pack(fill="both", expand=True)

            # Create right-click menu
            self.group_menu = tk.Menu(self.group_list, tearoff=0)
            self.group_menu.add_command(
                label="Delete", command=self._delete_selected_group
            )

            # Bind right-click to show menu
            self.group_list.bind("<Button-3>", self._show_group_menu)

            # Scrollbar for group list
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
            # Select item under cursor
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
                messagebox.showwarning("Warning", "No group selected")
                return

            item_id = selection[0]
            group_name = self.group_list.item(item_id)["text"]

            # Confirm deletion
            if messagebox.askyesno("Confirm Delete", f"Delete group '{group_name}'?"):
                # Remove from groups dictionary
                if group_name in self.groups:
                    del self.groups[group_name]

                # Remove from treeview
                self.group_list.delete(item_id)

                # If this was the currently displayed group, show all data
                self._update_data_view(self.current_data)

                self.update_status(f"Deleted group: {group_name}")

        except Exception as e:
            logging.error(f"Error deleting group: {e}")
            messagebox.showerror("Error", f"Failed to delete group: {e}")

    def create_filter_section(self) -> None:
        try:
            filter_frame = ttk.LabelFrame(self.paned_left, text="Filters", padding="5")
            self.paned_left.add(filter_frame, weight=0)
            self.filter_frame = filter_frame

            # Filter controls
            self.filter_var = tk.StringVar(value="")
            self.column_var = tk.StringVar(value="All Columns")

            # Column selection dropdown
            self.column_menu = ttk.Combobox(
                filter_frame, textvariable=self.column_var, state="readonly"
            )
            self.column_menu.pack(fill="x", pady=2)

            # Filter entry
            self.filter_entry_widget = ttk.Entry(filter_frame, textvariable=self.filter_var) # Store the widget
            self.filter_entry_widget.pack(fill="x", pady=2)
            
            ttk.Button(
                filter_frame, text="Apply Filter", command=self._on_apply_filter
            ).pack(fill="x", pady=2)
        except Exception as e:
            logging.error(f"Failed to create filter section: {e}")
            raise

    def create_data_section(self) -> None:
        try:
            data_frame = ttk.LabelFrame(self.paned_right, text="Data View", padding="5")
            self.paned_right.add(data_frame, weight=3)

            # Create container frame for table and scrollbars
            table_frame = ttk.Frame(data_frame)
            table_frame.grid(row=0, column=0, sticky="nsew")

            # Configure frame weights
            data_frame.grid_rowconfigure(0, weight=1)
            data_frame.grid_columnconfigure(0, weight=1)

            table_frame.grid_rowconfigure(0, weight=1)
            table_frame.grid_columnconfigure(0, weight=1)

            # Create scrolled frame to contain treeview
            self.data_table = ttk.Treeview(
                table_frame, show="headings", selectmode="browse"
            )

            # Create scrollbars
            y_scroll = ttk.Scrollbar(
                table_frame, orient="vertical", command=self.data_table.yview
            )
            x_scroll = ttk.Scrollbar(
                table_frame, orient="horizontal", command=self.data_table.xview
            )

            # Configure treeview to use scrollbars
            self.data_table.configure(
                yscrollcommand=y_scroll.set,
                xscrollcommand=x_scroll.set,
                style="Treeview",
            )

            # Bind sorting event
            self.data_table.bind("<Button-1>", self._on_column_click)

            # Grid layout with scrollbars
            self.data_table.grid(row=0, column=0, sticky="nsew")
            y_scroll.grid(row=0, column=1, sticky="ns")
            x_scroll.grid(row=1, column=0, sticky="ew")

            # Configure style to ensure proper scrolling
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
                self.paned_right, text="Details View", padding="5"
            )
            self.paned_right.add(details_frame, weight=1)

            # Create container frame for text and scrollbar
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
            logging.error(f"Failed to create details section: {e}") # Added logging for this exception
            # Consider re-raising or handling more gracefully if this is critical
            raise # Uncomment if this error should halt execution

    def _setup_details_tts(self) -> None:
        if not TTS_AVAILABLE:
            return

        try:
            # Create context menu for TTS
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(
                label="Read Selection", command=self._read_selection
            )
            context_menu.add_command(label="Read All", command=self._read_all_details)
            context_menu.add_separator()
            context_menu.add_command(label="Stop Reading", command=self._stop_reading)

            # Bind right-click to show context menu
            def show_context_menu(event):
                try:
                    context_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    context_menu.grab_release()

            self.details_text.bind("<Button-3>", show_context_menu)  # Right-click

        except Exception as e:
            logging.error(f"Error setting up details TTS: {e}")

    def _read_selection(self) -> None:
        if not TTS_AVAILABLE or not self.tts_engine:
            messagebox.showerror("TTS Error", "Text-to-speech functionality is not available.")
            return

        try:
            logging.info("Starting TTS playback for selection.")
            # Get selected text
            if self.details_text.tag_ranges(tk.SEL):
                selected_text = self.details_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            else:
                # If no selection, read current line
                current_line = self.details_text.index(tk.INSERT).split(".")[0]
                selected_text = self.details_text.get(
                    f"{current_line}.0", f"{current_line}.end"
                )

            if selected_text.strip():
                cleaned_text = self._clean_text(selected_text)
                self.tts_engine.say(cleaned_text)
                self.tts_engine.runAndWait()
                logging.info("TTS playback completed for selection.")

        except Exception as e:
            logging.error(f"TTS selection error: {e}")
            messagebox.showerror("TTS Error", f"Failed to read selection: {e}")

    def _read_all_details(self) -> None:
        if not TTS_AVAILABLE or not self.tts_engine:
            messagebox.showerror("TTS Error", "Text-to-speech functionality is not available.")
            return

        try:
            logging.info("Starting TTS playback for all details.")
            all_text = self.details_text.get("1.0", tk.END)
            if all_text.strip():
                cleaned_text = self._clean_text(all_text)
                self.tts_engine.say(cleaned_text)
                self.tts_engine.runAndWait()
                logging.info("TTS playback completed for all details.")

        except Exception as e:
            logging.error(f"TTS all details error: {e}")
            messagebox.showerror("TTS Error", f"Failed to read all details: {e}")

    def _read_status(self) -> None:
        if not TTS_AVAILABLE or not self.tts_engine:
            messagebox.showerror("TTS Error", "Text-to-speech functionality is not available.")
            return

        try:
            logging.info("Starting TTS playback for status.")
            if hasattr(self, "status_var") and self.status_var:
                status_text = self.status_var.get()
                if status_text.strip():
                    cleaned_text = self._clean_text(status_text)
                    self.tts_engine.say(cleaned_text)
                    self.tts_engine.runAndWait()
                    logging.info("TTS playback completed for status.")
        except Exception as e:
            logging.error(f"TTS status error: {e}")
            messagebox.showerror("TTS Error", f"Failed to read status: {e}")

    def _read_selected_item(self) -> None:
        if not TTS_AVAILABLE or not self.tts_engine:
            messagebox.showerror("TTS Error", "Text-to-speech functionality is not available.")
            return

        try:
            if hasattr(self, "data_table"):
                selection = self.data_table.selection()
                if selection:
                    item_id = selection[0]
                    item_values = self.data_table.item(item_id, "values")
                    # Read a summary or specific columns
                    if item_values:
                        # Example: Read the first column's value if it exists
                        text_to_read = str(item_values[0]) if item_values else "No details"
                        self.tts_engine.say(text_to_read)
                        self.tts_engine.runAndWait()
        except Exception as e:
            logging.error(f"TTS selected item error: {e}")

    def _stop_reading(self) -> None:
        if not TTS_AVAILABLE or not self.tts_engine:
            return

        try:
            # pyttsx3's stop method is on the engine instance.
            # It stops the current utterance and clears the queue.
            self.tts_engine.stop()
        except Exception as e:
            logging.error(f"Error stopping TTS: {e}")

    def _pause_reading(self) -> None:
        if not TTS_AVAILABLE or not self.tts_engine:
            return
        try:
            self.tts_engine.pause()
        except Exception as e:
            logging.error(f"Error pausing TTS: {e}")

    def _resume_reading(self) -> None:
        if not TTS_AVAILABLE or not self.tts_engine:
            return
        try:
            self.tts_engine.resume()
        except Exception as e:
            logging.error(f"Error resuming TTS: {e}")

    def preprocess_text_for_speech(self, text: str) -> str:
        """Clean and prepare text for better TTS pronunciation"""
        import re
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Handle common abbreviations and technical terms
        replacements = {
            'CSV': 'C S V', 'JSON': 'Jason', 'XML': 'X M L', 'HTML': 'H T M L',
            'URL': 'U R L', 'API': 'A P I', 'GUI': 'G U I', 'CLI': 'C L I',
            'DB': 'database', 'SQL': 'S Q L', 'ID': 'I D', 'UUID': 'U U I D',
            'HTTP': 'H T T P', 'HTTPS': 'H T T P S', 'FTP': 'F T P', 'SSH': 'S S H',
            'TCP': 'T C P', 'UDP': 'U D P', 'IP': 'I P', 'DNS': 'D N S',
            'CPU': 'C P U', 'GPU': 'G P U', 'RAM': 'ram', 'ROM': 'rom',
            'USB': 'U S B', 'PDF': 'P D F', 'JPG': 'J P G', 'PNG': 'P N G',
            'GIF': 'gif', 'MP3': 'M P 3', 'MP4': 'M P 4', 'WAV': 'wave',
            'ZIP': 'zip', 'RAR': 'rar', 'TAR': 'tar', 'GZ': 'G Z',
            'EXE': 'executable', 'DLL': 'D L L', 'SO': 'S O', 'LIB': 'library',
        }
        
        for abbrev, replacement in replacements.items():
            text = re.sub(r'\b' + re.escape(abbrev) + r'\b', replacement, text, flags=re.IGNORECASE)
        
        return text

    def chunk_text(self, text: str, max_length: int = 400) -> list[str]:
        """Split text into smaller chunks for smoother playback."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 > max_length:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0
            current_chunk.append(word)
            current_length += len(word) + 1

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _read_text_in_background(self, text: str) -> None:
        """Run TTS in a background thread to avoid blocking the GUI."""
        threading.Thread(target=self._read_text, args=(text,), daemon=True).start()

    def _read_text(self, text: str) -> None:
        """Read text using TTS with chunk-based playback."""
        if not TTS_AVAILABLE or not self.tts_engine:
            messagebox.showerror("TTS Error", "Text-to-speech functionality is not available.")
            return

        try:
            # Split text into chunks
            chunks = self.chunk_text(text, max_length=400)
            for chunk in chunks:
                self.tts_engine.say(chunk)  # Queue each chunk for playback
            self.tts_engine.runAndWait()  # Execute playback
        except Exception as e:
            logging.error(f"TTS playback error: {e}")
            messagebox.showerror("TTS Error", f"Failed to read text: {e}")

    def setup_female_voice(self, engine) -> bool:
        """Attempt to set up a female voice if available"""
        try:
            voices = engine.getProperty('voices')
            if not voices:
                return False
            
            # Look for female voices
            female_indicators = ['female', 'zira', 'hazel', 'susan', 'anna', 'catherine']
            
            for voice in voices:
                voice_name = voice.name.lower() if voice.name else ''
                voice_id = voice.id.lower() if voice.id else ''
                
                if any(indicator in voice_name or indicator in voice_id for indicator in female_indicators):
                    engine.setProperty('voice', voice.id)
                    return True
            
            # If no female voice found, use the second voice if available
            if len(voices) > 1:
                engine.setProperty('voice', voices[1].id)
                return True
                
            return False
        except Exception as e:
            logging.error(f"Error setting up female voice: {e}")
            return False

    def _read_item_type(self) -> None:
        """Read the type or category of the selected item"""
        if not TTS_AVAILABLE or not self.tts_engine:
            return

        try:
            if hasattr(self, "data_table"):
                selection = self.data_table.selection()
                if selection:
                    item_id = selection[0]
                    item_values = self.data_table.item(item_id, "values")
                    
                    # Try to determine item type from headers/values
                    if item_values and hasattr(self, 'headers'):
                        # Look for type-related columns
                        type_info = []
                        for i, header in enumerate(self.headers):
                            if i < len(item_values) and header.lower() in ['type', 'category', 'kind', 'class']:
                                type_info.append(f"{header}: {item_values[i]}")
                        
                        if type_info:
                            text_to_read = f"Item type: {', '.join(type_info)}"
                        else:
                            # Fallback to first column as identifier
                            text_to_read = f"Item: {item_values[0] if item_values else 'Unknown'}"
                        
                        cleaned_text = self.preprocess_text_for_speech(text_to_read)
                        chunks = self.chunk_text(cleaned_text)
                        
                        for chunk in chunks:
                            self.tts_engine.say(chunk)
                        self.tts_engine.runAndWait()
                    else:
                        self.tts_engine.say("No item selected or no type information available")
                        self.tts_engine.runAndWait()
                else:
                    self.tts_engine.say("No item selected")
                    self.tts_engine.runAndWait()
            else:
                self.tts_engine.say("Data table not available")
                self.tts_engine.runAndWait()
                
        except Exception as e:
            logging.error(f"Error reading item type: {e}")

    def _show_speech_settings(self) -> None:
        """Show TTS configuration dialog"""
        if not TTS_AVAILABLE or not self.tts_engine:
            messagebox.showinfo("TTS Not Available", "Text-to-speech functionality is not available.")
            return
        
        try:
            import tkinter.ttk as ttk
            
            settings_window = tk.Toplevel(self.root)
            settings_window.title("Speech Settings")
            settings_window.geometry("400x300")
            settings_window.transient(self.root)
            settings_window.grab_set()
            
            # Voice selection
            ttk.Label(settings_window, text="Voice:").pack(pady=5)
            voices = self.tts_engine.getProperty('voices')
            voice_names = [voice.name for voice in voices] if voices else ['Default']
            
            voice_var = tk.StringVar()
            current_voice = self.tts_engine.getProperty('voice')
            for voice in voices:
                if voice.id == current_voice:
                    voice_var.set(voice.name)
                    break
            else:
                voice_var.set(voice_names[0] if voice_names else 'Default')
            
            voice_combo = ttk.Combobox(settings_window, textvariable=voice_var, values=voice_names, state="readonly")
            voice_combo.pack(pady=5, padx=20, fill="x")
            
            # Female voice option
            female_voice_var = tk.BooleanVar()
            ttk.Checkbutton(settings_window, text="Prefer female voice", variable=female_voice_var).pack(pady=5)
            
            # Speed control
            ttk.Label(settings_window, text="Speaking Speed:").pack(pady=(10,5))
            speed_var = tk.IntVar(value=self.tts_engine.getProperty('rate'))
            speed_scale = tk.Scale(settings_window, from_=50, to=300, orient="horizontal", variable=speed_var)
            speed_scale.pack(pady=5, padx=20, fill="x")
            
            # Volume control
            ttk.Label(settings_window, text="Volume:").pack(pady=(10,5))
            volume_var = tk.DoubleVar(value=self.tts_engine.getProperty('volume'))
            volume_scale = tk.Scale(settings_window, from_=0.0, to=1.0, resolution=0.1, orient="horizontal", variable=volume_var)
            volume_scale.pack(pady=5, padx=20, fill="x")
            
            # Test button
            def test_voice():
                self.tts_engine.setProperty("rate", speed_var.get())
                self.tts_engine.setProperty("volume", volume_var.get())
                self.tts_engine.say("This is a test of the speech settings.")
                self.tts_engine.runAndWait()
            
            ttk.Button(settings_window, text="Test Voice", command=test_voice).pack(pady=5)

            # Apply button
            def apply_settings():
                try:
                    # Set voice
                    selected_voice = voice_var.get()
                    for voice in voices:
                        if voice.name == selected_voice:
                            voice_id = voice.id
                            if female_voice_var.get():
                                self.setup_female_voice(self.tts_engine)
                            else:
                                self.tts_engine.setProperty("voice", voice_id)
                            break

                    # Set speed and volume
                    self.tts_engine.setProperty("rate", speed_var.get())
                    self.tts_engine.setProperty("volume", volume_var.get())
                    
                    settings_window.destroy()
                    self.update_status("Speech settings applied")
                    
                except Exception as e:
                    logging.error(f"Error applying speech settings: {e}")
                    messagebox.showerror("Error", f"Failed to apply settings: {e}")
            
            # Buttons
            buttons_frame = ttk.Frame(settings_window)
            buttons_frame.pack(pady=10)
            ttk.Button(buttons_frame, text="Apply", command=apply_settings).pack(side="left", padx=5)
            ttk.Button(buttons_frame, text="Cancel", command=settings_window.destroy).pack(side="left", padx=5)

        except Exception as e:
            logging.error(f"Error showing speech settings: {e}")
            messagebox.showerror("Error", f"Failed to open speech settings: {e}")

    def _save_speech_to_file(self) -> None:
        """Save current text content as audio file"""
        if not TTS_AVAILABLE or not self.tts_engine:
            messagebox.showinfo("TTS Not Available", "Text-to-speech functionality is not available.")
            return
        
        try:
            # Get text to convert
            text_content = ""
            if hasattr(self, 'details_text'):
                if self.details_text.tag_ranges(tk.SEL):
                    text_content = self.details_text.get(tk.SEL_FIRST, tk.SEL_LAST)
                else:
                    text_content = self.details_text.get("1.0", tk.END)
            
            if not text_content.strip():
                messagebox.showwarning("No Text", "No text available to convert to speech.")
                return
            
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".wav",
                filetypes=[("WAV files", "*.wav"), ("All files", "*.*")],
                title="Save Speech As"
            )
            
            if file_path:
                # Preprocess text
                cleaned_text = self.preprocess_text_for_speech(text_content)
                
                # Save to file
                self.tts_engine.save_to_file(cleaned_text, file_path)
                self.tts_engine.runAndWait()
                
                self.update_status(f"Speech saved to: {os.path.basename(file_path)}")
                messagebox.showinfo("Success", f"Speech saved to:\n{file_path}")
        
        except Exception as e:
            logging.error(f"Error saving speech to file: {e}")
            messagebox.showerror("Save Error", f"Failed to save speech: {e}")

    def _update_details_view(self, item_data: Optional[Dict[str, Any]]) -> None:  # Updated signature with type hint
        try:
            if not hasattr(self, "details_text"):
                return

            # Clear current content
            self.details_text.delete("1.0", "end")

            if item_data and "values" in item_data: # Check if item_data is not None
                values = item_data["values"]

                # Check if this is a text file (has Content column)
                if hasattr(self, "headers") and "Content" in self.headers:
                    content_index = self.headers.index("Content")
                    if content_index < len(values):
                        content = values[content_index]
                        self.details_text.insert("1.0", content)
                        return

                # For non-text files, display structured information
                details = []
                if hasattr(self, "headers"):
                    for i, header in enumerate(self.headers):
                        if i < len(values):
                            details.append(f"{header}: {values[i]}")

                if details:
                    self.details_text.insert("1.0", "\n".join(details))
                else:
                    self.details_text.insert("1.0", str(values))
            else:
                self.details_text.delete("1.0", tk.END)
                self.details_text.insert("1.0", "Error displaying details after selection.")

        except Exception as e:
            logging.error(f"Error updating details view: {e}")
            if hasattr(self, "details_text"):
                self.details_text.delete("1.0", "end")
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

            if total_original == 0:
                return

            # Proportionally adjust column widths
            for col_index, original_width in original_widths.items():
                if col_index < len(self.data_table["columns"]):
                    col_id = self.data_table["columns"][col_index]
                    new_width = max(
                        50, int((original_width / total_original) * available_width)
                    )
                    self.data_table.column(col_id, width=new_width)

        except Exception as e:
            logging.error(f"Error during treeview configure: {e}")

    def _apply_filter(
        self, data: List[List[Any]], filter_text: str, column_name: str
    ) -> List[List[Any]]:
        if not filter_text:
            return data

        filtered_data = []
        for row in data:
            if column_name == "All Columns":
                # Search in all columns
                if any(
                    filter_text.lower() in str(cell).lower() for cell in row
                ):
                    filtered_data.append(row)
            else:
                # Search in specific column
                if hasattr(self, "headers") and column_name in self.headers:
                    col_index = self.headers.index(column_name)
                    if col_index < len(row) and filter_text.lower() in str(
                        row[col_index]
                    ).lower():
                        filtered_data.append(row)

        return filtered_data

    def _on_column_click(self, event: tk.Event) -> None:
        try:
            region = self.data_table.identify_region(event.x, event.y)
            if region == "heading":
                col = self.data_table.identify_column(event.x, event.y)
                col_index = int(col.replace("#", "")) - 1

                if hasattr(self, "headers") and col_index < len(self.headers):
                    header = self.headers[col_index]
                    self._sort_by_column(col_index, header)

        except Exception as e:
            logging.error(f"Error handling column click: {e}")

    def _sort_by_column(self, col_index: int, header: str) -> None:
        try:
            # Toggle sort direction
            if not hasattr(self, "_sort_column") or self._sort_column != col_index:
                self._sort_reverse = False
            else:
                self._sort_reverse = not self._sort_reverse

            self._sort_column = col_index

            # Get current data
            data = []
            for item in self.data_table.get_children():
                values = self.data_table.item(item, "values")
                data.append(list(values))

            # Sort data
            try:
                # Try numeric sort first
                data.sort(
                    key=lambda x: float(x[col_index]) if x[col_index] else 0,
                    reverse=self._sort_reverse,
                )
            except (ValueError, TypeError):
                # Fall back to string sort
                data.sort(
                    key=lambda x: str(x[col_index]).lower(),
                    reverse=self._sort_reverse,
                )

            # Update view
            self._update_data_view(data)

            # Update status
            direction = "descending" if self._sort_reverse else "ascending"
            self.update_status(f"Sorted by {header} ({direction})")

        except Exception as e:
            logging.error(f"Error sorting by column {header}: {e}")

    def _on_save_file(self) -> None:
        try:
            # Get current data
            data = []
            for item in self.data_table.get_children():
                values = self.data_table.item(item, "values")
                data.append(list(values))

            if not data:
                messagebox.showwarning("No Data", "No data available to save.")
                return

            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx") if PANDAS_AVAILABLE else None,
                    ("All files", "*.*"),
                ],
                title="Save Data As",
            )

            if file_path:
                self._save_data_to_file(data, file_path)

        except Exception as e:
            logging.error(f"Error in save file dialog: {e}")
            messagebox.showerror("Error", f"Failed to save file: {e}")

    def _save_data_to_file(self, data: List[List[Any]], file_path: str) -> None:
        try:
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
                # Basic text save for other types or if pandas/csv is not appropriate
                with open(file_path, "w", encoding="utf-8") as f:
                    if hasattr(self, 'headers'):
                        f.write(",".join(map(str, self.headers)) + "\n")
                    for row in data:
                        f.write(",".join(map(str, row)) + "\n")
            self.update_status(f"Saved to {file_path}")
        except Exception as e:
            logging.error(f"Error saving to file {file_path}: {e}") # Log error
            self.root.after(0, lambda: messagebox.showerror("Save Error", str(e))) # Show error to user
            self.update_status(f"Error saving to {file_path}") # Update status

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
                defaultextension=".txt",  # Default to .txt if no specific type chosen
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
                        self.details_text.delete("1.0", tk.END)  # Clear details view
                    self.run_in_background(
                        self._load_data_background, file_path, callback=self._on_data_loaded
                    )
                elif file_extension in [".txt", ".py", ".md"]:  # Added .md
                    self.update_status(f"Opening text file: {os.path.basename(file_path)}...")
                    # Clear previous data/text specific states
                    self.current_data = None
                    self.headers = []
                    if hasattr(self, 'data_table'):
                        self.data_table.delete(*self.data_table.get_children())  # Clear data table
                    self.run_in_background(
                        self._load_text_background, file_path, callback=self._on_text_loaded_callback
                    )
                else:
                    self.update_status(f"Unsupported file type: {file_extension}", error=True)
                    messagebox.showwarning(
                        "Unsupported File Type",
                        f"The file type '{file_extension}' is not directly supported for automatic display. You can try opening it as 'All Files'.",
                    )
        except Exception as e:
            logging.error(f"Error in _on_open_file: {e}")
            messagebox.showerror("Error", f"Failed to open file: {e}")

    def _on_data_table_select(self, event: tk.Event) -> None:
        """Handles the TreeviewSelect event for the data_table."""
        try:
            if not hasattr(self, "data_table"):
                return
            
            selection = self.data_table.selection()  # Get current selection
            if selection:
                item_id = selection[0]  # Get the first selected item ID
                item_data = self.data_table.item(item_id)  # Get item details
                self._update_details_view(item_data)  # Call with actual item data
            else:
                # Optionally, clear details view or show a default message if nothing is selected
                self._update_details_view(None) 
        except Exception as e:
            logging.error(f"Error handling data table selection: {e}")
            # Optionally, update details view with an error message
            if hasattr(self, "details_text"):
                self.details_text.delete("1.0", "end")
                self.details_text.insert("1.0", f"Error processing selection: {e}")

    def _update_script_menu(self) -> None:
        logging.info("Updating script menu as it is about to be displayed...")
        if not hasattr(self, 'script_menu') or not isinstance(self.script_menu, tk.Menu):
            logging.error(
                "self.script_menu is not initialized or is not a tk.Menu instance. "
                "The 'Run Script' submenu cannot be populated. "
                "Ensure create_menu_bar() correctly initializes self.script_menu and is called before _update_script_menu()."
            )
            return

        self.script_menu.delete(0, tk.END)  # Clear existing items

        try:
            if not hasattr(self, 'scripts_dir') or not self.scripts_dir:
                logging.warning("Scripts directory (self.scripts_dir) is not defined.")
                self.script_menu.add_command(label="(Scripts dir not configured)", state=tk.DISABLED)
            elif not os.path.exists(self.scripts_dir):
                logging.warning(f"Scripts directory '{self.scripts_dir}' not found.")
                self.script_menu.add_command(label="(Scripts dir missing)", state=tk.DISABLED)
                # Attempt to create it
                try:
                    os.makedirs(self.scripts_dir)
                    logging.info(f"Re-created missing scripts directory: {self.scripts_dir}")
                    # Optionally, create a sample script if the directory was just created
                    sample_script_path = os.path.join(self.scripts_dir, "sample_script.py")
                    if not os.path.exists(sample_script_path):
                        with open(sample_script_path, "w") as f:
                            f.write("# Sample script\nprint('Hello from sample script!')")
                        logging.info(f"Created sample script: {sample_script_path}")
                except Exception as e_mkdir:
                    logging.error(f"Failed to re-create scripts directory: {e_mkdir}")
            
            script_files = []
            # Check again for scripts_dir existence in case it was just created
            if hasattr(self, 'scripts_dir') and self.scripts_dir and os.path.exists(self.scripts_dir):
                script_files = glob.glob(os.path.join(self.scripts_dir, "*.py"))
            
            if not script_files:
                # This label will be added if scripts_dir existed but was empty,
                # or if scripts_dir was missing/not configured and the specific messages above were already added.
                # To avoid duplicate "missing" messages, we check if items were already added.
                if self.script_menu.index(tk.END) is None:  # No items added yet
                    self.script_menu.add_command(label="(No scripts found)", state=tk.DISABLED)
            else:
                for script_path in sorted(script_files):
                    script_name = os.path.basename(script_path)
                    self.script_menu.add_command(
                        label=script_name,
                        command=lambda sp=script_path: self._run_selected_script(sp)
                    )
            
            self.script_menu.add_separator()
            self.script_menu.add_command(label="Refresh Scripts", command=self._update_script_menu)
            self.script_menu.add_command(
                label="Open Scripts Folder...",
                command=self._open_scripts_folder
            )
            # Avoid updating status if scripts_dir was problematic initially, status might be confusing.
            if hasattr(self, 'scripts_dir') and self.scripts_dir and os.path.exists(self.scripts_dir):
                self.update_status(f"Scripts menu updated. Found {len(script_files)} scripts.")

        except Exception as e:
            logging.error(f"Error updating script menu: {e}", exc_info=True)
            messagebox.showerror("Script Menu Error", f"Could not update script menu: {e}")
            # Ensure self.script_menu is still valid before trying to add error items
            if hasattr(self, 'script_menu') and isinstance(self.script_menu, tk.Menu):
                 # Clear any partial items from the try block before adding error state
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
                try:
                    logging.info(f"Executing script: python '{script_path}'")
                    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    proc = subprocess.Popen(
                        ['python', script_path], stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, text=True,
                        creationflags=flags, cwd=self.scripts_dir
                    )
                    out, err = proc.communicate()
                    if proc.returncode == 0:
                        self.root.after(0, lambda: self.update_status(f"Script '{script_name}' finished."))
                        if out.strip():
                            self.root.after(0, lambda: messagebox.showinfo(f"{script_name} Output", out))
                        else:
                            self.root.after(0, lambda: messagebox.showinfo(f"{script_name} Finished", f"Script '{script_name}' completed with no output."))
                    else:
                        msg = f"Script '{script_name}' failed." + (f"\n\nError:\n{err}" if err.strip() else '')
                        self.root.after(0, lambda: messagebox.showerror(f"{script_name} Error", msg))
                        self.root.after(0, lambda: self.update_status(f"Script '{script_name}' failed.", error=True))
                except Exception as e_thread:
                    logging.error(f"Exception while running script {script_name}: {e_thread}")
                    self.root.after(0, lambda: messagebox.showerror("Script Execution Error", str(e_thread)))
                    self.root.after(0, lambda: self.update_status(f"Error running {script_name}.", error=True))
            threading.Thread(target=target, daemon=True).start()
        except Exception as e:
            logging.error(f"Error preparing to run script {script_path}: {e}")
            messagebox.showerror("Script Error", f"Could not run script {script_name}: {e}")
            self.update_status(f"Failed to start script {script_name}.", error=True)

    def _open_scripts_folder(self) -> None:
        if not hasattr(self, 'scripts_dir') or not self.scripts_dir:
            messagebox.showwarning("Error", "Scripts directory path is not configured.")
            logging.warning("scripts_dir not set when opening folder.")
            return
        if not os.path.isdir(self.scripts_dir):
            messagebox.showwarning(
                "Error", f"Scripts directory does not exist:\n{self.scripts_dir}")
            logging.warning(f"Non-existent scripts_dir: {self.scripts_dir}")
            return
        try:
            subprocess.run(['xdg-open', self.scripts_dir], check=True)
            self.update_status(f"Opened scripts folder: {self.scripts_dir}")
        except Exception as e:
            logging.error(f"Failed to open scripts folder: {e}")
            messagebox.showerror("Error", f"Could not open scripts folder: {e}")

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
            if not isinstance(content, str):
                logging.error(f"Invalid text load result: {type(content)}")
                messagebox.showerror("Error", "Failed to load text content.")
                self.update_status("Failed to load text.", error=True)
                if hasattr(self, 'details_text'):
                    self.details_text.delete("1.0", tk.END)
                    self.details_text.insert("1.0", "Error: Failed to load text content.")
                return
            if hasattr(self, 'details_text'):
                self.details_text.delete("1.0", tk.END)
                self.details_text.insert("1.0", content)
                status = f"Loaded: {os.path.basename(self.current_file_path)}" if hasattr(self, 'current_file_path') else "Text content loaded."
                self.update_status(status)
            if hasattr(self, 'data_table'):
                self.data_table.delete(*self.data_table.get_children())
            self.current_data = None
            self.headers = []
        except Exception as e:
            logging.error(f"Error in text loaded callback: {e}")
            messagebox.showerror("Error", f"Failed to load text: {e}")
            self.update_status("Failed to load text.", error=True)

    def _load_data_background(self, file_path: str) -> Tuple[List[List[Any]], List[str]]:
        try:
            if not PANDAS_AVAILABLE:
                raise ImportError("Pandas is required to load data.")
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            if ext == '.csv':
                df = pd.read_csv(file_path)
            elif ext in ['.xlsx', '.xls']:
                try:
                    df = pd.read_excel(file_path)
                except:
                    engine = 'openpyxl' if ext == '.xlsx' else 'xlrd'
                    df = pd.read_excel(file_path, engine=engine)
            elif ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = [l.strip() for l in f if l.strip()]
                df = pd.DataFrame(lines, columns=['text_data'])
            else:
                raise ValueError(f"Unsupported extension: {ext}")
            return df.values.tolist(), df.columns.tolist()
        except Exception as e:
            logging.error(f"Error loading data in background: {e}")
            raise

    def _load_text_background(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logging.error(f"Error loading text in background: {e}")
            raise

    def _clean_text(self, text: str) -> str:
        # Remove special characters and extra whitespace
        return text.replace("\n", " ").strip()

    def _read_filter_text(self) -> None:
        if not TTS_AVAILABLE or not self.tts_engine:
            messagebox.showerror("TTS Error", "Text-to-speech functionality is not available.")
            return

        try:
            filter_text = self.filter_var.get()
            if filter_text.strip():
                cleaned_text = self._clean_text(filter_text)
                self.tts_engine.say(cleaned_text)
                self.tts_engine.runAndWait()
        except Exception as e:
            logging.error(f"TTS filter text error: {e}")
            messagebox.showerror("TTS Error", f"Failed to read filter text: {e}")

    def _save_tts_settings(self) -> None:
        try:
            self.config.set("tts_voice", self.tts_engine.getProperty("voice"))
            self.config.set("tts_rate", self.tts_engine.getProperty("rate"))
            self.config.set("tts_volume", self.tts_engine.getProperty("volume"))
        except Exception as e:
            logging.error(f"Error saving TTS settings: {e}")

    def _load_tts_settings(self) -> None:
        try:
            voice = self.config.get("tts_voice")
            rate = self.config.get("tts_rate")
            volume = self.config.get("tts_volume")
            if voice:
                self.tts_engine.setProperty("voice", voice)
            if rate:
                self.tts_engine.setProperty("rate", int(rate))
            if volume:
                self.tts_engine.setProperty("volume", float(volume))
        except Exception as e:
            logging.error(f"Error loading TTS settings: {e}")

    def _test_tts(self) -> None:
        if not TTS_AVAILABLE or not self.tts_engine:
            messagebox.showerror("TTS Error", "Text-to-speech functionality is not available.")
            return
        try:
            self.tts_engine.say("This is a test of the text-to-speech system.")
            self.tts_engine.runAndWait()
        except Exception as e:
            logging.error(f"TTS test error: {e}")
            messagebox.showerror("TTS Error", f"Failed to test TTS: {e}")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = CrewGUI(root)
        root.mainloop()
    except Exception as e:
        logging.critical(f"Failed to launch Crew GUI: {e}", exc_info=True)
        # Fallback to a simple error message if GUI initialization fails
        print(f"Error: {e}")
        input("Press Enter to exit...")