
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from scipy.ndimage import label
from src.terrain.config import OUTPUT_DIRECTORY
from src.terrain.site import build_lunar_site, build_earth_site
from src.terrain.locations import (
    SHACKLETON_CRATER,
    HAWORTH_CRATER,
    EARTH_ANALOG_SITES,
)

EXPECTED_PIXEL_SIZE_M = 120.0
MAX_MISSING_FRACTION = 0.01
PIXEL_SIZE_TOLERANCE_M = 1.0

def validate_elevation_patterns(site):
    elevation = site.analysis.elevation_meters
    valid = np.isfinite(elevation)

    print(f"\nPADRÕES DE ELEVAÇÃO: {site.name}")

    if not valid.any():
        print("Sem pixels válidos.")
        return

    values = elevation[valid]

    # Verifica a quantidade de zeros
    zero_mask = valid & (elevation == 0)
    zero_count = np.count_nonzero(zero_mask)

    print(f"Pixels com elevação zero: {zero_count}")
    print(f"Porcentagem de zeros: {zero_count / valid.sum():.2%}")

    # Verifica o maior bloco conectado de zeros
    labeled, count = label(zero_mask)

    if count > 0:
        sizes = np.bincount(labeled.ravel())[1:]
        largest = sizes.max()

        print(f"Maior região conectada de zeros: {largest} pixels")
        print(
            f"Área aproximada: "
            f"{largest * site.pixel_size_meters**2 / 1e6:.2f} km²"
        )

    # Check concentrations of values near the median
    median = np.median(values)
    near_median = np.abs(values - median) < 1.0

    print(
        f"Pixels a menos de 1 m da mediana: "
        f"{near_median.mean():.2%}"
    )

    # Most frequent exact elevation values
    unique, counts = np.unique(values, return_counts=True)
    top_indices = np.argsort(counts)[-5:][::-1]

    print("Valores de elevação mais frequentes:")

    for index in top_indices:
        print(
            f"  {unique[index]:.2f} m: "
            f"{counts[index]} pixels"
        )





def plot_elevation_diagnostics(site, output_directory):
    elevation = site.analysis.elevation_meters
    valid = np.isfinite(elevation)

    if not valid.any():
        return

    median = np.median(elevation[valid])

    zero_mask = valid & (elevation == 0)
    flat_mask = valid & (np.abs(elevation - median) < 1.0)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    image = axes[0].imshow(elevation, cmap="terrain")
    axes[0].set_title("Elevação (m)")
    fig.colorbar(image, ax=axes[0], shrink=0.75)

    axes[1].imshow(zero_mask, cmap="gray", vmin=0, vmax=1)
    axes[1].set_title("Pixels com elevação zero")

    axes[2].imshow(flat_mask, cmap="gray", vmin=0, vmax=1)
    axes[2].set_title("Pixels próximos da mediana (±1 m)")

    for ax in axes:
        ax.set_xlabel("Coluna")
        ax.set_ylabel("Linha")

    fig.suptitle(site.name)
    fig.tight_layout()

    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    filename = site.name.lower().replace(" ", "_")

    fig.savefig(
        output_directory / f"{filename}_diagnostics.png",
        dpi=150,
    )
    plt.close(fig)


def validate_site(site):
    elevation = site.analysis.elevation_meters
    slope = site.analysis.metrics.slope_degrees
    profile = site.analysis.roughness_profile

    issues = []

    print(f"\n{'=' * 65}")
    print(f"VALIDANDO: {site.name}")
    print(f"{'=' * 65}")

    # 1. Spatial resolution
    pixel_size = float(site.pixel_size_meters)
    print(f"Resolução: {pixel_size:.3f} m/pixel")

    if not np.isfinite(pixel_size) or pixel_size <= 0:
        issues.append("Spatial resolution inválida.")
    elif abs(pixel_size - EXPECTED_PIXEL_SIZE_M) > PIXEL_SIZE_TOLERANCE_M:
        issues.append(
            f"Resolução diferente da esperada: {EXPECTED_PIXEL_SIZE_M} m."
        )

    # 2. Invalid pixels
    valid_mask = np.isfinite(elevation)
    valid_count = np.count_nonzero(valid_mask)
    total_count = elevation.size
    missing_fraction = 1 - valid_count / total_count

    print(f"Dimensões: {elevation.shape}")
    print(f"Pixels válidos: {valid_count}/{total_count}")
    print(f"Invalid pixels: {missing_fraction:.2%}")

    if valid_count == 0:
        issues.append("Nenhum pixel de elevação válido.")
    elif missing_fraction > MAX_MISSING_FRACTION:
        issues.append(
            "Mais de 1% dos pixels de elevação são inválidos."
        )

    if valid_count > 0:
        values = elevation[valid_mask]

        # 3. Elevation statistics
        print("\nELEVAÇÃO")
        print(f"Mínima: {np.min(values):.2f} m")
        print(f"Máxima: {np.max(values):.2f} m")
        print(f"Mediana: {np.median(values):.2f} m")
        print(f"P01: {np.percentile(values, 1):.2f} m")
        print(f"P99: {np.percentile(values, 99):.2f} m")

        relief = np.percentile(values, 99) - np.percentile(values, 1)
        print(f"Relevo P99-P01: {relief:.2f} m")

        if not np.isfinite(relief) or relief < 0:
            issues.append("Relevo calculado inválido.")

        # Check large differences between neighboring cells
        dx = np.abs(np.diff(elevation, axis=1))
        dy = np.abs(np.diff(elevation, axis=0))

        differences = np.concatenate([
            dx[np.isfinite(dx)],
            dy[np.isfinite(dy)],
        ])

        if differences.size:
            print(
                f"Variação entre pixels P99: "
                f"{np.percentile(differences, 99):.2f} m"
            )
            print(
                f"Variação máxima entre pixels: "
                f"{np.max(differences):.2f} m"
            )

    # 4. Declividade
    print("\nDECLIVIDADE")

    if slope.shape != elevation.shape:
        issues.append("Declividade e elevação têm dimensões diferentes.")

    finite_slope = slope[np.isfinite(slope)]

    if finite_slope.size == 0:
        issues.append("Nenhum valor válido de declividade.")
    else:
        print(f"Mediana: {np.median(finite_slope):.2f}°")
        print(f"P90: {np.percentile(finite_slope, 90):.2f}°")
        print(f"Máxima: {np.max(finite_slope):.2f}°")

        if np.any(finite_slope < 0) or np.any(finite_slope >= 90):
            issues.append("Declividades fora do intervalo [0, 90).")

        if finite_slope.size != total_count:
            issues.append("Existem valores inválidos na declividade.")

    # 5. Rugosidade
    print("\nRUGOSIDADE")

    baselines = np.asarray(profile.baseline_meters)
    rms_values = np.asarray(profile.rms_deviation_meters)

    if len(baselines) != len(rms_values):
        issues.append("Baselines e valores RMS possuem tamanhos diferentes.")
    elif len(baselines) == 0:
        issues.append("Perfil de rugosidade vazio.")
    else:
        for baseline, rms in zip(baselines, rms_values):
            print(f"Baseline {baseline:.0f} m: RMS = {rms:.4f} m")

        if np.any(~np.isfinite(rms_values)):
            issues.append("Existem valores RMS inválidos.")

        if np.any(rms_values < 0):
            issues.append("Existem valores RMS negativos.")

        if np.any(baselines <= 0) or np.any(~np.isfinite(baselines)):
            issues.append("Existem baselines inválidas.")

    # Validation result
    print("\nRESULTADO")

    if issues:
        print("ATENÇÃO: problemas ou condições para investigar:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("OK: nenhuma inconsistência detectada nas verificações.")

    return {
        "name": site.name,
        "pixel_size_m": pixel_size,
        "missing_fraction": missing_fraction,
        "issues": issues,
    }


if __name__ == "__main__":
    lunar_locations = [
        SHACKLETON_CRATER,
        HAWORTH_CRATER,
    ]

    sites = []

    for location in lunar_locations:
        sites.append(build_lunar_site(location))

    for location in EARTH_ANALOG_SITES:
        sites.append(build_earth_site(location))

    results = []

    for site in sites:
        results.append(validate_site(site))

        validate_elevation_patterns(site)

        if site.name in ("Haughton Crater", "Atacama"):
            plot_elevation_diagnostics(
                site,
                OUTPUT_DIRECTORY / "diagnostics",
            )

    print(f"\n{'=' * 65}")
    print("RESUMO FINAL")
    print(f"{'=' * 65}")

    for result in results:
        status = "OK" if not result["issues"] else "ATENÇÃO"
        print(
            f"{result['name']}: {status} | "
            f"Resolução: {result['pixel_size_m']:.2f} m | "
            f"Inválidos: {result['missing_fraction']:.2%}"
        )


