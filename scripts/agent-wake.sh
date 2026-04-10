#!/bin/bash
set -euo pipefail

ROOT="${YOMEMS_ROOT:-.yomems}"
PROJECT="${1:-}"
INTENT="${2:-project-onboard}"
KEYWORD="${3:-}"
TASK_ID="${4:-}"
LIMIT="${YOMEMS_WAKE_LIMIT:-3}"

if [ -z "$PROJECT" ]; then
    echo "Usage: $0 <project> [intent] [keyword] [task_id]" >&2
    exit 1
fi

PYTHONPATH="${PYTHONPATH:-$(pwd)/src}" exec python3 -m yomems wake \
  --root "$ROOT" \
  --project "$PROJECT" \
  --intent "$INTENT" \
  --keyword "$KEYWORD" \
  --task-id "$TASK_ID" \
  --limit "$LIMIT"
