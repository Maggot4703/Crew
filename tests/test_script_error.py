#!/usr/bin/env python3
"""
Test script designed to produce an error during execution.

This script intentionally raises a RuntimeError to test the error handling
capabilities of the script execution mechanism in the main application.
"""

import sys


def main():
    print("This script will demonstrate error handling...")
    print("Standard output message")

    # Write to stderr
    print("This is an error message", file=sys.stderr)

    # Cause an intentional error
    print("About to cause an error...")
    raise ValueError("This is a demonstration error - everything is working correctly!")


if __name__ == "__main__":
    main()
