
import rasterio
import numpy as np
import matplotlib.pyplot as plt

from pyproj import CRS, Transformer
from rasterio.windows import Window
from rasterio.plot import plotting_extent


caminho = "dados/AVGVISIB_85S_060M_201608.TIF"

latitude = -89.9
longitude = 129.8

meia_largura_m = 20_000

lua = CRS.from_proj4(
    "+proj=longlat +R=1737400 +no_defs"
)


with rasterio.open(caminho) as src:

    transformer = Transformer.from_crs(
        lua, src.crs, always_xy=True
    )

    x, y = transformer.transform(longitude, latitude)

    linha, coluna = src.index(x, y)

    if not (0 <= linha < src.height and 0 <= coluna < src.width):
        raise ValueError("Shackleton está fora da área do arquivo.")

    pixels = int(np.ceil(meia_largura_m / src.res[0]))

    janela = Window(
        coluna - pixels,
        linha - pixels,
        2 * pixels + 1,
        2 * pixels + 1
    )

    janela = janela.intersection(
        Window(0, 0, src.width, src.height)
    )

    dados = src.read(1, window=janela, masked=True)

    iluminacao = (
        dados.astype(np.float32) * src.scales[0]
        + src.offsets[0]
    ) * 100

    transformacao = src.window_transform(janela)
    extensao = plotting_extent(iluminacao, transformacao)

    extensao_km = [
        (extensao[0] - x) / 1000,
        (extensao[1] - x) / 1000,
        (extensao[2] - y) / 1000,
        (extensao[3] - y) / 1000
    ]

    print("Dimensões do recorte:", iluminacao.shape)
    print("Iluminação média:", iluminacao.mean(), "%")

    fig, ax = plt.subplots(figsize=(9, 8))

    imagem = ax.imshow(
        iluminacao,
        extent=extensao_km,
        origin="upper",
        cmap="inferno",
        vmin=0,
        vmax=100
    )

    ax.scatter(0, 0, color="cyan", marker="+", s=100,
               label="Centro de referência de Shackleton")

    plt.colorbar(imagem, ax=ax, label="Iluminação solar (%)")

    ax.set_title("Iluminação Solar - Região de Shackleton")
    ax.set_xlabel("Distância Leste/Oeste (km)")
    ax.set_ylabel("Distância Norte/Sul (km)")
    ax.legend()

    plt.tight_layout()
    plt.show()