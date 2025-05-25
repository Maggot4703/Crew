#!/usr/bin/python3
"""
NPCs Data Processing Tool

This script provides functionality for image processing, data analysis from CSV/Excel,
data visualization, and batch processing of files.
It includes utilities for handling images, files, and performing various data
manipulations and analyses. The script is designed to be modular and extensible,
allowing for easy addition of new processing jobs and utilities.

Key Features:
- Image processing: Overlay grids on images.
- File handling: Read data from CSV and Excel files using built-in modules and pandas.
- Data analysis: Perform basic statistical analysis, data filtering, and grouping.
- Geometric calculations: Convert colors between HEX and RGB, calculate hexagon points.
- Advanced data processing: Split CSV files into groups based on separators.
- GUI integration: Launch a separate GUI application.

Author: Mark Ferguson
Version: 1.0.0
Date: May 2025
"""

import csv
import logging
import math

# region Imports
import os
from pathlib import Path
from typing import List, Tuple

import ijson
import pandas as pd
from PIL import Image, ImageDraw

# endregion

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
        # print(f"Error: Image file '{image_path}' not found")
        logging.error(f"Error: Image file '{image_path}' not found")
        raise
    except Exception as e:
        # print(f"Error processing image: {e}")
        logging.error(f"Error processing image: {e}")
        raise


# endregion


# region File Handling Utilities
def read_csv_builtin(filename: str) -> list:
    """
    Reads CSV data using the built-in `csv` module.

    Skips the header row if present.

    Args:
        filename: Path to the CSV file.

    Returns:
        A list of lists, where each inner list represents a row from the CSV file.
    """
    data = []
    with open(filename, "r") as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip header row if present
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


def read_file(filename: str) -> pd.DataFrame | None:  # Added None to return type
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
        # print(f"Error: Could not find file '{filename}'")
        logging.error(f"Error: Could not find file '{filename}'")
    except Exception as e:
        # print(f"Error reading file: {e}")
        logging.error(f"Error reading file: {e}")
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
        logging.error("Error: data/columns.csv not found in showColumn")
    except Exception as e:
        logging.error(f"Error in showColumn: {e}")
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
def job2(filename: str = "data/npcs.csv") -> None:  # Added return type hint
    """
    Reads and analyzes a CSV file using pandas.

    Performs basic data exploration including shape, columns, head,
    and statistical summary. Also demonstrates position analysis,
    data filtering, and grouped analysis if a "POSITION" column exists.

    Args:
        filename: Path to the CSV file (default is "data/npcs.csv").
    """
    csv_file = filename
    try:
        data_pandas_df = pd.read_csv(
            csv_file
        )  # Renamed to avoid conflict if original data_pandas was meant to be used
        # Basic data exploration
        print("\\n=== Data Overview ===")
        print(f"Shape: {data_pandas_df.shape}")
        print(f"Columns: {data_pandas_df.columns.tolist()}")
        print("\\n=== First 5 rows ===")
        print(data_pandas_df.head())
        # Statistical summary
        print("\\n=== Numerical Statistics ===")
        print(data_pandas_df.describe())
        print(data_pandas_df)  # Column operations
        if "POSITION" in data_pandas_df.columns:
            print("\\n=== Position Analysis ===")
            position_counts = data_pandas_df["POSITION"].value_counts()
            print("Position distribution:")
            print(position_counts)
        # Data filtering example
        print("\\n=== Filtered Data ===")
        # Example: Filter rows where POSITION matches specific criteria
        filtered_data = data_pandas_df[
            data_pandas_df["POSITION"].str.contains("Captain", na=False)
        ]
        print("Managers in dataset:")
        print(filtered_data[["POSITION", "TAG"]])  # Adjust columns as needed
        # Group by operations
        print("\\n=== Grouped Analysis ===")
        # Example: Group by position and count
        grouped_data = data_pandas_df.groupby("POSITION").size()
        print("Counts by position:")
        print(grouped_data)
        position_percentage = (grouped_data / grouped_data.sum()) * 100
        print("\\n=== Position Percentage ===")
        print(position_percentage)
    except FileNotFoundError:
        print(f"Error: Could not find CSV file '{csv_file}'")
    except Exception as e:
        print(f"Error processing CSV file: {e}")  # Added error message
    print("\n=== Read CSV file complete ===\n")
    print("job2 CSV complete.")


# XLS
def job3(filename: str = "data/npcs.xls") -> None:  # Added return type hint
    """
    Reads and displays contents from an Excel file.

    Specifically looks for and analyzes an "npcs" column if present.

    Args:
        filename: Path to the Excel file (default is "data/npcs.xls").
    """
    # Excel file reading
    excel_file = filename
    try:
        df = read_excel(excel_file, sheet_name=0)  # Specify the sheet name or index
        print("\nExcel Data:")
        print(df.head())
        print(df.columns)
        print(df["npcs"])
        print("\n=== npcs Column Analysis ===")
        print(df["npcs"].value_counts())
        print("\n=== npcs Column Unique Values ===")
        print(df["npcs"].unique())
    except FileNotFoundError:
        print(f"Error: Could not find Excel file '{excel_file}'")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
    print("\n=== Excel file reading complete ===\n")
    print("job3 XLS complete.")


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
        df = read_file(filename)  # Read file once
        # Analyze data
        analyze_data(df)  # Analyze once
        # excel_df = read_file(filename) # Removed redundant read
        # analyze_data(excel_df) # Removed redundant analysis
    except Exception as e:
        print(f"Error in job4: {e}")
    print("\\n=== NPC Analysis complete ===\\n")  # Corrected f-string
    print("job4 show columns complete.")
    print("\\n=== CSV file analysis complete ===\\n")


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
    logging.info("\n=== SkyRig Cast ===\n")
    logging.info(data_pandas[["NPC", "ROLE"]])
    logging.info("\n=== <NPC> <ROLE> <PRIMUS> ===")
    logging.info(data_pandas[["NPC", "ROLE", "PRIMUS"]])

    cols = data_pandas.columns.tolist()
    for col in cols:
        logging.info(f"{data_pandas[col].unique()}")
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
                logging.info(f"{data_pandas.at[row, col]}")
                f.write(f"{data_pandas.at[row, col]}\\n")
            logging.info("")  # Removed whitespace before : (was f"")
            # print(f"File {fname} created successfully.")
    print("\\n=== SkyRig Cast Complete ===\\n")
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
    print("\\n=== SkyRig Complete ===\\n")
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


def calculate_hexagon_points(
    height: int, center_x: int = 0, center_y: int = 0
) -> List[Tuple[int, int]]:
    """
    Calculates the 6 vertex points of a regular hexagon given its height.

    The hexagon is oriented with two horizontal sides (top and bottom).
    The points are returned as integer coordinates.

    Args:
        height: The height of the hexagon (distance between parallel horizontal sides).
                Must be a positive integer.
        center_x: The x-coordinate of the center of the hexagon (default is 0).
        center_y: The y-coordinate of the center of the hexagon (default is 0).

    Returns:
        A list of 6 (x, y) tuples representing the vertices of the hexagon.
        Returns an empty list if the height is not positive.
    """
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
        logging.error(f"Error splitting CSV into groups: {e}")
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
    import subprocess

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


def main() -> int:  # Added return type hint
    """
    Main function to run the data processing script.

    Configures logging, creates necessary directories, and runs a series of predefined jobs.
    Handles errors during job execution and logs them.

    Returns:
        0 if processing completes successfully, 1 if a critical error occurs.
    """
    # Configure logging with both file and console output
    logging.basicConfig(
        filename="output.txt",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filemode="w",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Add console handler with same formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)
    try:
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
        logging.info("=== Starting Data Processing ===")
        # Run each job once
        for job_name, job_func in jobs:
            try:
                logging.info(f"\n--- Running {job_name} ---")
                job_func()
                spacer()
            except FileNotFoundError as fe:
                logging.error(f"Error in {job_name}: File not found - {str(fe)}")
            except Exception as e:
                logging.error(f"Error in {job_name}: {str(e)}")

        logging.info("=== Processing Complete ===\n")
        return 0

    except Exception as e:
        logging.error(f"Critical error in main execution: {str(e)}")
        return 1
    print("DONE")


if __name__ == "__main__":
    main()
    display_ascii_characters()
    start_gui()

# endregion

# region Documentation
# The script is designed to be run as a standalone program.
# It includes a main function that coordinates the execution of various jobs.
# The main function is called when the script is executed directly.
# The script is structured to allow for easy modification and extension.
# Each job is defined as a separate function, making it easy to add or remove jobs as needed.
# The script also includes error handling to ensure that any issues encountered during processing are logged.
# The logging module is used to log messages to both a file and the console.
# The script is designed to be modular and reusable, allowing for easy integration into larger projects.
# The script is intended for data processing and analysis, specifically for working with images and CSV/Excel files.
# The script is designed to be run in a Python 3 environment.
# The script is compatible with Python 3.6 and later versions.
# The script is intended for educational and research purposes.
# The script is not intended for production use without further testing and validation.
# The script is provided as-is, without any warranties or guarantees.
# The author is not responsible for any damages or losses resulting from the use of this script.
# endregion
