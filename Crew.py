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
import json
import logging
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

import ijson
import pandas as pd
from PIL import Image, ImageDraw

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Conditional import - moved after logging setup
try:
    from mcp_service import CustomEncoder, get_mcp_context_for_npcs
except ImportError:
    logger.warning("mcp_service module not found - MCP functionality disabled")

    def get_mcp_context_for_npcs(df):
        return {"error": "mcp_service not available"}

    class CustomEncoder(json.JSONEncoder):
        pass


# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

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


# region Main Processing Tasks
# Image Processing
def job1() -> None:
    """
    Processes images by overlaying grids and saving them.

    Reads image filenames from `IMAGE_FILES`, applies a grid overlay
    with specified `GRID_SIZES`, and saves the processed images to the `OUTPUT_DIR`.
    """
    output_dir = os.path.join(os.path.dirname(__file__), OUTPUT_DIR)
    os.makedirs(output_dir, exist_ok=True)

    # Use the imported constants
    files = [os.path.join(INPUT_DIR, f) for f in IMAGE_FILES]
    names = [f"Cars{i+1}.png" for i in range(len(IMAGE_FILES))]

    # Process each image
    for _, (input_image, output_name, grid_size) in enumerate(  # Replaced i with _
        zip(files, names, GRID_SIZES)
    ):
        try:
            output_path = os.path.join(output_dir, output_name)
            grid_image = overlayGrid(
                input_image, grid_color=DEFAULT_GRID_COLOR, grid_size=grid_size
            )
            grid_image.save(output_path)
            print(f"Image with grid saved as {output_path}")
        except Exception as e:
            print(f"Error processing {input_image}: {e}")
    print("\n=== Process images complete ===\n")
    print("job1 complete.")


# CSV
def job2(filename: str = "data/npcs.csv") -> None:
    """
    Reads and analyzes a CSV file using pandas.

    Performs basic data exploration including shape, columns, head,
    and statistical summary. Also demonstrates position analysis,
    data filtering, and grouped analysis if a "POSITION" column exists.
    Finally, it generates and prints MCP context for the loaded data.

    Args:
        filename: Path to the CSV file (default is "data/npcs.csv").
    """
    logger.info("\n--- Running CSV Analysis ---")
    try:
        # Load the CSV file into a pandas DataFrame
        data_pandas_df = pd.read_csv(filename)

        # Display basic information using logger
        logger.info("\n=== Data Overview ===")
        logger.info(f"Shape: {data_pandas_df.shape}")
        logger.info(f"Columns: {data_pandas_df.columns.tolist()}")
        logger.info("\n=== First 5 rows ===")
        logger.info(f"\n{data_pandas_df.head().to_string()}")
        logger.info("\n=== Numerical Statistics ===")
        logger.info(f"\n{data_pandas_df.describe().to_string()}")
        # logger.info(data_pandas_df.to_string()) # Log entire dataframe if needed, can be verbose

        if "ROLE" in data_pandas_df.columns:
            logger.info("\n=== Role Analysis ===")
            role_counts = data_pandas_df["ROLE"].value_counts()
            logger.info("Role distribution:")
            logger.info(f"\n{role_counts.to_string()}")

            # Data filtering example
            logger.info("\n=== Filtered Data ===")
            filtered_data = data_pandas_df[
                data_pandas_df["ROLE"].str.contains("Captain", na=False)
            ]
            logger.info("Captains in dataset:")
            columns_to_display = ["ROLE"]
            if "TAG" in data_pandas_df.columns:
                columns_to_display.append("TAG")

            if not filtered_data.empty:
                logger.info(f"\n{filtered_data[columns_to_display].to_string()}")
            else:
                logger.info("No Captains found matching criteria.")

            # Group by operations
            logger.info("\n=== Grouped Analysis ===")
            grouped_data = data_pandas_df.groupby("ROLE").size()
            logger.info("Counts by role:")
            logger.info(f"\n{grouped_data.to_string()}")
            role_percentage = (grouped_data / grouped_data.sum()) * 100
            logger.info("\n=== Role Percentage ===")
            logger.info(f"\n{role_percentage.to_string()}")
        else:
            logger.warning(
                "\n=== 'ROLE' column not found in CSV. Skipping related analysis. ==="
            )

        # Generate and print MCP context
        logger.info("\n=== MCP Context for NPCs ===")
        mcp_context = get_mcp_context_for_npcs(data_pandas_df)
        # Still print JSON to console for direct viewing, but also log it for record
        mcp_json_output = json.dumps(mcp_context, indent=4, cls=CustomEncoder)
        print(
            mcp_json_output
        )  # Keep direct print for this specific output as it's a primary artifact
        logger.info(f"MCP JSON Output:\n{mcp_json_output}")

        logger.info("\n=== Read CSV file complete ===")
        logger.info("\njob2 CSV complete.")
        logger.info("\n----------------------------------------")

    except FileNotFoundError:
        logger.error(f"Error: The file {filename} was not found.")
    except pd.errors.EmptyDataError:
        logger.error(f"Error: The CSV file {filename} is empty.")
    except Exception as e:
        logger.error(f"Error in CSV Analysis for {filename}: {e}")


# XLS
def job3(filename: str = "data/npcs.xls") -> None:  # Added return type hint
    """
    Reads and displays contents from an Excel file.

    Specifically looks for and analyzes an "npcs" column if present.

    Args:
        filename: Path to the Excel file (default is "data/npcs.xls").
    """
    logger.info(f"--- Running Excel Analysis for {filename} ---")
    # Excel file reading
    excel_file = filename
    try:
        df = read_excel(excel_file, sheet_name=0)  # Specify the sheet name or index
        if df is not None and not df.empty:
            logger.info("\nExcel Data:")
            logger.info(f"\n{df.head().to_string()}")
            logger.info(f"\nColumns: {df.columns.tolist()}")
            if "npcs" in df.columns:
                logger.info("\n=== npcs Column Analysis ===")
                logger.info(f"Value Counts:\n{df['npcs'].value_counts().to_string()}")
                logger.info(f"\nUnique Values: {df['npcs'].unique().tolist()}")
            else:
                logger.warning("'npcs' column not found in the Excel file.")
        elif df is not None and df.empty:
            logger.info("Excel file is empty.")
        else:
            # read_excel already logs FileNotFoundError
            pass  # Error already logged by read_excel or it returned None

    except Exception as e:  # Catch other potential errors during analysis
        logger.error(f"Error during Excel file analysis of '{excel_file}': {e}")
    logger.info("\n=== Excel file reading complete ===")
    logger.info("job3 XLS complete.")


# show column analysis
def job4(filename: str = "data/npcs.csv") -> None:  # Added return type hint
    """
    Processes and analyzes data from a given file (CSV or Excel).

    Reads the file and then calls `analyze_data` to perform basic analysis.

    Args:
        filename: Path to the data file (default is "data/npcs.csv").
    """
    try:
        # Read data files
        print(filename)
        df = read_structured_file(filename)  # Read file once
        # Analyze data
        analyze_data(df)  # Analyze once
        # excel_df = read_file(filename) # Removed redundant read
        # analyze_data(excel_df) # Removed redundant analysis
    except Exception as e:
        print(f"Error in job4: {e}")
    print("\n=== NPC Analysis complete ===\n")  # Corrected f-string
    print("job4 show columns complete.")
    print("\n=== CSV file analysis complete ===\n")


# save csv columns
def job5(filename: str = "data/npcs.csv") -> None:  # Added return type hint
    """
    Displays and saves CSV data, creating separate CSVs for unique values in each column.

    Logs information about the "NPC", "ROLE", and "PRIMUS" columns.
    Then, for each column in the input CSV, it logs unique values and writes
    these unique values to a new CSV file named 'data/<column_name>.csv'.

    Args:
        filename: Path to the input CSV file (default is "data/npcs.csv").
    """
    data_pandas = pd.read_csv(filename)
    logger.info("\n=== SkyRig Cast ===\n")
    logger.info(data_pandas[["NPC", "ROLE"]])
    logger.info("\n=== <NPC> <ROLE> <PRIMUS> ===")
    logger.info(data_pandas[["NPC", "ROLE", "PRIMUS"]])

    cols = data_pandas.columns.tolist()
    for col in cols:
        logger.info(f"{data_pandas[col].unique()}")
        fname = f"data/{col}.csv"
        # The above code is opening a file named `fname` in write mode and
        # assigning it to the variable `f`. This allows the program to write
        # data to the file. The `with` statement is used to ensure that the
        # file is properly closed after the block of code is executed, even
        # if an error occurs.

        with open(fname, "w") as f:
            name = col
            name = name.upper()

            f.write(f"{name}\n")
            for row in data_pandas.index:
                logger.info(f"{data_pandas.at[row, col]}")
                f.write(f"{data_pandas.at[row, col]}\n")
            logger.info("")  # Removed whitespace before : (was f"")
            # print(f"File {fname} created successfully.")
    print("\n=== SkyRig Cast Complete ===\n")
    print("job5 save csv complete.")  # Changed from job1 to job5


# show cols
def job6(filename: str = "data/npcs.csv") -> None:  # Added return type hint
    """
    Reads a CSV file and prints its column names.

    Args:
        filename: Path to the CSV file (default is "data/npcs.csv").
    """
    data_pandas = pd.read_csv(filename)
    cols = data_pandas.columns.tolist()
    print(cols)
    print("\n=== SkyRig Roles Complete ===\n")
    print("job6 complete.")  # Changed from job1 to job5


# save
def job7(filename: str = "data/npcs.csv") -> None:  # Added return type hint
    """
    Placeholder job function. Currently only prints completion messages.

    Args:
        filename: Path to a CSV file (default is "data/npcs.csv"), though not used.
    """
    print("\n=== SkyRig Complete ===\n")
    print("job7 complete.")  # Changed from job1 to job5


# save
def job8(filename: str = "data/npcs.csv") -> None:  # Added return type hint
    """
    Displays NPC groups and splits the CSV into groups.

    Calls `display_npc_groups` and `split_csv_groups` using the provided filename.

    Args:
        filename: Path to the CSV file (default is "data/npcs.csv").
    """
    display_npc_groups(filename)
    split_csv_groups(filename)
    print("job8 complete.")


# close
def Ending(filename: str = "data/npcs.csv") -> None:  # Added return type hint
    """
    Prints a series of completion messages.

    Args:
        filename: Path to a CSV file (default is "data/npcs.csv"), though not used.
    """
    print("\n=== Role Analysis Complete ===")
    print("\n=== CSV File Analysis Complete ===")
    print("\n=== Excel File Analysis Complete ===")
    print("\n=== Data Analysis Complete ===")
    print("\n=== All jobs have been commented out ===")


# endregion


# region General Utilities
def spacer() -> None:
    """
    Prints a separator line to the console for better readability of output.
    """
    print("\n" + "-" * 40 + "\n")


def analyze_data(df: pd.DataFrame) -> None:  # Added return type hint
    """
    Performs and prints a basic analysis of a pandas DataFrame.

    If the DataFrame is None, the function returns early.
    Otherwise, it prints the shape, first 5 rows, column names, and data types.

    Args:
        df: The pandas DataFrame to analyze.
    """
    if df is None:
        return

    print("\nData Overview:")
    print("-" * 40)
    print(f"Shape: {df.shape}")
    print("\nFirst 5 rows:")
    print(df.head())
    print("\nColumns:", df.columns.tolist())
    print("\nData Types:")
    print(df.dtypes)


def display_ascii_characters() -> None:  # Added return type hint
    """
    Displays ASCII characters and their corresponding integer values (0-255).
    """
    for i in range(256):
        ascii_char = chr(i)
        # if 32 >= i <= 126:
        print(f"{i}: {ascii_char}")


# Call the function to display the ASCII characters
# display_ascii_characters()

# endregion


# region Geometric and Color Calculations
def hex_to_rgb(hex_color: str) -> tuple:
    """
    Converts a hex color string to an RGB tuple.

    Args:
        hex_color: Hex color string (e.g., '#FF5733').
                   The '#' prefix is optional.

    Returns:
        tuple: RGB values as a tuple (R, G, B).
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: tuple) -> str:
    """
    Converts an RGB tuple to a hex color string.

    Args:
        rgb: Tuple of RGB values (R, G, B), where R, G, B are integers.

    Returns:
        str: Hex color string (e.g., '#FF5733').
    """
    return "#" + "".join(f"{int(c):02X}" for c in rgb)


# TODO: Add more functions for hex calculations


def calculate_hexagon_points(*args, **kwargs) -> List[Tuple[int, int]]:
    """
    Calculates the 6 vertex points of a regular hexagon.

    Can be called with:
    1. calculate_hexagon_points(center, radius) - legacy mode
    2. calculate_hexagon_points(height, center_x=0, center_y=0) - new mode

    Args:
        *args: Variable arguments to support both calling styles
        **kwargs: Keyword arguments for new style

    Returns:
        A list of 6 (x, y) tuples representing the vertices of the hexagon.
        Returns an empty list if the height/radius is not positive.
    """
    # Handle legacy call style: calculate_hexagon_points(center, radius)
    if len(args) == 2 and isinstance(args[0], tuple):
        center, radius = args
        center_x, center_y = center
        height = radius * 2  # Convert radius to height
    # Handle new call style: calculate_hexagon_points(height, center_x=0, center_y=0)
    elif len(args) >= 1:
        height = args[0]
        center_x = args[1] if len(args) > 1 else kwargs.get("center_x", 0)
        center_y = args[2] if len(args) > 2 else kwargs.get("center_y", 0)
    else:
        return []

    if height <= 0:
        return []

    # Side length 's' of the hexagon.
    # For a hexagon with height H (distance between parallel sides), s = H / sqrt(3)
    s = height / math.sqrt(3)

    points = [
        (center_x + s / 2, center_y + height / 2),  # Top-right
        (center_x - s / 2, center_y + height / 2),  # Top-left
        (center_x - s, center_y),  # Middle-left
        (center_x - s / 2, center_y - height / 2),  # Bottom-left
        (center_x + s / 2, center_y - height / 2),  # Bottom-right
        (center_x + s, center_y),  # Middle-right
    ]

    # Round coordinates to the nearest integer
    int_points = [(round(p[0]), round(p[1])) for p in points]
    return int_points


# TODO: Calculate point positions of 6 points of a hexagon by supplying the height only as integer.  Return int values for point coordinates only.


# endregion


# region Advanced Data Processing
def split_csv_groups(filename: str = "data/npcs.csv") -> dict:
    """
    Splits a CSV file into multiple DataFrames based on double blank line separators.

    Each group of rows separated by two consecutive blank lines in the CSV
    is treated as a separate DataFrame. Handles cases where data rows might
    have different column counts than the header by padding or truncating.

    Args:
        filename: Path to the CSV file (default is "data/npcs.csv").

    Returns:
        A dictionary where keys are group indices (0-based) and values are
        pandas DataFrames representing each group. Returns an empty dictionary
        if an error occurs or no groups are found.
    """
    groups = {}
    current_group = []
    group_index = 0
    blank_line_count = 0

    try:
        with open(filename, "r") as file:
            header = file.readline().strip().split(",")
            header_count = len(header)

            for line in file:
                if not line.strip():  # Found a blank line
                    blank_line_count += 1
                    if blank_line_count == 2:  # Two consecutive blank lines
                        if current_group:  # If we have rows in current group
                            # Ensure all rows have the same number of columns as header
                            normalized_group = []
                            for row in current_group:
                                # Pad or truncate row to match header length
                                if len(row) < header_count:
                                    row.extend([""] * (header_count - len(row)))
                                elif len(row) > header_count:
                                    row = row[:header_count]
                                normalized_group.append(row)

                            df = pd.DataFrame(normalized_group, columns=header)
                            df = df.dropna(how="all")  # Remove completely empty rows
                            groups[group_index] = df
                            group_index += 1
                            current_group = []
                        blank_line_count = 0
                else:
                    blank_line_count = 0
                    row = line.strip().split(",")
                    if any(cell.strip() for cell in row):  # Skip empty rows
                        current_group.append(row)

            # Don't forget the last group
            if current_group:
                # Apply same normalization to last group
                normalized_group = []
                for row in current_group:
                    if len(row) < header_count:
                        row.extend([""] * (header_count - len(row)))
                    elif len(row) > header_count:
                        row = row[:header_count]
                    normalized_group.append(row)

                df = pd.DataFrame(normalized_group, columns=header)
                df = df.dropna(how="all")
                groups[group_index] = df
        # print(current_group) # Removed debug print
        return groups
    except Exception as e:
        logger.error(f"Error splitting CSV into groups: {e}")
        return {}


def display_npc_groups(
    filename: str = "data/npcs.csv",
) -> None:  # Added return type hint
    """
    Displays NPC groups from a CSV file.

    Uses `split_csv_groups` to get the groups and then prints selected columns
    ("NPC", "ROLE", "COMPANY") for each group.

    Args:
        filename: Path to the CSV file (default is "data/npcs.csv").
    """
    groups = split_csv_groups(filename)

    if not groups:
        print("No groups found in the CSV file.")
        return

    for idx, group_df in groups.items():
        print(f"\n=== Group {idx + 1} ===")
        print(group_df[["NPC", "ROLE", "COMPANY"]].to_string(index=False))
        print("\n" + "-" * 40)


# endregion


# region JSON
def load_large_json_file(file_path: str) -> None:  # Added type hint and return type
    """
    Loads and prints objects from a large JSON file using ijson.

    This function is suitable for JSON files that are too large to be loaded
    into memory at once. It iterates through the items at the top level
    of the JSON structure.

    Args:
        file_path: The path to the JSON file.
    """
    try:
        with open(file_path, "r") as file:
            objects = ijson.items(file, "item")
            for obj in objects:
                print(obj)
    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
    except ijson.JSONError:
        print(f"Error: The file {file_path} is not a valid JSON file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# Example usage
# file_path = 'large_data.json'
# load_large_json_file(file_path)

# endregion


# region Main Execution
def start_gui() -> None:
    """
    Starts the GUI application by running 'gui.py' as a subprocess.

    Prints the output and errors (if any) from the subprocess.
    """
    # Define the command to be executed
    command = ["python", "gui.py"]
    # Execute the command
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        # Print the output
        print("Output:", result.stdout)
        print("Error (if any):", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        print("Error output:", e.stderr)


def fix_lint_errors() -> bool:
    """Fix common linting errors automatically."""
    try:
        project_dir = Path(__file__).parent

        # Run isort to fix import order
        result = subprocess.run(
            ["python", "-m", "isort", "."],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )

        if result.returncode == 0:
            logger.info("Import order fixed with isort")
        else:
            logger.warning(f"isort failed: {result.stderr}")

        return True

    except Exception as e:
        logger.error(f"Error fixing lint errors: {e}")
        return False


def get_version() -> str:
    """Return the current version of the application."""
    return "1.0.2"


def get_project_info() -> dict:
    """Return project information."""
    return {
        "name": "NPCs Data Processing Tool",
        "version": get_version(),
        "author": "Mark Ferguson",
        "description": "Image processing, data analysis, and file manipulation tool",
        "repository": "https://github.com/Maggot4703/Crew",
    }


def fix_git_unstaged_files() -> bool:
    """Fix unstaged files by staging and committing them."""
    try:
        project_dir = Path(__file__).parent

        # Check for unstaged files
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )

        if result.returncode != 0:
            logger.warning("Git not available or not a Git repository")
            return False

        unstaged_files = [
            line
            for line in result.stdout.strip().split("\n")
            if line and (line.startswith(" M") or line.startswith("??"))
        ]

        if not unstaged_files:
            logger.info("No unstaged files found")
            return True

        logger.info(f"Found {len(unstaged_files)} unstaged files")

        # Stage all files
        result = subprocess.run(
            ["git", "add", "."],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )

        if result.returncode != 0:
            logger.error(f"Failed to stage files: {result.stderr}")
            return False

        # Commit with descriptive message
        commit_message = (
            f"Fix unstaged files and update to v{get_version()}\n\n"
            "- Fixed import order (E402 error)\n"
            "- Improved Git handling\n"
            "- Enhanced error handling"
        )

        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )

        if result.returncode == 0:
            logger.info("Successfully staged and committed unstaged files")
            return True
        else:
            logger.error(f"Failed to commit: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error fixing unstaged files: {e}")
        return False


def check_git_status() -> bool:
    """Check and display current Git status. Returns True if there are unstaged files."""
    try:
        project_dir = Path(__file__).parent
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        if result.returncode == 0:
            if result.stdout.strip():
                logger.warning("Git status: Unstaged changes detected")
                logger.info(f"Unstaged files:\n{result.stdout}")
                return True  # Has unstaged files
            else:
                logger.info("Git status: Working directory clean")
                return False  # No unstaged files
        else:
            logger.warning("Git not initialized or not a Git repository")
            return False
    except Exception as e:
        logger.warning(f"Could not check Git status: {e}")
        return False


def setup_git_repository() -> None:
    """Initialize Git repository and set up remote if needed."""
    try:
        project_dir = Path(__file__).parent

        # Initialize git if not already done
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        if result.returncode != 0:
            logger.info("Initializing Git repository...")
            subprocess.run(["git", "init"], cwd=project_dir)
            subprocess.run(["git", "branch", "-M", "main"], cwd=project_dir)

        # Check if remote exists
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        if result.returncode != 0:
            logger.info("Setting up remote repository...")
            repo_url = get_project_info()["repository"]
            subprocess.run(
                ["git", "remote", "add", "origin", f"{repo_url}.git"], cwd=project_dir
            )

    except Exception as e:
        logger.error(f"Error setting up Git repository: {e}")


def check_unstaged_files() -> bool:
    """Check for unstaged files and return True if any are found."""
    try:
        project_dir = Path(__file__).parent
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )

        if result.returncode != 0:
            logger.warning("Git not available")
            return False

        unstaged_lines = result.stdout.strip().split("\n")
        unstaged_files = [
            line
            for line in unstaged_lines
            if line
            and (
                line.startswith(" M") or line.startswith("??") or line.startswith("M ")
            )
        ]

        if unstaged_files:
            logger.warning(f"Found {len(unstaged_files)} unstaged files:")
            for file_line in unstaged_files:
                logger.warning(f"  {file_line}")
            return True
        else:
            logger.info("No unstaged files found")
            return False

    except Exception as e:
        logger.error(f"Error checking unstaged files: {e}")
        return False


def auto_stage_and_commit() -> bool:
    """Automatically stage and commit unstaged files."""
    try:
        project_dir = Path(__file__).parent

        # Stage all files
        result = subprocess.run(
            ["git", "add", "."],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )

        if result.returncode != 0:
            logger.error(f"Failed to stage files: {result.stderr}")
            return False

        # Commit with automated message
        commit_message = f"Auto-commit: Fix linting and unstaged files v{get_version()}"
        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )

        if result.returncode == 0:
            logger.info("Successfully committed unstaged files")
            return True
        else:
            logger.warning("No changes to commit or commit failed")
            return False

    except Exception as e:
        logger.error(f"Error auto-committing: {e}")
        return False


def diagnose_git_issues() -> dict:
    """Diagnose common Git issues that prevent pushing."""
    issues = {
        "git_initialized": False,
        "remote_configured": False,
        "branch_exists": False,
        "authentication_ready": False,
        "upstream_set": False,
        "conflicts": False,
    }

    try:
        project_dir = Path(__file__).parent

        # Check if Git is initialized
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        issues["git_initialized"] = result.returncode == 0

        # Check if remote is configured
        result = subprocess.run(
            ["git", "remote", "-v"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        issues["remote_configured"] = "origin" in result.stdout

        # Check current branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        issues["branch_exists"] = result.returncode == 0 and result.stdout.strip()

        logger.info("Git diagnostics completed")
        return issues

    except Exception as e:
        logger.error(f"Error diagnosing Git issues: {e}")
        return issues


def fix_git_setup() -> bool:
    """Fix common Git setup issues."""
    try:
        project_dir = Path(__file__).parent

        # Initialize Git if needed
        if not diagnose_git_issues()["git_initialized"]:
            subprocess.run(["git", "init"], cwd=project_dir)
            logger.info("Initialized Git repository")

        # Set up remote if missing
        issues = diagnose_git_issues()
        if not issues["remote_configured"]:
            repo_url = get_project_info()["repository"]
            subprocess.run(
                ["git", "remote", "add", "origin", f"{repo_url}.git"], cwd=project_dir
            )
            logger.info(f"Added remote origin: {repo_url}")

        return True

    except Exception as e:
        logger.error(f"Error fixing Git setup: {e}")
        return False


def setup_github_push() -> bool:
    """Set up GitHub push with comprehensive error handling."""
    try:
        project_dir = Path(__file__).parent

        # Check if repository exists on GitHub
        repo_url = "https://github.com/Maggot4703/Crew"
        logger.info(f"Setting up push to: {repo_url}")

        # Configure Git user if not set
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        if result.returncode != 0:
            subprocess.run(
                ["git", "config", "user.name", "Maggot4703"], cwd=project_dir
            )

        result = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        if result.returncode != 0:
            subprocess.run(
                ["git", "config", "user.email", "mark@example.com"], cwd=project_dir
            )

        # Set remote URL with correct username
        subprocess.run(
            ["git", "remote", "set-url", "origin", f"{repo_url}.git"], cwd=project_dir
        )

        return True

    except Exception as e:
        logger.error(f"Error setting up GitHub push: {e}")
        return False


def push_to_github() -> bool:
    """Push to GitHub with multiple strategies."""
    try:
        project_dir = Path(__file__).parent

        # Strategy 1: Normal push
        result = subprocess.run(
            ["git", "push", "-u", "origin", "main"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )

        if result.returncode == 0:
            logger.info("✅ Successfully pushed to GitHub")
            return True

        # Strategy 2: Force push if normal push fails
        logger.warning("Normal push failed, trying force push...")
        result = subprocess.run(
            ["git", "push", "-u", "origin", "main", "--force"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )

        if result.returncode == 0:
            logger.info("✅ Force push successful")
            return True

        # Log the error for troubleshooting
        logger.error(f"❌ Push failed: {result.stderr}")

        # Print helpful troubleshooting info
        print("\n🔧 Troubleshooting GitHub Push Issues:")
        print("1. Ensure repository exists on GitHub")
        print("2. Check your GitHub credentials/token")
        print("3. Try creating repository manually on GitHub")
        print("4. Run: git remote -v (to check remote URL)")

        return False

    except Exception as e:
        logger.error(f"Error pushing to GitHub: {e}")
        return False


def detect_github_issues() -> dict:
    """Detect specific GitHub push issues and return diagnostic info."""
    issues = {}
    try:
        project_dir = Path(__file__).parent

        # Test Git installation
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        issues["git_installed"] = result.returncode == 0

        # Test repository initialization
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        issues["repo_initialized"] = result.returncode == 0

        # Test remote configuration
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        issues["remote_configured"] = result.returncode == 0
        issues["remote_url"] = (
            result.stdout.strip() if result.returncode == 0 else "Not set"
        )

        # Test authentication (dry run)
        result = subprocess.run(
            ["git", "ls-remote", "origin"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        issues["auth_working"] = result.returncode == 0
        issues["auth_error"] = result.stderr if result.returncode != 0 else ""

        # Check for uncommitted changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        issues["has_uncommitted"] = len(result.stdout.strip()) > 0

        # Check current branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        issues["current_branch"] = (
            result.stdout.strip() if result.returncode == 0 else "unknown"
        )

        return issues

    except Exception as e:
        logger.error(f"Error detecting GitHub issues: {e}")
        issues["error"] = str(e)
        return issues


def generate_help_file(issues: dict) -> None:
    """Generate a help file with specific solutions based on detected issues."""
    help_content = f"""# GitHub Push Issues - Diagnostic Report
Generated: {pd.Timestamp.now()}

## Detected Issues and Solutions

"""

    if not issues.get("git_installed", True):
        help_content += """### ❌ Git Not Installed
**Problem**: Git is not installed or not in PATH
**Solution**:
```bash
# Ubuntu/Debian:
sudo apt update && sudo apt install git

# macOS:
brew install git

# Windows: Download from https://git-scm.com/
```

"""

    if not issues.get("repo_initialized", True):
        help_content += """### ❌ Repository Not Initialized
**Problem**: Git repository not initialized
**Solution**:
```bash
cd /home/me/BACKUP/PROJECTS/Crew
git init
git add .
git commit -m "Initial commit"
```

"""

    if not issues.get("remote_configured", True):
        help_content += """### ❌ Remote Repository Not Configured
**Problem**: No remote repository configured
**Solution**:
```bash
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/Crew.git

# Or if remote exists but wrong URL:
git remote set-url origin https://github.com/YOUR_USERNAME/Crew.git
```

"""

    if not issues.get("auth_working", True):
        auth_error = issues.get("auth_error", "")
        help_content += f"""### ❌ Authentication Failed
**Problem**: Cannot authenticate with GitHub
**Error**: {auth_error}

**Solutions**:

1. **Use Personal Access Token**:
   - Go to GitHub Settings > Developer settings > Personal access tokens
   - Generate new token with 'repo' permissions
   - Use token as password when prompted

2. **Configure Git credentials**:
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

3. **Use SSH instead of HTTPS**:
```bash
git remote set-url origin git@github.com:YOUR_USERNAME/Crew.git
```

"""

    if issues.get("has_uncommitted", False):
        help_content += """### ⚠️ Uncommitted Changes
**Problem**: You have uncommitted changes
**Solution**:
```bash
git add .
git commit -m "Commit message describing changes"
```

"""

    # Add general troubleshooting
    help_content += f"""
## Current Configuration
- Remote URL: {issues.get('remote_url', 'Not set')}
- Current Branch: {issues.get('current_branch', 'unknown')}
- Git Installed: {issues.get('git_installed', 'unknown')}
- Repository Initialized: {issues.get('repo_initialized', 'unknown')}
- Remote Configured: {issues.get('remote_configured', 'unknown')}
- Authentication Working: {issues.get('auth_working', 'unknown')}

## Step-by-Step Push Process

1. **Initialize repository** (if needed):
```bash
git init
```

2. **Add remote** (replace with your GitHub URL):
```bash
git remote add origin https://github.com/YOUR_USERNAME/Crew.git
```

3. **Stage and commit changes**:
```bash
git add .
git commit -m "Initial commit"
```

4. **Set main branch**:
```bash
git branch -M main
```

5. **Push to GitHub**:
```bash
git push -u origin main
```

## If All Else Fails

1. **Create repository on GitHub manually**
2. **Use force push** (⚠️ USE WITH CAUTION):
```bash
git push -u origin main --force
```

3. **Start fresh**:
```bash
rm -rf .git
git init
git add .
git commit -m "Fresh start"
git remote add origin https://github.com/YOUR_USERNAME/Crew.git
git branch -M main
git push -u origin main
```

## Get Help
- GitHub Documentation: https://docs.github.com/en/get-started/using-git
- Git Documentation: https://git-scm.com/doc
"""

    # Save to file
    help_file = Path("github_issues_help.txt")
    with open(help_file, "w") as f:
        f.write(help_content)

    logger.info(f"Help file saved to: {help_file.absolute()}")
    print(f"📄 Detailed help saved to: {help_file.absolute()}")


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

        # Set up Git repository
        setup_git_repository()

        # Check for unstaged files and handle them automatically
        if check_git_status():
            logger.info("Auto-fixing unstaged files...")
            fix_git_unstaged_files()

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
        file_handler.close()

    print("DONE")


def auto_commit_changes() -> bool:
    """Automatically stage and commit all changes."""
    try:
        project_dir = Path(__file__).parent

        # Stage all changes
        result = subprocess.run(
            ["git", "add", "."],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )

        if result.returncode != 0:
            logger.error(f"Failed to stage files: {result.stderr}")
            return False

        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )

        if result.returncode == 0:
            logger.info("No changes to commit")
            return True

        # Commit with descriptive message
        commit_message = f"Auto-commit: Update NPCs Data Processing Tool v{get_version()}\n\n- Fixed GitHub username to Maggot4703\n- Updated repository URL\n- Added automatic commit functionality"

        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )

        if result.returncode == 0:
            logger.info("Successfully committed changes")
            print("✅ Changes committed successfully")
            return True
        else:
            logger.error(f"Failed to commit: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error committing changes: {e}")
        return False


def auto_fix_all_issues() -> bool:
    """Automatically detect and fix common project issues."""
    try:
        logger.info("🔧 Auto-fixing all detected issues...")
        
        # Fix import issues
        fix_lint_errors()
        
        # Fix Git setup
        setup_git_repository()
        
        # Fix GitHub configuration
        setup_github_push()
        
        # Stage and commit changes
        if check_git_status():
            stage_and_commit_files()
        
        # Attempt push to GitHub
        push_to_github()
        
        logger.info("✅ Auto-fix completed")
        return True
        
    except Exception as e:
        logger.error(f"Error in auto-fix: {e}")
        return False


def generate_project_summary() -> None:
    """Generate a comprehensive project summary."""
    summary_content = f"""# NPCs Data Processing Tool - Project Summary
Generated: {pd.Timestamp.now()}

## Project Information
- Name: {get_project_info()['name']}
- Version: {get_version()}
- Author: {get_project_info()['author']}
- Repository: {get_project_info()['repository']}

## Features
- Image processing with grid overlays
- CSV/Excel data analysis
- Geometric calculations (hexagon points, color conversion)
- Advanced data processing and grouping
- Git integration and automatic commits
- GitHub push automation

## Recent Updates
- Fixed GitHub username to Maggot4703
- Added automatic issue detection and fixing
- Enhanced Git and GitHub integration
- Improved error handling and logging

## Usage
```bash
python Crew.py
```

## Dependencies
- pandas
- Pillow (PIL)
- ijson

## File Structure
- Crew.py: Main application
- input/: Input images
- output/: Processed images
- data/: CSV/Excel data files
- tests/: Unit tests
"""
    
    with open("project_summary.md", "w") as f:
        f.write(summary_content)
    
    logger.info("📄 Project summary generated: project_summary.md")


def backup_project() -> bool:
    """Create a backup of the project."""
    try:
        import shutil
        import datetime
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"Crew_backup_{timestamp}"
        backup_path = Path.home() / "BACKUP" / "PROJECTS" / backup_name
        
        # Create backup directory
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Copy project files
        project_dir = Path(__file__).parent
        for item in project_dir.iterdir():
            if item.name != '.git' and not item.name.startswith('.'):
                if item.is_file():
                    shutil.copy2(item, backup_path)
                elif item.is_dir():
                    shutil.copytree(item, backup_path / item.name, dirs_exist_ok=True)
        
        logger.info(f"📦 Project backed up to: {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return False


def try_push_project() -> bool:
    """Comprehensive project push attempt with detailed logging."""
    try:
        project_dir = Path(__file__).parent
        
        print("🚀 Attempting to push project to GitHub...")
        print("=" * 50)
        
        # Step 1: Check and fix repository setup
        print("1. Checking repository setup...")
        issues = detect_github_issues()
        
        if not issues.get("repo_initialized", False):
            print("   Initializing Git repository...")
            subprocess.run(["git", "init"], cwd=project_dir)
        
        # Step 2: Fix remote URL
        print("2. Setting correct remote URL...")
        correct_url = "https://github.com/Maggot4703/Crew.git"
        subprocess.run(
            ["git", "remote", "set-url", "origin", correct_url],
            cwd=project_dir,
            stderr=subprocess.DEVNULL
        )
        subprocess.run(
            ["git", "remote", "add", "origin", correct_url],
            cwd=project_dir,
            stderr=subprocess.DEVNULL
        )
        
        # Step 3: Stage and commit changes
        print("3. Staging and committing changes...")
        result = subprocess.run(
            ["git", "add", "."],
            capture_output=True,
            text=True,
            cwd=project_dir
        )
        
        result = subprocess.run(
            ["git", "commit", "-m", "Push NPCs Data Processing Tool to GitHub\n\n- Complete project with image processing, data analysis, and Git integration\n- Fixed repository URL for Maggot4703 account\n- Added comprehensive push functionality"],
            capture_output=True,
            text=True,
            cwd=project_dir
        )
        
        # Step 4: Set main branch
        print("4. Setting main branch...")
        subprocess.run(
            ["git", "branch", "-M", "main"],
            cwd=project_dir
        )
        
        # Step 5: Attempt push
        print("5. Pushing to GitHub...")
        result = subprocess.run(
            ["git", "push", "-u", "origin", "main"],
            capture_output=True,
            text=True,
            cwd=project_dir
        )
        
        if result.returncode == 0:
            print("✅ SUCCESS: Project pushed to GitHub!")
            print(f"🌐 View at: https://github.com/Maggot4703/Crew")
            return True
        else:
            print("❌ Push failed. Trying force push...")
            result = subprocess.run(
                ["git", "push", "-u", "origin", "main", "--force"],
                capture_output=True,
                text=True,
                cwd=project_dir
            )
            
            if result.returncode == 0:
                print("✅ SUCCESS: Force push completed!")
                return True
            else:
                print(f"❌ FAILED: {result.stderr}")
                return False
                
    except Exception as e:
        logger.error(f"Error pushing project: {e}")
        return False


def create_push_log(success: bool, error_msg: str = "") -> None:
    """Create a detailed push log."""
    log_content = f"""# GitHub Push Log
Timestamp: {pd.Timestamp.now()}
Status: {'SUCCESS' if success else 'FAILED'}
Repository: https://github.com/Maggot4703/Crew

## Push Details
- Project: NPCs Data Processing Tool v{get_version()}
- Branch: main
- Remote: origin (https://github.com/Maggot4703/Crew.git)

{'## Success Details' if success else '## Error Details'}
{f'Push completed successfully to GitHub!' if success else f'Error: {error_msg}'}

## Next Steps
{'- Project is now live on GitHub' if success else '- Check GitHub repository exists'}
{'- Clone with: git clone https://github.com/Maggot4703/Crew.git' if success else '- Verify authentication credentials'}
{'- Share the repository link' if success else '- Try manual push commands'}
"""
    
    with open("push_log.txt", "w") as f:
        f.write(log_content)
    
    print(f"📄 Push log saved to: push_log.txt")


def read_and_analyze_logs() -> dict:
    """Read existing logs and analyze common issues."""
    log_analysis = {
        "git_errors": [],
        "auth_errors": [],
        "repo_errors": [],
        "suggestions": []
    }
    
    try:
        # Read push log if exists
        push_log_path = Path("push_log.txt")
        if push_log_path.exists():
            with open(push_log_path, "r") as f:
                content = f.read()
                
                if "repository not found" in content.lower():
                    log_analysis["repo_errors"].append("Repository doesn't exist on GitHub")
                    log_analysis["suggestions"].append("Create repository 'Crew' on GitHub under Maggot4703 account")
                
                if "authentication failed" in content.lower():
                    log_analysis["auth_errors"].append("GitHub authentication failed")
                    log_analysis["suggestions"].append("Use Personal Access Token instead of password")
                
                if "permission denied" in content.lower():
                    log_analysis["auth_errors"].append("Permission denied")
                    log_analysis["suggestions"].append("Check repository ownership and access rights")
        
        # Read Git output from previous attempts
        project_dir = Path(__file__).parent
        result = subprocess.run(
            ["git", "remote", "-v"],
            capture_output=True,
            text=True,
            cwd=project_dir
        )
        
        if "markferguson" in result.stdout:
            log_analysis["repo_errors"].append("Wrong GitHub username in remote URL")
            log_analysis["suggestions"].append("Fix remote URL to use Maggot4703")
        
        logger.info(f"Log analysis complete: {len(log_analysis['suggestions'])} issues found")
        return log_analysis
        
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return log_analysis


def apply_automated_fixes(log_analysis: dict) -> bool:
    """Apply automated fixes based on log analysis."""
    try:
        project_dir = Path(__file__).parent
        fixes_applied = []
        
        # Fix remote URL if wrong username detected
        if any("Wrong GitHub username" in error for error in log_analysis["repo_errors"]):
            subprocess.run(
                ["git", "remote", "set-url", "origin", "https://github.com/Maggot4703/Crew.git"],
                cwd=project_dir
            )
            fixes_applied.append("Fixed remote URL to Maggot4703")
        
        # Ensure Git user is set correctly
        subprocess.run(
            ["git", "config", "user.name", "Maggot4703"],
            cwd=project_dir
        )
        subprocess.run(
            ["git", "config", "user.email", "maggot4703@example.com"],
            cwd=project_dir
        )
        fixes_applied.append("Set Git user configuration")
        
        # Create fix summary
        if fixes_applied:
            fix_summary = f"""# Automated Fixes Applied
Timestamp: {pd.Timestamp.now()}

Fixes Applied:
{chr(10).join(f'- {fix}' for fix in fixes_applied)}

Issues Found in Logs:
{chr(10).join(f'- {error}' for error in log_analysis["repo_errors"] + log_analysis["auth_errors"])}

Suggestions:
{chr(10).join(f'- {suggestion}' for suggestion in log_analysis["suggestions"])}
"""
            
            with open("automated_fixes.txt", "w") as f:
                f.write(fix_summary)
            
            logger.info(f"Applied {len(fixes_applied)} automated fixes")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error applying fixes: {e}")
        return False


if __name__ == "__main__":
    print(f"Starting {get_project_info()['name']} v{get_version()}")
    print(f"Repository: {get_project_info()['repository']}")

    # Generate project summary
    generate_project_summary()
    
    # Create backup
    backup_project()
    
    # Auto-fix all issues
    print("🚀 Running auto-fix for all issues...")
    auto_fix_all_issues()

    # Detect GitHub issues first
    print("🔍 Detecting GitHub issues...")
    issues = detect_github_issues()

    # Generate help file
    generate_help_file(issues)

    # Setup Git and GitHub
    setup_git_repository()
    setup_github_push()

    # Handle unstaged files - use the correct function name
    if check_git_status():
        print("📝 Staging and committing unstaged files...")
        if stage_and_commit_files():
            print("✅ Files staged and committed successfully")
        else:
            print("❌ Failed to stage/commit files")
    
    # Push to GitHub
    print("📤 Attempting to push to GitHub...")
    if push_to_github():
        print("🎉 Successfully pushed to GitHub!")
    else:
        print("⚠️  GitHub push failed - see troubleshooting above")

    # Read and analyze existing logs
    print("📖 Reading and analyzing logs...")
    log_analysis = read_and_analyze_logs()
    
    if log_analysis["suggestions"]:
        print(f"Found {len(log_analysis['suggestions'])} issues in logs")
        print("🔧 Applying automated fixes...")
        apply_automated_fixes(log_analysis)
    
    # Try pushing the project
    print("\n" + "="*60)
    print("ATTEMPTING GITHUB PUSH")
    print("="*60)
    
    push_success = try_push_project()
    create_push_log(push_success, "" if push_success else "See error details above")
    
    if not push_success:
        print("\n💡 Manual push instructions:")
        print("1. Create repository 'Crew' at https://github.com/new")
        print("2. Run: git push -u origin main")
        print("3. Use Personal Access Token for password")
    
    exit_code = main()
    sys.exit(exit_code)
