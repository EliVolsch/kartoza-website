#!/usr/bin/env bash
#
# Development server script
# Runs pre-build then starts Hugo development server
#
# Usage:
#   ./scripts/dev-server.sh
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Run pre-build tasks
"$SCRIPT_DIR/pre-build.sh"

# Start Hugo development server
echo "→ Starting Hugo development server..."
hugo server
