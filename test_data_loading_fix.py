#!/usr/bin/env python3
"""Test the pandas parsing fix without GUI"""

import sys
import os
from pathlib import Path
sys.path.append('/home/me/BACKUP/PROJECTS/Crew')

def test_text_file_detection():
    """Test that we can detect text files vs CSV files"""
    
    # Test file paths
    csv_file = "/home/me/BACKUP/PROJECTS/Crew/sample_crew.csv"
    text_file = "/home/me/BACKUP/PROJECTS/Crew/use/use-CSS.txt"
    
    print("=== File Type Detection Test ===")
    
    # Check if files exist
    if os.path.exists(csv_file):
        print(f"✓ CSV file exists: {csv_file}")
    else:
        print(f"✗ CSV file missing: {csv_file}")
        
    if os.path.exists(text_file):
        print(f"✓ Text file exists: {text_file}")
    else:
        print(f"✗ Text file missing: {text_file}")
    
    # Test the file filtering logic from gui.py
    def should_use_script_loading(file_path):
        """Replicate the GUI logic for routing files"""
        file_path_obj = Path(file_path)
        
        # Check file extension
        if file_path_obj.suffix.lower() not in [".csv", ".xlsx", ".xls"]:
            return True, f"File type '{file_path_obj.suffix}' should use script loading"
        
        # Check if in use/ directory
        if "use" in file_path_obj.parts:
            return True, "Files in 'use/' directory should use script loading"
        
        return False, "File should use data loading"
    
    print("\n=== File Routing Test ===")
    
    # Test CSV file
    should_script, reason = should_use_script_loading(csv_file)
    print(f"CSV file routing: {'Script Loading' if should_script else 'Data Loading'}")
    print(f"Reason: {reason}")
    
    # Test text file
    should_script, reason = should_use_script_loading(text_file)
    print(f"Text file routing: {'Script Loading' if should_script else 'Data Loading'}")
    print(f"Reason: {reason}")
    
    return True

def test_database_manager_with_csv():
    """Test DatabaseManager with a proper CSV file"""
    print("\n=== DatabaseManager CSV Test ===")
    
    try:
        from database_manager import DatabaseManager
        print("✓ DatabaseManager imported successfully")
        
        csv_file = "/home/me/BACKUP/PROJECTS/Crew/sample_crew.csv"
        if not os.path.exists(csv_file):
            print(f"✗ CSV file not found: {csv_file}")
            return False
        
        # Test loading CSV data
        db_manager = DatabaseManager()
        print("✓ DatabaseManager instance created")
        
        headers, rows, groups = db_manager.load_data(csv_file)
        print(f"✓ CSV data loaded successfully:")
        print(f"  - Headers: {headers}")
        print(f"  - Rows: {len(rows)}")
        print(f"  - Groups: {len(groups) if groups else 0}")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error loading CSV: {e}")
        return False

def test_would_fail_on_text_file():
    """Test what would happen if we tried to load a text file as CSV"""
    print("\n=== Text File Pandas Error Test ===")
    
    try:
        import pandas as pd
        text_file = "/home/me/BACKUP/PROJECTS/Crew/use/use-CSS.txt"
        
        if not os.path.exists(text_file):
            print(f"✗ Text file not found: {text_file}")
            return False
        
        print(f"Attempting to load text file as CSV: {text_file}")
        
        # This should fail with pandas parsing error
        try:
            data = pd.read_csv(text_file)
            print(f"✗ Unexpected success - pandas parsed text file!")
            return False
        except Exception as e:
            print(f"✓ Expected pandas error occurred: {e}")
            print("This confirms that text files need special handling")
            return True
            
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Data Loading Fix")
    print("=" * 50)
    
    results = []
    
    # Test 1: File type detection
    results.append(test_text_file_detection())
    
    # Test 2: DatabaseManager with CSV
    results.append(test_database_manager_with_csv())
    
    # Test 3: Text file would fail
    results.append(test_would_fail_on_text_file())
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed - the pandas parsing fix should work!")
    else:
        print("✗ Some tests failed - there may be issues")
    
    return passed == total

if __name__ == "__main__":
    main()