#!/usr/bin/env python3
"""
Fetch QGIS plugin stats and update Hugo content files.

Updates downloads, version, rating, and votes for all plugins in content/plugins/.
"""

import re
import sys
from pathlib import Path

import requests
import yaml


def format_downloads(num: int) -> str:
    """Format download count with comma separators and + suffix."""
    return f"{num:,}+"


def get_plugin_stats(plugin_url: str) -> dict | None:
    """Fetch stats from QGIS Plugin Repository."""
    match = re.search(r'plugins\.qgis\.org/plugins/([^/]+)', plugin_url)
    if not match:
        return None

    plugin_name = match.group(1)
    stats = {}

    try:
        # Try XML plugin metadata first (most reliable)
        xml_url = f"https://plugins.qgis.org/plugins/plugins.xml?qgis=3.28"
        xml_response = requests.get(xml_url, timeout=30)
        xml_content = xml_response.text

        # Find the plugin in XML - look for the plugin by name attribute
        plugin_pattern = rf'<pyqgis_plugin\s+name="[^"]*"[^>]*version="([^"]*)"[^>]*>.*?</pyqgis_plugin>'

        # More targeted search for this specific plugin
        # The XML has plugins like: <pyqgis_plugin name="Plugin Name" version="1.0">
        plugin_section = re.search(
            rf'<pyqgis_plugin[^>]*>.*?<file_name>{plugin_name}[^<]*</file_name>.*?</pyqgis_plugin>',
            xml_content, re.DOTALL | re.IGNORECASE
        )

        if not plugin_section:
            # Try alternative: search by download_url containing plugin name
            plugin_section = re.search(
                rf'<pyqgis_plugin[^>]*>.*?<download_url>[^<]*{plugin_name}[^<]*</download_url>.*?</pyqgis_plugin>',
                xml_content, re.DOTALL | re.IGNORECASE
            )

        if plugin_section:
            section = plugin_section.group(0)

            # Extract downloads
            dl_match = re.search(r'<downloads>(\d+)</downloads>', section)
            if dl_match:
                stats['downloads'] = int(dl_match.group(1))

            # Extract version
            ver_match = re.search(r'<version>([^<]+)</version>', section)
            if ver_match:
                stats['version'] = ver_match.group(1).strip()

            # Extract rating
            rat_match = re.search(r'<average_vote>([^<]+)</average_vote>', section)
            if rat_match:
                try:
                    stats['rating'] = float(rat_match.group(1))
                except ValueError:
                    pass

            # Extract votes
            vote_match = re.search(r'<rating_votes>(\d+)</rating_votes>', section)
            if vote_match:
                stats['votes'] = int(vote_match.group(1))

        # Fallback: scrape the web page
        if not stats:
            page_url = f"https://plugins.qgis.org/plugins/{plugin_name}/"
            response = requests.get(page_url, timeout=10)
            html = response.text

            # Extract downloads
            downloads_match = re.search(r'>(\d[\d,]*)</td>\s*</tr>\s*<tr[^>]*>\s*<th[^>]*>Downloads', html, re.IGNORECASE)
            if not downloads_match:
                downloads_match = re.search(r'Downloads.*?(\d[\d,]+)', html, re.IGNORECASE | re.DOTALL)
            if downloads_match:
                stats['downloads'] = int(downloads_match.group(1).replace(',', ''))

        return stats if stats else None

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
            if isinstance(new_value, str) and ('+' in new_value or ',' in new_value):
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
    name_w = max(name_w, 12)

    # Header
    print("\n" + "=" * (name_w + 70))
    if dry_run:
        print("QGIS PLUGIN STATS UPDATE (DRY RUN)")
    else:
        print("QGIS PLUGIN STATS UPDATE")
    print("=" * (name_w + 70))
    print(f"{'Plugin':<{name_w}}  {'Downloads':<18}  {'Version':<14}  {'Rating':<12}  {'Votes':<10}  Status")
    print(f"{'':<{name_w}}  {'Old → New':<18}  {'Old → New':<14}  {'Old → New':<12}  {'Old → New':<10}")
    print("-" * (name_w + 70))

    for r in results:
        dl_change = f"{r['old_downloads']} → {r['new_downloads']}" if r['new_downloads'] != '-' else r['old_downloads']
        ver_change = f"{r['old_version']} → {r['new_version']}" if r['new_version'] != '-' else r['old_version']
        rat_change = f"{r['old_rating']} → {r['new_rating']}" if r['new_rating'] != '-' else r['old_rating']
        vote_change = f"{r['old_votes']} → {r['new_votes']}" if r['new_votes'] != '-' else r['old_votes']

        # Truncate long strings
        dl_change = dl_change[:18] if len(dl_change) > 18 else dl_change
        ver_change = ver_change[:14] if len(ver_change) > 14 else ver_change

        print(f"{r['name']:<{name_w}}  {dl_change:<18}  {ver_change:<14}  {rat_change:<12}  {vote_change:<10}  {r['status']}")

    print("-" * (name_w + 70))

    updated = sum(1 for r in results if r['status'] == 'Updated')
    unchanged = sum(1 for r in results if r['status'] == 'No change')
    errors = sum(1 for r in results if 'Error' in r['status'] or 'fail' in r['status'].lower())

    print(f"Total: {len(results)} | Updated: {updated} | Unchanged: {unchanged} | Errors: {errors}")
    print("=" * (name_w + 70))


def process_plugin_file(filepath: Path, dry_run: bool = False) -> dict:
    """Process a single plugin content file and return result dict."""
    result = {
        'name': filepath.stem,
        'old_downloads': '-',
        'new_downloads': '-',
        'old_version': '-',
        'new_version': '-',
        'old_rating': '-',
        'new_rating': '-',
        'old_votes': '-',
        'new_votes': '-',
        'status': 'Error'
    }

    content = filepath.read_text()
    front_matter = parse_front_matter(content)

    if not front_matter:
        result['status'] = 'No frontmatter'
        return result

    plugin_url = front_matter.get('plugin_url')
    if not plugin_url:
        result['status'] = 'No URL'
        return result

    result['old_downloads'] = str(front_matter.get('downloads', '-'))
    result['old_version'] = str(front_matter.get('version', '-'))
    result['old_rating'] = str(front_matter.get('rating', '-'))
    result['old_votes'] = str(front_matter.get('votes', '-'))

    stats = get_plugin_stats(plugin_url)
    if not stats:
        result['status'] = 'Fetch failed'
        return result

    new_content = content
    changed = False

    if 'downloads' in stats:
        downloads_formatted = format_downloads(stats['downloads'])
        result['new_downloads'] = downloads_formatted
        if result['old_downloads'] != downloads_formatted:
            new_content = update_front_matter_value(new_content, 'downloads', downloads_formatted)
            changed = True

    if 'version' in stats:
        result['new_version'] = stats['version']
        if result['old_version'] != stats['version']:
            new_content = update_front_matter_value(new_content, 'version', stats['version'])
            changed = True

    if 'rating' in stats:
        rating_str = f"{stats['rating']:.2f}"
        result['new_rating'] = rating_str
        if result['old_rating'] != rating_str:
            new_content = update_front_matter_value(new_content, 'rating', rating_str)
            changed = True

    if 'votes' in stats:
        votes_str = str(stats['votes'])
        result['new_votes'] = votes_str
        if result['old_votes'] != votes_str:
            new_content = update_front_matter_value(new_content, 'votes', votes_str)
            changed = True

    if not changed:
        result['status'] = 'No change'
        return result

    if not dry_run:
        filepath.write_text(new_content)

    result['status'] = 'Updated' if not dry_run else 'Would update'
    return result


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Update QGIS plugin stats in Hugo content')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Show what would be updated without making changes')
    parser.add_argument('--file', '-f', type=str,
                        help='Update a specific file instead of all files')
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    content_dir = script_dir.parent / 'content' / 'plugins'

    if not content_dir.exists():
        print(f"Error: Content directory not found: {content_dir}")
        sys.exit(1)

    if args.file:
        files = [Path(args.file)]
    else:
        files = sorted(content_dir.glob('*.md'))
        files = [f for f in files if f.name != '_index.md']

    print(f"Scanning {len(files)} plugin content files...")

    results = []
    for filepath in files:
        result = process_plugin_file(filepath, dry_run=args.dry_run)
        results.append(result)

    print_table(results, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
