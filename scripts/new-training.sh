#!/usr/bin/env bash
# Create a new training course page
# Usage: ./new-training.sh "Course Title"

set -euo pipefail

CONTENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/content/training-courses"
TITLE="${1:-}"

if [[ -z "$TITLE" ]]; then
    read -rp "Course title: " TITLE
fi

if [[ -z "$TITLE" ]]; then
    echo "Error: Title is required" >&2
    exit 1
fi

# Generate slug from title
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//')
FILENAME="${CONTENT_DIR}/${SLUG}.md"
DATE=$(date +%Y-%m-%d)

if [[ -f "$FILENAME" ]]; then
    echo "Error: File already exists: $FILENAME" >&2
    exit 1
fi

cat > "$FILENAME" << EOF
---
title: "${TITLE}"
description: "Brief description of the training course."
thumbnail: "/img/courses/${SLUG}.svg"
duration: "3 Days"
level: "Beginner"
track: "Desktop GIS"
trackOrder: 1
weight: 10
tags:
  - QGIS
  - Training
date: ${DATE}
---

## Course Overview

Comprehensive description of what participants will learn in this course.

## What You Will Learn

- Learning objective 1
- Learning objective 2
- Learning objective 3
- Learning objective 4
- Learning objective 5

## Who Should Attend

This course is ideal for:

- Target audience 1
- Target audience 2
- Target audience 3

## Prerequisites

List any prerequisites or prior knowledge required.

## Course Outline

### Day 1: Topic

- Session 1
- Session 2

### Day 2: Topic

- Session 3
- Session 4

### Day 3: Topic

- Session 5
- Session 6

## Materials Provided

- Course workbook
- Sample datasets
- Certificate of completion
EOF

echo "$FILENAME"
