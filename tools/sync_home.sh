#!/usr/bin/env bash
# Sync homepage Zhihu stats into index.html
# Usage: ./tools/sync_home.sh [--dry-run]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[home] Fetching Zhihu stats ..."
python3 tools/fetch_zhihu_stats.py "$@"

echo "[done] index.html updated."
