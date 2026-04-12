# Astro Pipeline Lab -- Master Plan

## Philosophy

Three processing phases, always in this order:

1. **Linear domain (physics)** -- calibrate, stack, extract background, color calibrate, deconvolve
2. **Nonlinear domain (aesthetics)** -- stretch, contrast shaping
3. **Finishing (enhancement)** -- denoise, sharpen, star control

Most people mix these. That's where quality collapses.

**Siril is the backbone.** SetiAstro and VeraLux are optional finishing plugins, not foundations. PixInsight is deferred until you hit a real ceiling, not because of hype.

---

## 1. Directory Structure

Start lean. Grow when real pain demands it.

```
astro-pipeline-lab/
├── README.md
├── raw/                          # original FITS, never modified
│   ├── origin/
│   │   ├── M51_Whirlpool/
│   │   │   ├── 2026-04-12/      # one dir per night
│   │   │   └── 2026-04-14/
│   │   └── M42_Orion/
│   ├── c11/
│   └── askar103/
│
├── calibration/                  # reusable calibration libraries
│   ├── origin/
│   │   ├── darks/
│   │   ├── flats/
│   │   └── bias/
│   ├── c11/
│   └── askar103/
│
├── projects/                     # organized by category then target
│   ├── galaxies/
│   │   └── M51_Whirlpool/       # see "Object folder layout" below
│   ├── nebulae/
│   ├── clusters/
│   ├── comets/
│   └── widefield/
│
├── scripts/                      # all automation lives here
│   ├── siril/                    # .ssf scripts
│   ├── python/                   # orchestrator, utilities
│   ├── config/                   # processing profiles
│   └── templates/                # session/object template generators
│
└── reference/                    # docs, presets, comparisons
```

**Why no numbered prefixes:** `01_raw_data` looks tidy but adds friction when typing paths and `cd`-ing around. Plain names sort fine and are faster to work with.

**Why no inbox/archive/exports at top level:** These emerge when you need them. Don't pre-create empties.

---

## 2. Object Folder Layout

Each target is a self-contained project that absorbs multiple nights.

```
M51_Whirlpool/
├── README.md                     # target overview, current status, best output
├── object_profile.yml            # target metadata and processing defaults
├── sessions/
│   ├── 2026-04-12_origin_native/ # see "Session folder" below
│   └── 2026-04-14_origin_native/
├── master/                       # multi-night integration work
│   ├── M51_combined_linear_v1.fit
│   ├── M51_final_v1.tif
│   └── integration_v1.yml        # which sessions, why, how
├── exports/                      # final deliverables (tif, jpg, png)
└── notes.md                      # processing journal, lessons learned
```

### Object profile (object_profile.yml)

Keep it minimal. Add fields when your scripts need them.

```yaml
object: M51_Whirlpool
category: galaxy
catalog_ids: [M51, NGC5194]
framing: full galaxy with companion
processing_profile: galaxy_conservative
notes: Favor faint outer halo over aggressive core contrast
```

### Integration plan (master/integration_v1.yml)

Created when you combine multiple nights.

```yaml
version: 1
object: M51_Whirlpool
sessions:
  - 2026-04-12_origin_native
  - 2026-04-14_origin_native
excluded:
  - session: 2026-04-20_c11_reducer
    reason: gradient mismatch, different image scale
reference_session: 2026-04-12_origin_native
stretch: siril_ghs
finishing:
  denoise: light     # or off
  sharpen: off
  veralux: off
output: M51_combined_linear_v1.fit
```

---

## 3. Session Folder Layout

One folder per imaging night per target. Start lean.

```
2026-04-12_origin_native/
├── manifest.yml          # session metadata (see below)
├── raw/                  # symlinks to raw/<instrument>/<target>/<date>/
├── work/                 # siril workspace (process, seq files, temp)
├── output/               # linear master, stretched, quick exports
├── logs/                 # siril.log, pipeline.log
└── notes.md              # what happened, conditions, decisions
```

Add `qc/` and `finishing/` subdirs only when you actually use them.

### Session manifest (manifest.yml)

```yaml
session: 2026-04-12_origin_native
object: M51_Whirlpool
category: galaxy
date: 2026-04-12

acquisition:
  instrument: origin
  config: native
  filter: none
  exposure_s: 10
  frames: 360
  total_integration_s: 3600

calibration:
  darks: true
  flats: false
  bias: false
  notes: No flats available

conditions:
  bortle: 8
  location: Falls Church VA
  moon: null
  seeing: unknown
  transparency: fair
  notes: Mild urban gradient

quality:
  tracking: good
  focus: good
  gradients: moderate

status:
  stacked: false
  qc_reviewed: false
  in_master: false

notes:
  - First M51 Origin session
```

### Session naming convention

```
YYYY-MM-DD_instrument_config
```

Examples:
- `2026-04-12_origin_native`
- `2026-04-20_c11_reducer`
- `2026-04-28_c11_hyperstar`
- `2026-05-02_askar103_native`

### Object naming convention

```
CATALOGID_CommonName
```

Examples: `M51_Whirlpool`, `M42_Orion`, `NGC7000_North_America`, `IC434_Horsehead`

No spaces. Underscores only.

---

## 4. Controlled Vocabulary

Scripts break when naming drifts. Use only these values.

| Field | Allowed values |
|-------|---------------|
| category | `galaxy`, `nebula`, `cluster`, `comet`, `widefield`, `moon_planet` |
| instrument | `origin`, `c11`, `askar103` |
| config | `native`, `reducer`, `hyperstar`, `flattener`, `barlow` |
| quality | `excellent`, `good`, `acceptable`, `poor`, `unknown` |
| transparency/seeing | `excellent`, `good`, `fair`, `poor`, `unknown` |
| boolean fields | `true`, `false` (not yes/no) |
| unknown values | `null` (not "n/a" or "unknown-ish") |

---

## 5. Processing Profiles

Stored in `scripts/config/profiles.yml`. Referenced by object profiles and integration plans.

```yaml
galaxy_conservative:
  gradient_removal: careful
  deconvolution: mild
  stretch: controlled         # siril GHS, protect highlights
  saturation: low
  denoise: off
  sharpen: off
  veralux: off

nebula_balanced:
  gradient_removal: moderate
  deconvolution: mild
  stretch: stronger           # more midtone boost OK
  saturation: medium
  denoise: light
  sharpen: light
  veralux: optional

cluster_clean:
  gradient_removal: light
  deconvolution: off
  stretch: moderate
  saturation: low
  denoise: light
  sharpen: light
  veralux: off

comet_soft:
  gradient_removal: careful
  deconvolution: off
  stretch: gentle
  saturation: low
  denoise: minimal
  sharpen: off
  veralux: off
```

---

## 6. Workflows by Object Type

### Galaxies (hardest, most important)

**Goal:** preserve faint outer halo, natural star field, no plastic look.

**Siril workflow:**
1. Convert/debayer raw FITS (Origin = Bayer BGGR)
2. Register
3. Stack (average + rejection)
4. Crop edges
5. Background extraction (careful, sparse sampling)
6. SPCC or PCC color calibration
7. Mild deconvolution (PSF-based, restrained)
8. GHS stretch (VERY controlled, slow reveal of faint halo)
9. Light saturation adjustment
10. Optional green noise removal (rarely needed after good cal)

**SetiAstro (optional, after stretch):** light denoise only. Very light sharpen if any. Destroys dust lanes if overused.

**VeraLux:** generally avoid for galaxies. Can over-crunch cores.

**Aggressiveness: LOW across the board.**

### Emission Nebulae (Orion, Rosette, etc.)

**Goal:** maximize contrast, preserve color richness.

**Siril workflow:**
1-4. Same as galaxies
5. Background extraction (more aggressive OK)
6. SPCC/PCC
7. Optional deconvolution
8. GHS or arcsinh stretch (boost midtones more aggressively)
9. Increase saturation
10. Optional star reduction

**SetiAstro:** more useful here. Moderate denoise + sharpen OK. Halo reduction if needed.

**VeraLux:** this is where it shines. Can replace stretch step entirely. Good nebula contrast.

**Aggressiveness: MEDIUM-HIGH.**

### Star Clusters (globular/open)

**Goal:** clean stars, no bloating, sharp but natural.

**Siril workflow:**
1-4. Same
5. Minimal background extraction
6. PCC/SPCC
7. Moderate stretch (don't push too far)
8. Slight sharpening, optional star tightening

**SetiAstro:** mild denoise + sharpen only.
**VeraLux:** usually not needed, can make stars look artificial.
**Aggressiveness: LOW-MODERATE.**

### Comets (special case)

**Goal:** preserve tail, avoid smearing nucleus.

**Siril workflow:**
1. Stack twice: stars aligned AND comet aligned
2. Combine carefully
3. Gentle stretch
4. Tail enhancement
5. Minimal denoise

**SetiAstro/VeraLux:** use VERY carefully. Easy to destroy tail structure.

### Fast Workflow (Origin stacked TIFF)

For quick same-night results:
1. Load TIFF in Siril
2. Crop
3. Background extraction
4. Quick PCC
5. GHS stretch
6. Light SetiAstro denoise
7. Export

~90% quality for ~30% effort.

---

## 7. Automation Architecture

### Layer 1: Siril scripts (.ssf)

One script per workflow variant. Run headless:
```bash
siril -s galaxy_conservative.ssf -d /path/to/session/work
```

Siril supports:
- Full script execution (`.ssf` files)
- Named pipe / programmatic control
- Batch pipelines across sessions

### Layer 2: Python orchestrator

```
raw FITS (Origin)
    |
    v
Python orchestrator
    |
    v
Siril CLI (stack + preprocess)
    |
    v
Optional finishing (SetiAstro CLI)
    |
    v
Post-processing (Python/OpenCV if needed)
    |
    v
Output (TIFF master + JPG web + archive)
```

What the orchestrator does:
- Auto-group lights by target, exposure, filter
- Detect bad frames (FWHM, eccentricity, sky brightness)
- Run Siril scripts per session
- Select processing profile based on object category
- Organize outputs into the standard folder structure
- Update manifest status fields
- Log everything

### Layer 3: Future (build when needed)

- AI-driven frame rejection
- Adaptive parameter tuning per target type
- Cross-session quality comparison
- Automated integration planning

---

## 8. Phased Execution Plan

### Phase 1 -- First image (this week)

- [x] Create the lean directory structure
- [x] Write Siril preprocessing scripts (3 calibration variants)
- [x] Write Siril post-processing scripts (galaxy, nebula, cluster, quick TIFF)
- [x] Write Python session orchestrator
- [x] Write session/object/integration metadata templates
- [x] Write new-session helper script
- [ ] Copy raw Origin FITS into first session
- [ ] Run `preprocess_lights_only.ssf` on first M51 dataset
- [ ] Run `postprocess_galaxy.ssf` on the stacked result
- [ ] Compare headless output vs manual Siril UI processing
- [ ] Tune GHS stretch parameters based on actual M51 data

### Phase 2 -- Validate and tune (next week)

- [ ] Process a second M51 night
- [ ] Run the Python orchestrator end-to-end
- [ ] Test the quick_tiff.ssf workflow on Origin stacked TIFF
- [ ] Tune SPCC sensor settings for Origin's IMX sensor
- [ ] Adjust background extraction parameters for Bortle 8 data
- [ ] Document what worked and what needed manual override

### Phase 3 -- Multi-night integration (week 3)

- [ ] Write the session combination workflow in Siril
- [ ] Build the integration plan YAML for M51
- [ ] Process combined M51 master from multiple nights
- [ ] Refine folder structure based on what was actually needed

### Phase 4 -- Expand and refine (ongoing)

- [ ] Test nebula workflow on emission nebula data
- [ ] Add SetiAstro Cosmic Clarity finishing step to orchestrator
- [ ] Build QC infrastructure (FWHM stats, frame rejection)
- [ ] Add more targets, validate the structure scales
- [ ] Add metadata fields as scripts demand them

---

## 9. Key Principles

1. **Process an image before perfecting the filing system.** Structure serves the work, not the other way around.
2. **YAGNI.** Don't create folders, metadata fields, or scripts for workflows you haven't done yet.
3. **One notes file per session.** Not three.
4. **Symlink raw data, don't copy.** Central raw store, project sessions reference it.
5. **Version outputs, not folders.** `M51_final_v1.tif`, `v2`, `v3`. Never `final_final`.
6. **Controlled vocabulary from day one.** This is the one thing worth being strict about early.
7. **Siril GHS over VeraLux for galaxies.** More control, less "smart-scope look."
8. **SetiAstro is a scalpel, not a foundation.** Apply after stretch, lightly, conditionally.
9. **Log everything.** When batch runs start, logs are the only way to debug.
10. **Schema grows with the code.** Add manifest fields when a script needs them, not before.

---

## 10. Bootstrap Commands

Create the initial structure:

```bash
cd ~/work/astro_pipeline_lab

# Top level
mkdir -p raw/{origin,c11,askar103}
mkdir -p calibration/{origin,c11,askar103}
mkdir -p projects/{galaxies,nebulae,clusters,comets,widefield}
mkdir -p scripts/{siril,python,config,templates}
mkdir -p reference

# First target
mkdir -p projects/galaxies/M51_Whirlpool/{sessions,master,exports}

# First session
mkdir -p projects/galaxies/M51_Whirlpool/sessions/2026-04-12_origin_native/{raw,work,output,logs}
```

Then start writing Siril scripts or run the orchestrator:

```bash
# Run the full pipeline on a session
python scripts/python/process_session.py projects/galaxies/M51_Whirlpool/sessions/2026-04-12_origin_native

# Or run Siril scripts directly
siril-cli -s scripts/siril/preprocess_lights_only.ssf -d /path/to/session/work
siril-cli -s scripts/siril/postprocess_galaxy.ssf -d /path/to/session/work
```

---

## 11. Script Reference

### Preprocessing scripts

| Script | Calibration | Use when |
|--------|------------|----------|
| `preprocess_lights_only.ssf` | None | Origin with internal calibration (most common) |
| `preprocess_with_darks.ssf` | Darks only | Origin or C11 with separate darks |
| `preprocess_full_cal.ssf` | Darks + flats + bias | C11, Askar 103 with full calibration library |

### Post-processing scripts

| Script | Profile | Aggressiveness | Best for |
|--------|---------|---------------|----------|
| `postprocess_galaxy.ssf` | Conservative | Low | M51, M31, NGC galaxies |
| `postprocess_nebula.ssf` | Balanced | Medium-high | M42, Rosette, North America |
| `postprocess_cluster.ssf` | Clean | Low-moderate | M13, M3, open clusters |
| `quick_tiff.ssf` | Fast | Moderate | Same-night quick results from Origin TIFF |

### Python orchestrator

```bash
# Full pipeline (auto-detects calibration type + processing profile)
python scripts/python/process_session.py <session_path>

# Skip preprocessing (use existing stacked result.fit)
python scripts/python/process_session.py <session_path> --skip-preprocess

# Only preprocess (no stretching/export)
python scripts/python/process_session.py <session_path> --skip-postprocess
```

### Helper scripts

```bash
# Create a new session with standard folder structure
./scripts/shell/new-session.sh <category> <object_name> <session_id>
```
