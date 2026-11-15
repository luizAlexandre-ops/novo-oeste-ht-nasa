"""Offline regression tests for the pipeline and ranking."""
from pathlib import Path
from unittest.mock import patch

import numpy as np

from src.terrain.analysis.terrain import analyze_site
from src.terrain.comparison.comparison import rank_analogs
from src.terrain.locations import Location
from src.terrain.pipeline.runner import inspect_quality, run_pipeline
from src.terrain.site import Site
from src.terrain.analysis.signature import build_signature


def make_site(name: str, offset: float) -> Site:
    x = np.arange(50, dtype=float)
    grid_x, grid_y = np.meshgrid(x, x)
    elevation = 0.05 * grid_x**2 + 0.03 * grid_y**2 + offset * np.sin(grid_x / 5)
    analysis = analyze_site(name, elevation, 120.0)
    return Site(analysis, np.full(elevation.shape, np.nan), [-3, 3, -3, 3], 120.0)


def test_quality_check():
    quality = inspect_quality(make_site("Example", 2.0))
    assert quality["pixel_size_m"] == 120
    assert quality["missing_fraction"] == 0


def test_rank_consistency():
    lunar = build_signature(make_site("Moon", 2.0))
    earth = [build_signature(make_site("Earth 1", 2.0)), build_signature(make_site("Earth 2", 20.0))]
    ranking = rank_analogs(lunar, earth)
    assert ranking[0]["earth_site"] == "Earth 1"


def test_complete_pipeline_offline(tmp_path: Path):
    lunar = [make_site("Shackleton", 2.0), make_site("Haworth", 5.0)]
    earth = [make_site("Tolbachik", 2.0), make_site("Death Valley", 7.0), make_site("Haughton Crater", 10.0)]
    with patch("src.terrain.pipeline.runner.download_lunar_inputs", return_value=[]), \
         patch("src.terrain.pipeline.runner.build_lunar_site", side_effect=lunar), \
         patch("src.terrain.pipeline.runner.build_earth_site", side_effect=earth), \
         patch("src.terrain.pipeline.runner.EARTH_ANALOG_SITES", [
             Location(site.name, 0.0, 0.0) for site in earth
         ]):
        result = run_pipeline(output_directory=tmp_path, generate_plots=True)
    assert (tmp_path / "shackleton_ranking.csv").exists()
    assert (tmp_path / "haworth_sensitivity_without_haughton.csv").exists()
    assert (tmp_path / "figures" / "tolbachik.png").exists()
    assert (tmp_path / "pipeline_summary.json").exists()
    assert result["targets"]["Shackleton"]["winner"] == "Tolbachik"