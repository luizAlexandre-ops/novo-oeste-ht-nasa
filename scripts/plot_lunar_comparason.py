
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.terrain.datasets.raster import RasterWindow
from src.terrain.analysis.terrain import TerrainMetrics
from src.terrain.site import Site


def plot_lunar_comparason(
    elevation_window: RasterWindow,
    illumination_window: RasterWindow,
    metrics: TerrainMetrics,
    elevation: np.ndarray,
    illumination: np.ndarray,
    target_name: str,
    save_path: Path | None = None,
    show: bool = True,
):
    """Compara a elevação e a iluminação solar de uma região lunar."""

    figure, axes = plt.subplots(1, 3, figsize=(16, 7))

    # Calcula os limites relativos ao ponto de interesse
    def get_extent(window):
        left, right, bottom, top = window.extent

        return [
            (left - window.target_x) / 1000,
            (right - window.target_x) / 1000,
            (bottom - window.target_y) / 1000,
            (top - window.target_y) / 1000,
        ]

    # Gráfico de elevação
    elevation_image = axes[0].imshow(
        elevation,
        extent=get_extent(elevation_window),
        origin="upper",
        cmap="terrain",
    )

    figure.colorbar(
        elevation_image,
        ax=axes[0],
        label="Elevação (m)",
    )

    axes[0].set_title("Elevação lunar")

    slope_image = axes[2].imshow(
            metrics.slope_degrees,
            extent=elevation_window.extent,
            cmap="magma",
            vmin=0,
            vmax=40,
    )

    figure.colorbar(
            slope_image,
            ax=axes[2],
            label="Declividade (°)",
    )

    axes[2].set_title("Declividade lunar")

    # Gráfico de iluminação
    illumination_image = axes[1].imshow(
        illumination,
        extent=get_extent(illumination_window),
        origin="upper",
        cmap="inferno",
        vmin=0,
        vmax=100,
    )

    figure.colorbar(
        illumination_image,
        ax=axes[1],
        label="Iluminação solar (%)",
    )

    axes[1].set_title("Iluminação solar")

    # Configura os dois gráficos
    for axis in axes:
        axis.scatter(
            0, 0,
            color="cyan",
            marker="+",
            s=100,
        )

        axis.set_xlabel("Distância Leste/Oeste (km)")
        axis.set_ylabel("Distância Norte/Sul (km)")
        axis.set_title(f"{target_name}: {axis.get_title()}")

    figure.tight_layout()

    if save_path is not None:
        figure.savefig(save_path, dpi=150, bbox_inches="tight")

    if show:
        plt.show()

    return figure



def plot_site(site: Site, save_path: Path | None = None, show: bool = True):
    metrics = site.analysis.metrics
    roughness_vmax = float(np.nanpercentile(metrics.roughness_meters, 98))
    panels = [
        ("Elevação (m)", site.analysis.elevation_meters, "cividis", {}),
        ("Declividade (°)", metrics.slope_degrees, "magma", {"vmin": 0, "vmax": 40}),
        ("Rugosidade (m)", metrics.roughness_meters, "viridis", {"vmin": 0, "vmax": roughness_vmax}),
        ("Iluminação solar (%)", site.illumination_percent, "inferno", {"vmin": 0, "vmax": 100}),
    ]
    panels = [panel for panel in panels if np.isfinite(panel[1]).any()]

    figure, axes = plt.subplots(
        1, len(panels), figsize=(5 * len(panels), 5.5),
        constrained_layout=True, squeeze=False,
    )
    for axis, (label, data, cmap, limits) in zip(axes[0], panels):
        image = axis.imshow(data, extent=site.extent_km, origin="upper", cmap=cmap, **limits)
        figure.colorbar(image, ax=axis, label=label, shrink=0.8)
        axis.scatter(0, 0, color="cyan", marker="+", s=40, linewidths=1)
        axis.set_title(label)
        axis.set_xlabel("X (km)")
        axis.set_ylabel("Y (km)")
    figure.suptitle(site.name)

    if save_path is not None:
        figure.savefig(save_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    return figure