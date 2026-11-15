import numpy as np
from src.terrain.analysis.roughness import compute_roughness_profile

rng = np.random.default_rng(0)
size, pixel = 400, 120.0
x, y = np.meshgrid(np.arange(size), np.arange(size))

# 1) Plano inclinado a ~20°: rugosidade deve ser ~0 com detrend
plane = np.tan(np.radians(20)) * pixel * x
print(compute_roughness_profile(plane, pixel).rms_deviation_meters)   # ~0

# 2) Ruído branco: RMS constante com a escala, Hurst ~ 0
noise = rng.normal(0, 5, (size, size))
print(compute_roughness_profile(noise, pixel).hurst_exponent)         # ~0

# 3) Superfície fractal (movimento browniano fracionário): Hurst ~ 0.5-0.9
#    gere via filtro espectral 1/f^(H+1) e confira se o valor recuperado bate

def fractal_surface(size, hurst, rng):
    freq = np.fft.fftfreq(size)
    fx, fy = np.meshgrid(freq, freq)
    radius = np.hypot(fx, fy)
    radius[0, 0] = 1
    amplitude = radius ** -(hurst + 1)
    amplitude[0, 0] = 0
    phase = np.exp(2j * np.pi * rng.random((size, size)))
    return np.real(np.fft.ifft2(amplitude * phase))

for h in (0.3, 0.6, 0.9):
    surface = fractal_surface(512, h, rng)
    print(h, compute_roughness_profile(surface, 120.0).hurst_exponent)