import os
import logging
from PIL import Image, ImageDraw, ImageColor
from typing import Any, List, Optional

DEFAULT_GRID_COLOR = "lightgrey"
DEFAULT_LINE_COLOR = "red"
DEFAULT_GRID_SIZE = (42, 32)
IMAGE_DIMENSIONS = (800, 600)

logger = logging.getLogger(__name__)

def mark_line(
    image=None,
    x1: int = 0,
    y1: int = 0,
    x2: int = 0,
    y2: int = 0,
    color: str = "red",
    thickness: int = 1,
):
    try:
        if image is None:
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

def overlay_grid(
    image_path: str,
    grid_color: str = DEFAULT_GRID_COLOR,
    grid_size: tuple = DEFAULT_GRID_SIZE,
    show_labels: bool = False,
):
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
        for x in range(0, width, grid_width):
            draw.line([(x, 0), (x, height)], fill=color_value)
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

def process_images(
    image_directory: str,
    output_directory: str,
    grid_size: tuple = DEFAULT_GRID_SIZE,
    grid_color: str = DEFAULT_GRID_COLOR,
    show_labels: bool = False,
    output_format: Optional[str] = None,
    quality: int = 95,
) -> List[str]:
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

def crop_from_annotations(
    image_path: str,
    annotations_csv: str,
    output_directory: str,
    output_format: Optional[str] = None,
    quality: int = 95,
) -> List[str]:
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
    import csv
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

def markHorizontalLine(
    x1: int, y1: int, x2: int, y2: int, color: str = "red", thickness: int = 1
):
    try:
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
    return overlay_grid(image_path, grid_color, grid_size)

def _resolve_color(color_value: Any) -> Any:
    if isinstance(color_value, tuple) and len(color_value) == 3:
        return color_value
    rgb = hex_to_rgb(color_value)
    return rgb

def _build_save_kwargs(extension: str, quality: int) -> dict:
    ext = extension.lower().lstrip(".")
    if ext in {"jpg", "jpeg", "webp"}:
        return {"quality": quality}
    return {}

def hex_to_rgb(hex_color: str) -> tuple:
    try:
        if not isinstance(hex_color, str) or not hex_color.strip():
            raise ValueError("Color value must be a non-empty string")
        color_value = hex_color.strip()
        if color_value.startswith("#") and len(color_value) == 4:
            color_value = (
                "#" + color_value[1] * 2 + color_value[2] * 2 + color_value[3] * 2
            )
        r, g, b = ImageColor.getrgb(color_value)
        logger.debug(f"Converted hex {hex_color} to RGB ({r}, {g}, {b})")
        return (r, g, b)
    except ValueError as e:
        logger.error(f"Invalid hex color format '{hex_color}': {e}")
        return (0, 0, 0)
    except Exception as e:
        logger.error(f"Error converting hex to RGB '{hex_color}': {e}", exc_info=True)
        return (0, 0, 0)
