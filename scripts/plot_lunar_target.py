from src.terrain.analysis.terrain import compute_terrain_metrics
from src.terrain.config import (
    DEFAULT_HALF_WIDTH_METERS, LOLA_LABEL_PATH, OUTPUT_DIRECTORY,
)
from src.terrain.datasets.lola import crop_lola_window
from src.terrain.locations import SHACKLETON_CRATER
from src.terrain.visualisation.lunar_view import plot_lunar_target

TARGET = SHACKLETON_CRATER  # try HAWORTH_CRATER

if __name__ == "__main__":
    OUTPUT_DIRECTORY.mkdir(exist_ok=True)

    window = crop_lola_window(
        LOLA_LABEL_PATH,
        TARGET.latitude,
        TARGET.longitude,
        DEFAULT_HALF_WIDTH_METERS,
    )

    metrics = compute_terrain_metrics(
        window.elevation_meters,
        window.pixel_size_meters,
    )

    plot_lunar_target(
        window,
        metrics,
        TARGET.name,
        save_path=OUTPUT_DIRECTORY / f"{TARGET.name.lower()}.png",
    )
