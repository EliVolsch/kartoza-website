#!/usr/bin/env bash
#
# Build script for Kartoza Hugo site
# Runs pre-build tasks then builds with Hugo
#
# Usage:
#   ./scripts/build.sh [hugo-args]
#
# Examples:
#   ./scripts/build.sh                    # Build production site
#   ./scripts/build.sh --environment dev  # Build development site
#   ./scripts/build.sh --minify          # Build with minification
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Run pre-build tasks
"$SCRIPT_DIR/pre-build.sh"

# Build with Hugo
echo "→ Building site with Hugo..."
hugo "$@"

echo ""
echo "✓ Build completed successfully"
