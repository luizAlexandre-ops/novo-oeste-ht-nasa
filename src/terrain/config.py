import numpy as np
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIRECTORY = PROJECT_ROOT / "data"
OUTPUT_DIRECTORY = PROJECT_ROOT / "outputs"

PSR_PATH = DATA_DIRECTORY / "LPSR_80S_20MPP_ADJ.TIF"
DIVINER_TABLE_PATH = DATA_DIRECTORY / "dlre_prp_south.tab"
DIVINER_CACHE_PATH = DATA_DIRECTORY / "diviner_south_cache.npz"
DIVINER_MAX_DISTANCE_METERS = 400.0
LOLA_DATASET_NAME = "ldem_75s_120m"
LOLA_LABEL_PATH = DATA_DIRECTORY / f"{LOLA_DATASET_NAME}.lbl"
AVGVISIB_PATH = DATA_DIRECTORY / "AVGVISIB_85S_060M_201608.TIF"


MOON_RADIUS_METERS = 1_737_400.0
METERS_PER_DEGREE_LATITUDE = 111_320.0

LOLA_BASE_URL = (
    "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/"
    "lrolol_1xxx/data/lola_gdr/polar/img/"
)

# elevation_meters = raw_value * scale (SCALING_FACTOR from the .LBL file)

COPERNICUS_TILE_URL_TEMPLATE = (
    "https://copernicus-dem-30m.s3.amazonaws.com/{tile_name}/{tile_name}.tif"
)

DEFAULT_HALF_WIDTH_METERS = 20_000
DEFAULT_ROUGHNESS_WINDOW_METERS = 150.0

DEFAULT_BASELINES_METERS = (120.0, 240.0, 480.0, 960.0, 1920.0)

ROUGHNESS_MAP_BASELINE_METERS = 240.0
ROUGHNESS_MAP_WINDOW_METERS = 1200.0


LANDING_SLOPE_LIMITS_DEGREES = (5.0, 10.0)

LIT_THRESHOLDS_PERCENT = (10.0, 20.0, 30.0)
LANDABLE_LIT_THRESHOLD_PERCENT = 20.0       # usado na métrica combinada pouso + Sol
SUNLIT_MAX_PSR_FRACTION = 0.1    
              # abaixo disso o pixel conta como fora do PSR
SLOPE_HISTOGRAM_BINS = np.arange(0, 46, 1.0)

MIN_RMS_METERS = 1e-6