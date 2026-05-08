#!/bin/bash
# Run Crew GUI tests locally with display

# Ensure DISPLAY is set (Linux/X11)
if [ -z "$DISPLAY" ]; then
  export DISPLAY=:0
fi

# Run the main GUI test file
python3 -m unittest tests/test_gui_complete.py

# Optionally run all GUI-related tests (uncomment if needed)
# python3 -m unittest discover -s tests -p 'test_gui*.py'
