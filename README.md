# Crew Manager

Crew Manager is a data processing and GUI tool for managing crew or NPC data. It supports batch image overlays, CSV/Excel analysis, and provides a user-friendly interface for data manipulation and reporting.

## Features

- Batch image grid overlays for vehicle/crew analysis
- Import and analyze CSV/Excel data
- GUI for viewing, filtering, grouping, and exporting crew data
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
    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

- To run the main data processing script:
    ```bash
    python Crew.py
    ```
- To launch the GUI:
    ```bash
    python gui.py
    ```
- Place data files in the `data` directory.

## Development

- Code is formatted with [black](https://github.com/psf/black).
- Linting is done using [flake8](https://flake8.pycqa.org/).
- Automated tests are located in the `tests/` directory.

## Testing

Run tests using pytest:
```bash
pytest
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License
