#!/usr/bin/env python3
# These .png files are to be 'CUT' into individual picture files
# Each shape is recorded in a text file of Name, x, y, width, height

import csv
import os
import pandas as pd
from PIL import Image, ImageDraw
import logging
import tkinter as tk # Add this import
from gui import CrewGUI # Add this import

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

def main():
    logger.info("Main application script started.")
    
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


