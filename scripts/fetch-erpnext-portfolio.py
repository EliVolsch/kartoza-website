#!/usr/bin/env python3
"""
Fetch portfolio/project articles from ERPNext and create Hugo content files.

Only fetches new articles that don't exist locally to preserve local edits.

Environment variables:
    ERPNEXT_URL: ERPNext instance URL (default: https://erp.kartoza.com)
    ERPNEXT_API_KEY: API key for authentication
    ERPNEXT_API_SECRET: API secret for authentication

Usage:
    ./fetch-erpnext-portfolio.py [--dry-run] [--force] [--list]
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

import requests
import yaml
from dateutil import parser as date_parser


# Configuration
ERPNEXT_URL = os.environ.get('ERPNEXT_URL', 'https://erp.kartoza.com')
API_KEY = os.environ.get('ERPNEXT_API_KEY', '')
API_SECRET = os.environ.get('ERPNEXT_API_SECRET', '')

# ERPNext doctype for portfolio items - adjust based on your ERPNext setup
PORTFOLIO_DOCTYPE = os.environ.get('ERPNEXT_PORTFOLIO_DOCTYPE', 'Project')


def get_auth_headers() -> dict:
    """Get authentication headers for ERPNext API."""
    if API_KEY and API_SECRET:
        return {
            'Authorization': f'token {API_KEY}:{API_SECRET}'
        }
    return {}


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def fetch_portfolio_list() -> list[dict]:
    """Fetch list of portfolio items from ERPNext."""
    url = f"{ERPNEXT_URL}/api/resource/{PORTFOLIO_DOCTYPE}"
    params = {
        'filters': '[["status", "!=", "Cancelled"]]',
        'fields': '["name", "project_name", "customer", "status", "modified", "creation"]',
        'limit_page_length': 0
    }

    try:
        response = requests.get(url, params=params, headers=get_auth_headers(), timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('data', [])
    except requests.RequestException as e:
        print(f"Error fetching portfolio list: {e}")
        return []


def fetch_portfolio_detail(name: str) -> dict | None:
    """Fetch full portfolio item details from ERPNext."""
    url = f"{ERPNEXT_URL}/api/resource/{PORTFOLIO_DOCTYPE}/{name}"

    try:
        response = requests.get(url, headers=get_auth_headers(), timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('data', {})
    except requests.RequestException as e:
        print(f"Error fetching portfolio '{name}': {e}")
        return None


def portfolio_to_hugo_frontmatter(item: dict) -> dict:
    """Convert ERPNext portfolio item to Hugo front matter."""
    # Parse date
    creation_date = item.get('creation') or item.get('expected_start_date')
    if creation_date:
        try:
            dt = date_parser.parse(str(creation_date))
            date_str = dt.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            date_str = datetime.now().strftime('%Y-%m-%d')
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')

    title = item.get('project_name') or item.get('name', 'Untitled')

    front_matter = {
        'title': title,
        'description': item.get('notes', '')[:200] if item.get('notes') else f"Project: {title}",
        'thumbnail': '/img/portfolio/placeholder.png',
        'tags': ['Project'],
        'client': item.get('customer', ''),
        'date': date_str,
        'services': [],
        'erpnext_id': item.get('name', ''),
        'erpnext_modified': item.get('modified', ''),
    }

    # Add project type as tag if available
    if item.get('project_type'):
        front_matter['tags'].append(item['project_type'])

    return front_matter


def portfolio_to_hugo_content(item: dict) -> str:
    """Convert ERPNext portfolio content to Hugo markdown."""
    title = item.get('project_name') or item.get('name', 'Project')
    client = item.get('customer', '')
    notes = item.get('notes', '')

    # Build content
    content = f"""{{{{< block
    title="{title}"
    subtitle="Project"
    class="is-primary"
    sub-block-side="bottom"
>}}}}
{notes[:200] if notes else 'Project description.'}
{{{{< /block >}}}}

## Overview

{notes if notes else 'Project overview and details.'}

"""

    if client:
        content += f"""## Client

{client}

"""

    return content.strip()


def create_hugo_file(item: dict, content_dir: Path, dry_run: bool = False) -> tuple[str, str]:
    """
    Create Hugo markdown file from ERPNext portfolio item.

    Returns:
        Tuple of (filename, status)
    """
    title = item.get('project_name') or item.get('name', 'Untitled')
    slug = slugify(title)
    filename = f"{slug}.md"
    filepath = content_dir / filename

    # Check if file already exists
    if filepath.exists():
        return filename, 'Exists (skipped)'

    front_matter = portfolio_to_hugo_frontmatter(item)
    content = portfolio_to_hugo_content(item)

    # Build the file content
    file_content = "---\n"
    file_content += yaml.dump(front_matter, default_flow_style=False, allow_unicode=True)
    file_content += "---\n\n"
    file_content += content
    file_content += "\n"

    if not dry_run:
        filepath.write_text(file_content)
        return filename, 'Created'
    else:
        return filename, 'Would create'


def print_table(results: list[dict], dry_run: bool = False):
    """Print a formatted table of results."""
    if not results:
        print("\nNo portfolio items found.")
        return

    title_w = max(len(r['title'][:40]) for r in results)
    title_w = max(title_w, 10)

    print("\n" + "=" * (title_w + 45))
    if dry_run:
        print("ERPNEXT PORTFOLIO FETCH (DRY RUN)")
    else:
        print("ERPNEXT PORTFOLIO FETCH")
    print("=" * (title_w + 45))
    print(f"{'Project':<{title_w}}  {'Client':<20}  Status")
    print("-" * (title_w + 45))

    for r in results:
        title = r['title'][:40] + ('...' if len(r['title']) > 40 else '')
        client = r['client'][:20] if r['client'] else '-'
        print(f"{title:<{title_w}}  {client:<20}  {r['status']}")

    print("-" * (title_w + 45))

    created = sum(1 for r in results if 'Created' in r['status'] or 'Would' in r['status'])
    skipped = sum(1 for r in results if 'skipped' in r['status'])
    errors = sum(1 for r in results if 'Error' in r['status'])

    print(f"Total: {len(results)} | New: {created} | Existing: {skipped} | Errors: {errors}")
    print("=" * (title_w + 45))


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Fetch portfolio from ERPNext')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Show what would be fetched without creating files')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Overwrite existing files (use with caution)')
    parser.add_argument('--list', '-l', action='store_true',
                        help='Only list available items, do not fetch')
    parser.add_argument('--doctype', '-d', type=str, default=PORTFOLIO_DOCTYPE,
                        help=f'ERPNext doctype to fetch (default: {PORTFOLIO_DOCTYPE})')
    args = parser.parse_args()

    global PORTFOLIO_DOCTYPE
    PORTFOLIO_DOCTYPE = args.doctype

    if not API_KEY or not API_SECRET:
        print("Warning: ERPNEXT_API_KEY and ERPNEXT_API_SECRET not set.")
        print("Attempting unauthenticated access (may fail for private content).")
        print()

    script_dir = Path(__file__).parent
    content_dir = script_dir.parent / 'content' / 'portfolio'

    if not content_dir.exists():
        print(f"Error: Content directory not found: {content_dir}")
        sys.exit(1)

    print(f"Fetching portfolio list from {ERPNEXT_URL}...")
    print(f"Using doctype: {PORTFOLIO_DOCTYPE}")
    items = fetch_portfolio_list()

    if not items:
        print("No portfolio items found or error occurred.")
        sys.exit(1)

    print(f"Found {len(items)} portfolio items")

    if args.list:
        results = []
        for item in items:
            results.append({
                'title': item.get('project_name') or item.get('name', 'Untitled'),
                'client': item.get('customer', ''),
                'status': 'Available'
            })
        print_table(results, dry_run=True)
        return

    results = []
    for item_summary in items:
        item_name = item_summary.get('name')
        if not item_name:
            continue

        item = fetch_portfolio_detail(item_name)
        if not item:
            results.append({
                'title': item_summary.get('project_name', 'Unknown'),
                'client': '-',
                'status': 'Error: fetch failed'
            })
            continue

        filename, status = create_hugo_file(item, content_dir, dry_run=args.dry_run)

        results.append({
            'title': item.get('project_name') or item.get('name', 'Untitled'),
            'client': item.get('customer', ''),
            'status': status
        })

    print_table(results, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
