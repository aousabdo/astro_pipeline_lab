#!/usr/bin/env python3
"""
Astro Pipeline Lab -- Batch Preprocessor

Preprocesses all sessions for a target and optionally combines
them into a single deep-integration linear master.

The output is a clean linear FITS ready for manual stretching
in Siril GUI. This script handles the tedious part (stacking,
registration, background extraction, deconvolution). You handle
the artistic part (stretching, color, saturation).

Usage:
    # Preprocess all sessions for a target
    python preprocess_all.py projects/nebulae/M42_Orion

    # Preprocess + combine into multi-session master
    python preprocess_all.py projects/nebulae/M42_Orion --combine

    # Only combine (sessions already preprocessed)
    python preprocess_all.py projects/nebulae/M42_Orion --combine-only

    # Preprocess a single session
    python preprocess_all.py projects/nebulae/M42_Orion --session 2026-02-12_origin_native

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("preprocess")

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "siril"


def run_siril(script: Path, workdir: Path, log_path: Path = None) -> bool:
    """Run a Siril script. Returns True on success."""
    (workdir / "process").mkdir(exist_ok=True)
    (workdir / "masters").mkdir(exist_ok=True)

    cmd = ["siril-cli", "-s", str(script), "-d", str(workdir)]
    log.info(f"  Running: {script.name} in {workdir.name}/")

    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    except FileNotFoundError:
        log.error("siril-cli not found on PATH")
        return False
    except subprocess.TimeoutExpired:
        log.error("Siril timed out after 1 hour")
        return False

    elapsed = time.time() - start

    if log_path:
        with open(log_path, "a") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Script: {script.name}\n")
            f.write(f"Workdir: {workdir}\n")
            f.write(f"Time: {datetime.now().isoformat()}\n")
            f.write(f"Duration: {elapsed:.1f}s\n")
            f.write(f"Exit: {result.returncode}\n")
            f.write(f"\n{result.stdout}\n")
            if result.stderr:
                f.write(f"\n--- STDERR ---\n{result.stderr}\n")

    if result.returncode != 0:
        log.error(f"  FAILED (exit {result.returncode}, {elapsed:.1f}s)")
        # Show the error
        for line in result.stdout.split("\n"):
            if "error" in line.lower() and "progress" not in line.lower():
                log.error(f"    {line.strip()}")
        return False

    log.info(f"  OK ({elapsed:.1f}s)")
    return True


def preprocess_session(session_path: Path) -> bool:
    """Preprocess a single session to a stacked linear master."""
    work = session_path / "work"
    lights = work / "lights"

    if not lights.exists() or not any(lights.iterdir()):
        log.warning(f"  No lights in {session_path.name}, skipping")
        return False

    frame_count = len(list(lights.glob("*.fits")))
    log.info(f"Session: {session_path.name} ({frame_count} frames)")

    output = session_path / "output"
    output.mkdir(exist_ok=True)
    logs = session_path / "logs"
    logs.mkdir(exist_ok=True)

    script = SCRIPTS_DIR / "preprocess_to_linear.ssf"
    success = run_siril(script, work, logs / "pipeline.log")

    # Clean intermediates to save disk space
    process_dir = work / "process"
    if process_dir.exists():
        shutil.rmtree(process_dir, ignore_errors=True)
        process_dir.mkdir()

    if success:
        result = work / "result.fits"
        linear = output / "linear.fits"
        if result.exists():
            log.info(f"  Stacked: {result.stat().st_size / 1024 / 1024:.0f} MB")
        if linear.exists():
            log.info(f"  Linear master: {linear.stat().st_size / 1024 / 1024:.0f} MB")

    return success


def combine_sessions(object_path: Path, session_names: list[str] = None) -> bool:
    """Combine per-session masters into one deep integration."""
    sessions_dir = object_path / "sessions"
    master_dir = object_path / "master"
    work = master_dir / "work"
    output = master_dir / "output"

    work.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)

    # Find sessions with stacked results
    if session_names:
        sessions = [sessions_dir / s for s in session_names]
    else:
        sessions = sorted(sessions_dir.iterdir())

    masters = []
    for s in sessions:
        result = s / "work" / "result.fits"
        if result.exists():
            masters.append((s.name, result))
        else:
            log.warning(f"  No result.fits for {s.name}, skipping")

    if len(masters) < 2:
        log.error(f"Need at least 2 session masters to combine, found {len(masters)}")
        return False

    log.info(f"Combining {len(masters)} sessions:")
    for name, path in masters:
        size = path.stat().st_size / 1024 / 1024
        log.info(f"  {name}: {size:.0f} MB")

    # Copy masters to work dir as session1, session2, ...
    # Also generate the combine script with the right number of platesolve blocks
    script_lines = [
        "requires 1.4.0",
        "set32bits",
        "setext fits",
        "",
    ]

    for i, (name, path) in enumerate(masters, 1):
        dest = work / f"session{i}.fits"
        shutil.copy2(path, dest)
        script_lines.extend([
            f"load session{i}",
            "platesolve -force -focal=335 -pixelsize=2.4",
            f"save session{i}",
            "close",
            "",
        ])

    script_lines.extend([
        "link session -out=.",
        "register session -2pass -interp=lanczos4",
        "seqapplyreg session -framing=min -interp=lanczos4",
        "stack r_session rej w 3 3 -norm=addscale -weight=noise -output_norm -32b -out=result",
        "",
        "load result",
        "mirrorx -bottomup",
        "save result",
        "",
        "# Post-stack linear processing",
        "subsky 4 -dither -samples=30 -tolerance=1.0",
        "platesolve -force -focal=335 -pixelsize=2.4",
        "makepsf blind -l0",
        "rl -alpha=5000 -iters=10 -tv",
        "save ../output/linear",
        "",
        "close",
    ])

    script_path = work / "combine_generated.ssf"
    script_path.write_text("\n".join(script_lines))

    log.info("Running combination...")
    success = run_siril(script_path, work, output / "combine.log")

    if success:
        linear = output / "linear.fits"
        if linear.exists():
            log.info(f"Combined linear master: {linear.stat().st_size / 1024 / 1024:.0f} MB")
            log.info(f"")
            log.info(f"Ready for manual processing:")
            log.info(f"  {linear}")
            log.info(f"")
            log.info(f"Open in Siril GUI and stretch to taste.")

    return success


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess astrophotography sessions to linear masters"
    )
    parser.add_argument("object", type=Path,
                        help="Path to object directory (e.g. projects/nebulae/M42_Orion)")
    parser.add_argument("--session", type=str,
                        help="Process only this session (name, not full path)")
    parser.add_argument("--combine", action="store_true",
                        help="After preprocessing, combine all sessions into one master")
    parser.add_argument("--combine-only", action="store_true",
                        help="Skip preprocessing, only combine existing session masters")
    args = parser.parse_args()

    obj = args.object.resolve()
    if not obj.exists():
        log.error(f"Object path does not exist: {obj}")
        sys.exit(1)

    sessions_dir = obj / "sessions"
    if not sessions_dir.exists():
        log.error(f"No sessions/ directory in {obj}")
        sys.exit(1)

    # Preprocess
    if not args.combine_only:
        if args.session:
            sessions = [sessions_dir / args.session]
        else:
            sessions = sorted(s for s in sessions_dir.iterdir() if s.is_dir())

        log.info(f"Preprocessing {len(sessions)} session(s) for {obj.name}")
        log.info("")

        results = {}
        for s in sessions:
            results[s.name] = preprocess_session(s)

        log.info("")
        log.info("=== Preprocessing Summary ===")
        for name, ok in results.items():
            log.info(f"  {name}: {'OK' if ok else 'FAILED'}")

        succeeded = sum(1 for ok in results.values() if ok)
        log.info(f"  {succeeded}/{len(results)} sessions succeeded")

    # Combine
    if args.combine or args.combine_only:
        log.info("")
        log.info("=== Combining Sessions ===")
        combine_sessions(obj)

    log.info("")
    log.info("Done.")


if __name__ == "__main__":
    main()
