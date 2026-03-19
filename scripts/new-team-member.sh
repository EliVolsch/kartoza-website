#!/usr/bin/env bash
# Create a new team member page
# Usage: ./new-team-member.sh "First Last"

set -euo pipefail

CONTENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/content/the_team"
NAME="${1:-}"

if [[ -z "$NAME" ]]; then
    read -rp "Team member name: " NAME
fi

if [[ -z "$NAME" ]]; then
    echo "Error: Name is required" >&2
    exit 1
fi

# Generate slug from name
SLUG=$(echo "$NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//')
FILENAME="${CONTENT_DIR}/${SLUG}.md"

if [[ -f "$FILENAME" ]]; then
    echo "Error: File already exists: $FILENAME" >&2
    exit 1
fi

cat > "$FILENAME" << EOF
---
title: "${NAME}"
role: "Job Title"
department: "Development"
departmentIcon: "fa-code"
weight: 50
draft: false
image: "/img/team/${SLUG}.jpg"
location: "City, Country"
country: "Country"
coordinates: "0.0, 0.0"
github: "github-username"
education:
  - degree: "Degree Name"
skills:
  - "Skill 1"
  - "Skill 2"
  - "Skill 3"
achievements:
  - "Achievement 1"
  - "Achievement 2"
bio: "Short one-line bio."
---

Full biography of the team member. Describe their background, experience, and what they bring to Kartoza.

Their expertise and areas of focus.

Personal interests or additional information.
EOF

echo "$FILENAME"
