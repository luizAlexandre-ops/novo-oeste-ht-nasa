from dataclasses import dataclass

import numpy as np
from scipy.ndimage import label
from scipy.stats import wasserstein_distance

from src.terrain.config import (
    LANDABLE_LIT_THRESHOLD_PERCENT,
    LANDING_SLOPE_LIMITS_DEGREES,
    LIT_THRESHOLDS_PERCENT,
    SLOPE_HISTOGRAM_BINS,
    SUNLIT_MAX_PSR_FRACTION,
)
from src.terrain.site import Site


@dataclass(frozen=True)
class SiteSignature:
    name: str
    scalars: dict[str, float]
    slope_histogram: np.ndarray          # Normalized histogram for Wasserstein
    roughness_baselines_m: np.ndarray
    roughness_rms_m: np.ndarray


def largest_region_km2(mask: np.ndarray, pixel_size_m: float) -> float:
    """Area of the largest 4-connected True region, in square kilometres."""
    labeled, count = label(mask)
    if count == 0:
        return 0.0
    sizes = np.bincount(labeled.ravel())[1:]
    return float(sizes.max() * pixel_size_m**2 / 1e6)


def build_signature(site: Site) -> SiteSignature:
    analysis = site.analysis
    slope = analysis.metrics.slope_degrees
    valid = np.isfinite(slope)
    slopes = slope[valid]
    low, high = LANDING_SLOPE_LIMITS_DEGREES

    scalars = {
        "slope_p50": np.percentile(slopes, 50),
        "slope_p90": np.percentile(slopes, 90),
        "slope_p99": np.percentile(slopes, 99),
        f"landable_fraction_{low:.0f}": (slopes < low).mean(),
        f"landable_fraction_{high:.0f}": (slopes < high).mean(),
        f"largest_landable_km2_{high:.0f}": largest_region_km2(
            valid & (slope < high), site.pixel_size_meters
        ),
        "relief_m": analysis.summary["relief_meters"],
        "hurst": analysis.roughness_profile.hurst_exponent,
    }

    # Only lunar sites provide illumination; Earth arrays are entirely NaN.
    illumination = site.illumination_percent
    lit_valid = np.isfinite(illumination)
    if lit_valid.any():
        psr = site.layers.get("psr_fraction")
        outside_psr = lit_valid if psr is None else lit_valid & (psr < SUNLIT_MAX_PSR_FRACTION)
        if psr is not None:
            scalars["psr_fraction"] = float(np.nanmean(psr))
        if outside_psr.any():
            values = illumination[outside_psr]
            scalars["lit_mean_outside_psr"] = values.mean()
            scalars["lit_p90_outside_psr"] = np.percentile(values, 90)
            scalars["lit_p99_outside_psr"] = np.percentile(values, 99)
            for threshold in LIT_THRESHOLDS_PERCENT:
                scalars[f"lit_fraction_{threshold:.0f}"] = (values >= threshold).mean()
            scalars["largest_landable_lit_km2"] = largest_region_km2(
                outside_psr & valid & (slope < high) & (illumination >= LANDABLE_LIT_THRESHOLD_PERCENT),
                site.pixel_size_meters,
            )

    # Clip extreme slopes into the final histogram bin.
    histogram, _ = np.histogram(
        np.clip(slopes, 0, SLOPE_HISTOGRAM_BINS[-1]), bins=SLOPE_HISTOGRAM_BINS
    )
    profile = analysis.roughness_profile
    return SiteSignature(
        site.name,
        {key: float(value) for key, value in scalars.items()},
        histogram / histogram.sum(),
        profile.baseline_meters,
        profile.rms_deviation_meters,
    )


def slope_distance(a: SiteSignature, b: SiteSignature) -> float:
    """Wasserstein distance between slope distributions, in degrees."""
    centers = 0.5 * (SLOPE_HISTOGRAM_BINS[:-1] + SLOPE_HISTOGRAM_BINS[1:])
    return float(wasserstein_distance(centers, centers, a.slope_histogram, b.slope_histogram))