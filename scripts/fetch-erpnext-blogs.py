#!/usr/bin/env python3
"""
Fetch blog articles from ERPNext and create Hugo content files.

Only fetches new articles that don't exist locally to preserve local edits.

Environment variables:
    ERPNEXT_URL: ERPNext instance URL (default: https://erp.kartoza.com)
    ERPNEXT_API_KEY: API key for authentication
    ERPNEXT_API_SECRET: API secret for authentication

Usage:
    ./fetch-erpnext-blogs.py [--dry-run] [--force] [--list]
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

import requests
import yaml
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from tabulate import tabulate
import json


# Configuration
ERPNEXT_URL = os.environ.get('ERPNEXT_URL', 'https://erp.kartoza.com')
API_KEY = os.environ.get('ERPNEXT_API_KEY', '')
API_SECRET = os.environ.get('ERPNEXT_API_SECRET', '')


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


def normalize_for_comparison(content: str) -> str:
    """
    Normalize content for fidelity comparison.
    Focuses on TEXT content, ignores formatting/layout.
    """
    if not content:
        return ''

    # Remove Hugo shortcodes like {{< block >}} or {{< /block >}}
    content = re.sub(r'\{\{[<>%].*?[>%]\}\}', '', content)

    # Strip HTML tags but keep text content
    soup = BeautifulSoup(content, 'html.parser')
    text = soup.get_text(separator=' ')

    # Collapse whitespace (multiple spaces/newlines -> single space)
    text = re.sub(r'\s+', ' ', text)

    # Strip leading/trailing whitespace and lowercase
    return text.strip().lower()


def check_fidelity(local_content: str, erpnext_content: str) -> bool:
    """
    Check if local and ERPNext content match (fidelity check).

    Returns True if text content matches (ignoring formatting).
    """
    local_norm = normalize_for_comparison(local_content)
    erpnext_norm = normalize_for_comparison(erpnext_content)
    return local_norm == erpnext_norm


def read_local_blog(filepath: Path) -> tuple[dict, str] | None:
    """
    Read a local Hugo blog file and extract front matter and content.

    Returns:
        Tuple of (front_matter_dict, content_str) or None if file doesn't exist
    """
    if not filepath.exists():
        return None

    try:
        text = filepath.read_text()
    except (IOError, OSError):
        return None

    # Check for front matter delimiter
    if not text.startswith('---'):
        return {}, text

    # Find end of front matter
    end_match = re.search(r'\n---\n', text[3:])
    if not end_match:
        return {}, text

    end_pos = end_match.start() + 3
    front_matter_raw = text[4:end_pos]
    content = text[end_pos + 5:]

    try:
        front_matter = yaml.safe_load(front_matter_raw) or {}
    except yaml.YAMLError:
        front_matter = {}

    return front_matter, content


def find_local_file(content_dir: Path, erpnext_id: str, title: str) -> Path | None:
    """
    Find a local Hugo file matching the ERPNext article.

    Matches by:
    1. erpnext_id in front matter (primary)
    2. Slugified title matching filename (fallback)

    Returns:
        Path to matching file or None
    """
    # First, try to find by erpnext_id in front matter
    for filepath in content_dir.glob('*.md'):
        if filepath.name == '_index.md':
            continue
        result = read_local_blog(filepath)
        if result:
            front_matter, _ = result
            if front_matter.get('erpnext_id') == erpnext_id:
                return filepath

    # Fallback: match by slugified title
    expected_filename = f"{slugify(title)}.md"
    expected_path = content_dir / expected_filename
    if expected_path.exists():
        return expected_path

    return None


def fetch_blog_list() -> list[dict]:
    """Fetch list of published blog posts from ERPNext."""
    url = f"{ERPNEXT_URL}/api/resource/Blog Post"
    params = {
        'filters': '[["published", "=", 1]]',
        'fields': '["name", "title", "published_on", "blogger", "blog_category", "modified"]',
        'limit_page_length': 0  # Get all
    }

    try:
        response = requests.get(url, params=params, headers=get_auth_headers(), timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('data', [])
    except requests.RequestException as e:
        print(f"Error fetching blog list: {e}")
        return []


def fetch_blog_detail(name: str) -> dict | None:
    """Fetch full blog post details from ERPNext."""
    url = f"{ERPNEXT_URL}/api/resource/Blog Post/{name}"

    try:
        response = requests.get(url, headers=get_auth_headers(), timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('data', {})
    except requests.RequestException as e:
        print(f"Error fetching blog '{name}': {e}")
        return None


def blog_to_hugo_frontmatter(blog: dict) -> dict:
    """Convert ERPNext blog to Hugo front matter."""
    # Parse date
    pub_date = blog.get('published_on') or blog.get('creation')
    if pub_date:
        try:
            dt = date_parser.parse(pub_date)
            date_str = dt.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            date_str = datetime.now().strftime('%Y-%m-%d')
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')

    # Build front matter
    front_matter = {
        'title': blog.get('title', 'Untitled'),
        'description': blog.get('blog_intro', '')[:200] if blog.get('blog_intro') else '',
        'date': date_str,
        'author': blog.get('blogger', 'Kartoza'),
        'thumbnail': '/img/blog/placeholder.png',
        'tags': [],
        'erpnext_id': blog.get('name', ''),
        'erpnext_modified': blog.get('modified', ''),
    }

    # Add category as tag
    if blog.get('blog_category'):
        front_matter['tags'].append(blog['blog_category'])

    return front_matter


def blog_to_hugo_content(blog: dict) -> str:
    """Convert ERPNext blog content to Hugo markdown."""
    content = blog.get('content') or blog.get('content_html') or ''

    # Basic HTML to markdown conversion for simple cases
    # For complex HTML, we preserve it as Hugo can handle it
    content = re.sub(r'<br\s*/?>', '\n', content)
    content = re.sub(r'<p>', '\n\n', content)
    content = re.sub(r'</p>', '', content)
    content = re.sub(r'<strong>([^<]+)</strong>', r'**\1**', content)
    content = re.sub(r'<b>([^<]+)</b>', r'**\1**', content)
    content = re.sub(r'<em>([^<]+)</em>', r'*\1*', content)
    content = re.sub(r'<i>([^<]+)</i>', r'*\1*', content)
    content = re.sub(r'<h1>([^<]+)</h1>', r'\n# \1\n', content)
    content = re.sub(r'<h2>([^<]+)</h2>', r'\n## \1\n', content)
    content = re.sub(r'<h3>([^<]+)</h3>', r'\n### \1\n', content)
    content = re.sub(r'<a href="([^"]+)">([^<]+)</a>', r'[\2](\1)', content)

    return content.strip()


def create_hugo_file(blog: dict, content_dir: Path, dry_run: bool = False) -> tuple[str, str]:
    """
    Create Hugo markdown file from ERPNext blog.

    Returns:
        Tuple of (filename, status)
    """
    title = blog.get('title', 'Untitled')
    slug = slugify(title)
    filename = f"{slug}.md"
    filepath = content_dir / filename

    # Check if file already exists
    if filepath.exists():
        return filename, 'Exists (skipped)'

    front_matter = blog_to_hugo_frontmatter(blog)
    content = blog_to_hugo_content(blog)

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
        print("\nNo blogs found.")
        return

    title_w = max(len(r['title'][:40]) for r in results)
    title_w = max(title_w, 10)

    print("\n" + "=" * (title_w + 50))
    if dry_run:
        print("ERPNEXT BLOG FETCH (DRY RUN)")
    else:
        print("ERPNEXT BLOG FETCH")
    print("=" * (title_w + 50))
    print(f"{'Title':<{title_w}}  {'Date':<12}  {'Author':<15}  Status")
    print("-" * (title_w + 50))

    for r in results:
        title = r['title'][:40] + ('...' if len(r['title']) > 40 else '')
        print(f"{title:<{title_w}}  {r['date']:<12}  {r['author'][:15]:<15}  {r['status']}")

    print("-" * (title_w + 50))

    created = sum(1 for r in results if 'Created' in r['status'] or 'Would' in r['status'])
    skipped = sum(1 for r in results if 'skipped' in r['status'])
    errors = sum(1 for r in results if 'Error' in r['status'])

    print(f"Total: {len(results)} | New: {created} | Existing: {skipped} | Errors: {errors}")
    print("=" * (title_w + 50))


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Fetch blogs from ERPNext')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Show what would be fetched without creating files')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Overwrite existing files (use with caution)')
    parser.add_argument('--list', '-l', action='store_true',
                        help='Only list available blogs, do not fetch')
    args = parser.parse_args()

    if not API_KEY or not API_SECRET:
        print("Warning: ERPNEXT_API_KEY and ERPNEXT_API_SECRET not set.")
        print("Attempting unauthenticated access (may fail for private content).")
        print()

    script_dir = Path(__file__).parent
    content_dir = script_dir.parent / 'content' / 'blog'

    if not content_dir.exists():
        print(f"Error: Content directory not found: {content_dir}")
        sys.exit(1)

    print(f"Fetching blog list from {ERPNEXT_URL}...")
    blogs = fetch_blog_list()

    if not blogs:
        print("No blogs found or error occurred.")
        sys.exit(1)

    print(f"Found {len(blogs)} published blogs")

    if args.list:
        # Just list the blogs
        results = []
        for blog in blogs:
            results.append({
                'title': blog.get('title', 'Untitled'),
                'date': str(blog.get('published_on', ''))[:10],
                'author': blog.get('blogger', 'Unknown'),
                'status': 'Available'
            })
        print_table(results, dry_run=True)
        return

    results = []
    for blog_summary in blogs:
        blog_name = blog_summary.get('name')
        if not blog_name:
            continue

        # Fetch full details
        blog = fetch_blog_detail(blog_name)
        if not blog:
            results.append({
                'title': blog_summary.get('title', 'Unknown'),
                'date': '-',
                'author': '-',
                'status': 'Error: fetch failed'
            })
            continue

        filename, status = create_hugo_file(blog, content_dir, dry_run=args.dry_run)

        results.append({
            'title': blog.get('title', 'Untitled'),
            'date': str(blog.get('published_on', ''))[:10],
            'author': blog.get('blogger', 'Unknown'),
            'status': status
        })

    print_table(results, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
