import csv
import logging
import os
from datetime import datetime
from typing import List, Optional, Union

from PIL import Image

from file_utils import read_csv_pandas, read_excel

logger = logging.getLogger(__name__)


def log_progress_md(message: str):
    """Append a timestamped Markdown progress entry to progress.md."""
    entry = f"### {datetime.now().isoformat()}\n- {message}\n\n"
    try:
        with open("progress.md", "a", encoding="utf-8") as handle:
            handle.write(entry)
        logger.info("[PROGRESS] %s", message)
    except OSError as exc:
        logger.error("Failed to append progress entry: %s", exc)
        try:
            import Crew as crew_module

            crew_module.Crew.logger.error("Failed to append progress entry: %s", exc)
        except Exception:
            pass


def show_user_error(message: str):
    """
    Display or log a user-facing error message (placeholder).
    """
    logger.error(f"[USER ERROR] {message}")


def spacer():
    """
    Print or log a visual spacer (placeholder).
    """
    print("-" * 40)


def process_csv_data(csv_file_path: str):
    """
    Example processing for CSV data.
    """
    logger.info(f"Processing CSV data from: {csv_file_path}")
    df = read_csv_pandas(csv_file_path)
    if df is not None:
        print(f"CSV Data from {csv_file_path}:")
        print(df.head())
    else:
        print(f"Could not read CSV data from {csv_file_path}.")


def process_excel_data(excel_file_path: str, sheet_name: Union[str, int, None] = 0):
    """
    Example processing for Excel data.
    """
    logger.info(f"Processing Excel data from: {excel_file_path}")
    df = read_excel(excel_file_path, sheet_name=sheet_name)
    if df is not None:
        print(f"Excel Data from {excel_file_path} (Sheet: {sheet_name or 'first'}):")
        print(df.head())
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

            save_kwargs = (
                _build_save_kwargs(ext, quality)
                if "_build_save_kwargs" in globals()
                else {}
            )
            try:
                cropped.save(output_path, **save_kwargs)
                saved_paths.append(output_path)
            except Exception as exc:
                logger.error("Failed to save crop for %s: %s", name, exc, exc_info=True)

    logger.info("Saved %d cropped regions to %s", len(saved_paths), output_directory)
    return saved_paths
