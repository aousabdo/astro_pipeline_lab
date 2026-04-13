# Astro Pipeline Lab

Automated astrophotography processing pipeline built around [Siril](https://siril.org/), designed for Celestron Origin, C11, and Askar 103 data from Bortle 8 urban skies.

## What this is

A set of Siril scripts, a Python orchestrator, and a project structure for repeatable, high-quality deep-sky image processing. The pipeline handles everything from raw FITS calibration through stretching and export.

**Processing philosophy:** automation handles the tedious part (stacking, calibration, background extraction, multi-night integration). You handle the artistic part (stretching, color, saturation) in Siril's GUI.

The pipeline outputs a clean **linear master** FITS -- background-extracted, deconvolved, ready for you to stretch to taste.

## Quick start

```bash
# 1. Create sessions and link your FITS
./scripts/shell/new-session.sh nebulae M42_Orion 2026-02-12_origin_native
ln -s /path/to/your/fits/* projects/nebulae/M42_Orion/sessions/2026-02-12_origin_native/work/lights/

# 2. Preprocess all sessions for a target
python scripts/python/preprocess_all.py projects/nebulae/M42_Orion

# 3. Combine multiple sessions into one deep master
python scripts/python/preprocess_all.py projects/nebulae/M42_Orion --combine

# 4. Open the linear master in Siril GUI and stretch to taste
#    Output: projects/nebulae/M42_Orion/master/output/linear.fits
```

Or run Siril scripts directly:

```bash
# Preprocess a single session to linear master
siril-cli -s scripts/siril/preprocess_to_linear.ssf -d <session>/work

# Combine multiple session masters
# (place session1.fits, session2.fits, ... in the work dir)
siril-cli -s scripts/siril/combine_sessions.ssf -d <object>/master/work
```

For fully automated end-to-end processing (stretch included):

```bash
python scripts/python/process_session.py <session_path>
python scripts/python/process_session.py <session_path> --profile nebula_pro
```

## Siril scripts

### Preprocessing (automated -- produces linear masters)

| Script | Purpose |
|--------|---------|
| **`preprocess_to_linear.ssf`** | **Recommended.** Stack + bg extraction + deconvolution → linear master for manual stretching |
| `preprocess_lights_only.ssf` | Stack only (no bg extraction or deconvolution) |
| `preprocess_with_darks.ssf` | Stack with dark subtraction |
| `preprocess_full_cal.ssf` | Full calibration: darks + flats + bias |
| **`combine_sessions.ssf`** | Combine multiple session masters into one deep-integration linear master |

### Post-processing (automated stretch -- optional)

| Script | Purpose |
|--------|---------|
| `postprocess_galaxy.ssf` | Conservative galaxy processing |
| `postprocess_nebula.ssf` | Nebula with PCC (broadband/no-filter data) |
| `postprocess_nebula_filter.ssf` | Nebula without PCC (nebula/dual-band filters) |
| `postprocess_nebula_pro.ssf` | StarNet + per-channel GHS (best for bright nebulae like M42). Requires StarNet++ |
| `postprocess_cluster.ssf` | Star cluster processing |
| `quick_tiff.ssf` | Fast processing from Origin's stacked TIFF |

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
