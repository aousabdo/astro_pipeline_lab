#!/usr/bin/env python3
"""
Astro Pipeline Lab -- Session Processor

Reads a session manifest, selects the right Siril scripts,
runs preprocessing + post-processing, and organizes outputs.

Usage:
    python process_session.py <session_path>
    python process_session.py projects/galaxies/M51_Whirlpool/sessions/2026-04-12_origin_native

Requires:
    - siril-cli on PATH
    - Python 3.10+
    - PyYAML: pip install pyyaml
"""

import argparse
import logging
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "siril"

PREPROCESS_SCRIPTS = {
    "lights_only": SCRIPTS_DIR / "preprocess_lights_only.ssf",
    "with_darks": SCRIPTS_DIR / "preprocess_with_darks.ssf",
    "full_cal": SCRIPTS_DIR / "preprocess_full_cal.ssf",
}

POSTPROCESS_SCRIPTS = {
    "galaxy": SCRIPTS_DIR / "postprocess_galaxy.ssf",
    "nebula": SCRIPTS_DIR / "postprocess_nebula.ssf",
    "nebula_filter": SCRIPTS_DIR / "postprocess_nebula_filter.ssf",
    "cluster": SCRIPTS_DIR / "postprocess_cluster.ssf",
}

# Nebula/dual-band filter names that should skip PCC
NEBULA_FILTERS = {"nebula", "uhc", "l-enhance", "l-extreme", "cls", "dual-band", "ha", "oiii", "sii"}

# Map manifest categories to postprocess script keys
CATEGORY_MAP = {
    "galaxy": "galaxy",
    "nebula": "nebula",
    "cluster": "cluster",
    "comet": "galaxy",       # conservative by default
    "widefield": "nebula",   # balanced by default
    "moon_planet": "galaxy",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("pipeline")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_manifest(session_path: Path) -> dict:
    """Load and validate the session manifest."""
    manifest_path = session_path / "manifest.yml"
    if not manifest_path.exists():
        log.error(f"No manifest.yml found in {session_path}")
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)

    required = ["session", "object", "category", "acquisition"]
    for key in required:
        if key not in manifest:
            log.error(f"Manifest missing required field: {key}")
            sys.exit(1)

    return manifest


def detect_calibration(session_path: Path) -> str:
    """Figure out which preprocess script to use based on available data."""
    work = session_path / "work"
    has_lights = (work / "lights").exists() and any((work / "lights").iterdir())
    has_darks = (work / "darks").exists() and any((work / "darks").iterdir())
    has_flats = (work / "flats").exists() and any((work / "flats").iterdir())
    has_biases = (work / "biases").exists() and any((work / "biases").iterdir())

    if not has_lights:
        log.error("No light frames found in work/lights/")
        sys.exit(1)

    if has_darks and has_flats and has_biases:
        return "full_cal"
    elif has_darks:
        return "with_darks"
    else:
        return "lights_only"


def run_siril(script: Path, workdir: Path, log_path: Path) -> bool:
    """Run a Siril script and capture output."""
    # Ensure process/ and masters/ dirs exist (Siril scripts cd into them)
    (workdir / "process").mkdir(exist_ok=True)
    (workdir / "masters").mkdir(exist_ok=True)

    cmd = ["siril-cli", "-s", str(script), "-d", str(workdir)]
    log.info(f"Running: {' '.join(cmd)}")

    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout
        )
    except FileNotFoundError:
        log.error("siril-cli not found on PATH. Install Siril and ensure siril-cli is available.")
        return False
    except subprocess.TimeoutExpired:
        log.error("Siril timed out after 1 hour")
        return False

    elapsed = time.time() - start

    # Write log
    with open(log_path, "a") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Script: {script.name}\n")
        f.write(f"Time: {datetime.now().isoformat()}\n")
        f.write(f"Duration: {elapsed:.1f}s\n")
        f.write(f"Exit code: {result.returncode}\n")
        f.write(f"\n--- STDOUT ---\n{result.stdout}\n")
        if result.stderr:
            f.write(f"\n--- STDERR ---\n{result.stderr}\n")

    if result.returncode != 0:
        log.error(f"Siril failed (exit {result.returncode}). Check {log_path}")
        log.error(f"Last stderr: {result.stderr[-500:]}" if result.stderr else "No stderr")
        return False

    log.info(f"Siril completed in {elapsed:.1f}s")
    return True


def update_manifest_status(session_path: Path, field: str, value):
    """Update a status field in the manifest."""
    manifest_path = session_path / "manifest.yml"
    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)

    if "status" not in manifest:
        manifest["status"] = {}
    manifest["status"][field] = value

    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def process_session(session_path: Path, skip_preprocess: bool = False, skip_postprocess: bool = False):
    """Run the full pipeline on a session."""
    session_path = session_path.resolve()
    log.info(f"Processing session: {session_path.name}")

    # Load manifest
    manifest = load_manifest(session_path)
    category = manifest["category"]
    log.info(f"Object: {manifest['object']} | Category: {category}")

    # Ensure output and log dirs
    output_dir = session_path / "output"
    output_dir.mkdir(exist_ok=True)
    logs_dir = session_path / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_path = logs_dir / "pipeline.log"

    work_dir = session_path / "work"
    if not work_dir.exists():
        log.error(f"No work/ directory in session. Set up the session first.")
        sys.exit(1)

    # --- PREPROCESS ---
    if not skip_preprocess:
        cal_type = detect_calibration(session_path)
        preprocess_script = PREPROCESS_SCRIPTS[cal_type]
        log.info(f"Calibration type: {cal_type} -> {preprocess_script.name}")

        if not run_siril(preprocess_script, work_dir, log_path):
            log.error("Preprocessing failed. Aborting.")
            sys.exit(1)

        update_manifest_status(session_path, "stacked", True)
        log.info("Preprocessing complete. Linear master created.")
    else:
        log.info("Skipping preprocessing (--skip-preprocess)")

    # Check that result.fits exists (try both .fit and .fits)
    result_fit = work_dir / "result.fits"
    if not result_fit.exists():
        result_fit = work_dir / "result.fit"
    if not result_fit.exists():
        log.error(f"No result.fit or result.fits found in {work_dir}. Preprocessing may have failed.")
        sys.exit(1)

    # --- POSTPROCESS ---
    if not skip_postprocess:
        post_key = CATEGORY_MAP.get(category, "galaxy")

        # For nebulae with a nebula/dual-band filter, use the no-PCC script
        acq_filter = manifest.get("acquisition", {}).get("filter", "none")
        if post_key == "nebula" and acq_filter.lower() in NEBULA_FILTERS:
            post_key = "nebula_filter"
            log.info(f"Detected nebula filter '{acq_filter}' -- skipping PCC")

        postprocess_script = POSTPROCESS_SCRIPTS[post_key]
        log.info(f"Post-processing with: {postprocess_script.name}")

        if not run_siril(postprocess_script, work_dir, log_path):
            log.error("Post-processing failed. Check logs.")
            sys.exit(1)

        update_manifest_status(session_path, "processed", True)
        log.info("Post-processing complete.")
    else:
        log.info("Skipping post-processing (--skip-postprocess)")

    # --- Summary ---
    outputs = list(output_dir.glob("*"))
    if outputs:
        log.info(f"Outputs ({len(outputs)} files):")
        for f in sorted(outputs):
            size_mb = f.stat().st_size / (1024 * 1024)
            log.info(f"  {f.name} ({size_mb:.1f} MB)")

    log.info("Done.")


def main():
    parser = argparse.ArgumentParser(description="Process an astrophotography session")
    parser.add_argument("session", type=Path, help="Path to session directory")
    parser.add_argument("--skip-preprocess", action="store_true",
                        help="Skip preprocessing (use existing result.fit)")
    parser.add_argument("--skip-postprocess", action="store_true",
                        help="Skip post-processing (only preprocess)")
    args = parser.parse_args()

    if not args.session.exists():
        log.error(f"Session path does not exist: {args.session}")
        sys.exit(1)

    process_session(args.session, args.skip_preprocess, args.skip_postprocess)


if __name__ == "__main__":
    main()
