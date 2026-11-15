
import numpy as np
from pyproj import CRS, Transformer
import rasterio
from scripts.plot_lunar_comparason import plot_site
from src.terrain import site
from src.terrain.analysis.roughness import compute_roughness_profile, rms_deviation_map
from src.terrain.config import AVGVISIB_PATH, LOLA_LABEL_PATH, DATA_DIRECTORY
from src.terrain.datasets import lola
from src.terrain.datasets.lola import crop_lola_window, lola_elevation_meters
from src.terrain.locations import EARTH_ANALOG_SITES, HAWORTH_CRATER, SHACKLETON_CRATER
from src.terrain.site import build_lunar_site, build_earth_site
from src.terrain.analysis.signature import build_signature, slope_distance

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


# site = build_lunar_site(SHACKLETON_CRATER)
# print(site.analysis.elevation_meters.shape, site.illumination_percent.shape)  # iguais
# print(np.nanmin(site.illumination_percent), np.nanmax(site.illumination_percent))
# print(np.isnan(site.illumination_percent).mean())  # fração sem dado
# plot_site(site)

# site = build_lunar_site(SHACKLETON_CRATER)
# r = site.analysis.metrics.roughness_meters
# print(r.shape, np.isfinite(r).mean(), np.nanmin(r), np.nanmax(r))

# rng = np.random.default_rng(0)
# noise = rng.normal(0, 5, (335, 335))
# m = rms_deviation_map(noise, 120.0, 240.0, 1200.0)
# print(np.isfinite(m).mean(), np.nanmean(m)) 


# with rasterio.open(LOLA_LABEL_PATH) as lola, \
#      rasterio.open(DATA_DIRECTORY / "LPSR_80S_20MPP_ADJ.TIF") as psr:
#     print(lola.crs == psr.crs)  # False pode ser só formatação do WKT: compare os dois
#     print(psr.crs, psr.res, psr.bounds, psr.dtypes, psr.nodata)

# moon = CRS.from_proj4("+proj=longlat +R=1737400 +no_defs")
# for crs in (lola.crs, psr.crs):
#     print(Transformer.from_crs(moon, crs, always_xy=True).transform(129.8, -89.9))


# for location in (SHACKLETON_CRATER, HAWORTH_CRATER):
#     site = build_lunar_site(location)
#     psr = site.layers["psr_fraction"]
#     lit = site.illumination_percent
#     ok = np.isfinite(psr) & np.isfinite(lit)
#     in_psr, dark = psr[ok] >= 0.5, lit[ok] <= 1.0
#     print(location.name)
#     print("  AVGVISIB ~0 dentro do PSR:", dark[in_psr].mean())
#     print("  PSR entre pixels escuros :", in_psr[dark].mean())
#     print("  sem dado Diviner:", np.isnan(site.layers["temp_max_k"]).mean())


# for location in EARTH_ANALOG_SITES:
#     site = build_earth_site(location)
#     elevation = site.analysis.elevation_meters
#     print(location.name, elevation.shape, np.isnan(elevation).mean(),
#           np.nanmin(elevation), np.nanmax(elevation))
#     plot_site(site)



# shackleton = build_signature(build_lunar_site(SHACKLETON_CRATER))
# haworth = build_signature(build_lunar_site(HAWORTH_CRATER))

# print(f"{'métrica':30s} {'Shackleton':>12s} {'Haworth':>12s}")
# for key, value in shackleton.scalars.items():
#     print(f"{key:30s} {value:12.3f} {haworth.scalars[key]:12.3f}")
# print("distância de declive:", slope_distance(shackleton, haworth))


# for location in (SHACKLETON_CRATER, HAWORTH_CRATER):
#     site = build_lunar_site(location)
#     lit, psr = site.illumination_percent, site.layers["psr_fraction"]
#     sun = lit[np.isfinite(lit) & (psr < 0.1)]
#     print(location.name, np.percentile(sun, [50, 90, 99, 100]))


# sites = [build_lunar_site(SHACKLETON_CRATER), build_lunar_site(HAWORTH_CRATER)]
# sites += [build_earth_site(location) for location in EARTH_ANALOG_SITES]
# signatures = [build_signature(site) for site in sites]

# # print(f"{'métrica':28s}" + "".join(f"{s.name[:13]:>15s}" for s in signatures))
# # for key in signatures[0].scalars:
# #     row = "".join(f"{s.scalars.get(key, float('nan')):15.3f}" for s in signatures)
# #     print(f"{key:28s}{row}")

# # print()
# # for s in signatures[1:]:
# #     print(f"declive: Shackleton x {s.name:25s} {slope_distance(signatures[0], s):.2f}")


# import matplotlib.pyplot as plt

# fig, ax = plt.subplots(figsize=(7, 5))
# for s in signatures:
#     ax.loglog(s.roughness_baselines_m, s.roughness_rms_m, "o-",
#               label=f"{s.name} (exp={s.scalars['hurst']:.2f})")
# ax.set_xlabel("Baseline (m)")
# ax.set_ylabel("RMS deviation (m)")
# ax.legend()
# plt.show()