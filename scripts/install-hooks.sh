#!/usr/bin/env bash
#
# Install git hooks for the Kartoza Hugo project.
#
# Usage: ./scripts/install-hooks.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
HOOKS_SRC="$SCRIPT_DIR/hooks"
HOOKS_DST="$PROJECT_DIR/.git/hooks"

echo "Installing git hooks..."

if [[ ! -d "$HOOKS_SRC" ]]; then
    echo "Error: Hooks source directory not found: $HOOKS_SRC"
    exit 1
fi

if [[ ! -d "$HOOKS_DST" ]]; then
    echo "Error: Git hooks directory not found: $HOOKS_DST"
    echo "Are you in a git repository?"
    exit 1
fi

# Install each hook
for hook in "$HOOKS_SRC"/*; do
    if [[ -f "$hook" ]]; then
        hook_name=$(basename "$hook")
        echo "  Installing $hook_name..."
        cp "$hook" "$HOOKS_DST/$hook_name"
        chmod +x "$HOOKS_DST/$hook_name"
    fi
done

echo ""
echo "Git hooks installed successfully!"
echo ""
echo "Installed hooks:"
ls -la "$HOOKS_DST" | grep -v '\.sample$' | grep -v '^total' | grep -v '^\.' | awk '{print "  " $NF}'
