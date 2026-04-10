#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TARGET_NAME="${YOMEMS_TARGET_NAME:-Claude Code}"
TARGET_SKILLS_DIR="${YOMEMS_TARGET_DIR:-${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}}"
TARGET_BUNDLE_NAME="${YOMEMS_BUNDLE_NAME:-yomems}"
TARGET_DIR="$TARGET_SKILLS_DIR/$TARGET_BUNDLE_NAME"
LEGACY_TARGET_DIR="$TARGET_SKILLS_DIR/.yomems"
COMMAND="${1:-help}"

show_help() {
    cat <<EOF
YOMems Installer

Usage:
  $0 install
  $0 remove
  $0 help

Environment overrides:
  YOMEMS_TARGET_NAME   Target host display name
  YOMEMS_TARGET_DIR    Target host skills directory
  YOMEMS_BUNDLE_NAME   Installed bundle directory name

Install target:
  target host: $TARGET_NAME
  skills root: $TARGET_SKILLS_DIR
  yomems dir: $TARGET_DIR
EOF
}

install_yomems() {
    mkdir -p "$TARGET_DIR/src" "$TARGET_DIR/design" "$TARGET_DIR/examples" "$TARGET_DIR/schemas" "$TARGET_DIR/bin" "$TARGET_DIR/scripts" "$TARGET_DIR/templates"
    cp -r "$PROJECT_DIR/src/yomems" "$TARGET_DIR/src/"
    cp -r "$PROJECT_DIR/design/." "$TARGET_DIR/design/"
    cp -r "$PROJECT_DIR/examples/." "$TARGET_DIR/examples/"
    cp -r "$PROJECT_DIR/schemas/." "$TARGET_DIR/schemas/"
    cp -r "$PROJECT_DIR/templates/." "$TARGET_DIR/templates/"
    cp "$PROJECT_DIR/scripts/agent-wake.sh" "$TARGET_DIR/scripts/agent-wake.sh"
    cp "$PROJECT_DIR/scripts/agent-remember.sh" "$TARGET_DIR/scripts/agent-remember.sh"
    cp "$PROJECT_DIR/scripts/resolve-memory-root.sh" "$TARGET_DIR/scripts/resolve-memory-root.sh"
    cp "$PROJECT_DIR/README.md" "$TARGET_DIR/README.md"
    cp "$PROJECT_DIR/SKILL.md" "$TARGET_DIR/SKILL.md"
    cp "$PROJECT_DIR/pyproject.toml" "$TARGET_DIR/pyproject.toml"
    chmod +x "$TARGET_DIR/scripts/agent-wake.sh" "$TARGET_DIR/scripts/agent-remember.sh" "$TARGET_DIR/scripts/resolve-memory-root.sh"

    cat > "$TARGET_DIR/bin/yomems" <<EOF
#!/bin/bash
set -euo pipefail
PYTHONPATH="$TARGET_DIR/src" exec python3 -m yomems "\$@"
EOF
    chmod +x "$TARGET_DIR/bin/yomems"

    cat > "$TARGET_DIR/INSTALLATION" <<EOF
installed_at=$(date -Iseconds)
target_name=$TARGET_NAME
target_skills_dir=$TARGET_SKILLS_DIR
target_dir=$TARGET_DIR
EOF

    echo "Installed YOMems to: $TARGET_DIR"
    echo "Command wrapper: $TARGET_DIR/bin/yomems"
    echo "Agent helpers: $TARGET_DIR/scripts/agent-wake.sh , $TARGET_DIR/scripts/agent-remember.sh , $TARGET_DIR/scripts/resolve-memory-root.sh"
    echo "Default repository path: ./.yomems"

    if [ "$LEGACY_TARGET_DIR" != "$TARGET_DIR" ] && [ -d "$LEGACY_TARGET_DIR" ]; then
        rm -rf "$LEGACY_TARGET_DIR"
        echo "Removed legacy bundle: $LEGACY_TARGET_DIR"
    fi
}

remove_yomems() {
    if [ "$LEGACY_TARGET_DIR" != "$TARGET_DIR" ] && [ -d "$LEGACY_TARGET_DIR" ]; then
        rm -rf "$LEGACY_TARGET_DIR"
        echo "Removed legacy YOMems from: $LEGACY_TARGET_DIR"
    fi
    if [ -d "$TARGET_DIR" ]; then
        rm -rf "$TARGET_DIR"
        echo "Removed YOMems from: $TARGET_DIR"
    else
        echo "YOMems not installed at: $TARGET_DIR"
    fi
}

case "$COMMAND" in
    install)
        install_yomems
        ;;
    remove|uninstall)
        remove_yomems
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $COMMAND" >&2
        show_help >&2
        exit 1
        ;;
esac
