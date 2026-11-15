
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
    """Plota a altura e a declividade da região lunar."""

    # Prepara os dados
    elevation = np.ma.masked_invalid(window.data)
    extent = window.extent

    # Cria os dois gráficos
    figure, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Gráfico 1: Altura do terreno
    elevation_image = axes[0].imshow(
        elevation,
        extent=extent,
        cmap="terrain",
    )

    figure.colorbar(
        elevation_image,
        ax=axes[0],
        label="Altura (m)",
    )

    axes[0].set_title(f"{target_name}: altura")

    # Gráfico 2: Declividade do terreno
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
        label="Declividade (°)",
    )

    axes[1].set_title(f"{target_name}: declividade")

    # Coordenadas do ponto de interesse
    target_x = window.target_x / 1000
    target_y = window.target_y / 1000

    # Marca o ponto de interesse nos dois gráficos
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

        axis.set_xlabel("X (km) a partir do polo")
        axis.set_ylabel("Y (km) a partir do polo")

        axis.set_xlim(extent[0], extent[1])
        axis.set_ylim(extent[2], extent[3])

    # Ajusta o espaçamento entre os gráficos
    figure.tight_layout()

    # Salva a imagem, caso um caminho tenha sido informado
    if save_path is not None:
        figure.savefig(save_path, dpi=150, bbox_inches="tight")

    # Exibe os gráficos
    if show:
        plt.show()

    return figure
