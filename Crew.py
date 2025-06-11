#!/usr/bin/env python3
# These .png files are to be 'CUT' into individual picture files
# Each shape is recorded in a text file of Name, x, y, width, height

import csv
import os
import pandas as pd
from PIL import Image, ImageDraw
import logging
import tkinter as tk # Add this import
import math

# Constants required by tests
DEFAULT_GRID_COLOR = 'lightgrey'
DEFAULT_LINE_COLOR = 'red'
DEFAULT_GRID_SIZE = (42, 32)  # Grid cell size (width, height)
IMAGE_DIMENSIONS = (800, 600)  # Default image dimensions (width, height)

# Setup logging
logging.basicConfig(
    level=logging.INFO, # Changed to INFO as DEBUG is verbose for general use
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='crew_app.log',
    filemode='a' # Append to log file
)
logger = logging.getLogger(__name__)

#gridly
def mark_line(image=None, x1: int = 0, y1: int = 0, x2: int = 0, y2: int = 0, color: str = 'red', thickness: int = 1):
    """
    Draw a line on the image using Pillow.
    :param image: Existing image to draw on (optional)
    :param x1: Starting x-coordinate
    :param y1: Starting y-coordinate
    :param x2: Ending x-coordinate
    :param y2: Ending y-coordinate
    :param color: Color of the line (default is red)
    :param thickness: Thickness of the line (default is 1)
    :return: Image with the drawn line or None on error
    """
    try:
        if image is None:
            # Create a new image if one isn't provided (example size)
            # This part might need adjustment based on typical use case
            logger.warning("No image provided to mark_line, creating a default 200x200 white image.")
            image = Image.new("RGB", (200, 200), "white") 
        draw = ImageDraw.Draw(image)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=thickness)
        logger.debug(f"Line drawn from ({x1},{y1}) to ({x2},{y2}) with color {color} and thickness {thickness}.")
        return image
    except Exception as e:
        logger.error(f"Error in mark_line: {e}", exc_info=True)
        return None

#gridify
def overlay_grid(image_path: str, grid_color: str = 'lightgrey', grid_size: tuple = (42,32)):
    """
    Overlay a grid on top of an image.
    :param image_path: Path to the input image
    :param grid_color: Color of the grid lines (default is light gray)
    :param grid_size: Tuple specifying the number of columns and rows in the grid (width, height of cell)
    :return: Image with grid overlay or None on error
    """
    try:
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        width, height = img.size
        grid_width, grid_height = grid_size

        # Draw vertical lines
        for x in range(0, width, grid_width):
            draw.line([(x, 0), (x, height)], fill=grid_color)

        # Draw horizontal lines
        for y in range(0, height, grid_height):
            draw.line([(0, y), (width, y)], fill=grid_color)
        
        logger.info(f"Grid overlay applied to {image_path} with grid size {grid_size}.")
        return img
    except FileNotFoundError:
        logger.error(f"Image file not found at {image_path} in overlay_grid.")
        return None
    except Exception as e:
        logger.error(f"Error in overlay_grid for {image_path}: {e}", exc_info=True)
        return None

#
def read_csv_builtin(filename: str) -> list:
    """
    Read CSV data using built-in csv module
    :param filename: Path to the CSV file
    :return: List of rows from CSV or empty list on error
    """
    if not filename or not isinstance(filename, str):
        logger.error("Invalid filename provided for read_csv_builtin.")
        return []
    
    data = []
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                data.append(row)
        logger.info(f"Successfully read {filename} using built-in csv module.")
        return data
    except FileNotFoundError:
        logger.error(f"CSV file not found: {filename}")
        return []
    except Exception as e:
        logger.error(f"Error reading CSV file {filename} with built-in csv: {e}", exc_info=True)
        return []

#
def read_csv_pandas(filename: str):
    """
    Read CSV data using pandas
    :param filename: Path to the CSV file
    :return: Pandas DataFrame containing CSV data or None on error
    """
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
        return pd.DataFrame() # Return empty DataFrame for empty files
    except Exception as e:
        logger.error(f"Error reading CSV file {filename} with pandas: {e}", exc_info=True)
        return None

#
def read_excel(filename: str, sheet_name: str = None):
    """
    Read Excel data using pandas
    :param filename: Path to the Excel file (.xlsx or .xls)
    :param sheet_name: Name of the sheet to read (default is first sheet)
    :return: Pandas DataFrame containing Excel data or None on error
    """
    if not filename or not isinstance(filename, str):
        logger.error("Invalid filename provided for read_excel.")
        return None
    
    try:
        df = pd.read_excel(filename, sheet_name=sheet_name)
        logger.info(f"Successfully read {filename} (sheet: {sheet_name or 'first'}) using pandas.")
        return df
    except FileNotFoundError:
        logger.error(f"Excel file not found: {filename}")
        return None
    except Exception as e:
        logger.error(f"Error reading Excel file {filename}: {e}", exc_info=True)
        return None

#
def spacer():
    logger.info("Spacer function called - typically for separating output or logical sections.")
    print("\n" + "-"*20 + "\n")

#gridify scans
def process_images(image_directory: str, output_directory: str, grid_size: tuple = (42,32)):
    """
    Processes all images in a directory to overlay a grid and saves them.
    Assumes images are .png, .jpg, .jpeg. 
    """
    # Implementation would involve os.listdir, checking file extensions,
    # calling overlay_grid, and saving the modified image (e.g., img.save()).
    logger.info(f"Starting image processing for directory: {image_directory}")
    # Placeholder - full implementation needed
    pass
    

#csv
def process_csv_data(csv_file_path: str):
    """
    Example processing for CSV data.
    """
    logger.info(f"Processing CSV data from: {csv_file_path}")
    df = read_csv_pandas(csv_file_path)
    if df is not None:
        # Example: Print some info about the DataFrame
        print(f"CSV Data from {csv_file_path}:")
        print(df.head())
        # Further processing...
    else:
        print(f"Could not read CSV data from {csv_file_path}.")

#xls
def process_excel_data(excel_file_path: str, sheet_name: str = None):
    """
    Example processing for Excel data.
    """
    logger.info(f"Processing Excel data from: {excel_file_path}")
    df = read_excel(excel_file_path, sheet_name=sheet_name)
    if df is not None:
        # Example: Print some info about the DataFrame
        print(f"Excel Data from {excel_file_path} (Sheet: {sheet_name or 'first'}):")
        print(df.head())
        # Further processing...
    else:
        print(f"Could not read Excel data from {excel_file_path}.")

#???
def job4():
    logger.info("job4 called - specific task to be defined.")
    # Placeholder for a specific task
    pass

def get_version():
    """Return the version of the Crew application."""
    return "1.0.0"

def get_project_info():
    """
    Return project information as a dictionary.
    :return: Dictionary containing project metadata
    """
    return {
        'name': 'Crew',
        'version': get_version(),
        'description': 'Image processing and crew management application',
        'author': 'Crew Team',
        'license': 'MIT',
        'python_version': '3.11+',
        'dependencies': ['PIL', 'pandas', 'tkinter'],
        'features': ['image_processing', 'csv_handling', 'grid_overlay', 'gui']
    }

def read_file(filename: str, encoding: str = 'utf-8') -> str:
    """
    Read the contents of a text file.
    :param filename: Path to the file to read
    :param encoding: File encoding (default: utf-8)
    :return: File contents as string or empty string on error
    """
    if not filename or not isinstance(filename, str):
        logger.error("Invalid filename provided for read_file.")
        return ""
    
    try:
        with open(filename, 'r', encoding=encoding) as file:
            content = file.read()
        logger.info(f"Successfully read file: {filename}")
        return content
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        return ""
    except UnicodeDecodeError as e:
        logger.error(f"Unicode decode error reading {filename}: {e}")
        return ""
    except Exception as e:
        logger.error(f"Error reading file {filename}: {e}", exc_info=True)
        return ""

def calculate_hexagon_points(center_x: float, center_y: float, radius: float) -> list:
    """
    Calculate the points of a regular hexagon given center and radius.
    :param center_x: X coordinate of the center
    :param center_y: Y coordinate of the center  
    :param radius: Radius of the hexagon
    :return: List of (x, y) tuples representing hexagon vertices
    """
    try:
        points = []
        for i in range(6):
            angle = math.pi * i / 3  # 60 degrees in radians
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            points.append((x, y))
        logger.debug(f"Calculated hexagon points for center ({center_x}, {center_y}) with radius {radius}")
        return points
    except Exception as e:
        logger.error(f"Error calculating hexagon points: {e}", exc_info=True)
        return []

def hex_to_rgb(hex_color: str) -> tuple:
    """
    Convert hexadecimal color to RGB tuple.
    :param hex_color: Hex color string (e.g., '#FF0000' or 'FF0000')
    :return: RGB tuple (r, g, b) or (0, 0, 0) on error
    """
    try:
        # Remove '#' if present
        hex_color = hex_color.lstrip('#')
        
        # Validate hex color format
        if len(hex_color) != 6:
            raise ValueError(f"Invalid hex color length: {hex_color}")
        
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        logger.debug(f"Converted hex {hex_color} to RGB ({r}, {g}, {b})")
        return (r, g, b)
    except ValueError as e:
        logger.error(f"Invalid hex color format '{hex_color}': {e}")
        return (0, 0, 0)
    except Exception as e:
        logger.error(f"Error converting hex to RGB '{hex_color}': {e}", exc_info=True)
        return (0, 0, 0)

def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Convert RGB values to hexadecimal color string.
    :param r: Red component (0-255)
    :param g: Green component (0-255)  
    :param b: Blue component (0-255)
    :return: Hex color string (e.g., '#FF0000') or '#000000' on error
    """
    try:
        # Validate RGB values
        if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
            raise ValueError(f"RGB values must be 0-255: ({r}, {g}, {b})")
        
        hex_color = f"#{r:02X}{g:02X}{b:02X}"
        logger.debug(f"Converted RGB ({r}, {g}, {b}) to hex {hex_color}")
        return hex_color
    except ValueError as e:
        logger.error(f"Invalid RGB values ({r}, {g}, {b}): {e}")
        return "#000000"
    except Exception as e:
        logger.error(f"Error converting RGB to hex ({r}, {g}, {b}): {e}", exc_info=True)
        return "#000000"

def markHorizontalLine(x1: int, y1: int, x2: int, y2: int, color: str = 'red', thickness: int = 1):
    """
    Create a new image with a line marked on it (test-compatible function).
    :param x1: Starting x-coordinate
    :param y1: Starting y-coordinate
    :param x2: Ending x-coordinate
    :param y2: Ending y-coordinate
    :param color: Color of the line (default is red)
    :param thickness: Thickness of the line (default is 1)
    :return: Image with the drawn line
    """
    try:
        # Create a new image with default dimensions
        image = Image.new("RGB", IMAGE_DIMENSIONS, "white")
        return mark_line(image, x1, y1, x2, y2, color, thickness)
    except Exception as e:
        logger.error(f"Error in markHorizontalLine: {e}", exc_info=True)
        return None

def overlayGrid(image_path: str, grid_color: str = DEFAULT_GRID_COLOR, grid_size: tuple = DEFAULT_GRID_SIZE):
    """
    Overlay a grid on an image (test-compatible function).
    :param image_path: Path to the input image
    :param grid_color: Color of the grid lines
    :param grid_size: Tuple specifying the grid cell size (width, height)
    :return: Image with grid overlay
    """
    return overlay_grid(image_path, grid_color, grid_size)

def main():
    logger.info("Main application script started.")
    
    # Import GUI locally to avoid circular import
    from gui import CrewGUI
    
    # Start the GUI
    root = tk.Tk()
    app = CrewGUI(root)
    root.mainloop()

    # Example usage (replace with actual logic or CLI argument parsing)
    # Image processing example
    # Note: Ensure image_path and output_path are valid
    #test_image_path = "path/to/your/image.png" 
    #output_image_path = "path/to/your/output_image.png"
    #if os.path.exists(test_image_path):
    #    grid_image = overlay_grid(test_image_path, grid_size=(50,50))
    #    if grid_image:
    #        grid_image.save(output_image_path)
    #        logger.info(f"Saved gridded image to {output_image_path}")
    #else:
    #    logger.warning(f"Test image {test_image_path} not found, skipping overlay example.")

    # CSV processing example
    # sample_csv = "sample_crew_data.csv" # Assuming this file exists in the script's directory or a known path
    # if os.path.exists(sample_csv):
    #     process_csv_data(sample_csv)
    # else:
    #     logger.warning(f"Sample CSV {sample_csv} not found, skipping CSV processing example.")

    # Excel processing example
    # sample_excel = "sample_crew_data.xlsx" # Assuming this file exists
    # if os.path.exists(sample_excel):
    #     process_excel_data(sample_excel)
    # else:
    #     logger.warning(f"Sample Excel {sample_excel} not found, skipping Excel processing example.")
    
    spacer()
    logger.info("Main application script finished.")

if __name__ == "__main__":
    # It's good practice to add os.path checks for file paths used in main or provide them via args
    # For now, main() is mostly illustrative.
    # Consider using argparse for command-line arguments to specify files and operations.
    main()


