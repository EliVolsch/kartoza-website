#!/usr/bin/env python3
"""
Compare local Hugo content with ERPNext source content.

Shows differences between local files and ERPNext, ignoring layout/formatting.
Useful for identifying content drift after local edits.

Environment variables:
    ERPNEXT_URL: ERPNext instance URL (default: https://erp.kartoza.com)
    ERPNEXT_API_KEY: API key for authentication
    ERPNEXT_API_SECRET: API secret for authentication

Usage:
    ./compare-erpnext-content.py [--blogs] [--portfolio] [--verbose]
"""

import difflib
import os
import re
import sys
from pathlib import Path

import requests
import yaml
from bs4 import BeautifulSoup

try:
    import html2text
    HAS_HTML2TEXT = True
except ImportError:
    HAS_HTML2TEXT = False


# Configuration
ERPNEXT_URL = os.environ.get('ERPNEXT_URL', 'https://erp.kartoza.com')
API_KEY = os.environ.get('ERPNEXT_API_KEY', '')
API_SECRET = os.environ.get('ERPNEXT_API_SECRET', '')


def get_auth_headers() -> dict:
    """Get authentication headers for ERPNext API."""
    if API_KEY and API_SECRET:
        return {'Authorization': f'token {API_KEY}:{API_SECRET}'}
    return {}


def normalize_text(text: str) -> str:
    """Normalize text for comparison by removing formatting."""
    if not text:
        return ''

    # Remove HTML tags
    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text(separator=' ')

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip().lower()

    # Remove common markdown/shortcode syntax
    text = re.sub(r'\{\{[<>%].*?[>%]\}\}', '', text)  # Hugo shortcodes
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Links
    text = re.sub(r'[*_#`]+', '', text)  # Markdown formatting
    text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)  # Images

    return text.strip()


def extract_content_from_hugo(filepath: Path) -> tuple[dict, str]:
    """Extract front matter and content from Hugo markdown file."""
    content = filepath.read_text()

    if not content.startswith('---'):
        return {}, content

    # Find end of front matter
    end_match = re.search(r'\n---\n', content[3:])
    if not end_match:
        return {}, content

    end_pos = end_match.start() + 3
    front_matter_raw = content[4:end_pos]
    body = content[end_pos + 5:]

    try:
        front_matter = yaml.safe_load(front_matter_raw) or {}
    except yaml.YAMLError:
        front_matter = {}

    return front_matter, body


def fetch_erpnext_blog(name: str) -> dict | None:
    """Fetch blog from ERPNext by name/ID."""
    url = f"{ERPNEXT_URL}/api/resource/Blog Post/{name}"
    try:
        response = requests.get(url, headers=get_auth_headers(), timeout=30)
        response.raise_for_status()
        return response.json().get('data', {})
    except requests.RequestException:
        return None


def fetch_erpnext_project(name: str) -> dict | None:
    """Fetch project from ERPNext by name/ID."""
    url = f"{ERPNEXT_URL}/api/resource/Project/{name}"
    try:
        response = requests.get(url, headers=get_auth_headers(), timeout=30)
        response.raise_for_status()
        return response.json().get('data', {})
    except requests.RequestException:
        return None


def compare_content(local_content: str, remote_content: str) -> dict:
    """
    Compare local and remote content.

    Returns:
        Dict with 'similarity' (0-1), 'diff_lines', 'status'
    """
    local_norm = normalize_text(local_content)
    remote_norm = normalize_text(remote_content)

    if not local_norm and not remote_norm:
        return {'similarity': 1.0, 'diff_lines': 0, 'status': 'Both empty'}

    if not remote_norm:
        return {'similarity': 0.0, 'diff_lines': 0, 'status': 'No remote content'}

    # Calculate similarity ratio
    matcher = difflib.SequenceMatcher(None, local_norm, remote_norm)
    similarity = matcher.ratio()

    # Get diff for verbose output
    local_lines = local_norm.split('. ')
    remote_lines = remote_norm.split('. ')
    diff = list(difflib.unified_diff(remote_lines, local_lines, lineterm=''))
    diff_lines = len([l for l in diff if l.startswith('+') or l.startswith('-')])

    if similarity >= 0.95:
        status = 'Identical'
    elif similarity >= 0.8:
        status = 'Minor changes'
    elif similarity >= 0.5:
        status = 'Modified'
    else:
        status = 'Significantly different'

    return {
        'similarity': similarity,
        'diff_lines': diff_lines,
        'status': status,
        'diff': diff
    }


def compare_blogs(content_dir: Path, verbose: bool = False) -> list[dict]:
    """Compare all local blog posts with ERPNext."""
    results = []

    for filepath in sorted(content_dir.glob('*.md')):
        if filepath.name == '_index.md':
            continue

        front_matter, local_content = extract_content_from_hugo(filepath)
        erpnext_id = front_matter.get('erpnext_id')

        result = {
            'file': filepath.name,
            'title': front_matter.get('title', filepath.stem),
            'erpnext_id': erpnext_id or '-',
            'similarity': '-',
            'status': 'No ERPNext ID'
        }

        if erpnext_id:
            remote = fetch_erpnext_blog(erpnext_id)
            if remote:
                remote_content = remote.get('content') or remote.get('content_html', '')
                comparison = compare_content(local_content, remote_content)
                result['similarity'] = f"{comparison['similarity']:.0%}"
                result['status'] = comparison['status']
                if verbose and comparison.get('diff'):
                    result['diff'] = comparison['diff']
            else:
                result['status'] = 'Not found in ERPNext'

        results.append(result)

    return results


def compare_portfolio(content_dir: Path, verbose: bool = False) -> list[dict]:
    """Compare all local portfolio items with ERPNext."""
    results = []

    for filepath in sorted(content_dir.glob('*.md')):
        if filepath.name == '_index.md':
            continue

        front_matter, local_content = extract_content_from_hugo(filepath)
        erpnext_id = front_matter.get('erpnext_id')

        result = {
            'file': filepath.name,
            'title': front_matter.get('title', filepath.stem),
            'erpnext_id': erpnext_id or '-',
            'similarity': '-',
            'status': 'No ERPNext ID'
        }

        if erpnext_id:
            remote = fetch_erpnext_project(erpnext_id)
            if remote:
                remote_content = remote.get('notes', '')
                comparison = compare_content(local_content, remote_content)
                result['similarity'] = f"{comparison['similarity']:.0%}"
                result['status'] = comparison['status']
                if verbose and comparison.get('diff'):
                    result['diff'] = comparison['diff']
            else:
                result['status'] = 'Not found in ERPNext'

        results.append(result)

    return results


def print_table(results: list[dict], title: str, verbose: bool = False):
    """Print a formatted table of comparison results."""
    if not results:
        print(f"\nNo {title.lower()} files found.")
        return

    file_w = max(len(r['file'][:30]) for r in results)
    file_w = max(file_w, 10)
    title_w = max(len(r['title'][:25]) for r in results)
    title_w = max(title_w, 10)

    print("\n" + "=" * (file_w + title_w + 50))
    print(f"{title} COMPARISON")
    print("=" * (file_w + title_w + 50))
    print(f"{'File':<{file_w}}  {'Title':<{title_w}}  {'Similarity':<12}  Status")
    print("-" * (file_w + title_w + 50))

    for r in results:
        file_name = r['file'][:30] + ('...' if len(r['file']) > 30 else '')
        title_text = r['title'][:25] + ('...' if len(r['title']) > 25 else '')
        print(f"{file_name:<{file_w}}  {title_text:<{title_w}}  {r['similarity']:<12}  {r['status']}")

        if verbose and r.get('diff'):
            print("    Diff preview:")
            for line in r['diff'][:10]:
                print(f"      {line}")
            if len(r['diff']) > 10:
                print(f"      ... and {len(r['diff']) - 10} more lines")

    print("-" * (file_w + title_w + 50))

    identical = sum(1 for r in results if r['status'] == 'Identical')
    modified = sum(1 for r in results if 'change' in r['status'].lower() or 'Modified' in r['status'])
    no_link = sum(1 for r in results if 'No ERPNext' in r['status'])

    print(f"Total: {len(results)} | Identical: {identical} | Modified: {modified} | No ERPNext link: {no_link}")
    print("=" * (file_w + title_w + 50))


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Compare local content with ERPNext')
    parser.add_argument('--blogs', '-b', action='store_true',
                        help='Compare blog posts')
    parser.add_argument('--portfolio', '-p', action='store_true',
                        help='Compare portfolio items')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed diff for modified files')
    parser.add_argument('--all', '-a', action='store_true',
                        help='Compare all content types')
    args = parser.parse_args()

    # Default to all if nothing specified
    if not args.blogs and not args.portfolio and not args.all:
        args.all = True

    if not API_KEY or not API_SECRET:
        print("Warning: ERPNEXT_API_KEY and ERPNEXT_API_SECRET not set.")
        print("Attempting unauthenticated access (may fail for private content).")
        print()

    script_dir = Path(__file__).parent
    base_dir = script_dir.parent / 'content'

    if args.blogs or args.all:
        blog_dir = base_dir / 'blog'
        if blog_dir.exists():
            print(f"Comparing blogs from {blog_dir}...")
            results = compare_blogs(blog_dir, verbose=args.verbose)
            print_table(results, "BLOG", verbose=args.verbose)

    if args.portfolio or args.all:
        portfolio_dir = base_dir / 'portfolio'
        if portfolio_dir.exists():
            print(f"\nComparing portfolio from {portfolio_dir}...")
            results = compare_portfolio(portfolio_dir, verbose=args.verbose)
            print_table(results, "PORTFOLIO", verbose=args.verbose)


if __name__ == '__main__':
    main()
