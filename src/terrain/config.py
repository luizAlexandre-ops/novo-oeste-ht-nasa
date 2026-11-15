from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIRECTORY = PROJECT_ROOT / "data"
OUTPUT_DIRECTORY = PROJECT_ROOT / "outputs"

MOON_RADIUS_METERS = 1_737_400.0
METERS_PER_DEGREE_LATITUDE = 111_320.0

LOLA_BASE_URL = (
    "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/"
    "lrolol_1xxx/data/lola_gdr/polar/img/"
)
LOLA_DATASET_NAME = "ldem_75s_120m"
LOLA_LABEL_PATH = DATA_DIRECTORY / f"{LOLA_DATASET_NAME}.lbl"
AVGVISIB_PATH = DATA_DIRECTORY / "AVGVISIB_85S_060M_201608.TIF"
# elevation_meters = raw_value * scale (SCALING_FACTOR from the .LBL file)
LOLA_ELEVATION_SCALE_FACTOR = 0.5

COPERNICUS_TILE_URL_TEMPLATE = (
    "https://copernicus-dem-30m.s3.amazonaws.com/{tile_name}/{tile_name}.tif"
)

DEFAULT_HALF_WIDTH_METERS = 20_000
DEFAULT_ROUGHNESS_WINDOW_METERS = 150.0