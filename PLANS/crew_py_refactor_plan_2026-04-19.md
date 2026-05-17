# Crew.py Refactor Plan (2026-04-19)

## Objective

Improve maintainability, clarity, and testability of Crew.py by splitting responsibilities, improving structure, and aligning with project standards.

---

## 1. Split by Responsibility

- **Move CLI logic** (argument parsing, run_cli, helpers) to `cli.py`.
- **Move GUI startup** and helpers to `gui.py` (if not already there).
- **Move utility functions** (color conversion, logging helpers, etc.) to `utils.py` or a dedicated section.
- **Keep only the main entry point** and high-level orchestration in `Crew.py`.

## 2. Refactor CLI Command Implementations

- For each CLI subcommand, create a dedicated function in `cli.py`.
- The main CLI handler should only dispatch to these functions.

## 3. Review and Add Type Hints

- Ensure all functions have complete type hints for parameters and return values.

## 4. Docstrings and Comments

- Add or update concise docstrings for all public functions and modules.

## 5. Remove or Clearly Mark Placeholders

- Remove unused placeholder functions like `job4()`, or mark them with TODO and clear comments.

## 6. Dependency Management

- Consider moving `_auto_install_deps` to a separate install script or make it optional via a CLI flag.

## 7. Testing

- Ensure all major functions are covered by tests in the `tests/` directory.

## 8. Lint and Format

- Run `black .` and `flake8 .` to ensure code style and lint cleanliness.

---

### Next Steps

1. Create new files as needed (`cli.py`, `utils.py`, etc.).
2. Move code sections according to the plan.
3. Update imports and references.
4. Test CLI and GUI entry points after refactor.
5. Update or add tests for moved/refactored code.
6. Run formatting and linting tools.

---

*Author: GitHub Copilot (GPT-4.1)*
*Date: 2026-04-19*
