import logging


def user_info(message: str):
    """Display a user-facing info message (CLI output)."""
    print(message)


def log_progress_md(message: str) -> None:
    """
    Append a progress update to progress.md in the workspace root.
    Args:
        message (str): Progress message to append.
    """
    try:
        with open("progress.md", "a") as f:
            f.write(f"{message}\n")
        logging.getLogger(__name__).info(f"Logged progress: {message}")
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to log progress to progress.md: {e}")
        show_user_error("Could not update progress log. Please check file permissions.")


def show_user_error(message: str, gui: bool = False):
    """
    Display a user-friendly error message to the user.
    If gui=True, integrate with GUI dialog (placeholder for now).
    Otherwise, print to stderr for CLI.
    """
    if gui:
        # Placeholder: Integrate with GUI dialog system
        # from tkinter import messagebox
        # messagebox.showerror("Error", message)
        logging.getLogger(__name__).error(
            f"[GUI ERROR] {message}"
        )  # Replace with dialog in real GUI
    else:
        logging.getLogger(__name__).error(f"Error: {message}")


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color string to RGB tuple."""
    try:
        color_value = hex_color.lstrip("#")
        if len(color_value) == 3:
            color_value = "".join([c * 2 for c in color_value])
        return tuple(int(color_value[i : i + 2], 16) for i in (0, 2, 4))
    except Exception as e:
        logging.getLogger(__name__).error(
            f"Error converting hex to RGB '{hex_color}': {e}"
        )
        return (0, 0, 0)


def rgb_to_hex(r: int, g: int = None, b: int = None) -> str:
    """Convert RGB values to hexadecimal color string."""
    if isinstance(r, tuple):
        r, g, b = r
    return "#{:02X}{:02X}{:02X}".format(r, g, b)


def calculate_hexagon_points(center: tuple, radius: float) -> list:
    """Calculate the 6 points of a hexagon given center and radius."""
    import math

    cx, cy = center
    return [
        (
            cx + radius * math.cos(math.radians(60 * i)),
            cy + radius * math.sin(math.radians(60 * i)),
        )
        for i in range(6)
    ]


def spacer():
    """Print a spacer line (for test)."""
    logging.getLogger(__name__).info("-" * 40)
