import csv
from pathlib import Path

import numpy as np

from src.terrain.analysis.signature import SiteSignature, slope_distance

def roughness_distance(a: SiteSignature, b: SiteSignature) -> float:
    """
    Compare RMS terrain roughness at shared spatial baselines.

    Use logarithmic differences to compare ratios,
    rather than absolute differences.
    """
    shared_baselines = np.intersect1d(
        a.roughness_baselines_m,
        b.roughness_baselines_m,
    )

    if len(shared_baselines) == 0:
        raise ValueError("The signatures have no common roughness baselines.")

    distances = []

    for baseline in shared_baselines:
        index_a = np.where(a.roughness_baselines_m == baseline)[0][0]
        index_b = np.where(b.roughness_baselines_m == baseline)[0][0]

        rms_a = a.roughness_rms_m[index_a]
        rms_b = b.roughness_rms_m[index_b]

        if not np.isfinite(rms_a) or not np.isfinite(rms_b):
            continue

        epsilon = 1e-6

        distances.append(
            abs(np.log((rms_a + epsilon) / (rms_b + epsilon)))
        )

    if not distances:
        raise ValueError("There are no valid RMS values for comparison.")

    return float(np.mean(distances))


def relief_distance(a: SiteSignature, b: SiteSignature) -> float:
    """
    Compare relative site relief using P99 minus P1.

    The logarithmic difference prevents relief magnitude
    from directly dominating the other metrics.
    """
    relief_a = a.scalars["relief_m"]
    relief_b = b.scalars["relief_m"]

    epsilon = 1e-6

    return float(
        abs(np.log((relief_a + epsilon) / (relief_b + epsilon)))
    )


def compare_signatures(
    lunar: SiteSignature,
    earth: SiteSignature,
) -> dict:
    """Calculate component distances between a lunar and an Earth site."""

    return {
        "lunar_target": lunar.name,
        "earth_site": earth.name,
        "slope_distance": slope_distance(lunar, earth),
        "roughness_distance": roughness_distance(lunar, earth),
        "relief_distance": relief_distance(lunar, earth),
    }


def normalize_distances(values: np.ndarray) -> np.ndarray:
    """
    Normalize distances to the range [0, 1].

    The smallest distance maps to 0 and the largest maps to 1.
    """
    minimum = np.min(values)
    maximum = np.max(values)

    if np.isclose(maximum, minimum):
        return np.zeros_like(values, dtype=float)

    return (values - minimum) / (maximum - minimum)


def rank_analogs(
    lunar: SiteSignature,
    earth_sites: list[SiteSignature],
    weights: dict[str, float] | None = None,
) -> list[dict]:
    """
    Compare a lunar target against multiple Earth sites
    and return Earth candidates ordered by increasing distance.
    """
    if not earth_sites:
        return []

    if weights is None:
        weights = {
            "slope_distance": 1 / 3,
            "roughness_distance": 1 / 3,
            "relief_distance": 1 / 3,
        }

    expected_metrics = {
        "slope_distance",
        "roughness_distance",
        "relief_distance",
    }

    if set(weights) != expected_metrics:
        raise ValueError(f"Weights must contain exactly: {expected_metrics}")

    if any(weight < 0 for weight in weights.values()):
        raise ValueError("Weights must be non-negative.")

    total_weight = sum(weights.values())

    if total_weight <= 0:
        raise ValueError("The weight sum must be positive.")

    weights = {
        key: value / total_weight
        for key, value in weights.items()
    }

    comparisons = [
        compare_signatures(lunar, earth)
        for earth in earth_sites
    ]

    for metric in expected_metrics:
        values = np.array([
            comparison[metric]
            for comparison in comparisons
        ])

        normalized = normalize_distances(values)

        for comparison, value in zip(comparisons, normalized):
            comparison[f"{metric}_normalized"] = float(value)

    # Compute the weighted composite distance
    for comparison in comparisons:
        comparison["weight_slope"] = weights["slope_distance"]
        comparison["weight_roughness"] = weights["roughness_distance"]
        comparison["weight_relief"] = weights["relief_distance"]

        comparison["composite_distance"] = sum(
            comparison[f"{metric}_normalized"] * weight
            for metric, weight in weights.items()
        )

    comparisons.sort(key=lambda item: item["composite_distance"])

    for rank, comparison in enumerate(comparisons, start=1):
        comparison["rank"] = rank

    return comparisons


def export_ranking_csv(
    rankings: list[dict],
    output_path: str | Path,
) -> None:
    """Export ranking records to a CSV file."""

    if not rankings:
        raise ValueError("There are no results to export.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = rankings[0].keys()

    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rankings)





SENSITIVITY_SCENARIOS = {
    "balanced": {
        "slope_distance": 1 / 3,
        "roughness_distance": 1 / 3,
        "relief_distance": 1 / 3,
    },
    "slope_focus": {
        "slope_distance": 0.60,
        "roughness_distance": 0.20,
        "relief_distance": 0.20,
    },
    "roughness_focus": {
        "slope_distance": 0.20,
        "roughness_distance": 0.60,
        "relief_distance": 0.20,
    },
    "relief_focus": {
        "slope_distance": 0.20,
        "roughness_distance": 0.20,
        "relief_distance": 0.60,
    },
    "slope_roughness": {
        "slope_distance": 0.40,
        "roughness_distance": 0.40,
        "relief_distance": 0.20,
    },
    "slope_relief": {
        "slope_distance": 0.40,
        "roughness_distance": 0.20,
        "relief_distance": 0.40,
    },
    "roughness_relief": {
        "slope_distance": 0.20,
        "roughness_distance": 0.40,
        "relief_distance": 0.40,
    },
}


def sensitivity_analysis(
    lunar: SiteSignature,
    earth_sites: list[SiteSignature],
) -> list[dict]:
    """
    Test different component weights and return
    the ranking under each scenario.
    """
    results = []

    for scenario_name, weights in SENSITIVITY_SCENARIOS.items():
        ranking = rank_analogs(
            lunar,
            earth_sites,
            weights=weights,
        )

        for item in ranking:
            results.append({
                "lunar_target": lunar.name,
                "scenario": scenario_name,
                "earth_site": item["earth_site"],
                "rank": item["rank"],
                "composite_distance": item["composite_distance"],
                "weight_slope": weights["slope_distance"],
                "weight_roughness": weights["roughness_distance"],
                "weight_relief": weights["relief_distance"],
            })

    return results
