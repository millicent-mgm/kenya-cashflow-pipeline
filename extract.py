import logging
import sys
import time
from pathlib import Path

import pandas as pd

from clean_transform import RAW_FILE, DATE_COLS, ID_COLS, TEXT_COLS

REQUIRED_COLS = (DATE_COLS + ID_COLS + TEXT_COLS +
                 ["trx_id", "trx_value_kes", "trx_bsheet_direction", "tot_hh_daysofobs"])

EXPECTED_N_COLS = 58
MIN_ROWS = 400_000
LOG_FILE = Path("logs/pipeline.log")

def setup_logging():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
        force=True,
    )
#fist check for missing files
def extract(path=RAW_FILE):
    log = logging.getLogger("extract")
    start = time.time()
    log.info("Extract started: %s", path)

    if not path.exists():
        log.error("File not found: %s. Download it and put it in data/raw/.", path.resolve())
        sys.exit(1)   
    # checks for an empty file
    if path.stat().st_size == 0:
        log.error("File is empty (0 bytes): %s", path)
        sys.exit(1)

    # reads the file, and stops if it can't be read
    try:
        df = pd.read_csv(path, low_memory=False)
    except Exception as err:
        log.error("Could not read %s as a CSV: %s", path, err)
        sys.exit(1)

        # checks for no rows
    if df.empty:
        log.error("File has column names but no rows: %s", path)
        sys.exit(1)

    # checks for missing columns
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        log.error("Missing required columns: %s", missing)
        sys.exit(1)

#checks for warnings and success message
    if len(df) < MIN_ROWS:
        log.warning("Only %s rows; expected at least %s. Is the download complete?",
                    f"{len(df):,}", f"{MIN_ROWS:,}")
    if len(df.columns) != EXPECTED_N_COLS:
        log.warning("Expected %s columns but found %s. The file layout may have changed.",
                    EXPECTED_N_COLS, len(df.columns))

    log.info("Extract finished: %s rows x %s columns in %.1f seconds",
             f"{len(df):,}", len(df.columns), time.time() - start)
    return df

if __name__ == "__main__":    #  so that extract.py runs as a task in airflow
    setup_logging()
    extract()