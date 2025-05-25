"""
Utility script to convert BMP image files to PNG format.

This script likely iterates through a specified directory (or a list of files),
reads BMP images, and saves them as PNG files, possibly in a different
directory or with a modified filename.
"""

import glob
import os

# Import necessary libraries
from PIL import Image

# --- Configuration ---
INPUT_BMP_DIR = "input_bmps/"  # Directory containing BMP files
OUTPUT_PNG_DIR = "output_pngs/"  # Directory to save converted PNG files
DEFAULT_BMP_FILE = (
    "default.bmp"  # A default BMP file to convert if no specific one is given
)


def convert_bmp_to_png(bmp_filepath: str, png_filepath: str) -> bool:
    """
    Convert a single BMP image file to PNG format.

    Args:
        bmp_filepath (str): The full path to the input BMP file.
        png_filepath (str): The full path to save the output PNG file.

    Returns:
        bool: True if conversion was successful, False otherwise.
    """
    try:
        img = Image.open(bmp_filepath)
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(png_filepath), exist_ok=True)
        img.save(png_filepath, "PNG")
        print(f"Successfully converted '{bmp_filepath}' to '{png_filepath}'")
        return True
    except FileNotFoundError:
        print(f"Error: BMP file not found at '{bmp_filepath}'")
        return False
    except IOError as e:
        print(f"Error converting '{bmp_filepath}': {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred with '{bmp_filepath}': {e}")
        return False


def batch_convert_bmps_in_directory(input_dir: str, output_dir: str):
    """
    Convert all BMP files in a given directory to PNG format.

    PNG files are saved in the specified output directory with the same base name.

    Args:
        input_dir (str): Path to the directory containing BMP files.
        output_dir (str): Path to the directory where PNG files will be saved.
    """
    if not os.path.isdir(input_dir):
        print(f"Error: Input directory '{input_dir}' not found.")
        return

    os.makedirs(output_dir, exist_ok=True)

    bmp_files = glob.glob(os.path.join(input_dir, "*.bmp"))
    if not bmp_files:
        print(f"No BMP files found in '{input_dir}'.")
        return

    success_count = 0
    failure_count = 0
    for bmp_file in bmp_files:
        base_name = os.path.basename(bmp_file)
        png_name = os.path.splitext(base_name)[0] + ".png"
        png_filepath = os.path.join(output_dir, png_name)
        if convert_bmp_to_png(bmp_file, png_filepath):
            success_count += 1
        else:
            failure_count += 1

    print(
        f"Batch conversion complete. {success_count} successful, {failure_count} failed."
    )


# Example Usage (if this script were to be run directly):
if __name__ == "__main__":
    print("BMP to PNG Conversion Script")

    # --- Option 1: Convert a single file ---
    bmp_input_file = "path/to/your/image.bmp"  # Replace with actual path
    png_output_file = "path/to/your/converted_image.png"  # Replace with actual path
    if os.path.exists(bmp_input_file):
        convert_bmp_to_png(bmp_input_file, png_output_file)
    else:
        print(f"Single file for conversion not found: {bmp_input_file}")
        # Example: Convert a default file if it exists
        if os.path.exists(DEFAULT_BMP_FILE):
            print(f"Attempting to convert default file: {DEFAULT_BMP_FILE}")
            convert_bmp_to_png(DEFAULT_BMP_FILE, "default_converted.png")
        else:
            print(f"Default BMP file '{DEFAULT_BMP_FILE}' also not found.")

    # --- Option 2: Batch convert a directory ---
    input_directory = INPUT_BMP_DIR
    output_directory = OUTPUT_PNG_DIR
    print(
        f"Attempting batch conversion from '{input_directory}' to '{output_directory}'"
    )
    batch_convert_bmps_in_directory(input_directory, output_directory)

    # --- Simplified Example for when script is run directly ---
    # Create dummy files/dirs for placeholder execution if they don't exist
    dummy_input_dir = "dummy_bmps"
    dummy_output_dir = "dummy_pngs"
    os.makedirs(dummy_input_dir, exist_ok=True)
    # Create a dummy BMP file for testing
    if not os.path.exists(os.path.join(dummy_input_dir, "test.bmp")):
        try:
            # Create a minimal valid BMP manually or copy a small one
            # For simplicity, we'll just create an empty file as a placeholder for the placeholder
            with open(os.path.join(dummy_input_dir, "test.bmp"), "wb") as f:
                # A very basic BMP header (1x1 pixel, 24-bit)
                # This is just for the file to exist, PIL would need a real BMP
                f.write(
                    b"BM\x3e\x00\x00\x00\x00\x00\x00\x00\x36\x00\x00\x00\x28\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x18\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00"
                )  # Blue pixel
            with open(os.path.join(dummy_input_dir, "error_test.bmp"), "w") as f:
                f.write("This is not a BMP")  # To simulate an error
            print(f"Created dummy BMP files in '{dummy_input_dir}'")
        except Exception as e:
            print(f"Could not create dummy BMP for testing: {e}")

    batch_convert_bmps_in_directory(dummy_input_dir, dummy_output_dir)

    # For the script to be runnable as is with placeholders:
    print("\nRunning placeholder conversion for a single file:")
    convert_bmp_to_png("example.bmp", "example.png")
    convert_bmp_to_png("example_error.bmp", "example_error.png")  # Simulate error

    print("\nRunning placeholder batch conversion:")
    # Need to ensure os is imported if using os.path.join in main for placeholders
    import os

    batch_convert_bmps_in_directory("placeholder_input_bmps", "placeholder_output_pngs")

    print("\nScript execution finished.")
