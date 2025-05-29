#!/bin/bash
# Wrapper script to run read_use.sh with the virtual environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/.venv/bin/python"
"$PYTHON" "$SCRIPT_DIR/read_use_file_cli.py" --file "$@"
