# Crew Manager

Crew Manager is a data processing and GUI tool for managing crew or NPC data. It supports batch image overlays, CSV/Excel analysis, and provides a user-friendly interface for data manipulation and reporting.

## Features

- Batch image grid overlays for vehicle/crew analysis
- Defaults aligned with the local `CARDCUTTER/CardCutter` workspace for shared image inputs and outputs
- Import and analyze CSV/Excel data
- GUI for viewing, filtering, grouping, and exporting crew data
- `Crew Chatbot` window with persistent history, optional voice input/output, and a rule-based reply path with DeepSeek HTTP fallback
- `Crew Multi-User Chat` window with role-based local messaging, file attachments, and extensibility hooks for richer bot-assisted collaboration
- Customizable configuration
- Caching and database support

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/Maggot4703/Crew.git
    cd Crew
    ```

2. Create and activate a virtual environment:
    ```bash
    cd /home/me/Notebooks/CREW
    uv sync
    ```

3. Install dependencies:
    ```bash
    uv sync
    ```

## Usage

- To run the main data processing script:
    ```bash
    uv run python Crew.py
    ```
- To launch the GUI:
    ```bash
    uv run python gui.py
    ```
- Place data files in the `data` directory.
- Crew's default image-processing paths now point at `CARDCUTTER/CardCutter/gimp` for inputs and
  `CARDCUTTER/CardCutter/` for generated `Cars*.png` outputs and `Cars1_rectangles/` tiles, unless
  overridden with `CREW_INPUT_DIR`, `CREW_OUTPUT_DIR`, `--input-dir`, or `--output-dir`.

## Documentation

- `docs/README.md` - documentation build notes for the production Crew app
- `docs/index.rst` - Sphinx landing page
- `ReadMine.py` - production ReadMine generator
- `Reading Now/README.md` - generated ReadMine output layout

## Development

- Code is formatted with [black](https://github.com/psf/black).
- Linting is done using [flake8](https://flake8.pycqa.org/).
- Automated tests are located in the `tests/` directory.

## Testing

Run tests using pytest:
```bash
pytest
```

Run a single test file:
```bash
pytest tests/test_gui_complete.py
```

Run a single test:
```bash
pytest tests/test_basic.py::TestBasicApp::test_module_imports
```

### ReadMine and targeted test runs

Some test runs in `CREW/Crew` currently hit a package import problem via `CREW/Crew/__init__.py`, which can interrupt broad `pytest` collection before the target test file runs.

When that happens, targeted direct execution is often more reliable for ReadMine-focused work:

```bash
cd /home/me/Notebooks/CREW/Crew
python -m py_compile ReadMine.py tests/test_readmine_features.py tests/test_readmine_progress.py
python tests/test_readmine_features.py
python tests/test_readmine_progress.py
```

Use the normal `pytest` flow when it works for the area you are changing, but keep the direct test path in mind for ReadMine-specific validation.

## Chat windows: current state

The GUI currently exposes two separate chat surfaces in `gui.py`:

- `Crew Chatbot` stores conversation history in `~/.crew_chat_history.json`, supports search/filter, import/export, optional speech-to-text, optional text-to-speech, and falls back to `deepseek_integration.py` for uncategorized prompts.
- `Crew Multi-User Chat` uses `message_router.py` for in-memory message routing between fixed crew roles, supports attachments copied into `~/.crew_chat_files`, and is structured to allow bot replies alongside user messages.

Important implementation notes for future work:

- `generate_bot_reply()` in `gui.py` is currently a keyword/rule-based helper with a final HTTP POST fallback to `http://localhost:8000/v1/completions`.
- The chat windows read `self.llm_backend_var` if present and otherwise default to `ollama`; no backend selector wiring is currently documented in `CREW/Crew/`.
- `gui.py` imports `strategies.user_strategy.UserStrategy` and `strategies.referee_strategy.RefereeStrategy`; the current production fallback implementations live under `CREW/Crew/strategies/`.
- `message_router.py` is local and in-memory only, so `Crew Multi-User Chat` does not yet synchronize messages across processes or devices on the network.
- Voice features depend on optional runtime components such as `SpeechRecognition`, microphone access, and a working TTS/audio stack.

## Raspberry Pi and LAN direction

For Raspberry Pi 500 / Raspberry Pi 4B work, the safest path is to keep these Tk windows as lightweight clients and move model inference into a separate local-network service. That preserves the current GUI behavior while allowing retries, streaming, backend switching, and offline fallbacks to be added incrementally.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License


## Startup Code

```bash
cd /home/me/Notebooks/CREW/Crew
uv sync
uv run python Crew.py
```
