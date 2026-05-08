"""Compatibility helpers for standalone event-hook tests."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any


def setup_event_handlers(
    target: Any | None = None, bindings: Iterable[tuple[str, Callable[..., Any]]] | None = None
) -> int:
    """Attach a simple list of event bindings to a target widget.

    When ``target`` is omitted, this function behaves as a harmless no-op so
    lightweight tests can import and call it without needing a GUI instance.
    """

    if target is None or bindings is None:
        return 0

    bound = 0
    for event_name, handler in bindings:
        if hasattr(target, "bind"):
            target.bind(event_name, handler)
            bound += 1
    return bound
