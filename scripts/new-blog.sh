#!/usr/bin/env bash
# Create a new blog post
# Usage: ./new-blog.sh "My Blog Title"

set -euo pipefail

CONTENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/content/blog"
TITLE="${1:-}"

if [[ -z "$TITLE" ]]; then
    read -rp "Blog post title: " TITLE
fi

if [[ -z "$TITLE" ]]; then
    echo "Error: Title is required" >&2
    exit 1
fi

# Generate slug from title
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//')
FILENAME="${CONTENT_DIR}/${SLUG}.md"
DATE=$(date +%Y-%m-%d)

# Get git user for author
AUTHOR=$(git config user.name 2>/dev/null || echo "Author Name")

if [[ -f "$FILENAME" ]]; then
    echo "Error: File already exists: $FILENAME" >&2
    exit 1
fi

cat > "$FILENAME" << EOF
---
title: "${TITLE}"
description: "Brief description of the blog post."
tags:
  - Tag1
  - Tag2
date: ${DATE}
author: "${AUTHOR}"
thumbnail: "/img/blog/placeholder.png"
---

{{< block
    title="${TITLE}"
    subtitle="Subtitle"
    class="is-primary"
    sub-block-side="bottom"
>}}
Brief introduction to the blog post.
{{< /block >}}

## Introduction

Write your introduction here.

## Main Content

Main content goes here.

## Conclusion

Concluding thoughts.
EOF

echo "$FILENAME"
