import csv
import os
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Any, Optional
import logging

class FileManager:
    """Handles all file I/O operations for the Crew application."""
    
    def __init__(self):
        self.supported_data_extensions = ['.csv', '.xlsx', '.xls']
        self.supported_text_extensions = ['.txt', '.py', '.md']
        self.pandas_available = self._check_pandas_availability()
    
    def _check_pandas_availability(self) -> bool:
        try:
            import pandas as pd
            return True
        except ImportError:
            return False
    
    def get_supported_file_types(self) -> List[Tuple[str, str]]:
        """Return file type filters for dialogs."""
        return [
            ("Supported Files", ("*.csv", "*.xlsx", "*.xls", "*.txt", "*.py", "*.md")),
            ("Data Files", ("*.csv", "*.xlsx", "*.xls")),
            ("Text Files", ("*.txt", "*.py", "*.md")),
            ("All Files", "*.*"),
        ]
    
    def load_data_file(self, file_path: str) -> Tuple[List[List[Any]], List[str]]:
        """Load data from CSV/Excel files."""
        if not self.pandas_available:
            raise ImportError("Pandas is required to load data files.")
        
        try:
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            if ext == '.csv':
                df = pd.read_csv(file_path)
            elif ext in ['.xlsx', '.xls']:
                try:
                    df = pd.read_excel(file_path)
                except Exception:
                    engine = 'openpyxl' if ext == '.xlsx' else 'xlrd'
                    df = pd.read_excel(file_path, engine=engine)
            else:
                raise ValueError(f"Unsupported data file extension: {ext}")
            
            return df.values.tolist(), df.columns.tolist()
            
        except Exception as e:
            logging.error(f"Error loading data file {file_path}: {e}")
            raise
    
    def load_text_file(self, file_path: str) -> str:
        """Load content from text files."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logging.error(f"Error loading text file {file_path}: {e}")
            raise
    
    def save_data_file(self, data: List[List[Any]], headers: List[str], file_path: str) -> None:
        """Save data to CSV/Excel files."""
        try:
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            if ext == '.xlsx' and self.pandas_available:
                df = pd.DataFrame(data, columns=headers)
                df.to_excel(file_path, index=False)
            elif ext == '.csv':
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(data)
            else:
                # Fallback to basic text format
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(",".join(map(str, headers)) + "\n")
                    for row in data:
                        f.write(",".join(map(str, row)) + "\n")
                        
            logging.info(f"Data saved to {file_path}")
            
        except Exception as e:
            logging.error(f"Error saving data to {file_path}: {e}")
            raise
    
    def is_data_file(self, file_path: str) -> bool:
        """Check if file is a supported data file."""
        _, ext = os.path.splitext(file_path)
        return ext.lower() in self.supported_data_extensions
    
    def is_text_file(self, file_path: str) -> bool:
        """Check if file is a supported text file."""
        _, ext = os.path.splitext(file_path)
        return ext.lower() in self.supported_text_extensions