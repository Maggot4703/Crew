#!/usr/bin/env bash
# Setup helper for Ollama model runner (instructions + optional automated steps)
# Usage: bash setup_ollama.sh [--pull MODEL]
# Note: This script does NOT attempt to install Ollama automatically. Follow official docs if binary missing.

set -euo pipefail
MODEL_DEFAULT="deepseek-r1:1.5b"
PULL_MODEL="${MODEL_DEFAULT}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pull)
      shift
      PULL_MODEL="$1"
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [--pull MODEL]"
      exit 0
      ;;
    *)
      echo "Unknown arg: $1"
      exit 1
      ;;
  esac
done

echo "Checking for 'ollama' binary..."
if ! command -v ollama >/dev/null 2>&1; then
  cat <<'EOF'
Ollama binary not found on PATH.
Please install Ollama following official instructions:
  https://ollama.ai/docs/installation
Common steps (Linux/macOS):
  # macOS (Homebrew)
  brew install ollama

  # Or follow the installer script page on Ollama website

After installing, re-run this script to pull a model.
EOF
  exit 0
fi

echo "ollama found: $(ollama --version 2>/dev/null || echo '[version unknown]')"

echo "Pulling model: ${PULL_MODEL}"
set -x
ollama pull "${PULL_MODEL}"
set +x

echo "Model pull finished. Start the ollama server with:"
cat <<EOF
  ollama serve &
  # or run in foreground for debugging:
  ollama serve

Verify the API is reachable locally:
  curl -sS http://localhost:11434/api/tags | jq .

If running the server on a remote machine (me@home), use that machine's IP and ensure port 11434 is reachable from the Crew host.
EOF

exit 0
