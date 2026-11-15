"""Retrieve lunar datasets without overwriting existing local copies."""
from pathlib import Path

import requests

from src.terrain.config import (
    AVGVISIB_PATH, AVGVISIB_URL, DATA_DIRECTORY,
    LOLA_BASE_URL, LOLA_DATASET_NAME,
)


def download_file(url: str, destination: Path, timeout: int = 60) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and destination.stat().st_size > 0:
        return destination
    temporary = destination.with_name(destination.name + ".part")
    try:
        with requests.get(url, stream=True, timeout=timeout) as response:
            response.raise_for_status()
            with temporary.open("wb") as output:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        output.write(chunk)
        if temporary.stat().st_size == 0:
            raise OSError(f"Empty download: {url}")
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def download_lola_dataset(dataset_name: str = LOLA_DATASET_NAME) -> list[Path]:
    """Download the PDS detached label and binary raster, if absent."""
    return [
        download_file(
            f"{LOLA_BASE_URL}{dataset_name}{extension}",
            DATA_DIRECTORY / f"{dataset_name}{extension}",
        )
        for extension in (".lbl", ".img")
    ]


def download_lunar_inputs() -> list[Path]:
    """Ensure required lunar DEM and mean-illumination files exist."""
    return [*download_lola_dataset(), download_file(AVGVISIB_URL, AVGVISIB_PATH)]
