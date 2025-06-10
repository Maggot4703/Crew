"""
StateManager for CrewGUI Application

Phase 2 of the CrewGUI refactoring plan - Extracts all state persistence logic from the main GUI class.
"""

import logging
import tkinter as tk
from typing import Dict, Any, Optional


class StateManager:
    """Manages state persistence and restoration for the CrewGUI application."""
    
    def __init__(self, gui_instance):
        """Initialize the StateManager."""
        self.gui = gui_instance
        self.root = gui_instance.root
        self.config = gui_instance.config
        self._saved_column_widths = {}
        self._column_visibility = {}
        
        logging.info("StateManager initialized")
    
    def load_window_state(self) -> None:
        """Load and restore window state from configuration."""
        try:
            # Restore window geometry
            window_size = self.config.get("window_size")
            if window_size:
                self.root.geometry(window_size)
                logging.debug(f"Restored window size: {window_size}")

            # Restore minimum window size
            min_window_size = self.config.get("min_window_size")
            if min_window_size:
                try:
                    width, height = map(int, min_window_size.split("x"))
                    self.root.minsize(width, height)
                    logging.debug(f"Restored minimum window size: {width}x{height}")
                except ValueError as e:
                    logging.warning(f"Invalid min_window_size format '{min_window_size}': {e}")

            # Store column widths for later application after table is populated
            saved_widths = self.config.get("column_widths", {})
            if saved_widths:
                self._saved_column_widths = saved_widths
                # Also set on GUI instance for compatibility
                if hasattr(self.gui, '_saved_column_widths'):
                    self.gui._saved_column_widths = saved_widths
                logging.debug(f"Loaded column widths: {len(saved_widths)} columns")

            # Restore column visibility preferences
            saved_visibility = self.config.get("column_visibility", {})
            if saved_visibility:
                self._column_visibility = saved_visibility
                # Update GUI instance column visibility if it exists
                if hasattr(self.gui, "column_visibility"):
                    self.gui.column_visibility.update(saved_visibility)
                logging.debug(f"Loaded column visibility: {len(saved_visibility)} columns")

            logging.info("Window state loaded successfully")

        except Exception as e:
            logging.error(f"Error loading window state: {e}")
    
    def save_window_state(self) -> None:
        """Save current window state to configuration."""
        try:
            # Save window geometry
            current_geometry = self.root.geometry()
            self.config.set("window_size", current_geometry)
            logging.debug(f"Saved window geometry: {current_geometry}")

            # Save column widths if data table exists
            if hasattr(self.gui, 'data_table') and self.gui.data_table:
                column_widths = self._get_current_column_widths()
                if column_widths:
                    self.config.set("column_widths", column_widths)
                    self._saved_column_widths = column_widths
                    logging.debug(f"Saved column widths: {len(column_widths)} columns")

            # Save column visibility preferences
            if hasattr(self.gui, "column_visibility") and self.gui.column_visibility:
                self.config.set("column_visibility", self.gui.column_visibility)
                self._column_visibility = self.gui.column_visibility.copy()
                logging.debug(f"Saved column visibility: {len(self.gui.column_visibility)} columns")

            logging.info("Window state saved successfully")

        except Exception as e:
            logging.error(f"Error saving window state: {e}")
    
    def _get_current_column_widths(self) -> Dict[str, int]:
        """Get current column widths from the data table."""
        column_widths = {}
        try:
            if hasattr(self.gui, 'data_table') and self.gui.data_table:
                columns = self.gui.data_table["columns"]
                if columns:
                    for col in columns:
                        try:
                            width = self.gui.data_table.column(col, "width")
                            if width:  # Only store non-zero widths
                                column_widths[col] = width
                        except tk.TclError as e:
                            logging.warning(f"Could not get width for column {col}: {e}")
                            
        except Exception as e:
            logging.error(f"Error getting current column widths: {e}")
            
        return column_widths
    
    def apply_saved_column_widths(self) -> None:
        """Apply saved column widths to the data table."""
        try:
            if not self._saved_column_widths:
                # Try to get from GUI instance for compatibility
                if hasattr(self.gui, '_saved_column_widths'):
                    self._saved_column_widths = self.gui._saved_column_widths or {}
                    
            if not self._saved_column_widths:
                logging.debug("No saved column widths to apply")
                return

            if not hasattr(self.gui, 'data_table') or not self.gui.data_table:
                logging.debug("No data table available for applying column widths")
                return

            # Ensure columns exist before trying to configure them
            table_columns = self.gui.data_table["columns"]
            if not table_columns:  # Table might not be fully populated yet
                logging.debug("Data table columns not yet populated")
                return

            applied_count = 0
            for col_id, width in self._saved_column_widths.items():
                # Check if col_id is a valid column identifier for the current table
                if col_id in table_columns:
                    try:
                        self.gui.data_table.column(col_id, width=width)
                        applied_count += 1
                        logging.debug(f"Applied width {width} to column {col_id}")
                    except tk.TclError as e:
                        logging.warning(f"Could not apply width to column {col_id}: {e}")
                else:
                    logging.debug(f"Column ID {col_id} not found in current table")

            if applied_count > 0:
                logging.info(f"Applied saved widths to {applied_count} columns")

        except Exception as e:
            logging.error(f"Error applying saved column widths: {e}")
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of current state for debugging."""
        try:
            return {
                'window_geometry': self.root.geometry(),
                'saved_column_widths_count': len(self._saved_column_widths),
                'column_visibility_count': len(self._column_visibility),
                'gui_has_saved_widths': hasattr(self.gui, '_saved_column_widths'),
                'gui_has_column_visibility': hasattr(self.gui, 'column_visibility'),
                'data_table_exists': hasattr(self.gui, 'data_table') and self.gui.data_table is not None
            }
        except Exception as e:
            logging.error(f"Error getting state summary: {e}")
            return {'error': str(e)}