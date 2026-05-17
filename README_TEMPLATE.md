# Crew Project Documentation Template

## Overview

Crew is an image processing and crew management application with both CLI and GUI interfaces. It supports grid overlay, image cropping, CSV/Excel reading, and more.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
  - [CLI Usage](#cli-usage)
  - [GUI Usage](#gui-usage)
- [Features](#features)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Installation

Describe how to install dependencies and set up the environment.

```
pip install -r requirements.txt
# or use your preferred environment manager
```

## Usage

### CLI Usage

Show how to use the CLI commands:

```
python Crew.py --help
python Crew.py grid-image --image-path <path> --output-path <path>
python Crew.py grid-folder --image-dir <dir> --output-dir <dir>
python Crew.py read-csv --csv-path <path>
python Crew.py read-excel --excel-path <path> [--sheet <name>]
python Crew.py crop-csv --image-path <path> --annotations-csv <path> --output-dir <dir>
```

### GUI Usage

Explain how to launch and use the GUI:

```
python Crew.py
```

## Features

- Overlay grids on images or folders of images
- Crop images using CSV annotations
- Read and preview CSV/Excel files
- GUI and CLI modes
- Logging and progress tracking

## Configuration

Describe any configuration files or environment variables.

## API Reference (Expanded)

### log_progress_md
```python
log_progress_md(message: str) -> None
```
Append a progress update to progress.md in the workspace root.

**Args:**
- `message` (str): Progress message to append.

**Example:**
```python
log_progress_md("Started Crew main application script.")
```

---

### show_user_error
```python
show_user_error(message: str, gui: bool = False) -> None
```
Display a user-friendly error message to the user. If `gui=True`, integrates with GUI dialog (placeholder for now). Otherwise, prints to stderr for CLI.

**Args:**
- `message` (str): The error message to display.
- `gui` (bool): If True, show in GUI (placeholder); else log to stderr.

**Example:**
```python
show_user_error("File not found.")
```

---

### hex_to_rgb
```python
hex_to_rgb(hex_color: str) -> Tuple[int, int, int]
```
Convert hex color string to RGB tuple.

**Args:**
- `hex_color` (str): Hexadecimal color string (e.g., '#FF00FF' or 'FF00FF').

**Returns:**
- Tuple[int, int, int]: Corresponding RGB values.

**Example:**
```python
rgb = hex_to_rgb("#FF00FF")  # (255, 0, 255)
```

---

### rgb_to_hex
```python
rgb_to_hex(r: int, g: Optional[int] = None, b: Optional[int] = None) -> str
```
Convert RGB values to hexadecimal color string.

**Args:**
- `r` (int or tuple): Red value or (r, g, b) tuple.
- `g` (Optional[int]): Green value.
- `b` (Optional[int]): Blue value.

**Returns:**
- str: Hexadecimal color string.

**Example:**
```python
hex_color = rgb_to_hex(255, 0, 255)  # '#FF00FF'
```

---

### mark_line
```python
mark_line(image=None, x1=0, y1=0, x2=0, y2=0, color="red", thickness=1) -> Optional[Image]
```
Draw a line on the image using Pillow.

**Args:**
- `image`: Existing image to draw on (optional, Pillow Image or None).
- `x1` (int): Starting x-coordinate.
- `y1` (int): Starting y-coordinate.
- `x2` (int): Ending x-coordinate.
- `y2` (int): Ending y-coordinate.
- `color` (str): Color of the line (default is red).
- `thickness` (int): Thickness of the line (default is 1).

**Returns:**
- Optional[Image]: Image with the drawn line or None on error.

**Example:**
```python
from PIL import Image
img = Image.new("RGB", (100, 100), "white")
img = mark_line(img, 10, 10, 90, 90, color="blue", thickness=2)
img.save("output.png")
```

---

### overlay_grid
```python
overlay_grid(image_path: str, grid_color: str = "lightgrey", grid_size: tuple = (42, 32), show_labels: bool = False) -> Optional[Image]
```
Overlay a grid on top of an image.

**Args:**
- `image_path` (str): Path to the input image.
- `grid_color` (str): Color of the grid lines (default is light gray).
- `grid_size` (tuple): (width, height) of grid cells.
- `show_labels` (bool): Whether to show row/column labels.

**Returns:**
- Optional[Image]: Image with grid overlay or None on error.

**Example:**
```python
img = overlay_grid("input.png", grid_color="red", grid_size=(50, 50), show_labels=True)
if img:
    img.save("output_grid.png")
```

---

## GUI Screenshots/Diagrams

- To add a screenshot: Run the GUI (`python Crew.py`), take a screenshot, and save it as `docs/gui_screenshot.png`.
- To add a diagram: Use a tool like draw.io or Mermaid. Example (Mermaid):

```
flowchart TD
    Start[Start GUI] -->|User selects image| OpenImage[Open Image]
    OpenImage --> OverlayGrid[Overlay Grid]
    OverlayGrid --> Save[Save Image]
    Save --> End[Done]
```

- ![GUI Screenshot](docs/gui_screenshot.png)

## Testing

How to run tests:

```
python -m unittest discover
```

## Contributing

Guidelines for contributing to the project.

## License

MIT License
