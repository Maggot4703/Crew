# Test Run Summary (2026-04-11)

## Results
- Total tests run: 194
- Failures: 1
- Errors: 13
- Skipped: 2

## Key Issues
- **Import errors**: Several tests fail due to import/module path issues (e.g., test_cli_copy, test_data_files_copy, test_logging_copy). These are often caused by incorrect sys.path or import statements assuming Crew is a package.
- **Fixture/argument errors**: Some tests expect pytest fixtures (tmp_path) but are run with unittest, causing missing argument errors (test_error_handler).
- **Class instantiation errors**: Some classes require arguments (e.g., ScriptManager, UIManager, StateManager) that are not provided or are mocked incorrectly.
- **Method/attribute errors**: Some tests call methods as callables when they are properties (e.g., is_available in TTSManager).
- **Logic error**: test_load_data_invalid_structure in test_data_manager.py expects False but gets True (likely a bug in DataManager or the test).

## Recommendations
- Fix import/module path issues: Standardize sys.path usage or refactor imports for local test runs.
- Adjust test frameworks: Use pytest for tests with fixtures, or refactor tests to work with unittest only.
- Update test templates: Ensure required constructor arguments and attributes are provided/mocked.
- Fix logic in DataManager or its test for invalid structure.
- Review and update test_error_handler.py to work with unittest or switch to pytest.
- Review all new test templates for correct instantiation and attribute mocking.

---

_Last updated: 2026-04-11_
