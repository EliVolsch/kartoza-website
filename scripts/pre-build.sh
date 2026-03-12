#!/usr/bin/env bash
#
# Pre-build script for Hugo
# Runs before Hugo builds the site to fetch fresh data
#
# This script:
# - Syncs training schedule from ERPNext with caching
# - Can be run manually or as part of CI/CD
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "======================================"
echo "  Kartoza Hugo Pre-Build"
echo "======================================"
echo ""

# Check if we're in development or production
if [ "${HUGO_ENV}" = "production" ]; then
    CACHE_TTL=1  # 1 hour for production builds
    echo "→ Running in PRODUCTION mode (cache TTL: ${CACHE_TTL}h)"
else
    CACHE_TTL=6  # 6 hours for development
    echo "→ Running in DEVELOPMENT mode (cache TTL: ${CACHE_TTL}h)"
fi

# Sync all content from ERPNext
echo ""
echo "→ Syncing content from ERPNext..."
if python3 "$SCRIPT_DIR/sync-content-from-erpnext.py" --cache-ttl "$CACHE_TTL" --only all; then
    echo "  ✓ Content synced successfully"
else
    echo "  ⚠ Content sync failed (using existing/cached data)"
    # Don't fail the build if sync fails - use existing data
fi

echo ""
echo "======================================"
echo "  Pre-build completed"
echo "======================================"
echo ""
