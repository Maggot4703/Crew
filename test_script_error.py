#!/usr/bin/env python3
"""
Demo script that shows error handling in the script selector
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
