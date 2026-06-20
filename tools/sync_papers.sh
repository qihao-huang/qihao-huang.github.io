#!/usr/bin/env bash
# One-command paper library sync: detect → generate → verify → commit → push
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VENV_PY="tools/.venv/bin/python"
VENV_PIP="tools/.venv/bin/pip"
GEN="tools/generate_papers.py"
DETECT="tools/sync_papers.py"

ONLINE=1
DO_PUSH=1
DO_COMMIT=1
DETECT_ONLY=0
GEN_ARGS=()

usage() {
  cat <<'EOF'
Usage: tools/sync_papers.sh [options] [-- extra generate_papers.py args]

Options:
  --no-online     Skip online date enrichment
  --no-push       Commit but do not push
  --no-commit     Generate only, skip git commit/push
  --detect-only   Report new/updated/total PDF counts and exit
  -h, --help      Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-online)   ONLINE=0; shift ;;
    --no-push)     DO_PUSH=0; shift ;;
    --no-commit)   DO_COMMIT=0; DO_PUSH=0; shift ;;
    --detect-only) DETECT_ONLY=1; shift ;;
    -h|--help)     usage; exit 0 ;;
    --)            shift; GEN_ARGS+=("$@"); break ;;
    *)             GEN_ARGS+=("$1"); shift ;;
  esac
done

ensure_venv() {
  if [[ ! -x "$VENV_PY" ]]; then
    echo "[venv] Creating tools/.venv ..."
    python3 -m venv tools/.venv
  fi
  if ! "$VENV_PY" -c "import fitz" 2>/dev/null; then
    echo "[venv] Installing requirements ..."
    "$VENV_PIP" install -r tools/requirements.txt
  fi
}

run_detect() {
  ensure_venv
  "$VENV_PY" "$DETECT" --detect-only
}

if [[ "$DETECT_ONLY" -eq 1 ]]; then
  run_detect
  exit 0
fi

ensure_venv

echo "[detect] Scanning PDF libraries vs cache ..."
DETECT_OUT="$(run_detect)"
echo "$DETECT_OUT"
NEW=$(echo "$DETECT_OUT" | sed -n 's/^NEW=\([0-9]*\).*/\1/p')
UPDATED=$(echo "$DETECT_OUT" | sed -n 's/^UPDATED=\([0-9]*\).*/\1/p')
TOTAL=$(echo "$DETECT_OUT" | sed -n 's/^TOTAL=\([0-9]*\).*/\1/p')
NEW=${NEW:-0}
UPDATED=${UPDATED:-0}
TOTAL=${TOTAL:-0}

if [[ "$ONLINE" -eq 0 ]]; then
  GEN_ARGS=(--no-online "${GEN_ARGS[@]}")
fi

# Incremental LLM summaries when API key is available (two-tier: ~74% rules, ~26% LLM)
if [[ -n "${OPENAI_API_KEY:-}" ]]; then
  echo "[llm] OPENAI_API_KEY set — incremental LLM summaries (limit 50/run) ..."
  GEN_ARGS=(--llm-summary --llm-limit 50 "${GEN_ARGS[@]}")
fi

echo "[generate] Running generate_papers.py ${GEN_ARGS[*]:-} ..."
"$VENV_PY" "$GEN" "${GEN_ARGS[@]}"

echo "[verify] Sanity check papers.html ..."
"$VENV_PY" "$DETECT" --sanity-check

if [[ "$DO_COMMIT" -eq 0 ]]; then
  echo "[done] Generated papers.html (skipped git)."
  exit 0
fi

# Safety: abort on merge/rebase conflicts
if git rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1 \
   || git rev-parse -q --verify REBASE_HEAD >/dev/null 2>&1 \
   || [[ -d .git/rebase-merge ]]; then
  echo "ERROR: merge/rebase in progress — resolve before syncing." >&2
  exit 1
fi

git add papers.html
git add tools/snapshots/history.json 2>/dev/null || true
git add tools/sync_papers.sh tools/sync_papers.py tools/generate_papers.py 2>/dev/null || true

if git diff --cached --quiet; then
  echo "[git] Nothing staged — skipping commit."
  exit 0
fi

if [[ "$NEW" -gt 0 ]]; then
  MSG="chore(papers): sync ${NEW} new papers from auto_ai/physical_ai"
elif [[ "$UPDATED" -gt 0 ]]; then
  MSG="chore(papers): update ${UPDATED} changed papers from auto_ai/physical_ai"
else
  MSG="chore(papers): regenerate papers.html from auto_ai/physical_ai"
fi

git commit -m "$MSG" -m "Total PDFs scanned: ${TOTAL}. Regenerate papers.html from iCloud libraries."

COMMIT=$(git rev-parse --short HEAD)
echo "[git] Committed ${COMMIT}: ${MSG}"

if [[ "$DO_PUSH" -eq 0 ]]; then
  echo "[git] Skipped push (--no-push)."
  exit 0
fi

if git push; then
  echo "[git] Push OK."
else
  echo "ERROR: git push failed — resolve (e.g. git pull --rebase) and retry." >&2
  exit 1
fi
