#!/usr/bin/python3
"""
npcs Data Processing Tool

This script provides functionality for:
1. Image processing with grid overlays for vehicle analysis
2. CSV and Excel file reading for npcs data analysis 
3. Data visualization and statistical reporting
4. Batch processing of multiple image and data files

Author: Mark Ferguson
Version: 1.0.0
Date: April 2025
"""

#region Imports
import os
from pathlib import Path
from typing import List, Tuple, Optional
import csv
import globals
import logging
import pandas as pd
from PIL import Image, ImageDraw
import matplotlib as plt
import numpy as np
import ijson
import math
#endregion

#region globals
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
IMAGE_FILES = [
    "Cars1.png",
    "Cars2.png",
    "Cars3.png",
    "Cars4.png",
    "Cars5.png"
]
GRID_SIZES = [
    (10, 10),
    (20, 20),
    (30, 30),
    (40, 40),
    (50, 50)
]
#endregion

#region Image Processing Functions
def markHorizontalLine(x1: int, y1: int, x2: int, y2: int, 
                      color: Tuple[int, int, int] = DEFAULT_LINE_COLOR, 
                      thickness: int = 1) -> Image:
    """
    Create a new image with a horizontal line drawn on it.
    
    Args:
        x1: Starting x-coordinate
        y1: Starting y-coordinate
        x2: Ending x-coordinate
        y2: Ending y-coordinate
        color: Color of the line (default: DEFAULT_LINE_COLOR)
        thickness: Width of the line in pixels (default: 1)
    
    Returns:
        PIL.Image: New image with the drawn line
    """
    img = Image.new("RGB", IMAGE_DIMENSIONS, "white")
    draw = ImageDraw.Draw(img)
    # Draw the line
    draw.line([(x1, y1), (x2, y2)], fill=color, width=thickness)
    # Return the image
    return img

def overlayGrid(image_path: str, 
                grid_color: str = DEFAULT_GRID_COLOR, 
                grid_size: tuple = DEFAULT_GRID_SIZE) -> Image:
    """
    Overlay a grid on an existing image.
    
    Creates a grid overlay with specified dimensions on the input image.
    Grid lines are drawn at equal intervals based on the grid_size parameter.
    
    Args:
        image_path: Path to the source image file
        grid_color: Color for grid lines (default: DEFAULT_GRID_COLOR)
        grid_size: Tuple of (columns, rows) for grid dimensions
    
    Returns:
        PIL.Image: Modified image with grid overlay
        
    Raises:
        ValueError: If grid dimensions are not positive
        FileNotFoundError: If source image doesn't exist
        IOError: If image file cannot be opened/processed
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
            draw.line([(pos_x, 0), (pos_x, img_height)], 
                     fill=grid_color, width=1)

        for y in range(1, rows):
            pos_y = int(y * cell_height)
            draw.line([(0, pos_y), (img_width, pos_y)], 
                     fill=grid_color, width=1)

        return img
    
    except FileNotFoundError:
        # print(f"Error: Image file '{image_path}' not found")
        logging.error(f"Error: Image file '{image_path}' not found")
        raise
    except Exception as e:
        # print(f"Error processing image: {e}")
        logging.error(f"Error processing image: {e}")
        raise
#endregion

#region File Reading Functions
def read_csv_builtin(filename: str) -> list:
    """
    Read CSV data using built-in csv module
    :param filename: Path to the CSV file
    :return: List of rows from CSV
    """
    data = []
    with open(filename, 'r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip header row if present
        for row in csv_reader:
            data.append(row)
    return data

def read_csv_pandas(filename: str) -> pd.DataFrame:
    
    """
    Read CSV data using pandas
    :param filename: Path to the CSV file
    :return: Pandas DataFrame containing CSV data
    """
    return pd.read_csv(filename)

def read_excel(filename: str, sheet_name: str = None) -> pd.DataFrame:
    """
    Read Excel data using pandas
    :param filename: Path to the Excel file (.xlsx or .xls)
    :param sheet_name: Name of the sheet to read (default is first sheet)
    :return: Pandas DataFrame containing Excel data
    """
    return pd.read_excel(filename, sheet_name=sheet_name)

def read_file(filename: str):
    '''
    Read CSV or Excel file using pandas
    
    Args:
        filename (str): Path to the file (.csv or .xlsx)
        
    Returns:
        pd.DataFrame: Loaded data frame
    '''
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(filename)
        elif filename.endswith(('.xlsx', '.xls')):
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
    string = f"Column: {col}"
    print(string)
    try:
        with open("data/columns.csv","r") as f: # Changed "w" to "r"
            reader = csv.reader(f)
            for row in reader:
                if row and not row[0].startswith("#"): # Added check for empty row
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

def showAllColumns(columns: list) -> None:
    """Display all columns in the provided list."""
    for col in columns:
        showColumn(col)
#endregion

#region Data Processing Jobs
#Image Processing
def job1() -> None:
    
    """Process images with grid overlay."""
    output_dir = os.path.join(os.path.dirname(__file__), OUTPUT_DIR)
    os.makedirs(output_dir, exist_ok=True)
    
    # Use the imported constants
    files = [os.path.join(INPUT_DIR, f) for f in IMAGE_FILES]
    names = [f"Cars{i+1}.png" for i in range(len(IMAGE_FILES))]
    
    # Process each image
    for i, (input_image, output_name, grid_size) in enumerate(zip(files, names, GRID_SIZES)):
        try:
            output_path = os.path.join(output_dir, output_name)
            grid_image = overlayGrid(input_image, 
                                   grid_color=DEFAULT_GRID_COLOR,
                                   grid_size=grid_size)
            grid_image.save(output_path)
            print(f"Image with grid saved as {output_path}")
        except Exception as e:  
            print(f"Error processing {input_image}: {e}")
    print("\n=== Process images complete ===\n")
    print("job1 complete.")  

#CSV
def job2(filename: str = "data/npcs.csv"):
    '''
    Read CSV file using both built-in csv module and pandas
    CSV file reading
    '''
    csv_file = filename
    try:
        # `data_pandas` is a pandas DataFrame that stores the data read from the CSV file "npcs.csv".
        # The `read_csv_pandas` function is used to read the CSV file and load its contents into the
        # DataFrame. The DataFrame is then stored in the variable `data_pandas`. This variable is used
        # to access and manipulate the data from the CSV file, such as displaying the first few rows,
        # column names, specific columns like 'POSITION', and accessing rows using `iloc`.
        data_pandas = pd.read_csv(csv_file)
        # Basic data exploration
        print("\n=== Data Overview ===")
        print(f"Shape: {data_pandas.shape}")
        print(f"Columns: {data_pandas.columns.tolist()}")
        print("\n=== First 5 rows ===")
        print(data_pandas.head())
        # Statistical summary
        print("\n=== Numerical Statistics ===")
        print(data_pandas.describe())
        print(data_pandas)  # Column operations
        if 'POSITION' in data_pandas.columns:
            print("\n=== Position Analysis ===")
            position_counts = data_pandas['POSITION'].value_counts()
            print("Position distribution:")
            print(position_counts)
        # Data filtering example
        print("\n=== Filtered Data ===")
        # Example: Filter rows where POSITION matches specific criteria
        filtered_data = data_pandas[data_pandas['POSITION'].str.contains('Captain', na=False)]
        print("Managers in dataset:")
        print(filtered_data[['POSITION', 'TAG']])  # Adjust columns as needed
        # Group by operations
        print("\n=== Grouped Analysis ===")
        # Example: Group by position and count
        grouped_data = data_pandas.groupby('POSITION').size()
        print("Counts by position:")
        print(grouped_data)
        position_percentage = (grouped_data / grouped_data.sum()) * 100
        print("\n=== Position Percentage ===")
        print(position_percentage)
    except FileNotFoundError:
        print(f"Error: Could not find CSV file '{csv_file}'")
    except Exception as e:
        print(f"Error processing CSV file: {e}")  # Added error message
    print("\n=== Read CSV file complete ===\n")
    print("job2 CSV complete.")  

#XLS
def job3(filename: str = "data/npcs.xls"):
    '''
    Read Excel file and display its contents.
    '''
    # Excel file reading
    excel_file = filename
    try:
        df = read_excel(excel_file, sheet_name=0)  # Specify the sheet name or index
        print("\nExcel Data:")
        print(df.head())
        print(df.columns)
        print(df['npcs'])
        print("\n=== npcs Column Analysis ===")
        print(df['npcs'].value_counts())
        print("\n=== npcs Column Unique Values ===")
        print(df['npcs'].unique())
    except FileNotFoundError:
        print(f"Error: Could not find Excel file '{excel_file}'")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
    print("\n=== Excel file reading complete ===\n")
    print("job3 XLS complete.")  

#show column analysis
def job4(filename: str = "data/npcs.csv"):
    """Process and analyze data frames"""
    try:
        # Read data files
        print(filename)
        df = read_file(filename) # Read file once
        # Analyze data
        analyze_data(df) # Analyze once
        # excel_df = read_file(filename) # Removed redundant read
        # analyze_data(excel_df) # Removed redundant analysis
    except Exception as e:
        print(f"Error in job4: {e}")
    print("\\n=== NPC Analysis complete ===\\n")
    print("job4 show columns complete.")  
    print("\n=== CSV file analysis complete ===\n")

#save csv columns
def job5(filename: str = "data/npcs.csv"):
    """
    Function to display CSV data.
    """
    data_pandas = pd.read_csv(filename)
    logging.info("\n=== SkyRig Cast ===\n")
    logging.info(data_pandas[['NPC', 'ROLE']])
    logging.info("\n=== <NPC> <ROLE> <PRIMUS> ===")
    logging.info(data_pandas[['NPC', 'ROLE', 'PRIMUS']])
    
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
            name=col
            name = name.upper()
            
            f.write(f"{name}\n")
            for row in data_pandas.index:
                logging.info(f"{data_pandas.at[row, col]}")
                f.write(f"{data_pandas.at[row, col]}\n")
            logging.info(f"")
            #print(f"File {fname} created successfully.")
    print("\n=== SkyRig Cast Complete ===\n")
    print("job5 save csv complete.")  # Changed from job1 to job5

#show cols
def job6(filename: str = "data/npcs.csv"):
    data_pandas = pd.read_csv(filename)
    cols=data_pandas.columns.tolist()
    print(cols)
    print("\n=== SkyRig Roles Complete ===\n")
    print("job6 complete.")  # Changed from job1 to job5

#save
def job7(filename: str = "data/npcs.csv"):
    data_pandas = pd.read_csv(filename)
    print("\n=== SkyRig Complete ===\n")
    print("job7 complete.")  # Changed from job1 to job5

#save
def job8(filename: str = "data/npcs.csv"):
    display_npc_groups(filename)
    split_csv_groups(filename)
    print("job8 complete.")
#close
def Ending(filename: str = "data/npcs.csv"):
    print("\n=== Role Analysis Complete ===")
    print("\n=== CSV File Analysis Complete ===")
    print("\n=== Excel File Analysis Complete ===")
    print("\n=== Data Analysis Complete ===")
    print("\n=== All jobs have been commented out ===")
#endregion

#region Utility Functions
def spacer():
    """
    Print a blank line or separator for better readability in the output.
    """
    print("\n" + "-" * 40 + "\n")

def analyze_data(df: pd.DataFrame):
    '''
    Basic data analysis of a dataframe
    '''
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

def display_ascii_characters():
    for i in range(256):
        ascii_char = chr(i) 
        #if 32 >= i <= 126:
        print(f"{i}: {ascii_char}")
# Call the function to display the ASCII characters
#display_ascii_characters()

#endregion

#region Hex Calculations
def hex_to_rgb(hex_color: str) -> tuple:
    """
    Convert a hex color string to an RGB tuple.
    
    Args:
        hex_color: Hex color string (e.g., '#FF5733')
        
    Returns:
        tuple: RGB values as a tuple (R, G, B)
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb: tuple) -> str:
    """
    Convert an RGB tuple to a hex color string.
    Args:
        rgb: Tuple of RGB values (R, G, B)
    Returns:
        str: Hex color string (e.g., '#FF5733')
    """
    return '#' + ''.join(f'{int(c):02X}' for c in rgb)

#TODO: Add more functions for hex calculations

def calculate_hexagon_points(height: int, center_x: int = 0, center_y: int = 0) -> List[Tuple[int, int]]:
    """
    Calculate point positions of 6 points of a hexagon by supplying the height only.
    Returns int values for point coordinates.
    The hexagon is oriented with two horizontal sides (top and bottom).

    Args:
        height: The height of the hexagon (distance between parallel horizontal sides).
        center_x: The x-coordinate of the center of the hexagon.
        center_y: The y-coordinate of the center of the hexagon.

    Returns:
        List[Tuple[int, int]]: A list of 6 (x, y) tuples representing the vertices.
    """
    if height <= 0:
        return []

    # Side length 's' of the hexagon.
    # For a hexagon with height H (distance between parallel sides), s = H / sqrt(3)
    s = height / math.sqrt(3)

    points = [
        (center_x + s / 2, center_y + height / 2),  # Top-right
        (center_x - s / 2, center_y + height / 2),  # Top-left
        (center_x - s, center_y),                   # Middle-left
        (center_x - s / 2, center_y - height / 2),  # Bottom-left
        (center_x + s / 2, center_y - height / 2),  # Bottom-right
        (center_x + s, center_y)                    # Middle-right
    ]

    # Round coordinates to the nearest integer
    int_points = [(round(p[0]), round(p[1])) for p in points]
    return int_points

#TODO: Calculate point positions of 6 points of a hexagon by supplying the height only as integer.  Return int values for point coordinates only.


#endregion

#region CSV Data Processing Functions
def split_csv_groups(filename: str = "data/npcs.csv") -> dict:
    """
    Split CSV file into groups based on blank line separators.
    Each group is separated by two consecutive blank lines in the CSV.
    Handles cases where data rows might have different column counts than header.
    
    Args:
        filename (str): Path to the CSV file
        
    Returns:
        dict: Dictionary with group index as key and DataFrame as value
    """
    groups = {}
    current_group = []
    group_index = 0
    blank_line_count = 0
    
    try:
        with open(filename, 'r') as file:
            header = file.readline().strip().split(',')
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
                                    row.extend([''] * (header_count - len(row)))
                                elif len(row) > header_count:
                                    row = row[:header_count]
                                normalized_group.append(row)
                                
                            df = pd.DataFrame(normalized_group, columns=header)
                            df = df.dropna(how='all')  # Remove completely empty rows
                            groups[group_index] = df
                            group_index += 1
                            current_group = []
                        blank_line_count = 0
                else:
                    blank_line_count = 0
                    row = line.strip().split(',')
                    if any(cell.strip() for cell in row):  # Skip empty rows
                        current_group.append(row)
            
            # Don't forget the last group
            if current_group:
                # Apply same normalization to last group
                normalized_group = []
                for row in current_group:
                    if len(row) < header_count:
                        row.extend([''] * (header_count - len(row)))
                    elif len(row) > header_count:
                        row = row[:header_count]
                    normalized_group.append(row)
                    
                df = pd.DataFrame(normalized_group, columns=header)
                df = df.dropna(how='all')
                groups[group_index] = df
        # print(current_group) # Removed debug print
        return groups
    except Exception as e:
        logging.error(f"Error splitting CSV into groups: {e}")
        return {}

def display_npc_groups(filename: str = "data/npcs.csv"):
    """
    Display NPC groups from the CSV file.
    
    Args:
        filename (str): Path to the CSV file
    """
    groups = split_csv_groups(filename)
    
    if not groups:
        print("No groups found in the CSV file.")
        return
        
    for idx, group_df in groups.items():
        print(f"\n=== Group {idx + 1} ===")
        print(group_df[['NPC', 'ROLE', 'COMPANY']].to_string(index=False))
        print("\n" + "-" * 40)
#endregion

#region JSON
def load_large_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            objects = ijson.items(file, 'item')
            for obj in objects:
                print(obj)
    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
    except ijson.JSONError:
        print(f"Error: The file {file_path} is not a valid JSON file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
# Example usage
#file_path = 'large_data.json'
#load_large_json_file(file_path)

#endregion

#region Main Execution
def start_gui()->None:
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

def main():
    # Configure logging with both file and console output
    logging.basicConfig(
        filename='output.txt',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='w',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # Add console handler with same formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)
    try:
        # Ensure required directories exist
        for directory in [INPUT_DIR, OUTPUT_DIR, DATA_DIR]:
            directory.mkdir(exist_ok=True)
        # Define jobs to run
        jobs = [
            #("Image Processing", job1),
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
    
#endregion

#region Documentation
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
#endregion

