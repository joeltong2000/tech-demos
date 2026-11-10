#!/usr/bin/env bash
# Deterministic offline happy path for all four variants (no API keys).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
export PATH="${HOME}/.dotnet:${HOME}/.local/bin:${PATH:-}"
export AF_CHAT_MODE="${AF_CHAT_MODE:-scripted}"

echo "======= Microsoft Agent Framework skills demo (offline) ======="
echo
dotnet run --project "$ROOT/dotnet/baseline"
echo
echo "----------------------------------------------------------------"
echo
dotnet run --project "$ROOT/dotnet/with-skill"
echo
echo "----------------------------------------------------------------"
echo
(cd "$ROOT/python" && uv run python baseline.py)
echo
echo "----------------------------------------------------------------"
echo
(cd "$ROOT/python" && uv run python with_skill.py)
echo
echo "======= done ======="
