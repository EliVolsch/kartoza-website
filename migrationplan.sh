#!/usr/bin/env bash

# Convert migration plan markdown with Mermaid diagrams to PDF
# Requires: pandoc, npx (for mermaid-cli), chromium/chrome for rendering

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_FILE="${SCRIPT_DIR}/migrationplan.md"
OUTPUT_PDF="${SCRIPT_DIR}/Kartoza_Website_Migration_Plan.pdf"
TEMP_DIR=$(mktemp -d)
PROCESSED_MD="${TEMP_DIR}/processed.md"

cleanup() {
    rm -rf "${TEMP_DIR}"
}
trap cleanup EXIT

# Check dependencies
if ! command -v pandoc &> /dev/null; then
    echo "Error: pandoc is required but not installed."
    exit 1
fi

if ! command -v npx &> /dev/null; then
    echo "Error: npx (Node.js) is required but not installed."
    exit 1
fi

if [[ ! -f "${INPUT_FILE}" ]]; then
    echo "Error: ${INPUT_FILE} not found."
    exit 1
fi

echo "Processing Mermaid diagrams..."

# Extract and render each mermaid diagram
cp "${INPUT_FILE}" "${PROCESSED_MD}"
diagram_count=0

# Find all mermaid code blocks and render them
while IFS= read -r -d '' block; do
    ((diagram_count++)) || true
    diagram_file="${TEMP_DIR}/diagram_${diagram_count}.mmd"
    image_file="${TEMP_DIR}/diagram_${diagram_count}.png"

    # Write the mermaid code to a file
    echo "$block" > "${diagram_file}"

    # Render with mermaid-cli
    echo "  Rendering diagram ${diagram_count}..."
    npx --yes @mermaid-js/mermaid-cli -i "${diagram_file}" -o "${image_file}" -b white -w 800 2>/dev/null || {
        echo "    Warning: Failed to render diagram ${diagram_count}, keeping as code block"
        continue
    }

    # Replace the mermaid block with an image reference in the markdown
    # We need to escape special chars for sed
    escaped_block=$(printf '%s\n' "$block" | sed 's/[[\.*^$()+?{|]/\\&/g' | tr '\n' '\001')

done < <(grep -Pzo '(?s)```mermaid\n\K.*?(?=\n```)' "${INPUT_FILE}" | tr '\0' '\n' | awk 'BEGIN{RS=""; ORS="\0"}{print}')

# Alternative approach: use pandoc with mermaid filter
echo "Generating PDF with pandoc and mermaid filter..."

# Create a lua filter for mermaid
cat > "${TEMP_DIR}/mermaid-filter.lua" << 'LUAEOF'
local system = require 'pandoc.system'

local function render_mermaid(code, filetype)
    return pandoc.pipe('npx', {'--yes', '@mermaid-js/mermaid-cli', '-i', '/dev/stdin', '-o', '/dev/stdout', '-e', filetype, '-b', 'white'}, code)
end

function CodeBlock(block)
    if block.classes[1] == 'mermaid' then
        local success, img = pcall(render_mermaid, block.text, 'png')
        if success then
            local fname = system.with_temporary_directory('mermaid', function(tmpdir)
                local fpath = tmpdir .. '/diagram.png'
                local f = io.open(fpath, 'wb')
                f:write(img)
                f:close()
                return fpath
            end)
            return pandoc.Para{pandoc.Image({}, fname)}
        end
    end
end
LUAEOF

# Try using pandoc with mermaid filter via docker or direct rendering
# Since mermaid-cli piping is complex, let's pre-render all diagrams

echo "Pre-rendering Mermaid diagrams..."
mkdir -p "${TEMP_DIR}/images"

# Extract mermaid blocks, render them, and create a new markdown with image references
awk '
BEGIN { in_mermaid = 0; diagram_num = 0; }
/^```mermaid/ {
    in_mermaid = 1;
    diagram_num++;
    mermaid_file = "'"${TEMP_DIR}"'/mermaid_" diagram_num ".mmd"
    next
}
/^```$/ && in_mermaid {
    in_mermaid = 0;
    close(mermaid_file)
    print "![Diagram " diagram_num "]('"${TEMP_DIR}"'/images/mermaid_" diagram_num ".png)"
    next
}
in_mermaid { print > mermaid_file; next }
{ print }
' "${INPUT_FILE}" > "${PROCESSED_MD}"

# Render each mermaid file
for mmd_file in "${TEMP_DIR}"/mermaid_*.mmd; do
    if [[ -f "${mmd_file}" ]]; then
        base=$(basename "${mmd_file}" .mmd)
        echo "  Rendering ${base}..."
        npx --yes @mermaid-js/mermaid-cli \
            -i "${mmd_file}" \
            -o "${TEMP_DIR}/images/${base}.png" \
            -b white \
            -w 1200 \
            --scale 2 \
            2>/dev/null || echo "    Warning: Failed to render ${base}"
    fi
done

echo "Converting to PDF..."

pandoc "${PROCESSED_MD}" -o "${OUTPUT_PDF}" \
    --from markdown \
    --to pdf \
    --pdf-engine=xelatex \
    --toc \
    --toc-depth=3 \
    --highlight-style=tango \
    --variable geometry:margin=1in \
    --variable fontsize=11pt \
    --variable colorlinks=true \
    --variable linkcolor=blue \
    --variable urlcolor=blue \
    --metadata title="Kartoza Website Migration Plan" \
    --metadata subtitle="kartoza.com Infrastructure Transition" \
    --metadata author="Kartoza Team" \
    --metadata date="$(date +'%d %B %Y')" \
    --standalone

echo "PDF created: ${OUTPUT_PDF}"
