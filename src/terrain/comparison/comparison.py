import csv
from pathlib import Path

import numpy as np

from src.terrain.analysis.signature import SiteSignature, slope_distance

def roughness_distance(a: SiteSignature, b: SiteSignature) -> float:
    """
    Compara a rugosidade RMS nas escalas espaciais compartilhadas.

    Usa a diferença logarítmica para comparar proporções,
    em vez de diferenças absolutas.
    """
    shared_baselines = np.intersect1d(
        a.roughness_baselines_m,
        b.roughness_baselines_m,
    )

    if len(shared_baselines) == 0:
        raise ValueError("As assinaturas não possuem escalas de rugosidade em comum.")

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
        raise ValueError("Não existem valores RMS válidos para comparação.")

    return float(np.mean(distances))


def relief_distance(a: SiteSignature, b: SiteSignature) -> float:
    """
    Compara o relevo relativo dos locais usando P99 - P1.

    A diferença logarítmica evita que a escala do relevo
    domine diretamente as outras métricas.
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
    """Calcula as distâncias individuais entre um alvo lunar e um local terrestre."""

    return {
        "lunar_target": lunar.name,
        "earth_site": earth.name,
        "slope_distance": slope_distance(lunar, earth),
        "roughness_distance": roughness_distance(lunar, earth),
        "relief_distance": relief_distance(lunar, earth),
    }


def normalize_distances(values: np.ndarray) -> np.ndarray:
    """
    Normaliza distâncias entre 0 e 1.

    O menor valor recebe 0 e o maior recebe 1.
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
    Compara um alvo lunar com vários locais terrestres
    e retorna os candidatos ordenados por similaridade.
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
        raise ValueError(f"Os pesos devem conter exatamente: {expected_metrics}")

    if any(weight < 0 for weight in weights.values()):
        raise ValueError("Os pesos não podem ser negativos.")

    total_weight = sum(weights.values())

    if total_weight <= 0:
        raise ValueError("A soma dos pesos deve ser maior que zero.")

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

    # Calcula a distância composta
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
    """Exporta os resultados do ranking para CSV."""

    if not rankings:
        raise ValueError("Não existem resultados para exportar.")

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
    Testa diferentes combinações de pesos e retorna
    o ranking de cada cenário.
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
