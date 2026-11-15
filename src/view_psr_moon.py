import rasterio
import numpy as np
import matplotlib.pyplot as plt

from matplotlib.colors import ListedColormap
from matplotlib.patches import Circle
from pyproj import CRS, Transformer
from rasterio.windows import Window
from rasterio.plot import plotting_extent


caminho = "dataLPSR_80S_20MPP_ADJ.TIF"

latitude = -89.9
longitude = 129.8

meia_largura_m = 20_000   # tamanho do recorte exibido
raio_metrica_m = 10_000   # raio usado para calcular a fração de PSR

lua = CRS.from_proj4(
    "+proj=longlat +R=1737400 +no_defs"
)

with rasterio.open(caminho) as src:

    # --- Metadados para conferir como o arquivo codifica os dados ---
    print("CRS:", src.crs)
    print("Resolução (m/pixel):", src.res)
    print("nodata:", src.nodata)
    print("dtype:", src.dtypes[0])
    print("scales/offsets:", src.scales, src.offsets)

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
    transformacao = src.window_transform(janela)

# --- Valores presentes no recorte (confirmar o significado da máscara) ---
valores, contagens = np.unique(dados.compressed(), return_counts=True)
print("Valores no recorte:", dict(zip(valores.tolist(), contagens.tolist())))

# Máscara binária confirmada: 0 = fora do PSR; 1 = PSR.
validos = ~np.ma.getmaskarray(dados)
em_psr = (dados.filled(0) != 0) & validos

# --- Métrica: fração de PSR dentro de um círculo de raio_metrica_m ---
linhas, colunas = np.indices(dados.shape)
xs, ys = transformacao * (colunas + 0.5, linhas + 0.5)  # centro de cada pixel
distancia = np.hypot(xs - x, ys - y)

dentro = (distancia <= raio_metrica_m) & validos

if dentro.sum() == 0:
    raise ValueError("Nenhum pixel válido dentro do raio da métrica.")

fracao_psr = 100 * em_psr[dentro].mean()

print("Dimensões do recorte:", dados.shape)
print("Pixels em PSR no recorte:", int(em_psr.sum()))
print(f"Fração de PSR em {raio_metrica_m / 1000:.0f} km: {fracao_psr:.2f} %")

# --- Visualização ---
extensao = plotting_extent(dados, transformacao)

extensao_km = [
    (extensao[0] - x) / 1000,
    (extensao[1] - x) / 1000,
    (extensao[2] - y) / 1000,
    (extensao[3] - y) / 1000
]

# Pixels sem dado ficam transparentes; 0 = fora do PSR; 1 = PSR
mapa = np.ma.masked_where(~validos, em_psr.astype(np.uint8))
cores = ListedColormap(["#2b2b2b", "#4fc3f7"])

fig, ax = plt.subplots(figsize=(9, 8))

ax.imshow(
    mapa,
    extent=extensao_km,
    origin="upper",
    cmap=cores,
    vmin=0,
    vmax=1,
    interpolation="nearest"
)

# Círculo que mostra a área usada no cálculo da fração de PSR
ax.add_patch(
    Circle(
        (0, 0),
        raio_metrica_m / 1000,
        fill=False,
        edgecolor="white",
        linestyle="--",
        linewidth=1.2
    )
)

# Centro de referência de Shackleton
ax.scatter(
    0, 0,
    color="red",
    marker="+",
    s=100
)

ax.set_title(
    f"Regiões Permanentemente Sombreadas - Shackleton (azul = PSR)\n"
    f"Fração de PSR em {raio_metrica_m / 1000:.0f} km: {fracao_psr:.1f} %"
)
ax.set_xlabel("Distância Leste/Oeste (km)")
ax.set_ylabel("Distância Norte/Sul (km)")

plt.tight_layout()
plt.show()