#!/bin/bash
set -euo pipefail

ROOT="${YOMEMS_ROOT:-.yomems}"
MODE="${1:-}"
KIND="${2:-}"
ID="${3:-}"
PROJECT="${4:-}"
TOPIC="${5:-}"
SUMMARY="${6:-}"
TASK_ID="${7:-}"

if [ -z "$MODE" ] || [ -z "$KIND" ] || [ -z "$ID" ] || [ -z "$SUMMARY" ]; then
    echo "Usage: $0 <suggest|prepare|propose|save|check> <kind> <id> <project> <topic> <summary> [task_id]" >&2
    exit 1
fi

SCOPE="project"
if [ "$KIND" = "identity_fact" ]; then
    SCOPE="global"
    PROJECT=""
elif [ "$KIND" = "active_task" ]; then
    SCOPE="task"
fi

if [ "$MODE" = "check" ] || [ "$MODE" = "prepare" ]; then
  TMP_FILE="$(mktemp)"
  cat > "$TMP_FILE" <<EOF
{"id":"$ID","kind":"$KIND","scope":"$SCOPE","project":"$PROJECT","task_id":"$TASK_ID","topic":"$TOPIC","content":"$SUMMARY"}
EOF
  PYTHONPATH="${PYTHONPATH:-$(pwd)/src}" exec python3 -m yomems "$MODE" \
    --root "$ROOT" \
    --input "$TMP_FILE"
fi

PYTHONPATH="${PYTHONPATH:-$(pwd)/src}" exec python3 -m yomems remember \
  --root "$ROOT" \
  --mode "$MODE" \
  --id "$ID" \
  --kind "$KIND" \
  --scope "$SCOPE" \
  --project "$PROJECT" \
  --task-id "$TASK_ID" \
  --topic "$TOPIC" \
  --summary "$SUMMARY"
