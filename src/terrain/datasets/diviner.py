import numpy as np
import pandas as pd
from pyproj import CRS, Transformer
from scipy.spatial import cKDTree

from src.terrain.config import (
    DIVINER_CACHE_PATH,
    DIVINER_MAX_DISTANCE_METERS,
    DIVINER_TABLE_PATH,
    MOON_RADIUS_METERS,
)

_COLUMNS = ["clon", "clat", "temp_avg", "temp_max"]
_COLSPECS = [(126, 141), (143, 158), (177, 185), (187, 195)]

def load_diviner_table() -> dict[str, np.ndarray]:
    """Load and cache the large Diviner table in an NPZ file."""
    if DIVINER_CACHE_PATH.exists():
        with np.load(DIVINER_CACHE_PATH) as cache:
            return {name: cache[name] for name in _COLUMNS}

    chunks = []
    for chunk in pd.read_fwf(
        DIVINER_TABLE_PATH, colspecs=_COLSPECS, header=None,
        skiprows=1, names=_COLUMNS, chunksize=500_000,
    ):
        chunks.append(chunk.apply(pd.to_numeric, errors="coerce").dropna())
    table = pd.concat(chunks, ignore_index=True)
    print(table.describe())

    arrays = {name: table[name].to_numpy() for name in _COLUMNS}
    np.savez_compressed(DIVINER_CACHE_PATH, **arrays)
    return arrays

def diviner_on_grid(
    bounds: tuple[float, float, float, float], 
    shape: tuple[int, int],
    crs,
    max_distance_meters: float = DIVINER_MAX_DISTANCE_METERS,
) -> dict[str, np.ndarray]:
    """Map temperature (K) to the target grid via nearest triangular cell."""
    table = load_diviner_table()
    moon = CRS.from_proj4(f"+proj=longlat +R={MOON_RADIUS_METERS} +no_defs")
    transformer = Transformer.from_crs(moon, crs, always_xy=True)
    x, y = transformer.transform(table["clon"], table["clat"])
    x, y = np.asarray(x), np.asarray(y)

    left, bottom, right, top = bounds
    margin = 2 * max_distance_meters
    near = (
        (x > left - margin) & (x < right + margin)
        & (y > bottom - margin) & (y < top + margin)
    )
    if not near.any():
        raise ValueError("No Diviner triangles found near this region.")
    tree = cKDTree(np.column_stack([x[near], y[near]]))

    rows, columns = shape
    pixel_x = (right - left) / columns
    pixel_y = (top - bottom) / rows
    grid_x, grid_y = np.meshgrid(
        left + (np.arange(columns) + 0.5) * pixel_x,   
        top - (np.arange(rows) + 0.5) * pixel_y,
    )
    distance, index = tree.query(
        np.column_stack([grid_x.ravel(), grid_y.ravel()]),
        distance_upper_bound=max_distance_meters,
    )
    found = np.isfinite(distance)  

    layers = {}
    for column, name in (("temp_avg", "temp_mean_k"), ("temp_max", "temp_max_k")):
        values = table[column][near]
        flat = np.full(rows * columns, np.nan)
        flat[found] = values[index[found]]
        layers[name] = flat.reshape(shape)
    return layers