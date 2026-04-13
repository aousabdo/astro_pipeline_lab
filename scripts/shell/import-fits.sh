#!/usr/bin/env bash
# Import FITS files from a source directory into a session's work/lights/.
#
# Handles:
#   - Symlinks (default) or copies
#   - Auto-discovers Light*.fits files
#   - Validates FITS exist before linking
#   - Also copies Origin's info.json and stacked TIFF if present
#   - Can scan the default Origin data directory by target name
#
# Usage:
#   ./import-fits.sh <session_path> <source_dir>
#   ./import-fits.sh <session_path> <source_dir> --copy     # copy instead of symlink
#   ./import-fits.sh <session_path> --scan <target_name>    # find Origin dirs by name
#
# Examples:
#   ./import-fits.sh projects/nebulae/M42_Orion/sessions/2026-02-12_origin_native \
#       ~/Documents/astro_imaging/Celestron_Origin/Astrophotography/Orion_Nebula_2026-02-12_19-38-32
#
#   ./import-fits.sh projects/nebulae/M42_Orion/sessions/2026-02-12_origin_native \
#       --scan "Orion_Nebula"

set -euo pipefail

ORIGIN_BASE="$HOME/Documents/astro_imaging/Celestron_Origin/Astrophotography"

usage() {
    echo "Usage: $0 <session_path> <source_dir> [--copy]"
    echo "       $0 <session_path> --scan <target_name>"
    echo ""
    echo "Examples:"
    echo "  $0 projects/nebulae/M42_Orion/sessions/2026-02-12_origin_native /path/to/fits/"
    echo "  $0 projects/nebulae/M42_Orion/sessions/2026-02-12_origin_native --scan Orion_Nebula"
    exit 1
}

[ $# -lt 2 ] && usage

SESSION_DIR="$1"
shift

# Resolve session path
if [ ! -d "$SESSION_DIR" ]; then
    echo "ERROR: Session directory not found: $SESSION_DIR"
    exit 1
fi

LIGHTS_DIR="$SESSION_DIR/work/lights"
mkdir -p "$LIGHTS_DIR"

MODE="symlink"
SOURCE_DIR=""

# Parse arguments
if [ "$1" = "--scan" ]; then
    [ $# -lt 2 ] && usage
    TARGET_NAME="$2"
    shift 2

    echo "Scanning $ORIGIN_BASE for '$TARGET_NAME'..."
    echo ""

    # Find matching directories
    matches=()
    while IFS= read -r dir; do
        [ -d "$dir" ] || continue
        fits_count=$(ls "$dir"/Light*.fits 2>/dev/null | wc -l | tr -d ' ')
        [ "$fits_count" -eq 0 ] && continue
        # Get date from info.json if available
        info=""
        if [ -f "$dir/info.json" ]; then
            info=$(python3 -c "
import json
with open('$dir/info.json') as f:
    d = json.load(f)['StackedInfo']
print(f\"{d['dateTime'][:10]}  {d['captureParams']['exposure']:.0f}s  {d['stackedDepth']}/{int('$fits_count')} frames  {d['filter']}\")
" 2>/dev/null || echo "")
        fi
        matches+=("$dir")
        echo "  [${#matches[@]}] $(basename "$dir")"
        [ -n "$info" ] && echo "      $info"
    done < <(find "$ORIGIN_BASE" -maxdepth 1 -type d -name "*${TARGET_NAME}*" | sort)

    if [ ${#matches[@]} -eq 0 ]; then
        echo "No matching directories found for '$TARGET_NAME'"
        echo ""
        echo "Available targets in $ORIGIN_BASE:"
        ls -1 "$ORIGIN_BASE" | sed 's/_20[0-9][0-9]-.*//' | sort -u | sed 's/^/  /'
        exit 1
    fi

    echo ""
    if [ ${#matches[@]} -eq 1 ]; then
        SOURCE_DIR="${matches[0]}"
        echo "Using: $(basename "$SOURCE_DIR")"
    else
        echo -n "Select directory [1-${#matches[@]}]: "
        read -r choice
        if [ -z "$choice" ] || [ "$choice" -lt 1 ] || [ "$choice" -gt ${#matches[@]} ] 2>/dev/null; then
            echo "Invalid selection"
            exit 1
        fi
        SOURCE_DIR="${matches[$((choice-1))]}"
    fi
else
    SOURCE_DIR="$1"
    shift
    # Check for --copy flag
    [ "${1:-}" = "--copy" ] && MODE="copy"
fi

# Validate source
if [ ! -d "$SOURCE_DIR" ]; then
    echo "ERROR: Source directory not found: $SOURCE_DIR"
    exit 1
fi

# Find FITS files
FITS_FILES=("$SOURCE_DIR"/Light*.fits)
if [ ! -f "${FITS_FILES[0]}" ]; then
    # Try lowercase
    FITS_FILES=("$SOURCE_DIR"/light*.fits)
fi
if [ ! -f "${FITS_FILES[0]}" ]; then
    echo "ERROR: No Light*.fits files found in $SOURCE_DIR"
    exit 1
fi

COUNT=${#FITS_FILES[@]}
echo ""
echo "Found $COUNT FITS files in $(basename "$SOURCE_DIR")"

# Import
if [ "$MODE" = "copy" ]; then
    echo "Copying $COUNT files..."
    cp "${FITS_FILES[@]}" "$LIGHTS_DIR/"
else
    echo "Symlinking $COUNT files..."
    for f in "${FITS_FILES[@]}"; do
        ln -sf "$f" "$LIGHTS_DIR/"
    done
fi

# Verify
LINKED=$(ls "$LIGHTS_DIR"/*.fits 2>/dev/null | wc -l | tr -d ' ')
echo "Linked: $LINKED files in $LIGHTS_DIR"

# Copy metadata if available
if [ -f "$SOURCE_DIR/info.json" ]; then
    cp "$SOURCE_DIR/info.json" "$SESSION_DIR/"
    echo "Copied: info.json"
fi

# Copy Origin stacked TIFF if present (for quick_tiff workflow)
if [ -f "$SOURCE_DIR/FinalStackedMaster.tiff" ]; then
    WORK_DIR="$SESSION_DIR/work"
    if [ ! -f "$WORK_DIR/origin_stack.tif" ]; then
        cp "$SOURCE_DIR/FinalStackedMaster.tiff" "$WORK_DIR/origin_stack.tif"
        echo "Copied: FinalStackedMaster.tiff → work/origin_stack.tif"
    fi
fi

echo ""
echo "Done. Ready to preprocess."
