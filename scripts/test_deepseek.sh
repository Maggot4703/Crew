#!/usr/bin/env bash
# Test connectivity to a DeepSeek HTTP completions endpoint
# Usage: bash test_deepseek.sh [host] [port]

set -euo pipefail
HOST="${1:-localhost}"
PORT="${2:-8000}"
URL="http://${HOST}:${PORT}/v1/completions"

echo "Posting test completion request to ${URL}"
curl --fail -sS -X POST "${URL}" -H 'Content-Type: application/json' -d '{"prompt":"Hello from Crew test"}' | jq . || { echo "DeepSeek request failed"; exit 2; }

echo "DeepSeek connectivity test succeeded."
exit 0
