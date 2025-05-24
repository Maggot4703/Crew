#!/usr/bin/python3
"""
Crew GUI Tool
This script provides a graphical interface for:
1. Loading and viewing CSV data files
2. Filtering and analyzing data
3. Managing crew groups and roles
4. Displaying detailed previews
5. Exporting data to various formats
6. User authentication and role management
"""

import tkinter as tk

#region Imports
from tkinter import ttk, messagebox, filedialog
from database_manager import DatabaseManager
from pathlib import Path
import logging
from typing import Dict, List, Any
import os
from config import Config
import asyncio
import threading
from queue import Queue
from typing import Optional, Callable, Any, Tuple
import time
#endregion

def auto_import_py_files() -> Tuple[List[str], List[Tuple[str, str]]]:
    """Automatically import all .py files in the workspace on startup"""
    import sys
    import importlib.util
    import glob
    import os
    
    try:
        # Get the current working directory
        workspace_root = Path.cwd()
        
        # Find all .py files in the workspace
        py_files = []
        
        # Main directory .py files (excluding current file and known problematic files)
        main_py_files = glob.glob(str(workspace_root / "*.py"))
        py_files.extend(main_py_files)
        
        # Subdirectory .py files  
        sub_py_files = glob.glob(str(workspace_root / "**/*.py"), recursive=True)
        py_files.extend(sub_py_files)
        
        # Remove duplicates and sort
        py_files = sorted(list(set(py_files)))
        
        imported_modules = []
        failed_imports = []
        
        # Files to skip (known problematic files or current file)
        skip_files = {
            'gui.py',
            'setup.py',
            '__init__.py'
        }
        
        # Directories to skip
        skip_dirs = {
            '__pycache__',
            '.git',
            'venv',
            'env',
            'tests',
            'test'
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
                
                # Skip test files
                if py_path.name.startswith('test_') or 'unittest' in py_path.name:
                    continue
                
                # Create module name from path
                module_name = str(relative_path.with_suffix(''))
                module_name = module_name.replace('/', '.').replace('\\', '.')
                
                # Handle files with spaces or special characters in names
                if ' ' in module_name or any(char in module_name for char in ',-'):
                    # Create a safe module name
                    safe_name = module_name.replace(' ', '_').replace(',', '_').replace('-', '_')
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
                    
            except (ImportError, SyntaxError, ModuleNotFoundError) as e:
                # These are expected for some files
                failed_imports.append((str(relative_path), f"Import error: {str(e)[:100]}"))
                continue
            except Exception as e:
                failed_imports.append((str(relative_path), f"Unexpected error: {str(e)[:100]}"))
                logging.warning(f"Failed to auto-import {py_file}: {e}")
                continue
        
        # Log the results
        if imported_modules:
            logging.info(f"Auto-imported {len(imported_modules)} modules")
        
        if failed_imports:
            logging.info(f"Skipped {len(failed_imports)} modules (expected for some files)")
                
        return imported_modules, failed_imports
        
    except Exception as e:
        logging.error(f"Auto-import process failed: {e}")
        return [], [(str(workspace_root), str(e))]

class CrewGUI:
    def __init__(self, root: tk.Tk) -> None:
        """Initialize the GUI application
        
        Args:
            root: The root tkinter window
        """
        try:
            self.root = root
            self.root.title("Crew Manager")
            
            # Create menu bar before other UI elements
            self.create_menu_bar()
            
            self.config = Config()
            self.setup_logging()
            self.setup_state()
            self.create_main_layout()
            self.create_all_widgets()
            self.bind_events()
            
            # Auto-import all .py files in workspace after GUI is set up
            self.update_status("Auto-importing workspace modules...")
            self.imported_modules, self.failed_imports = auto_import_py_files()
            
            # Initialize background worker
            self.task_queue: Queue = Queue()
            self.worker_thread = threading.Thread(target=self._background_worker, daemon=True)
            self.worker_thread.start()
            
            # Load window state after widgets are created
            self.load_window_state()
            
            # Load default data file if exists
            self.load_default_data()
            
            # Update status with import results
            total_imported = len(self.imported_modules) if hasattr(self, 'imported_modules') else 0
            total_failed = len(self.failed_imports) if hasattr(self, 'failed_imports') else 0
            self.update_status(f"Ready - Auto-imported {total_imported} modules ({total_failed} failed)")
            
        except Exception as e:
            logging.error(f"Failed to initialize GUI: {e}")
            messagebox.showerror("Error", f"Failed to initialize application: {e}")
            raise

    def create_menu_bar(self) -> None:
        """Create application menu bar"""
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Data (Ctrl+O)", command=self._on_load_data)
        file_menu.add_command(label="Save (Ctrl+S)", command=self._on_save)
        file_menu.add_command(label="Export (Ctrl+E)", command=self._on_export)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Edit menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Find (Ctrl+F)", command=lambda: self.filter_var.focus_set())
        edit_menu.add_command(label="Clear Filter (Esc)", command=self.clear_filter)

        # View menu
        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh (F5)", command=self._refresh_views)
        view_menu.add_command(label="Show Imported Modules", command=self._show_imported_modules)
        view_menu.add_separator()
        
        # Add column visibility submenu
        self.column_visibility_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Columns", menu=self.column_visibility_menu)

    def load_window_state(self) -> None:
        """Load saved window state"""
        try:
            # Restore window geometry
            if self.config.get("window_size"):
                self.root.geometry(self.config.get("window_size"))
            
            if self.config.get("min_window_size"):
                self.root.minsize(*map(int, self.config.get("min_window_size").split("x")))
            
            # Store column widths for later application after table is populated
            self._saved_column_widths = self.config.get("column_widths", {})
            
        except Exception as e:
            logging.error(f"Error loading window state: {e}")

    def save_window_state(self) -> None:
        """Save window state before closing"""
        try:
            self.config.set("window_size", self.root.geometry())
            
            # Save column widths
            column_widths = {}
            for col in self.data_table["columns"]:
                column_widths[col] = self.data_table.column(col, "width")
            self.config.set("column_widths", column_widths)
            
        except Exception as e:
            logging.error(f"Error saving window state: {e}")

    def _background_worker(self) -> None:
        """Background worker to handle long-running tasks"""
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

    def run_in_background(self, func: Callable, *args, callback: Optional[Callable] = None) -> None:
        """Run a function in the background thread"""
        self.task_queue.put((func, args, callback))

    def setup_logging(self) -> None:
        """Configure logging for the application"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def setup_state(self) -> None:
        """Initialize application state and database"""
        self.db = DatabaseManager()
        self.groups = {}  # Store groups data
        self.current_groups = {}
        self.group_preview = {}
        self.current_columns = []
        self.current_data = []
        self.headers = []  # Initialize empty headers

    def create_main_layout(self) -> None:
        """Create main application layout frames"""
        # Configure root window
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Main container
        self.main_frame = ttk.Frame(self.root, padding="5")
        self.main_frame.grid(row=0, column=0, sticky='nsew')
        
        # Configure root window weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Configure main frame weights
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Create PanedWindow for resizable divider between left and right sections
        self.paned_window = ttk.PanedWindow(self.main_frame, orient='horizontal')
        self.paned_window.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        
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
        self.left_frame.grid_rowconfigure(0, weight=0)  # Controls section - fixed height
        self.left_frame.grid_rowconfigure(1, weight=1)  # Groups section - expandable
        self.left_frame.grid_rowconfigure(2, weight=0)  # Filter section - fixed height

        # Configure right frame row weights
        self.right_frame.grid_rowconfigure(0, weight=3)  # Data view gets more space
        self.right_frame.grid_rowconfigure(1, weight=1)  # Details view gets less space
        self.right_frame.grid_columnconfigure(0, weight=1)

    def create_all_widgets(self) -> None:
        """Create all GUI widgets"""
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
        """Create status bar at bottom of window"""
        try:
            # Create frame with border effect
            status_frame = ttk.Frame(self.root, relief=tk.GROOVE, borderwidth=1)
            status_frame.grid(row=1, column=0, sticky='ew', padx=2, pady=(2,2))
            
            # Status message
            self.status_var = tk.StringVar(value="Ready")
            self.status_bar = ttk.Label(
                status_frame,
                textvariable=self.status_var,
                padding=(5, 2),
                anchor=tk.W  # Left align text
            )
            self.status_bar.pack(fill=tk.X, expand=True)
            
            # Configure status bar layout
            self.root.grid_rowconfigure(1, weight=0)
            self.root.grid_columnconfigure(0, weight=1)
            
            # Add tooltip
            self.status_tooltip = None
            self.status_bar.bind('<Enter>', self._show_status_tooltip)
            self.status_bar.bind('<Leave>', self._hide_status_tooltip)
            
        except Exception as e:
            logging.error(f"Failed to create status bar: {e}")
            raise

    def update_status(self, message: str) -> None:
        """Update status bar message
        
        Args:
            message: The message to display in the status bar
        """
        try:
            if not message:
                message = "Ready"
            self.status_var.set(message)
            self.root.update_idletasks()
        except Exception as e:
            logging.error(f"Failed to update status: {e}")

    def _show_status_tooltip(self, event: tk.Event) -> None:
        """Show tooltip with full status message on hover"""
        msg = self.status_var.get()
        if len(msg) > 50:  # Only show for long messages
            import tkinter.tix as tix
            self.status_tooltip = tix.Balloon(self.root)
            self.status_tooltip.bind_widget(self.status_bar, balloonmsg=msg)

    def _hide_status_tooltip(self, event: tk.Event) -> None:
        """Hide status tooltip"""
        if self.status_tooltip:
            self.status_tooltip.unbind_widget(self.status_bar)
            self.status_tooltip = None

    def create_control_section(self) -> None:
        """Create the control panel section"""
        try:
            control_frame = ttk.LabelFrame(self.left_frame, text="Controls", padding="5")
            control_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
            
            # Add control buttons
            ttk.Button(control_frame, text="Load Data", command=self._on_load_data).pack(fill='x', pady=2)
            ttk.Button(control_frame, text="Save", command=self._on_save).pack(fill='x', pady=2)
            ttk.Button(control_frame, text="Export", command=self._on_export).pack(fill='x', pady=2)
        except Exception as e:
            logging.error(f"Failed to create control section: {e}")
            raise

    def create_group_section(self) -> None:
        """Create the group management section"""
        try:
            group_frame = ttk.LabelFrame(self.left_frame, text="Groups", padding="5")
            group_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
            
            # Group list
            self.group_list = ttk.Treeview(group_frame, selectmode='browse', height=10)
            self.group_list.pack(fill='both', expand=True)
            
            # Create right-click menu
            self.group_menu = tk.Menu(self.group_list, tearoff=0)
            self.group_menu.add_command(label="Delete", command=self._delete_selected_group)
            
            # Bind right-click to show menu
            self.group_list.bind('<Button-3>', self._show_group_menu)
            
            # Scrollbar for group list
            scrollbar = ttk.Scrollbar(group_frame, orient='vertical', command=self.group_list.yview)
            scrollbar.pack(side='right', fill='y')
            self.group_list.configure(yscrollcommand=scrollbar.set)
        except Exception as e:
            logging.error(f"Failed to create group section: {e}")
            raise

    def _show_group_menu(self, event: tk.Event) -> None:
        """Show context menu for group list on right click"""
        try:
            # Select item under cursor
            item = self.group_list.identify_row(event.y)
            if item:
                self.group_list.selection_set(item)
                self.group_menu.post(event.x_root, event.y_root)
        except Exception as e:
            logging.error(f"Error showing group menu: {e}")

    def _delete_selected_group(self) -> None:
        """Delete the selected group"""
        try:
            selection = self.group_list.selection()
            if selection:
                item_id = selection[0]
                group_name = self.group_list.item(item_id)["text"]
                
                # Remove from groups dictionary and update views
                if group_name in self.groups:
                    del self.groups[group_name]
                    self._update_groups_view()
                    self._update_data_view(self.current_data)  # Show all data
                    self.update_status(f"Deleted group: {group_name}")
        except Exception as e:
            logging.error(f"Error deleting group: {e}")
            messagebox.showerror("Error", f"Failed to delete group: {e}")

    def create_filter_section(self) -> None:
        """Create the filter controls section"""
        try:
            filter_frame = ttk.LabelFrame(self.left_frame, text="Filters", padding="5")
            filter_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
            self.filter_frame = filter_frame
            
            # Filter controls
            self.filter_var = tk.StringVar(value="")
            self.column_var = tk.StringVar(value="All Columns")
            
            # Column selection dropdown
            self.column_menu = ttk.Combobox(
                filter_frame, 
                textvariable=self.column_var,
                state="readonly"
            )
            self.column_menu.pack(fill='x', pady=2)
            
            # Filter entry
            ttk.Entry(filter_frame, textvariable=self.filter_var).pack(fill='x', pady=2)
            ttk.Button(filter_frame, text="Apply Filter", command=self._on_apply_filter).pack(fill='x', pady=2)
        except Exception as e:
            logging.error(f"Failed to create filter section: {e}")
            raise

    def create_data_section(self) -> None:
        """Create the main data display section"""
        try:
            data_frame = ttk.LabelFrame(self.right_frame, text="Data View", padding="5")
            data_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
            
            # Create container frame for table and scrollbars
            table_frame = ttk.Frame(data_frame)
            table_frame.grid(row=0, column=0, sticky='nsew')
            
            # Configure frame weights
            data_frame.grid_rowconfigure(0, weight=1)
            data_frame.grid_columnconfigure(0, weight=1)
            
            table_frame.grid_rowconfigure(0, weight=1)
            table_frame.grid_columnconfigure(0, weight=1)
            
            # Create scrolled frame to contain treeview
            self.data_table = ttk.Treeview(table_frame, show="headings", selectmode="browse")
            
            # Create scrollbars
            y_scroll = ttk.Scrollbar(table_frame, orient='vertical', command=self.data_table.yview)
            x_scroll = ttk.Scrollbar(table_frame, orient='horizontal', command=self.data_table.xview)
            
            # Configure treeview to use scrollbars
            self.data_table.configure(
                yscrollcommand=y_scroll.set,
                xscrollcommand=x_scroll.set,
                style='Treeview'
            )
            
            # Bind sorting event
            self.data_table.bind('<Button-1>', self._on_column_click)
            90
            # Grid layout with scrollbars
            self.data_table.grid(row=0, column=0, sticky='nsew')
            y_scroll.grid(row=0, column=1, sticky='ns')
            x_scroll.grid(row=1, column=0, sticky='ew')
            
            # Configure style to ensure proper scrolling
            style = ttk.Style()
            style.configure('Treeview', rowheight=25)
            style.configure('Treeview.Heading', font=('TkDefaultFont', 10, 'bold'))
            
            # Add hook to apply saved column widths after table is populated
            def apply_saved_column_widths(event=None):
                if hasattr(self, '_saved_column_widths'):
                    for col, width in self._saved_column_widths.items():
                        # Only set width if column exists
                        if col in self.data_table["columns"]:
                            self.data_table.column(col, width=width)
                    delattr(self, '_saved_column_widths')  # Clean up after applying
            
            # Bind to table population event
            self.data_table.bind('<<TreeviewPopulated>>', apply_saved_column_widths)
            
        except Exception as e:
            logging.error(f"Failed to create data section: {e}")
            raise

    def _on_column_click(self, event: tk.Event) -> None:
        """Handle column header click for sorting"""
        try:
            region = self.data_table.identify_region(event.x, event.y)
            if region == "heading":
                column = self.data_table.identify_column(event.x)
                column_id = int(column[1]) - 1  # Convert #1 to 0, #2 to 1, etc.
                
                # Get all items
                items = [(self.data_table.set(item, column), item) for item in self.data_table.get_children("")]
                
                # Toggle sort direction
                if not hasattr(self, '_last_sort'):
                    self._last_sort = {'column': None, 'reverse': False}
                
                if self._last_sort['column'] == column:
                    self._last_sort['reverse'] = not self._last_sort['reverse']
                else:
                    self._last_sort['column'] = column
                    self._last_sort['reverse'] = False
                
                # Sort items
                items.sort(reverse=self._last_sort['reverse'])
                
                # Rearrange items in sorted order
                for index, (_, item) in enumerate(items):
                    self.data_table.move(item, "", index)
                
                # Update column header to show sort direction
                for col in self.data_table["columns"]:
                    if col == column:
                        direction = " ↓" if self._last_sort['reverse'] else " ↑"
                        text = self.headers[column_id] + direction
                    else:
                        text = self.headers[int(col[3:])]  # Remove "col" prefix to get index
                    self.data_table.heading(col, text=text)
                
        except Exception as e:
            logging.error(f"Error handling column click: {e}")

    def _apply_filter(self, data: List[Any], filter_text: str, column_index: int = None) -> List[Any]:
        """Apply filter to data
        
        Args:
            data: List of data rows to filter
            filter_text: Text to filter by
            column_index: Optional index of column to filter by
            
        Returns:
            Filtered list of data rows
        """
        filter_text = filter_text.lower()
        if column_index is not None:
            # Filter specific column
            return [
                row for row in data 
                if str(row[column_index]).lower().find(filter_text) >= 0
            ]
        else:
            # Filter all columns
            return [
                row for row in data 
                if any(str(cell).lower().find(filter_text) >= 0 for cell in row)
            ]

    def _update_groups_view(self) -> None:
        """Update the groups treeview with current groups"""
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
                        tags=(group_name,)
                    )
            
            # Sort groups by name
            items = [(self.group_list.item(item)["text"], item) for item in self.group_list.get_children("")]
            items.sort()
            for idx, (_, item) in enumerate(items):
                self.group_list.move(item, "", idx)
                
        except Exception as e:
            logging.error(f"Error updating groups view: {e}")
            raise

    def _on_group_select(self, event: tk.Event) -> None:
        """Handle group selection in treeview"""
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
        """Handle data row selection in treeview"""
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
        """Handle Apply Filter button click"""
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
                filtered_data = self._apply_filter(current_view, filter_text, column_index)
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

    def _update_data_view(self, data: List[Any] = None) -> None:
        """Update the data treeview
        
        Args:
            data: Data to display, defaults to current_data if None
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

    def _on_treeview_configure(self, event: tk.Event, original_widths: Dict[int, int]) -> None:
        """Handle treeview resize events by adjusting column widths
        
        Args:
            event: The configure event
            original_widths: Original calculated column widths
        """
        try:
            if not hasattr(self, 'last_width'):
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
                    self.data_table.column(f"col{i}", width=new_width, minwidth=min_col_width)
                    
        except Exception as e:
            logging.error(f"Error handling treeview configure: {e}")
            # Don't raise - we don't want to crash on resize events

    def _update_details_view(self, data: Any) -> None:
        """Update details view and save selected row as text file"""
        try:
            self.details_text.delete("1.0", tk.END)
            
            if isinstance(data, dict) and 'values' in data:
                values = data['values']
                if values and len(values) > 0:  # Ensure we have values
                    # Format details text
                    formatted_text = ""
                    for header, value in zip(self.headers, values):
                        formatted_text += f"{header}: {value}\n"
                    
                    # Show in details view
                    self.details_text.insert("1.0", formatted_text)
                    
                    # Get current CSV name (e.g., "npcs" from "npcs.csv")
                    folder_name = Path(self.current_file).stem.lower()
                    
                    # Create folder if needed (e.g., "data/npcs/")
                    save_dir = Path("data") / folder_name
                    save_dir.mkdir(parents=True, exist_ok=True)
                    
                    # First column value becomes filename (e.g., "Guard.txt")
                    filename = f"{values[0]}.txt"
                    filename = ''.join(c for c in filename if c.isalnum() or c in '- _.()[]')
                    
                    # Save formatted text to file (e.g., "data/npcs/Guard.txt")
                    filepath = save_dir / filename
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(formatted_text)
                    self.update_status(f"Saved to {filepath}")
                
            else:
                self.details_text.insert("1.0", str(data))
            
        except Exception as e:
            logging.error(f"Error updating details: {e}")
            self.update_status("Failed to save details")

    def create_details_section(self) -> None:
        """Create the details preview section"""
        try:
            details_frame = ttk.LabelFrame(self.right_frame, text="Details", padding="5")
            details_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
            
            # Create text widget with improved scrolling
            self.details_text = tk.Text(
                details_frame,
                wrap='word',  # Word wrapping for better readability
                padx=5,
                pady=5,
                width=50,
                height=10
            )
            
            # Create and configure scrollbar
            y_scroll = ttk.Scrollbar(details_frame, orient='vertical', command=self.details_text.yview)
            
            # Configure text widget to use scrollbar
            self.details_text.configure(yscrollcommand=y_scroll.set)
            
            # Grid layout with proper weights
            details_frame.grid_columnconfigure(0, weight=1)
            details_frame.grid_rowconfigure(0, weight=1)
            
            self.details_text.grid(row=0, column=0, sticky='nsew')
            y_scroll.grid(row=0, column=1, sticky='ns')
            
        except Exception as e:
            logging.error(f"Failed to create details section: {e}")
            raise

    def bind_events(self) -> None:
        """Bind event handlers to widgets"""
        try:
            # Data table events
            self.data_table.bind('<<TreeviewSelect>>', self._on_data_select)
            
            # Group list events
            self.group_list.bind('<<TreeviewSelect>>', self._on_group_select)
            
            # Add keyboard shortcuts
            self.root.bind('<Control-o>', lambda e: self._on_load_data())
            self.root.bind('<Control-s>', lambda e: self._on_save())
            self.root.bind('<Control-e>', lambda e: self._on_export())
            self.root.bind('<Control-f>', lambda e: self.filter_var.focus_set())
            self.root.bind('<Escape>', lambda e: self.clear_filter())
            self.root.bind('<F5>', lambda e: self._refresh_views())
            
            # Filter entry bindings
            filter_entry = self.filter_frame.winfo_children()[1]
            filter_entry.bind('<Return>', lambda e: self._on_apply_filter())
            filter_entry.bind('<KP_Enter>', lambda e: self._on_apply_filter())
            
            # Window close handler
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            self._update_column_menu()
            
        except Exception as e:
            logging.error(f"Error binding events: {e}")
            raise

    def clear_filter(self) -> None:
        """Clear current filter and reset view"""
        self.filter_var.set('')
        self._on_apply_filter()

    def _refresh_views(self) -> None:
        """Refresh all views with current data"""
        self._update_data_view()
        self._update_groups_view()
        self.update_status("Views refreshed")

    def _show_imported_modules(self) -> None:
        """Show dialog with imported modules information"""
        try:
            # Create dialog window
            dialog = tk.Toplevel(self.root)
            dialog.title("Auto-Imported Modules")
            dialog.geometry("800x600")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Create main frame
            main_frame = ttk.Frame(dialog, padding="10")
            main_frame.grid(row=0, column=0, sticky='nsew')
            
            # Configure dialog weights
            dialog.grid_rowconfigure(0, weight=1)
            dialog.grid_columnconfigure(0, weight=1)
            main_frame.grid_rowconfigure(1, weight=1)
            main_frame.grid_columnconfigure(0, weight=1)
            
            # Title label
            title_label = ttk.Label(main_frame, text="Auto-Imported Python Modules", 
                                  font=('TkDefaultFont', 12, 'bold'))
            title_label.grid(row=0, column=0, pady=(0, 10), sticky='w')
            
            # Create notebook for tabs
            notebook = ttk.Notebook(main_frame)
            notebook.grid(row=1, column=0, sticky='nsew')
            
            # Successful imports tab
            success_frame = ttk.Frame(notebook)
            notebook.add(success_frame, text=f"Successfully Imported ({len(getattr(self, 'imported_modules', []))})")
            
            success_frame.grid_rowconfigure(0, weight=1)
            success_frame.grid_columnconfigure(0, weight=1)
            
            success_text = tk.Text(success_frame, wrap='word', font=('Consolas', 10))
            success_scroll = ttk.Scrollbar(success_frame, orient='vertical', command=success_text.yview)
            success_text.configure(yscrollcommand=success_scroll.set)
            
            success_text.grid(row=0, column=0, sticky='nsew')
            success_scroll.grid(row=0, column=1, sticky='ns')
            
            # Failed imports tab
            failed_frame = ttk.Frame(notebook)
            notebook.add(failed_frame, text=f"Failed Imports ({len(getattr(self, 'failed_imports', []))})")
            
            failed_frame.grid_rowconfigure(0, weight=1)
            failed_frame.grid_columnconfigure(0, weight=1)
            
            failed_text = tk.Text(failed_frame, wrap='word', font=('Consolas', 10))
            failed_scroll = ttk.Scrollbar(failed_frame, orient='vertical', command=failed_text.yview)
            failed_text.configure(yscrollcommand=failed_scroll.set)
            
            failed_text.grid(row=0, column=0, sticky='nsew')
            failed_scroll.grid(row=0, column=1, sticky='ns')
            
            # Populate successful imports
            if hasattr(self, 'imported_modules'):
                success_text.insert('1.0', "Successfully imported modules:\n\n")
                for i, module in enumerate(self.imported_modules, 1):
                    success_text.insert('end', f"{i:3d}. {module}\n")
            else:
                success_text.insert('1.0', "No import information available.\nAuto-import may not have run yet.")
            
            # Populate failed imports
            if hasattr(self, 'failed_imports') and self.failed_imports:
                failed_text.insert('1.0', "Failed imports:\n\n")
                for i, (file_path, error) in enumerate(self.failed_imports, 1):
                    failed_text.insert('end', f"{i:3d}. {file_path}\n")
                    failed_text.insert('end', f"     Error: {error}\n\n")
            else:
                failed_text.insert('1.0', "No failed imports!")
            
            # Make text widgets read-only
            success_text.configure(state='disabled')
            failed_text.configure(state='disabled')
            
            # Button frame
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=2, column=0, pady=(10, 0), sticky='ew')
            
            # Re-import button
            ttk.Button(button_frame, text="Re-import All", 
                      command=lambda: self._reimport_modules(dialog)).pack(side='left', padx=(0, 5))
            
            # Close button
            ttk.Button(button_frame, text="Close", 
                      command=dialog.destroy).pack(side='right')
            
        except Exception as e:
            logging.error(f"Error showing imported modules dialog: {e}")
            messagebox.showerror("Error", f"Failed to show imported modules: {e}")

    def _reimport_modules(self, dialog=None) -> None:
        """Re-run the auto-import process"""
        try:
            self.update_status("Re-importing workspace modules...")
            self.imported_modules, self.failed_imports = auto_import_py_files()
            
            # Update status with import results
            total_imported = len(self.imported_modules)
            total_failed = len(self.failed_imports)
            self.update_status(f"Re-import complete - {total_imported} modules ({total_failed} failed)")
            
            # Close dialog if provided and show new one
            if dialog:
                dialog.destroy()
                self._show_imported_modules()
                
        except Exception as e:
            logging.error(f"Error re-importing modules: {e}")
            self.update_status("Re-import failed")

    def load_default_data(self) -> None:
        """Load default data file if it exists"""
        try:
            default_file = Path("data/npcs.csv")
            if default_file.exists():
                self.headers, self.current_data, self.groups = self.db.load_data(str(default_file))
                self._update_data_view()
                self._update_groups_view()
                self.update_status(f"Loaded default data from {default_file.name}")
        except Exception as e:
            logging.error(f"Failed to load default data: {e}")
            # Don't show error dialog for default data load failure

    def _on_load_data(self, event=None) -> None:
        """Handle Load Data menu/button action
        
        Opens a file dialog for selecting CSV data files and initiates the loading process.
        Supports both menu command and keyboard shortcut (Ctrl+O) triggers.
        
        Args:
            event: Optional keyboard event when triggered by shortcut
            
        Error handling:
            - Logs errors and shows error dialog to user
            - Gracefully handles dialog cancellation
        """
        try:
            filetypes = [
                ('CSV files', '*.csv'),
                ('All files', '*.*')
            ]
            
            filename = filedialog.askopenfilename(
                title="Select Data File",
                filetypes=filetypes,
                initialdir="data"
            )
            
            if filename:
                self.load_data_file(filename)
                
        except Exception as e:
            logging.error(f"Error loading data: {e}")
            messagebox.showerror("Error", f"Failed to load data: {e}")

    def load_data_file(self, filename: str) -> None:
        """Load data and store current filename for saving details"""
        try:
            self.update_status(f"Loading {Path(filename).name}...")
            self.root.update_idletasks()
            
            # Store current file path for saving details
            self.current_file = filename  # Add this line
            
            def load_callback(result):
                headers, data, groups = result
                self.headers = headers 
                self.current_data = data
                self.groups = groups
                self._update_data_view()
                self._update_groups_view()
                self._update_column_menu()
                self.update_status(f"Loaded {Path(filename).name}")
            
            self.run_in_background(
                self.db.load_data,
                filename,
                callback=load_callback
            )
            
        except Exception as e:
            logging.error(f"Error loading file {filename}: {e}")
            messagebox.showerror("Error", f"Failed to load file: {e}")
            self.update_status("Failed to load data")

    def _on_save(self, event=None) -> None:
        """Handle Save menu/button action
        
        Saves current data and groups to CSV file.
        Supports both menu command and keyboard shortcut (Ctrl+S).
        
        Args:
            event: Optional keyboard event when triggered by shortcut
        """
        try:
            filetypes = [
                ('CSV files', '*.csv'),
                ('All files', '*.*')
            ]
            
            filename = filedialog.asksaveasfilename(
                title="Save Data",
                filetypes=filetypes,
                initialdir="data",
                defaultextension=".csv"
            )
            
            if filename:
                # Show saving status
                self.update_status(f"Saving to {os.path.basename(filename)}...")
                self.root.update_idletasks()
                
                def save_callback(result):
                    if result:
                        self.update_status(f"Saved to {os.path.basename(filename)}")
                    else:
                        self.update_status("Failed to save data")
                        messagebox.showerror("Error", "Failed to save data file")
                
                # Save in background
                self.run_in_background(
                    self.db.save_data,
                    filename,
                    self.headers,
                    self.current_data,
                    callback=save_callback
                )
                
        except Exception as e:
            logging.error(f"Error saving data: {e}")
            messagebox.showerror("Error", f"Failed to save data: {e}")
            self.update_status("Failed to save data")

    def _on_export(self, event=None) -> None:
        """Handle Export menu/button action
        
        Exports current view data to Excel file.
        Supports both menu command and keyboard shortcut (Ctrl+E).
        
        Args:
            event: Optional keyboard event when triggered by shortcut
        """
        try:
            filetypes = [
                ('Excel files', '*.xlsx'),
                ('All files', '*.*')
            ]
            
            filename = filedialog.asksaveasfilename(
                title="Export Data",
                filetypes=filetypes,
                initialdir="data",
                defaultextension=".xlsx"
            )
            
            if filename:
                # Show exporting status
                self.update_status(f"Exporting to {os.path.basename(filename)}...")
                self.root.update_idletasks()
                
                def export_callback(result):
                    if result:
                        self.update_status(f"Exported to {os.path.basename(filename)}")
                    else:
                        self.update_status("Failed to export data")
                        messagebox.showerror("Error", "Failed to export data file")
                
                # Get current view data from treeview
                view_data = []
                for item in self.data_table.get_children():
                    view_data.append(self.data_table.item(item)['values'])
                
                # Export in background
                self.run_in_background(
                    self.db.export_data,
                    filename,
                    self.headers,
                    view_data,
                    callback=export_callback
                )
                
        except Exception as e:
            logging.error(f"Error exporting data: {e}")
            messagebox.showerror("Error", f"Failed to export data: {e}")
            self.update_status("Failed to export data")

    def _update_column_menu(self) -> None:
        """Update column visibility menu with current headers"""
        try:
            if hasattr(self, 'column_visibility_menu') and hasattr(self, 'headers'):
                # Clear existing menu items
                self.column_visibility_menu.delete(0, 'end')
                
                # Initialize column visibility tracking if not exists
                if not hasattr(self, 'column_visibility'):
                    self.column_visibility = {}
                
                # Add "Show All" and "Hide All" options
                self.column_visibility_menu.add_command(label="Show All", command=self._show_all_columns)
                self.column_visibility_menu.add_command(label="Hide All", command=self._hide_all_columns)
                self.column_visibility_menu.add_separator()
                
                # Add toggle option for each column
                for i, header in enumerate(self.headers):
                    # Initialize visibility state if not set
                    if header not in self.column_visibility:
                        self.column_visibility[header] = True
                    
                    # Create checkable menu item
                    var = tk.BooleanVar(value=self.column_visibility[header])
                    self.column_visibility_menu.add_checkbutton(
                        label=header,
                        variable=var,
                        command=lambda h=header, v=var: self._toggle_column_visibility(h, v)
                    )
                    
                    # Store variable for later reference
                    setattr(self, f'column_var_{i}', var)
                    
            # Also update the filter dropdown with column names
            if hasattr(self, 'column_menu') and hasattr(self, 'headers'):
                headers = ['All Columns'] + self.headers
                self.column_menu['values'] = headers
                if self.column_var.get() not in headers:
                    self.column_var.set('All Columns')
                    
        except Exception as e:
            logging.error(f"Error updating column menu: {e}")

    def _show_all_columns(self) -> None:
        """Show all columns in the data view"""
        try:
            if hasattr(self, 'headers') and hasattr(self, 'column_visibility'):
                for i, header in enumerate(self.headers):
                    self.column_visibility[header] = True
                    if hasattr(self, f'column_var_{i}'):
                        getattr(self, f'column_var_{i}').set(True)
                
                self._apply_column_visibility()
                self.update_status("All columns shown")
                
        except Exception as e:
            logging.error(f"Error showing all columns: {e}")

    def _hide_all_columns(self) -> None:
        """Hide all columns except the first one (to maintain table structure)"""
        try:
            if hasattr(self, 'headers') and hasattr(self, 'column_visibility'):
                for i, header in enumerate(self.headers):
                    # Keep at least the first column visible
                    visibility = True if i == 0 else False
                    self.column_visibility[header] = visibility
                    if hasattr(self, f'column_var_{i}'):
                        getattr(self, f'column_var_{i}').set(visibility)
                
                self._apply_column_visibility()
                self.update_status("All columns hidden except first")
                
        except Exception as e:
            logging.error(f"Error hiding all columns: {e}")

    def _toggle_column_visibility(self, header: str, var: tk.BooleanVar) -> None:
        """Toggle visibility of a specific column"""
        try:
            if hasattr(self, 'column_visibility'):
                self.column_visibility[header] = var.get()
                self._apply_column_visibility()
                status = "shown" if var.get() else "hidden"
                self.update_status(f"Column '{header}' {status}")
                
        except Exception as e:
            logging.error(f"Error toggling column visibility for {header}: {e}")

    def _apply_column_visibility(self) -> None:
        """Apply current column visibility settings to the data table"""
        try:
            if not hasattr(self, 'column_visibility') or not hasattr(self, 'headers'):
                return
                
            # Get current columns
            columns = self.data_table["columns"]
            if not columns:
                return
            
            # Apply visibility settings
            for i, header in enumerate(self.headers):
                if i < len(columns):
                    column_id = columns[i]
                    is_visible = self.column_visibility.get(header, True)
                    
                    if is_visible:
                        # Show column - restore width
                        self.data_table.column(column_id, width=100, minwidth=50)
                    else:
                        # Hide column - set width to 0
                        self.data_table.column(column_id, width=0, minwidth=0)
                        
        except Exception as e:
            logging.error(f"Error applying column visibility: {e}")

    def _on_closing(self) -> None:
        """Handle window closing event"""
        try:
            self.save_window_state()
            self.root.destroy()
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")
            self.root.destroy()

def main() -> None:
    """Main entry point for the Crew Manager application"""
    try:
        root = tk.Tk()
        app = CrewGUI(root)
        root.mainloop()
    except Exception as e:
        logging.error(f"Application crashed: {e}")
        messagebox.showerror("Fatal Error", f"Application crashed: {e}")
        raise

if __name__ == "__main__":
    main()
