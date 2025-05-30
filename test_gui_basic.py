#!/usr/bin/env python3
"""
Simple GUI test to diagnose display issues
"""
import sys
import tkinter as tk

def test_basic_gui():
    """Test basic GUI functionality"""
    try:
        print("Testing basic tkinter functionality...")
        
        # Create root window
        root = tk.Tk()
        root.title("GUI Test")
        root.geometry("400x300")
        
        # Add some basic widgets
        label = tk.Label(root, text="GUI Test - If you see this, GUI works!")
        label.pack(pady=20)
        
        button = tk.Button(root, text="Click Me!")
        button.pack(pady=10)
        
        def close_app():
            print("GUI test completed successfully")
            root.destroy()
            
        close_button = tk.Button(root, text="Close", command=close_app)
        close_button.pack(pady=10)
        
        # Auto-close after 3 seconds
        root.after(3000, close_app)
        
        print("Starting GUI mainloop...")
        root.mainloop()
        print("GUI mainloop ended")
        
        return True
        
    except Exception as e:
        print(f"GUI Test Failed: {e}")
        return False

if __name__ == "__main__":
    print("GUI Functionality Test")
    print("Python version:", sys.version)
    print("Tkinter version:", tk.TkVersion)
    
    success = test_basic_gui()
    
    if success:
        print("Basic GUI functionality test PASSED")
    else:
        print("Basic GUI functionality test FAILED")