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
            self.root = root
            self.root.title("Crew Manager")

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

    def create_menu_bar(self) -> None:
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Data (Ctrl+O)", command=self._on_load_data)
        file_menu.add_command(
            label="Import (Ctrl+I)", command=self._on_import_data
        )  # Added Import menu item
        file_menu.add_command(
            label="Load Text Content", command=self._on_load_text_content
        )
        file_menu.add_separator()
        file_menu.add_command(label="Save (Ctrl+S)", command=self._on_save)
        file_menu.add_command(label="Export (Ctrl+E)", command=self._on_export)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Edit menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(
            label="Find (Ctrl+F)", command=lambda: self.filter_var.focus_set()
        )
        edit_menu.add_command(label="Clear Filter (Esc)", command=self.clear_filter)

        # View menu
        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh (F5)", command=self._refresh_views)
        view_menu.add_command(
            label="Show Imported Modules", command=self._show_imported_modules
        )
        view_menu.add_separator()

        # Add column visibility submenu
        self.column_visibility_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Columns", menu=self.column_visibility_menu)

        # Add script selector submenu
        self.script_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Run Script", menu=self.script_menu)
        view_menu.add_command(label="Refresh Scripts", command=self._update_script_menu)

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

        # Configure left frame grid weights for sections
        self.left_frame.grid_columnconfigure(0, weight=1)
        self.left_frame.grid_rowconfigure(
            0, weight=0
        )  # Controls section - fixed height
        self.left_frame.grid_rowconfigure(1, weight=1)  # Groups section - expandable
        self.left_frame.grid_rowconfigure(2, weight=0)  # Filter section - fixed height

        # Configure right frame row weights
        self.right_frame.grid_rowconfigure(0, weight=3)  # Data view gets more space
        self.right_frame.grid_rowconfigure(1, weight=1)  # Details view gets less space
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
            control_frame = ttk.LabelFrame(
                self.left_frame, text="Controls", padding="5"
            )
            control_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

            # Add control buttons
            ttk.Button(
                control_frame, text="Load Data", command=self._on_load_data
            ).pack(fill="x", pady=2)
            ttk.Button(control_frame, text="Save", command=self._on_save).pack(
                fill="x", pady=2
            )
            ttk.Button(control_frame, text="Export", command=self._on_export).pack(
                fill="x", pady=2
            )
        except Exception as e:
            logging.error(f"Failed to create control section: {e}")
            raise

    def create_group_section(self) -> None:
        try:
            group_frame = ttk.LabelFrame(self.left_frame, text="Groups", padding="5")
            group_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

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
            filter_frame = ttk.LabelFrame(self.left_frame, text="Filters", padding="5")
            filter_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
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
            ttk.Entry(filter_frame, textvariable=self.filter_var).pack(fill="x", pady=2)
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
            # Create details frame in right panel row 1
            details_frame = ttk.LabelFrame(
                self.right_frame, text="Details View", padding="5"
            )
            details_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

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
                self.data_table.bind("<<TreeviewSelect>>", self._update_details_view)

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
            return

        try:
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
            logging.error(f"TTS stop error: {e}")

    def _update_details_view(self, event: tk.Event = None) -> None:
        try:
            selection = self.data_table.selection()
            if not selection:
                self.details_text.delete("1.0", tk.END)
                self.details_text.insert("1.0", "No item selected.")
                return

            item_id = selection[0]
            item_data = self.data_table.item(item_id)
            item_values = item_data.get("values", [])
            
            self.details_text.delete("1.0", tk.END)
            
            details_str = f"Item ID: {item_id}\\n"
            if self.headers and item_values:
                for header, value in zip(self.headers, item_values):
                    details_str += f"{header}: {value}\\n"
            else: # Fallback if headers are not available or item_values is empty
                details_str += f"Values: {item_values}\\n"

            self.details_text.insert("1.0", details_str)

        except Exception as e:
            logging.error(f"Error updating details view: {e}")
            self.details_text.delete("1.0", tk.END)
            self.details_text.insert("1.0", "Error displaying details.")

    # Callback methods
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
        try:
            # Clear existing items
            self.group_list.delete(*self.group_list.get_children())

            # Configure columns for better display
            if not self.group_list["columns"]:
                self.group_list["columns"] = ("members", "primary", "secondary")
                self.group_list.heading("#0", text="Group Name")
                self.group_list.heading("members", text="#")
                self.group_list.heading("primary", text="Primary")
                self.group_list.heading("secondary", text="Secondary")

                # Configure column widths
                self.group_list.column("#0", width=150, minwidth=100)
                self.group_list.column("members", width=50, minwidth=30)
                self.group_list.column("primary", width=100, minwidth=50)
                self.group_list.column("secondary", width=100, minwidth=50)

            # Add groups to treeview
            for group_name, group_data in self.groups.items():
                if group_name and group_data:  # Only add non-empty groups
                    # Get primary and secondary skills for the group
                    primary = ""
                    secondary = ""
                    for row in group_data:
                        if len(row) > 5 and row[5]:  # PRIMUS column
                            primary = row[5] if not primary else primary
                        if len(row) > 6 and row[6]:  # SECUNDUS column
                            secondary = row[6] if not secondary else secondary

                    # Insert group into treeview
                    self.group_list.insert(
                        "",
                        "end",
                        text=group_name,
                        values=(len(group_data), primary, secondary),
                        tags=(group_name,),
                    )

            # Sort groups by name
            items = [
                (self.group_list.item(item)["text"], item)
                for item in self.group_list.get_children("")
            ]
            items.sort()
            for idx, (_, item) in enumerate(items):
                self.group_list.move(item, "", idx)

        except Exception as e:
            logging.error(f"Error updating groups view: {e}")
            raise

    def _on_group_select(self, event: tk.Event) -> None:
        try:
            selection = self.group_list.selection()
            if selection:
                item_id = selection[0]
                group_name = self.group_list.item(item_id)["text"]
                if group_name in self.groups:
                    # Update data view with just this groups data
                    self._update_data_view(self.groups[group_name])
                    self.update_status(f"Showing group: {group_name}")
        except Exception as e:
            logging.error(f"Error handling group selection: {e}")

    def _on_data_select(self, event: tk.Event) -> None:
        # This method is called when a data item is selected.
        # It's already correctly calling _update_details_view if bound.
        # If you need additional logic when a data item is selected, add it here.
        # For now, we'll assume _update_details_view handles what's needed.
        pass # Placeholder if no additional specific action is needed beyond _update_details_view

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
            if hasattr(self, "_update_script_menu"):
                self._update_script_menu()

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

    def _update_details_view(self, item_data) -> None:
        try:
            if not hasattr(self, "details_text"):
                return

            # Clear current content
            self.details_text.delete("1.0", "end")

            if item_data and "values" in item_data:
                values = item_data["values"]

                # Check if this is a text file (has Content column)
                if (
                    hasattr(self, "headers")
                    and len(self.headers) >= 2
                    and self.headers[1] == "Content"
                ):
                    # Display filename and content for text files
                    details_text = f"File: {values[0]}\\n\\n{values[1]}"
                else:
                    # Display all headers and values for other data
                    details_text = ""
                    if hasattr(self, "headers"):
                        for header, value in zip(self.headers, values):
                            details_text += f"{header}: {value}\\n"

                # Add Item ID if available in item_data (Treeview item's internal ID)
                if "text" in item_data: # Check if 'text' key exists
                    details_text += f"\\nItem ID: {item_data['text']}\\n"

                self.details_text.insert("1.0", details_text)
            else:
                self.details_text.insert("1.0", "No details available for this item.")

        except Exception as e:
            logging.error(f"Error updating details view: {e}")
            if hasattr(self, "details_text"):
                self.details_text.delete("1.0", "end")
                self.details_text.insert("1.0", f"Error displaying details: {e}")

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

            # Get available voices
            voices = self.tts_engine.getProperty("voices")
            voice_names = [voice.name for voice in voices]
            voice_combo["values"] = voice_names

            # Set current voice
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

            # Apply button
            def apply_settings():
                try:
                    # Set voice
                    selected_voice = voice_var.get()
                    for voice in voices:
                        if voice.name == selected_voice:
                            self.tts_engine.setProperty("voice", voice.id)
                            break

                    # Set speed and volume
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

            ttk.Button(buttons_frame, text="Apply", command=apply_settings).pack(
                side="left", padx=5
            )
            ttk.Button(
                buttons_frame, text="Cancel", command=settings_window.destroy
            ).pack(side="left", padx=5)

        except Exception as e:
            logging.error(f"Error showing speech settings: {e}")

    # Event handler methods for menu operations
    def _on_load_data(self) -> None:
        try:
            file_path = filedialog.askopenfilename(
                title="Select Data File",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx;*.xls"),
                    # ("Text files", "*.txt"), # Text files are handled by a separate menu item
                    ("All files", "*.* G")
                ],
            )
            if file_path:
                self.update_status("Loading data...")
                self.run_in_background(
                    self._load_data_background, file_path, callback=self._on_data_loaded
                )
        except Exception as e:
            logging.error(f"Error loading data: {e}")
            messagebox.showerror("Error", f"Failed to load data: {e}")

    def _on_import_data(self) -> None:
        try:
            file_path = filedialog.askopenfilename(
                title="Import Data File",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx;*.xls"),
                    ("All files", "*.*"),
                ],
            )
            if file_path:
                self.update_status("Importing data...")
                self.run_in_background(
                    self._load_data_background, file_path, callback=self._on_data_loaded
                )
        except Exception as e:
            logging.error(f"Error importing data: {e}")
            messagebox.showerror("Error", f"Failed to import data: {e}")

    def _on_save(self) -> None:
        try:
            if hasattr(self, "current_file_path") and self.current_file_path:
                self.run_in_background(
                    self._save_to_file, self.current_file_path, self.current_data
                )
            else:
                self._on_save_as()
        except Exception as e:
            logging.error(f"Error saving data: {e}")
            messagebox.showerror("Error", f"Failed to save data: {e}")

    def _on_save_as(self) -> None:
        try:
            file_path = filedialog.asksaveasfilename(
                title="Save Data As",
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx"),
                    ("All files", "*.*"),
                ],
            )
            if file_path:
                self.current_file_path = file_path
                self.run_in_background(self._save_to_file, file_path, self.current_data)
        except Exception as e:
            logging.error(f"Error saving data as: {e}")
            messagebox.showerror("Error", f"Failed to save data: {e}")

    def _on_export(self) -> None:
        try:
            file_path = filedialog.asksaveasfilename(
                title="Export to Excel",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            )
            if file_path:
                self.update_status("Exporting to Excel...")
                self.run_in_background(
                    self._export_to_excel, file_path, self.current_data
                )
        except Exception as e:
            logging.error(f"Error exporting data: {e}")
            messagebox.showerror("Error", f"Failed to export data: {e}")

    def _on_load_text_content(self) -> None:
        try:
            file_path = filedialog.askopenfilename(
                title="Load Text File",
                filetypes=[
                    ("Text files", "*.txt"),
                    ("Python files", "*.py"),
                    ("All files", "*.*"),
                ],
            )
            if file_path:
                self.update_status("Loading text content...")
                self.run_in_background(
                    self._load_text_background, file_path, callback=self._on_text_loaded
                )
        except Exception as e:
            logging.error(f"Error loading text content: {e}")
            messagebox.showerror("Error", f"Failed to load text content: {e}")

    def _show_imported_modules(self) -> None:
        try:
            if hasattr(self, "imported_modules") and hasattr(self, "failed_imports"):
                info = f"Successfully imported: {len(self.imported_modules)} modules\\n"
                info += f"Failed imports: {len(self.failed_imports)} modules\\n\\n"

                if self.imported_modules:
                    info += "Imported modules:\\n"
                    for module in self.imported_modules:
                        info += f"  - {module}\\n"

                if self.failed_imports:
                    info += "\\nFailed imports:\\n"
                    # failed_imports is a list of tuples (module_name, error_message)
                    for module, error in self.failed_imports:
                        info += f"  - {module}: {error}\\n"

                messagebox.showinfo("Module Import Status", info)
            else:
                messagebox.showinfo(
                    "Module Import Status", "No module import data available"
                )
        except Exception as e:
            logging.error(f"Error showing imported modules: {e}")
            messagebox.showerror("Error", f"Failed to show module information: {e}")

    def _update_script_menu(self) -> None:
        try:
            if not hasattr(self, "script_menu"):
                return

            # Clear existing menu items
            self.script_menu.delete(0, "end")

            # Find Python files in current directory
            py_files = glob.glob("*.py")
            if py_files:
                for py_file in sorted(py_files):
                    if py_file != "__pycache__":
                        self.script_menu.add_command(
                            label=py_file, command=lambda f=py_file: self._run_script(f)
                        )
            else:
                self.script_menu.add_command(
                    label="No Python files found", state="disabled"
                )

        except Exception as e:
            logging.error(f"Error updating script menu: {e}")

    def _run_script(self, script_name: str) -> None:
        try:
            self.update_status(f"Running script: {script_name}")
            self.run_in_background(self._execute_script, script_name)
        except Exception as e:
            logging.error(f"Error running script: {e}")
            messagebox.showerror("Error", f"Failed to run script {script_name}: {e}")

    def _execute_script(self, script_name: str) -> None:
        try:
            self.update_status(f"Executing script: {script_name}...") # Added status update
            result = subprocess.run(
                [sys.executable, script_name],
                capture_output=True,
                text=True,
                timeout=30, # Added timeout
            )

            if result.returncode == 0:
                self.root.after(0, lambda: messagebox.showinfo("Script Result", f"Script {script_name} finished.\\nOutput:\\n{result.stdout}")) # Show output
            else:
                self.root.after(0, lambda: messagebox.showerror("Script Error", f"Script {script_name} failed.\\nError:\\n{result.stderr}")) # Show error
        except Exception as e:
            logging.error(f"Error executing script {script_name}: {e}")
            self.root.after(0, lambda: messagebox.showerror("Script Error", str(e)))

    # Background processing methods
    def _load_data_background(
        self, file_path: str
    ) -> Tuple[List[List[Any]], List[str]]:
        try:
            self.current_file_path = file_path # Store the loaded file path
            if file_path.endswith(".txt"):
                # Handle text files specially - load content for details view
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Create a simple single-row data structure for text files
                headers = ["File Name", "Content"]
                file_name = os.path.basename(file_path)
                data = [[file_name, content]]
                return data, headers
            else:
                # Handle CSV and Excel files with pandas
                if file_path.endswith(".csv"):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)

                headers = df.columns.tolist()
                data = df.values.tolist()
                return data, headers
        except Exception as e:
            logging.error(f"Error loading data from {file_path}: {e}")
            raise

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
                self.root.after(
                    0, lambda: self.update_status(f"Exported to {file_path}")
                )
            else:
                raise ValueError("No data to export")
        except Exception as e:
            logging.error(f"Error exporting to Excel: {e}")
            self.root.after(0, lambda: messagebox.showerror("Export Error", str(e)))

    def _save_to_file(self, file_path: str, data: List[List[Any]]) -> None:
        try:
            self.update_status(f"Saving to {file_path}...") # Added status update
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
                        f.write(",".join(map(str, self.headers)) + "\\n")
                    for row in data:
                        f.write(",".join(map(str, row)) + "\\n")
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


# Add a main execution block to launch the GUI directly if this file is run
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = CrewGUI(root)
        root.mainloop()
    except Exception as e:
        logging.critical(f"Failed to launch Crew GUI: {e}", exc_info=True)
        # Fallback to a simple error message if logging or messagebox fails
        try:
            messagebox.showerror("Fatal Error", f"Could not start the application: {e}")
        except tk.TclError:
            print(f"FATAL ERROR: Could not start the application: {e}")
