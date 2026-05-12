# Sphinx configuration for Crew project

# To build the docs:
# 1. Install Sphinx and autodoc: pip install sphinx sphinx-autodoc-typehints
# 2. Run: make html (or sphinx-build -b html . _build/html)

import os
import sys

project = "Crew"
author = "Crew Team"
release = "1.0.0"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
]
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "alabaster"

sys.path.insert(0, os.path.abspath(".."))
