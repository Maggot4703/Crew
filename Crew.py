#!/usr/bin/env python3
"""
Crew main script: image processing and crew management application.

Usage:

Run without a command to start the GUI:
    python Crew.py

Run with a command for CLI mode:
    python Crew.py --help
    python Crew.py grid-image --image-path <path> --output-path <path>
    python Crew.py grid-folder --image-dir <dir> --output-dir <dir>
    python Crew.py read-csv --csv-path <path>
    python Crew.py read-excel --excel-path <path> [--sheet <name>]
    python Crew.py crop-csv --image-path <path> \
        --annotations-csv <path> --output-dir <dir>

Notes:
- Default grid size is 42x32.
- Logs are written to crew_app.log.
"""

# Utility functions moved to utils.py
import csv
import importlib
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from PIL import Image

from utils import log_progress_md, show_user_error, spacer

# Local imports (absolute only)
try:
    from image_utils import (
        DEFAULT_GRID_COLOR,
        DEFAULT_GRID_SIZE,
        DEFAULT_LINE_COLOR,
        IMAGE_DIMENSIONS,
        _resolve_color,
    )
except ImportError as e:
    raise ImportError(
        "Failed to import image_utils. Ensure it is in the PYTHONPATH."
    ) from e

# --- Utility Functions ---

logger = logging.getLogger(__name__)

# --- Dependency Auto-Installer ---
REQUIRED_PACKAGES = [
    ("PIL", "pillow"),
    ("pandas", "pandas"),
    ("speech_recognition", "SpeechRecognition"),
    ("tkinter", None),  # tkinter is standard in most Python installs
]


def _auto_install_deps() -> None:
    """Attempt to auto-install required dependencies if missing."""
    for mod, pip_name in REQUIRED_PACKAGES:
        if mod == "tkinter":
            try:
                importlib.import_module("tkinter")
            except ImportError:
                logger.error(
                    "tkinter is not installed. Please install the "
                    "python3-tk package via your system package manager."
                )
                show_user_error(
                    "tkinter is not installed. Please install the "
                    "python3-tk package via your system package manager."
                )
                sys.exit(1)
            continue
        try:
            importlib.import_module(mod)
        except ImportError:
            if pip_name:
                try:
                    subprocess.check_call(["python3", "-m", "pip", "install", pip_name])
                    logger.info(f"Auto-installed missing dependency: {pip_name}")
                except Exception as e:
                    logger.error(f"Failed to auto-install {pip_name}: {e}")
            else:

                logger.warning(f"Dependency {mod} not found and no pip name provided.")


# These .png files are to be 'CUT' into individual picture files
# Each shape is recorded in a text file of Name, x, y, width, height


# Base Constants
WIDTH = 1920
HEIGHT = 1080
REPO_ROOT = Path(__file__).resolve().parents[2]
CARDCUTTER_DIR = REPO_ROOT / "CARDCUTTER" / "CardCutter"
CARDCUTTER_INPUT_DIR = CARDCUTTER_DIR / "gimp"
CARDCUTTER_OUTPUT_DIR = CARDCUTTER_DIR
CARDCUTTER_RECTANGLES_DIR = CARDCUTTER_DIR / "Cars1_rectangles"
# Allow override via environment variables
INPUT_DIR = Path(os.environ.get("CREW_INPUT_DIR", str(CARDCUTTER_INPUT_DIR)))
OUTPUT_DIR = Path(os.environ.get("CREW_OUTPUT_DIR", str(CARDCUTTER_OUTPUT_DIR)))
IMAGE_FILES = [
    "Cars1.png",
    "Cars2.png",
    "Cars3.png",
    "Cars4.png",
    "Cars5.png",
    "Cars6.png",
    "Cars7.png",
]

# Ensure test constants are visible for import
__all__ = [
    "WIDTH",
    "HEIGHT",
    "INPUT_DIR",
    "OUTPUT_DIR",
    "IMAGE_FILES",
    "CARDCUTTER_DIR",
    "CARDCUTTER_INPUT_DIR",
    "CARDCUTTER_OUTPUT_DIR",
    "CARDCUTTER_RECTANGLES_DIR",
    "DEFAULT_GRID_COLOR",
    "DEFAULT_LINE_COLOR",
    "DEFAULT_GRID_SIZE",
    "IMAGE_DIMENSIONS",
]


# gridly
def mark_line(
    image: Optional["Image.Image"] = None,
    x1: int = 0,
    y1: int = 0,
    x2: int = 0,
    y2: int = 0,
    color: str = "red",
    thickness: int = 1,
) -> Optional["Image.Image"]:
    """
    Draw a line on the image using Pillow.
    Args:
        image: Existing image to draw on (optional, Pillow Image or None).
        x1 (int): Starting x-coordinate.
        y1 (int): Starting y-coordinate.
        x2 (int): Ending x-coordinate.
        y2 (int): Ending y-coordinate.
        color (str): Color of the line (default is red).
        thickness (int): Thickness of the line (default is 1).
    Returns:
        Optional[Image]: Image with the drawn line or None on error.
    """
    # Defer heavy import
    from PIL import Image, ImageDraw

    try:
        if image is None:
            # Create a new image if one isn't provided (example size)
            # This part might need adjustment based on typical use case
            logger.warning(
                "No image provided to mark_line, creating a default 200x200 "
                "white image."
            )
            image = Image.new("RGB", (200, 200), "white")
        draw = ImageDraw.Draw(image)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=thickness)
        logger.debug(
            f"Line drawn from ({x1},{y1}) to ({x2},{y2}) with color {color} "
            f"and thickness {thickness}."
        )
        return image
    except Exception as e:
        logger.error(f"Error in mark_line: {e}", exc_info=True)
        return None


# gridify
def overlay_grid(
    image_path: str,
    grid_color: str = "lightgrey",
    grid_size: tuple[int, int] = (42, 32),
    show_labels: bool = False,
) -> Optional["Image.Image"]:
    """
    Overlay a grid on top of an image.
    Args:
        image_path (str): Path to the input image.
        grid_color (str): Color of the grid lines (default is light gray).
        grid_size (tuple): (width, height) of grid cells.
        show_labels (bool): Whether to show row/column labels.
    Returns:
        Optional[Image]: Image with grid overlay or None on error.
    """
    # Defer heavy import
    from PIL import Image, ImageDraw

    try:
        if not image_path or not isinstance(image_path, str):
            show_user_error(
                "No image path provided. Please specify a valid image file."
            )
            return None
        if not isinstance(grid_size, tuple) or len(grid_size) != 2:
            show_user_error("Grid size must be a tuple of (width, height).")
            return None
        grid_width, grid_height = grid_size
        if not isinstance(grid_width, int) or not isinstance(grid_height, int):
            show_user_error("Grid size values must be integers.")
            return None
        if grid_width <= 0 or grid_height <= 0:
            show_user_error("Grid size values must be positive integers.")
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
        logger.info(
            f"Grid overlay applied to {image_path} with grid size " f"{grid_size}."
        )
        return img
    except FileNotFoundError:
        logger.error(f"Image file not found at {image_path} in overlay_grid.")
        show_user_error(
            "Image file not found: {}. Please check the file path and "
            "try again.".format(image_path)
        )
        return None
    except Exception as e:
        logger.error(f"Error in overlay_grid for {image_path}: {e}", exc_info=True)
        show_user_error(
            "Could not overlay grid on image. Please check your input and " "try again."
        )
        return None

def get_version() -> str:
    """
    Return the version of the Crew application.
    Returns:
        str: Version string.
    """
    return "1.0.0"


def get_project_info() -> dict:
    """
    Return project information as a dictionary.
    Returns:
        dict: Project metadata.
    """
    return {
        "name": "Crew",
        "version": get_version(),
        "description": "Image processing and crew management application",
        "author": "Crew Team",
        "license": "MIT",
        "python_version": (f"{sys.version_info.major}.{sys.version_info.minor}+"),
        "dependencies": ["PIL", "pandas", "tkinter"],
        "features": [
            "image_processing",
            "csv_handling",
            "grid_overlay",
            "cardcutter_integration",
            "gui",
        ],
    }


def main() -> None:
    import time

    start_time = time.perf_counter()
    # Centralized Logging Configuration (file + console)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    # File handler
    file_handler = logging.FileHandler("crew_app.log", mode="a")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.info("Main application script started.")
    log_progress_md("Started Crew main application script.")
    _auto_install_deps()
    # Import CLI parser and runner from cli.py (defer heavy imports)
    cli_import_start = time.perf_counter()
    try:
        from cli import create_cli_parser, run_cli
    except ImportError as e:
        raise ImportError(
            "Failed to import cli. Ensure it is in the PYTHONPATH."
        ) from e
    cli_import_end = time.perf_counter()
    logger.info(f"CLI import time: {cli_import_end - cli_import_start:.3f}s")
    parser = create_cli_parser()
    # Add CLI options for input/output dir
    parser.add_argument(
        "--input-dir",
        type=str,
        default=None,
        help="Input directory (overrides env CREW_INPUT_DIR)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (overrides env CREW_OUTPUT_DIR)",
    )
    parsed_args = parser.parse_args()
    global INPUT_DIR, OUTPUT_DIR
    if getattr(parsed_args, "input_dir", None):
        INPUT_DIR = Path(parsed_args.input_dir)
    if getattr(parsed_args, "output_dir", None):
        OUTPUT_DIR = Path(parsed_args.output_dir)
    if hasattr(parsed_args, "command") and parsed_args.command:
        # Defer heavy imports for CLI commands
        cli_run_start = time.perf_counter()
        result = run_cli(parsed_args)
        cli_run_end = time.perf_counter()
        logger.info(
            f"CLI command '{parsed_args.command}' completed in "
            f"{cli_run_end - cli_run_start:.3f}s with exit code {result}."
        )
        log_progress_md(
            f"CLI command '{parsed_args.command}' completed with "
            f"exit code {result}."
        )
        logger.info(f"Total startup time: {cli_run_end - start_time:.3f}s")
        raise SystemExit(result)
    # Start the GUI when no CLI command is provided
    gui_import_start = time.perf_counter()
    try:
        from gui import main_gui
    except ImportError as e:
        raise ImportError(
            "Failed to import gui. Ensure it is in the PYTHONPATH."
        ) from e
    gui_import_end = time.perf_counter()
    logger.info(f"GUI import time: {gui_import_end - gui_import_start:.3f}s")
    gui_start = time.perf_counter()
    main_gui()
    gui_end = time.perf_counter()
    logger.info(f"GUI startup time: {gui_end - gui_start:.3f}s")
    spacer()
    logger.info(
        f"Main application script finished. Total time: " f"{gui_end - start_time:.3f}s"
    )


if __name__ == "__main__":
    main()
