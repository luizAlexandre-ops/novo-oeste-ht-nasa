from dataclasses import dataclass

import numpy as np
from scipy.ndimage import uniform_filter

from src.terrain.config import DEFAULT_ROUGHNESS_WINDOW_METERS


@dataclass(frozen=True)
class TerrainMetrics:
    slope_degrees: np.ndarray
    roughness_meters: np.ndarray


@dataclass(frozen=True)
class SiteAnalysis:
    name: str
    elevation_meters: np.ndarray
    metrics: TerrainMetrics
    summary: dict


def fill_missing_with_mean(elevation_meters: np.ndarray) -> np.ndarray:
    """Replace NaNs by the mean so filters and gradients do not propagate NaN."""
    return np.where(
        np.isfinite(elevation_meters), elevation_meters, np.nanmean(elevation_meters)
    ).astype("float64")


def compute_terrain_metrics(
    elevation_meters: np.ndarray,
    pixel_size_meters: float,
    roughness_window_meters: float = DEFAULT_ROUGHNESS_WINDOW_METERS,
) -> TerrainMetrics:
    """Slope (degrees) and roughness (local standard deviation, meters)."""
    missing_mask = ~np.isfinite(elevation_meters)
    filled_elevation = fill_missing_with_mean(elevation_meters)

    gradient_y, gradient_x = np.gradient(filled_elevation, pixel_size_meters)
    slope_degrees = np.degrees(np.arctan(np.hypot(gradient_x, gradient_y)))

    window_pixels = max(3, int(round(roughness_window_meters / pixel_size_meters)) | 1)
    local_mean = uniform_filter(filled_elevation, window_pixels)
    local_mean_of_squares = uniform_filter(filled_elevation**2, window_pixels)
    roughness_meters = np.sqrt(np.maximum(local_mean_of_squares - local_mean**2, 0))

    slope_degrees[missing_mask] = np.nan
    roughness_meters[missing_mask] = np.nan
    return TerrainMetrics(slope_degrees, roughness_meters)


def summarize_terrain(elevation_meters: np.ndarray, metrics: TerrainMetrics) -> dict:
    valid_mask = np.isfinite(elevation_meters)
    slopes = metrics.slope_degrees[valid_mask]
    roughness = metrics.roughness_meters[valid_mask]
    elevations = elevation_meters[valid_mask]
    return {
        "slope_mean_degrees": slopes.mean(),
        "slope_median_degrees": np.median(slopes),
        "slope_p90_degrees": np.percentile(slopes, 90),
        "percent_slope_below_10": 100 * (slopes < 10).mean(),
        "percent_slope_above_20": 100 * (slopes > 20).mean(),
        "roughness_median_meters": np.median(roughness),
        "relief_meters": np.percentile(elevations, 99) - np.percentile(elevations, 1),
    }


def analyze_site(
    name: str,
    elevation_meters: np.ndarray,
    pixel_size_meters: float,
    roughness_window_meters: float = DEFAULT_ROUGHNESS_WINDOW_METERS,
) -> SiteAnalysis:
    metrics = compute_terrain_metrics(elevation_meters, pixel_size_meters, roughness_window_meters)
    return SiteAnalysis(name, elevation_meters, metrics, summarize_terrain(elevation_meters, metrics))
