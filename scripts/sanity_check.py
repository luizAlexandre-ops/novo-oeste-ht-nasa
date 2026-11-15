
import numpy as np
from scripts.plot_lunar_comparason import plot_site
from src.terrain import site
from src.terrain.analysis.roughness import compute_roughness_profile, rms_deviation_map
from src.terrain.config import AVGVISIB_PATH, LOLA_LABEL_PATH
from src.terrain.datasets.lola import crop_lola_window, lola_elevation_meters
from src.terrain.locations import SHACKLETON_CRATER
from src.terrain.site import build_lunar_site

# rng = np.random.default_rng(0)
# size, pixel = 400, 120.0
# x, y = np.meshgrid(np.arange(size), np.arange(size))

# # 1) Plano inclinado a ~20°: rugosidade deve ser ~0 com detrend
# plane = np.tan(np.radians(20)) * pixel * x
# print(compute_roughness_profile(plane, pixel).rms_deviation_meters)   # ~0

# # 2) Ruído branco: RMS constante com a escala, Hurst ~ 0
# noise = rng.normal(0, 5, (size, size))
# print(compute_roughness_profile(noise, pixel).hurst_exponent)         # ~0

# # 3) Superfície fractal (movimento browniano fracionário): Hurst ~ 0.5-0.9
# #    gere via filtro espectral 1/f^(H+1) e confira se o valor recuperado bate

# def fractal_surface(size, hurst, rng):
#     freq = np.fft.fftfreq(size)
#     fx, fy = np.meshgrid(freq, freq)
#     radius = np.hypot(fx, fy)
#     radius[0, 0] = 1
#     amplitude = radius ** -(hurst + 1)
#     amplitude[0, 0] = 0
#     phase = np.exp(2j * np.pi * rng.random((size, size)))
#     return np.real(np.fft.ifft2(amplitude * phase))

# for h in (0.3, 0.6, 0.9):
#     surface = fractal_surface(512, h, rng)
#     print(h, compute_roughness_profile(surface, 120.0).hurst_exponent)



# w = crop_lola_window(LOLA_LABEL_PATH, -89.9, 129.8, 20_000)
# print(w.scale, w.offset)                  # esperado: 0.5 e talvez 1737400.0 (ou 0.0)
# elev = lola_elevation_meters(w)
# print(np.nanmin(elev), np.nanmax(elev))   # esperado: poucos km negativos a positivos
# print(w.data.shape, w.pixel_size_x)       # ~ (333, 333) e ~120.0

# import rasterio
# with rasterio.open(AVGVISIB_PATH) as d:
#     print(d.crs, d.res, d.shape, d.dtypes, d.scales, d.offsets, d.nodata, d.bounds)


site = build_lunar_site(SHACKLETON_CRATER)
print(site.analysis.elevation_meters.shape, site.illumination_percent.shape)  # iguais
print(np.nanmin(site.illumination_percent), np.nanmax(site.illumination_percent))
print(np.isnan(site.illumination_percent).mean())  # fração sem dado
plot_site(site)

# site = build_lunar_site(SHACKLETON_CRATER)
# r = site.analysis.metrics.roughness_meters
# print(r.shape, np.isfinite(r).mean(), np.nanmin(r), np.nanmax(r))

# rng = np.random.default_rng(0)
# noise = rng.normal(0, 5, (335, 335))
# m = rms_deviation_map(noise, 120.0, 240.0, 1200.0)
# print(np.isfinite(m).mean(), np.nanmean(m)) 