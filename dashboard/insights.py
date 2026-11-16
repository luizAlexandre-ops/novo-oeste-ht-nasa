"""Explain and visualize how terrain metric weights affect analogue selection.

All inputs are the archived, per-target normalized component distances.
No raw DEMs or pipeline reprocessing are needed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from dashboard.data import METRICS, weighted_ranking

PAIR = ('Tolbachik', 'Death Valley')
LABELS = {'slope': 'Slope', 'roughness': 'Roughness', 'relief': 'Relief'}


def pairwise_comparison(ranking: pd.DataFrame, weights: dict[str, float],
                        first: str = PAIR[0], second: str = PAIR[1]) -> dict:
    """Explain the signed score difference (first minus second) at given weights."""
    data = ranking.set_index('earth_site')
    if first not in data.index or second not in data.index:
        raise ValueError('Both candidates must be present in the ranking')
    computed = weighted_ranking(ranking, weights).set_index('earth_site')
    a, b = computed.loc[first], computed.loc[second]
    differences = {
        metric: float(a[f'{metric}_contribution'] - b[f'{metric}_contribution'])
        for metric in METRICS
    }
    score_a, score_b = float(a['composite_distance']), float(b['composite_distance'])
    if np.isclose(score_a, score_b, atol=1e-10):
        winner = 'Tie'
    else:
        winner = first if score_a < score_b else second
    return {
        'first': first, 'second': second, 'first_score': score_a,
        'second_score': score_b, 'winner': winner, 'difference': score_a - score_b,
        'metric_differences': differences,
    }


def slope_threshold_with_equal_other_weights(ranking: pd.DataFrame,
                                               first: str = PAIR[0], second: str = PAIR[1]) -> float | None:
    """Slope weight at which the two candidates tie if roughness=relief=(1-slope)/2.

    Returns None when the tie lies outside the 0..1 weight simplex, or
    scores are identical throughout the chosen line.
    """
    data = ranking.set_index('earth_site')
    if first not in data.index or second not in data.index:
        return None
    delta = {m: float(data.loc[first, f'{m}_distance_normalized'] -
                      data.loc[second, f'{m}_distance_normalized']) for m in METRICS}
    others = (delta['roughness'] + delta['relief']) / 2
    denom = delta['slope'] - others
    if abs(denom) <= 1e-12:
        return None
    s = -others / denom
    return float(s) if 0 <= s <= 1 else None


def weight_simplex_winners(ranking: pd.DataFrame, steps: int = 31) -> pd.DataFrame:
    """Sample non-negative weight triples summing to one (ternary diagram)."""
    if steps < 2:
        raise ValueError('steps must be >= 2')
    fields = [f'{m}_distance_normalized' for m in METRICS]
    candidates = ranking['earth_site'].to_numpy()
    values = ranking[fields].to_numpy(dtype=float)
    result = []
    denominator = steps - 1
    for i in range(steps):
        for j in range(steps - i):
            k = denominator - i - j
            weights = np.array([i, j, k], dtype=float) / denominator
            scores = values @ weights
            winner_idx = int(np.argmin(scores))
            order = np.argsort(scores)
            gap = float(scores[order[1]] - scores[order[0]]) if len(order) > 1 else 0.0
            result.append({
                'slope': weights[0] * 100,
                'roughness': weights[1] * 100,
                'relief': weights[2] * 100,
                'winner': str(candidates[winner_idx]),
                'winning_distance': float(scores[winner_idx]),
                'gap_to_runner_up': gap,
            })
    return pd.DataFrame(result)
