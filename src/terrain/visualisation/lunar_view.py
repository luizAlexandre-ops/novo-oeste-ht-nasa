
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.terrain.analysis.terrain import TerrainMetrics
from src.terrain.datasets.raster import RasterWindow


def plot_lunar_target(
    window: RasterWindow,
    metrics: TerrainMetrics,
    target_name: str,
    save_path: Path | None = None,
    show: bool = True,
):
    """Plot lunar elevation and slope for the selected region."""

    # Prepare input values
    elevation = np.ma.masked_invalid(window.data)
    extent = window.extent

    # Create two map panels
    figure, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Panel 1: terrain elevation
    elevation_image = axes[0].imshow(
        elevation,
        extent=extent,
        cmap="terrain",
    )

    figure.colorbar(
        elevation_image,
        ax=axes[0],
        label="Elevation (m)",
    )

    axes[0].set_title(f"{target_name}: altura")

    # Panel 2: terrain slope
    slope_image = axes[1].imshow(
        metrics.slope_degrees,
        extent=extent,
        cmap="magma",
        vmin=0,
        vmax=40,
    )

    figure.colorbar(
        slope_image,
        ax=axes[1],
        label="Slope (°)",
    )

    axes[1].set_title(f"{target_name}: declividade")

    # Target coordinates
    target_x = window.target_x / 1000
    target_y = window.target_y / 1000

    # Mark the target on both panels
    for axis in axes:
        axis.plot(target_x, target_y, "r+", ms=16, mew=2)

        axis.annotate(
            target_name,
            (target_x, target_y),
            color="red",
            xytext=(6, 6),
            textcoords="offset points",
            fontweight="bold",
        )

        axis.set_xlabel("X (km) from pole")
        axis.set_ylabel("Y (km) from pole")

        axis.set_xlim(extent[0], extent[1])
        axis.set_ylim(extent[2], extent[3])

    # Adjust panel spacing
    figure.tight_layout()

    # Save the figure if a destination was provided
    if save_path is not None:
        figure.savefig(save_path, dpi=150, bbox_inches="tight")

    # Display panels when requested
    if show:
        plt.show()

    return figure
