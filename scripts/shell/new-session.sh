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
#   with manifest.yml, raw/, work/lights/, output/, logs/, notes.md

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
    # Check if lights already imported
    lights_count=$(find "$SESSION_DIR/work/lights" -name "*.fits" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$lights_count" -gt 0 ]; then
        echo "Session already exists with $lights_count FITS files: $SESSION_DIR"
        echo -n "Use existing session? [Y/n] "
        read -r ans
        if [ "${ans:-Y}" = "n" ] || [ "${ans:-Y}" = "N" ]; then
            echo "Aborted. Remove it manually if you want to start fresh:"
            echo "  rm -rf $SESSION_DIR"
            exit 1
        fi
    else
        echo "Session exists but has no FITS imported yet: $SESSION_DIR"
    fi
    echo ""
else
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
fi

echo "Next steps:"
echo "  1. Import FITS:"
echo "     ./scripts/shell/import-fits.sh $SESSION_DIR --scan \"<origin_target_name>\""
echo "     (e.g. Rosette_Nebula, Orion_Nebula, Horsehead_Nebula, Sombrero_Galaxy)"
echo ""
echo "  2. Preprocess:"
echo "     python scripts/python/preprocess_all.py $OBJECT_DIR --session $SESSION"
