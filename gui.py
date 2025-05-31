#!/usr/bin/python3
"""
Crew Manager GUI Application
============================

A comprehensive graphical interface for managing crew data with advanced features:

Core Features:
- Load and display CSV data files with sortable columns
- Filter data by columns with real-time search
- Create and manage custom crew groups
- Column visibility controls via View menu
- Resizable layout with adjustable panels
- Background script execution from workspace
- Export data to Excel format
- Auto-save window state and preferences
- Text-to-speech functionality for details view

Layout:
- Left panel: Controls, Groups, and Filters (narrow, fixed width)
- Right panel: Data table and Details view (expandable)
- Resizable divider between panels for user customization
- Status bar with progress indicators and tooltips

Technical Features:
- Background worker thread for non-blocking operations
- Auto-discovery and import of workspace Python modules
- Configurable window state persistence
- Error handling with user-friendly dialogs
- Comprehensive logging system
- TTS (pyttsx3) integration for selected text

Author: Generated via AI assistance
Date: May 2025
Version: 2.0 with enhanced layout and script execution
"""

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
    """
    Automatically discover and import all Python files in the workspace

    This function scans the current workspace for .py files and attempts to import
    them dynamically. This enables the GUI to have access to all workspace modules
    without requiring manual import statements.

    Returns:
        Tuple containing:
        - List[str]: Successfully imported module names
        - List[Tuple[str, str]]: Failed imports with (filename, error_message)

    Exclusions:
        - Current GUI file (to prevent self-import)
        - __pycache__ directories and .pyc files
        - Hidden files and directories (starting with .)
        - Common virtual environment directories (venv, env, node_modules)

    Note:
        Import failures are logged but don't halt the application startup.
        This allows the GUI to function even if some workspace modules have issues.
    """
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
            except (json.JSONDecodeError, KeyError, OSError):
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
            "tts_venv",
            ".venv",
            "node_modules",
            "build",
            "dist",
            ".pytest_cache",
            ".mypy_cache",
            "site-packages",
            "lib",
            "bin",
            "include",
            "share",
            ".tox",
            ".coverage",
            "htmlcov",
            ".idea",
            ".vscode",
            "migrations",
            "docs",
            "documentation",
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
                    # If we can't read the file, skip it for safety
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
        return [], [(str(workspace_root), str(e))]

        # Directories to skip
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

        for py_file in py_files:
            try:
                py_path = Path(py_file)
                relative_path = py_path.relative_to(workspace_root)

                # Skip files in excluded directories
                if any(skip_dir in relative_path.parts for skip_dir in skip_dirs):
                    continue

                # Skip excluded files
                if py_path.name in skip_files:
                    continue

                # Skip files matching problematic patterns
                if any(pattern in py_path.name for pattern in skip_patterns):
                    continue

                # Skip test files
                if py_path.name.startswith("test_") or "unittest" in py_path.name:
                    continue

                # Additional safety check: skip files that look like scripts rather than modules
                if py_path.name.lower() in {
                    "main.py",
                    "run.py",
                    "start.py",
                    "launch.py",
                }:
                    continue

                # Quick safety check: read first few lines to detect obvious script files
                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        first_lines = [f.readline().strip() for _ in range(10)]

                    # Skip files that look like scripts
                    script_indicators = [
                        'if __name__ == "__main__"',
                        "subprocess.call",
                        "subprocess.run",
                        "sys.argv",
                        "argparse",
                        "print(",  # Files with immediate print statements
                        "input(",  # Interactive scripts
                        "main()",  # Scripts with main function calls
                        "logging.basicconfig",  # Scripts that configure logging
                        "logger.info",  # Scripts with immediate logging
                        "speak(",  # Scripts with TTS functionality
                        "sys.exit",  # Scripts that exit immediately
                        "os.system",  # Scripts that run system commands
                        "plt.show",  # Scripts with matplotlib plots
                        "plt.plot",  # Scripts with immediate plotting
                    ]

                    file_content = "\n".join(first_lines).lower()
                    if any(
                        indicator in file_content for indicator in script_indicators
                    ):
                        logging.debug(
                            f"Skipping {py_path.name} - appears to be a script file"
                        )
                        continue

                    # Special check for files with immediate side effects
                    if "print(" in file_content and "loaded" in file_content:
                        logging.debug(
                            f"Skipping {py_path.name} - has print statements with side effects"
                        )
                        continue

                except (IOError, UnicodeDecodeError):
                    # If we can't read the file, skip it for safety
                    continue

                # Create module name from path
                module_name = str(relative_path.with_suffix(""))
                module_name = module_name.replace("/", ".").replace("\\", ".")

                # Handle files with spaces or special characters in names
                if " " in module_name or any(
                    char in module_name for char in (",", "-")
                ):
                    # Create a safe module name
                    safe_name = (
                        module_name.replace(" ", "_")
                        .replace(",", "_")
                        .replace("-", "_")
                    )
                    module_name = safe_name

                # Try to import the module
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec and spec.loader:
                    # Check if module is already loaded to avoid conflicts
                    if module_name in sys.modules:
                        imported_modules.append(f"{module_name} (already loaded)")
                        continue

                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    imported_modules.append(module_name)

            except (
                ImportError,
                SyntaxError,
            ) as e:
                # These are expected for some files
                failed_imports.append(
                    (str(relative_path), f"Import error: {str(e)[:100]}")
                )
                continue
            except Exception as e:
                failed_imports.append(
                    (str(relative_path), f"Unexpected error: {str(e)[:100]}")
                )
                logging.warning(f"Failed to auto-import {py_file}: {e}")
                continue

        # Log the results
        if imported_modules:
            logging.info(f"Auto-imported {len(imported_modules)} modules")

        if failed_imports:
            logging.info(
                f"Skipped {len(failed_imports)} modules (expected for some files)"
            )

        return imported_modules, failed_imports

    except Exception as e:
        logging.error(f"Auto-import process failed: {e}")
        return [], [(str(workspace_root), str(e))]


class CrewGUI:
    """Main GUI class for the Crew Management application.

    This class implements a comprehensive crew management interface with features for:

    Core Features:
    - CSV file import/export and crew data management
    - Dynamic table display with sorting and filtering capabilities
    - Script execution environment with Python interpreter integration
    - Real-time status updates and logging display

    User Interface Components:
    - Responsive PanedWindow layout with resizable sections
    - Menu bar with file operations and view controls
    - Data table with configurable column visibility
    - Script editor with syntax highlighting and execution controls
    - Console output display with scrollable text area
    - Status bar with operation feedback

    Data Management:
    - Automatic CSV file detection and loading
    - Support for various crew data formats
    - Data validation and error handling
    - Export functionality with formatting options

    Technical Features:
    - Multi-threaded background processing
    - Auto-import of workspace Python modules
    - Persistent window state and configuration
    - Keyboard shortcuts and event handling
    - Error logging and user feedback systems

    Attributes:
        root: Main tkinter window
        config: Configuration manager instance
        data: Current crew data (pandas DataFrame)
        ui_components: Dictionary of UI element references
        script_vars: Variables available in script execution context
        task_queue: Queue for background task management
        worker_thread: Background thread for long-running operations

    Example:
        root = tk.Tk()
        app = CrewGUI(root)
        root.mainloop()
    """

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the GUI application with all components and settings.

        Sets up the complete application environment including:
        - Main window configuration and menu system
        - Layout management with resizable panes
        - Data management and configuration systems
        - Background processing and auto-import functionality
        - Event bindings and keyboard shortcuts
        - Default data loading and window state restoration

        Args:
            root: The root tkinter window that will contain the application

        Raises:
            Exception: If critical initialization steps fail (logged and handled gracefully)

        Note:
            Initialization order is important - menu bar is created first, followed by
            layout setup, widget creation, event binding, and finally background services.
        """
        try:
            self.root = root
            self.root.title("Crew Manager")

            # Create menu bar before other UI elements
            self.create_menu_bar()

            self.config = Config()
            # self.setup_logging() # os is used here, but this line is commented out
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
        """Create comprehensive application menu system with organized commands.

        Builds a full-featured menu bar providing access to all major functionality:

        Menu Structure and Organization:

        File Menu:
        - Load Data (Ctrl+O): Import CSV/Excel files with format detection
        - Import (Ctrl+I): Import data from CSV/Excel files (similar to Load)
        - Save (Ctrl+S): Save current data to original or new file
        - Export (Ctrl+E): Export to Excel with formatting options
        - Exit: Graceful application termination with state saving

        Edit Menu:
        - Find (Ctrl+F): Quick access to filter input field
        - Clear Filter (Esc): Reset all filters and restore full data view
        - Provides essential editing and navigation operations

        View Menu:
        - Refresh (F5): Reload all views and refresh data display
        - Show Imported Modules: Display auto-imported module information
        - Columns Submenu: Dynamic column visibility management
        - Run Script Submenu: Execute workspace Python scripts
        - Refresh Scripts: Update script menu with current workspace files

        Dynamic Submenus:

        Column Visibility Submenu:
        - Dynamically populated based on current data headers
        - Individual column show/hide toggles
        - "Show All" and "Hide All" convenience commands
        - Persistent state across data reloads

        Script Execution Submenu:
        - Auto-discovery of Python files in workspace
        - Dynamic menu population with available scripts
        - Safe execution environment with error handling
        - Integration with background task system

        Menu Configuration:
        - Tearoff disabled (tearoff=0) for clean appearance
        - Keyboard shortcuts displayed in menu items
        - Logical grouping with separators for visual organization
        - Consistent command naming and organization

        Integration Features:
        - Connected to corresponding event handler methods
        - Keyboard shortcut integration with menu commands
        - Dynamic content updates based on application state
        - Proper focus management for input fields

        Technical Implementation:
        - Menu bar attached to root window configuration
        - Cascading menu structure for hierarchical organization
        - Lambda functions for parameter passing to handlers
        - Submenu references stored for dynamic updates

        Accessibility Features:
        - Keyboard navigation support
        - Mnemonic key access for quick operation
        - Clear visual hierarchy and organization
        - Consistent command placement across sessions

        Note:
            Menu creation occurs early in initialization to ensure all subsequent
            operations can use logging functionality.
        """
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
        """Set up keyboard shortcuts and event bindings for the application.

        Configures essential keyboard shortcuts for improved user experience:

        Keyboard Shortcuts:
        - Escape: Clear all filters and restore full data view
        - Ctrl+F: Focus on filter input field for quick search
        - Ctrl+S: Save current data (if implemented)
        - Ctrl+E: Export current data view (if implemented)
        - F5: Refresh all views and reload data

        Event Bindings:
        - Window close events for proper cleanup
        - Focus events for optimal user workflow
        - Selection events for data table and group list

        Integration:
        - Works seamlessly with menu commands
        - Provides alternative access to key functionality
        - Maintains consistency with standard application shortcuts
        - Supports efficient keyboard-driven workflows
        """
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
        """Restore previously saved window configuration and layout preferences.

        Provides seamless user experience by maintaining window state across sessions:

        Window Geometry Restoration:
        - Retrieves saved window size and position from configuration
        - Uses tkinter geometry() method to restore exact window dimensions
        - Maintains window placement on screen for consistent user experience
        - Handles cases where saved geometry may be invalid or off-screen

        Window Size Constraints:
        - Applies saved minimum window size constraints if available
        - Uses minsize() to prevent window from becoming unusably small
        - Parses "WIDTHxHEIGHT" format from configuration string
        - Ensures application remains functional regardless of window size

        Column Width Preservation:
        - Stores saved column widths in temporary _saved_column_widths attribute
        - Defers application until after data table is fully populated
        - Handles missing or invalid column width data gracefully
        - Maintains user customizations for table layout preferences

        Configuration Integration:
        - Uses self.config.get() for robust configuration retrieval
        - Handles missing configuration entries with appropriate defaults
        - Provides fallback behavior when configuration is unavailable
        - Ensures application starts successfully regardless of config state

        Error Handling:
        - Comprehensive exception catching for robust startup behavior
        - Detailed error logging for debugging configuration issues
        - Graceful failure that uses default window state when needed
        - Prevents configuration errors from blocking application startup

        Performance Considerations:
        - Minimal overhead during application initialization
        - Efficient configuration access with single calls per setting
        - Deferred column width application for optimal timing
        - Quick execution that doesn't delay user interface appearance

        User Experience Features:
        - Seamless restoration of previous session's window layout
        - Maintains user's preferred window size and position
        - Preserves customized column widths across sessions
        - Provides consistent interface appearance between sessions

        Integration Points:
        - Called during application initialization process
        - Coordinates with configuration management system
        - Works with table population events for column width timing
        - Supports window state saving for complete session management

        Data Handling:
        - Temporary storage in _saved_column_widths for later application
        - Safe parsing of geometry strings and dimension values
        - Validation of retrieved configuration data before use
        - Cleanup of temporary data after successful application

        Note:
            Column widths are stored temporarily and applied after table
            population to ensure columns exist before width configuration.
            This prevents errors from applying widths to non-existent columns.
        """
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
        """Preserve current window configuration for future sessions.

        Ensures user interface preferences persist across application restarts:

        Window Geometry Capture:
        - Retrieves current window size and position using geometry() method
        - Captures complete window state including dimensions and screen position
        - Stores geometry string in format "WIDTHxHEIGHT+X+Y" for precise restoration
        - Enables exact window placement recreation in future sessions

        Column Width Preservation:
        - Iterates through all visible data table columns
        - Captures current width settings for each column individually
        - Stores column width dictionary for structured preservation
        - Maintains user customizations of table layout preferences

        Configuration Management:
        - Uses self.config.set() for persistent storage of window state
        - Integrates with application configuration system seamlessly
        - Ensures settings are written to permanent storage
        - Provides centralized configuration management for all preferences

        Data Structure Organization:
        - Creates dictionary mapping column identifiers to width values
        - Uses column identifiers as keys for reliable restoration
        - Maintains referential integrity between save and load operations
        - Enables selective column width restoration if needed

        Error Handling:
        - Comprehensive exception catching for robust shutdown behavior
        - Detailed error logging for debugging configuration save issues
        - Graceful failure that doesn't interrupt application closing
        - Prevents save errors from affecting normal shutdown process

        Performance Considerations:
        - Efficient single-pass collection of all column widths
        - Minimal processing overhead during application shutdown
        - Quick execution that doesn't delay application closing
        - Streamlined configuration updates for fast persistence

        User Experience Features:
        - Automatic preservation of interface customizations
        - Seamless state persistence without user intervention
        - Maintains personalized layouts across sessions
        - Provides consistent interface experience over time

        Integration Points:
        - Typically called during application shutdown or close events
        - Coordinates with configuration system for data persistence
        - Works with window state loading for complete session management
        - Supports graceful application lifecycle management

        State Validation:
        - Captures actual current state rather than cached values
        - Ensures saved state reflects real window configuration
        - Provides accurate basis for future state restoration
        - Maintains synchronization between UI and saved preferences

        Note:
            This method should be called before application termination
            to ensure all user interface customizations are properly
            preserved for the next session. Typically bound to window
            close events or shutdown procedures.
        """
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
        """Execute long-running tasks in background thread without blocking UI.

        Provides responsive user interface through asynchronous task processing:

        Thread Architecture:
        - Runs in dedicated background thread separate from UI thread
        - Continuous execution loop using task queue for work distribution
        - Daemon thread design that terminates with main application
        - Prevents UI freezing during CPU-intensive or I/O operations

        Task Queue Processing:
        - Retrieves tasks from self.task_queue in FIFO order
        - Processes task tuples containing function, arguments, and callback
        - Blocks on empty queue until new tasks are available
        - Maintains orderly task execution sequence

        Task Execution Model:
        - Unpacks task components for structured function calls
        - Executes target function with provided arguments safely
        - Captures function results for potential callback processing
        - Isolates task execution errors from worker thread stability

        Callback Integration:
        - Uses root.after() for thread-safe UI updates from background
        - Schedules callback execution on main UI thread
        - Passes task results to callbacks for UI state updates
        - Maintains thread safety for all GUI operations

        Error Handling:
        - Comprehensive exception catching for robust task processing
        - Detailed error logging for debugging failed background tasks
        - Graceful task failure that doesn't terminate worker thread
        - Continues processing subsequent tasks after failures

        Queue Management:
        - Calls task_done() to mark task completion properly
        - Enables queue join() operations for synchronization
        - Maintains accurate queue state for monitoring
        - Supports clean shutdown procedures

        Performance Features:
        - Efficient blocking wait on empty queue
        - Minimal overhead for task dispatch and completion
        - Concurrent execution isolated from UI responsiveness
        - Optimized for handling multiple long-running operations

        Thread Safety:
        - Complete isolation of background processing from UI thread
        - Safe cross-thread communication via root.after()
        - No direct GUI manipulation from background thread
        - Proper synchronization for shared resource access

        Integration Points:
        - Works with run_in_background() for task submission
        - Coordinates with file loading and export operations
        - Supports data processing and import functionality
        - Enables responsive UI during intensive calculations

        Lifecycle Management:
        - Infinite loop design for continuous task processing
        - Proper cleanup on application termination
        - Exception resilience for stable long-term operation
        - Resource management for efficient memory usage

        Note:
            This worker thread is essential for maintaining UI responsiveness
            during file I/O, data processing, and other potentially blocking
            operations. All GUI updates must use callbacks via root.after().
        """
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
        """Submit functions for background execution to maintain UI responsiveness.

        Provides simple interface for asynchronous task execution without UI blocking:

        Task Submission Model:
        - Accepts any callable function with arbitrary arguments
        - Packages task components into structured tuple format
        - Queues task for background thread processing
        - Returns immediately without waiting for task completion

        Function Execution:
        - Background thread executes function with provided arguments
        - Maintains function context and argument passing integrity
        - Isolates execution from main UI thread completely
        - Supports any callable including methods, functions, and lambdas

        Callback Integration:
        - Optional callback function for result processing
        - Callback executed on main UI thread for thread safety
        - Receives function result as argument for UI updates
        - Enables seamless integration with GUI updates

        Threading Architecture:
        - Leverages existing background worker thread infrastructure
        - Uses thread-safe queue for cross-thread communication
        - Maintains proper execution isolation for stability
        - Supports concurrent execution of multiple background tasks

        Performance Benefits:
        - Immediate return prevents UI freezing during long operations
        - Non-blocking submission for responsive user interface
        - Efficient task queuing with minimal overhead
        - Scalable approach for handling multiple concurrent operations

        Usage Patterns:
        - File I/O operations: Loading, saving, and export functions
        - Data processing: Complex calculations and transformations
        - Network operations: API calls and data synchronization
        - Any operation that might block UI for noticeable time

        Error Handling:
        - Background worker handles task execution errors safely
        - Failed tasks don't affect other queued operations
        - Error logging provides debugging information
        - Graceful degradation maintains application stability

        Thread Safety:
        - Complete isolation of background execution from UI thread
        - Safe callback scheduling via root.after() mechanism
        - No direct GUI manipulation from background context
        - Proper synchronization for shared resource access

        Integration Features:
        - Works seamlessly with _background_worker() infrastructure
        - Supports complex workflows with chained operations
        - Enables progress updates via callback mechanisms
        - Facilitates responsive user experience design

        Args:
            func: Callable function to execute in background thread
            *args: Arguments to pass to the function during execution
            callback: Optional function to call with result on UI thread

        Note:
            Functions executed in background should not directly manipulate
            GUI components. Use callbacks for all UI updates to maintain
            thread safety and prevent application instability.
        """
        self.task_queue.put((func, args, callback))

    def setup_logging(self) -> None:
        """Configure logging system for the application.

        Sets up basic logging configuration with INFO level and standardized
        formatting for all application log messages. This provides consistent
        logging output for debugging and monitoring application behavior.

        Configuration:
        - Level: INFO (captures informational messages and above)
        - Format: Timestamp - Level - Message for easy parsing
        - Output: Console output for real-time monitoring

        Note:
            This is called early in initialization to ensure all subsequent
            operations can use logging functionality.
        """
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def setup_state(self) -> None:
        """Initialize application state variables and database connection.

        Establishes the core data structures and database connection needed
        for the application to function. This includes:

        Database Setup:
        - Creates DatabaseManager instance for data persistence
        - Handles database connection and schema initialization

        State Variables:
        - groups: Dictionary storing group data configurations
        - current_groups: Active group selections and filters
        - group_preview: Temporary group data for preview operations
        - current_columns: List of currently displayed table columns
        - current_data: Active dataset being displayed
        - headers: Column headers for the current dataset

        Note:
            All state variables are initialized to empty/default values
            and will be populated when data is loaded.
        """
        self.db = DatabaseManager()
        self.groups = {}  # Store groups data
        self.current_groups = {}
        self.group_preview = {}
        self.current_columns = []
        self.current_data = []
        self.headers = []  # Initialize empty headers
        self.column_visibility = {}  # Initialize column visibility tracking

    def create_main_layout(self) -> None:
        """Create the main application layout with resizable panels.

        Establishes the primary GUI structure using a responsive layout system:

        Layout Structure:
        - Root window: 1200x800 default size, 800x600 minimum
        - Main frame: Primary container with padding for visual separation
        - PanedWindow: Horizontal divider allowing user-resizable sections
        - Left panel: Fixed-width (280px) control and navigation area
        - Right panel: Expandable content area for data display

        Left Panel Sections (top to bottom):
        - Controls: Fixed height for action buttons
        - Groups: Expandable section for group management
        - Filters: Fixed height for filter controls

        Right Panel Sections (top to bottom):
        - Data view: Primary area (75% height) for table display
        - Details: Secondary area (25% height) for item details

        Grid Configuration:
        - Uses tkinter grid manager with proper weight distribution
        - Left frame: Non-expandable (weight=0) for consistent width
        - Right frame: Expandable (weight=1) to use available space
        - Row weights configured for optimal space distribution

        Note:
            Frame propagation is disabled on left panel to maintain fixed width,
            preventing it from shrinking when content changes.
        """
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
        """Create all GUI components in the correct order.

        Initializes all user interface elements following a logical creation order
        to ensure proper parent-child relationships and event binding:

        Creation Order:
        1. Control section: Action buttons (Load, Save, Export)
        2. Group section: Group management and selection controls
        3. Filter section: Data filtering and search interface
        4. Data section: Main table for displaying crew data
        5. Details section: Detail view for selected items
        6. Status bar: Application status and feedback display

        Error Handling:
        - Each section creation is monitored for exceptions
        - Failures are logged with specific error details
        - Critical failures are re-raised to prevent incomplete UI

        Dependencies:
        - Requires main layout to be created first
        - Each section depends on its parent frame being available
        - Status bar should be created last for proper layering

        Raises:
            Exception: If any critical widget creation fails, ensuring
                      the application doesn't start with incomplete UI
        """
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
        """Create an informative status bar with tooltip support.

        Builds a professional status display system at the bottom of the application:

        Visual Design:
        - Frame with groove relief and border for visual separation
        - Positioned at bottom (row=1) with full width expansion
        - Consistent padding and spacing for professional appearance
        - Fixed height (weight=0) to maintain layout stability

        Status Display Components:
        - StringVar for dynamic message updates
        - Label widget with left-aligned text for readability
        - Internal padding (5,2) for comfortable text spacing
        - Full width expansion to utilize available space

        Interactive Features:
        - Hover tooltip for long status messages
        - Enter/Leave event bindings for tooltip management
        - Automatic tooltip creation for messages over 50 characters
        - Graceful tooltip cleanup on mouse leave

        Layout Configuration:
        - Grid positioning with proper weight distribution
        - Root window row configuration for fixed status bar height
        - Column expansion to fill window width
        - Consistent spacing with main application frame

        Message Management:
        - Default "Ready" state for application idle
        - Dynamic updates via StringVar for real-time feedback
        - Support for operational status and progress information
        - Error state display capability

        Technical Implementation:
        - Exception handling for robust status bar creation
        - Tooltip system using tkinter.tix for enhanced UX
        - Event binding for responsive user interaction
        - Proper widget reference storage for dynamic updates

        Integration Points:
        - Connected to update_status method for message changes
        - Integrated with application event system
        - Supports long-running operation feedback
        - Provides user feedback for all major operations

        Note:
            The status bar is created last in the widget hierarchy
            to ensure proper layering and event handling precedence.
        """
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
        """Update status bar with new message and provide user feedback.

        Provides real-time status updates throughout the application lifecycle:

        Message Processing:
        - Accepts string messages for display in status bar
        - Handles empty/None messages by defaulting to "Ready" state
        - Ensures consistent message formatting and display
        - Supports both brief and detailed status information

        Display Updates:
        - Immediately updates status bar via StringVar.set()
        - Forces GUI refresh with update_idletasks() for responsiveness
        - Maintains visual consistency across all status changes
        - Provides instant user feedback for operations

        Error Handling:
        - Comprehensive exception catching for robust operation
        - Detailed error logging for debugging status update failures
        - Graceful degradation when status updates fail
        - Prevents status update errors from affecting main operations

        Usage Patterns:
        - Operation start: "Loading data..." or "Processing..."
        - Progress updates: "Loaded 150 records" or "Processing file 3 of 5"
        - Completion: "Data loaded successfully" or "Export completed"
        - Error states: "Failed to load file" or "Import error"
        - Idle state: "Ready" for normal operation availability

        Performance Considerations:
        - Efficient StringVar updates without full widget recreation
        - Minimal GUI thread impact with focused refresh operations
        - Safe for frequent calls during long-running operations
        - Non-blocking updates that don't interrupt user workflow

        Integration Features:
        - Called by background operations for progress reporting
        - Used by event handlers for immediate feedback
        - Supports tooltip system for detailed message display
        - Maintains message history context for debugging

        Args:
            message: Status text to display, empty/None defaults to "Ready"

        Note:
            This method is safe to call frequently and from background
            threads, providing essential user feedback throughout the
            application's operation lifecycle.
        """
        try:
            if not message:
                message = "Ready"
            self.status_var.set(message)
            self.root.update_idletasks()
        except Exception as e:
            logging.error(f"Failed to update status: {e}")

    def _show_status_tooltip(self, event: tk.Event) -> None:
        """Display detailed tooltip for long status messages on hover.

        Note: Uses simple Label widget instead of deprecated tix.Balloon
        """
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
        """Clean up and hide status tooltip when mouse leaves area."""
        if hasattr(self, "status_tooltip") and self.status_tooltip:
            try:
                self.status_tooltip.destroy()
                self.status_tooltip = None
            except tk.TclError:
                # Tooltip already destroyed
                self.status_tooltip = None

    def create_control_section(self) -> None:
        """Create the main control panel with action buttons.

        Builds the primary interaction area containing essential file operations
        and data management controls:

        Layout:
        - LabelFrame container with "Controls" title and padding
        - Positioned in left panel, row 0 (top section)
        - Sticky 'ew' for full width within parent container

        Control Buttons:
        - Load Data: Opens file dialog to import CSV/Excel files
        - Save: Saves current data to the loaded file or prompts for location
        - Export: Exports data to Excel format with formatting options

        Button Configuration:
        - Full width (fill='x') for consistent appearance
        - Vertical padding (pady=2) for proper spacing
        - Connected to respective event handlers via command parameter

        Error Handling:
        - Wraps creation in try-catch for graceful failure handling
        - Logs specific error details for debugging
        - Re-raises exceptions to prevent incomplete UI initialization

        Note:
            This section is positioned first in the left panel and maintains
            a fixed height to provide consistent access to core functions.
        """
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
        """Create the group management interface for organizing crew data.

        Builds an interactive group management system that allows users to:

        Main Components:
        - LabelFrame container titled "Groups" with padding for visual clarity
        - Treeview widget for displaying group hierarchy and information
        - Vertical scrollbar for navigation through large group lists
        - Right-click context menu for group operations

        Treeview Configuration:
        - Single selection mode (selectmode='browse') for focused interaction
        - Height of 10 rows for optimal display within left panel
        - Expandable (fill='both', expand=True) to use available space
        - Vertical scrolling support for large datasets

        Context Menu Features:
        - Delete operation for removing selected groups
        - Right-click activation (Button-3 event binding)
        - Tearoff disabled for clean appearance

        Layout Structure:
        - Positioned in left panel, row 1 (middle section)
        - Sticky 'nsew' for full expansion within parent
        - Treeview packed first, scrollbar aligned to right
        - Scrollbar synchronized with treeview scroll commands

        Data Display:
        - Groups shown with member count and skill information
        - Hierarchical display for nested group structures
        - Real-time updates when data changes

        Error Handling:
        - Comprehensive exception catching and logging
        - Re-raises exceptions to prevent incomplete initialization
        - Specific error messages for debugging assistance

        Note:
            This section is expandable (weight=1) in the left panel layout,
            allowing it to grow/shrink based on available space.
        """
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
        """Display context menu for group management operations.

        Provides user-friendly right-click functionality for group manipulation:

        Event Processing:
        - Captures right-click (Button-3) events on group list
        - Uses identify_row() to determine which group was clicked
        - Validates that click occurred on an actual group item
        - Prevents menu display for empty areas of the treeview

        Selection Management:
        - Automatically selects the group under the cursor
        - Ensures visual feedback for the target of menu operations
        - Updates selection state before displaying context menu
        - Maintains consistent selection behavior across interactions

        Menu Positioning:
        - Uses event.x_root and event.y_root for absolute screen coordinates
        - Positions menu at cursor location for intuitive interaction
        - Ensures menu appears at the exact click point
        - Handles screen edge cases automatically via tkinter

        User Experience Features:
        - Immediate visual response to right-click actions
        - Context-sensitive menu that only appears for valid targets
        - Professional interaction pattern following GUI conventions
        - Clean menu presentation without visual artifacts

        Error Handling:
        - Comprehensive exception catching for robust operation
        - Detailed error logging for debugging menu issues
        - Graceful failure that doesn't interrupt workflow
        - Prevents menu display errors from affecting other operations

        Integration Points:
        - Connected to group_list Button-3 event binding
        - Triggers display of self.group_menu with delete operations
        - Coordinates with selection events for consistent state
        - Supports future expansion of context menu options

        Args:
            event: Right-click event containing cursor position and timing

        Note:
            Menu only appears when clicking on actual group items,
            preventing confusion when clicking in empty treeview areas.
        """
        try:
            # Select item under cursor
            item = self.group_list.identify_row(event.y)
            if item:
                self.group_list.selection_set(item)
                self.group_menu.post(event.x_root, event.y_root)
        except Exception as e:
            logging.error(f"Error showing group menu: {e}")

    def _delete_selected_group(self) -> None:
        """Delete the currently selected group."""
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
        """Create the data filtering and search interface.

        Builds a comprehensive filtering system for data exploration:

        Container Structure:
        - LabelFrame with "Filters" title and consistent padding
        - Positioned in left panel, row 2 (bottom section)
        - Fixed height design to maintain consistent layout

        Filter Components:
        1. Column Selection Dropdown:
           - Combobox widget for choosing filter target column
           - "All Columns" default option for broad searches
           - Read-only state to prevent invalid inputs
           - Full width (fill='x') for consistent appearance

        2. Filter Input Field:
           - Entry widget connected to filter_var StringVar
           - Supports text-based filtering and pattern matching
           - Enter key binding for quick filter application
           - Full width layout with vertical spacing

        3. Apply Filter Button:
           - Triggers filter operation via _on_apply_filter method
           - Full width design for easy access
           - Consistent spacing with other controls

        Variable Management:
        - filter_var: StringVar for current filter text
        - column_var: StringVar for selected column ("All Columns" default)
        - Both variables support real-time updates and event binding

        Layout Configuration:
        - Vertical packing (pack) for stacked arrangement
        - Consistent vertical padding (pady=2) between elements
        - Full width (fill='x') for uniform appearance
        - Sticky 'ew' positioning within parent frame

        User Interaction Features:
        - Column-specific filtering for precise data exploration
        - Global search across all columns when "All Columns" selected
        - Real-time filter application with immediate visual feedback
        - Keyboard shortcuts for efficient workflow

        Error Handling:
        - Exception wrapping with specific error logging
        - Re-raises critical failures to prevent incomplete UI
        - Detailed error messages for debugging support

        Note:
            This section maintains fixed height in the layout to ensure
            controls remain accessible regardless of group section expansion.
        """
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
        """Create the main data display table with advanced features.

        Constructs a sophisticated data visualization interface featuring:

        Container Architecture:
        - LabelFrame titled "Data View" with consistent padding
        - Positioned in right panel, row 0 (primary display area)
        - Nested frame structure for complex scrollbar management
        - Expandable design (sticky='nsew') to utilize available space

        Table Configuration:
        - Treeview widget in "headings" mode for tabular data display
        - Single row selection (selectmode="browse") for focused interaction
        - Professional styling with custom fonts and row heights
        - Column header click support for interactive sorting

        Scrolling System:
        - Dual scrollbars for both vertical and horizontal navigation
        - Synchronized scrolling between table and scrollbar controls
        - Proper grid layout with weight distribution for responsive design
        - Scrollbars positioned at edges (right/bottom) for intuitive use

        Advanced Features:
        - Dynamic column width adjustment and persistence
        - Saved column width restoration after data loading
        - Custom event handling for table population
        - Click-to-sort functionality on column headers

        Visual Styling:
        - Professional row height (25px) for readability
        - Bold font headers for clear column identification
        - Custom treeview style configuration
        - Consistent spacing and padding throughout

        Grid Weight Configuration:
        - data_frame: Full expansion (weight=1) in both directions
        - table_frame: Full expansion within data_frame
        - Proper weight distribution for responsive resizing
        - Maintains proportions during window size changes

        Event Integration:
        - Column click binding for sorting operations
        - Table population events for width restoration
        - Configure events for dynamic layout adjustments
        - Selection events for detail view updates

        Column Width Management:
        - Automatic restoration of saved column widths
        - Cleanup of temporary width storage after application
        - Dynamic width adjustment based on content
        - Minimum width constraints for usability

        Error Handling:
        - Comprehensive exception monitoring and logging
        - Re-raises critical failures to ensure complete UI
        - Specific error context for debugging assistance
        - Graceful degradation when possible

        Note:
            This section receives the majority of screen space (weight=3)
            in the right panel layout, emphasizing its role as the primary
            data interaction interface.
        """
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
                if hasattr(self, "_saved_column_widths"):
                    for col, width in self._saved_column_widths.items():
                        # Only set width if column exists
                        if col in self.data_table["columns"]:
                            self.data_table.column(col, width=width)
                    delattr(self, "_saved_column_widths")  # Clean up after applying

            # Bind to table population event
            self.data_table.bind("<<TreeviewPopulated>>", apply_saved_column_widths)

        except Exception as e:
            logging.error(f"Failed to create data section: {e}")
            raise

    def create_details_section(self) -> None:
        """Create the details view section for displaying selected item information.

        Builds a comprehensive details display interface in the right panel:

        Container Architecture:
        - LabelFrame titled "Details View" with consistent padding
        - Positioned in right panel, row 1 (secondary display area)
        - Expandable design (sticky='nsew') to utilize available space
        - Professional styling consistent with other application sections

        Text Display Component:
        - Text widget with rich formatting capabilities
        - Professional monospace font for structured data display
        - Scrollbar support for long detail content
        - Read-only configuration to prevent accidental edits

        Scrolling System:
        - Vertical scrollbar for navigating long details
        - Synchronized scrolling between text widget and scrollbar
        - Proper grid layout with weight distribution
        - Positioned at right edge for intuitive use

        Visual Styling:
        - Consistent padding and spacing with other sections
        - Professional appearance with border and relief
        - Proper font selection for readability
        - Integrated with application color scheme

        Layout Configuration:
        - Grid positioning in right panel row 1
        - Weight=1 for proportional space allocation
        - Full expansion to utilize available vertical space
        - Responsive design for different window sizes

        Integration Points:
        - Connected to _update_details_view method for content updates
        - Linked to table selection events for automatic updates
        - Supports TTS functionality via _setup_details_tts
        - Provides context for selected item examination

        Text Widget Features:
        - Multi-line text display with word wrapping
        - Support for formatted text and structure
        - Clear content management via delete/insert operations
        - Professional font rendering for data presentation

        Error Handling:
        - Comprehensive exception monitoring and logging
        - Re-raises critical failures to ensure complete UI
        - Specific error context for debugging assistance
        - Graceful degradation when possible

        Note:
            This section receives less space (weight=1) compared to the
            data table (weight=3) but provides essential detailed view
            functionality for examining individual records.
        """
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
                self.data_table.bind("<<TreeviewSelect>>", self._on_data_select)

            # Setup TTS functionality if available
            self._setup_details_tts()

        except Exception as e:
            logging.error(f"Failed to create details section: {e}")
            raise

    def _setup_details_tts(self) -> None:
        """Set up Text-to-Speech functionality for the details view.

        Creates right-click context menu with TTS options when TTS is available.
        """
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
        """Read selected text from details view using TTS."""
        if not TTS_AVAILABLE:
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
                import pyttsx3

                engine = pyttsx3.init()
                engine.say(selected_text)
                engine.runAndWait()

        except Exception as e:
            logging.error(f"TTS selection error: {e}")

    def _read_all_details(self) -> None:
        """Read all text from details view using TTS."""
        if not TTS_AVAILABLE:
            return

        try:
            all_text = self.details_text.get("1.0", tk.END)
            if all_text.strip():
                import pyttsx3

                engine = pyttsx3.init()
                engine.say(all_text)
                engine.runAndWait()

        except Exception as e:
            logging.error(f"TTS all details error: {e}")

    def _read_status(self) -> None:
        """Read current status aloud using TTS."""
        if not TTS_AVAILABLE:
            return

        try:
            if hasattr(self, "status_var") and self.status_var:
                status_text = self.status_var.get()
                if status_text.strip():
                    import pyttsx3

                    engine = pyttsx3.init()
                    engine.say(status_text)
                    engine.runAndWait()
        except Exception as e:
            logging.error(f"TTS status error: {e}")

    def _read_selected_item(self) -> None:
        """Read selected item details aloud using TTS."""
        if not TTS_AVAILABLE:
            return

        try:
            if hasattr(self, "data_table"):
                selection = self.data_table.selection()
                if selection:
                    item_data = self.data_table.item(selection[0])
                    if "values" in item_data and item_data["values"]:
                        text = (
                            f"Selected item: {', '.join(map(str, item_data['values']))}"
                        )
                        import pyttsx3

                        engine = pyttsx3.init()
                        engine.say(text)
                        engine.runAndWait()
        except Exception as e:
            logging.error(f"TTS selected item error: {e}")

    def _stop_reading(self) -> None:
        """Stop TTS if currently running."""
        if not TTS_AVAILABLE:
            return

        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.stop()
        except Exception as e:
            logging.error(f"TTS stop error: {e}")

    # Callback methods
    def _on_data_loaded(self, result: Tuple[List[List[Any]], List[str]]) -> None:
        """Callback when data loading is complete."""
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

    # ...existing code...

    def _on_column_click(self, event: tk.Event) -> None:
        """Handle interactive column header clicks for data sorting functionality.

        Provides sophisticated click-to-sort capabilities for enhanced data navigation:

        Event Detection:
        - Uses identify_region() to detect clicks specifically on column headers
        - Filters out clicks on data rows or other treeview areas
        - Ensures sorting only activates for intended header interactions
        - Validates event coordinates for precise region identification

        Column Identification:
        - Extracts column identifier from click coordinates
        - Converts tkinter column format (#1, #2, etc.) to zero-based indices
        - Maps visual columns to internal data structure positions
        - Handles dynamic column configurations reliably

        Sort State Management:
        - Maintains persistent sort state in _last_sort dictionary
        - Tracks both current sort column and direction
        - Toggles sort direction for repeated clicks on same column
        - Resets to ascending when switching to different column

        Data Sorting Process:
        - Extracts all visible table items with their data values
        - Creates sortable tuples of (value, item_id) for processing
        - Applies sort() with reverse parameter for direction control
        - Maintains item identity throughout sorting operation

        Visual Feedback:
        - Updates column headers with directional indicators (↑/↓)
        - Shows clear visual cue for current sort column and direction
        - Clears indicators from previously sorted columns
        - Provides immediate user feedback for sort operations

        Table Reorganization:
        - Uses move() method to rearrange items in sorted order
        - Preserves all data relationships during reordering
        - Maintains selection state when possible
        - Updates display efficiently without full rebuild

        Header Management:
        - Dynamically updates column header text with sort indicators
        - Preserves original header text from self.headers array
        - Handles column header formatting consistently
        - Manages header state across multiple sort operations

        Error Handling:
        - Comprehensive exception catching for robust sorting
        - Detailed error logging for debugging sort issues
        - Graceful failure that maintains current table state
        - Prevents sort errors from corrupting data display

        Performance Considerations:
        - Efficient tuple creation for sort operations
        - Single-pass table reorganization after sorting
        - Minimal UI updates for responsive user experience
        - Optimized for large datasets with reasonable performance

        Integration Features:
        - Bound to data table Button-1 event for standard interaction
        - Coordinates with data display and filtering systems
        - Maintains sort state across data refreshes when possible
        - Supports complex data types through string conversion

        Args:
            event: Mouse click event containing position and timing information

        Note:
            Sorting operates on displayed data only and may interact
            with active filters. Sort state is maintained independently
            of data filtering operations for consistent user experience.
        """
        try:
            region = self.data_table.identify_region(event.x, event.y)
            if region == "heading":
                column = self.data_table.identify_column(event.x)
                column_id = int(column[1]) - 1  # Convert #1 to 0, #2 to 1, etc.

                # Get all items
                items = [
                    (self.data_table.set(item, column), item)
                    for item in self.data_table.get_children("")
                ]

                # Toggle sort direction
                if not hasattr(self, "_last_sort"):
                    self._last_sort = {"column": None, "reverse": False}

                if self._last_sort["column"] == column:
                    self._last_sort["reverse"] = not self._last_sort["reverse"]
                else:
                    self._last_sort["column"] = column
                    self._last_sort["reverse"] = False

                # Sort items
                items.sort(reverse=self._last_sort["reverse"])

                # Rearrange items in sorted order
                for index, (_, item) in enumerate(items):
                    self.data_table.move(item, "", index)

                # Update column header to show sort direction
                for col in self.data_table["columns"]:
                    if col == column:
                        direction = " ↓" if self._last_sort["reverse"] else " ↑"
                        text = self.headers[column_id] + direction
                    else:
                        text = self.headers[
                            int(col[3:])
                        ]  # Remove "col" prefix to get index
                    self.data_table.heading(col, text=text)

        except Exception as e:
            logging.error(f"Error handling column click: {e}")

    def _apply_filter(
        self, data: List[Any], filter_text: str, column_index: int = None
    ) -> List[Any]:
        """Apply text-based filtering to tabular data with flexible targeting.

        Provides comprehensive data filtering capabilities for enhanced user navigation:

        Filter Processing:
        - Converts filter text to lowercase for case-insensitive matching
        - Supports both column-specific and global filtering modes
        - Uses substring matching for flexible pattern detection
        - Returns filtered subset maintaining original data structure

        Column-Specific Filtering:
        - Targets single column when column_index is provided
        - Searches only the specified column for matching text
        - Enables precise filtering for focused data exploration
        - Optimizes performance by limiting search scope

        Global Filtering:
        - Searches across all columns when column_index is None
        - Uses any() function for efficient multi-column scanning
        - Catches matches in any field of each data row
        - Provides broad search capability for general exploration

        Matching Algorithm:
        - Uses str.find() for substring detection (returns >= 0 for matches)
        - Handles various data types by converting to string first
        - Case-insensitive comparison for user-friendly searching
        - Preserves original data formatting in results

        Data Preservation:
        - Returns complete rows that match filter criteria
        - Maintains original data structure and relationships
        - Preserves column order and data types
        - No modification of source data during filtering

        Performance Optimizations:
        - List comprehension for efficient filtering operations
        - Single-pass scanning through data rows
        - Minimal string operations per comparison
        - Early termination for any() evaluations in global mode

        Error Resilience:
        - Handles mixed data types gracefully via str() conversion
        - Processes None values safely without exceptions
        - Robust against empty or malformed data rows
        - Maintains filtering capability with inconsistent data

        Args:
            data: List of data rows (each row is a list/tuple of values)
            filter_text: Search term to match against data (case-insensitive)
            column_index: Optional column index for targeted filtering,
                         None for global search across all columns

        Returns:
            List[Any]: Filtered data rows matching the search criteria,
                      preserving original structure and content

        Note:
            Filter uses substring matching rather than exact matching,
            enabling flexible user searches without requiring precise
            text entry. Empty filter_text returns all data unchanged.
        """
        filter_text = filter_text.lower()
        if column_index is not None:
            # Filter specific column
            return [
                row
                for row in data
                if str(row[column_index]).lower().find(filter_text) >= 0
            ]
        else:
            # Filter all columns
            return [
                row
                for row in data
                if any(str(cell).lower().find(filter_text) >= 0 for cell in row)
            ]

    def _update_groups_view(self) -> None:
        """Refresh the group management display with current group data.

        Provides comprehensive group visualization with detailed information display:

        Display Refresh Process:
        - Clears all existing items from group treeview for clean update
        - Rebuilds display from current self.groups dictionary
        - Ensures display reflects latest group membership changes
        - Maintains visual consistency across group operations

        Column Configuration:
        - Initializes treeview columns on first run for optimal layout
        - Sets up four-column display: Name, Member Count, Primary, Secondary
        - Configures appropriate column widths for readable display
        - Establishes minimum widths to prevent layout collapse

        Header Setup:
        - "Group Name" in main tree column (#0) for hierarchical display
        - "#" column shows member count for quick group size reference
        - "Primary" column displays dominant primary skill in group
        Visual Organization:
        - Groups displayed with consistent formatting and spacing
        - Member count provides immediate group size awareness
        - Skill columns enable quick group capability assessment
        - Professional layout with optimized column proportions

        Layout Management:
        - Name column: 150px width, 100px minimum for group identification
        - Member count: 50px width, 30px minimum for compact display
        - Skill columns: 100px width each, 50px minimum for readability
        - Responsive design maintains usability across window sizes

        Data Integrity:
        - Only processes groups with valid names and member data
        - Handles malformed or incomplete group data safely
        - Prevents display corruption from invalid group structures
        - Maintains consistent display state regardless of data quality

        Error Handling:
        - Comprehensive exception catching for robust operation
        - Detailed error logging for debugging display issues
        - Graceful failure that maintains current group view
        - Prevents group display errors from affecting other operations

        Integration Features:
        - Called after group creation, deletion, or modification
        - Coordinates with group selection and filtering systems
        - Updates automatically when data changes occur
        - Maintains group view consistency across operations

        Note:
            This method completely rebuilds the group display rather than
            performing incremental updates, ensuring consistency and
            preventing display artifacts from partial updates.
        """
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
        """Handle user selection of groups for focused data viewing.

        Provides group-focused data display functionality with seamless integration:

        Selection Processing:
        - Captures group selection events from treeview widget
        - Extracts selected item identifier for group lookup
        - Validates selection exists before processing
        - Retrieves group name from treeview item data

        Group Validation:
        - Verifies selected group exists in self.groups dictionary
        - Prevents errors from stale or invalid group references
        - Handles cases where groups may have been deleted
        - Ensures data integrity before view updates

        Data View Integration:
        - Calls _update_data_view with group-specific data only
        - Filters main data table to show only group members
        - Maintains all existing table functionality for filtered view
        - Preserves column visibility and sorting preferences

        User Feedback:
        - Updates status bar with current group name
        - Provides clear indication of active group filter
        - Gives users confirmation of successful group selection
        - Shows context for all subsequent data operations

        View State Management:
        - Temporarily overrides global data view with group focus
        - Maintains group selection context until changed
        - Allows return to full data view via other controls
        - Preserves original data while showing filtered subset

        Event Handling:
        - Responds to standard treeview selection events
        - Processes single-selection mode interactions
        - Handles rapid selection changes smoothly
        - Maintains responsiveness during frequent group switching

        Error Resilience:
        - Comprehensive exception catching for robust operation
        - Detailed error logging for debugging selection issues
        - Graceful failure that maintains current view state
        - Prevents selection errors from corrupting data display

        Integration Features:
        - Coordinates with filtering and search systems
        - Maintains compatibility with data table operations
        - Supports export operations on filtered group data
        - Enables group-specific data analysis workflows

        Performance Considerations:
        - Efficient group lookup using dictionary access
        - Minimal data processing for view updates
        - Fast response to user selection changes
        - Optimized for frequent group switching operations

        Args:
            event: Selection event containing timing and selection information

        Note:

        Note:
                       Group selection creates a temporary filtered view of the data
            table, allowing users to focus on specific group members while
            maintaining access to all standard data operations and features.
        """
        try:
            selection = self.group_list.selection()
            if selection:
                item_id = selection[0]
                group_name = self.group_list.item(item_id)["text"]
                if group_name in self.groups:
                    # Update data view with just this group's data
                    self._update_data_view(self.groups[group_name])
                    self.update_status(f"Showing group: {group_name}")
        except Exception as e:
            logging.error(f"Error handling group selection: {e}")

    def _on_data_select(self, event: tk.Event) -> None:
        """Handle user selection of data rows for detailed information display.

        Provides seamless integration between table selection and detail views:

        Selection Processing:
        - Captures row selection events from main data table
        - Extracts selected item identifier for data retrieval
        - Validates selection exists before processing
        - Handles empty selections gracefully without errors

        Data Extraction:
        - Retrieves complete item data from selected table row
        - Accesses both displayed values and internal item structure
        - Preserves data relationships and formatting
        - Maintains data integrity during detail view updates

        Detail View Integration:
        - Calls _update_details_view with selected row data
        - Triggers formatted display of complete row information
        - Enables detailed examination of individual records
        - Provides context for single-record analysis

        User Experience Features:
        - Immediate response to row selection changes
        - Seamless transition between table and detail views
        - Maintains selection context across view operations
        - Provides intuitive data exploration workflow

        Event Handling:
        - Responds to standard TreeviewSelect events
        - Processes single-selection mode interactions efficiently



        - Handles rapid selection changes without conflicts
        - Maintains responsive user interface performance

        Error Resilience:
        - Comprehensive exception catching for robust operation
        - Detailed error logging for debugging selection issues
        - Graceful failure that maintains current detail view
        - Prevents selection errors from affecting table display

        Performance Considerations:
        - Efficient item data retrieval using direct access
        - Minimal processing overhead for selection changes
        - Quick response to user selection interactions
        - Optimized for frequent selection change operations

        Integration Points:
        - Coordinates with detail view display system
        - Works with data formatting and file output features
        - Supports export operations for selected records
        - Enables context-sensitive data operations

        Data Flow:
        - Table selection triggers detail view update
        - Selected data flows to formatting and display systems
        - Maintains data consistency throughout selection process
        - Preserves original data structure and content

        Args:
            event: Selection event containing timing and selection information

        Note:
            Selection events trigger automatic detail view updates,
            providing immediate access to complete record information
            and enabling detailed data examination workflows.
        """
        try:
            selection = self.data_table.selection()
            if selection:
                item_id = selection[0]
                item_data = self.data_table.item(item_id)
                if item_data:
                    self._update_details_view(item_data)
        except Exception as e:
            logging.error(f"Error handling data selection: {e}")

    def _on_apply_filter(self) -> None:
        """Process user filter requests and update data display accordingly.

               Provides comprehensive filtering functionality with context-sensitive behavior:

               Input Processing:
               - Retrieves filter text from UI input field with whitespace trimming
               - Extracts selected column target from dropdown selection
               - Validates column selection against current header structure
               - Handles both specific column and global filtering modes

               Column Target Resolution:
               - Maps selected column name to internal column index
               - Falls back to global search when column mapping fails
               - Supports "All Columns" option for comprehensive searching
               - Maintains robust operation with dynamic column configurations

               Context-Aware Filtering:
               - Applies filters to currently active data view context
               - Resets active group selection for scoped filtering
               - Falls back to full dataset when no group is selected
               - Maintains user workflow continuity across filter operations

               Filter Group Creation:
               - Creates named filter groups for filtered result sets
               - Uses descriptive naming based on column and filter text
               - Adds filter groups to group management system automatically
               - Enables filter result persistence and reuse

               Filter Group Management:
               - Automatically selects newly created filter groups
               - Scrolls to show new filter group in group list
               - Provides visual feedback for successful filter creation

               - Integrates seamlessly with existing group functionality

               View Reset Functionality:
               - Clears filters when filter text is empty
               - Restores previous view context (group or full data)
               - Maintains consistent behavior for filter clearing
               - Provides intuitive user experience for filter management

               Status Communication:
               - Updates status bar with filter operation results
               - Provides clear feedback for filter success or clearing
               - Includes descriptive information about applied filters
               - Maintains user awareness of current data view state

               Error Handling:
               - Comprehensive exception catching for robust operation
               - Detailed error logging for debugging filter issues
               - User-friendly error dialogs for filter failures
               - Graceful degradation that maintains current view state

               Performance Considerations:
               - Efficient filter application using existing _apply_filter method
               - Minimal UI updates focused on necessary changes
               - Quick response for small to medium datasets
               - Optimized for interactive filtering workflows

               Integration Features:
               - Coordinates with group management system seamlessly
               - Works with data view updates and table population
               - Supports complex filtering workflows with multiple criteria
               - Enables filter composition and refinement operations

               Note:
        •            Filter operations create temporary groups that persist until
                   manually deleted, allowing users to build collections of
                   filtered data for analysis and comparison purposes.
        """
        try:
            filter_text = self.filter_var.get().strip()
            column_name = self.column_var.get().strip()
            column_index = None

            if column_name and column_name != "All Columns":
                try:
                    column_index = self.headers.index(column_name)
                except ValueError:
                    pass  # Fall back to searching all columns

            if filter_text:
                # Apply filter to current view (either full data or group data)
                current_view = []
                selection = self.group_list.selection()
                if selection:
                    # If a group is selected, filter within that group
                    item_id = selection[0]
                    group_name = self.group_list.item(item_id)["text"]
                    if group_name in self.groups:
                        current_view = self.groups[group_name]
                else:
                    # Otherwise filter all data
                    current_view = self.current_data

                # Filter the data
                filtered_data = self._apply_filter(
                    current_view, filter_text, column_index
                )
                self._update_data_view(filtered_data)

                # Add filtered result as a custom group
                if column_name and column_name != "All Columns":
                    group_name = f"Filter {column_name}: {filter_text}"
                else:
                    group_name = f"Filter: {filter_text}"

                self.groups[group_name] = filtered_data
                self._update_groups_view()

                # Select the new filter group
                for item in self.group_list.get_children():
                    if self.group_list.item(item)["text"] == group_name:
                        self.group_list.selection_set(item)
                        self.group_list.see(item)
                        break

                self.update_status(f"Added filter group: {group_name}")
            else:
                # Show either group data or all data depending on selection
                selection = self.group_list.selection()
                if selection:
                    item_id = selection[0]
                    group_name = self.group_list.item(item_id)["text"]
                    if group_name in self.groups:
                        self._update_data_view(self.groups[group_name])
                else:
                    self._update_data_view(self.current_data)
                self.update_status("Cleared filter")
        except Exception as e:
            logging.error(f"Error applying filter: {e}")
            messagebox.showerror("Error", f"Failed to apply filter: {e}")

    def clear_filter(self) -> None:
        """Clear all filters and restore the full data view.

        Provides comprehensive filter clearing functionality:

        Filter State Reset:
        - Clears the filter text input field completely
        - Resets column selection to "All Columns" default
        - Removes any active filter groups or selections
        - Restores original data display state

        View Restoration:
        - Returns to full dataset display when no groups selected
        - Maintains group view if a non-filter group is selected
        - Clears group selection if current selection is a filter group
        - Preserves user workflow context appropriately

        User Interface Updates:
        - Updates status bar to confirm filter clearing
        - Refreshes data table with unfiltered content
        - Maintains table sorting and column visibility preferences
        - Provides immediate visual feedback

        Integration:
        - Works seamlessly with existing filter and group systems
        - Bound to Escape key for quick access
        - Available via Edit menu for discoverability
        - Maintains consistency with filter application workflow
        """
        try:
            # Clear filter inputs
            self.filter_var.set("")
            self.column_var.set("All Columns")

            # Clear group selection if it's a filter group
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
        """Refresh all data views and reload current data.

        Provides comprehensive view refresh functionality:

        Data Refresh:
        - Reloads current data from source file if available
        - Updates main data table with latest information
        - Refreshes group list with current group memberships
        - Maintains current filter and selection states

        View Updates:
        - Refreshes data table display with current sorting
        - Updates group list with latest group information
        - Maintains column visibility preferences
        - Preserves user interface customizations

        Status Updates:
        - Provides user feedback during refresh operation
        - Shows completion status in status bar
        - Handles refresh errors gracefully
        - Maintains application responsiveness

        Integration:
        - Bound to F5 key for quick access
        - Available via View menu for discoverability
        - Works with existing data loading systems
        - Maintains consistency with other refresh operations
        """
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
        """Refresh the main data table with specified or current dataset.

        Provides comprehensive table update functionality with advanced features:

        Data Source Management:
        - Uses provided data parameter when specified for targeted updates
        - Falls back to self.current_data for standard refresh operations
        - Handles None or empty data gracefully with early return
        - Maintains data integrity throughout update process

        Table Reset Process:
        - Completely clears existing table contents for clean update
        - Removes all child items to prevent display artifacts
        - Ensures fresh table state for new data population
        - Maintains consistent table appearance across updates

        Column Configuration:
        - Dynamically creates column identifiers based on header count
        - Uses "col{i}" naming convention for reliable column reference
        - Configures table to show headings only (no tree structure)
        - Sets up appropriate column structure for tabular data

        Header Management:
        - Maps column identifiers to human-readable header text
        - Sets initial column widths to 100px for consistent appearance
        - Configures all column headers from self.headers array
        - Maintains professional table presentation standards

        Data Population:
        - Iterates through data rows for sequential table insertion
        - Uses unique row identifiers for reliable row reference
        - Inserts complete row data as values for each table entry
        - Maintains data order and structure during population

        Column Menu Integration:
        - Updates column visibility controls with current headers
        - Ensures column menu reflects current table structure
        - Synchronizes UI controls with table configuration
        - Maintains consistency between table and menu systems

        Column Visibility Application:
        - Applies current column visibility settings after population
        - Ensures hidden columns remain hidden during updates
        - Maintains user customizations across data refreshes
        - Provides consistent column display preferences

        Error Handling:
        - Comprehensive exception catching for robust operation
        - Detailed error logging for debugging table update issues
        - Re-raises critical errors to prevent incomplete table state
        - Maintains application stability during update failures

        Performance Considerations:
        - Coordinates with group management system seamlessly
        - Works with data view updates and table population
        - Supports complex filtering workflows with multiple criteria
        - Enables filter composition and refinement operations

        Visual Consistency:
        - Maintains professional table appearance standards
        - Ensures consistent column widths and spacing
        - Preserves table formatting across different data sets
        - Provides predictable user experience for data viewing

        Args:
            data: Optional data list to display, defaults to current_data
                 Each row should be a list/tuple of values matching headers

        Note:
            This method performs a complete table rebuild rather than
            incremental updates, ensuring consistency and preventing
            display artifacts from partial updates or data changes.
        """
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
        """Update the column visibility menu with current table headers.

        Provides dynamic column control functionality:

        Menu Refresh:
        - Clears existing column visibility menu items
        - Rebuilds menu with current table headers
        - Creates checkable menu items for each column
        - Maintains menu consistency with table structure

        Column Controls:
        - Individual checkboxes for each column visibility
        - Default visibility state (all columns shown initially)
        - Interactive toggling for user customization
        - Immediate visual feedback for column changes

        State Management:
        - Tracks column visibility preferences
        - Integrates with configuration system
        - Preserves user choices across sessions
        - Handles dynamic header changes gracefully

        Integration:
        - Works with data view updates seamlessly
        - Coordinates with table population events
        - Supports runtime header modifications
        - Maintains consistency with other UI elements
        """
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
        """Apply current column visibility settings to the data table."""
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
        """Toggle the visibility of a specific column.

        Args:
            header: The column header name to toggle
            var: The BooleanVar associated with the menu checkbox
        """
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
        """Handle treeview resize events by adjusting column widths"""
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

                for i, original_width in original_widths.items():
                    new_width = max(int(original_width * scale_factor), min_col_width)
                    col_id = f"col{i}"
                    if col_id in self.data_table["columns"]:
                        self.data_table.column(col_id, width=new_width)

        except Exception as e:
            logging.error(f"Error handling treeview configure: {e}")
            # Don't raise - we don't want to crash on resize events

    def _update_details_view(self, item_data) -> None:
        """Update the details view with selected item information."""
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
                    # This is a text file - display the content in a readable format
                    file_name = values[0] if len(values) > 0 else "Unknown File"
                    content = values[1] if len(values) > 1 else "No content"

                    details_text = f"Text File: {file_name}\n"
                    details_text += "=" * 50 + "\n\n"
                    details_text += content

                    self.details_text.insert("1.0", details_text)
                else:
                    # Regular data format - display field by field
                    details_text = "Selected Item Details:\n"
                    details_text += "=" * 30 + "\n\n"

                    for i, value in enumerate(values):
                        if i < len(self.headers):
                            details_text += f"{self.headers[i]}: {value}\n"

                    # Add any additional metadata
                    if "text" in item_data:
                        details_text += f"\nItem ID: {item_data['text']}\n"

                    self.details_text.insert("1.0", details_text)
            else:
                self.details_text.insert("1.0", "No item selected or no data available")

        except Exception as e:
            logging.error(f"Error updating details view: {e}")
            if hasattr(self, "details_text"):
                self.details_text.delete("1.0", "end")
                self.details_text.insert("1.0", f"Error displaying details: {e}")

    def _show_speech_settings(self) -> None:
        """Show TTS configuration dialog."""
        try:
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
        """Load crew data from CSV, Excel, or text files."""
        try:
            file_path = filedialog.askopenfilename(
                title="Select Data File",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx;*.xls"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*"),
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
        """Import additional data and merge with current data."""
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
        """Save current data to file."""
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
        """Save current data to a new file."""
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
        """Export current data to Excel format."""
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
        """Load text content from file."""
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
        """Show dialog with imported modules information."""
        try:
            if hasattr(self, "imported_modules") and hasattr(self, "failed_imports"):
                info = f"Successfully imported: {len(self.imported_modules)} modules\n"
                info += f"Failed imports: {len(self.failed_imports)} modules\n\n"

                if self.imported_modules:
                    info += "Imported modules:\n"
                    for module in self.imported_modules:
                        info += f"  - {module}\n"

                if self.failed_imports:
                    info += "\nFailed imports:\n"
                    # failed_imports is a list of tuples (module_name, error_message)
                    for module, error in self.failed_imports:
                        info += f"  - {module}: {error}\n"

                messagebox.showinfo("Module Import Status", info)
            else:
                messagebox.showinfo(
                    "Module Import Status", "No module import data available"
                )
        except Exception as e:
            logging.error(f"Error showing imported modules: {e}")
            messagebox.showerror("Error", f"Failed to show module information: {e}")

    def _update_script_menu(self) -> None:
        """Update the script menu with available Python files."""
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
        """Run a Python script in the background."""
        try:
            self.update_status(f"Running script: {script_name}")
            self.run_in_background(self._execute_script, script_name)
        except Exception as e:
            logging.error(f"Error running script: {e}")
            messagebox.showerror("Error", f"Failed to run script {script_name}: {e}")

    def _execute_script(self, script_name: str) -> None:
        """Execute Python script in background thread."""
        try:
            import subprocess

            result = subprocess.run(
                [sys.executable, script_name],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                self.root.after(
                    0,
                    lambda: self.update_status(
                        f"Script {script_name} completed successfully"
                    ),
                )
            else:
                error_msg = result.stderr or "Script execution failed"
                self.root.after(
                    0, lambda: messagebox.showerror("Script Error", error_msg)
                )
        except Exception as e:
            logging.error(f"Error executing script {script_name}: {e}")
            self.root.after(0, lambda: messagebox.showerror("Script Error", str(e)))

    # Background processing methods
    def _load_data_background(
        self, file_path: str
    ) -> Tuple[List[List[Any]], List[str]]:
        """Load data from file in background thread."""
        try:
            if not PANDAS_AVAILABLE:
                # Fallback for CSV without pandas
                if file_path.endswith(".csv"):
                    import csv

                    with open(file_path, "r", encoding="utf-8") as f:
                        reader = csv.reader(f)
                        rows = list(reader)
                        if rows:
                            headers = rows[0]
                            data = rows[1:]
                            return data, headers
                        return [], []
                else:
                    raise ImportError("pandas required for Excel files")

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
        """Load text content from file in background thread."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logging.error(f"Error loading text from {file_path}: {e}")
            raise

    def _export_to_excel(self, file_path: str, data: List[List[Any]]) -> None:
        """Export data to Excel file in background thread."""
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
        """Save data to file in background thread."""
        try:
            if data and hasattr(self, "headers"):
                if file_path.endswith(".csv"):
                    if PANDAS_AVAILABLE:
                        df = pd.DataFrame(data, columns=self.headers)
                        df.to_csv(file_path, index=False)
                    else:
                        # Fallback CSV writing
                        import csv

                        with open(file_path, "w", newline="", encoding="utf-8") as f:
                            writer = csv.writer(f)
                            writer.writerow(self.headers)
                            writer.writerows(data)
                else:
                    if not PANDAS_AVAILABLE:
                        raise ImportError("pandas required for Excel files")
                    df = pd.DataFrame(data, columns=self.headers)
                    df.to_excel(file_path, index=False)

                self.root.after(0, lambda: self.update_status(f"Saved to {file_path}"))
            else:
                raise ValueError("No data to save")
        except Exception as e:
            logging.error(f"Error saving to file: {e}")
            self.root.after(0, lambda: messagebox.showerror("Save Error", str(e)))
