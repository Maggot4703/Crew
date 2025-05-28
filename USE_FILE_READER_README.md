# Use File Reader Tools

This directory contains utilities for reading "use-*.txt" files aloud using text-to-speech.

## 1. GUI Version (`read_use_file.py`)

A graphical user interface for selecting and reading use files.

### Features

- File browser with preview
- Adjustable reading speed and volume
- Start/stop controls
- Clean formatting of technical content for better reading

### Usage

```bash
./read_use_file.py
```

or

```bash
python3 read_use_file.py
```

## 2. Command Line Version (`read_use_file_cli.py`)

A simpler command-line utility for quickly reading use files.

### Features

- List all available use-*.txt files
- Read files by number or name
- Adjustable reading speed

### Usage

```bash
# List all available files
./read_use_file_cli.py --list

# Read a specific file by number
./read_use_file_cli.py --file 1

# Read a specific file by name (partial matching)
./read_use_file_cli.py --file Docker

# Change the reading speed (words per minute)
./read_use_file_cli.py --file Docker --rate 180
```

## 3. Shell Script Helper (`read_use.sh`)

A convenient shell script for quick access to any use file.

### Features

- Simple one-command access to any use file
- Shows available files if no name is provided

### Usage

```bash
# Show available use files
./read_use.sh

# Read a specific file by name
./read_use.sh Docker

# Read a specific file with partial name matching
./read_use.sh JS  # Will find use-Javascript.txt
```

## Requirements

These tools require the pyttsx3 library, which will be automatically installed if missing.

## Notes

- Press Ctrl+C to stop reading at any time in the CLI version
- The tools search for use-*.txt files in the current directory and all subdirectories
- Duplicate files (same name in different directories) are handled by only showing one copy
