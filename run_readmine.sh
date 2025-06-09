#!/bin/bash
# run_readmine.sh - Script to run ReadMine.py with the .venv virtual environment

# Script directory
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR" || exit 1

# Check if .venv exists, if not create it
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Setting up .venv..."
    python3 ReadMine.py --setup-venv
    
    if [ $? -ne 0 ]; then
        echo "Failed to set up virtual environment. Exiting."
        exit 1
    fi
    
    echo "Virtual environment set up successfully."
fi

# Activate virtual environment and run ReadMine.py
echo "Activating virtual environment and running ReadMine.py..."
source .venv/bin/activate

# Run ReadMine.py with all arguments passed to this script
python3 ReadMine.py "$@"

# Deactivate virtual environment
deactivate

echo "ReadMine.py execution completed."