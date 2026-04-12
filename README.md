# Astro Pipeline Lab

Automated astrophotography processing pipeline built around [Siril](https://siril.org/), designed for Celestron Origin, C11, and Askar 103 data from Bortle 8 urban skies.

## What this is

A set of Siril scripts, a Python orchestrator, and a project structure for repeatable, high-quality deep-sky image processing. The pipeline handles everything from raw FITS calibration through stretching and export.

**Processing philosophy:** three phases, always in order:
1. **Linear domain** (physics) -- calibrate, stack, extract background, color calibrate, deconvolve
2. **Nonlinear domain** (aesthetics) -- stretch with GHS
3. **Finishing** (enhancement) -- denoise, sharpen, saturation

## Quick start

```bash
# 1. Create a new session
./scripts/shell/new-session.sh galaxies M51_Whirlpool 2026-04-12_origin_native

# 2. Put your raw FITS in the session
ln -s /path/to/your/fits/* projects/galaxies/M51_Whirlpool/sessions/2026-04-12_origin_native/work/lights/

# 3. Edit the manifest
vim projects/galaxies/M51_Whirlpool/sessions/2026-04-12_origin_native/manifest.yml

# 4. Run the pipeline
python scripts/python/process_session.py projects/galaxies/M51_Whirlpool/sessions/2026-04-12_origin_native
```

Or run Siril scripts directly:

```bash
# Preprocess (stack raw frames)
siril-cli -s scripts/siril/preprocess_lights_only.ssf -d /path/to/session/work

# Post-process (background extraction, color cal, stretch, export)
siril-cli -s scripts/siril/postprocess_galaxy.ssf -d /path/to/session/work
```

## Siril scripts

| Script | Purpose |
|--------|---------|
| `preprocess_lights_only.ssf` | Stack light frames with no calibration (typical Origin workflow) |
| `preprocess_with_darks.ssf` | Stack with dark subtraction |
| `preprocess_full_cal.ssf` | Full calibration: darks + flats + bias |
| `postprocess_galaxy.ssf` | Conservative galaxy processing (faint halos, natural look) |
| `postprocess_nebula.ssf` | Balanced nebula processing with PCC (broadband/no-filter data) |
| `postprocess_nebula_filter.ssf` | Nebula processing without PCC (for nebula/dual-band/UHC filters -- preserves Ha reds) |
| `postprocess_nebula_pro.ssf` | **Best quality.** StarNet star separation + per-channel GHS + screen-blend recomposition. Requires StarNet++ |
| `postprocess_cluster.ssf` | Clean star cluster processing (minimal, sharp stars) |
| `quick_tiff.ssf` | Fast processing from Origin's stacked TIFF (~90% quality, ~30% effort) |

## Processing profiles

Defined in `scripts/config/profiles.yml`:

- **galaxy_conservative** -- low aggression everywhere, protect faint structure
- **nebula_balanced** -- stronger stretch and saturation, optional VeraLux
- **cluster_clean** -- minimal processing, preserve star colors
- **comet_soft** -- gentle stretch, preserve tail structure
- **fast_tiff** -- quick results from pre-stacked data

## Project structure

```
astro_pipeline_lab/
├── raw/                     # original FITS by instrument/target/date
├── calibration/             # reusable darks/flats/bias libraries
├── projects/                # by category, then target
│   └── galaxies/
│       └── M51_Whirlpool/
│           ├── object_profile.yml
│           ├── sessions/
│           │   └── 2026-04-12_origin_native/
│           │       ├── manifest.yml
│           │       ├── raw/     # symlinks to central raw
│           │       ├── work/    # siril workspace
│           │       ├── output/  # results
│           │       └── logs/
│           ├── master/          # multi-night combined work
│           └── exports/         # final deliverables
├── scripts/
│   ├── siril/               # .ssf processing scripts
│   ├── python/              # orchestrator
│   ├── config/              # profiles, vocabulary
│   ├── templates/           # manifest/profile templates
│   └── shell/               # helper scripts
└── reference/               # docs, presets
```

## Requirements

- [Siril](https://siril.org/) >= 1.4.0 (with `siril-cli` on PATH)
- Python >= 3.10
- PyYAML (`pip install pyyaml`)
- Optional: [StarNet++](https://www.starnetastro.com/) for star removal
- Optional: [SetiAstro Cosmic Clarity](https://www.yoursite.com) for AI denoise/sharpen

## Equipment

- **Celestron Origin** -- 6" Rasa f/2.2, integrated OSC camera (Bayer BGGR)
- **Celestron C11** -- with HyperStar or 0.7x reducer
- **Askar 103** -- native configuration
- **Location:** Falls Church, VA (Bortle 8)

## Roadmap

- [x] Directory structure and metadata standards
- [x] Siril preprocessing scripts (3 calibration variants)
- [x] Siril post-processing scripts (galaxy, nebula, cluster, quick)
- [x] Python session orchestrator
- [ ] Multi-night session combination workflow
- [ ] Automated frame quality scoring (FWHM, eccentricity)
- [ ] SetiAstro Cosmic Clarity integration
- [ ] Adaptive parameter tuning per target

## License

MIT
