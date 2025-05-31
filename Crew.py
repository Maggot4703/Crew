#!/usr/bin/python3
"""
NPCs Data Processing Tool

This script provides functionality for image processing, data analysis from CSV/Excel,
data visualization, and batch processing of files.

Repository: https://github.com/markferguson/Crew
Author: Mark Ferguson
Version: 1.0.1
Date: May 2025
License: MIT
"""

import csv
import fnmatch  # Add this import if not already present
import json
import logging
import math
import os
import shutil  # Added import
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple  # Updated typing

import ijson
import pandas as pd
import pyttsx3  # Added import for TTS
from PIL import Image, ImageDraw
from tqdm import tqdm  # Added for progress bar

# Import our error handling utilities
try:
    from error_handler import (
        CSV_FILE_VALIDATORS,
        EXCEL_FILE_VALIDATORS,
        DataProcessingError,
        FileOperationError,
        handle_errors,
        safe_execute,
        safe_file_operation,
        validate_data,
    )

    ERROR_HANDLING_AVAILABLE = True
except ImportError:
    ERROR_HANDLING_AVAILABLE = False
    logging.warning(
        "Error handling utilities not available - using basic error handling"
    )

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Initialize pyttsx3 engine globally
try:
    tts_engine = pyttsx3.init()
    # Attempt to set an English voice by default
    voices = tts_engine.getProperty("voices")
    english_voice = None
    for voice in voices:
        if voice.id and "english" in voice.id.lower():
            english_voice = voice
            break
    if english_voice:
        tts_engine.setProperty("voice", english_voice.id)
        logger.info(f"TTS Using voice: {english_voice.id}")
    else:
        logger.warning("No English voice found for TTS, using default.")
except Exception as e:
    logger.error(f"Failed to initialize TTS engine: {e}")
    tts_engine = None


# region Text-to-Speech Utilities
def speak(text: str, voice_id: str = None) -> None:
    """
    Uses pyttsx3 to speak the given text.
    Logs errors if TTS fails, but does not raise an exception.
    """
    global tts_engine  # Ensure we are using the globally initialized engine
    if tts_engine:
        try:
            if voice_id:
                tts_engine.setProperty("voice", voice_id)
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS speak error: {e}", exc_info=False)
    else:
        logger.info(f"TTS disabled, would have said: '{text}'")


# endregion

# Conditional import - moved after logging setup
try:
    from mcp_service import CustomEncoder, get_mcp_context_for_npcs
except ImportError:
    logger.warning("mcp_service module not found - MCP functionality disabled")

    def get_mcp_context_for_npcs(df):
        return {"error": "mcp_service not available"}

    class CustomEncoder(json.JSONEncoder):
        pass


# region Configuration and Constants
# Constants
WIDTH = 1920
HEIGHT = 1080
IMAGE_DIMENSIONS = (WIDTH, HEIGHT)
DEFAULT_LINE_COLOR = (255, 0, 0)  # Red
DEFAULT_GRID_COLOR = (0, 255, 0)  # Green
DEFAULT_GRID_SIZE = (10, 10)  # 10x10 grid

# Directory structure
INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")
DATA_DIR = Path("data")

# File configurations
IMAGE_FILES = ["Cars1.png", "Cars2.png", "Cars3.png", "Cars4.png", "Cars5.png"]
GRID_SIZES = [(10, 10), (20, 20), (30, 30), (40, 40), (50, 50)]
# endregion


# region Backup Utilities
def backup_project(project_dir: Path, backup_parent_dir: Path) -> bool:
    """
    Creates a timestamped backup of the project_dir to a subdirectory in backup_parent_dir,
    excluding specified files and directories.

    Args:
        project_dir: The Path object of the directory to back up.
        backup_parent_dir: The Path object of the parent directory where backups will be stored.

    Returns:
        True if backup was successful, False otherwise.
    """
    excluded_patterns = [
        # ".venv",  # Commented out to include .venv in backups
        "tts_venv",  # Legacy TTS environment (removed, kept for compatibility)
        "data",  # Added to exclude the data directory
        ".git",
        ".pytest_cache",
        "__pycache__",
        "*.log",  # General log files
        "output.txt",
        "push_log.txt",
        "automated_fixes.txt",
        "HELP.txt",
        "project_summary.md",
        "*.pyc",
        "*.tmp",
        "*.bak",
        "*.swp",
        "Thumbs.db",
        ".DS_Store",
        "node_modules",  # Common JS dependency folder
        "build",  # Common build output folder
        "dist",  # Common distribution folder
        "*.egg-info",  # Python packaging metadata
    ]

    def ignore_func(directory, contents):
        """
        Custom ignore function for shutil.copytree.
        It ignores files and directories matching the excluded_patterns.
        """
        ignored_names = []
        for item in contents:
            item_path = Path(directory) / item
            # Check against each pattern for both files and directories
            for pattern in excluded_patterns:
                if fnmatch.fnmatch(
                    item, pattern
                ):  # Direct match for files/folders in current dir
                    ignored_names.append(item)
                    logger.debug(
                        f"Ignoring '{item_path}' due to pattern '{pattern}' (direct match)"
                    )
                    break
                # For directories, also check if any part of the path matches (e.g. excluding all .git folders)
                # This is implicitly handled by copytree calling ignore_func for subdirectories.
                # We primarily care about matching items *within* the current `contents` list.

            # Additionally, ensure common hidden directories are explicitly checked if not caught by simple patterns
            # This is somewhat redundant if patterns like ".*" are used but good for specific common ones.
            if item.startswith(".") and item in [
                ".venv",
                ".git",
                ".pytest_cache",
            ]:  # Redundant with patterns but safe
                if item not in ignored_names:
                    ignored_names.append(item)
                    logger.debug(
                        f"Ignoring hidden directory '{item_path}' (explicit check)"
                    )

        # Log what's being processed vs ignored in the current directory
        # logger.debug(f"In directory: {directory}")
        # logger.debug(f"  Contents: {contents}")
        # logger.debug(f"  Ignoring: {ignored_names}")
        return set(
            ignored_names
        )  # shutil.copytree expects a set or list of names to ignore

    try:
        project_name = project_dir.name
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        backup_subdir_name = f"{project_name}_Backup_{timestamp}"
        backup_target_dir = backup_parent_dir / backup_subdir_name

        backup_parent_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting backup of '{project_dir}' to '{backup_target_dir}'...")
        speak(f"Starting backup of project {project_name}.")

        shutil.copytree(
            project_dir, backup_target_dir, ignore=ignore_func, dirs_exist_ok=True
        )

        logger.info(f"Project backup completed successfully to '{backup_target_dir}'.")
        speak(f"Project {project_name} backup completed successfully.")
        return True

    except FileNotFoundError as e:
        logger.error(
            f"Backup failed: Source directory '{project_dir}' not found. Error: {e}",
            exc_info=True,
        )
        speak(f"Backup of project {project_name} failed. Source directory not found.")
        return False
    except Exception as e:
        logger.error(f"Backup failed for '{project_dir}'. Error: {e}", exc_info=True)
        speak(f"An error occurred during the backup of project {project_name}.")
        return False


# endregion


# region Image Processing Utilities
def markHorizontalLine(
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    color: Tuple[int, int, int] = DEFAULT_LINE_COLOR,
    thickness: int = 1,
) -> Image:
    """
    Creates a new image with a horizontal line drawn on it.

    The line is drawn on a new white image of default dimensions.

    Args:
        x1: Starting x-coordinate of the line.
        y1: Starting y-coordinate of the line.
        x2: Ending x-coordinate of the line.
        y2: Ending y-coordinate of the line.
        color: Color of the line as an RGB tuple (default is DEFAULT_LINE_COLOR).
        thickness: Width of the line in pixels (default is 1).

    Returns:
        PIL.Image.Image: A new PIL Image object with the drawn line.
    """
    img = Image.new("RGB", IMAGE_DIMENSIONS, "white")
    draw = ImageDraw.Draw(img)
    # Draw the line
    draw.line([(x1, y1), (x2, y2)], fill=color, width=thickness)
    # Return the image
    return img


def overlayGrid(
    image_path: str,
    grid_color: Tuple[int, int, int] = DEFAULT_GRID_COLOR,  # Corrected type hint
    grid_size: tuple = DEFAULT_GRID_SIZE,
) -> Image:
    """
    Overlays a grid on an existing image.

    The grid lines are drawn at equal intervals based on the `grid_size` parameter.
    The color of the grid can also be specified.

    Args:
        image_path: Path to the source image file.
        grid_color: Color for grid lines as an RGB tuple (default is DEFAULT_GRID_COLOR).
        grid_size: Tuple of (columns, rows) for grid dimensions (default is DEFAULT_GRID_SIZE).

    Returns:
        PIL.Image.Image: The modified PIL Image object with the grid overlay.

    Raises:
        ValueError: If grid dimensions (columns or rows) are not positive.
        FileNotFoundError: If the source image file does not exist.
        IOError: If the image file cannot be opened or processed.
    """
    # Input validation
    if not all(x > 0 for x in grid_size):
        raise ValueError("Grid dimensions must be positive")

    try:
        # Load and process image
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)

        # Calculate dimensions
        img_width, img_height = img.size
        cols, rows = grid_size
        cell_width = img_width / cols
        cell_height = img_height / rows

        # Draw grid lines
        for x in range(1, cols):
            pos_x = int(x * cell_width)
            draw.line([(pos_x, 0), (pos_x, img_height)], fill=grid_color, width=1)

        for y in range(1, rows):
            pos_y = int(y * cell_height)
            draw.line([(0, pos_y), (img_width, pos_y)], fill=grid_color, width=1)

        return img

    except FileNotFoundError:
        logger.error(f"Error: Image file '{image_path}' not found")
        raise
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise


# endregion


# region File Handling Utilities
def read_csv_builtin(filename: str) -> list:
    """
    Reads CSV data using the built-in `csv` module.

    Returns all rows including the header row.

    Args:
        filename: Path to the CSV file.

    Returns:
        A list of lists, where each inner list represents a row from the CSV file.
    """
    data = []
    with open(filename, "r") as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            data.append(row)
    return data


def read_csv_pandas(filename: str) -> pd.DataFrame:
    """
    Reads CSV data using the pandas library.

    Args:
        filename: Path to the CSV file.

    Returns:
        A pandas DataFrame containing the CSV data.
    """
    return pd.read_csv(filename)


def read_excel(filename: str, sheet_name: str = None) -> pd.DataFrame:
    """
    Reads Excel data using the pandas library.

    Args:
        filename: Path to the Excel file (.xlsx or .xls).
        sheet_name: Name or index of the sheet to read (default is the first sheet).

    Returns:
        A pandas DataFrame containing the Excel data.
    """
    return pd.read_excel(filename, sheet_name=sheet_name)


def read_file_as_string(filename: str) -> str | None:
    """
    Reads a file and returns its contents as a string.

    Args:
        filename: Path to the file to read.

    Returns:
        A string containing the file contents, or None if an error occurs.
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Error: Could not find file '{filename}'")
    except Exception as e:
        logger.error(f"Error reading file: {e}")
    return None


def read_file(filename: str) -> str | None:
    """
    Reads a file and returns its contents as a string.
    This is the backward-compatible version that returns string content.

    For structured data (CSV/Excel), use read_structured_file() instead.

    Args:
        filename: Path to the file to read.

    Returns:
        A string containing the file contents, or None if an error occurs.
    """
    return read_file_as_string(filename)


def read_structured_file(filename: str) -> pd.DataFrame | None:
    """
    Reads a CSV or Excel file using pandas.

    Determines the file type based on the extension.

    Args:
        filename: Path to the file (.csv, .xlsx, or .xls).

    Returns:
        A pandas DataFrame containing the loaded data, or None if an error occurs.
    """
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(filename)
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(filename)
        else:
            raise ValueError("Unsupported file format. Use .csv or .xlsx/.xls")
        return df
    except FileNotFoundError:
        logger.error(f"Error: Could not find file '{filename}'")
    except Exception as e:
        logger.error(f"Error reading file: {e}")
    return None


def showColumn(col: str = "SQUAD") -> str:
    """
    Displays data from a specific column in 'data/columns.csv'.

    Prints the column name and then iterates through 'data/columns.csv',
    printing rows that are not comments and have content.

    Args:
        col: The name of the column to display (default is "SQUAD").

    Returns:
        A string indicating the column being displayed, e.g., "Column: SQUAD".
    """
    string = f"Column: {col}"
    print(string)
    try:
        with open("data/columns.csv", "r") as f:  # Changed "w" to "r"
            reader = csv.reader(f)
            for row in reader:
                if row and not row[0].startswith("#"):  # Added check for empty row
                    if len(row) > 1:
                        print(row[0], row[1])
                        # f.write(f"{row[0]}, {row[1]}\\n") # Removed problematic write
                    else:
                        print(row[0])
    except FileNotFoundError:
        logger.error("Error: data/columns.csv not found in showColumn")
    except Exception as e:
        logger.error(f"Error in showColumn: {e}")
    return string


def showAllColumns(columns: List[str]) -> None:  # Corrected type hint
    """
    Displays all specified columns by calling `showColumn` for each.

    Args:
        columns: A list of column names to display.
    """
    for col in columns:
        showColumn(col)


# endregion


# region Help File Generation
def generate_help_file(output_path_str: str) -> bool:
    """
    Generates a HELP.txt file with comprehensive advice on using Crew.py.

    Args:
        output_path_str: The string path for the output HELP.txt file.

    Returns:
        True if help file generation was successful, False otherwise.
    """
    output_path = Path(output_path_str)
    logger.info(f"Generating help file at '{output_path}'...")
    speak("Generating help file.")

    help_content = f"""
# Crew.py Help Guide - {pd.Timestamp.now().strftime('%Y-%m-%d')}

Thank you for using Crew.py! This guide provides an overview of its features and how to use them.

## Core Functionalities:

1.  **Project Backup (`backup_project`)**:
    *   Creates a timestamped backup of the entire project directory.
    *   Excludes common temporary files, virtual environments, and Git folders (see `excluded_patterns` in `Crew.py`).
    *   Backups are stored in a sister directory named `PROJECTS_Crew_Backups` (or as configured).
    *   Usage: This is typically run automatically at the start of the main script execution.

2.  **Project Summary (`generate_project_summary`)**:
    *   Generates a `project_summary.md` file in the project root.
    *   This file includes:
        *   Directory structure (excluding common temporary/build directories).
        *   Total file and directory counts.
        *   Breakdown of file types.
        *   Approximate lines of Python code (excluding comments and blank lines).
    *   Usage: Run automatically by the main script.

3.  **Automated Fixes & Git Integration (`auto_fix_all_issues`)**:
    *   **Code Formatting**: Runs `isort` (for import sorting) and `black` (for code style) on all Python files in the project.
        *   Requires `isort` and `black` to be installed in your Python environment (`pip install isort black`).
    *   **Git Commit & Push**: After formatting, it automatically:
        *   Adds all changes (`git add .`).
        *   Commits changes with a timestamped message (e.g., "Automated fixes and updates (YYYY-MM-DD HH:MM:SS)").
        *   Pushes the commit to the `origin` remote (typically GitHub).
        *   Requires Git to be installed and configured for the project (e.g., `git init`, `git remote add origin <your-repo-url>`).
        *   Errors during Git operations are logged to `push_log.txt`.
    *   Usage: Run automatically by the main script.

4.  **Text-to-Speech (TTS) Notifications (`speak`)**:
    *   Provides audible feedback for key operations (e.g., backup start/finish, errors).
    *   Uses the `pyttsx3` library. Requires TTS engines to be installed on your system.
        *   On Linux: `sudo apt-get install espeak festival` (or other TTS engines).
        *   See `tts_requirements.txt` and `install_tts.sh` for setup help.
    *   If TTS initialization fails, it logs a warning and continues silently.

5.  **GUI Launch (`launch_gui_if_configured`)**:
    *   Attempts to launch a `gui.py` script if it exists in the project directory.
    *   The GUI is expected to be a separate Tkinter or PyQt application.
    *   Usage: Run automatically at the end of the main script execution.

6.  **Image Processing (`job1`, `markHorizontalLine`, `overlayGrid`)**:
    *   `job1`: Example task that overlays grids on images specified in `IMAGE_FILES`.
    *   These are more specific utilities and might need adaptation for your use case.

7.  **Data Handling (`job2`, `job3`, `read_csv_pandas`, `read_excel`, etc.)**:
    *   Example tasks for reading and performing basic analysis on CSV and Excel files.
    *   Utilizes the `pandas` library.

8.  **Logging**:
    *   Comprehensive logging is implemented using Python's `logging` module.
    *   Logs are by default sent to the console and also to `output.txt` in the project root when the script is run directly.
    *   Log file `output.txt` is created by the main script to capture stdout/stderr.

## Setup & Requirements:

*   **Python 3.x**: Ensure you have a compatible Python version.
*   **`requirements.txt`**: Install core dependencies: `pip install -r requirements.txt`
    *   Key libraries: `pandas`, `Pillow` (for image processing), `tqdm`.
*   **`tts_requirements.txt`**: For Text-to-Speech: `pip install -r tts_requirements.txt`
    *   Key library: `pyttsx3`.
    *   System-level TTS engines might also be needed (see TTS section above).
*   **Linters/Formatters**: For `auto_fix_all_issues`: `pip install isort black`.
*   **Git**: For `auto_fix_all_issues`: Ensure Git is installed and your project is a Git repository with a remote configured.

## Running Crew.py:

    python3 Crew.py

The script will perform its main sequence: backup, summary, auto-fixes, GUI launch, etc.

## Customization:

*   **Backup Exclusions**: Modify `excluded_patterns` in the `backup_project` function in `Crew.py`.
*   **Image Processing**: Adjust `IMAGE_FILES`, `GRID_SIZES`, etc., in the "Configuration and Constants" section of `Crew.py`.
*   **Data Files**: Update paths in `job2`, `job3`, etc., if you use these data processing tasks.
*   **Main Sequence**: Modify the `if __name__ == "__main__":` block in `Crew.py` to change the order of operations or disable certain features.

## Troubleshooting:

*   **TTS Issues**:
    *   Check `tts_requirements.txt` and `install_tts.sh`.
    *   Ensure system TTS engines are installed (e.g., `espeak` on Linux).
    *   Look for error messages in the console log related to `pyttsx3.init()`.
    *   The script attempts to find an English voice; if not found, it uses the default.
*   **Git Push Failures**:
    *   Check `push_log.txt` for detailed error messages from Git.
    *   Ensure your Git remote (`origin`) is correctly configured.
    *   Ensure you have an internet connection and permissions to push to the repository.
*   **Linter/Formatter Issues**:
    *   Make sure `isort` and `black` are installed in the environment where `Crew.py` is run.
    *   Check console logs for errors from these tools.
*   **`ModuleNotFoundError`**: Ensure all dependencies from `requirements.txt` (and `tts_requirements.txt` if using TTS) are installed in your active Python environment.
*   **File Paths**: The script uses `pathlib.Path` for robust path handling. Most paths are relative to the script's location.

This help file is automatically generated. For the most up-to-date information, please refer to the source code and comments within `Crew.py`.
"""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(help_content)
        logger.info(f"Help file '{output_path}' generated successfully.")
        speak("Help file generated successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to generate help file. Error: {e}", exc_info=True)
        speak("Failed to generate help file.")
        return False


# endregion


# region Project Analysis Utilities
def generate_project_summary(project_dir: Path, output_file: Path) -> bool:
    """
    Generates a Markdown summary of the project structure, file types, and basic stats.

    Args:
        project_dir: The Path object of the project directory.
        output_file: The Path object for the output Markdown file.

    Returns:
        True if summary generation was successful, False otherwise.
    """
    logger.info(f"Generating project summary for '{project_dir}' to '{output_file}'...")
    speak("Generating project summary.")
    try:
        summary_content = [f"# Project Summary for {project_dir.name}\\n\\n"]
        summary_content.append(
            f"Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n"
        )
        summary_content.append("## Directory Structure\\n\\n")

        file_stats: Dict[str, Any] = {
            "total_files": 0,
            "total_dirs": 0,
            "file_types": {},
        }
        # More comprehensive exclusion list
        excluded_dirs = {
            ".git",
            ".venv",
            "__pycache__",
            "node_modules",
            "build",
            "dist",
            "output",
            "input",
            "data",  # Common data/output folders for this project
            "tests",
            "docs",
            ".vscode",
            ".idea",
            "site",
            "htmlcov",
            "*.egg-info",
            "temp",
            "tmp",
            "logs",
            "backups",  # General temporary/log/backup folders
        }
        excluded_files = {
            ".DS_Store",
            "Thumbs.db",
            "desktop.ini",
            "*.log",
            "*.tmp",
            "*.bak",
            "*.swp",  # General temp/backup files
            "output.txt",
            "project_summary.md",
            "HELP.txt",
            "push_log.txt",
            "automated_fixes.txt",  # Files generated by this script
        }

        # Use project_dir.glob for specific exclusions if needed, os.walk is generally fine
        paths_to_log = []
        for root_str, dirs, files in os.walk(project_dir, topdown=True):
            root = Path(root_str)
            # Filter directories
            dirs[:] = [
                d for d in dirs if d not in excluded_dirs and not d.startswith(".")
            ]

            level = len(root.relative_to(project_dir).parts)
            indent = "  " * level

            if root != project_dir:
                paths_to_log.append(f"{indent}- {root.name}/\\n")

            file_stats["total_dirs"] += 1

            sub_indent = "  " * (level + 1)
            for f_name in files:
                # Check against excluded files patterns
                if any(
                    fnmatch.fnmatch(f_name, pattern) for pattern in excluded_files
                ) or f_name.startswith("."):
                    continue

                file_stats["total_files"] += 1
                file_ext = (
                    Path(f_name).suffix.lower()
                    if Path(f_name).suffix
                    else "no_extension"
                )
                file_stats["file_types"][file_ext] = (
                    file_stats["file_types"].get(file_ext, 0) + 1
                )

                paths_to_log.append(f"{sub_indent}- {f_name}\\n")

        summary_content.extend(paths_to_log)

        summary_content.append("\\n## File Statistics\\n\\n")
        summary_content.append(
            f"- Total Directories (scanned): {file_stats['total_dirs'] -1 }\\n"
        )  # -1 for project_dir itself
        summary_content.append(
            f"- Total Files (scanned): {file_stats['total_files']}\\n"
        )
        summary_content.append("- File Types:\\n")
        for ext, count in sorted(file_stats["file_types"].items()):
            summary_content.append(f"  - {ext}: {count}\\n")

        # Basic Python LoC count
        py_files = [
            p
            for p in project_dir.rglob("*.py")
            if not any(excluded_part in p.parts for excluded_part in excluded_dirs)
        ]
        total_loc = 0
        if py_files:
            summary_content.append("\\n## Python Code Statistics (Approximate)\\n\\n")
            for py_file in py_files:
                try:
                    with open(py_file, "r", encoding="utf-8", errors="ignore") as pf:
                        lines = sum(
                            1
                            for line in pf
                            if line.strip() and not line.strip().startswith("#")
                        )
                        total_loc += lines
                except Exception:
                    pass
            summary_content.append(
                f"- Approximate Lines of Python Code (excluding comments/blanks): {total_loc}\\n"
            )

        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(summary_content)

        logger.info(f"Project summary saved to '{output_file}'.")
        speak("Project summary generated successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to generate project summary. Error: {e}", exc_info=True)
        speak("Failed to generate project summary.")
        return False


# endregion


# region Git and Linting Utilities
def fix_lint_errors(project_dir: Path) -> bool:
    """
    Runs isort and black to format Python code in the project directory.
    SAFE VERSION: Only processes main Python files with timeouts and exclusions.

    Args:
        project_dir: The Path object of the project directory.

    Returns:
        True if linters ran successfully, False on error.
    """
    logger.info(f"Running linters (isort, black) on '{project_dir}' (safe mode)...")
    speak("Running code formatters in safe mode.")
    try:
        abs_project_dir = project_dir.resolve()

        # Define specific Python files to format (avoid huge directories)
        main_python_files = []
        for py_file in abs_project_dir.glob("*.py"):
            # Skip test files and generated files
            if not py_file.name.startswith(("test_", "output.txt", "__")):
                main_python_files.append(str(py_file))

        if not main_python_files:
            logger.info("No main Python files found to format.")
            return True

        logger.info(
            f"Formatting {len(main_python_files)} Python files: {[Path(f).name for f in main_python_files]}"
        )

        isort_path = shutil.which("isort")
        black_path = shutil.which("black")

        # Run isort with timeout and specific files
        if not isort_path:
            logger.warning("isort command not found. Skipping isort.")
        else:
            try:
                isort_result = subprocess.run(
                    [isort_path] + main_python_files,
                    cwd=abs_project_dir,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=30,  # 30 second timeout
                )
                if isort_result.returncode != 0:
                    logger.warning(
                        f"isort issues:\nSTDOUT:\n{isort_result.stdout}\nSTDERR:\n{isort_result.stderr}"
                    )
                else:
                    logger.info(f"isort completed.\n{isort_result.stdout}")
            except subprocess.TimeoutExpired:
                logger.error("isort timed out after 30 seconds. Skipping.")
                speak("isort timed out, skipping.")

        # Run black with timeout, specific files, and fast mode
        if not black_path:
            logger.warning("black command not found. Skipping black.")
        else:
            try:
                # Use --fast to skip AST safety checks (much faster)
                black_result = subprocess.run(
                    [black_path, "--fast"] + main_python_files,
                    cwd=abs_project_dir,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=60,  # 60 second timeout
                )
                if black_result.returncode != 0:
                    logger.error(
                        f"black encountered an error:\nSTDOUT:\n{black_result.stdout}\nSTDERR:\n{black_result.stderr}"
                    )
                else:
                    logger.info(f"black completed.\n{black_result.stdout}")
            except subprocess.TimeoutExpired:
                logger.error("black timed out after 60 seconds. Skipping.")
                speak("black timed out, skipping.")

        logger.info("Linters (isort, black) finished safely.")
        speak("Code formatting complete.")
        return True
    except Exception as e:
        logger.error(f"Error running linters: {e}", exc_info=True)
        speak("An error occurred while running code formatters.")
        return False


def push_to_github(project_dir: Path, commit_message: str) -> bool:
    """
    Adds all changes, commits them, and pushes to the remote GitHub repository.
    Logs errors to push_log.txt.

    Args:
        project_dir: The Path object of the project directory (git repository).
        commit_message: The commit message.

    Returns:
        True if all git operations were successful, False otherwise.
    """
    logger.info(f"Attempting to push changes to GitHub for '{project_dir}'...")
    speak("Attempting to push changes to GitHub.")

    abs_project_dir = project_dir.resolve()
    push_log_file = project_dir / "push_log.txt"
    git_path = shutil.which("git")

    if not git_path:
        err_msg = "Git command not found. Ensure Git is installed and in PATH."
        logger.error(err_msg)
        with open(push_log_file, "a", encoding="utf-8") as log_f:
            log_f.write(f"{pd.Timestamp.now()}: {err_msg}\\n")
        speak("Git command not found. Please check installation.")
        return False

    try:
        add_result = subprocess.run(
            [git_path, "add", "."],
            cwd=abs_project_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        if add_result.returncode != 0:
            err_msg = f"git add failed:\nSTDOUT:\n{add_result.stdout}\nSTDERR:\n{add_result.stderr}"
            logger.error(err_msg)
            with open(push_log_file, "a", encoding="utf-8") as log_f:
                log_f.write(f"{pd.Timestamp.now()}: {err_msg}\\n")
            speak("Git add command failed.")
            return False
        logger.info("git add . successful.")

        commit_result = subprocess.run(
            [git_path, "commit", "-m", commit_message],
            cwd=abs_project_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        if commit_result.returncode != 0 and not (
            "nothing to commit" in commit_result.stdout.lower()
            or "nothing to commit" in commit_result.stderr.lower()
        ):
            err_msg = f"git commit failed:\nSTDOUT:\n{commit_result.stdout}\nSTDERR:\n{commit_result.stderr}"
            logger.error(err_msg)
            with open(push_log_file, "a", encoding="utf-8") as log_f:
                log_f.write(f"{pd.Timestamp.now()}: {err_msg}\\n")
            speak("Git commit command failed.")
            return False
        elif (
            "nothing to commit" in commit_result.stdout.lower()
            or "nothing to commit" in commit_result.stderr.lower()
        ):
            logger.info("Nothing to commit.")
            speak("Nothing to commit to GitHub.")
            return True
        logger.info(f"git commit successful: {commit_message}")

        current_branch_result = subprocess.run(
            [git_path, "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=abs_project_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        current_branch = (
            current_branch_result.stdout.strip()
            if current_branch_result.returncode == 0
            and current_branch_result.stdout.strip()
            else "main"
        )

        push_result = subprocess.run(
            [git_path, "push", "origin", current_branch],
            cwd=abs_project_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        if push_result.returncode != 0:
            err_msg = f"git push failed:\nSTDOUT:\n{push_result.stdout}\nSTDERR:\n{push_result.stderr}"
            logger.error(err_msg)
            with open(push_log_file, "a", encoding="utf-8") as log_f:
                log_f.write(f"{pd.Timestamp.now()}: {err_msg}\\n")
            speak("Git push command failed. Check push log for details.")
            return False

        logger.info(
            f"Successfully pushed to origin/{current_branch}.\n{push_result.stdout}"
        )
        speak("Changes successfully pushed to GitHub.")
        return True

    except subprocess.TimeoutExpired as e:
        err_msg = f"Git operation timed out: {e}"
        logger.error(err_msg, exc_info=True)
        with open(push_log_file, "a", encoding="utf-8") as log_f:
            log_f.write(f"{pd.Timestamp.now()}: {err_msg}\\n")
        speak("A Git operation timed out.")
        return False
    except Exception as e:
        err_msg = f"Error during Git operations: {e}"
        logger.error(err_msg, exc_info=True)
        with open(push_log_file, "a", encoding="utf-8") as log_f:
            log_f.write(f"{pd.Timestamp.now()}: {err_msg}\\n")
        speak("An error occurred during Git operations. Check push log for details.")
        return False


def auto_fix_all_issues(project_dir: Path) -> None:
    """
    Runs linters/formatters and then commits and pushes changes to GitHub.
    """
    logger.info("Starting auto-fix all issues process...")
    speak("Starting automated fixes and GitHub push.")

    if fix_lint_errors(project_dir):
        logger.info("Linting completed. Proceeding to Git operations.")
        timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"Automated fixes and updates ({timestamp})"
        if not push_to_github(project_dir, commit_message):
            logger.error("Auto-fix process: GitHub push failed.")
            # speak("Automated GitHub push failed.") # push_to_github already speaks
        else:
            logger.info("Auto-fix process: GitHub push successful.")
            # speak("Automated fixes and GitHub push completed successfully.") # push_to_github already speaks
    else:
        logger.error("Auto-fix process: Linting failed. Skipping Git operations.")
        speak("Automated code formatting failed. Skipping GitHub push.")


# endregion


# region Job Functions - Data Processing Tasks
def spacer():
    """Print a visual separator for console output."""
    print("\n" + "=" * 50 + "\n")


def job1():
    """Image Processing - Overlay grids on images in IMAGE_FILES."""
    logger.info("Starting image processing job...")
    speak("Starting image processing.")

    try:
        if not IMAGE_FILES:
            logger.warning("No image files specified in IMAGE_FILES list")
            return

        for img_file in IMAGE_FILES:
            img_path = INPUT_DIR / img_file
            if img_path.exists():
                logger.info(f"Processing image: {img_file}")
                # Process with multiple grid sizes
                for grid_size in GRID_SIZES:
                    output_name = (
                        f"{img_path.stem}_grid_{grid_size[0]}x{grid_size[1]}.png"
                    )
                    output_path = OUTPUT_DIR / output_name

                    # Call image processing functions if they exist
                    try:
                        if "overlayGrid" in globals():
                            overlayGrid(str(img_path), str(output_path), grid_size)
                            logger.info(f"Created grid overlay: {output_name}")
                        else:
                            logger.warning(
                                "overlayGrid function not available - creating placeholder"
                            )
                            # Create a simple placeholder file
                            import shutil

                            shutil.copy2(str(img_path), str(output_path))
                    except Exception as e:
                        logger.error(
                            f"Error processing {img_file} with grid {grid_size}: {e}"
                        )
            else:
                logger.warning(f"Image file not found: {img_path}")

        logger.info("Image processing job completed")
        speak("Image processing complete.")

    except Exception as e:
        logger.error(f"Error in job1: {e}")
        speak("Image processing encountered an error.")


@handle_errors(default_return=None) if ERROR_HANDLING_AVAILABLE else lambda f: f
def job2(csv_file: str):
    """CSV Analysis - Comprehensive analysis of CSV data with statistics and insights."""
    logger.info(f"Starting enhanced CSV analysis job for: {csv_file}")
    speak("Starting CSV analysis.")

    # Validate input file if error handling is available
    if ERROR_HANDLING_AVAILABLE:
        if not validate_data(csv_file, CSV_FILE_VALIDATORS, "CSV file validation"):
            logger.error("CSV file validation failed - cannot proceed with analysis")
            speak("CSV file validation failed.")
            return

    try:
        csv_path = Path(csv_file)
        if not csv_path.exists():
            logger.error(f"CSV file not found: {csv_path}")
            return

        # Try to import pandas for comprehensive CSV processing
        try:
            import pandas as pd

            # Load CSV with error handling for encoding issues
            encodings_to_try = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
            df = None
            encoding_used = None

            for encoding in encodings_to_try:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding)
                    encoding_used = encoding
                    break
                except UnicodeDecodeError:
                    continue

            if df is None:
                logger.error("Could not decode CSV file with any standard encoding")
                return

            logger.info(f"CSV loaded successfully with {encoding_used} encoding")
            logger.info(f"Dataset shape: {len(df)} rows, {len(df.columns)} columns")

            # === COMPREHENSIVE CSV ANALYSIS ===
            logger.info("=== CSV ANALYSIS REPORT ===")

            # 1. Basic Data Information
            logger.info(f"File: {csv_path.name}")
            logger.info(f"Size: {csv_path.stat().st_size / 1024:.2f} KB")
            logger.info(f"Columns: {list(df.columns)}")

            # 2. Data Types Analysis
            logger.info("\n--- Data Types ---")
            for col, dtype in df.dtypes.items():
                null_count = df[col].isnull().sum()
                null_pct = (null_count / len(df)) * 100
                logger.info(f"  {col}: {dtype} ({null_count} nulls, {null_pct:.1f}%)")

            # 3. Missing Data Analysis
            missing_data = df.isnull().sum()
            total_missing = missing_data.sum()
            if total_missing > 0:
                logger.info(f"\n--- Missing Data Summary ---")
                logger.info(f"Total missing values: {total_missing}")
                for col, count in missing_data[missing_data > 0].items():
                    percentage = (count / len(df)) * 100
                    logger.info(f"  {col}: {count} ({percentage:.2f}%)")
            else:
                logger.info("\n--- No Missing Data Found ---")

            # 4. Numeric Columns Analysis
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) > 0:
                logger.info(f"\n--- Numeric Analysis ({len(numeric_cols)} columns) ---")
                for col in numeric_cols:
                    stats = df[col].describe()
                    logger.info(f"  {col}:")
                    logger.info(
                        f"    Mean: {stats['mean']:.2f}, Std: {stats['std']:.2f}"
                    )
                    logger.info(f"    Min: {stats['min']:.2f}, Max: {stats['max']:.2f}")
                    logger.info(
                        f"    Q1: {stats['25%']:.2f}, Median: {stats['50%']:.2f}, Q3: {stats['75%']:.2f}"
                    )

            # 5. Categorical Columns Analysis
            categorical_cols = df.select_dtypes(include=["object"]).columns
            if len(categorical_cols) > 0:
                logger.info(
                    f"\n--- Categorical Analysis ({len(categorical_cols)} columns) ---"
                )
                for col in categorical_cols:
                    unique_count = df[col].nunique()
                    logger.info(f"  {col}: {unique_count} unique values")

                    if (
                        unique_count <= 20
                    ):  # Show distribution for columns with few unique values
                        value_counts = df[col].value_counts().head(10)
                        logger.info(f"    Distribution: {dict(value_counts)}")
                    else:
                        # Show most and least common values
                        top_values = df[col].value_counts().head(3)
                        logger.info(f"    Top 3 values: {dict(top_values)}")

            # 6. Data Quality Checks
            logger.info(f"\n--- Data Quality Assessment ---")

            # Check for duplicates
            duplicates = df.duplicated().sum()
            if duplicates > 0:
                logger.info(f"  Duplicate rows: {duplicates}")
            else:
                logger.info("  No duplicate rows found")

            # Check for empty strings in text columns
            empty_strings = 0
            for col in categorical_cols:
                empty_count = (df[col] == "").sum()
                empty_strings += empty_count
                if empty_count > 0:
                    logger.info(f"  Empty strings in {col}: {empty_count}")

            if empty_strings == 0:
                logger.info("  No empty strings found in text columns")

            # 7. Sample Data Display
            if not df.empty and len(df) > 0:
                logger.info(f"\n--- Sample Data (first 3 rows) ---")
                for i, row in df.head(3).iterrows():
                    logger.info(
                        f"  Row {i+1}: {dict(row.head(10))}"
                    )  # Limit to first 10 columns for readability

                if len(df.columns) > 10:
                    logger.info(f"    ... and {len(df.columns) - 10} more columns")

            # 8. Pattern Detection for common CSV types
            logger.info(f"\n--- Pattern Detection ---")

            # Look for common data patterns
            patterns_found = []
            column_names_lower = [col.lower() for col in df.columns]

            # Check for common patterns
            if any("id" in name for name in column_names_lower):
                patterns_found.append("ID columns detected")
            if any("name" in name for name in column_names_lower):
                patterns_found.append("Name columns detected")
            if any("date" in name or "time" in name for name in column_names_lower):
                patterns_found.append("Date/Time columns detected")
            if any("email" in name for name in column_names_lower):
                patterns_found.append("Email columns detected")
            if any("phone" in name for name in column_names_lower):
                patterns_found.append("Phone columns detected")

            # NPC-specific patterns
            npc_indicators = [
                "npc",
                "character",
                "role",
                "class",
                "level",
                "hp",
                "strength",
                "dexterity",
            ]
            if any(
                indicator in name
                for name in column_names_lower
                for indicator in npc_indicators
            ):
                patterns_found.append("NPC/Gaming data detected")

            if patterns_found:
                for pattern in patterns_found:
                    logger.info(f"  {pattern}")
            else:
                logger.info("  No specific patterns detected")

            logger.info("\n=== CSV Analysis Complete ===")
            speak("CSV analysis complete.")

        except ImportError:
            logger.warning("pandas not available - using basic CSV reading")
            import csv

            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
                logger.info(f"CSV loaded: {len(rows)} rows")
                if rows:
                    logger.info(f"Headers: {rows[0]}")
                    if len(rows) > 1:
                        logger.info(f"Sample row: {rows[1]}")

    except Exception as e:
        logger.error(f"Error in job2: {e}")
        speak("CSV analysis encountered an error.")


@handle_errors(default_return=None) if ERROR_HANDLING_AVAILABLE else lambda f: f
def job3(excel_file: str):
    """Excel Analysis - Comprehensive analysis of Excel data with multi-sheet support."""
    logger.info(f"Starting enhanced Excel analysis job for: {excel_file}")
    speak("Starting Excel analysis.")

    # Validate input file if error handling is available
    if ERROR_HANDLING_AVAILABLE:
        if not validate_data(
            excel_file, EXCEL_FILE_VALIDATORS, "Excel file validation"
        ):
            logger.error("Excel file validation failed - cannot proceed with analysis")
            speak("Excel file validation failed.")
            return

    try:
        excel_path = Path(excel_file)
        if not excel_path.exists():
            logger.error(f"Excel file not found: {excel_path}")
            return

        try:
            import pandas as pd

            # First, check all available sheets
            excel_file_obj = pd.ExcelFile(excel_path)
            sheet_names = excel_file_obj.sheet_names

            logger.info("=== EXCEL ANALYSIS REPORT ===")
            logger.info(f"File: {excel_path.name}")
            logger.info(f"Size: {excel_path.stat().st_size / 1024:.2f} KB")
            logger.info(f"Number of sheets: {len(sheet_names)}")
            logger.info(f"Sheet names: {sheet_names}")

            # Analyze each sheet
            for sheet_idx, sheet_name in enumerate(sheet_names):
                logger.info(f"\n--- SHEET {sheet_idx + 1}: '{sheet_name}' ---")

                try:
                    # Load the sheet
                    df = pd.read_excel(excel_path, sheet_name=sheet_name)

                    if df.empty:
                        logger.info(f"  Sheet '{sheet_name}' is empty")
                        continue

                    logger.info(f"  Shape: {len(df)} rows, {len(df.columns)} columns")
                    logger.info(f"  Columns: {list(df.columns)}")

                    # Data types analysis
                    logger.info("  Data Types:")
                    for col, dtype in df.dtypes.items():
                        null_count = df[col].isnull().sum()
                        null_pct = (null_count / len(df)) * 100 if len(df) > 0 else 0
                        logger.info(
                            f"    {col}: {dtype} ({null_count} nulls, {null_pct:.1f}%)"
                        )

                    # Missing data analysis
                    missing_data = df.isnull().sum()
                    total_missing = missing_data.sum()
                    if total_missing > 0:
                        logger.info(f"  Missing values summary:")
                        for col, count in missing_data[missing_data > 0].items():
                            percentage = (count / len(df)) * 100
                            logger.info(f"    {col}: {count} ({percentage:.2f}%)")

                    # Numeric analysis
                    numeric_cols = df.select_dtypes(include=["number"]).columns
                    if len(numeric_cols) > 0:
                        logger.info(f"  Numeric columns ({len(numeric_cols)}):")
                        for col in numeric_cols:
                            stats = df[col].describe()
                            logger.info(
                                f"    {col}: Mean={stats['mean']:.2f}, "
                                f"Std={stats['std']:.2f}, Min={stats['min']:.2f}, Max={stats['max']:.2f}"
                            )

                    # Categorical analysis
                    categorical_cols = df.select_dtypes(include=["object"]).columns
                    if len(categorical_cols) > 0:
                        logger.info(f"  Categorical columns ({len(categorical_cols)}):")
                        for col in categorical_cols:
                            unique_count = df[col].nunique()
                            logger.info(f"    {col}: {unique_count} unique values")

                            if (
                                unique_count <= 10
                            ):  # Show distribution for small categorical sets
                                value_counts = df[col].value_counts().head(5)
                                logger.info(f"      Top values: {dict(value_counts)}")

                    # Date columns detection
                    date_like_cols = []
                    for col in df.columns:
                        if df[col].dtype == "object":
                            # Try to detect date-like strings
                            sample_values = df[col].dropna().head(10)
                            if len(sample_values) > 0:
                                # Simple heuristic for date detection
                                sample_str = str(sample_values.iloc[0])
                                if any(
                                    indicator in sample_str.lower()
                                    for indicator in [
                                        "date",
                                        "time",
                                        "/",
                                        "-",
                                        ":",
                                        "2020",
                                        "2021",
                                        "2022",
                                        "2023",
                                        "2024",
                                        "2025",
                                    ]
                                ):
                                    date_like_cols.append(col)

                    if date_like_cols:
                        logger.info(f"  Potential date columns: {date_like_cols}")

                    # Data quality checks
                    duplicates = df.duplicated().sum()
                    if duplicates > 0:
                        logger.info(f"  Duplicate rows: {duplicates}")

                    # Sample data
                    if len(df) > 0:
                        logger.info("  Sample data (first 2 rows):")
                        for i, row in df.head(2).iterrows():
                            # Limit display to first 8 columns for readability
                            sample_data = dict(list(row.items())[:8])
                            logger.info(f"    Row {i+1}: {sample_data}")
                            if len(df.columns) > 8:
                                logger.info(
                                    f"      ... and {len(df.columns) - 8} more columns"
                                )

                    # Excel-specific checks
                    # Check for merged cells (approximate by looking for repeated values)
                    if len(df) > 1:
                        potential_merged = []
                        for col in df.columns:
                            if df[col].dtype == "object":
                                # Look for consecutive identical values (might indicate merged cells)
                                consecutive_same = 0
                                for i in range(
                                    1, min(len(df), 20)
                                ):  # Check first 20 rows
                                    if (
                                        pd.notna(df[col].iloc[i])
                                        and df[col].iloc[i] == df[col].iloc[i - 1]
                                    ):
                                        consecutive_same += 1
                                    else:
                                        consecutive_same = 0
                                    if (
                                        consecutive_same >= 3
                                    ):  # 3+ consecutive same values
                                        potential_merged.append(col)
                                        break

                        if potential_merged:
                            logger.info(
                                f"  Potential merged cell columns: {potential_merged}"
                            )

                    # Pattern detection for specific data types
                    patterns = []
                    column_names_lower = [col.lower() for col in df.columns]

                    # Financial data patterns
                    if any(
                        keyword in name
                        for name in column_names_lower
                        for keyword in [
                            "price",
                            "cost",
                            "amount",
                            "salary",
                            "revenue",
                            "profit",
                        ]
                    ):
                        patterns.append("Financial data detected")

                    # Personal data patterns
                    if any(
                        keyword in name
                        for name in column_names_lower
                        for keyword in [
                            "name",
                            "first",
                            "last",
                            "email",
                            "phone",
                            "address",
                        ]
                    ):
                        patterns.append("Personal/Contact data detected")

                    # Inventory/Product patterns
                    if any(
                        keyword in name
                        for name in column_names_lower
                        for keyword in [
                            "product",
                            "item",
                            "inventory",
                            "stock",
                            "quantity",
                        ]
                    ):
                        patterns.append("Inventory/Product data detected")

                    # Gaming/NPC patterns
                    if any(
                        keyword in name
                        for name in column_names_lower
                        for keyword in [
                            "npc",
                            "character",
                            "level",
                            "hp",
                            "strength",
                            "class",
                            "role",
                        ]
                    ):
                        patterns.append("Gaming/NPC data detected")

                    if patterns:
                        logger.info(f"  Data patterns: {', '.join(patterns)}")

                except Exception as sheet_error:
                    logger.error(
                        f"  Error analyzing sheet '{sheet_name}': {sheet_error}"
                    )
                    continue

            # Summary across all sheets
            if len(sheet_names) > 1:
                logger.info(f"\n--- WORKBOOK SUMMARY ---")
                total_rows = 0
                total_cols = 0

                for sheet_name in sheet_names:
                    try:
                        df = pd.read_excel(excel_path, sheet_name=sheet_name)
                        total_rows += len(df)
                        total_cols += len(df.columns)
                    except:
                        continue

                logger.info(
                    f"  Total data across all sheets: {total_rows} rows, {total_cols} total columns"
                )
                logger.info(
                    f"  Average per sheet: {total_rows/len(sheet_names):.1f} rows, "
                    f"{total_cols/len(sheet_names):.1f} columns"
                )

            logger.info("\n=== EXCEL ANALYSIS COMPLETE ===")
            speak("Excel analysis complete.")

        except ImportError:
            logger.warning(
                "pandas not available for Excel reading - install pandas and openpyxl for full Excel support"
            )
            logger.info("Excel analysis requires pandas and openpyxl packages")
            speak("Excel analysis requires additional packages.")

        except Exception as read_error:
            logger.error(f"Could not read Excel file: {read_error}")
            logger.info(
                "Note: For .xlsx files, you may need to install openpyxl: pip install openpyxl"
            )
            logger.info(
                "Note: For .xls files, you may need to install xlrd: pip install xlrd"
            )

    except Exception as e:
        logger.error(f"Error in job3: {e}")
        speak("Excel analysis encountered an error.")


def job4(data_file: str):
    """Combined Analysis - Advanced analysis combining multiple data sources."""
    logger.info(f"Starting combined analysis job for: {data_file}")
    speak("Starting combined analysis.")

    try:
        data_path = Path(data_file)
        if not data_path.exists():
            logger.error(f"Data file not found: {data_path}")
            return

        logger.info("Performing combined data analysis...")

        # Try to load and analyze data
        try:
            import pandas as pd

            # Load data based on file type
            if data_path.suffix.lower() == ".csv":
                df = pd.read_csv(data_path)
            elif data_path.suffix.lower() in [".xlsx", ".xls"]:
                df = pd.read_excel(data_path)
            else:
                logger.warning(f"Unsupported file type: {data_path.suffix}")
                return

            logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")

            # Perform comprehensive analysis
            logger.info("=== Data Summary ===")
            logger.info(f"Shape: {df.shape}")
            logger.info(f"Columns: {list(df.columns)}")

            # Check for missing values
            missing_data = df.isnull().sum()
            if missing_data.any():
                logger.info("Missing values found:")
                for col, count in missing_data[missing_data > 0].items():
                    logger.info(f"  {col}: {count} missing")

            # Basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) > 0:
                logger.info("Numeric column statistics:")
                stats = df[numeric_cols].describe()
                for col in numeric_cols:
                    logger.info(
                        f"  {col}: mean={stats.loc['mean', col]:.2f}, std={stats.loc['std', col]:.2f}"
                    )

            # Analyze categorical columns
            categorical_cols = df.select_dtypes(include=["object"]).columns
            if len(categorical_cols) > 0:
                logger.info("Categorical column analysis:")
                for col in categorical_cols:
                    unique_count = df[col].nunique()
                    logger.info(f"  {col}: {unique_count} unique values")
                    if unique_count <= 10:  # Show values if not too many
                        value_counts = df[col].value_counts().head(5)
                        logger.info(f"    Top values: {dict(value_counts)}")

            logger.info("Combined analysis completed successfully")

        except ImportError:
            logger.warning("pandas not available - using basic file analysis")
            # Basic file analysis without pandas
            with open(data_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
                logger.info(f"File contains {len(lines)} lines")
                logger.info(f"File size: {len(content)} characters")

        speak("Combined analysis complete.")

    except Exception as e:
        logger.error(f"Error in job4: {e}")
        speak("Combined analysis encountered an error.")


def job5(npc_file: str):
    """NPC Analysis - Specialized analysis for NPC character data."""
    logger.info(f"Starting NPC analysis job for: {npc_file}")
    speak("Starting NPC analysis.")

    try:
        npc_path = Path(npc_file)
        if not npc_path.exists():
            logger.error(f"NPC file not found: {npc_path}")
            return

        logger.info("Performing NPC character analysis...")

        try:
            import pandas as pd

            # Load NPC data
            if npc_path.suffix.lower() == ".csv":
                df = pd.read_csv(npc_path)
            elif npc_path.suffix.lower() in [".xlsx", ".xls"]:
                df = pd.read_excel(npc_path)
            else:
                logger.warning(
                    f"Unsupported file type for NPC analysis: {npc_path.suffix}"
                )
                return

            logger.info(f"Loaded {len(df)} NPCs")

            # Analyze NPC data structure
            logger.info("=== NPC Analysis ===")
            logger.info(f"Total NPCs: {len(df)}")
            logger.info(f"Data columns: {list(df.columns)}")

            # Look for common NPC fields and analyze them
            role_columns = [
                col
                for col in df.columns
                if any(
                    keyword in col.lower()
                    for keyword in ["role", "class", "job", "position", "rank"]
                )
            ]

            if role_columns:
                for col in role_columns:
                    logger.info(f"Role distribution in {col}:")
                    role_counts = df[col].value_counts()
                    for role, count in role_counts.head(10).items():
                        logger.info(f"  {role}: {count}")

            # Look for skill or attribute columns
            skill_columns = [
                col
                for col in df.columns
                if any(
                    keyword in col.lower()
                    for keyword in ["skill", "attribute", "stat", "ability"]
                )
            ]

            if skill_columns:
                logger.info("Skill/Attribute analysis:")
                for col in skill_columns:
                    if df[col].dtype in ["int64", "float64"]:
                        avg_val = df[col].mean()
                        logger.info(f"  {col}: average = {avg_val:.2f}")

            # Look for name patterns
            name_columns = [col for col in df.columns if "name" in col.lower()]
            if name_columns:
                for col in name_columns:
                    unique_names = df[col].nunique()
                    logger.info(f"Unique values in {col}: {unique_names}")

            # Group analysis if applicable
            group_columns = [
                col
                for col in df.columns
                if any(
                    keyword in col.lower()
                    for keyword in ["group", "team", "squad", "faction", "org"]
                )
            ]

            if group_columns:
                for col in group_columns:
                    logger.info(f"Group distribution in {col}:")
                    group_counts = df[col].value_counts()
                    for group, count in group_counts.head(10).items():
                        logger.info(f"  {group}: {count} members")

            # Look for common NPC columns from the original implementation
            npc_columns = [
                "NPC",
                "NAME",
                "CHARACTER",
                "ROLE",
                "CLASS",
                "POSITION",
                "PRIMUS",
                "SECUNDUS",
            ]
            found_columns = [col for col in npc_columns if col in df.columns]

            if found_columns:
                logger.info(f"Found standard NPC columns: {found_columns}")

                # Basic NPC statistics
                if "NPC" in df.columns:
                    unique_npcs = df["NPC"].nunique()
                    logger.info(f"Unique NPCs: {unique_npcs}")

                if "ROLE" in df.columns:
                    roles = df["ROLE"].value_counts()
                    logger.info(f"Role distribution: {dict(roles.head())}")

            logger.info("NPC analysis completed successfully")

        except ImportError:
            logger.warning("pandas not available - using basic NPC file analysis")
            # Basic analysis without pandas
            import csv

            with open(npc_path, "r", encoding="utf-8") as f:
                if npc_path.suffix.lower() == ".csv":
                    reader = csv.reader(f)
                    rows = list(reader)
                    if rows:
                        logger.info(f"NPC file headers: {rows[0]}")
                        logger.info(f"Total NPC records: {len(rows) - 1}")

        speak("NPC analysis complete.")

    except Exception as e:
        logger.error(f"Error in job5: {e}")
        speak("NPC analysis encountered an error.")


def job6(data_file: str):
    """Job6 - Data Quality Analysis and Validation."""
    logger.info(f"Starting job6 for: {data_file}")
    speak("Starting job 6.")

    try:
        data_path = Path(data_file)
        if not data_path.exists():
            logger.error(f"Data file not found: {data_path}")
            return

        logger.info("Executing data quality analysis...")

        try:
            import pandas as pd

            # Load data based on file type
            if data_path.suffix.lower() == ".csv":
                df = pd.read_csv(data_path)
            elif data_path.suffix.lower() in [".xlsx", ".xls"]:
                df = pd.read_excel(data_path)
            else:
                logger.warning(f"Unsupported file type: {data_path.suffix}")
                return

            logger.info("=== Data Quality Analysis ===")
            logger.info(f"Dataset shape: {df.shape}")

            # Check for missing values
            missing_analysis = df.isnull().sum()
            total_missing = missing_analysis.sum()
            if total_missing > 0:
                logger.info(f"Total missing values: {total_missing}")
                for col, missing_count in missing_analysis[
                    missing_analysis > 0
                ].items():
                    percentage = (missing_count / len(df)) * 100
                    logger.info(f"  {col}: {missing_count} ({percentage:.2f}%)")
            else:
                logger.info("No missing values found")

            # Check for duplicate rows
            duplicates = df.duplicated().sum()
            if duplicates > 0:
                logger.info(f"Duplicate rows found: {duplicates}")
            else:
                logger.info("No duplicate rows found")

            # Data type analysis
            logger.info("Data types:")
            for col, dtype in df.dtypes.items():
                logger.info(f"  {col}: {dtype}")

            # Check for potential data inconsistencies
            for col in df.columns:
                if df[col].dtype == "object":  # String columns
                    unique_count = df[col].nunique()
                    if unique_count < len(df) * 0.1:  # If less than 10% unique values
                        logger.info(
                            f"Categorical column '{col}' has {unique_count} unique values"
                        )
                        top_values = df[col].value_counts().head(5)
                        logger.info(f"  Top values: {dict(top_values)}")

            # Check for outliers in numeric columns
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) > 0:
                logger.info("Outlier analysis (values beyond 3 standard deviations):")
                for col in numeric_cols:
                    mean_val = df[col].mean()
                    std_val = df[col].std()
                    outliers = df[
                        (df[col] < mean_val - 3 * std_val)
                        | (df[col] > mean_val + 3 * std_val)
                    ]
                    if len(outliers) > 0:
                        logger.info(f"  {col}: {len(outliers)} potential outliers")

            logger.info("Data quality analysis completed successfully")

        except ImportError:
            logger.warning("pandas not available - using basic file validation")
            # Basic file validation without pandas
            file_size = data_path.stat().st_size
            logger.info(f"File size: {file_size} bytes")

            if data_path.suffix.lower() == ".csv":
                import csv

                with open(data_path, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                    logger.info(f"CSV has {len(rows)} rows")
                    if rows:
                        logger.info(f"Headers: {rows[0]}")

        speak("Job 6 complete.")

    except Exception as e:
        logger.error(f"Error in job6: {e}")
        speak("Job 6 encountered an error.")


def job8(data_file: str):
    """Job8 - Data Export and Reporting."""
    logger.info(f"Starting job8 for: {data_file}")
    speak("Starting job 8.")

    try:
        data_path = Path(data_file)
        if not data_path.exists():
            logger.error(f"Data file not found: {data_path}")
            return

        logger.info("Executing data export and reporting...")

        try:
            import pandas as pd

            # Load data based on file type
            if data_path.suffix.lower() == ".csv":
                df = pd.read_csv(data_path)
            elif data_path.suffix.lower() in [".xlsx", ".xls"]:
                df = pd.read_excel(data_path)
            else:
                logger.warning(f"Unsupported file type: {data_path.suffix}")
                return

            logger.info("=== Data Export and Reporting ===")
            logger.info(
                f"Processing dataset with {len(df)} rows and {len(df.columns)} columns"
            )

            # Create output directory if it doesn't exist
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)

            # Generate comprehensive data report
            report_file = output_dir / f"data_report_{data_path.stem}.txt"
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(f"Data Analysis Report for {data_path.name}\n")
                f.write("=" * 50 + "\n\n")
                f.write(
                    f"Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )

                f.write(f"Dataset Information:\n")
                f.write(f"- File: {data_path.name}\n")
                f.write(f"- Shape: {df.shape}\n")
                f.write(f"- Columns: {', '.join(df.columns)}\n\n")

                f.write("Data Types:\n")
                for col, dtype in df.dtypes.items():
                    f.write(f"- {col}: {dtype}\n")
                f.write("\n")

                # Missing values summary
                missing_data = df.isnull().sum()
                if missing_data.any():
                    f.write("Missing Values:\n")
                    for col, count in missing_data[missing_data > 0].items():
                        percentage = (count / len(df)) * 100
                        f.write(f"- {col}: {count} ({percentage:.2f}%)\n")
                else:
                    f.write("Missing Values: None\n")
                f.write("\n")

                # Summary statistics for numeric columns
                numeric_cols = df.select_dtypes(include=["number"]).columns
                if len(numeric_cols) > 0:
                    f.write("Numeric Column Statistics:\n")
                    stats = df[numeric_cols].describe()
                    f.write(str(stats))
                    f.write("\n\n")

                # Categorical columns summary
                categorical_cols = df.select_dtypes(include=["object"]).columns
                if len(categorical_cols) > 0:
                    f.write("Categorical Columns:\n")
                    for col in categorical_cols:
                        unique_count = df[col].nunique()
                        f.write(f"- {col}: {unique_count} unique values\n")
                        if unique_count <= 10:
                            top_values = df[col].value_counts().head(5)
                            f.write(f"  Top values: {dict(top_values)}\n")
                    f.write("\n")

            logger.info(f"Data report saved to: {report_file}")

            # Export processed data in multiple formats
            if not df.empty:
                # Export to CSV (cleaned version)
                csv_export = output_dir / f"processed_{data_path.stem}.csv"
                df.to_csv(csv_export, index=False)
                logger.info(f"Processed data exported to: {csv_export}")

                # Export to JSON for API use
                json_export = output_dir / f"processed_{data_path.stem}.json"
                df.to_json(json_export, orient="records", indent=2)
                logger.info(f"JSON export created: {json_export}")

                # Create summary statistics file
                summary_file = output_dir / f"summary_{data_path.stem}.json"
                summary_data = {
                    "file_name": data_path.name,
                    "total_rows": len(df),
                    "total_columns": len(df.columns),
                    "columns": list(df.columns),
                    "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
                    "missing_values": {
                        col: int(count)
                        for col, count in df.isnull().sum().items()
                        if count > 0
                    },
                    "generated_on": pd.Timestamp.now().isoformat(),
                }

                with open(summary_file, "w", encoding="utf-8") as f:
                    json.dump(summary_data, f, indent=2)
                logger.info(f"Summary data saved to: {summary_file}")

            logger.info("Data export and reporting completed successfully")

        except ImportError:
            logger.warning("pandas not available - using basic export")
            # Basic export without pandas
            if data_path.suffix.lower() == ".csv":
                import csv
                import shutil

                output_dir = Path("output")
                output_dir.mkdir(exist_ok=True)
                backup_file = output_dir / f"backup_{data_path.name}"
                shutil.copy2(data_path, backup_file)
                logger.info(f"Basic backup created: {backup_file}")

        speak("Job 8 complete.")

    except Exception as e:
        logger.error(f"Error in job8: {e}")
        speak("Job 8 encountered an error.")


def display_npc_groups(npc_file: str):
    """Display NPC groups organized by roles or other criteria."""
    logger.info(f"Starting NPC groups display for: {npc_file}")
    speak("Displaying NPC groups.")

    try:
        npc_path = Path(npc_file)
        if not npc_path.exists():
            logger.error(f"NPC file not found: {npc_path}")
            return

        try:
            import pandas as pd

            df = pd.read_csv(npc_path)

            logger.info("Organizing NPCs into groups...")

            # Group by role if available
            if "ROLE" in df.columns:
                groups = df.groupby("ROLE")
                logger.info(f"NPC Groups by Role:")
                for role, group in groups:
                    npcs = (
                        group["NPC"].tolist()
                        if "NPC" in group.columns
                        else group.index.tolist()
                    )
                    logger.info(
                        f"  {role}: {len(npcs)} members - {', '.join(npcs[:5])}"
                    )
                    if len(npcs) > 5:
                        logger.info(f"    ... and {len(npcs) - 5} more")

            # Group by class if available
            elif "CLASS" in df.columns:
                groups = df.groupby("CLASS")
                logger.info(f"NPC Groups by Class:")
                for cls, group in groups:
                    npcs = (
                        group["NPC"].tolist()
                        if "NPC" in group.columns
                        else group.index.tolist()
                    )
                    logger.info(f"  {cls}: {len(npcs)} members - {', '.join(npcs[:3])}")

            else:
                logger.info("No suitable grouping columns found (ROLE, CLASS)")
                logger.info(f"Available columns: {list(df.columns)}")

            logger.info("NPC groups display completed")
            speak("NPC groups display complete.")

        except ImportError:
            logger.warning("pandas not available for NPC groups display")

    except Exception as e:
        logger.error(f"Error in display_npc_groups: {e}")
        speak("NPC groups display encountered an error.")


# endregion


# region Main Execution
def main() -> int:
    """
    Main function to run the data processing script.

    Configures logging, creates necessary directories, and runs a series of predefined jobs.
    Handles errors during job execution and logs them.

    Returns:
        0 if processing completes successfully, 1 if a critical error occurs.
    """
    # Configure file logging (console logging is already configured at module level)
    file_handler = logging.FileHandler("output.txt", mode="w")
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)

    # Add file handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

    try:
        # Fix linting errors first
        fix_lint_errors()

        # Example of using the speak function
        speak("Crew system initialization sequence started.")

        # Set up Git repository
        # setup_git_repository() # Removed as it's not defined

        # Check for unstaged files and handle them automatically
        # if check_git_status(): # Commented out as it's not defined
        #     logger.info("Auto-fixing unstaged files...")
        #     fix_git_unstaged_files() # Commented out as it's not defined

        # Ensure required directories exist
        for directory in [INPUT_DIR, OUTPUT_DIR, DATA_DIR]:
            directory.mkdir(exist_ok=True)

        # Define jobs to run
        jobs = [
            ("Image Processing", job1),
            ("CSV Analysis", lambda: job2("data/npcs.csv")),
            ("Excel Analysis", lambda: job3("data/npcs.xls")),
            ("Combined Analysis", lambda: job4("data/npcs.xls")),
            ("NPC Analysis", lambda: job5("data/npcs.csv")),
            ("Job6", lambda: job6("data/npcs.csv")),
            ("Job8", lambda: job8("data/npcs.csv")),
            ("NPC Groups Display", lambda: display_npc_groups("data/npcs.csv")),
        ]

        logger.info("=== Starting Data Processing ===")

        # Run each job once
        for job_name, job_func in jobs:
            try:
                logger.info(f"\n--- Running {job_name} ---")
                job_func()
                spacer()
            except FileNotFoundError as fe:
                logger.error(f"Error in {job_name}: File not found - {str(fe)}")
            except Exception as e:
                logger.error(f"Error in {job_name}: {str(e)}")

        logger.info("=== Processing Complete ===\n")
        return 0

    except Exception as e:
        logger.error(f"Critical error in main execution: {str(e)}")
        return 1
    finally:
        # Remove the file handler to clean up
        root_logger.removeHandler(file_handler)
        file_handler.close()  # Ensure file handler is closed


if __name__ == "__main__":
    current_script_path = Path(__file__).resolve()
    project_root = current_script_path.parent
    log_file_path = project_root / "output.txt"

    # Configure logging for the main execution
    root_logger = logging.getLogger()  # Get the root logger

    # Clear any handlers already configured by the top-level basicConfig if this script is run directly
    # This ensures that we don't get duplicate messages if basicConfig was already called.
    if root_logger.hasHandlers():
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            handler.close()

    # Add new handlers for file and console
    # File handler for output.txt
    try:
        file_handler = logging.FileHandler(log_file_path, mode="w", encoding="utf-8")
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)  # Capture debug messages in file
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(
            f"Critical Error: Could not set up file logger for {log_file_path}. Error: {e}"
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)  # Show INFO and above on console
    root_logger.addHandler(console_handler)

    root_logger.setLevel(logging.DEBUG)  # Set root logger to lowest level of handlers

    logger.info("Crew.py script started. Logging to console and output.txt")
    speak("Crew script initialized.")

    project_dir = project_root
    backup_parent_dir = project_dir.parent / f"{project_dir.name}_Backups"

    # Add backup pause option
    logger.info("--- Backup Control ---")
    backup_response = (
        input("Do you want to proceed with backup? (y/n): ").strip().lower()
    )
    if backup_response not in ["y", "yes"]:
        logger.info("Backup skipped by user request.")
        speak("Backup skipped.")
    else:
        logger.info("--- Task: Project Backup ---")
        logger.info("--- Task: Project Backup ---")
        if backup_project(project_dir, backup_parent_dir):
            logger.info("Project backup task completed successfully.")
        else:
            logger.error("Project backup task failed.")

    logger.info("--- Task: Generate Project Summary ---")
    summary_file = project_dir / "project_summary.md"
    if generate_project_summary(project_dir, summary_file):
        logger.info("Project summary generation completed successfully.")
    else:
        logger.error("Project summary generation failed.")

    logger.info("--- Task: Generate Help File ---")
    help_file_path = project_dir / "HELP.txt"
    if generate_help_file(str(help_file_path)):
        logger.info("Help file generation completed successfully.")
    else:
        logger.error("Help file generation failed.")

    logger.info("--- Task: Auto Fix All Issues ---")
    # SAFETY: Set to False to skip potentially slow linting operations
    ENABLE_LINTING = True  # Change to False to skip linting entirely

    if ENABLE_LINTING:
        if (project_dir / ".git").is_dir():
            # Add GitHub push prompt
            logger.info("--- GitHub Push Control ---")
            github_response = (
                input("Do you want to proceed with GitHub push? (y/n): ")
                .strip()
                .lower()
            )
            if github_response not in ["y", "yes"]:
                logger.info("GitHub push skipped by user request.")
                speak("GitHub push skipped.")
                # Still run local linting without GitHub push
                logger.info("Running local linters/formatters only...")
                if fix_lint_errors(project_dir):
                    logger.info("Local linting/formatting completed.")
                else:
                    logger.error("Local linting/formatting failed.")
            else:
                auto_fix_all_issues(project_dir)
                logger.info("Auto-fix and Git push task processed.")
        else:
            logger.warning(
                f"'{project_dir}' is not a Git repository. Skipping Git operations in auto_fix_all_issues."
            )
            speak("Project is not a Git repository. Skipping automated Git push.")
            logger.info("Attempting to run local linters/formatters...")
            if fix_lint_errors(project_dir):
                logger.info("Local linting/formatting completed.")
            else:
                logger.error("Local linting/formatting failed.")
    else:
        logger.info("Linting disabled for safety. Skipping auto-fix operations.")
        speak("Skipping code formatting for safety.")

    # Optional: Run original job tasks
    # logger.info("--- Task: Running Original Jobs (job1, job2, etc.) ---")
    # try:
    #     job1()
    #     job2()
    #     # job3(), job4(), job5() - ensure they are robust or handle errors
    #     logger.info("Original jobs completed.")
    # except Exception as e:
    #     logger.error(f"Error during original job execution: {e}", exc_info=True)
    #     speak("An error occurred while running scheduled jobs.")

    logger.info("--- Task: Launch GUI ---")
    gui_script_path = project_dir / "gui.py"
    if gui_script_path.is_file():
        logger.info(f"Attempting to launch GUI: {gui_script_path}")
        speak("Attempting to launch the graphical user interface.")
        try:
            # Temporarily show output to debug GUI issues
            subprocess.Popen(
                [sys.executable, str(gui_script_path)],
                cwd=project_dir,
                # stdout=subprocess.DEVNULL,
                # stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            logger.info("GUI launch command issued.")
        except Exception as e:
            logger.error(f"Failed to launch GUI: {e}", exc_info=True)
            speak("Failed to launch the graphical user interface.")
    else:
        logger.info("gui.py not found, skipping GUI launch.")

    logger.info("Crew.py script finished.")
    speak("Crew script execution complete.")
