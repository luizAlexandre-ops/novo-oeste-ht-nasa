import rasterio, numpy as np
import matplotlib.pyplot as plt

caminho = "data/ldem_75s_120m.lbl"

# with rasterio.open(caminho) as src:
#     print("crs:", src.crs, "res:", src.res, "shape:", src.shape, "scales:", src.scales, "offsets:", src.offsets)
#     dem = src.read(1).astype(np.float32)

with rasterio.open(caminho) as src:
    fator = 20
    out_shape = (src.height // fator, src.width // fator)
    dn = src.read(1, out_shape=out_shape, resampling=rasterio.enums.Resampling.average)
    print(src.dtypes, src.nodata)

alt = dn.astype(np.float32) * 0.5
plt.imshow(alt, cmap="terrain"); plt.colorbar(label="m"); plt.show()