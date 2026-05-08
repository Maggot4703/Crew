"""Compatibility helpers for standalone layout tests."""

from __future__ import annotations

from typing import Any


def initialize_gui(root: Any | None = None, *, title: str = "Crew Manager") -> dict[str, Any]:
    """Apply a minimal layout configuration and report what was configured.

    The production GUI layout lives in ``gui.py``. This helper exists so older
    imports and lightweight tests have a real, non-placeholder entry point.
    """

    config = {"title": title, "configured": False}
    if root is not None and hasattr(root, "title"):
        root.title(title)
        config["configured"] = True
    return config
