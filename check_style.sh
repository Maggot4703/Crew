#!/bin/bash
# check_style.sh - Format and lint Crew project for PEP8 compliance

set -e

# Format code with Black
black Crew/

# Sort imports with isort
isort Crew/

# Lint with Flake8
flake8 Crew/

echo "All style checks complete."
