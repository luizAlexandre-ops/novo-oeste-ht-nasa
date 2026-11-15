from dataclasses import dataclass, field

import numpy as np
from rasterio.enums import Resampling

from src.terrain.analysis.terrain import SiteAnalysis, analyze_site
from src.terrain.config import AVGVISIB_PATH, DEFAULT_HALF_WIDTH_METERS, LOLA_LABEL_PATH, PSR_PATH
from src.terrain.datasets.diviner import diviner_on_grid
from src.terrain.datasets.lola import crop_lola_window, lola_elevation_meters
from src.terrain.datasets.raster import read_on_grid
from src.terrain.locations import Location  # ajuste ao nome real do seu arquivo
from src.terrain.datasets.copernicus import crop_copernicus_window


LUNAR_PIXEL_SIZE_METERS = 120.0

@dataclass(frozen=True)
class Site:
    """Elevação, métricas e iluminação alinhadas pixel a pixel."""

    analysis: SiteAnalysis
    illumination_percent: np.ndarray  # mesma grade da elevação, 0-100
    extent_km: list[float]            # [left, right, bottom, top] relativo ao alvo
    pixel_size_meters: float
    layers: dict[str, np.ndarray] = field(default_factory=dict)

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

    bounds = (left, bottom, right, top)
    psr = read_on_grid(PSR_PATH, bounds, elevation.shape, resampling=Resampling.average)
    layers = {"psr_fraction": np.ma.filled(psr, np.nan)}
    layers.update(diviner_on_grid(bounds, elevation.shape, window.crs))

    analysis = analyze_site(location.name, elevation, pixel_size)
    return Site(analysis, illumination_percent, extent_km, pixel_size, layers)


def build_earth_site(
    location: Location,
    half_width_meters: float = DEFAULT_HALF_WIDTH_METERS,
    pixel_size_meters: float = LUNAR_PIXEL_SIZE_METERS,
) -> Site:
    elevation, half_extent = crop_copernicus_window(
        location.latitude, location.longitude, half_width_meters, pixel_size_meters
    )
    half_km = half_extent / 1000
    analysis = analyze_site(location.name, elevation.astype("float64"), pixel_size_meters)
    return Site(
        analysis=analysis,
        illumination_percent=np.full(elevation.shape, np.nan),  # sem análogo na Terra
        extent_km=[-half_km, half_km, -half_km, half_km],
        pixel_size_meters=pixel_size_meters,
    )