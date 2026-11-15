from dataclasses import dataclass

import numpy as np
from scipy.ndimage import uniform_filter

from src.terrain.config import DEFAULT_BASELINES_METERS, MIN_RMS_METERS

@dataclass
class RoughnessProfile:
    """Terrain roughness profile."""

    baseline_meters: np.ndarray
    rms_deviation_meters: np.ndarray
    hurst_exponent: float

def baseline_to_lag(
        baseline_meters: float, 
        pixel_size_meters: float
    ) -> int:
    """Convert spatial baseline from metres to pixel displacement."""
    return int(round(baseline_meters / pixel_size_meters))

def _directional_differences(
        elevation_meters: np.ndarray, lag_pixels: int
        ) -> tuple[np.ndarray, np.ndarray]:
    """Calculate directional elevation differences at the given pixel lag."""
    difference_x = elevation_meters[:, lag_pixels:] - elevation_meters[:, :-lag_pixels]
    difference_y = elevation_meters[lag_pixels:, :] - elevation_meters[:-lag_pixels, :]
    return difference_x, difference_y

def rms_deviation(
        elevation_meters: np.ndarray,
        lag_pixels: int,
        detrend: bool = True,
    ) -> float:
    """RMS of elevation differences between points separated by `lag_pixels`.

    With detrending, subtract the mean difference in each direction to remove
    broad regional slope (an ideal inclined plane has near-zero roughness).
    """
    squared_sum, count = 0.0, 0
    for differences in _directional_differences(elevation_meters, lag_pixels):
        values = differences[np.isfinite(differences)]
        if values.size == 0:
            continue
        if detrend:
            values = values - values.mean()
        squared_sum += float(np.sum(values**2))
        count += values.size

    if count == 0:
        return float("nan")
    return float(np.sqrt(squared_sum / count))


def compute_roughness_profile(
        elevation_meters: np.ndarray,
        pixel_size_meters: float,
        baselines_meters: tuple[float, ...] = DEFAULT_BASELINES_METERS,
        detrend: bool = True,
    ) -> RoughnessProfile:
    """RMS deviation at several baselines and Hurst exponent (RMS ∝ L^H)."""
    max_lag = min(elevation_meters.shape) // 2

    used_baselines, used_values = [], []
    for baseline in baselines_meters:
        lag = baseline_to_lag(baseline, pixel_size_meters)
        if lag >= max_lag:
            continue
        value = rms_deviation(elevation_meters, lag, detrend=detrend)
        if np.isfinite(value) and value > 0:
            used_baselines.append(lag * pixel_size_meters)
            used_values.append(value)

    baselines = np.array(used_baselines)
    values = np.array(used_values)

    if len(baselines) >= 2:
        hurst = float(np.polyfit(np.log(baselines), np.log(values), 1)[0])
    else:
        hurst = float("nan")
    return RoughnessProfile(baselines, values, hurst)

def _masked_local_mean(
        values: np.ndarray, 
        valid: np.ndarray, 
        window_pixels: int):
    
    total = uniform_filter(
        np.where(valid, values, 0.0), 
        window_pixels
    )
    
    fraction_valid = uniform_filter(
        valid.astype("float64"), 
        window_pixels
    )

    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(fraction_valid > 0, total / fraction_valid, np.nan)

def rms_deviation_map(
        elevation_meters: np.ndarray,
        pixel_size_meters: float,
        baseline_meters: float,
        window_meters: float
) -> np.ndarray:
    """Local RMS deviation map (local mean slope removed).

    Within each window: difference variance = E[d²] - E[d]², where E[d] is
    the local mean directional difference. Combine both directions afterward.
    """
    lag = baseline_to_lag(baseline_meters, pixel_size_meters)
    window_pixels = max(3, int(round(window_meters / pixel_size_meters)) | 1)
    if window_pixels < lag:
        raise ValueError("Janela muito pequena para o tamanho do pixel.")

    differences_x, differences_y = _directional_differences(elevation_meters, lag)

    def to_full_grid(differences: np.ndarray, axis: int) -> np.ndarray:
        """Expand differences to the input shape, padding with NaN."""
        full = np.full(elevation_meters.shape, np.nan)
        if axis == 1:
            full[:, : differences.shape[1]] = differences
        else:
            full[: differences.shape[0], :] = differences
        return full

    variances = []
    for differences, axis in ((differences_x, 1), (differences_y, 0)):
        full = to_full_grid(differences, axis)
        valid = np.isfinite(full)
        mean_difference = _masked_local_mean(full, valid, window_pixels)
        mean_squared = _masked_local_mean(full**2, valid, window_pixels)
        variances.append(np.maximum(mean_squared - mean_difference**2, 0))
    
    roughness = np.sqrt(np.nanmean(np.stack(variances), axis = 0))
    roughness[~np.isfinite(elevation_meters)] = np.nan
    return roughness


def compute_local_roughness_profile(
    elevation_meters: np.ndarray,
    pixel_size_meters: float,
    baselines_meters: tuple[float, ...] = DEFAULT_BASELINES_METERS,
    window_factor: float = 4.0,
) -> RoughnessProfile:
    """Median of locally detrended RMS deviation for each baseline.
    The window scales with the baseline so it spans several point differences."""
    used_baselines, used_values = [], []
    for baseline in baselines_meters:
        lag = baseline_to_lag(baseline, pixel_size_meters)
        window_meters = window_factor * lag * pixel_size_meters
        if window_meters / pixel_size_meters > min(elevation_meters.shape) // 2:
            continue  # Window would exceed the available crop
        local_map = rms_deviation_map(
            elevation_meters, pixel_size_meters, baseline, window_meters
        )
        value = np.nanmedian(local_map)
        if np.isfinite(value) and value > MIN_RMS_METERS:
            used_baselines.append(lag * pixel_size_meters)
            used_values.append(value)

    baselines, values = np.array(used_baselines), np.array(used_values)
    hurst = (
        float(np.polyfit(np.log(baselines), np.log(values), 1)[0])
        if len(baselines) >= 2
        else float("nan")
    )
    return RoughnessProfile(baselines, values, hurst)