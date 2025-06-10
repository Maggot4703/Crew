"""
UIManager/LayoutManager for CrewGUI

This module provides a safe, non-intrusive manager for widget creation and layout
management. It's designed to work alongside the existing GUI without requiring
import changes that could break the fragile interface.

Key Features:
- Safe widget creation methods extracted from CrewGUI
- Layout management with proper error handling  
- Thread-safe operations for GUI updates
- Maintains existing widget references and behavior
- Compatible with existing PanedWindow-based layout
"""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from typing import Dict, Any, Optional, Callable
import logging


class UIManager:
    """
    Manages widget creation and layout for the CrewGUI application.
    
    This manager provides a centralized way to create and configure widgets
    while maintaining compatibility with the existing GUI structure.
    """
    
    def __init__(self, parent_gui: Any) -> None:
        """
        Initialize UIManager with reference to parent GUI.
        
        Args:
            parent_gui: The CrewGUI instance that owns this manager
        """
        self.gui = parent_gui
        self.root = parent_gui.root
        self._widget_registry: Dict[str, tk.Widget] = {}
        
        # Store commonly used style configurations
        self._default_style = self._setup_default_styles()
        
    def _setup_default_styles(self) -> Dict[str, Any]:
        """Setup default style configurations for consistent appearance."""
        try:
            style = ttk.Style()
            
            # Configure Treeview styles
            style.configure("Treeview", rowheight=25)
            style.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"))
            
            return {
                'label_frame_padding': "5",
                'button_padding': 2,
                'treeview_height': 8,
                'text_font': ("Consolas", 10),
                'default_font': tkfont.nametofont("TkDefaultFont")
            }
        except Exception as e:
            logging.error(f"Error setting up default styles: {e}")
            return {}
    
    def register_widget(self, name: str, widget: tk.Widget) -> None:
        """Register a widget for later reference."""
        self._widget_registry[name] = widget
    
    def get_widget(self, name: str) -> Optional[tk.Widget]:
        """Get a registered widget by name."""
        return self._widget_registry.get(name)

    def create_main_layout(self) -> None:
        """
        Create the main application layout structure.
        
        This method replicates the layout creation from the original GUI
        but in a more organized, maintainable way.
        """
        try:
            # Configure root window
            self.root.geometry("1200x800")
            self.root.minsize(800, 600)

            # Main container
            self.gui.main_frame = ttk.Frame(self.root, padding="5")
            self.gui.main_frame.grid(row=0, column=0, sticky="nsew")

            # Configure root window weights
            self.root.grid_rowconfigure(0, weight=1)
            self.root.grid_columnconfigure(0, weight=1)

            # Configure main frame weights
            self.gui.main_frame.grid_rowconfigure(0, weight=1)
            self.gui.main_frame.grid_columnconfigure(0, weight=1)

            # Create PanedWindow for resizable divider
            self.gui.paned_window = ttk.PanedWindow(
                self.gui.main_frame, orient="horizontal"
            )
            self.gui.paned_window.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

            # Create left and right panels
            self._create_panel_structure()
            
            logging.info("Main layout created successfully")
            
        except Exception as e:
            logging.error(f"Failed to create main layout: {e}")
            raise
    
    def _create_panel_structure(self) -> None:
        """Create the left and right panel structure."""
        try:
            # Left panel with fixed narrow width
            self.gui.left_frame = ttk.Frame(self.gui.paned_window, width=140)
            self.gui.left_frame.grid_propagate(False)

            # Right panel
            self.gui.right_frame = ttk.Frame(self.gui.paned_window)

            # Add frames to paned window
            self.gui.paned_window.add(self.gui.left_frame, weight=0)
            self.gui.paned_window.add(self.gui.right_frame, weight=1)

            # Split left panel into Controls/Groups/Filters
            self.gui.paned_left = ttk.PanedWindow(self.gui.left_frame, orient="vertical")
            self.gui.paned_left.grid(row=0, column=0, sticky="nsew")
            
            # Configure left frame
            self.gui.left_frame.grid_rowconfigure(0, weight=1)
            self.gui.left_frame.grid_columnconfigure(0, weight=1)

            # Split right panel into Data/Details
            self.gui.paned_right = ttk.PanedWindow(self.gui.right_frame, orient="vertical")
            self.gui.paned_right.grid(row=0, column=0, sticky="nsew")
            
            # Configure right frame
            self.gui.right_frame.grid_rowconfigure(0, weight=1)
            self.gui.right_frame.grid_columnconfigure(0, weight=1)
            
        except Exception as e:
            logging.error(f"Failed to create panel structure: {e}")
            raise
    
    def create_menu_bar(self) -> None:
        """Create the application menu bar with all menus."""
        try:
            self.gui.menu_bar = tk.Menu(self.root)
            self.root.config(menu=self.gui.menu_bar)

            # Create individual menus
            self._create_file_menu()
            self._create_edit_menu()
            self._create_view_menu()
            self._create_tts_menu()
            
            logging.info("Menu bar created successfully")
            
        except Exception as e:
            logging.error(f"Failed to create menu bar: {e}")
            raise
    
    def _create_file_menu(self) -> None:
        """Create the File menu."""
        file_menu = tk.Menu(self.gui.menu_bar, tearoff=0)
        self.gui.menu_bar.add_cascade(label="File", menu=file_menu)
        
        file_menu.add_command(
            label="Open... (Ctrl+O)", 
            command=getattr(self.gui, '_on_open_file', lambda: None)
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Save... (Ctrl+S)", 
            command=getattr(self.gui, '_on_save_file', lambda: None)
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
    
    def _create_edit_menu(self) -> None:
        """Create the Edit menu."""
        edit_menu = tk.Menu(self.gui.menu_bar, tearoff=0)
        self.gui.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        
        edit_menu.add_command(
            label="Find (Ctrl+F)", 
            command=lambda: (
                self.gui.filter_entry_widget.focus_set() 
                if hasattr(self.gui, 'filter_entry_widget') else None
            )
        )
        edit_menu.add_command(
            label="Clear Filter (Esc)", 
            command=getattr(self.gui, 'clear_filter', lambda: None)
        )
    
    def _create_view_menu(self) -> None:
        """Create the View menu with submenus."""
        view_menu = tk.Menu(self.gui.menu_bar, tearoff=0)
        self.gui.menu_bar.add_cascade(label="View", menu=view_menu)
        
        view_menu.add_command(
            label="Refresh (F5)", 
            command=getattr(self.gui, '_refresh_views', lambda: None)
        )
        view_menu.add_separator()

        # Column visibility submenu
        self.gui.column_visibility_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Columns", menu=self.gui.column_visibility_menu)

        # Script selector submenu
        self.gui.script_menu = tk.Menu(
            view_menu, tearoff=0, 
            postcommand=getattr(self.gui, '_update_script_menu', lambda: None)
        )
        view_menu.add_cascade(label="Run Script", menu=self.gui.script_menu)
    
    def _create_tts_menu(self) -> None:
        """Create the TTS menu if TTS is available."""
        try:
            # Check if TTS is available (safely handle import issues)
            tts_available = getattr(self.gui, 'TTS_AVAILABLE', False) or hasattr(self.gui, '_read_selected_item')
            
            if tts_available:
                tts_menu = tk.Menu(self.gui.menu_bar, tearoff=0)
                self.gui.menu_bar.add_cascade(label="🔊 Speech", menu=tts_menu)
                
                tts_menu.add_command(
                    label="Read Selection (Ctrl+Shift+R)", 
                    command=getattr(self.gui, '_read_selected_item', lambda: None)
                )
                tts_menu.add_command(
                    label="Read All Details (Ctrl+Shift+A)", 
                    command=getattr(self.gui, '_read_all_details', lambda: None)
                )
                tts_menu.add_command(
                    label="Read Status (Ctrl+Shift+S)", 
                    command=getattr(self.gui, '_read_status', lambda: None)
                )
                tts_menu.add_command(
                    label="Read Item Type (Ctrl+Shift+T)", 
                    command=getattr(self.gui, '_read_item_type', lambda: None)
                )
                tts_menu.add_separator()
                tts_menu.add_command(
                    label="Stop Reading", 
                    command=getattr(self.gui, '_stop_reading', lambda: None)
                )
                tts_menu.add_separator()
                tts_menu.add_command(
                    label="Save Speech to File...", 
                    command=getattr(self.gui, '_save_speech_to_file', lambda: None)
                )
                tts_menu.add_command(
                    label="Speech Settings...", 
                    command=getattr(self.gui, '_show_speech_settings', lambda: None)
                )
        except Exception as e:
            logging.warning(f"TTS menu creation failed: {e}")
    
    def create_control_section(self) -> ttk.LabelFrame:
        """Create the control section with buttons."""
        try:
            control_frame = ttk.LabelFrame(
                self.gui.paned_left, 
                text="Controls", 
                padding=self._default_style.get('label_frame_padding', "5")
            )
            self.gui.paned_left.add(control_frame, weight=0)

            # Add control buttons
            open_btn = ttk.Button(
                control_frame, 
                text="Open...", 
                command=getattr(self.gui, '_on_open_file', lambda: None)
            )
            open_btn.pack(fill="x", pady=self._default_style.get('button_padding', 2))
            
            save_btn = ttk.Button(
                control_frame, 
                text="Save...", 
                command=getattr(self.gui, '_on_save_file', lambda: None)
            )
            save_btn.pack(fill="x", pady=self._default_style.get('button_padding', 2))
            
            # Register widgets
            self.register_widget('control_frame', control_frame)
            self.register_widget('open_button', open_btn)
            self.register_widget('save_button', save_btn)
            
            logging.info("Control section created successfully")
            return control_frame
            
        except Exception as e:
            logging.error(f"Failed to create control section: {e}")
            raise
    
    def create_group_section(self) -> ttk.LabelFrame:
        """Create the group section with treeview."""
        try:
            # Calculate optimal height
            default_font = self._default_style.get('default_font', tkfont.nametofont("TkDefaultFont"))
            line_height = default_font.metrics("linespace") if default_font else 20
            desired_height_pixels = (5 * 25) + 2 * int(getattr(default_font, 'metrics', lambda x: {'ascent': 10})('ascent'))

            group_frame = ttk.LabelFrame(
                self.gui.paned_left,
                text="Groups",
                padding=self._default_style.get('label_frame_padding', "5"),
                height=int(desired_height_pixels)
            )
            self.gui.paned_left.add(group_frame, weight=0)

            # Group list treeview
            self.gui.group_list = ttk.Treeview(
                group_frame, 
                selectmode="browse", 
                height=5
            )
            self.gui.group_list.pack(fill="both", expand=True)

            # Create right-click menu for groups
            self._create_group_context_menu()

            # Create scrollbar for group list
            scrollbar = ttk.Scrollbar(
                group_frame, 
                orient="vertical", 
                command=self.gui.group_list.yview
            )
            scrollbar.pack(side="right", fill="y")
            self.gui.group_list.configure(yscrollcommand=scrollbar.set)
            
            # Register widgets
            self.register_widget('group_frame', group_frame)
            self.register_widget('group_list', self.gui.group_list)
            self.register_widget('group_scrollbar', scrollbar)
            
            logging.info("Group section created successfully")
            return group_frame
            
        except Exception as e:
            logging.error(f"Failed to create group section: {e}")
            raise
    
    def _create_group_context_menu(self) -> None:
        """Create context menu for group list."""
        try:
            self.gui.group_menu = tk.Menu(self.gui.group_list, tearoff=0)
            self.gui.group_menu.add_command(
                label="Delete", 
                command=getattr(self.gui, '_delete_selected_group', lambda: None)
            )
            
            # Bind right-click to show menu
            self.gui.group_list.bind(
                "<Button-3>", 
                getattr(self.gui, '_show_group_menu', lambda e: None)
            )
            
        except Exception as e:
            logging.warning(f"Failed to create group context menu: {e}")
    
    def create_filter_section(self) -> ttk.LabelFrame:
        """Create the filter section with controls."""
        try:
            # Calculate height for filter section
            default_font = self._default_style.get('default_font', tkfont.nametofont("TkDefaultFont"))
            line_height = default_font.metrics("linespace") if default_font else 20
            desired_height_pixels = 7 * line_height

            filter_frame = ttk.LabelFrame(
                self.gui.paned_left,
                text="Filters",
                padding=self._default_style.get('label_frame_padding', "5"),
                height=int(desired_height_pixels)
            )
            self.gui.paned_left.add(filter_frame, weight=0)
            self.gui.filter_frame = filter_frame

            # Initialize filter variables if not present
            if not hasattr(self.gui, 'filter_var'):
                self.gui.filter_var = tk.StringVar(value="")
            if not hasattr(self.gui, 'column_var'):
                self.gui.column_var = tk.StringVar(value="All Columns")
            if not hasattr(self.gui, 'filter_case_sensitive_var'):
                self.gui.filter_case_sensitive_var = tk.BooleanVar(value=False)

            # Column selection dropdown
            self.gui.column_menu = ttk.Combobox(
                filter_frame, 
                textvariable=self.gui.column_var, 
                state="readonly"
            )
            self.gui.column_menu.pack(fill="x", pady=2)
            
            # Bind column selection event
            self.gui.column_menu.bind(
                "<<ComboboxSelected>>", 
                getattr(self.gui, '_on_filter_column_selected', lambda e: None)
            )

            # Filter entry
            self.gui.filter_entry_widget = ttk.Entry(
                filter_frame, 
                textvariable=self.gui.filter_var
            )
            self.gui.filter_entry_widget.pack(fill="x", pady=2)

            # Case sensitive checkbox
            case_sensitive_check = ttk.Checkbutton(
                filter_frame, 
                text="Case Sensitive", 
                variable=self.gui.filter_case_sensitive_var
            )
            case_sensitive_check.pack(anchor="w", pady=2)

            # Button frame for filter controls
            button_frame = ttk.Frame(filter_frame)
            button_frame.pack(fill="x", pady=(5, 2))

            apply_btn = ttk.Button(
                button_frame, 
                text="Apply Filter", 
                command=getattr(self.gui, '_on_apply_filter', lambda: None)
            )
            apply_btn.pack(side="left", expand=True, fill="x", padx=(0, 1))

            clear_btn = ttk.Button(
                button_frame, 
                text="Clear Filter", 
                command=getattr(self.gui, 'clear_filter', lambda: None)
            )
            clear_btn.pack(side="left", expand=True, fill="x", padx=(1, 0))
            
            # Register widgets
            self.register_widget('filter_frame', filter_frame)
            self.register_widget('column_menu', self.gui.column_menu)
            self.register_widget('filter_entry', self.gui.filter_entry_widget)
            self.register_widget('case_sensitive_check', case_sensitive_check)
            self.register_widget('apply_filter_btn', apply_btn)
            self.register_widget('clear_filter_btn', clear_btn)
            
            logging.info("Filter section created successfully")
            return filter_frame
            
        except Exception as e:
            logging.error(f"Failed to create filter section: {e}")
            raise
    
    def create_new_view_section(self) -> ttk.LabelFrame:
        """Create the new view section (Mods View)."""
        try:
            # Create a new frame for the view
            new_view_frame = ttk.LabelFrame(
                self.gui.paned_left, 
                text="Mods View", 
                padding=self._default_style.get('label_frame_padding', "5")
            )
            self.gui.paned_left.add(new_view_frame, weight=0) 

            # Add content
            ttk.Label(
                new_view_frame, 
                text="Content for the mods view"
            ).pack(padx=5, pady=5)
            
            ttk.Button(
                new_view_frame, 
                text="Saver", 
                command=lambda: print("Saver button in Mods View clicked")
            ).pack(fill="x", pady=2)
            
            # Register widget
            self.register_widget('new_view_frame', new_view_frame)
            
            logging.info("New view section created successfully")
            return new_view_frame

        except Exception as e:
            logging.error(f"Failed to create new view section: {e}")
            raise
    
    def create_data_section(self) -> ttk.LabelFrame:
        """Create the data section with treeview table."""
        try:
            data_frame = ttk.LabelFrame(
                self.gui.paned_right, 
                text="Data View", 
                padding=self._default_style.get('label_frame_padding', "5")
            )
            self.gui.paned_right.add(data_frame, weight=1)

            # Create container frame for table and scrollbars
            table_frame = ttk.Frame(data_frame)
            table_frame.grid(row=0, column=0, sticky="nsew")

            # Configure frame weights
            data_frame.grid_rowconfigure(0, weight=1)
            data_frame.grid_columnconfigure(0, weight=1)
            table_frame.grid_rowconfigure(0, weight=1)
            table_frame.grid_columnconfigure(0, weight=1)

            # Create data table
            self.gui.data_table = ttk.Treeview(
                table_frame, 
                show="headings", 
                selectmode="browse", 
                height=self._default_style.get('treeview_height', 8)
            )

            # Create scrollbars
            y_scroll = ttk.Scrollbar(
                table_frame, 
                orient="vertical", 
                command=self.gui.data_table.yview
            )
            x_scroll = ttk.Scrollbar(
                table_frame, 
                orient="horizontal", 
                command=self.gui.data_table.xview
            )

            # Configure treeview to use scrollbars
            self.gui.data_table.configure(
                yscrollcommand=y_scroll.set,
                xscrollcommand=x_scroll.set,
                style="Treeview",
            )

            # Grid layout with scrollbars
            self.gui.data_table.grid(row=0, column=0, sticky="nsew")
            y_scroll.grid(row=0, column=1, sticky="ns")
            x_scroll.grid(row=1, column=0, sticky="ew")

            # Bind events
            self.gui.data_table.bind(
                "<Button-1>", 
                getattr(self.gui, '_on_column_click', lambda e: None)
            )
            
            # Register widgets
            self.register_widget('data_frame', data_frame)
            self.register_widget('table_frame', table_frame)
            self.register_widget('data_table', self.gui.data_table)
            self.register_widget('data_y_scroll', y_scroll)
            self.register_widget('data_x_scroll', x_scroll)
            
            logging.info("Data section created successfully")
            return data_frame
            
        except Exception as e:
            logging.error(f"Failed to create data section: {e}")
            raise
    
    def create_details_section(self) -> ttk.LabelFrame:
        """Create the details section with text widget."""
        try:
            details_frame = ttk.LabelFrame(
                self.gui.paned_right, 
                text="Details View", 
                padding=self._default_style.get('label_frame_padding', "5")
            )
            self.gui.paned_right.add(details_frame, weight=5)

            # Create container frame for text and scrollbar
            text_frame = ttk.Frame(details_frame)
            text_frame.grid(row=0, column=0, sticky="nsew")

            # Configure frame weights for expansion
            details_frame.grid_rowconfigure(0, weight=1)
            details_frame.grid_columnconfigure(0, weight=1)
            text_frame.grid_rowconfigure(0, weight=1)
            text_frame.grid_columnconfigure(0, weight=1)

            # Create text widget for details display
            self.gui.details_text = tk.Text(
                text_frame,
                wrap=tk.WORD,
                font=self._default_style.get('text_font', ("Consolas", 10)),
                state=tk.NORMAL,
                height=8,
                background="white",
                foreground="black",
            )

            # Create vertical scrollbar for text widget
            details_scroll = ttk.Scrollbar(
                text_frame, 
                orient="vertical", 
                command=self.gui.details_text.yview
            )

            # Configure text widget to use scrollbar
            self.gui.details_text.configure(yscrollcommand=details_scroll.set)

            # Grid layout with scrollbar
            self.gui.details_text.grid(row=0, column=0, sticky="nsew")
            details_scroll.grid(row=0, column=1, sticky="ns")

            # Set initial content
            self.gui.details_text.insert(
                "1.0", 
                "Select an item from the table above to view details here."
            )

            # Bind selection event for table to update details
            if hasattr(self.gui, "data_table"):
                self.gui.data_table.bind(
                    "<<TreeviewSelect>>", 
                    getattr(self.gui, '_on_data_table_select', lambda e: None)
                )
            
            # Register widgets
            self.register_widget('details_frame', details_frame)
            self.register_widget('details_text_frame', text_frame)
            self.register_widget('details_text', self.gui.details_text)
            self.register_widget('details_scroll', details_scroll)
            
            logging.info("Details section created successfully")
            return details_frame
            
        except Exception as e:
            logging.error(f"Failed to create details section: {e}")
            raise
    
    def create_status_bar(self) -> ttk.Frame:
        """Create the status bar at the bottom of the window."""
        try:
            # Create frame with border effect
            status_frame = ttk.Frame(self.root, relief=tk.GROOVE, borderwidth=1)
            status_frame.grid(row=1, column=0, sticky="ew", padx=2, pady=(2, 2))

            # Initialize status variable if not present
            if not hasattr(self.gui, 'status_var'):
                self.gui.status_var = tk.StringVar(value="Ready")

            # Status message
            self.gui.status_bar = ttk.Label(
                status_frame,
                textvariable=self.gui.status_var,
                padding=(5, 2),
                anchor=tk.W,
            )
            self.gui.status_bar.pack(fill=tk.X, expand=True)

            # Configure status bar layout
            self.root.grid_rowconfigure(1, weight=0)
            self.root.grid_columnconfigure(0, weight=1)

            # Add tooltip functionality
            self.gui.status_tooltip = None
            self.gui.status_bar.bind(
                "<Enter>", 
                getattr(self.gui, '_show_status_tooltip', lambda e: None)
            )
            self.gui.status_bar.bind(
                "<Leave>", 
                getattr(self.gui, '_hide_status_tooltip', lambda e: None)
            )
            
            # Register widgets
            self.register_widget('status_frame', status_frame)
            self.register_widget('status_bar', self.gui.status_bar)
            
            logging.info("Status bar created successfully")
            return status_frame
            
        except Exception as e:
            logging.error(f"Failed to create status bar: {e}")
            raise
    
    def create_all_widgets(self) -> None:
        """
        Create all GUI widgets in the correct order.
        
        This method creates all sections and maintains the proper
        creation order for dependencies.
        """
        try:
            self.create_control_section()
            self.create_group_section()
            self.create_filter_section()
            self.create_new_view_section()  # Handle directly in UIManager
            self.create_data_section()
            self.create_details_section()
            self.create_status_bar()
            
            logging.info("All widgets created successfully")
            
        except Exception as e:
            logging.error(f"Failed to create widgets: {e}")
            raise
    
    def update_status(self, message: str) -> None:
        """
        Thread-safe status update method.
        
        Args:
            message: Status message to display
        """
        try:
            if hasattr(self.gui, 'status_var'):
                # Schedule update on main thread
                self.root.after(0, lambda: self.gui.status_var.set(message))
            else:
                logging.warning("Status variable not available for update")
        except Exception as e:
            logging.error(f"Failed to update status: {e}")
    
    def get_widget_info(self) -> Dict[str, str]:
        """Get information about all registered widgets."""
        info = {}
        for name, widget in self._widget_registry.items():
            try:
                widget_type = type(widget).__name__
                widget_state = "exists"
                if hasattr(widget, 'winfo_exists'):
                    widget_state = "active" if widget.winfo_exists() else "destroyed"
                info[name] = f"{widget_type} - {widget_state}"
            except Exception as e:
                info[name] = f"Error: {e}"
        return info