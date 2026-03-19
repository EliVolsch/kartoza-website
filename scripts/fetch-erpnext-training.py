#!/usr/bin/env python3
"""
Fetch training course information and scheduled events from ERPNext.

Usage:
    python3 fetch-erpnext-training.py [--list] [--dry-run]

Options:
    --list      List training courses from ERPNext without downloading
    --dry-run   Preview changes without writing files
"""

import os
import sys
import re
import json
import argparse
import requests
from pathlib import Path
from datetime import datetime

# ERPNext configuration
ERPNEXT_URL = os.environ.get("ERPNEXT_URL", "https://erp.kartoza.com")
TRAINING_CONTENT_DIR = Path(__file__).parent.parent / "content" / "training-courses"
CALENDAR_DATA_DIR = Path(__file__).parent.parent / "data" / "training"


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text


def fetch_courses_from_erpnext() -> list:
    """Fetch training course types from ERPNext."""
    try:
        response = requests.get(
            f"{ERPNEXT_URL}/api/resource/Training Course",
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
    except Exception as e:
        print(f"Warning: Could not fetch courses from ERPNext: {e}")

    return []


def fetch_scheduled_events_from_erpnext() -> list:
    """Fetch scheduled training events from ERPNext."""
    try:
        response = requests.get(
            f"{ERPNEXT_URL}/api/resource/Training Event",
            params={
                "filters": json.dumps([["start_date", ">=", datetime.now().strftime("%Y-%m-%d")]]),
                "order_by": "start_date asc"
            },
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
    except Exception as e:
        print(f"Warning: Could not fetch events from ERPNext: {e}")

    return []


def get_existing_courses() -> dict:
    """Get existing course files."""
    courses = {}

    if not TRAINING_CONTENT_DIR.exists():
        return courses

    for md_file in TRAINING_CONTENT_DIR.glob("*.md"):
        if md_file.name == "_index.md":
            continue

        courses[md_file.stem] = {
            "file": md_file,
            "slug": md_file.stem
        }

    return courses


def create_course_page(course: dict, dry_run: bool = False) -> Path:
    """Create a new training course page."""
    slug = slugify(course.get("name", course.get("title", "unknown")))
    filepath = TRAINING_CONTENT_DIR / f"{slug}.md"

    # Check if file already exists
    if filepath.exists():
        print(f"Skipping (exists): {filepath}")
        return filepath

    content = f'''---
title: "{course.get('name', course.get('title', 'Training Course'))}"
description: "{course.get('description', 'Professional training course from Kartoza')[:200]}"
thumbnail: "/img/training/{slug}.jpg"
duration: "{course.get('duration', 'Contact us for details')}"
level: "{course.get('level', 'All levels')}"
format: "{course.get('format', 'Online or In-person')}"
price: ""
syllabus: []
draft: false
---

{{{{< block
    title="{course.get('name', course.get('title', 'Training Course'))}"
    subtitle="Professional GIS Training"
    class="is-primary"
    sub-block-side="bottom"
>}}}}
{course.get('description', 'Course description coming soon.')}
{{{{< /block >}}}}

## Overview

{course.get('overview', course.get('description', 'Course overview coming soon.'))}

## What You Will Learn

- Course content details coming soon

## Prerequisites

{course.get('prerequisites', 'Contact us for prerequisite information.')}

## Duration

{course.get('duration', 'Contact us for duration details.')}

{{{{< button-bar >}}}}
{{{{< button link="/contact-us/" text="Enquire About This Course" class="is-primary" >}}}}
{{{{< button link="/training-courses/" text="View All Courses" class="is-secondary" >}}}}
{{{{< /button-bar >}}}}
'''

    if dry_run:
        print(f"Would create: {filepath}")
    else:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content)
        print(f"Created: {filepath}")

    return filepath


def save_calendar_data(events: list, dry_run: bool = False):
    """Save training events as JSON data for calendar view."""
    CALENDAR_DATA_DIR.mkdir(parents=True, exist_ok=True)
    data_file = CALENDAR_DATA_DIR / "events.json"

    calendar_events = []
    for event in events:
        calendar_events.append({
            "title": event.get("course_name", event.get("name", "Training Event")),
            "start": event.get("start_date", ""),
            "end": event.get("end_date", ""),
            "location": event.get("location", "Online"),
            "url": f"/training-courses/{slugify(event.get('course_name', 'course'))}/",
            "description": event.get("description", ""),
            "registration_url": event.get("registration_url", "/contact-us/"),
            "price": event.get("price", "Contact for pricing"),
            "spots_available": event.get("spots_available", "")
        })

    if dry_run:
        print(f"Would save calendar data to: {data_file}")
        print(f"Events: {len(calendar_events)}")
    else:
        data_file.write_text(json.dumps(calendar_events, indent=2))
        print(f"Saved {len(calendar_events)} events to: {data_file}")


def list_training_content():
    """List all training content from ERPNext and local."""
    print("=" * 60)
    print("Training Content")
    print("=" * 60)

    print("\nERPNext Courses:")
    print("-" * 40)
    courses = fetch_courses_from_erpnext()
    if courses:
        for course in courses:
            name = course.get("name", course.get("title", "Unknown"))
            print(f"  - {name}")
    else:
        print("  No courses fetched from ERPNext")
        print("  (API may require authentication)")

    print("\nERPNext Scheduled Events:")
    print("-" * 40)
    events = fetch_scheduled_events_from_erpnext()
    if events:
        for event in events:
            name = event.get("course_name", event.get("name", "Unknown"))
            date = event.get("start_date", "TBD")
            print(f"  - {name} ({date})")
    else:
        print("  No scheduled events fetched from ERPNext")

    print("\nLocal Courses:")
    print("-" * 40)
    local_courses = get_existing_courses()
    if local_courses:
        for slug, info in sorted(local_courses.items()):
            print(f"  - {slug}")
    else:
        print("  No local courses found")


def sync_training_content(dry_run: bool = False):
    """Sync training content from ERPNext."""
    print("=" * 60)
    print("Syncing Training Content")
    print("=" * 60)

    # Fetch courses
    print("\nFetching courses...")
    courses = fetch_courses_from_erpnext()
    local_courses = get_existing_courses()

    if courses:
        new_courses = []
        for course in courses:
            slug = slugify(course.get("name", course.get("title", "")))
            if slug and slug not in local_courses:
                new_courses.append(course)
                create_course_page(course, dry_run)

        print(f"New courses added: {len(new_courses)}")
    else:
        print("No courses fetched from ERPNext")

    # Fetch and save scheduled events
    print("\nFetching scheduled events...")
    events = fetch_scheduled_events_from_erpnext()
    if events:
        save_calendar_data(events, dry_run)
    else:
        print("No scheduled events fetched from ERPNext")
        # Create empty events file if it doesn't exist
        if not dry_run:
            CALENDAR_DATA_DIR.mkdir(parents=True, exist_ok=True)
            events_file = CALENDAR_DATA_DIR / "events.json"
            if not events_file.exists():
                events_file.write_text("[]")


def main():
    parser = argparse.ArgumentParser(description="Fetch training content from ERPNext")
    parser.add_argument("--list", action="store_true", help="List content without syncing")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without making them")
    args = parser.parse_args()

    if args.list:
        list_training_content()
    else:
        sync_training_content(args.dry_run)


if __name__ == "__main__":
    main()
