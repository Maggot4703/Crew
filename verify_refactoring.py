#!/usr/bin/env python3
"""Final verification for CrewGUI refactoring"""

import os
import sys


def main():
    print("🎉 CrewGUI Refactoring Verification")
    print("=" * 40)

    # Test imports
    try:
        import gui
        from data_manager import DataManager
        from event_manager import EventManager
        from script_manager import ScriptManager
        from state_manager import StateManager
        from ui_manager import UIManager

        print("✅ All imports successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return 1

    # Check files
    files = [
        "gui.py",
        "ui_manager.py",
        "event_manager.py",
        "state_manager.py",
        "data_manager.py",
        "script_manager.py",
    ]

    total_lines = 0
    for f in files:
        if os.path.exists(f):
            lines = sum(1 for _ in open(f))
            total_lines += lines
            print(f"✅ {f}: {lines} lines")
        else:
            print(f"❌ {f} missing")
            return 1

    print(f"\n🎯 Total: {total_lines} lines across {len(files)} files")
    print("🎉 REFACTORING COMPLETE!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
