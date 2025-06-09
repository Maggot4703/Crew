#!/usr/bin/env python3
"""
Demonstration script for testing script execution functionality.

This script prints a simple message to standard output and is used to verify
that the script execution mechanism in the main application works correctly.
"""

import sys
import time
from pathlib import Path


def main():
    print("=" * 50)
    print("Demo Script Execution")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {Path.cwd()}")
    print(f"Script location: {__file__}")
    print()

    print("Listing Python files in current directory:")
    python_files = list(Path.cwd().glob("*.py"))
    for i, py_file in enumerate(python_files[:10], 1):  # Show first 10
        print(f"  {i:2d}. {py_file.name}")

    if len(python_files) > 10:
        print(f"  ... and {len(python_files) - 10} more files")

    print()
    print("Simulating some work...")
    for i in range(3):
        time.sleep(0.5)
        print(f"  Step {i+1}/3 completed")

    print()
    print("✓ Demo script completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    main()
