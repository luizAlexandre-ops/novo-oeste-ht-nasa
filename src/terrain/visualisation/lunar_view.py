from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource

from src.terrain.analysis.terrain import TerrainMetrics
from src.terrain.analysis.terrain import fill_missing_with_mean
from src.terrain.datasets.lola import LolaWindow
from src.terrain.visualisation.graticule import draw_graticule


def plot_lunar_target(
    window: LolaWindow,
    metrics: TerrainMetrics,
    target_name: str,
    target_latitude: float,
    show_graticule: bool = True,
    parallel_step_degrees: float = 1.0,
    meridian_step_degrees: float = 30.0,
    save_path: Path | None = None,
    show: bool = True,
):
    """Three panels: elevation, hillshade + colored elevation, slope."""
    extent_km = window.extent_km
    pixel_size = window.pixel_size_meters
    masked_elevation = np.ma.masked_invalid(window.elevation_meters)

    hillshade = LightSource(azdeg=315, altdeg=20).hillshade(
        fill_missing_with_mean(window.elevation_meters),
        vert_exag=2, dx=pixel_size, dy=pixel_size,
    )

    figure, axes = plt.subplots(1, 3, figsize=(20, 6.5))

    elevation_image = axes[0].imshow(masked_elevation, extent=extent_km, cmap="gray")
    plt.colorbar(elevation_image, ax=axes[0], fraction=0.046, label="Altura (m)")
    axes[0].set_title(f"{target_name}: altura (LDEM {pixel_size:.0f} m)")

    axes[1].imshow(hillshade, extent=extent_km, cmap="gray")
    colored_image = axes[1].imshow(masked_elevation, extent=extent_km, cmap="terrain", alpha=0.5)
    plt.colorbar(colored_image, ax=axes[1], fraction=0.046, label="Altura (m)")
    axes[1].set_title(f"{target_name}: hillshade")

    slope_image = axes[2].imshow(
        metrics.slope_degrees, extent=extent_km, cmap="magma", vmin=0, vmax=40
    )
    plt.colorbar(slope_image, ax=axes[2], fraction=0.046, label="Declividade (°)")
    axes[2].set_title(f"{target_name}: declividade")

    target_x_km = window.target_x_meters / 1000
    target_y_km = window.target_y_meters / 1000
    pole_latitude = -90.0 if target_latitude < 0 else 90.0
    for axis in axes:
        axis.plot(target_x_km, target_y_km, "r+", ms=16, mew=2)
        axis.annotate(
            target_name, (target_x_km, target_y_km), color="red",
            xytext=(6, 6), textcoords="offset points", fontweight="bold",
        )
        axis.set_xlabel("X (km) a partir do polo")
        axis.set_ylabel("Y (km) a partir do polo")
        if show_graticule:
            draw_graticule(
                axis, window.longitude_latitude_to_projected, pole_latitude,
                extent_km, parallel_step_degrees, meridian_step_degrees,
            )
        axis.set_xlim(extent_km[0], extent_km[1])
        axis.set_ylim(extent_km[2], extent_km[3])

    figure.tight_layout()
    if save_path:
        figure.savefig(save_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    return figure
