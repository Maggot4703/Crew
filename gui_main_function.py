import tkinter as tk
import logging
import math
from pathlib import Path

from gui import CrewGUI


logger = logging.getLogger(__name__)


def _set_safe_icon(root: tk.Tk, icon_ico: Path, icon_png: Path) -> None:
    """Set a window icon while avoiding X11 crashes from oversized images."""
    if icon_ico.exists():
        root.iconbitmap(str(icon_ico))
        return

    if not icon_png.exists():
        return

    icon_image = tk.PhotoImage(file=str(icon_png))

    # Large icons can trigger X11 BadLength on some Linux stacks.
    max_dim = max(icon_image.width(), icon_image.height())
    if max_dim > 128:
        scale = max(1, math.ceil(max_dim / 128))
        icon_image = icon_image.subsample(scale, scale)

    root.iconphoto(True, icon_image)
    # Keep a reference to prevent Tk from garbage collecting the image.
    root._icon_image = icon_image


def main() -> None:
    """Initialize and run the Crew GUI application."""
    root = tk.Tk()
    root.title("Crew GUI")

    # Resolve icon relative to this module; keep startup resilient if missing.
    base_dir = Path(__file__).resolve().parent
    icon_ico = base_dir / "input" / "Cars1.ico"
    icon_png = base_dir / "input" / "Cars1.png"

    try:
        _set_safe_icon(root, icon_ico, icon_png)
    except (tk.TclError, OSError) as exc:
        # Icon setup is optional and should never block GUI startup.
        logger.warning("Icon setup skipped: %s", exc)

    CrewGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
