from dataclasses import dataclass

import numpy as np
from scipy.ndimage import uniform_filter

from src.terrain.analysis.roughness import RoughnessProfile, rms_deviation_map, compute_roughness_profile
from src.terrain.config import (
    DEFAULT_BASELINES_METERS,
    ROUGHNESS_MAP_BASELINE_METERS,
    ROUGHNESS_MAP_WINDOW_METERS,
)


@dataclass(frozen=True)
class TerrainMetrics:
    slope_degrees: np.ndarray
    roughness_meters: np.ndarray


@dataclass(frozen=True)
class SiteAnalysis:
    name: str
    elevation_meters: np.ndarray
    metrics: TerrainMetrics
    roughness_profile: RoughnessProfile
    summary: dict


def fill_missing_with_mean(elevation_meters: np.ndarray) -> np.ndarray:
    """Replace NaNs by the mean so filters and gradients do not propagate NaN."""
    return np.where(
        np.isfinite(elevation_meters), elevation_meters, np.nanmean(elevation_meters)
    ).astype("float64")


def compute_terrain_metrics(
    elevation_meters: np.ndarray,
    pixel_size_meters: float,
) -> TerrainMetrics:
    """Slope (degrees) and roughness (local standard deviation, meters)."""
    missing_mask = ~np.isfinite(elevation_meters)
    filled_elevation = fill_missing_with_mean(elevation_meters)

    gradient_y, gradient_x = np.gradient(filled_elevation, pixel_size_meters)
    slope_degrees = np.degrees(np.arctan(np.hypot(gradient_x, gradient_y)))

    slope_degrees[missing_mask] = np.nan

    roughness_meters = rms_deviation_map(
        elevation_meters, 
        pixel_size_meters, 
        ROUGHNESS_MAP_BASELINE_METERS, 
        ROUGHNESS_MAP_WINDOW_METERS
    )
    return TerrainMetrics(slope_degrees, roughness_meters)


def summarize_terrain(elevation_meters, metrics, profile) -> dict:
    valid_mask = np.isfinite(elevation_meters)
    slopes = metrics.slope_degrees[valid_mask]
    elevations = elevation_meters[valid_mask]
    summary = {
        "slope_mean_degrees": slopes.mean(),
        "slope_median_degrees": np.median(slopes),
        "slope_p90_degrees": np.percentile(slopes, 90),
        "percent_slope_below_10": 100 * (slopes < 10).mean(),
        "percent_slope_above_20": 100 * (slopes > 20).mean(),
        "relief_meters": np.percentile(elevations, 99) - np.percentile(elevations, 1),
        "hurst_exponent": profile.hurst_exponent,
    }
    for baseline, value in zip(profile.baseline_meters, profile.rms_deviation_meters):
        summary[f"roughness_{baseline:.0f}m"] = value
    return summary


def analyze_site(
    name: str,
    elevation_meters: np.ndarray,
    pixel_size_meters: float,
) -> SiteAnalysis:
    metrics = compute_terrain_metrics(elevation_meters, pixel_size_meters)
    profile = compute_roughness_profile(
        elevation_meters, pixel_size_meters, DEFAULT_BASELINES_METERS
    )
    return SiteAnalysis(
        name, 
        elevation_meters, 
        metrics, 
        profile,
        summarize_terrain(elevation_meters, metrics, profile))
