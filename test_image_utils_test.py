import os
import tempfile
import shutil
import pytest
from PIL import Image
import logging

import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import image_utils_test as image_utils

def test_mark_line_basic():
    img = Image.new("RGB", (100, 100), "white")
    result = image_utils.mark_line(img, 10, 10, 90, 90, color="blue", thickness=3)
    assert result is not None
    assert isinstance(result, Image.Image)

def test_overlay_grid(tmp_path):
    img = Image.new("RGB", (100, 100), "white")
    img_path = tmp_path / "test.png"
    img.save(img_path)
    result = image_utils.overlay_grid(str(img_path), grid_color="green", grid_size=(10, 10), show_labels=True)
    assert result is not None
    assert isinstance(result, Image.Image)

def test_process_images(tmp_path):
    # Setup input directory with one image
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    img = Image.new("RGB", (50, 50), "white")
    img_path = input_dir / "img1.png"
    img.save(img_path)
    results = image_utils.process_images(str(input_dir), str(output_dir), grid_size=(5, 5), grid_color="red", show_labels=False)
    assert isinstance(results, list)
    assert len(results) == 1
    assert os.path.exists(results[0])

def test_crop_from_annotations(tmp_path):
    # Create image
    img = Image.new("RGB", (100, 100), "white")
    img_path = tmp_path / "img.png"
    img.save(img_path)
    # Create CSV
    csv_path = tmp_path / "ann.csv"
    with open(csv_path, "w") as f:
        f.write("name,x,y,width,height\n")
        f.write("crop1,10,10,20,20\n")
        f.write("crop2,50,50,30,30\n")
    output_dir = tmp_path / "crops"
    output_dir.mkdir()
    results = image_utils.crop_from_annotations(str(img_path), str(csv_path), str(output_dir))
    assert isinstance(results, list)
    assert len(results) == 2
    for path in results:
        assert os.path.exists(path)

def test_hex_to_rgb():
    assert image_utils.hex_to_rgb("#fff") == (255, 255, 255)
    assert image_utils.hex_to_rgb("#000000") == (0, 0, 0)
    assert image_utils.hex_to_rgb("#ff0000") == (255, 0, 0)
    assert image_utils.hex_to_rgb("red") == (255, 0, 0)
    assert image_utils.hex_to_rgb("") == (0, 0, 0)

def test_build_save_kwargs():
    assert image_utils._build_save_kwargs(".jpg", 80) == {"quality": 80}
    assert image_utils._build_save_kwargs(".png", 80) == {}
    assert image_utils._build_save_kwargs("jpeg", 50) == {"quality": 50}
    assert image_utils._build_save_kwargs("webp", 90) == {"quality": 90}
