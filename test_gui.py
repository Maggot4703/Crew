#!/usr/bin/env python3
import sys
import traceback

try:
    from gui import CrewGUI
    print("GUI class imported successfully")
    
    app = CrewGUI()
    print("GUI instance created successfully")
    
    if hasattr(app, '_on_apply_filter'):
        print("_on_apply_filter method found")
    else:
        print("ERROR: _on_apply_filter method NOT found")
    
    filter_methods = [method for method in dir(app) if 'filter' in method.lower()]
    print(f"Filter-related methods: {filter_methods}")
    
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
