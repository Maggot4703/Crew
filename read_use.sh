#!/bin/bash
# This script provides a simple way to read a use file by name
# Usage: ./read_use.sh [filename]

if [ $# -eq 0 ]; then
  echo "Usage: ./read_use.sh [filename]"
  echo "Example: ./read_use.sh Docker"
  echo "Available use files:"
  python3 read_use_file_cli.py --list
  exit 0
fi

python3 read_use_file_cli.py --file "$1"
