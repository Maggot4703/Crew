# Crew Project Documentation

This directory contains the Sphinx entry point for the production `CREW/Crew` application.

## What lives here

- `docs/index.rst` - main Sphinx landing page
- `docs/conf.py` - Sphinx configuration
- generated HTML under `docs/_build/html/` after a local docs build

For broader project documentation, also see:

- `../README.md`
- `../Reading Now/README.md`
- `../../docs/fetchdocs_readmine.md`

## Build the docs

1. Install Sphinx and extensions:

   ```bash
   pip install sphinx sphinx-autodoc-typehints
   ```

2. From `CREW/Crew/docs/`, run:

   ```bash
   sphinx-build -b html . _build/html
   ```

3. Open `_build/html/index.html` in your browser.

## Notes

- The API reference depends on Python imports working in the docs environment.
- If package imports are currently broken for full project collection, the Sphinx API section may need a lighter environment or targeted import fixes before it builds cleanly.
- Edit `docs/index.rst` when the project entry points or documentation map changes.
