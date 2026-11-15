
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.windows import Window
from math import radians

# Arquivo MOLA
ARQUIVO = Path("dados/mars/mola/megt44n180hb.img")

# Centro de referência de Arcadia Planitia
LATITUDE = 39.8
LONGITUDE = 202.1

# Dimensões dos recortes, em quilômetros
TAMANHO_CONTEXTO_KM = 300
TAMANHO_DETALHE_KM = 50

# Constantes da projeção MOLA
RAIO_MARTE = 3_396_000
RESOLUCAO = 463.0576672  # metros por pixel


def criar_janela(src, tamanho_km):
    """Calcula uma janela quadrada centrada nas coordenadas de referência."""

    x = RAIO_MARTE * radians(LONGITUDE - 180)
    y = RAIO_MARTE * radians(LATITUDE)

    linha, coluna = src.index(x, y)

    pixels = round(tamanho_km * 1000 / RESOLUCAO)

    inicio_linha = linha - pixels // 2
    inicio_coluna = coluna - pixels // 2

    # Garante que a janela fique dentro do raster
    inicio_linha = max(0, inicio_linha)
    inicio_coluna = max(0, inicio_coluna)

    altura = min(pixels, src.height - inicio_linha)
    largura = min(pixels, src.width - inicio_coluna)

    janela = Window(inicio_coluna, inicio_linha, largura, altura)

    dados = src.read(1, window=janela, masked=True)

    # Eixos locais em quilômetros, relativos ao centro do recorte
    largura_km = largura * RESOLUCAO / 1000
    altura_km = altura * RESOLUCAO / 1000

    extensao = (
        -largura_km / 2,
        largura_km / 2,
        -altura_km / 2,
        altura_km / 2,
    )

    return dados, extensao



def main():
    with rasterio.open(ARQUIVO) as src:
        detalhe, extensao = criar_janela(
            src, TAMANHO_DETALHE_KM
        )

    valores = detalhe.compressed()

    if valores.size == 0:
        raise ValueError("O recorte não contém pixels válidos.")

    vmin, vmax = np.percentile(valores, [2, 98])

    fig = plt.figure(figsize=(9, 7))
    gs = fig.add_gridspec(
        1, 2,
        width_ratios=[1, 0.04],
        wspace=0.12
    )

    ax = fig.add_subplot(gs[0, 0])
    cax = fig.add_subplot(gs[0, 1])

    imagem = ax.imshow(
        detalhe,
        extent=extensao,
        origin="upper",
        cmap="terrain",
        vmin=vmin,
        vmax=vmax,
    )

    ax.set_title("MOLA — Arcadia Planitia (50 × 50 km)")
    ax.set_xlabel("Distância leste-oeste (km)")
    ax.set_ylabel("Distância norte-sul (km)")

    # Marca o centro da região
    ax.plot(0, 0, "r+", markersize=12, markeredgewidth=2)

    barra = fig.colorbar(imagem, cax=cax)
    barra.set_label("Elevação em relação ao areoide (m)")

    fig.suptitle("Centro: 39.8°N, 202.1°E")

    plt.show()


if __name__ == "__main__":
    main()
