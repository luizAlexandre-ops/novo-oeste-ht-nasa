import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from matplotlib.collections import PolyCollection
from matplotlib.patches import Circle


caminho = "data/dlre_prp_south.tab"

latitude = -89.9
longitude = 129.8

meia_largura_km = 20     # tamanho do recorte exibido (quadrado)
margem_km = 1            # margem para incluir triângulos que cruzam a borda
raio_metrica_km = 10     # raio usado nas métricas
limite_gelo_k = 110      # abaixo disso a superfície retém gelo de água

R_LUA_KM = 1737.4

# Centro de Shackleton no referencial da tabela (x, y em km, centrado na Lua)
lat_r, lon_r = np.radians(latitude), np.radians(longitude)
x0 = R_LUA_KM * np.cos(lat_r) * np.cos(lon_r)
y0 = R_LUA_KM * np.cos(lat_r) * np.sin(lon_r)

# --- Leitura em pedaços: a tabela tem ~2,9 milhões de triângulos (~600 MB) ---
# O arquivo tem colunas de largura fixa (posições dadas no rótulo .xml).
# Colunas usadas: vértices (x, y) dos 3 cantos, centro (lon, lat) e temperaturas.
colunas = ["x1", "y1", "x2", "y2", "x3", "y3",
           "clon", "clat", "temp_avg", "temp_max"]
posicoes = [(0, 12), (14, 26), (42, 54), (56, 68), (84, 96), (98, 110),
            (126, 141), (143, 158), (177, 185), (187, 195)]

# Mostra as primeiras linhas cruas, para conferir o formato do arquivo
with open(caminho, "r", errors="replace") as f:
    print("Primeiras linhas do arquivo:")
    for _ in range(3):
        print(repr(f.readline()[:215]))

recortes = []
for pedaco in pd.read_fwf(
    caminho, colspecs=posicoes, header=None, skiprows=1,
    names=colunas, chunksize=500_000
):
    # Qualquer valor não numérico vira NaN e a linha é descartada
    pedaco = pedaco.apply(pd.to_numeric, errors="coerce").dropna()

    cx = (pedaco.x1 + pedaco.x2 + pedaco.x3) / 3
    cy = (pedaco.y1 + pedaco.y2 + pedaco.y3) / 3
    perto = (
        (np.abs(cx - x0) <= meia_largura_km + margem_km)
        & (np.abs(cy - y0) <= meia_largura_km + margem_km)
    )

    pedaco = pedaco[perto].copy()
    pedaco["cx"] = cx[perto]
    pedaco["cy"] = cy[perto]
    recortes.append(pedaco)

dados = pd.concat(recortes, ignore_index=True)

if dados.empty:
    raise ValueError("Nenhum triângulo encontrado perto de Shackleton.")

# Área de cada triângulo projetada no plano polar (km²), usada como peso
dados["area"] = 0.5 * np.abs(
    (dados.x2 - dados.x1) * (dados.y3 - dados.y1)
    - (dados.x3 - dados.x1) * (dados.y2 - dados.y1)
)
dados["dist"] = np.hypot(dados.cx - x0, dados.cy - y0)

print(dados[["temp_avg", "temp_max"]].describe())
print("área mediana por triângulo (km²):", dados.area.median())


# dentro = dados[dados.dist <= raio_metrica_km]

# if dentro.empty:
#     raise ValueError("Nenhum triângulo dentro do raio da métrica.")

# # --- Conferência do referencial: a longitude calculada a partir de (x, y)
# # deve bater com a coluna de longitude da própria tabela ---
# longe_do_polo = dentro[np.hypot(dentro.cx, dentro.cy) > 2]
# lon_calc = np.degrees(np.arctan2(longe_do_polo.cy, longe_do_polo.cx))
# erro_lon = ((lon_calc - longe_do_polo.clon + 180) % 360) - 180
# print(f"Erro mediano de longitude (x, y vs tabela): "
#       f"{np.median(np.abs(erro_lon)):.2f} graus (esperado: perto de 0)")

# # --- Métricas, ponderadas pela área dos triângulos ---
# temp_media = np.average(dentro.temp_avg, weights=dentro.area)
# temp_max_media = np.average(dentro.temp_max, weights=dentro.area)
# fracao_frio = 100 * dentro.area[dentro.temp_max < limite_gelo_k].sum() / dentro.area.sum()

# print("Triângulos no recorte:", len(dados))
# print("Triângulos dentro do raio:", len(dentro))
# print(f"Área coberta: {dentro.area.sum():.0f} km² "
#       f"(círculo ideal: {np.pi * raio_metrica_km ** 2:.0f} km²)")
# print(f"Temperatura média anual (2 cm): {temp_media:.1f} K")
# print(f"Temperatura máxima anual (superfície), média: {temp_max_media:.1f} K")
# print(f"Fração da área com máxima < {limite_gelo_k} K: {fracao_frio:.2f} %")

# # --- Visualização ---
# # Cada triângulo da malha é desenhado com seus 3 vértices reais.
# # Mesma orientação dos rasters polares (x = ρ·sen λ, y = ρ·cos λ)
# vertices = np.stack([
#     np.column_stack([dados.y1 - y0, dados.x1 - x0]),
#     np.column_stack([dados.y2 - y0, dados.x2 - x0]),
#     np.column_stack([dados.y3 - y0, dados.x3 - x0]),
# ], axis=1)

# fig, eixos = plt.subplots(1, 2, figsize=(14, 6.5))

# paineis = [
#     (eixos[0], "temp_avg", "viridis",
#      f"Temperatura média anual (K)\nMédia em {raio_metrica_km} km: {temp_media:.1f} K"),
#     (eixos[1], "temp_max", "magma",
#      f"Temperatura máxima anual (K)\n"
#      f"Área < {limite_gelo_k} K em {raio_metrica_km} km: {fracao_frio:.1f} %"),
# ]

# for ax, coluna, mapa, titulo in paineis:
#     triangulos = PolyCollection(
#         vertices, array=dados[coluna].to_numpy(), cmap=mapa,
#         edgecolors="face", linewidths=0.3
#     )
#     ax.add_collection(triangulos)
#     plt.colorbar(triangulos, ax=ax, label="K")

#     ax.add_patch(
#         Circle((0, 0), raio_metrica_km, fill=False,
#                edgecolor="white", linestyle="--", linewidth=1.2)
#     )
#     ax.scatter(0, 0, color="red", marker="+", s=100)

#     ax.set_xlim(-meia_largura_km, meia_largura_km)
#     ax.set_ylim(-meia_largura_km, meia_largura_km)
#     ax.set_aspect("equal")
#     ax.set_facecolor("#2b2b2b")
#     ax.set_title(titulo)
#     ax.set_xlabel("Distância Leste/Oeste (km)")
#     ax.set_ylabel("Distância Norte/Sul (km)")

# fig.suptitle("Temperatura (Diviner PRP) - Shackleton")
# plt.tight_layout()
# plt.show()