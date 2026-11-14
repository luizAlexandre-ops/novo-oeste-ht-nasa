from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine
from pyproj import CRS, Transformer
from rasterio.windows import Window

from src.terrain.config import LOLA_ELEVATION_SCALE_FACTOR, MOON_RADIUS_METERS


@dataclass(frozen=True)
class LolaWindow:
    """A cropped piece of the LOLA LDEM centered on a target."""

    elevation_meters: np.ndarray
    window_transform: Affine
    pixel_size_meters: float
    target_x_meters: float
    target_y_meters: float
    longitude_latitude_to_projected: Transformer

    @property
    def extent_km(self) -> list[float]:
        """[left, right, bottom, top] in km, ready for matplotlib `extent`."""
        row_count, column_count = self.elevation_meters.shape
        left, top = self.window_transform * (0, 0)
        right, bottom = self.window_transform * (column_count, row_count)
        return [left / 1000, right / 1000, bottom / 1000, top / 1000]


def crop_lola_window(
    label_path: Path,
    latitude: float,
    longitude: float,
    half_width_meters: float,
    elevation_scale_factor: float = LOLA_ELEVATION_SCALE_FACTOR,
) -> LolaWindow:
    """Crop the LDEM around (latitude, longitude). Heights are relative to the
    reference sphere of 1737.4 km."""
    moon_geographic_crs = CRS.from_proj4(f"+proj=longlat +R={MOON_RADIUS_METERS} +no_defs")

    with rasterio.open(label_path) as dataset:
        pixel_size_meters = dataset.res[0]
        transformer = Transformer.from_crs(moon_geographic_crs, dataset.crs, always_xy=True)
        target_x, target_y = transformer.transform(longitude, latitude)
        target_row, target_column = dataset.index(target_x, target_y)

        half_width_pixels = int(half_width_meters / pixel_size_meters)
        first_column = max(target_column - half_width_pixels, 0)
        first_row = max(target_row - half_width_pixels, 0)
        last_column = min(target_column + half_width_pixels, dataset.width)
        last_row = min(target_row + half_width_pixels, dataset.height)
        if last_column <= first_column or last_row <= first_row:
            raise ValueError(
                "Target is outside the raster. Check latitude/longitude, the file "
                "coverage (e.g. 75S vs 75N) and the longitude convention."
            )

        window = Window(first_column, first_row, last_column - first_column, last_row - first_row)
        raw_values = dataset.read(1, window=window)
        window_transform = dataset.window_transform(window)
        nodata_value = dataset.nodata

    elevation_meters = raw_values.astype("float32") * elevation_scale_factor
    if nodata_value is not None:
        elevation_meters[raw_values == nodata_value] = np.nan

    return LolaWindow(
        elevation_meters=elevation_meters,
        window_transform=window_transform,
        pixel_size_meters=pixel_size_meters,
        target_x_meters=target_x,
        target_y_meters=target_y,
        longitude_latitude_to_projected=transformer,
    )
