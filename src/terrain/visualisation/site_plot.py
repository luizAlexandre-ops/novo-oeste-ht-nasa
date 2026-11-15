from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.terrain.site import Site


def plot_site(site: Site, save_path: Path | None = None, show: bool = True):
    metrics = site.analysis.metrics
    roughness_vmax = float(np.nanpercentile(metrics.roughness_meters, 98))
    panels = [
        ("Elevation (m)", site.analysis.elevation_meters, "cividis", {}),
        ("Slope (°)", metrics.slope_degrees, "magma", {"vmin": 0, "vmax": 40}),
        ("Roughness (m)", metrics.roughness_meters, "viridis", {"vmin": 0, "vmax": roughness_vmax}),
        ("Mean solar visibility (%)", site.illumination_percent, "inferno", {"vmin": 0, "vmax": 100}),
    ]
    panels = [panel for panel in panels if np.isfinite(panel[1]).any()]

    figure, axes = plt.subplots(
        1, len(panels), figsize=(5 * len(panels), 5.5),
        constrained_layout=True, squeeze=False,
    )
    for axis, (label, data, cmap, limits) in zip(axes[0], panels):
        image = axis.imshow(data, extent=site.extent_km, origin="upper", cmap=cmap, **limits)
        figure.colorbar(image, ax=axis, label=label, shrink=0.8)
        axis.scatter(0, 0, color="cyan", marker="+", s=40, linewidths=1)
        axis.set_title(label)
        axis.set_xlabel("X (km)")
        axis.set_ylabel("Y (km)")
    figure.suptitle(site.name)

    if save_path is not None:
        figure.savefig(save_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    return figure