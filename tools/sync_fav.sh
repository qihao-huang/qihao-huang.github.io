#!/usr/bin/env bash
# Sync favorites dashboard: Chrome bookmarks + Zhihu → fav.html
# Usage: ./tools/sync_fav.sh [--no-zhihu] [--llm-tags] [--llm-limit N]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[fav] Running generate_fav.py ..."
python3 tools/generate_fav.py "$@"

echo "[done] fav.html updated."
