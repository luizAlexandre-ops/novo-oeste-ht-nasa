"""Validated, pipeline-independent loading and scoring of exported results."""
from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / 'outputs'
METRICS = ('slope', 'roughness', 'relief')
TARGETS = ('Shackleton', 'Haworth')

EARTH_COORDINATES = {
    'Atacama': (-23.5, -68.2),
    'Haughton Crater': (75.37, -89.68),
    'Death Valley': (36.24, -116.82),
    'Pinacate': (31.95, -113.5),
    'Tolbachik': (55.83, 160.38),
    'Meteor Crater': (35.027, -111.023),
}


def results_path(target: str, exclude_haughton: bool = False) -> Path:
    if target not in TARGETS:
        raise ValueError(f'Unknown lunar target: {target}')
    suffix = '_without_haughton' if exclude_haughton else ''
    return OUTPUTS / f'{target.lower()}_ranking{suffix}.csv'


def sensitivity_path(target: str, exclude_haughton: bool = False) -> Path:
    if target not in TARGETS:
        raise ValueError(f'Unknown lunar target: {target}')
    suffix = '_without_haughton' if exclude_haughton else ''
    return OUTPUTS / f'{target.lower()}_sensitivity{suffix}.csv'


def read_ranking(target: str, exclude_haughton: bool = False) -> pd.DataFrame:
    path = results_path(target, exclude_haughton)
    df = pd.read_csv(path, encoding='utf-8-sig')
    required = {'earth_site', 'rank', 'composite_distance'} | {
        f'{m}_distance_normalized' for m in METRICS
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f'{path.name}: missing columns: {sorted(missing)}')
    if df.empty:
        raise ValueError(f'{path.name} is empty')
    for m in METRICS:
        column = f'{m}_distance_normalized'
        if not np.isfinite(df[column]).all():
            raise ValueError(f'{path.name}: non-finite values in {column}')
    return df


def read_sensitivity(target: str, exclude_haughton: bool = False) -> pd.DataFrame:
    path = sensitivity_path(target, exclude_haughton)
    df = pd.read_csv(path, encoding='utf-8-sig')
    required = {'scenario', 'earth_site', 'rank', 'composite_distance'}
    if required - set(df.columns):
        raise ValueError(f'{path.name}: missing columns {sorted(required - set(df.columns))}')
    return df


def read_summary() -> dict:
    path = OUTPUTS / 'pipeline_summary.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def weighted_ranking(ranking: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    """Reweight fixed per-candidate Min-Max components, without reprocessing DEMs."""
    if set(weights) != set(METRICS):
        raise ValueError('Weights must contain slope, roughness and relief')
    if any(not np.isfinite(v) or v < 0 for v in weights.values()):
        raise ValueError('Weights must be finite and non-negative')
    total = sum(weights.values())
    if total <= 0:
        raise ValueError('At least one weight must be positive')
    out = ranking.copy()
    out['composite_distance'] = 0.0
    for m in METRICS:
        out[f'{m}_contribution'] = out[f'{m}_distance_normalized'] * weights[m] / total
        out['composite_distance'] += out[f'{m}_contribution']
    out = out.sort_values(['composite_distance', 'earth_site'], kind='stable').reset_index(drop=True)
    out['rank'] = np.arange(1, len(out) + 1)
    return out


def validate_baseline(ranking: pd.DataFrame) -> float:
    """Maximum absolute error between exported balanced scores and recomputed scores."""
    reranked = weighted_ranking(ranking, {'slope': 1, 'roughness': 1, 'relief': 1})
    original = ranking.set_index('earth_site')['composite_distance']
    computed = reranked.set_index('earth_site')['composite_distance']
    return float((original - computed).abs().max()) if len(original) else 0.0


def winners(sensitivity: pd.DataFrame) -> pd.DataFrame:
    return sensitivity.loc[sensitivity['rank'].eq(1), ['scenario', 'earth_site']].reset_index(drop=True)


def terrain_figure_path(name: str) -> Path:
    return OUTPUTS / 'figures' / (name.lower().replace(' ', '_') + '.png')
