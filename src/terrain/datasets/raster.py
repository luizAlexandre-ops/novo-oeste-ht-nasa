
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio

from affine import Affine
from pyproj import CRS, Transformer
from rasterio.windows import Window


@dataclass(frozen=True)
class RasterWindow:
    """Dados de uma região extraída de um raster."""

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
        """Limites espaciais do recorte."""

        rows, columns = self.data.shape

        left, top = self.transform * (0, 0)
        right, bottom = self.transform * (columns, rows)

        return [left, right, bottom, top]


def crop_raster_window(
    raster_path: Path,
    x: float,
    y: float,
    half_width: float,
    coordinate_crs: CRS,
    band: int = 1,
) -> RasterWindow:
    """Extrai uma região de um raster ao redor de uma coordenada."""

    with rasterio.open(raster_path) as dataset:

        # Converte as coordenadas para o sistema de referência do raster
        transformer = Transformer.from_crs(
            coordinate_crs,
            dataset.crs,
            always_xy=True,
        )

        target_x, target_y = transformer.transform(x, y)

        # Identifica a posição do ponto no raster
        row, column = dataset.index(target_x, target_y)

        if not (0 <= row < dataset.height and 0 <= column < dataset.width):
            raise ValueError("O ponto está fora da área coberta pelo raster.")

        # Calcula o tamanho do recorte em pixels
        half_width_x = int(np.ceil(half_width / abs(dataset.res[0])))
        half_width_y = int(np.ceil(half_width / abs(dataset.res[1])))

        # Define a janela ao redor do ponto
        window = Window(
            column - half_width_x,
            row - half_width_y,
            2 * half_width_x + 1,
            2 * half_width_y + 1,
        )

        # Garante que a janela não ultrapasse o raster
        window = window.intersection(
            Window(0, 0, dataset.width, dataset.height)
        )

        # Lê os dados e suas informações espaciais
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
