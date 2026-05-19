CREW - Installation and Dependencies

This file explains how to install and prepare the environment for the CREW application (CREW/Crew).

Overview
--------
The CREW application intentionally no longer attempts to auto-install Python packages at runtime. This avoids unexpected changes to developer environments and ensures reproducible setups.

Required Python packages
------------------------
- pillow (PIL) -> pip install pillow
- pandas -> pip install pandas
- SpeechRecognition -> pip install SpeechRecognition
- (Optional) openpyxl -> pip install openpyxl
- (Optional) xlrd -> pip install xlrd

System packages
---------------
- tkinter: install via your OS package manager. Examples:
  - Debian/Ubuntu: sudo apt install python3-tk
  - Fedora/RHEL: sudo dnf install python3-tkinter

Recommended installation methods
--------------------------------
1) Using the workspace manager (recommended):

   cd /home/me/Notebooks/CREW
   uv sync
   uv run python Crew/Crew.py

2) Using a virtual environment:

   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install pillow pandas SpeechRecognition openpyxl xlrd
   python Crew/Crew.py

Notes
-----
- If dependencies are missing, Crew will exit with a clear error describing which packages are required and how to install them.
- Copy CREW/Crew/config.llm.example.json -> CREW/Crew/config.json and edit to point to your LLM backend (e.g., mock DeepSeek at http://127.0.0.1:8000).
- For local LLM testing, see scripts/mock_deepseek_server.py

Support
-------
If installation problems persist, run `uv sync` or ask the maintainer for help.
