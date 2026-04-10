#!/bin/bash
set -euo pipefail

start_dir="${1:-$PWD}"
dir="$(cd "$start_dir" && pwd)"

find_ancestor_root() {
    local current="$1"
    while [ "$current" != "/" ]; do
        if [ -d "$current/.yomems" ]; then
            printf '%s\n' "$current/.yomems"
            return 0
        fi
        current="$(dirname "$current")"
    done
    return 1
}

if ancestor_root="$(find_ancestor_root "$dir")"; then
    printf '%s\n' "$ancestor_root"
    exit 0
fi

git_root=""
if git_root="$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null)"; then
    workspace_candidate="$(dirname "$git_root")/.yomems"
    if [ -d "$workspace_candidate" ]; then
        printf '%s\n' "$workspace_candidate"
        exit 0
    fi
fi

printf '%s\n' "$dir/.yomems"
