import logging
import pandas as pd
import csv
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

def read_file(filename: str, encoding: str = "utf-8", show_error_popup: bool = False) -> str:
    """
    Read the contents of a text file with robust error handling and optional GUI popup.
    :param filename: Path to the file to read
    :param encoding: File encoding (default: utf-8)
    :param show_error_popup: If True, show a Tkinter error popup on failure
    :return: File contents as string, or None on error
    """
    if not filename or not isinstance(filename, str):
        logger.error("Invalid filename provided for read_file.")
        if show_error_popup:
            _show_file_error_popup(f"Invalid filename provided: {filename}")
        return None
    try:
        with open(filename, "r", encoding=encoding) as file:
            content = file.read()
        logger.info(f"Successfully read file: {filename}")
        return content
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        if show_error_popup:
            _show_file_error_popup(f"File not found: {filename}")
        return None
    except UnicodeDecodeError as e:
        logger.error(f"Unicode decode error reading {filename}: {e}")
        if show_error_popup:
            _show_file_error_popup(f"Unicode decode error reading {filename}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading file {filename}: {e}", exc_info=True)
        if show_error_popup:
            _show_file_error_popup(f"Error reading file {filename}: {e}")
        return None


def _show_file_error_popup(message: str):
    """Show a Tkinter error popup for file read errors."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("File Read Error", message)
        root.destroy()
    except Exception as e:
        logger.error(f"Failed to show error popup: {e}")

def read_csv_builtin(filename: str) -> list:
    if not filename or not isinstance(filename, str):
        logger.error("Invalid filename provided for read_csv_builtin.")
        return []
    data = []
    try:
        with open(filename, mode="r", newline="", encoding="utf-8") as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                data.append(row)
        logger.info(f"Successfully read {filename} using built-in csv module.")
        return data
    except FileNotFoundError:
        logger.error(f"CSV file not found: {filename}")
        return []
    except Exception as e:
        logger.error(
            f"Error reading CSV file {filename} with built-in csv: {e}", exc_info=True
        )
        return []

def read_csv_pandas(filename: str):
    if not filename or not isinstance(filename, str):
        logger.error("Invalid filename provided for read_csv_pandas.")
        return None
    try:
        df = pd.read_csv(filename)
        logger.info(f"Successfully read {filename} using pandas.")
        return df
    except FileNotFoundError:
        logger.error(f"Pandas CSV file not found: {filename}")
        return None
    except pd.errors.EmptyDataError:
        logger.warning(f"Pandas CSV file is empty: {filename}")
        return pd.DataFrame()  # Return empty DataFrame for empty files
    except Exception as e:
        logger.error(
            f"Error reading CSV file {filename} with pandas: {e}", exc_info=True
        )
        return None

def read_excel(filename: str, sheet_name: str = None):
    if not filename or not isinstance(filename, str):
        logger.error("Invalid filename provided for read_excel.")
        return None
    try:
        df = pd.read_excel(filename, sheet_name=sheet_name)
        logger.info(
            f"Successfully read {filename} (sheet: {sheet_name or 'first'}) using pandas."
        )
        return df
    except FileNotFoundError:
        logger.error(f"Excel file not found: {filename}")
        return None
    except Exception as e:
        logger.error(f"Error reading Excel file {filename}: {e}", exc_info=True)
        return None
