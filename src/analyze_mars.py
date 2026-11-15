import matplotlib.pyplot as plt
import numpy as np
from math import cos, radians
from src.view_mars import (
    ARQUIVO,
    TAMANHO_DETALHE_KM,
    RESOLUCAO,
    criar_janela,
)

import rasterio


def main():
    with rasterio.open(ARQUIVO) as src:
        elevacao, extensao = criar_janela(
            src, TAMANHO_DETALHE_KM
        )

    # Converte os dados para uma matriz com NaN nos pixels inválidos
    dados = elevacao.astype(np.float32).filled(np.nan)

    # Corrige a distância leste-oeste conforme a latitude
    resolucao_x = RESOLUCAO * cos(radians(39.8))
    resolucao_y = RESOLUCAO

    gradiente_y, gradiente_x = np.gradient(
        dados,
        resolucao_y,
        resolucao_x,
    )

    # Calcula a declividade em graus
    declividade = np.degrees(
        np.arctan(
            np.sqrt(gradiente_x**2 + gradiente_y**2)
        )
    )

    declividade = np.ma.masked_invalid(declividade)

    # Estatísticas
    valores = declividade.compressed()

    print("\n--- DECLIVIDADE DE ARCADIA PLANITIA ---")
    print(f"Pixels analisados: {valores.size}")
    print(f"Média: {np.mean(valores):.2f}°")
    print(f"Mediana: {np.median(valores):.2f}°")
    print(f"Mínima: {np.min(valores):.2f}°")
    print(f"Máxima: {np.max(valores):.2f}°")
    print(f"Desvio padrão: {np.std(valores):.2f}°")

    # Visualização
    fig = plt.figure(figsize=(9, 7))
    gs = fig.add_gridspec(
        1, 2,
        width_ratios=[1, 0.04],
        wspace=0.12,
    )

    ax = fig.add_subplot(gs[0, 0])
    cax = fig.add_subplot(gs[0, 1])

    imagem = ax.imshow(
        declividade,
        extent=extensao,
        origin="upper",
        cmap="viridis",
        vmin=0,
        vmax=20,
    )

    ax.set_title("Declividade — Arcadia Planitia (50 × 50 km)")
    ax.set_xlabel("Distância leste-oeste (km)")
    ax.set_ylabel("Distância norte-sul (km)")

    barra = fig.colorbar(imagem, cax=cax)
    barra.set_label("Declividade (graus)")

    plt.show()


if __name__ == "__main__":
    main()
