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

### Python Dependencies

- **pyttsx3**: Python text-to-speech library (automatically installed if missing)

### System Dependencies

- **espeak**: Speech synthesis engine used by pyttsx3 on Linux
- **libespeak-dev**: Development files for espeak (may be required on some systems)
- **python3-espeak**: Python bindings for espeak (optional)

The `read_use.sh` script automatically checks for and installs these dependencies if they're missing.

### Installation Methods

#### Automated Installation with Virtual Environment (Recommended)

Use the provided installation script:

```bash
./install_tts.sh
```

This script will:

- Create a Python virtual environment (`tts_venv`) if it doesn't exist if it doesn't exist
- Install pyttsx3 in the virtual environment
- Install espeak and related system dependencies
- Make all scripts executable
- Create virtual environment wrapper scripts for convenience

After installation, use the following wrapper scripts:

- `./read_use_file_venv.sh` - GUI version
- `./read_use_file_cli_venv.sh --list` - CLI version (list all available files)
- `./read_use_file_cli_venv.sh --file Docker` - CLI version (read specific file)
- `./read_use_venv.sh Docker` - Quick access version

#### Semi-Automated Installation

The `read_use.sh` script includes built-in dependency checking (but doesn't use a virtual environment):

```bash
./read_use.sh
```

#### Manual Installation

If you prefer to install dependencies manually:

```bash
# Create and activate a virtual environment
python3 -m venv tts_venv
source tts_venv/bin/activate

# Install Python dependencies in the virtual environment
pip install pyttsx3

# Install system dependencies (Debian/Ubuntu)
sudo apt-get install espeak libespeak-dev

# For other Linux distributions, use the appropriate package manager
# Fedora/CentOS: sudo dnf install espeak espeak-devel
# Arch: sudo pacman -S espeak
```

## Notes

- Press Ctrl+C to stop reading at any time in the CLI version
- The tools search for use-*.txt files in the current directory and all subdirectories
- Duplicate files (same name in different directories) are handled by only showing one copy
- On first run, there might be a delay as the required dependencies are installed
