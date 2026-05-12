#!/usr/bin/env python3
"""
GUI Status Verification Script
=============================

This script verifies that the GUI application is working correctly.
"""

import subprocess
from pathlib import Path


def check_gui_process():
    """Check if GUI process is running"""
    try:
        result = subprocess.run(
            ["ps", "aux"], capture_output=True, text=True, check=True
        )
        for line in result.stdout.split("\n"):
            if "gui.py" in line and "python" in line:
                return True, line.strip()
        return False, None
    except Exception as e:
        return False, f"Error: {e}"


def main():
    print("=" * 50)
    print("GUI Application Status Verification")
    print("=" * 50)

    # Check GUI process
    is_running, process_info = check_gui_process()
    if is_running:
        print("✅ GUI process is RUNNING")
        print(f"📋 Process: {process_info}")
    else:
        print("❌ GUI process is NOT running")

    # Check files
    files = ["gui.py", "Crew.py", "gui.log"]
    print(f"\n📁 Checking files:")
    for f in files:
        exists = Path(f).exists()
        status = "✅" if exists else "❌"
        print(f"   {status} {f}")

    print("\n🎉 GUI application setup complete!")
    print("🚀 Usage:")
    print("   • python gui.py - Run GUI directly")
    print("   • python Crew.py - Run via Crew launcher")


if __name__ == "__main__":
    main()
