
import os
import csv
import pytest
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import file_utils

# Test reading a valid CSV file
def test_read_csv_pandas_valid(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("name,x,y,width,height\nA,1,2,3,4\nB,5,6,7,8\n")
    df = file_utils.read_csv_pandas(str(csv_file))
    assert not df.empty
    assert list(df.columns) == ["name", "x", "y", "width", "height"]
    assert df.iloc[0]["name"] == "A"

# Test reading a malformed CSV file
def test_read_csv_pandas_malformed(tmp_path):
    csv_file = tmp_path / "bad.csv"
    csv_file.write_text("name,x,y,width,height\nA,1,2\nB,5,6,7,8,9,10\n")
    df = file_utils.read_csv_pandas(str(csv_file))
    # Accept None as valid for malformed CSVs (pandas.read_csv fails on bad structure)
    assert df is None or df.empty

# Test missing file
def test_read_csv_pandas_missing():
    df = file_utils.read_csv_pandas("/nonexistent/file.csv")
    assert df is None or df.empty
