---
name: Crew Python Standards
description: "Use when editing Python source, fixing bugs, adding features, or reviewing PRs in the Crew project. Captures preferred formatting, linting, testing, and documentation conventions."
applyTo: "**/*.py"
---

# Crew Python Standards

- Target Python `3.7+` compatibility unless the task explicitly states otherwise.
- Prefer formatting Python changes with `black .`.
- Prefer keeping code lint-clean with `flake8 .`.
- Prefer adding or updating tests in `tests/` when behavior changes.
- Prefer running `pytest` after behavior changes.
- Use `snake_case` for functions/variables, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants.
- Prefer clear type hints for new or changed function signatures.
- Add concise docstrings for new public classes and functions.
- Keep changes focused and avoid unrelated refactors in the same patch.