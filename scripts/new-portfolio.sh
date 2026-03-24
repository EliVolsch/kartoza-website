#!/usr/bin/env bash
# Create a new portfolio project page
# Usage: ./new-portfolio.sh "Project Name"

set -euo pipefail

CONTENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/content/portfolio"
TITLE="${1:-}"

if [[ -z "$TITLE" ]]; then
    read -rp "Project name: " TITLE
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
description: "Brief description of the project."
thumbnail: "/img/portfolio/${SLUG}.png"
tags:
  - GIS
  - Development
client: "Client Name"
date: ${DATE}
services:
  - Development
  - Training
related_plugins:
  - plugin-slug
---

{{< block
    title="${TITLE}"
    subtitle="Project tagline"
    class="is-primary"
    sub-block-side="bottom"
    link="https://example.com"
    link-text="Visit Project"
>}}
Brief description of the project and its impact.
{{< /block >}}

## Overview

Detailed description of the project, its goals, and outcomes.

![${TITLE}](/img/portfolio/${SLUG}.png)

## Challenge

What problem did this project solve?

## Solution

How did Kartoza address the challenge?

## Outcomes

What were the results and impact?

## Links

- [Project Website](https://example.com)
EOF

echo "$FILENAME"
