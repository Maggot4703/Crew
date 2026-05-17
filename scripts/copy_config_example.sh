#!/usr/bin/env bash
set -euo pipefail

# Copy CREW LLM example config to local config.json if it doesn't exist.
# Intended for local developer/testing only. config.json is gitignored by design.
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR" || exit 1
EXAMPLE="config.llm.example.json"
TARGET="config.json"

if [ -f "$TARGET" ]; then
  echo "config.json already exists; leaving untouched"
  exit 0
fi

if [ ! -f "$EXAMPLE" ]; then
  echo "Example config not found: $EXAMPLE" >&2
  exit 1
fi

cp "$EXAMPLE" "$TARGET"
echo "Copied $EXAMPLE to $TARGET. Edit $TARGET with your host/IP and credentials as needed."
