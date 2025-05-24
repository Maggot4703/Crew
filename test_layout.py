#!/usr/bin/env python3
"""
Test script to verify the GUI layout changes
"""

import tkinter as tk
from tkinter import ttk

def test_layout():
    """Test the basic layout structure"""
    try:
        # Import the GUI class
        from gui import CrewGUI
        
        # Create a test instance
        root = tk.Tk()
        app = CrewGUI(root)
        
        # Check if PanedWindow exists
        if hasattr(app, 'paned_window'):
            print("✓ PanedWindow successfully created")
            
            # Check if frames are properly configured
            if hasattr(app, 'left_frame') and hasattr(app, 'right_frame'):
                print("✓ Left and right frames exist")
                
                # Check left frame width configuration
                left_width = app.left_frame.cget('width')
                print(f"✓ Left frame width: {left_width}px")
                
                print("✓ Layout test completed successfully!")
                
        else:
            print("✗ PanedWindow not found")
            
        # Close without showing the GUI
        root.quit()
        root.destroy()
        
    except Exception as e:
        print(f"✗ Layout test failed: {e}")

if __name__ == "__main__":
    test_layout()
