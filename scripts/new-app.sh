#!/usr/bin/env bash
# Create a new app page
# Usage: ./new-app.sh "My App Name"

set -euo pipefail

CONTENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/content/apps"
TITLE="${1:-}"

if [[ -z "$TITLE" ]]; then
    read -rp "App name: " TITLE
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
description: "Brief description of the app."
thumbnail: "/img/apps/${SLUG}.png"
tags:
  - Mobile
  - Web
date: ${DATE}
---

{{< block
    title="${TITLE}"
    subtitle="App tagline"
    class="is-primary"
    sub-block-side="bottom"
    link="https://example.com"
    link-text="Try the App"
>}}
Brief description of what the app does.
{{< /block >}}

## Overview

Detailed description of the app and its purpose.

![${TITLE}](/img/apps/${SLUG}.png)

## Features

- Feature 1
- Feature 2
- Feature 3

## Download

- [Google Play Store](https://play.google.com/store/apps/details?id=com.example)
- [Apple App Store](https://apps.apple.com/app/example)
EOF

echo "$FILENAME"
