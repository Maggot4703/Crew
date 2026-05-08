# Crew Project Documentation

To build the documentation:

1. Install Sphinx and extensions:
   pip install sphinx sphinx-autodoc-typehints

2. From the docs/ directory, run:
   sphinx-build -b html . _build/html

3. Open _build/html/index.html in your browser to view the docs.

- The API Reference is generated automatically from Python docstrings.
- Edit docs/index.rst to add more sections or custom content.
