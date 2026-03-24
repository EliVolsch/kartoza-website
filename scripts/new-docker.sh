#!/usr/bin/env bash
# Create a new Docker image page
# Usage: ./new-docker.sh "Image Name"

set -euo pipefail

CONTENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/content/docker"
TITLE="${1:-}"

if [[ -z "$TITLE" ]]; then
    read -rp "Docker image name: " TITLE
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
description: "Brief description of the Docker image."
thumbnail: "/img/docker/${SLUG}.png"
dockerhub: "https://hub.docker.com/r/kartoza/${SLUG}"
github: "https://github.com/kartoza/docker-${SLUG}"
pulls: "1K+"
stars: 10
tags:
  - Docker
  - DevOps
upstream:
  name: "${TITLE}"
  url: "https://example.com"
  description: "Description of the upstream project."
date: ${DATE}
weight: 10
---

## Overview

Detailed description of the Docker image and its purpose.

## Features

- **Feature 1** - Description
- **Feature 2** - Description
- **Feature 3** - Description

## Quick Start

### Basic Usage

\`\`\`bash
docker run -d \\
  --name ${SLUG} \\
  -p 8080:8080 \\
  kartoza/${SLUG}:latest
\`\`\`

### With Docker Compose

\`\`\`yaml
version: '3.8'
services:
  ${SLUG}:
    image: kartoza/${SLUG}:latest
    ports:
      - "8080:8080"
    volumes:
      - ./data:/data
\`\`\`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| \`VAR_NAME\` | Description | \`default\` |

## Links

- [Docker Hub](https://hub.docker.com/r/kartoza/${SLUG})
- [GitHub Repository](https://github.com/kartoza/docker-${SLUG})
EOF

echo "$FILENAME"
