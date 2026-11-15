"""Tests for dashboard scoring without the Streamlit runtime."""
import pandas as pd
import pytest
from dashboard.data import read_ranking, read_sensitivity, weighted_ranking, validate_baseline, winners


def test_exported_balanced_scores_match():
    for target in ('Shackleton','Haworth'):
        for excluded in (False, True):
            assert validate_baseline(read_ranking(target, excluded)) < 1e-10


def test_balanced_winner_is_tolbachik():
    for target in ('Shackleton','Haworth'):
        ranked = weighted_ranking(read_ranking(target), {'slope':1,'roughness':1,'relief':1})
        assert ranked.iloc[0]['earth_site'] == 'Tolbachik'


def test_shackleton_slope_focus_switches_winner():
    ranked = weighted_ranking(read_ranking('Shackleton'), {'slope':0.6,'roughness':0.2,'relief':0.2})
    assert ranked.iloc[0]['earth_site'] == 'Death Valley'


def test_saved_sensitivity_winners():
    assert (winners(read_sensitivity('Haworth'))['earth_site'] == 'Tolbachik').all()
    assert (winners(read_sensitivity('Shackleton'))['earth_site'] == 'Tolbachik').sum() == 5


def test_invalid_weights_raise():
    with pytest.raises(ValueError):
        weighted_ranking(read_ranking('Shackleton'), {'slope':0,'roughness':0,'relief':0})
