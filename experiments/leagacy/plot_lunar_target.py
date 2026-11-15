from zipfile import Path

from pyproj import CRS

from experiments.leagacy.plot_lunar_comparason import plot_lunar_comparason
from src.terrain.analysis.terrain import compute_terrain_metrics
from src.terrain.config import (
    DEFAULT_HALF_WIDTH_METERS, LOLA_LABEL_PATH, MOON_RADIUS_METERS, OUTPUT_DIRECTORY, AVGVISIB_PATH,
)
from src.terrain.datasets.lola import crop_lola_window, lola_elevation_meters
from src.terrain.datasets.raster import crop_raster_window
from src.terrain.locations import HAWORTH_CRATER, SHACKLETON_CRATER
from src.terrain.visualisation.lunar_view import plot_lunar_target

TARGET = SHACKLETON_CRATER  # ou HAWORTH_CRATER

if __name__ == "__main__":
    OUTPUT_DIRECTORY.mkdir(exist_ok=True)

    moon_crs = CRS.from_proj4(
        f"+proj=longlat +R={MOON_RADIUS_METERS} +no_defs"
    )

    elevation_window = crop_raster_window(
        LOLA_LABEL_PATH,
        TARGET.longitude,
        TARGET.latitude,
        DEFAULT_HALF_WIDTH_METERS,
        moon_crs,
    )

    elevation = (
        lola_elevation_meters(elevation_window)
    )

        # Extrai iluminação
    illumination_window = crop_raster_window(
        AVGVISIB_PATH,
        TARGET.longitude,
        TARGET.latitude,
        DEFAULT_HALF_WIDTH_METERS,
        moon_crs,
    )

    illumination = (
        illumination_window.data.astype("float32")
        * illumination_window.scale
        + illumination_window.offset
    ) * 100

    metrics = compute_terrain_metrics(
        elevation,
        elevation_window.pixel_size_x,
    )

    plot_lunar_comparason(
        elevation_window,
        illumination_window,
        metrics,
        elevation,
        illumination,
        TARGET.name,
        save_path=OUTPUT_DIRECTORY / f"{TARGET.name.lower()}_comparison.png",
    )
