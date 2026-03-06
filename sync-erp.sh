#!/usr/bin/env bash
#
# Sync content from ERPNext to Hugo site
# Requires VPN access to erp.kartoza.com
#
# Usage:
#   ./sync-erp.sh                    # Sync all content (uses cache)
#   ./sync-erp.sh --force            # Force refresh, ignore cache
#   ./sync-erp.sh --only portfolio   # Sync only portfolio items
#   ./sync-erp.sh --only blog        # Sync only blog articles
#   ./sync-erp.sh --only training    # Sync only training content
#   ./sync-erp.sh --dry-run          # Test without writing files
#   ./sync-erp.sh --help             # Show all options
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables from .env file
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo "Error: .env file not found"
    echo ""
    echo "Create it from the example:"
    echo "  cp .env.example .env"
    echo "  # Then edit .env with your ERPNext credentials"
    exit 1
fi

# Check for required credentials
if [ -z "$ERPNEXT_API_URL" ] || [ -z "$ERPNEXT_API_KEY" ] || [ -z "$ERPNEXT_API_SECRET" ]; then
    echo "Error: ERPNext credentials not configured in .env"
    echo ""
    echo "Required variables:"
    echo "  ERPNEXT_API_URL=https://erp.kartoza.com"
    echo "  ERPNEXT_API_KEY=your_api_key"
    echo "  ERPNEXT_API_SECRET=your_api_secret"
    exit 1
fi

# Run the sync script
echo "Syncing content from $ERPNEXT_API_URL..."
echo ""

nix develop --command ./scripts/sync-content-from-erpnext.py "$@"
