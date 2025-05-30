#!/bin/bash
# Enhanced wrapper script to run read_use_file.py with the virtual environment
# Supports TTS functionality and proper signal handling

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/.venv/bin/python"
MAIN_SCRIPT="$SCRIPT_DIR/read_use_file.py"
LOG_FILE="$SCRIPT_DIR/read_use_file.log"

# Color output for better visibility
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error handling function
error_exit() {
    echo -e "${RED}Error: $1${NC}" >&2
    log "ERROR: $1"
    exit 1
}

# Success message function
success() {
    echo -e "${GREEN}$1${NC}"
    log "SUCCESS: $1"
}

# Warning message function
warn() {
    echo -e "${YELLOW}Warning: $1${NC}"
    log "WARNING: $1"
}

# Info message function
info() {
    echo -e "${BLUE}$1${NC}"
    log "INFO: $1"
}

# Signal handler for graceful shutdown (preserves TTS)
cleanup() {
    info "Received interrupt signal. Allowing TTS to complete..."
    # Don't kill the Python process immediately - let it handle graceful shutdown
    if [[ -n "${PYTHON_PID:-}" ]]; then
        # Send SIGTERM first (allows graceful shutdown)
        kill -TERM "$PYTHON_PID" 2>/dev/null || true
        
        # Wait a bit for graceful shutdown
        sleep 2
        
        # If still running, send SIGKILL as last resort
        if kill -0 "$PYTHON_PID" 2>/dev/null; then
            warn "Process still running, forcing termination..."
            kill -KILL "$PYTHON_PID" 2>/dev/null || true
        fi
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Validation checks
info "Starting read_use_file with virtual environment..."

# Check if virtual environment exists
if [[ ! -d "$SCRIPT_DIR/.venv" ]]; then
    error_exit "Virtual environment not found at $SCRIPT_DIR/.venv"
fi

# Check if Python executable exists in venv
if [[ ! -x "$PYTHON" ]]; then
    error_exit "Python executable not found or not executable: $PYTHON"
fi

# Check if main script exists
if [[ ! -f "$MAIN_SCRIPT" ]]; then
    error_exit "Main script not found: $MAIN_SCRIPT"
fi

# Check Python version
PYTHON_VERSION=$("$PYTHON" --version 2>&1)
info "Using Python: $PYTHON_VERSION"

# Check if required packages are available
info "Checking TTS dependencies..."
if ! "$PYTHON" -c "import pyttsx3" 2>/dev/null; then
    warn "pyttsx3 not available - TTS functionality will be disabled"
else
    success "TTS (pyttsx3) available"
fi

# Check for other common dependencies
for package in "pandas" "pathlib"; do
    if ! "$PYTHON" -c "import $package" 2>/dev/null; then
        warn "$package not available - some functionality may be limited"
    fi
done

# Enhanced argument processing
if [[ $# -eq 0 ]]; then
    info "No arguments provided. Running with default settings..."
    info "Usage: $0 [file_path] [additional_args...]"
    info "Available options:"
    info "  --help, -h     Show help"
    info "  --verbose, -v  Enable verbose output"
    info "  --no-tts      Disable text-to-speech"
    info "  --version     Show version information"
fi

# Handle special arguments
case "${1:-}" in
    --help|-h)
        info "Enhanced wrapper for read_use_file.py"
        info "This script runs read_use_file.py with proper virtual environment activation"
        info "and enhanced error handling while preserving TTS functionality."
        echo
        "$PYTHON" "$MAIN_SCRIPT" --help
        exit 0
        ;;
    --version)
        info "Wrapper script version 2.0"
        "$PYTHON" "$MAIN_SCRIPT" --version 2>/dev/null || info "Version info not available from main script"
        exit 0
        ;;
esac

# Create log entry for this run
log "========================================"
log "Starting new session with args: $*"
log "Python: $PYTHON"
log "Script: $MAIN_SCRIPT"
log "Working directory: $(pwd)"

# Run the main script with proper error handling
info "Executing: $MAIN_SCRIPT $*"
info "Press Ctrl+C to gracefully stop (allows TTS to finish)"

# Start the Python script in background to capture PID
"$PYTHON" "$MAIN_SCRIPT" "$@" &
PYTHON_PID=$!

# Wait for the process to complete
if wait "$PYTHON_PID"; then
    success "Script completed successfully"
    log "Script execution completed successfully"
    exit 0
else
    EXIT_CODE=$?
    if [[ $EXIT_CODE -eq 130 ]]; then
        # SIGINT (Ctrl+C)
        info "Script interrupted by user"
        log "Script interrupted by user (SIGINT)"
    else
        error_exit "Script failed with exit code: $EXIT_CODE"
    fi
    exit $EXIT_CODE
fi