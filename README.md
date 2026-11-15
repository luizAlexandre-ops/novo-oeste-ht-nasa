# Lunar–Earth Terrain Analogue Analysis

Compare two lunar south-pole targets (Shackleton and Haworth) with six predefined terrestrial regions using 120 m terrain windows. The ranking uses a Wasserstein distance between slope distributions, RMS roughness profiles across shared baselines, and P99–P01 relief. Each component is min-max normalized **separately for each lunar target and set of Earth candidates**. Lower composite distances imply greater relative terrain similarity; they are **not** percentages of physical similarity.

## Quick start

Use Python 3.11+ from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m scripts.run_pipeline
```

On Linux/macOS use `source .venv/bin/activate`. **The first run needs internet** and downloads significant data (LOLA ~116 MB, plus illumination, and remote Copernicus tiles). A second run reuses the local LOLA/illumination files and cached 120 m Copernicus crops.

Useful options:

```powershell
python -m scripts.run_pipeline --skip-download   # use existing lunar files
python -m scripts.run_pipeline --no-plots        # faster, CSV and JSON only
python -m scripts.run_pipeline --skip-failed-sites # allow unavailable Earth sites
python -m scripts.run_pipeline --include-diviner  # optional thermal context
```

By default the run fails when an Earth candidate is unavailable, avoiding silently changing the candidate pool. Use `--skip-failed-sites` only when that is intentional. It still requires at least two Earth sites.

## Inputs and downloads

- LOLA LDEM: `data/ldem_75s_120m.lbl` and `data/ldem_75s_120m.img`, downloaded from NASA PDS Geosciences if absent.
- PGDA mean solar visibility: `data/AVGVISIB_85S_060M_201608.TIF`, downloaded if absent.
- Copernicus DSM: remotely streamed AWS public 30 m GeoTIFF tiles; each resulting 120 m site window is cached as `.npz` under `data/cache/copernicus/`.
- **Optional Diviner**: put `data/dlre_prp_south.tab` or `data/diviner_south_cache.npz` in place and run with `--include-diviner`. Alternatively set the `DIVINER_URL` environment variable to a verified direct download URL. The file is ~600 MB; no unverified default URL is assumed. The temperature layer is **not used in the ranking**.
- Permanent shadow is not separately downloaded in this project. Solar-visibility metrics do not substitute for an independent PSR dataset.

The downloader skips existing nonempty files and removes incomplete `.part` files after download failures. It does not verify scientific file checksums; provenance and completeness should be independently checked before publication.

## Outputs

`outputs/` contains:

- `shackleton_ranking.csv`, `haworth_ranking.csv`
- `*_sensitivity.csv` for seven weight scenarios
- `*_ranking_without_haughton.csv` and `*_sensitivity_without_haughton.csv` to test robustness to exclusion of the potentially water-covered Haughton crop
- `figures/*.png`: terrain elevation, slope, roughness and available illumination layers for every processed region
- `pipeline_summary.json`: rankings, winners, flags and data-quality summary

Scientific cautions: candidate coverage is regional, not a global search. Same output spacing (120 m) does not guarantee equal effective resolution between instruments. Zero elevation at Haughton and near-constant elevation at Atacama need source-level evaluation; the pipeline reports warnings without silently altering the data. The elevation references on Earth and the Moon differ, so only within-window relief is compared, not absolute elevation. Both Diviner and AVGVISIB are lunar context and never Earth similarity terms. This project does **not** establish landing safety or mission suitability.

## Organization

- `src/terrain/analysis/`: quantitative terrain calculations and signatures.
- `src/terrain/comparison/`: distances, ranking and weight sensitivity.
- `src/terrain/datasets/`: rasters, downloader, Copernicus, Diviner and LOLA.
- `src/terrain/pipeline/`: supported reproducible workflow.
- `src/terrain/visualisation/`: reusable plots.
- `scripts/run_pipeline.py`: supported command-line entrypoint.
- `experiments/legacy/`: early investigation scripts preserved for future work; **not part of the delivery workflow**.
- `experiments/diagnostics/`: manual validation and exploratory ranking; these files may require local data and their historical assumptions.
- `requirements-legacy.txt`: optional older PostgreSQL integration dependencies.

Run tests with `python -m pytest -q` after installing `pytest`.