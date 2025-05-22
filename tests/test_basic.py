import pytest
import os

def test_data_dir_exists():
    assert os.path.isdir("data")

def test_input_dir_exists():
    assert os.path.isdir("input")

def test_output_dir_exists():
    assert os.path.isdir("output")