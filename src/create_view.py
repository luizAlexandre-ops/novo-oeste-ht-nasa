import rasterio
import numpy as np
import matplotlib.pyplot as plt
from pyproj import CRS, Transformer
from rasterio.windows import Window
from rasterio.plot import plotting_extent
from matplotlib.colors import LightSource

lua = CRS.from_proj4("+proj=longlat +R=1737400 +no_defs")

caminho = "dados/ldem_75s_120m.lbl"

shackletonLat, shackletonLon = -89.9, 129.8

lat_general = -89.9
lon_general = 129.8
MapSize = 50_000


def create_view(src, lat, lon, meia_largura_m=20_000):
    tr = Transformer.from_crs(lua, src.crs, always_xy=True)
    x, y = tr.transform(lon, lat)
    lin, col = src.index(x, y)                   
    n = int(meia_largura_m / src.res[0])
    janela = Window(col - n, lin - n, 2*n, 2*n)
    dn = src.read(1, window=janela)
    return dn.astype("float32") * 0.5, src.window_transform(janela)

with rasterio.open(caminho) as src:
    print("pixel do polo:", src.index(0, 0))     
    alt, tf = create_view(src, lat_general, lon_general, MapSize) 
    #haworth, _ = create_view(src, -87.5, -5.0, 30_000) #cordenadas de haworth crater

ext = plotting_extent(alt, tf)
ext_km = [e / 1000 for e in ext]

ls = LightSource(azdeg=315, altdeg=20)  
hs = ls.hillshade(alt, vert_exag=2, dx=30, dy=30)

fig, ax = plt.subplots(figsize=(8, 8))
ax.imshow(hs, extent=ext_km, cmap="gray")
im = ax.imshow(alt, extent=ext_km, cmap="terrain", alpha=0.5)
plt.colorbar(im, ax=ax, label="Altura (m, rel. à esfera de 1737,4 km)")
ax.set_xlabel("X (km)"); ax.set_ylabel("Y (km)")
ax.set_title("LOLA LDEM 30 m: Shackleton")
plt.show()