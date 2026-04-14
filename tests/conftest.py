# conftest.py
# Automatically add project root to sys.path for all tests in this directory
import sys
from pathlib import Path

crew_dir = Path(__file__).resolve().parent.parent
if str(crew_dir) not in sys.path:
    sys.path.insert(0, str(crew_dir))
