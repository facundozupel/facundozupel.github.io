#!/bin/bash
# Download images from Wikimedia Commons, convert to WebP
# Usage: ./download-wikimedia.sh <url> <output_path> <width>
# Example: ./download-wikimedia.sh "https://upload.wikimedia.org/..." "public/assets/cascadas/salto-del-laja/hero.webp" 1600

set -euo pipefail

URL="$1"
OUTPUT="$2"
WIDTH="${3:-1600}"

TMPFILE=$(mktemp /tmp/wikimedia-XXXXXX)

echo "Downloading: $URL"
curl -s -L -A "CascadasDeChile/1.0 (cascadaschile.com)" -o "$TMPFILE" "$URL"

# Get file size
SIZE=$(wc -c < "$TMPFILE" | tr -d ' ')
echo "  Downloaded: ${SIZE} bytes"

# Create output directory if needed
mkdir -p "$(dirname "$OUTPUT")"

# Convert to WebP using cwebp with resize
# First resize with sips (macOS native), then convert with cwebp
TMPRESIZED=$(mktemp /tmp/wikimedia-resized-XXXXXX.png)

# Use sips to resize maintaining aspect ratio
sips --resampleWidth "$WIDTH" "$TMPFILE" --out "$TMPRESIZED" 2>/dev/null || {
    # If sips fails (e.g. unsupported format), try converting first
    sips -s format png "$TMPFILE" --out "$TMPRESIZED" 2>/dev/null
    sips --resampleWidth "$WIDTH" "$TMPRESIZED" --out "$TMPRESIZED" 2>/dev/null
}

# Convert to WebP with quality 80
cwebp -q 80 -m 6 "$TMPRESIZED" -o "$OUTPUT" 2>/dev/null

# Report
OUTSIZE=$(wc -c < "$OUTPUT" | tr -d ' ')
echo "  Output: $OUTPUT (${OUTSIZE} bytes)"

# Cleanup
rm -f "$TMPFILE" "$TMPRESIZED"
