#!/usr/bin/env bash
# Create a new imaging session folder with the standard layout.
#
# Usage:
#   ./new-session.sh <category> <object_name> <session_id>
#
# Example:
#   ./new-session.sh galaxies M51_Whirlpool 2026-04-12_origin_native
#
# This creates:
#   projects/galaxies/M51_Whirlpool/sessions/2026-04-12_origin_native/
#   with manifest.yml, raw/, work/, output/, logs/, notes.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ $# -lt 3 ]; then
    echo "Usage: $0 <category> <object_name> <session_id>"
    echo "Example: $0 galaxies M51_Whirlpool 2026-04-12_origin_native"
    exit 1
fi

CATEGORY="$1"
OBJECT="$2"
SESSION="$3"

OBJECT_DIR="$ROOT/projects/$CATEGORY/$OBJECT"
SESSION_DIR="$OBJECT_DIR/sessions/$SESSION"

if [ -d "$SESSION_DIR" ]; then
    echo "ERROR: Session already exists: $SESSION_DIR"
    exit 1
fi

# Create object folder if it doesn't exist
mkdir -p "$OBJECT_DIR"/{sessions,master,exports}
if [ ! -f "$OBJECT_DIR/object_profile.yml" ]; then
    cp "$ROOT/scripts/templates/object_profile.yml" "$OBJECT_DIR/object_profile.yml"
    echo "Created object_profile.yml -- edit it for $OBJECT"
fi
if [ ! -f "$OBJECT_DIR/notes.md" ]; then
    echo "# $OBJECT" > "$OBJECT_DIR/notes.md"
    echo "" >> "$OBJECT_DIR/notes.md"
    echo "Processing journal and lessons learned." >> "$OBJECT_DIR/notes.md"
fi

# Create session folder (work/lights is where raw FITS go for Siril)
mkdir -p "$SESSION_DIR"/{raw,work/lights,output,logs}

# Copy and partially fill manifest
cp "$ROOT/scripts/templates/session_manifest.yml" "$SESSION_DIR/manifest.yml"

# Create session notes
cat > "$SESSION_DIR/notes.md" <<EOF
# Session: $SESSION

**Object:** $OBJECT
**Category:** $CATEGORY

## Conditions


## Decisions


## Results

EOF

echo "Created: $SESSION_DIR"
echo ""
echo "Next steps:"
echo "  1. Import FITS (pick one):"
echo "     ./scripts/shell/import-fits.sh $SESSION_DIR --scan \"$OBJECT\""
echo "     ./scripts/shell/import-fits.sh $SESSION_DIR /path/to/origin/dir/"
echo "  2. Preprocess:"
echo "     python scripts/python/preprocess_all.py $(dirname $(dirname $SESSION_DIR)) --session $SESSION"
