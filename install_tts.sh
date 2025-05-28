#!/bin/bash
# Installation script for Use File Reader tools

echo "==== Use File Reader Tools - Dependency Installer ===="

# Check for Python and ability to create virtual environments
if ! command -v python3 &>/dev/null; then
  echo "ERROR: Python 3 is required but not installed."
  exit 1
fi

# Setup virtual environment
echo "Setting up Python virtual environment..."
if [ ! -d "tts_venv" ]; then
  python3 -m venv tts_venv || {
    echo "ERROR: Failed to create virtual environment. Make sure python3-venv is installed."
    echo "On Debian/Ubuntu: sudo apt-get install python3-venv"
    exit 1
  }
fi

# Activate virtual environment and install dependencies
echo "Installing Python dependencies..."
source tts_venv/bin/activate
pip install --upgrade pip
pip install pyttsx3

# Install system dependencies
echo "Installing system dependencies..."
if command -v apt-get &>/dev/null; then
  sudo apt-get update
  sudo apt-get install -y espeak libespeak-dev
elif command -v dnf &>/dev/null; then
  sudo dnf install -y espeak espeak-devel
elif command -v pacman &>/dev/null; then
  sudo pacman -S espeak
else
  echo "WARNING: Unknown distribution. Please install espeak manually."
fi

# Make scripts executable
echo "Setting execute permissions on scripts..."
chmod +x read_use_file.py
chmod +x read_use_file_cli.py
chmod +x read_use.sh

# Create wrapper scripts that use the virtual environment
echo "Creating virtual environment wrapper scripts..."

cat > read_use_venv.sh << 'WRAPPER'
#!/bin/bash
# Wrapper script to run read_use_file_cli.py with the virtual environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/tts_venv/bin/python"
"$PYTHON" "$SCRIPT_DIR/read_use_file_cli.py" --file "$@"
WRAPPER

cat > read_use_file_venv.sh << 'WRAPPER'
#!/bin/bash
# Wrapper script to run read_use_file.py with the virtual environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/tts_venv/bin/python"
"$PYTHON" "$SCRIPT_DIR/read_use_file.py" "$@"
WRAPPER

cat > read_use_file_cli_venv.sh << 'WRAPPER'
#!/bin/bash
# Wrapper script to run read_use_file_cli.py with the virtual environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/tts_venv/bin/python"
"$PYTHON" "$SCRIPT_DIR/read_use_file_cli.py" "$@"
WRAPPER

chmod +x read_use_venv.sh
chmod +x read_use_file_venv.sh
chmod +x read_use_file_cli_venv.sh

echo
echo "==== Installation Complete ===="
echo "You can now use the following commands with the virtual environment:"
echo "  ./read_use_file_venv.sh          - GUI version"
echo "  ./read_use_file_cli_venv.sh --list - CLI version (list files)"
echo "  ./read_use_venv.sh Docker        - Quick access to read a specific file"
echo
echo "Or activate the virtual environment manually:"
echo "  source tts_venv/bin/activate"
echo "  ./read_use_file.py"
echo "  (when done) deactivate"
echo
