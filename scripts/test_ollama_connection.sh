#!/usr/bin/env bash
# Test connectivity to an Ollama server and basic model generation
# Usage: bash test_ollama_connection.sh [host]

set -euo pipefail
HOST="${1:-localhost}"
BASE_URL="http://${HOST}:11434"
MODEL="${2:-deepseek-r1:1.5b}"

echo "Checking /api/tags on ${BASE_URL}..."
curl --fail -sS "${BASE_URL}/api/tags" | jq . || { echo "Failed to reach ${BASE_URL}/api/tags"; exit 2; }

echo "Testing generate endpoint (non-streaming) with model ${MODEL}..."
# The exact payload keys may vary by ollama version; this matches ollama_client.py usage.
PAYLOAD=$(jq -n --arg model "$MODEL" --arg prompt "Hello from Crew test" '{model: $model, prompt: $prompt, stream: false}')

curl --fail -sS -X POST "${BASE_URL}/api/generate" -H 'Content-Type: application/json' -d "${PAYLOAD}" | jq . || { echo "Generate request failed"; exit 3; }

echo "Ollama connectivity and generate request succeeded."
exit 0
