from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
import logging
import os
import csv
import pandas as pd

@dataclass
class FilterConfig:
    text: str = ""
    column: str = "All Columns"
    case_sensitive: bool = False

@dataclass
class DataState:
    raw_data: List[List[Any]]
    filtered_data: List[List[Any]]
    headers: List[str]
    current_filter: FilterConfig
    sort_column: Optional[str] = None
    sort_ascending: bool = True
    
class DataManager:
    def __init__(self):
        self._state = DataState([], [], [], FilterConfig())
        self._observers: List[Callable] = []
        
    def register_observer(self, callback: Callable) -> None:
        """Register UI callback for data changes"""
        self._observers.append(callback)
        
    def _notify_observers(self) -> None:
        """Notify all observers of data changes"""
        for callback in self._observers:
            try:
                callback(self._state)
            except Exception as e:
                logging.error(f"Observer notification failed: {e}")
    
    def load_data(self, data: List[List[Any]], headers: List[str]) -> bool:
        """Load new data and validate"""
        try:
            # Validate data structure
            if not self._validate_data_structure(data, headers):
                return False
                
            self._state.raw_data = data
            self._state.headers = headers
            self._state.filtered_data = data.copy()
            
            # Reset filter and sort when new data is loaded
            self._state.current_filter = FilterConfig()
            self._state.sort_column = None
            self._state.sort_ascending = True
            
            self._notify_observers()
            return True
            
        except Exception as e:
            logging.error(f"Failed to load data: {e}")
            return False
    
    def load_data_from_file(self, file_path: str) -> Tuple[List[List[Any]], List[str]]:
        """Load data from file using pandas (moved from GUI)"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
                
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            # Check if pandas is available
            try:
                import pandas as pd
                PANDAS_AVAILABLE = True
            except ImportError:
                PANDAS_AVAILABLE = False
                raise ImportError("Pandas is required to load data.")
            
            if ext == '.csv':
                df = pd.read_csv(file_path)
            elif ext in ['.xlsx', '.xls']:
                try:
                    df = pd.read_excel(file_path)
                except:
                    engine = 'openpyxl' if ext == '.xlsx' else 'xlrd'
                    df = pd.read_excel(file_path, engine=engine)
            elif ext == '.txt':
                # For text files, create single column data
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = [l.strip() for l in f if l.strip()]
                df = pd.DataFrame(lines, columns=['text_data'])
            else:
                raise ValueError(f"Unsupported file extension: {ext}")
                
            data = df.values.tolist()
            headers = df.columns.tolist()
            
            # Load into internal state
            if self.load_data(data, headers):
                return data, headers
            else:
                raise ValueError("Failed to validate loaded data")
                
        except Exception as e:
            logging.error(f"Error loading data from file {file_path}: {e}")
            raise
    
    def load_csv_data(self, file_path: str) -> bool:
        """Load CSV data directly (simpler method for default data)"""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                headers = next(reader)  # First row as headers
                data = list(reader)
                return self.load_data(data, headers)
        except Exception as e:
            logging.error(f"Error loading CSV data: {e}")
            return False
    
    def save_data_to_file(self, file_path: str, data: Optional[List[List[Any]]] = None) -> bool:
        """Save data to file (moved from GUI)"""
        try:
            # Use current filtered data if no data provided
            if data is None:
                data = self._state.filtered_data
                
            headers = self._state.headers
            
            # Check if pandas is available for Excel support
            try:
                import pandas as pd
                PANDAS_AVAILABLE = True
            except ImportError:
                PANDAS_AVAILABLE = False
            
            if PANDAS_AVAILABLE and file_path.endswith(".xlsx"):
                df = pd.DataFrame(data, columns=headers if headers else None)
                df.to_excel(file_path, index=False)
            elif file_path.endswith(".csv"):
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    if headers:
                        writer.writerow(headers)
                    writer.writerows(data)
            else:
                # Basic text save for other types
                with open(file_path, "w", encoding="utf-8") as f:
                    if headers:
                        f.write(",".join(map(str, headers)) + "\n")
                    for row in data:
                        f.write(",".join(map(str, row)) + "\n")
            
            logging.info(f"Data saved successfully to {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving data to file {file_path}: {e}")
            return False

    def apply_filter(self, filter_config: FilterConfig) -> List[List[Any]]:
        """Apply filter and return filtered data"""
        try:
            self._state.current_filter = filter_config
            
            if not filter_config.text:
                self._state.filtered_data = self._state.raw_data.copy()
            else:
                self._state.filtered_data = self._filter_data(
                    self._state.raw_data, 
                    filter_config
                )
            
            # Apply current sort if any
            if self._state.sort_column:
                self._apply_sort()
            
            self._notify_observers()
            return self._state.filtered_data
            
        except Exception as e:
            logging.error(f"Filter application failed: {e}")
            return self._state.raw_data
    
    def sort_by_column(self, column_name: str, ascending: bool = True) -> List[List[Any]]:
        """Sort data by column"""
        try:
            if column_name not in self._state.headers:
                logging.warning(f"Column {column_name} not found in headers")
                return self._state.filtered_data
                
            self._state.sort_column = column_name
            self._state.sort_ascending = ascending
            
            self._apply_sort()
            self._notify_observers()
            return self._state.filtered_data
            
        except Exception as e:
            logging.error(f"Sort operation failed: {e}")
            return self._state.filtered_data
    
    def _apply_sort(self) -> None:
        """Apply current sort configuration"""
        if not self._state.sort_column or not self._state.filtered_data:
            return
            
        try:
            col_index = self._state.headers.index(self._state.sort_column)
            
            def sort_key(row):
                if col_index < len(row):
                    value = row[col_index]
                    # Try to convert to number for proper numeric sorting
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return str(value).lower()
                return ""
            
            self._state.filtered_data.sort(
                key=sort_key, 
                reverse=not self._state.sort_ascending
            )
            
        except Exception as e:
            logging.error(f"Error applying sort: {e}")

    def _filter_data(self, data: List[List[Any]], config: FilterConfig) -> List[List[Any]]:
        """Core filtering logic - separated from UI"""
        filtered_data = []
        
        for row in data:
            if config.column == "All Columns":
                if self._search_all_columns(row, config.text, config.case_sensitive):
                    filtered_data.append(row)
            else:
                if self._search_specific_column(row, config.column, config.text, config.case_sensitive):
                    filtered_data.append(row)
                    
        return filtered_data
    
    def _search_all_columns(self, row: List[Any], search_text: str, case_sensitive: bool) -> bool:
        """Search across all columns in a row"""
        for cell in row:
            cell_str = str(cell)
            if case_sensitive:
                if search_text in cell_str:
                    return True
            else:
                if search_text.lower() in cell_str.lower():
                    return True
        return False
    
    def _search_specific_column(self, row: List[Any], column_name: str, search_text: str, case_sensitive: bool) -> bool:
        """Search in a specific column"""
        if column_name not in self._state.headers:
            return False
            
        col_index = self._state.headers.index(column_name)
        if col_index >= len(row):
            return False
            
        cell_str = str(row[col_index])
        if case_sensitive:
            return search_text in cell_str
        else:
            return search_text.lower() in cell_str.lower()
    
    def _validate_data_structure(self, data: List[List[Any]], headers: List[str]) -> bool:
        """Validate data structure consistency"""
        if not headers:
            logging.warning("No headers provided")
            return False
            
        if not data:
            return True  # Empty data is valid
            
        header_count = len(headers)
        for i, row in enumerate(data):
            if len(row) != header_count:
                logging.warning(f"Row {i} has {len(row)} columns but headers have {header_count}")
                # Could auto-fix by padding or truncating, but for now just warn
                
        return True
    
    def get_current_data(self) -> List[List[Any]]:
        """Get currently filtered data"""
        return self._state.filtered_data
    
    def get_raw_data(self) -> List[List[Any]]:
        """Get original unfiltered data"""
        return self._state.raw_data
    
    def get_headers(self) -> List[str]:
        """Get current headers"""
        return self._state.headers
    
    def get_current_filter(self) -> FilterConfig:
        """Get current filter configuration"""
        return self._state.current_filter
    
    def get_sort_info(self) -> Tuple[Optional[str], bool]:
        """Get current sort column and direction"""
        return self._state.sort_column, self._state.sort_ascending
    
    def clear_filter(self) -> List[List[Any]]:
        """Clear all filters and return to raw data"""
        self._state.current_filter = FilterConfig()
        self._state.filtered_data = self._state.raw_data.copy()
        
        # Reapply sort if any
        if self._state.sort_column:
            self._apply_sort()
            
        self._notify_observers()
        return self._state.filtered_data
    
    def clear_sort(self) -> List[List[Any]]:
        """Clear sorting and return to filtered data in original order"""
        self._state.sort_column = None
        self._state.sort_ascending = True
        
        # Reapply filter to get unsorted filtered data
        if self._state.current_filter.text:
            self._state.filtered_data = self._filter_data(
                self._state.raw_data, 
                self._state.current_filter
            )
        else:
            self._state.filtered_data = self._state.raw_data.copy()
            
        self._notify_observers()
        return self._state.filtered_data
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary information about current data"""
        return {
            "total_rows": len(self._state.raw_data),
            "filtered_rows": len(self._state.filtered_data),
            "total_columns": len(self._state.headers),
            "headers": self._state.headers.copy(),
            "has_filter": bool(self._state.current_filter.text),
            "filter_text": self._state.current_filter.text,
            "filter_column": self._state.current_filter.column,
            "sort_column": self._state.sort_column,
            "sort_ascending": self._state.sort_ascending
        }
    
    def reset_data(self) -> None:
        """Reset all data and state"""
        self._state = DataState([], [], [], FilterConfig())
        self._notify_observers()