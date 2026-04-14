"""Tests for extra functionality additions in Crew.py."""

import csv
from pathlib import Path

from PIL import Image

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Crew import crop_from_annotations, hex_to_rgb, process_images


def _create_image(path: Path, size=(100, 80), color="white"):
    image = Image.new("RGB", size, color)
    image.save(path)


def test_hex_to_rgb_supports_shorthand_hex():
    assert hex_to_rgb("#FFF") == (255, 255, 255)


def test_hex_to_rgb_supports_named_colors():
    assert hex_to_rgb("red") == (255, 0, 0)


def test_process_images_supports_output_format(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    _create_image(input_dir / "sample.png")

    saved = process_images(
        str(input_dir),
        str(output_dir),
        grid_size=(10, 10),
        output_format="webp",
        quality=80,
    )

    assert len(saved) == 1
    assert saved[0].endswith(".webp")
    assert (output_dir / "sample_grid.webp").exists()


def test_crop_from_annotations_skips_invalid_rows(tmp_path):
    image_path = tmp_path / "source.png"
    csv_path = tmp_path / "annotations.csv"
    output_dir = tmp_path / "crops"

    _create_image(image_path, size=(120, 100))

    rows = [
        {"name": "valid_1", "x": "10", "y": "10", "width": "20", "height": "20"},
        {"name": "bad_num", "x": "x", "y": "10", "width": "20", "height": "20"},
        {"name": "outside", "x": "110", "y": "95", "width": "20", "height": "20"},
        {"name": "valid_2", "x": "0", "y": "0", "width": "30", "height": "30"},
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "x", "y", "width", "height"])
        writer.writeheader()
        writer.writerows(rows)

    saved = crop_from_annotations(str(image_path), str(csv_path), str(output_dir), output_format="png")

    assert len(saved) == 2
    assert (output_dir / "valid_1.png").exists()
    assert (output_dir / "valid_2.png").exists()
