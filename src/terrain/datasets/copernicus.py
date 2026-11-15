import math

import numpy as np
import rasterio
from pyproj import CRS
from rasterio.errors import RasterioIOError
from rasterio.merge import merge
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject

from src.terrain.config import (
    COPERNICUS_TILE_URL_TEMPLATE, COPERNICUS_CACHE_DIRECTORY,
    METERS_PER_DEGREE_LATITUDE,
)

TILE_SEARCH_MARGIN_FACTOR = 1.3


def build_tile_name(tile_latitude: int, tile_longitude: int) -> str:
    north_south = "N" if tile_latitude >= 0 else "S"
    east_west = "E" if tile_longitude >= 0 else "W"
    return (
        f"Copernicus_DSM_COG_10_{north_south}{abs(tile_latitude):02d}"
        f"_00_{east_west}{abs(tile_longitude):03d}_00_DEM"
    )


def crop_copernicus_window(
    latitude: float,
    longitude: float,
    half_width_meters: float,
    pixel_size_meters: float,
) -> tuple[np.ndarray, float]:
    """Return elevation on an odd-sized local AEQD metric grid and half-extent."""


    cache_name = (
        f"lat{latitude:+.5f}_lon{longitude:+.5f}_"
        f"half{half_width_meters:.1f}_px{pixel_size_meters:.1f}.npz"
    )
    cache_path = COPERNICUS_CACHE_DIRECTORY / cache_name
    if cache_path.is_file():
        with np.load(cache_path) as cached:
            return cached["elevation"], float(cached["half_extent"])

    latitude_margin = TILE_SEARCH_MARGIN_FACTOR * half_width_meters / METERS_PER_DEGREE_LATITUDE
    longitude_margin = latitude_margin / max(math.cos(math.radians(latitude)), 0.05)
    west, south = longitude - longitude_margin, latitude - latitude_margin
    east, north = longitude + longitude_margin, latitude + latitude_margin
    if west < -180 or east > 180:
        raise NotImplementedError("Region crosses the antimeridian: choose another center.")

    opened_tiles, missing_tile_names = [], []
    with rasterio.Env(AWS_NO_SIGN_REQUEST="YES", GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
        for tile_latitude in range(math.floor(south), math.floor(north) + 1):
            for tile_longitude in range(math.floor(west), math.floor(east) + 1):
                tile_name = build_tile_name(tile_latitude, tile_longitude)
                try:
                    opened_tiles.append(
                        rasterio.open(COPERNICUS_TILE_URL_TEMPLATE.format(tile_name=tile_name))
                    )
                except RasterioIOError:
                    missing_tile_names.append(tile_name)  # Ocean or unavailable tile

        if not opened_tiles:
            raise RuntimeError(
                f"No tile found at ({latitude}, {longitude}). Tried: {missing_tile_names}"
            )
        try:
            mosaic, mosaic_transform = merge(
                opened_tiles, bounds=(west, south, east, north), nodata=np.nan
            )
        finally:
            for tile in opened_tiles:
                tile.close()

    if missing_tile_names:
        print(f"  warning: missing tiles (NaN in the result): {missing_tile_names}")

    local_metric_crs = CRS.from_proj4(
        f"+proj=aeqd +lat_0={latitude} +lon_0={longitude} +datum=WGS84 +units=m +no_defs"
    )
    half_pixels = math.ceil(half_width_meters / pixel_size_meters)
    side_pixels = 2 * half_pixels + 1
    half_extent = side_pixels * pixel_size_meters / 2

    resampled_elevation = np.full((side_pixels, side_pixels), np.nan, dtype="float32")
    reproject(
        source=mosaic[0].astype("float32"),
        destination=resampled_elevation,
        src_transform=mosaic_transform,
        src_crs="EPSG:4326",
        src_nodata=np.nan,
        dst_transform=from_origin(-half_extent, half_extent, pixel_size_meters, pixel_size_meters),
        dst_crs=local_metric_crs,
        dst_nodata=np.nan,
        resampling=Resampling.average if pixel_size_meters >= 30 else Resampling.bilinear,
    )
    COPERNICUS_CACHE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        cache_path, elevation=resampled_elevation, half_extent=half_extent
    )
    return resampled_elevation, half_extent
