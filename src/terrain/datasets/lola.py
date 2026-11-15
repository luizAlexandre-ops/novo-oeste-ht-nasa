from pathlib import Path

from pyproj import CRS

from src.terrain.config import MOON_RADIUS_METERS
from src.terrain.datasets.raster import crop_raster_window


def crop_lola_window(
    label_path: Path,
    latitude: float,
    longitude: float,
    half_width_meters: float,
):
    moon_crs = CRS.from_proj4(
        f"+proj=longlat +R={MOON_RADIUS_METERS} +no_defs"
    )

    return crop_raster_window(
        raster_path=label_path,
        x=longitude,
        y=latitude,
        half_width=half_width_meters,
        coordinate_crs=moon_crs,
    )