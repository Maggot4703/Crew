
from PIL import Image
from image_utils import mark_line, overlay_grid, process_images, crop_from_annotations, markHorizontalLine


def test_mark_line_creates_image():
    img = mark_line(None, 10, 10, 100, 100, color="blue", thickness=2)
    assert isinstance(img, Image.Image)


def test_overlay_grid_returns_image(tmp_path):
    # Create a blank image
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (100, 100), "white")
    img.save(img_path)
    result = overlay_grid(
        str(img_path), grid_color="black", grid_size=(10, 10)
    )
    assert isinstance(result, Image.Image)


def test_process_images(tmp_path):
    # Create a blank image
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (100, 100), "white")
    img.save(img_path)
    output_dir = tmp_path / "out"
    result = process_images(str(tmp_path), str(output_dir), grid_size=(10, 10))
    assert isinstance(result, list)
    assert any(str(output_dir) in p for p in result)


def test_markHorizontalLine():
    img = markHorizontalLine(0, 0, 50, 0, color="red", thickness=1)
    assert isinstance(img, Image.Image)


def test_crop_from_annotations(tmp_path):
    # Create a blank image
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (100, 100), "white")
    img.save(img_path)
    # Create annotation CSV
    csv_path = tmp_path / "ann.csv"
    with open(csv_path, "w") as f:
        f.write("name,x,y,width,height\nregion1,10,10,20,20\n")
    output_dir = tmp_path / "out"
    result = crop_from_annotations(
        str(img_path), str(csv_path), str(output_dir)
    )
    assert isinstance(result, list)
    assert any("region1" in p for p in result)
