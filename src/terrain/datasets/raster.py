
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio

from affine import Affine
from pyproj import CRS, Transformer
from rasterio.windows import Window, from_bounds
from rasterio.enums import Resampling





@dataclass(frozen=True)
class RasterWindow:
    """Data and metadata for a cropped raster region."""

    data: np.ma.MaskedArray
    transform: Affine
    crs: CRS

    pixel_size_x: float
    pixel_size_y: float

    target_x: float
    target_y: float

    scale: float
    offset: float

    @property
    def extent(self) -> list[float]:
        """Spatial bounds of the crop."""

        rows, columns = self.data.shape

        left, top = self.transform * (0, 0)
        right, bottom = self.transform * (columns, rows)

        return [left, right, bottom, top]

    @property
    def scaled_values(self) -> np.ma.MaskedArray:
        """Scaled data numbers; the LOLA offset defines the reference radius."""
        return self.data.astype("float64") * self.scale


def crop_raster_window(
    raster_path: Path,
    x: float,
    y: float,
    half_width: float,
    coordinate_crs: CRS,
    band: int = 1,
) -> RasterWindow:
    """Crop a raster around a target coordinate."""

    with rasterio.open(raster_path) as dataset:

        # Transform coordinates into the raster reference system
        transformer = Transformer.from_crs(
            coordinate_crs,
            dataset.crs,
            always_xy=True,
        )

        target_x, target_y = transformer.transform(x, y)

        # Locate the target pixel
        row, column = dataset.index(target_x, target_y)

        if not (0 <= row < dataset.height and 0 <= column < dataset.width):
            raise ValueError("Target coordinate is outside the raster coverage.")

        # Convert metric crop size to pixels
        half_width_x = int(np.ceil(half_width / abs(dataset.res[0])))
        half_width_y = int(np.ceil(half_width / abs(dataset.res[1])))

        # Center the crop window around the target
        window = Window(
            column - half_width_x,
            row - half_width_y,
            2 * half_width_x + 1,
            2 * half_width_y + 1,
        )

        # Clamp the window to the raster bounds
        window = window.intersection(
            Window(0, 0, dataset.width, dataset.height)
        )

        # Read elevation values and georeferencing metadata
        data = dataset.read(band, window=window, masked=True)
        transform = dataset.window_transform(window)

        pixel_size_x = abs(dataset.res[0])
        pixel_size_y = abs(dataset.res[1])

        scale = dataset.scales[band - 1]
        offset = dataset.offsets[band - 1]

        crs = dataset.crs

    return RasterWindow(
        data=data,
        transform=transform,
        crs=crs,
        pixel_size_x=pixel_size_x,
        pixel_size_y=pixel_size_y,
        target_x=target_x,
        target_y=target_y,
        scale=scale,
        offset=offset,
    )


def read_on_grid(
    raster_path: Path,
    bounds: tuple[float, float, float, float],  # left, bottom, right, top
    shape: tuple[int, int],
    band: int = 1,
    resampling: Resampling = Resampling.average,
) -> np.ma.MaskedArray:
    """Read raster bounds resampled to the requested shape in physical units."""
    with rasterio.open(raster_path) as dataset:
        window = from_bounds(*bounds, transform=dataset.transform)
        data = dataset.read(
            band,
            window=window,
            out_shape=shape,
            resampling=resampling,
            masked=True,
            boundless=True,  # Mark areas outside coverage as masked
        )
        scale = dataset.scales[band - 1]
    return data.astype("float64") * scale