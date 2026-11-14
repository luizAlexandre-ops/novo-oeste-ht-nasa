import numpy as np
from pyproj import Transformer

LOLA_POLAR_LIMIT_LATITUDE = 80


def draw_graticule(
    axis,
    longitude_latitude_to_projected: Transformer,
    pole_latitude: float,
    extent_km: list[float],
    parallel_step_degrees: float,
    meridian_step_degrees: float,
) -> None:
    """Draw parallels (circles) and meridians (rays) with the dataset's own CRS."""
    hemisphere_sign = 1 if pole_latitude > 0 else -1
    longitudes = np.linspace(-180, 180, 721)
    left, right, bottom, top = extent_km

    latitude = pole_latitude - hemisphere_sign * parallel_step_degrees
    while abs(latitude) >= LOLA_POLAR_LIMIT_LATITUDE:
        xs, ys = longitude_latitude_to_projected.transform(
            longitudes, np.full_like(longitudes, latitude)
        )
        axis.plot(xs / 1000, ys / 1000, color="cyan", ls="--", lw=0.6, alpha=0.8)
        label_x, label_y = longitude_latitude_to_projected.transform(0.0, latitude)
        if left < label_x / 1000 < right and bottom < label_y / 1000 < top:
            axis.text(label_x / 1000, label_y / 1000, f"{latitude:.0f}°", color="cyan", fontsize=7)
        latitude -= hemisphere_sign * parallel_step_degrees

    meridian_latitudes = np.linspace(pole_latitude, hemisphere_sign * LOLA_POLAR_LIMIT_LATITUDE, 100)
    for meridian_longitude in np.arange(-180, 180, meridian_step_degrees):
        xs, ys = longitude_latitude_to_projected.transform(
            np.full_like(meridian_latitudes, meridian_longitude), meridian_latitudes
        )
        axis.plot(xs / 1000, ys / 1000, color="cyan", ls=":", lw=0.5, alpha=0.7)
