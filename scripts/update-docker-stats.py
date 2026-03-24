#!/usr/bin/env python3
"""
Fetch Docker Hub stats and update Hugo content files.

Updates pulls and stars for all Docker images in content/docker/.
"""

import re
import sys
from pathlib import Path

import requests
import yaml


def format_number(num: int) -> str:
    """Format large numbers with K, M, B suffixes."""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B+"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.0f}M+"
    elif num >= 1_000:
        return f"{num / 1_000:.0f}K+"
    else:
        return str(num)


def get_docker_stats(dockerhub_url: str) -> dict | None:
    """Fetch stats from Docker Hub API."""
    match = re.search(r'hub\.docker\.com/r/([^/]+)/([^/]+)', dockerhub_url)
    if not match:
        return None

    namespace, repo = match.groups()
    api_url = f"https://hub.docker.com/v2/repositories/{namespace}/{repo}/"

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            'pulls': data.get('pull_count', 0),
            'stars': data.get('star_count', 0),
        }
    except requests.RequestException:
        return None


def parse_front_matter(content: str) -> dict:
    """Parse YAML front matter from markdown content."""
    if not content.startswith('---'):
        return {}
    end_match = re.search(r'\n---\n', content[3:])
    if not end_match:
        return {}
    front_matter_raw = content[4:end_match.start() + 3]
    try:
        return yaml.safe_load(front_matter_raw) or {}
    except yaml.YAMLError:
        return {}


def update_front_matter_value(content: str, key: str, new_value: str) -> str:
    """Update a single value in the front matter while preserving formatting."""
    pattern = rf'^({key}:\s*)(.+)$'

    def replacer(match):
        prefix = match.group(1)
        old_value = match.group(2).strip()
        if old_value.startswith('"') and old_value.endswith('"'):
            return f'{prefix}"{new_value}"'
        elif old_value.startswith("'") and old_value.endswith("'"):
            return f"{prefix}'{new_value}'"
        else:
            if isinstance(new_value, str) and ('+' in new_value or new_value[0].isdigit()):
                return f'{prefix}"{new_value}"'
            return f'{prefix}{new_value}'

    return re.sub(pattern, replacer, content, flags=re.MULTILINE)


def print_table(results: list[dict], dry_run: bool = False):
    """Print a formatted table of results."""
    if not results:
        print("\nNo files processed.")
        return

    # Column widths
    name_w = max(len(r['name']) for r in results)
    name_w = max(name_w, 10)

    # Header
    print("\n" + "=" * (name_w + 50))
    if dry_run:
        print("DOCKER HUB STATS UPDATE (DRY RUN)")
    else:
        print("DOCKER HUB STATS UPDATE")
    print("=" * (name_w + 50))
    print(f"{'Image':<{name_w}}  {'Pulls':<20}  {'Stars':<12}  Status")
    print(f"{'':<{name_w}}  {'Old → New':<20}  {'Old → New':<12}")
    print("-" * (name_w + 50))

    for r in results:
        pulls_change = f"{r['old_pulls']} → {r['new_pulls']}"
        stars_change = f"{r['old_stars']} → {r['new_stars']}"
        print(f"{r['name']:<{name_w}}  {pulls_change:<20}  {stars_change:<12}  {r['status']}")

    print("-" * (name_w + 50))

    updated = sum(1 for r in results if r['status'] == 'Updated')
    unchanged = sum(1 for r in results if r['status'] == 'No change')
    errors = sum(1 for r in results if r['status'] == 'Error')

    print(f"Total: {len(results)} | Updated: {updated} | Unchanged: {unchanged} | Errors: {errors}")
    print("=" * (name_w + 50))


def process_docker_file(filepath: Path, dry_run: bool = False) -> dict:
    """Process a single Docker content file and return result dict."""
    result = {
        'name': filepath.stem,
        'old_pulls': '-',
        'new_pulls': '-',
        'old_stars': '-',
        'new_stars': '-',
        'status': 'Error'
    }

    content = filepath.read_text()
    front_matter = parse_front_matter(content)

    if not front_matter:
        result['status'] = 'No frontmatter'
        return result

    dockerhub_url = front_matter.get('dockerhub')
    if not dockerhub_url:
        result['status'] = 'No URL'
        return result

    result['old_pulls'] = str(front_matter.get('pulls', '-'))
    result['old_stars'] = str(front_matter.get('stars', '-'))

    stats = get_docker_stats(dockerhub_url)
    if not stats:
        result['status'] = 'Fetch failed'
        return result

    pulls_formatted = format_number(stats['pulls'])
    stars = str(stats['stars'])

    result['new_pulls'] = pulls_formatted
    result['new_stars'] = stars

    # Check if anything changed
    if result['old_pulls'] == pulls_formatted and result['old_stars'] == stars:
        result['status'] = 'No change'
        return result

    # Update the content
    new_content = content
    new_content = update_front_matter_value(new_content, 'pulls', pulls_formatted)
    new_content = update_front_matter_value(new_content, 'stars', stars)

    if not dry_run:
        filepath.write_text(new_content)

    result['status'] = 'Updated' if not dry_run else 'Would update'
    return result


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Update Docker Hub stats in Hugo content')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Show what would be updated without making changes')
    parser.add_argument('--file', '-f', type=str,
                        help='Update a specific file instead of all files')
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    content_dir = script_dir.parent / 'content' / 'docker'

    if not content_dir.exists():
        print(f"Error: Content directory not found: {content_dir}")
        sys.exit(1)

    if args.file:
        files = [Path(args.file)]
    else:
        files = sorted(content_dir.glob('*.md'))
        files = [f for f in files if f.name != '_index.md']

    print(f"Scanning {len(files)} Docker content files...")

    results = []
    for filepath in files:
        result = process_docker_file(filepath, dry_run=args.dry_run)
        results.append(result)

    print_table(results, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
