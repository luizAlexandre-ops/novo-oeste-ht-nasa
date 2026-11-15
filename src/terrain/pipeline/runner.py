"""Reproducible lunar-to-Earth topographic analogue workflow."""
from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import label

from src.terrain.analysis.signature import build_signature
from src.terrain.comparison.comparison import (
    export_ranking_csv, rank_analogs, sensitivity_analysis,
)
from src.terrain.config import (
    DATA_DIRECTORY, DIVINER_CACHE_PATH, DIVINER_TABLE_PATH,
    OUTPUT_DIRECTORY,
)
from src.terrain.datasets.download import download_file, download_lunar_inputs
from src.terrain.locations import (
    EARTH_ANALOG_SITES, HAWORTH_CRATER, SHACKLETON_CRATER,
)
from src.terrain.site import build_earth_site, build_lunar_site
from src.terrain.visualisation.site_plot import plot_site


LUNAR_TARGETS = (SHACKLETON_CRATER, HAWORTH_CRATER)


def safe_name(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "_" for char in value).strip("_")


def inspect_quality(site) -> dict:
    """Report numerical and diagnostic checks; flags are not automatic exclusions."""
    elevation = site.analysis.elevation_meters
    slope = site.analysis.metrics.slope_degrees
    valid = np.isfinite(elevation)
    if not valid.any():
        raise ValueError(f"{site.name}: elevation contains no valid pixels")
    if abs(float(site.pixel_size_meters) - 120.0) > 1.0:
        raise ValueError(f"{site.name}: expected 120-m output pixels")
    if slope.shape != elevation.shape or not np.isfinite(slope[valid]).all():
        raise ValueError(f"{site.name}: invalid slope grid")
    profile = site.analysis.roughness_profile
    if not len(profile.baseline_meters) or not np.isfinite(profile.rms_deviation_meters).all():
        raise ValueError(f"{site.name}: invalid roughness profile")

    zeros = valid & (elevation == 0)
    regions, count = label(zeros)
    sizes = np.bincount(regions.ravel())[1:] if count else np.array([])
    median = float(np.median(elevation[valid]))
    missing_fraction = float((~valid).mean())
    zero_fraction = float(zeros.sum() / valid.sum())
    near_median_fraction = float((np.abs(elevation[valid] - median) < 1.0).mean())
    flags = []
    if missing_fraction > 0.01:
        flags.append("over_1_percent_missing_elevation")
    if zero_fraction > 0.01:
        flags.append("over_1_percent_exact_zero_elevation_check_surface_or_nodata")
    if near_median_fraction > 0.70:
        flags.append("over_70_percent_near_median_check_real_flatness_or_interpolation")
    return {
        "name": site.name, "pixel_size_m": float(site.pixel_size_meters),
        "shape": list(elevation.shape), "missing_fraction": missing_fraction,
        "zero_fraction": zero_fraction,
        "largest_zero_region_km2": float(sizes.max() * site.pixel_size_meters**2 / 1e6) if sizes.size else 0.0,
        "near_median_fraction": near_median_fraction, "flags": flags,
    }


def save_figure(site, folder: Path) -> None:
    figure = plot_site(site, save_path=folder / f"{safe_name(site.name)}.png", show=False)
    plt.close(figure)


def sensitivity_winners(rows: list[dict]) -> dict[str, str]:
    return {row["scenario"]: row["earth_site"] for row in rows if row["rank"] == 1}


def run_pipeline(
    *,
    output_directory: Path = OUTPUT_DIRECTORY,
    skip_download: bool = False,
    include_diviner: bool = False,
    generate_plots: bool = True,
    strict: bool = True,
) -> dict:
    """Fetch inputs, analyze all sites, validate, compare and export results.

    Optional Diviner source: set DIVINER_URL to a directly downloadable table URL,
    or put the table or cached .npz at the configured paths before running.
    """
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    figure_folder = output_directory / "figures"
    if generate_plots:
        figure_folder.mkdir(parents=True, exist_ok=True)

    if not skip_download:
        print("[1/5] Preparing lunar datasets (existing files are reused)...", flush=True)
        download_lunar_inputs()
    else:
        from src.terrain.config import AVGVISIB_PATH, LOLA_LABEL_PATH
        required = (LOLA_LABEL_PATH, LOLA_LABEL_PATH.with_suffix(".img"), AVGVISIB_PATH)
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise FileNotFoundError(f"Required local files missing: {missing}")

    if include_diviner and not (DIVINER_TABLE_PATH.is_file() or DIVINER_CACHE_PATH.is_file()):
        url = os.environ.get("DIVINER_URL", "").strip()
        if not url:
            raise FileNotFoundError(
                "Diviner requested but not installed. Place dlre_prp_south.tab in data/, "
                "or set DIVINER_URL to a direct download URL."
            )
        print("Downloading optional Diviner resource table...", flush=True)
        download_file(url, DIVINER_TABLE_PATH)

    # Never load an accidental local Diviner file when optional mode is disabled.
    # This is passed explicitly so that behavior is reproducible across machines.
    print("[2/5] Building lunar sites...", flush=True)
    lunar_sites = [build_lunar_site(target, include_diviner=include_diviner) for target in LUNAR_TARGETS]
    print("[3/5] Building Earth sites (Copernicus tiles may require network access)...", flush=True)
    earth_sites = []
    failures = {}
    for location in EARTH_ANALOG_SITES:
        try:
            site = build_earth_site(location)
            earth_sites.append(site)
            print(f"  {location.name}: OK", flush=True)
        except Exception as exc:
            if strict:
                raise RuntimeError(f"Earth site failed: {location.name}") from exc
            failures[location.name] = str(exc)
            print(f"  {location.name}: FAILED ({exc})", flush=True)
    if len(earth_sites) < 2:
        raise RuntimeError("At least two Earth candidates are required for a meaningful ranking.")

    print("[4/5] Validating and plotting...", flush=True)
    all_sites = lunar_sites + earth_sites
    quality = [inspect_quality(site) for site in all_sites]
    if generate_plots:
        for site in all_sites:
            save_figure(site, figure_folder)
    signatures = {site.name: build_signature(site) for site in all_sites}
    earth_signatures = [signatures[site.name] for site in earth_sites]
    without_haughton = [signature for signature in earth_signatures if signature.name != "Haughton Crater"]

    print("[5/5] Computing rankings, sensitivity and exclusion checks...", flush=True)
    target_results = {}
    for target in lunar_sites:
        lunar = signatures[target.name]
        stem = safe_name(target.name)
        ranking = rank_analogs(lunar, earth_signatures)
        sensitivity = sensitivity_analysis(lunar, earth_signatures)
        export_ranking_csv(ranking, output_directory / f"{stem}_ranking.csv")
        export_ranking_csv(sensitivity, output_directory / f"{stem}_sensitivity.csv")
        filtered = None
        filtered_sensitivity = None
        if len(without_haughton) >= 2 and len(without_haughton) < len(earth_signatures):
            filtered = rank_analogs(lunar, without_haughton)
            filtered_sensitivity = sensitivity_analysis(lunar, without_haughton)
            export_ranking_csv(filtered, output_directory / f"{stem}_ranking_without_haughton.csv")
            export_ranking_csv(filtered_sensitivity, output_directory / f"{stem}_sensitivity_without_haughton.csv")
        winners = sensitivity_winners(sensitivity)
        target_results[target.name] = {
            "winner": ranking[0]["earth_site"],
            "runner_up": ranking[1]["earth_site"],
            "ranking": ranking,
            "sensitivity_winners": winners,
            "win_counts": dict(Counter(winners.values())),
            "without_haughton_winner": filtered[0]["earth_site"] if filtered else None,
            "without_haughton_sensitivity_winners": (
                sensitivity_winners(filtered_sensitivity) if filtered_sensitivity else None
            ),
        }
        print(f"  {target.name}: {ranking[0]['earth_site']} (lowest composite distance)", flush=True)

    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "method": "slope Wasserstein + log RMS ratio + log relief ratio; per-target candidate min-max normalization",
        "caveats": [
            "Ranking only compares specified target-centred terrain windows and candidate sites.",
            "Normalized distances are not absolute similarity percentages.",
            "Illumination/Diviner are contextual lunar layers, not Earth similarity terms.",
            "Potential water/no-data and unusually flat terrain require independent source verification.",
        ],
        "earth_failures": failures,
        "quality": quality,
        "targets": target_results,
    }
    (output_directory / "pipeline_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8"
    )
    print(f"Results saved in: {output_directory}", flush=True)
    return summary
