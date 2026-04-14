#!/usr/bin/env python3
# These .png files are to be 'CUT' into individual picture files
# Each shape is recorded in a text file of Name, x, y, width, height

"""Crew script usage instructions.

Run without a command to start the GUI:
    python Crew.py

Run with a command for CLI mode:
    python Crew.py --help
    python Crew.py grid-image --image-path <path> --output-path <path>
    python Crew.py grid-folder --image-dir <dir> --output-dir <dir>
    python Crew.py read-csv --csv-path <path>
    python Crew.py read-excel --excel-path <path> [--sheet <name>]
    python Crew.py crop-csv --image-path <path> --annotations-csv <path> --output-dir <dir>

Notes:
- Default grid size is 42x32.
- Logs are written to crew_app.log.
"""

import csv
import os
import pandas as pd
from PIL import Image, ImageDraw
import logging
import tkinter as tk  # Add this import
import math
import argparse
from typing import Any, List, Optional, Union
from PIL import ImageColor

# Constants required by tests
DEFAULT_GRID_COLOR = "lightgrey"
DEFAULT_LINE_COLOR = "red"
DEFAULT_GRID_SIZE = (42, 32)  # Grid cell size (width, height)
IMAGE_DIMENSIONS = (800, 600)  # Default image dimensions (width, height)

# Setup logging
logging.basicConfig(
    level=logging.INFO,  # Changed to INFO as DEBUG is verbose for general use
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="crew_app.log",
    filemode="a",  # Append to log file
)
logger = logging.getLogger(__name__)


# gridly
def mark_line(
    image=None,
    x1: int = 0,
    y1: int = 0,
    x2: int = 0,
    y2: int = 0,
    color: str = "red",
    thickness: int = 1,
):
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
            logger.warning(
                "No image provided to mark_line, creating a default 200x200 white image."
            )
            image = Image.new("RGB", (200, 200), "white")
        draw = ImageDraw.Draw(image)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=thickness)
        logger.debug(
            f"Line drawn from ({x1},{y1}) to ({x2},{y2}) with color {color} and thickness {thickness}."
        )
        return image
    except Exception as e:
        logger.error(f"Error in mark_line: {e}", exc_info=True)
        return None


# gridify
def overlay_grid(
    image_path: str,
    grid_color: str = "lightgrey",
    grid_size: tuple = (42, 32),
    show_labels: bool = False,
):
    """
    Overlay a grid on top of an image.
    :param image_path: Path to the input image
    :param grid_color: Color of the grid lines (default is light gray)
    :param grid_size: Tuple specifying the number of columns and rows in the grid (width, height of cell)
    :return: Image with grid overlay or None on error
    """
    try:
        if not image_path or not isinstance(image_path, str):
            logger.error("Invalid image path provided to overlay_grid.")
            return None

        if not isinstance(grid_size, tuple) or len(grid_size) != 2:
            logger.error("Invalid grid_size. Expected tuple(width, height).")
            return None

        grid_width, grid_height = grid_size
        if not isinstance(grid_width, int) or not isinstance(grid_height, int):
            logger.error("grid_size values must be integers.")
            return None
        if grid_width <= 0 or grid_height <= 0:
            logger.error("grid_size values must be > 0.")
            return None

        color_value = _resolve_color(grid_color)

        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        width, height = img.size

        # Draw vertical lines
        for x in range(0, width, grid_width):
            draw.line([(x, 0), (x, height)], fill=color_value)

        # Draw horizontal lines
        for y in range(0, height, grid_height):
            draw.line([(0, y), (width, y)], fill=color_value)

        if show_labels:
            for idx, x in enumerate(range(0, width, grid_width)):
                draw.text((x + 2, 2), f"C{idx}", fill=color_value)
            for idx, y in enumerate(range(0, height, grid_height)):
                draw.text((2, y + 2), f"R{idx}", fill=color_value)

        logger.info(f"Grid overlay applied to {image_path} with grid size {grid_size}.")
        return img
    except FileNotFoundError:
        logger.error(f"Image file not found at {image_path} in overlay_grid.")
        return None
    except Exception as e:
        logger.error(f"Error in overlay_grid for {image_path}: {e}", exc_info=True)
        return None


# csv read helpers
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


# csv/pandas read helper
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
        return pd.DataFrame()  # Return empty DataFrame for empty files
    except Exception as e:
        logger.error(
            f"Error reading CSV file {filename} with pandas: {e}", exc_info=True
        )
        return None


# excel read helper
def read_excel(filename: str, sheet_name: Union[str, int, None] = 0):
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


# spacer helper
def spacer():
    logger.info(
        "Spacer function called - typically for separating output or logical sections."
    )
    print("\n" + "-" * 20 + "\n")


# gridify scans
def process_images(
    image_directory: str,
    output_directory: str,
    grid_size: tuple = (42, 32),
    grid_color: str = DEFAULT_GRID_COLOR,
    show_labels: bool = False,
    output_format: Optional[str] = None,
    quality: int = 95,
) -> List[str]:
    """
    Processes all images in a directory to overlay a grid and saves them.
    Assumes images are .png, .jpg, .jpeg.
    """
    logger.info(f"Starting image processing for directory: {image_directory}")
    saved_paths: List[str] = []

    if not os.path.isdir(image_directory):
        logger.error("Input directory not found: %s", image_directory)
        return saved_paths

    if quality < 1 or quality > 100:
        logger.warning("Invalid quality %s; using 95.", quality)
        quality = 95

    os.makedirs(output_directory, exist_ok=True)
    supported_extensions = {".png", ".jpg", ".jpeg"}

    for filename in sorted(os.listdir(image_directory)):
        source_path = os.path.join(image_directory, filename)
        if not os.path.isfile(source_path):
            continue

        base_name, ext = os.path.splitext(filename)
        if ext.lower() not in supported_extensions:
            continue

        image = overlay_grid(
            source_path,
            grid_color=grid_color,
            grid_size=grid_size,
            show_labels=show_labels,
        )
        if image is None:
            logger.warning("Skipping image due to processing error: %s", source_path)
            continue

        save_ext = ext.lower()
        if output_format:
            save_ext = f".{output_format.lower().lstrip('.')}"

        output_filename = f"{base_name}_grid{save_ext}"
        output_path = os.path.join(output_directory, output_filename)

        save_kwargs = _build_save_kwargs(save_ext, quality)
        try:
            image.save(output_path, **save_kwargs)
            saved_paths.append(output_path)
        except Exception as exc:
            logger.error(
                "Failed to save output image %s: %s", output_path, exc, exc_info=True
            )

    logger.info("Processed %d images into %s", len(saved_paths), output_directory)
    return saved_paths


# csv
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


# xls
def process_excel_data(excel_file_path: str, sheet_name: Union[str, int, None] = 0):
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


def crop_from_annotations(
    image_path: str,
    annotations_csv: str,
    output_directory: str,
    output_format: Optional[str] = None,
    quality: int = 95,
) -> List[str]:
    """
    Crop image regions using CSV rows in format: name,x,y,width,height.
    Invalid rows are skipped and logged as warnings.
    """
    saved_paths: List[str] = []

    if not os.path.isfile(image_path):
        logger.error("Image file not found: %s", image_path)
        return saved_paths
    if not os.path.isfile(annotations_csv):
        logger.error("Annotations CSV not found: %s", annotations_csv)
        return saved_paths

    os.makedirs(output_directory, exist_ok=True)
    if quality < 1 or quality > 100:
        logger.warning("Invalid quality %s; using 95.", quality)
        quality = 95

    try:
        source_image = Image.open(image_path)
    except Exception as exc:
        logger.error(
            "Failed to open source image %s: %s", image_path, exc, exc_info=True
        )
        return saved_paths

    image_width, image_height = source_image.size

    with open(annotations_csv, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row_number, row in enumerate(reader, start=2):
            name = (row.get("name") or "").strip()
            if not name:
                logger.warning("Skipping row %d: missing name", row_number)
                continue

            try:
                x = int(row.get("x", ""))
                y = int(row.get("y", ""))
                width = int(row.get("width", ""))
                height = int(row.get("height", ""))
            except ValueError:
                logger.warning(
                    "Skipping row %d (%s): invalid numeric values", row_number, name
                )
                continue

            if width <= 0 or height <= 0:
                logger.warning(
                    "Skipping row %d (%s): width/height must be > 0", row_number, name
                )
                continue
            if x < 0 or y < 0:
                logger.warning(
                    "Skipping row %d (%s): x/y cannot be negative", row_number, name
                )
                continue

            x2 = x + width
            y2 = y + height
            if x2 > image_width or y2 > image_height:
                logger.warning(
                    "Skipping row %d (%s): crop outside bounds (%s, %s)",
                    row_number,
                    name,
                    image_width,
                    image_height,
                )
                continue

            cropped = source_image.crop((x, y, x2, y2))
            ext = f".{output_format.lower().lstrip('.')}" if output_format else ".png"
            output_path = os.path.join(output_directory, f"{name}{ext}")

            save_kwargs = _build_save_kwargs(ext, quality)
            try:
                cropped.save(output_path, **save_kwargs)
                saved_paths.append(output_path)
            except Exception as exc:
                logger.error("Failed to save crop for %s: %s", name, exc, exc_info=True)

    logger.info("Saved %d cropped regions to %s", len(saved_paths), output_directory)
    return saved_paths


# placeholder job
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
        "name": "Crew",
        "version": get_version(),
        "description": "Image processing and crew management application",
        "author": "Crew Team",
        "license": "MIT",
        "python_version": "3.11+",
        "dependencies": ["PIL", "pandas", "tkinter"],
        "features": ["image_processing", "csv_handling", "grid_overlay", "gui"],
    }


def read_file(filename: str, encoding: str = "utf-8") -> str:
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
        with open(filename, "r", encoding=encoding) as file:
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
        logger.debug(
            f"Calculated hexagon points for center ({center_x}, {center_y}) with radius {radius}"
        )
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
        if not isinstance(hex_color, str) or not hex_color.strip():
            raise ValueError("Color value must be a non-empty string")

        color_value = hex_color.strip()
        if color_value.startswith("#") and len(color_value) == 4:
            color_value = (
                "#" + color_value[1] * 2 + color_value[2] * 2 + color_value[3] * 2
            )

        # ImageColor handles named colors and #RRGGBB.
        r, g, b = ImageColor.getrgb(color_value)

        logger.debug(f"Converted hex {hex_color} to RGB ({r}, {g}, {b})")
        return (r, g, b)
    except ValueError as e:
        logger.error(f"Invalid hex color format '{hex_color}': {e}")
        return (0, 0, 0)
    except Exception as e:
        logger.error(f"Error converting hex to RGB '{hex_color}': {e}", exc_info=True)
        return (0, 0, 0)


def rgb_to_hex(r: int, g: Optional[int] = None, b: Optional[int] = None) -> str:
    """
    Convert RGB values to hexadecimal color string.
    :param r: Red component (0-255)
    :param g: Green component (0-255)
    :param b: Blue component (0-255)
    :return: Hex color string (e.g., '#FF0000') or '#000000' on error
    """
    try:
        if isinstance(r, tuple) and len(r) == 3:
            r, g, b = r

        if g is None or b is None:
            raise ValueError("RGB values are required")

        # Validate RGB values
        if not (0 <= int(r) <= 255 and 0 <= int(g) <= 255 and 0 <= int(b) <= 255):
            raise ValueError(f"RGB values must be 0-255: ({r}, {g}, {b})")

        hex_color = f"#{int(r):02X}{int(g):02X}{int(b):02X}"
        logger.debug(f"Converted RGB ({r}, {g}, {b}) to hex {hex_color}")
        return hex_color
    except ValueError as e:
        logger.error(f"Invalid RGB values ({r}, {g}, {b}): {e}")
        return "#000000"
    except Exception as e:
        logger.error(f"Error converting RGB to hex ({r}, {g}, {b}): {e}", exc_info=True)
        return "#000000"


def markHorizontalLine(
    x1: int, y1: int, x2: int, y2: int, color: str = "red", thickness: int = 1
):
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


def overlayGrid(
    image_path: str,
    grid_color: str = DEFAULT_GRID_COLOR,
    grid_size: tuple = DEFAULT_GRID_SIZE,
):
    """
    Overlay a grid on an image (test-compatible function).
    :param image_path: Path to the input image
    :param grid_color: Color of the grid lines
    :param grid_size: Tuple specifying the grid cell size (width, height)
    :return: Image with grid overlay
    """
    return overlay_grid(image_path, grid_color, grid_size)


def _resolve_color(color_value: Any) -> Any:
    """Resolve named colors and hex values to a Pillow-compatible color value."""
    if isinstance(color_value, tuple) and len(color_value) == 3:
        return color_value
    rgb = hex_to_rgb(color_value)
    return rgb


def _build_save_kwargs(extension: str, quality: int) -> dict:
    """Build image save options based on extension."""
    ext = extension.lower().lstrip(".")
    if ext in {"jpg", "jpeg", "webp"}:
        return {"quality": quality}
    return {}


def create_cli_parser() -> argparse.ArgumentParser:
    """Create CLI parser for Crew utility commands."""
    parser = argparse.ArgumentParser(description="Crew utility CLI")
    subparsers = parser.add_subparsers(dest="command")

    grid_image = subparsers.add_parser("grid-image", help="Overlay a grid on one image")
    grid_image.add_argument("image_path")
    grid_image.add_argument("output_path")
    grid_image.add_argument("--grid-width", type=int, default=DEFAULT_GRID_SIZE[0])
    grid_image.add_argument("--grid-height", type=int, default=DEFAULT_GRID_SIZE[1])
    grid_image.add_argument("--grid-color", default=DEFAULT_GRID_COLOR)
    grid_image.add_argument("--labels", action="store_true")
    grid_image.add_argument("--output-format", choices=["png", "jpg", "jpeg", "webp"])
    grid_image.add_argument("--quality", type=int, default=95)

    grid_folder = subparsers.add_parser(
        "grid-folder", help="Overlay a grid for all images in a folder"
    )
    grid_folder.add_argument("input_dir")
    grid_folder.add_argument("output_dir")
    grid_folder.add_argument("--grid-width", type=int, default=DEFAULT_GRID_SIZE[0])
    grid_folder.add_argument("--grid-height", type=int, default=DEFAULT_GRID_SIZE[1])
    grid_folder.add_argument("--grid-color", default=DEFAULT_GRID_COLOR)
    grid_folder.add_argument("--labels", action="store_true")
    grid_folder.add_argument("--output-format", choices=["png", "jpg", "jpeg", "webp"])
    grid_folder.add_argument("--quality", type=int, default=95)

    read_csv_cmd = subparsers.add_parser("read-csv", help="Read CSV and print preview")
    read_csv_cmd.add_argument("csv_path")

    read_excel_cmd = subparsers.add_parser(
        "read-excel", help="Read Excel and print preview"
    )
    read_excel_cmd.add_argument("excel_path")
    read_excel_cmd.add_argument("--sheet")

    crop_csv = subparsers.add_parser(
        "crop-csv",
        help="Crop image regions from CSV annotations with columns name,x,y,width,height",
    )
    crop_csv.add_argument("image_path")
    crop_csv.add_argument("annotations_csv")
    crop_csv.add_argument("output_dir")
    crop_csv.add_argument("--output-format", choices=["png", "jpg", "jpeg", "webp"])
    crop_csv.add_argument("--quality", type=int, default=95)

    return parser


def run_cli(args: argparse.Namespace) -> int:
    """Run CLI command and return process exit code."""
    if args.command == "grid-image":
        image = overlay_grid(
            args.image_path,
            grid_color=args.grid_color,
            grid_size=(args.grid_width, args.grid_height),
            show_labels=args.labels,
        )
        if image is None:
            return 1

        extension = os.path.splitext(args.output_path)[1]
        if args.output_format:
            extension = f".{args.output_format}"
            args.output_path = os.path.splitext(args.output_path)[0] + extension

        save_kwargs = _build_save_kwargs(extension or ".png", args.quality)
        image.save(args.output_path, **save_kwargs)
        print(f"Saved: {args.output_path}")
        return 0

    if args.command == "grid-folder":
        saved = process_images(
            args.input_dir,
            args.output_dir,
            grid_size=(args.grid_width, args.grid_height),
            grid_color=args.grid_color,
            show_labels=args.labels,
            output_format=args.output_format,
            quality=args.quality,
        )
        print(f"Processed {len(saved)} file(s)")
        return 0 if saved else 1

    if args.command == "read-csv":
        process_csv_data(args.csv_path)
        return 0

    if args.command == "read-excel":
        process_excel_data(args.excel_path, sheet_name=args.sheet)
        return 0

    if args.command == "crop-csv":
        saved = crop_from_annotations(
            args.image_path,
            args.annotations_csv,
            args.output_dir,
            output_format=args.output_format,
            quality=args.quality,
        )
        print(f"Saved {len(saved)} crop(s)")
        return 0 if saved else 1

    return 1


def main():
    logger.info("Main application script started.")

    parser = create_cli_parser()
    parsed_args = parser.parse_args()

    if parsed_args.command:
        raise SystemExit(run_cli(parsed_args))

    # Import GUI locally to avoid circular import
    from gui import CrewGUI

    # Start the GUI when no CLI command is provided
    root = tk.Tk()
    CrewGUI(root)
    root.mainloop()

    # Example usage (replace with actual logic or CLI argument parsing)
    # Image processing example
    # Note: Ensure image_path and output_path are valid
    # test_image_path = "path/to/your/image.png"
    # output_image_path = "path/to/your/output_image.png"
    # if os.path.exists(test_image_path):
    #    grid_image = overlay_grid(test_image_path, grid_size=(50,50))
    #    if grid_image:
    #        grid_image.save(output_image_path)
    #        logger.info(f"Saved gridded image to {output_image_path}")
    # else:
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
    main()
