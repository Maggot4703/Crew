#!/usr/bin/env python3
"""
Legacy compatibility launcher for Crew GUI.

Canonical startup is gui_main_function.main. Keep this file as a thin wrapper.
"""
import logging
import sys

from gui_main_function import main as launch_main


logger = logging.getLogger(__name__)


def main() -> int:
    """Launch the Crew GUI application via canonical startup path."""
    try:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        logger.info("Launching Crew GUI via canonical startup path")
        launch_main()
        return 0
    except (KeyboardInterrupt, SystemExit):
        raise
    except (ImportError, RuntimeError, OSError) as exc:
        logger.exception(
            "Launcher failed before or during GUI startup: %s",
            exc,
        )
        return 1
    except Exception as exc:
        logger.exception("Unexpected launcher failure: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
