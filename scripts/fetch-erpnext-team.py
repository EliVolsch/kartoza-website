#!/usr/bin/env python3
"""
Fetch team member information from ERPNext.
Adds new team members and marks departed ones as inactive.

Usage:
    python3 fetch-erpnext-team.py [--list] [--dry-run]

Options:
    --list      List team members from ERPNext without downloading
    --dry-run   Preview changes without writing files
"""

import os
import sys
import re
import argparse
import requests
from pathlib import Path
from datetime import datetime

# ERPNext configuration
ERPNEXT_URL = os.environ.get("ERPNEXT_URL", "https://erp.kartoza.com")
TEAM_CONTENT_DIR = Path(__file__).parent.parent / "content" / "the_team"


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text


def fetch_team_from_erpnext() -> list:
    """Fetch team member list from ERPNext."""
    # This is a placeholder - actual implementation would depend on ERPNext API
    # For now, we'll try to fetch from a public endpoint if available
    try:
        # Try to fetch from ERPNext website/team API
        response = requests.get(
            f"{ERPNEXT_URL}/api/resource/Website Team Member",
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
    except Exception as e:
        print(f"Warning: Could not fetch from ERPNext API: {e}")
        print("Note: ERPNext team API may require authentication")

    return []


def get_existing_team_members() -> dict:
    """Get existing team member files and their status."""
    team_members = {}

    if not TEAM_CONTENT_DIR.exists():
        return team_members

    for md_file in TEAM_CONTENT_DIR.glob("*.md"):
        if md_file.name == "_index.md":
            continue

        content = md_file.read_text()

        # Parse front matter
        name = None
        is_active = True

        # Extract name from title
        title_match = re.search(r'^title:\s*["\']?([^"\'\n]+)["\']?', content, re.MULTILINE)
        if title_match:
            name = title_match.group(1).strip()

        # Check if marked as inactive/departed
        if "departed: true" in content.lower() or "active: false" in content.lower():
            is_active = False

        if name:
            team_members[slugify(name)] = {
                "name": name,
                "file": md_file,
                "is_active": is_active,
                "slug": md_file.stem
            }

    return team_members


def create_team_member_page(member: dict, dry_run: bool = False) -> Path:
    """Create a new team member page."""
    slug = slugify(member.get("full_name", member.get("name", "unknown")))
    filepath = TEAM_CONTENT_DIR / f"{slug}.md"

    # Default template
    content = f'''---
title: "{member.get('full_name', member.get('name', 'Team Member'))}"
description: "{member.get('designation', 'Team Member')} at Kartoza"
thumbnail: "/img/team/{slug}.jpg"
position: "{member.get('designation', 'Team Member')}"
email: "{member.get('email', '')}"
github: ""
linkedin: ""
twitter: ""
weight: 100
draft: false
---

{{{{< block
    title="{member.get('full_name', member.get('name', 'Team Member'))}"
    subtitle="{member.get('designation', 'Team Member')}"
    class="is-primary"
    sub-block-side="bottom"
>}}}}
{member.get('bio', 'Bio coming soon.')}
{{{{< /block >}}}}

## About

{member.get('bio', 'Bio coming soon.')}
'''

    if dry_run:
        print(f"Would create: {filepath}")
    else:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content)
        print(f"Created: {filepath}")

    return filepath


def mark_member_departed(member_info: dict, dry_run: bool = False):
    """Mark a team member as departed."""
    filepath = member_info["file"]
    content = filepath.read_text()

    # Add departed flag to front matter
    if "departed:" not in content:
        # Insert departed: true after the opening ---
        content = content.replace("---\n", "---\ndeparted: true\n", 1)

        if dry_run:
            print(f"Would mark as departed: {filepath}")
        else:
            filepath.write_text(content)
            print(f"Marked as departed: {filepath}")


def list_team_members():
    """List all team members from ERPNext and local."""
    print("=" * 60)
    print("Team Members")
    print("=" * 60)

    print("\nERPNext Team Members:")
    print("-" * 40)
    erpnext_team = fetch_team_from_erpnext()
    if erpnext_team:
        for member in erpnext_team:
            name = member.get("full_name", member.get("name", "Unknown"))
            role = member.get("designation", "")
            print(f"  - {name} ({role})")
    else:
        print("  No team members fetched from ERPNext")
        print("  (API may require authentication)")

    print("\nLocal Team Members:")
    print("-" * 40)
    local_team = get_existing_team_members()
    active = [m for m in local_team.values() if m["is_active"]]
    departed = [m for m in local_team.values() if not m["is_active"]]

    print(f"\n  Active ({len(active)}):")
    for member in sorted(active, key=lambda x: x["name"]):
        print(f"    - {member['name']}")

    if departed:
        print(f"\n  Departed ({len(departed)}):")
        for member in sorted(departed, key=lambda x: x["name"]):
            print(f"    - {member['name']}")


def sync_team_members(dry_run: bool = False):
    """Sync team members between ERPNext and local content."""
    print("=" * 60)
    print("Syncing Team Members")
    print("=" * 60)

    erpnext_team = fetch_team_from_erpnext()
    local_team = get_existing_team_members()

    if not erpnext_team:
        print("\nWarning: No team members fetched from ERPNext")
        print("This may be because:")
        print("  - ERPNext API requires authentication")
        print("  - The endpoint structure is different")
        print("\nNo changes will be made.")
        return

    # Convert ERPNext team to a lookup by slug
    erpnext_slugs = {}
    for member in erpnext_team:
        name = member.get("full_name", member.get("name", ""))
        if name:
            erpnext_slugs[slugify(name)] = member

    # Find new team members (in ERPNext but not local)
    new_members = []
    for slug, member in erpnext_slugs.items():
        if slug not in local_team:
            new_members.append(member)

    # Find departed team members (in local but not ERPNext)
    departed = []
    for slug, info in local_team.items():
        if info["is_active"] and slug not in erpnext_slugs:
            departed.append(info)

    print(f"\nNew team members to add: {len(new_members)}")
    for member in new_members:
        name = member.get("full_name", member.get("name", "Unknown"))
        print(f"  + {name}")
        create_team_member_page(member, dry_run)

    print(f"\nDeparted team members to mark: {len(departed)}")
    for info in departed:
        print(f"  - {info['name']}")
        mark_member_departed(info, dry_run)

    if not new_members and not departed:
        print("\nNo changes needed - team is in sync")


def main():
    parser = argparse.ArgumentParser(description="Fetch team members from ERPNext")
    parser.add_argument("--list", action="store_true", help="List team members without syncing")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without making them")
    args = parser.parse_args()

    if args.list:
        list_team_members()
    else:
        sync_team_members(args.dry_run)


if __name__ == "__main__":
    main()
