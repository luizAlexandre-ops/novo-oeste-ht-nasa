from pathlib import Path

import requests

from src.terrain.config import DATA_DIRECTORY, LOLA_BASE_URL, LOLA_DATASET_NAME


def download_file(url: str, destination_directory: Path = DATA_DIRECTORY) -> Path:
    destination_directory.mkdir(parents=True, exist_ok=True)
    destination_path = destination_directory / url.split("/")[-1]
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(destination_path, "wb") as output_file:
            for chunk in response.iter_content(chunk_size=8192):
                output_file.write(chunk)
    return destination_path


def download_lola_dataset(dataset_name: str = LOLA_DATASET_NAME) -> list[Path]:
    """Download the .lbl (label) and .img (data) files of a LOLA polar LDEM."""
    return [
        download_file(f"{LOLA_BASE_URL}{dataset_name}{extension}")
        for extension in (".lbl", ".img")
    ]
