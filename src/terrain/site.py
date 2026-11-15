from dataclasses import dataclass

import numpy as np
from rasterio.enums import Resampling

from src.terrain.analysis.terrain import SiteAnalysis, analyze_site
from src.terrain.config import AVGVISIB_PATH, DEFAULT_HALF_WIDTH_METERS, LOLA_LABEL_PATH
from src.terrain.datasets.lola import crop_lola_window, lola_elevation_meters
from src.terrain.datasets.raster import read_on_grid
from src.terrain.locations import Location  # ajuste ao nome real do seu arquivo


@dataclass(frozen=True)
class Site:
    """Elevação, métricas e iluminação alinhadas pixel a pixel."""

    analysis: SiteAnalysis
    illumination_percent: np.ndarray  # mesma grade da elevação, 0-100
    extent_km: list[float]            # [left, right, bottom, top] relativo ao alvo
    pixel_size_meters: float

    @property
    def name(self) -> str:
        return self.analysis.name


def build_lunar_site(
    location: Location,
    half_width_meters: float = DEFAULT_HALF_WIDTH_METERS,
) -> Site:
    window = crop_lola_window(
        LOLA_LABEL_PATH, location.latitude, location.longitude, half_width_meters
    )
    elevation = lola_elevation_meters(window)
    pixel_size = window.pixel_size_x

    left, right, bottom, top = window.extent
    illumination_fraction = read_on_grid(
        AVGVISIB_PATH,
        bounds=(left, bottom, right, top),
        shape=elevation.shape,
        resampling=Resampling.average,
    )
    illumination_percent = np.ma.filled(100 * illumination_fraction, np.nan)

    extent_km = [
        (left - window.target_x) / 1000,
        (right - window.target_x) / 1000,
        (bottom - window.target_y) / 1000,
        (top - window.target_y) / 1000,
    ]
    analysis = analyze_site(location.name, elevation, pixel_size)
    return Site(analysis, illumination_percent, extent_km, pixel_size)