#!/bin/bash
# Pre-commit hook: run lint and tests before commit
set -e
flake8 Crew/
pytest tests/
