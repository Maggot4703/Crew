# Suggestions: Critical Runtime Fixes (Option 1)

Date: 25 March 2026

## Scope

- Included in this pass: critical/runtime defects, launcher ambiguity, exception safety in active paths, duplicate runtime definitions.
- Explicitly excluded in this pass: bulk lint/style cleanup not tied to runtime behavior.

## P0 Findings and Actions

### P0-1 Startup integrity in `gui_main_function.py`

- Root cause: startup path previously had fragile optional icon handling with broad catch.
- Recommended fix: keep one startup flow and narrow exception handling for optional icon load.
- Implemented:
  - Kept single canonical startup in `Crew/gui_main_function.py`.
  - Replaced broad icon catch with explicit `(tk.TclError, OSError)` and warning log.
- Status: Completed.

### P0-2 Python version alignment

- Root cause: potential environment drift if version constraints diverge.
- Recommended fix: enforce one real baseline version across project configs.
- Implemented/verified:
  - `pyproject.toml` requires `>=3.11`.
  - `Crew/Pipfile` requires `3.11`.
- Status: Completed (already aligned).

## P1 Findings and Actions

### P1-1 Canonical launcher path

- Root cause: multiple launch files each owning startup logic.
- Recommended fix: route all launchers through one canonical startup function.
- Implemented:
  - `Crew/gui_main_function.py` is canonical startup.
  - `Crew/run_gui.py` is an explicit compatibility wrapper to canonical `main()`.
  - `Crew/launch_gui.py` is a legacy compatibility wrapper to canonical `main()` with structured logging and explicit exit codes.
- Status: Completed.

### P1-2 Bare exception in active data loading path

- Root cause: bare `except:` in Excel import fallback hides intent and diagnostics.
- Recommended fix: catch specific expected failures and log fallback reason.
- Implemented:
  - `Crew/data_manager.py` now catches `(ValueError, ImportError, OSError)` in Excel fallback and logs retry engine.
- Status: Completed.

### P1-3 Critical duplicate method definition in active GUI

- Root cause: duplicate `load_default_data` method in canonical GUI class causes shadowing and maintenance ambiguity.
- Recommended fix: keep a single authoritative implementation.
- Implemented:
  - Removed duplicate `load_default_data` from `Crew/gui.py`.
- Status: Completed.

### P1-4 Hard-coded absolute path risk

- Root cause: startup resources can break when tied to machine-specific paths.
- Recommended fix: resolve startup assets relative to repository/module path.
- Implemented:
  - Canonical startup uses repository-relative icon resolution via `pathlib`.
- Status: Completed.

## P2 Backlog (Deferred by Scope)

### P2-1 GUI duplicate module migration

- Canonical runtime file: `Crew/gui.py`.
Migration plan:

1. Freeze imports to canonical module only.
2. Mark `Crew/gui_copy.py` and `Crew/gui copy.py` as deprecated wrappers or archive candidates.
3. Remove archived duplicates after one release cycle of clean startup/usage telemetry.

### P2-2 Error module canonicalization

- Canonical error hierarchy: `Crew/errors.py`.
Migration plan:

1. Redirect new imports to `Crew/errors.py`.
2. Keep `Crew/error_handler.py` as compatibility layer only.
3. Remove duplicate exception definitions from active call sites incrementally.

## Verification Checklist

### Executed checks

1. Syntax check of changed runtime files:
Command: `python -m py_compile Crew/gui.py Crew/data_manager.py Crew/gui_main_function.py Crew/run_gui.py Crew/launch_gui.py`
Result: Pass.

1. Launcher smoke test from workspace root:
Command: `timeout 5s python Crew/run_gui.py`
Result: failed with X server `BadLength` error (`EXIT:1`) in this environment.

1. Launcher smoke test from project folder:
Command: `cd Crew && timeout 5s python run_gui.py`
Result: failed with X server `BadLength` error (`EXIT:1`) in this environment.

### Pending manual UI checks

1. Confirm default CSV appears in Data View.
2. Open a CSV manually and confirm table population and row-details selection behavior.
3. Re-run runtime diagnostics and confirm remaining issues are mostly lint/style.

### Follow-up targeted check (same scope)

1. Re-ran launcher smoke test from workspace root:
Command: `timeout 5s python Crew/run_gui.py`
Result: failed with X server `BadLength` error (`EXIT:1`) in this environment.

1. Re-ran launcher smoke test from project folder:
Command: `cd Crew && timeout 5s python run_gui.py`
Result: warning for unknown config key `tts_settings`, then X server `BadLength` error (`EXIT:1`) in this environment.

## Summary

- Critical/runtime-focused fixes were applied without broad lint cleanup.
- The active startup path and launcher behavior are now canonicalized.
- Remaining high-volume lint/style issues are intentionally deferred and should be tracked as a separate non-runtime cleanup pass.
