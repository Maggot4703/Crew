"""
EventManager for CrewGUI Application

Phase 2 of the CrewGUI refactoring plan - Extracts all event handling logic from the main GUI class.
"""

import logging
import tkinter as tk
from typing import Callable, Optional

# Check if TTS is available
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False


class EventManager:
    """Manages event handling for the CrewGUI application."""
    
    def __init__(self, gui_instance):
        """Initialize the EventManager."""
        self.gui = gui_instance
        self.root = gui_instance.root
        self._event_bindings = {}
        
        logging.info("EventManager initialized")
    
    def setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts for the application."""
        try:
            # Clear filter with Escape key
            self._bind_event("<Escape>", lambda event: self._safe_callback(self.gui.clear_filter))
            
            # Focus filter field with Ctrl+F
            self._bind_event("<Control-f>", self._focus_filter_handler)
            
            # Refresh with F5
            self._bind_event("<F5>", self._refresh_handler)
            
            # TTS keyboard shortcuts (if TTS is available)
            if TTS_AVAILABLE and hasattr(self.gui, 'tts_engine') and self.gui.tts_engine:
                self._setup_tts_shortcuts()
            
            logging.debug("Keyboard shortcuts setup completed")
            
        except Exception as e:
            logging.error(f"Error setting up keyboard shortcuts: {e}")
    
    def setup_widget_events(self) -> None:
        """Setup widget-specific event handlers."""
        try:
            # Data table selection events will be bound when table is created
            # This method is called early, so we store the handlers for later binding
            self._widget_handlers = {
                'data_table_select': self._on_data_table_select,
                'column_click': self._on_column_click,
                'treeview_populated': self._on_treeview_populated
            }
            
            logging.debug("Widget event handlers prepared")
            
        except Exception as e:
            logging.error(f"Error setting up widget events: {e}")
    
    def bind_data_table_events(self) -> None:
        """Bind events to the data table once it's created."""
        try:
            if hasattr(self.gui, 'data_table') and self.gui.data_table:
                # Bind selection event
                self.gui.data_table.bind("<<TreeviewSelect>>", self._on_data_table_select)
                
                # Bind column click events for sorting
                for col in self.gui.data_table["columns"]:
                    self.gui.data_table.heading(col, command=lambda c=col: self._on_column_click(c))
                
                # Bind the populated event
                self.gui.data_table.bind("<<TreeviewPopulated>>", self._on_treeview_populated)
                
                logging.debug("Data table events bound successfully")
            
        except Exception as e:
            logging.error(f"Error binding data table events: {e}")
    
    def _setup_tts_shortcuts(self) -> None:
        """Setup TTS-specific keyboard shortcuts."""
        try:
            self._bind_event("<Control-Shift-R>", lambda event: self._safe_callback(self.gui._read_selected_item))
            self._bind_event("<Control-Shift-A>", lambda event: self._safe_callback(self.gui._read_all_details))
            self._bind_event("<Control-Shift-S>", lambda event: self._safe_callback(self.gui._read_status))
            self._bind_event("<Control-Shift-T>", lambda event: self._safe_callback(self.gui._read_item_type))
            
            logging.debug("TTS shortcuts setup completed")
            
        except Exception as e:
            logging.error(f"Error setting up TTS shortcuts: {e}")
    
    def _bind_event(self, sequence: str, handler: Callable) -> None:
        """Safely bind an event with tracking."""
        try:
            self.root.bind(sequence, handler)
            self._event_bindings[sequence] = handler
            logging.debug(f"Bound event: {sequence}")
            
        except Exception as e:
            logging.error(f"Error binding event {sequence}: {e}")
    
    def _focus_filter_handler(self, event) -> None:
        """Handle Ctrl+F to focus filter field."""
        try:
            if hasattr(self.gui, 'filter_entry_widget') and self.gui.filter_entry_widget:
                self.gui.filter_entry_widget.focus_set()
            elif hasattr(self.gui, 'filter_var'):
                self.gui.filter_var.focus_set()
        except Exception as e:
            logging.error(f"Error focusing filter field: {e}")
    
    def _refresh_handler(self, event) -> None:
        """Handle F5 refresh."""
        try:
            if hasattr(self.gui, '_refresh_views'):
                self.gui._refresh_views()
        except Exception as e:
            logging.error(f"Error refreshing views: {e}")
    
    def _on_data_table_select(self, event) -> None:
        """Handle data table selection events."""
        try:
            # Delegate to GUI's original handler if it exists
            if hasattr(self.gui, '_on_data_table_select_original'):
                self.gui._on_data_table_select_original(event)
            elif hasattr(self.gui, '_on_data_table_select'):
                self.gui._on_data_table_select(event)
                
        except Exception as e:
            logging.error(f"Error handling data table selection: {e}")
    
    def _on_column_click(self, column) -> None:
        """Handle column header clicks for sorting."""
        try:
            # Delegate to GUI's original handler if it exists
            if hasattr(self.gui, '_on_column_click_original'):
                self.gui._on_column_click_original(column)
            elif hasattr(self.gui, '_on_column_click'):
                self.gui._on_column_click(column)
                
        except Exception as e:
            logging.error(f"Error handling column click: {e}")
    
    def _on_treeview_populated(self, event) -> None:
        """Handle treeview populated events."""
        try:
            # Apply saved column widths when table is populated
            if hasattr(self.gui, 'state_manager'):
                self.gui.state_manager.apply_saved_column_widths()
            elif hasattr(self.gui, '_apply_saved_column_widths'):
                self.gui._apply_saved_column_widths()
                
        except Exception as e:
            logging.error(f"Error handling treeview populated: {e}")
    
    def _safe_callback(self, callback: Callable, *args, **kwargs) -> None:
        """Execute a callback with error handling."""
        try:
            if callable(callback):
                callback(*args, **kwargs)
            else:
                logging.warning(f"Attempted to call non-callable: {callback}")
                
        except Exception as e:
            logging.error(f"Error in callback execution: {e}")
    
    def unbind_all_events(self) -> None:
        """Unbind all tracked events (cleanup)."""
        try:
            for sequence in self._event_bindings:
                try:
                    self.root.unbind(sequence)
                except tk.TclError:
                    # Event already unbound or widget destroyed
                    pass
            
            self._event_bindings.clear()
            logging.debug("All events unbound successfully")
            
        except Exception as e:
            logging.error(f"Error unbinding events: {e}")
    
    def get_event_summary(self) -> dict:
        """Get a summary of bound events for debugging."""
        return {
            'bound_events_count': len(self._event_bindings),
            'bound_events': list(self._event_bindings.keys()),
            'tts_available': TTS_AVAILABLE,
            'gui_has_data_table': hasattr(self.gui, 'data_table')
        }