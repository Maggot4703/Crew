# Crew.py Global Refactoring & Testing Plan

## 1. Global Principles
- Always work on copies of Crew.py and referenced files. Never overwrite originals until tested and verified.
- Remember and log all errors and warnings encountered during development and testing.
- Proceed step-by-step, debugging and fixing issues frequently. Mark off completed steps.
- Use and adapt existing code where possible; avoid unnecessary rewrites.
- Be vigilant about linting errors and code quality.
- Add clear, descriptive comments throughout all code changes.

## 2. Plan for Crew.py
- Identify all files referenced/imported by Crew.py (done; see below).
- For each referenced file, ensure there is a corresponding test in the tests/ directory.
- If a file is not covered by a test, create a new test file or add to an existing one.
- Run all tests after each change. Debug and fix issues as they arise.
- Save all suggestions, research, and plans in this PLANS folder. Update plans as work progresses.
- If problems occur, document suggestions and troubleshooting steps here.

## 3. Referenced Files in Crew.py
- image_utils.py
- file_utils.py
- cli.py
- gui.py
- data_manager.py
- database_manager.py
- error_handler.py
- events.py
- state_manager.py
- logic.py
- layout.py
- tts_manager.py
- script_manager.py
- ui_manager.py
- globals.py

## 4. Test Coverage Plan
- Review existing tests in tests/ for each referenced file.
- For files lacking tests, create new test scripts (e.g., test_file_utils.py, test_image_utils.py, etc.).
- For Crew.py itself, ensure test_crew_main.py and related tests cover all CLI and GUI entry points.
- Add tests for error handling, edge cases, and integration between modules.

## 5. Step-by-Step Process
1. Make a copy of Crew.py and any file to be modified. Work only on the copy.
2. Implement changes incrementally, running tests after each change.
3. Log all errors/warnings and debugging steps in this folder.
4. Update this plan and checklist as tasks are completed.
5. Only replace the original file after all tests pass and manual verification is complete.

## 6. Suggestions & Troubleshooting
- If a test fails, document the error and proposed fix here before making changes.
- If a module is difficult to test, consider refactoring for better testability.
- Use logging and comments to clarify complex logic.
- If unsure about a dependency or import, research and document findings here.

---

_Last updated: 2026-04-11_
