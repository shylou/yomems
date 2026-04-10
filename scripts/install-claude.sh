#!/bin/bash
set -euo pipefail

export YOMEMS_TARGET_NAME="Claude Code"
export YOMEMS_TARGET_DIR="${YOMEMS_TARGET_DIR:-$HOME/.claude/skills}"
export YOMEMS_BUNDLE_NAME="${YOMEMS_BUNDLE_NAME:-yomems}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/install.sh" "$@"
