#!/usr/bin/env bash
# Create a new QGIS plugin page
# Usage: ./new-plugin.sh "My Plugin Name"

set -euo pipefail

CONTENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/content/plugins"
TITLE="${1:-}"

if [[ -z "$TITLE" ]]; then
    read -rp "Plugin name: " TITLE
fi

if [[ -z "$TITLE" ]]; then
    echo "Error: Title is required" >&2
    exit 1
fi

# Generate slug from title
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//')
FILENAME="${CONTENT_DIR}/${SLUG}.md"

if [[ -f "$FILENAME" ]]; then
    echo "Error: File already exists: $FILENAME" >&2
    exit 1
fi

cat > "$FILENAME" << EOF
---
title: "${TITLE}"
description: "Brief description of the QGIS plugin."
thumbnail: "/img/plugins/${SLUG}.png"
plugin_type: "kartoza"
client: "Client Name"
client_url: "https://client.example.com"
downloads: "1,000+"
version: "1.0.0"
rating: "5.0"
votes: 10
repository: "https://github.com/kartoza/${SLUG}"
plugin_url: "https://plugins.qgis.org/plugins/${SLUG}/"
homepage: "https://kartoza.com"
qgis_min: "3.22.0"
qgis_max: "3.99.0"
tags:
  - QGIS
  - Plugin
related_portfolio:
  - portfolio-slug
weight: 50
---

## Overview

Detailed description of what the plugin does and its purpose.

## Key Features

- **Feature 1**: Description
- **Feature 2**: Description
- **Feature 3**: Description

## Installation

1. Open QGIS
2. Go to Plugins → Manage and Install Plugins
3. Search for "${TITLE}"
4. Click Install

## Usage

Instructions on how to use the plugin.

## Links

- [GitHub Repository](https://github.com/kartoza/${SLUG})
- [QGIS Plugin Repository](https://plugins.qgis.org/plugins/${SLUG}/)
EOF

echo "$FILENAME"
