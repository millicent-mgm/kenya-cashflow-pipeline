import logging   #writes messages with a time and a level
import os        #reads settings
import sys       #allows to stop the script
import time      #measures how long things take
from pathlib import Path

import pandas as pd
import psycopg2   #talks to postgres SQL
from dotenv import load_dotenv

from extract import setup_logging    #borrows the log setup already wrote in extract.py

load_dotenv()       #reads.env file, where the password is
log = logging.getLogger("load")    #creates the writer i’ll use for messages, labelled load.

PROCESSED = Path("data/processed")  #folder with the 5 csv files

# parent tables first, because other tables point to them
#shows the list of the five tables in the order they’ll be loaded. The order matters because eg, household is from regions
LOAD_ORDER = ["dim_region", "dim_household", "dim_category", "dim_mode", "household_cashflow_clean"]

#allowed flags for quality chcek
ALLOWED_FLAGS = {"bad_date", "balance_record", "cash_on_hand_record", "missing_amount", "non_cash_fee",
                 "balance_sheet_movement", "unknown_direction", "zero_or_negative_amount",
                 "possible_duplicate", "large_shock"}

#this functions counts rows in each csv file
def count_csv_rows(path):
    with open(path, encoding="utf-8") as f:   #opens the file and names it f.with makes sure the file is closed again when done.
        return sum(1 for _ in f) - 1   #goes through the file one line at a time, and adds 1 for each line.-1 removes the 1st line which is column names

#this checks that all the 5 csv files exist
def check_files():
    expected = {}
    for table in LOAD_ORDER:
        path = PROCESSED / f"{table}.csv"
        if not path.exists():
            log.error("Missing file: %s. Run build_tables.py first.", path)
            sys.exit(1)
        expected[table] = count_csv_rows(path)
        log.info("%s: %s rows in the file", table, f"{expected[table]:,}")
    return expected 

#quality check flags
def check_flags():
    path = PROCESSED / "household_cashflow_clean.csv"
    flags = pd.read_csv(path, usecols=["quality_flag"])["quality_flag"].dropna().unique()
    unexpected = set(flags) - ALLOWED_FLAGS  #the labels in my data that are not on the allowed list i.e subtracting from aset
    if unexpected:
        log.error("quality_flag values the database does not allow: %s", sorted(unexpected))
        sys.exit(1)
    log.info("Quality flags OK: %s", sorted(flags))


#add the connecting to postgres function
def connect():
    return psycopg2.connect(
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
    )

#empty the tables so that re-running is safe.if it doesnt empty running is done twice
def empty_tables(cur):
    cur.execute("TRUNCATE TABLE " + ", ".join(f"clean.{t}" for t in LOAD_ORDER))
    log.info("Emptied the five tables")
#the command that runs in sql above is TRUNCATE TABLE clean.dim_region, clean.dim_household, clean.dim_category, clean.dim_mode, clean.household_cashflow_clean


#now after emptying load the csv files
def copy_csv(cur, table, path):
    with open(path, encoding="utf-8", newline="") as f:
        columns = f.readline().strip()
        f.seek(0)
        cur.copy_expert(   #sends the command the file together
            f"COPY clean.{table} ({columns}) FROM STDIN WITH (FORMAT csv, HEADER true)", f) #is PostgreSQL’s bulk-loading command.
        #It reads a whole file in one go, which is far faster than adding rows one by one#

#this now loads the list of tables
def load_tables(cur, tables):
    for table in tables:
        start = time.time()
        copy_csv(cur, table, PROCESSED / f"{table}.csv")
        log.info("Loaded %s in %.1f seconds", table, time.time() - start) 


#lets check whether the data loaded
def verify(cur, expected):
    ok = True
    for table in LOAD_ORDER:
        cur.execute(f"SELECT COUNT(*) FROM clean.{table}")
        loaded = cur.fetchone()[0]
        status = "OK" if loaded == expected[table] else "MISMATCH"  #looks up the file’s row count from the dictionary check_files
        if loaded != expected[table]:
            ok = False
        log.info("%s: file %s | database %s -> %s",
                 table, f"{expected[table]:,}", f"{loaded:,}", status)
    return ok


#main function 
def main():
    setup_logging()
    start = time.time()
    log.info("Load started")
    expected = check_files()
    check_flags()

    try:
        conn = connect()
    except Exception as err:
        log.error("Could not connect to PostgreSQL: %s", err)
        sys.exit(1)

    try:
        with conn:                           # all or nothing
            with conn.cursor() as cur:
                empty_tables(cur)
                load_tables(cur, LOAD_ORDER)
                if not verify(cur, expected):
                    raise RuntimeError("row counts in the database do not match the files")
        log.info("Load finished in %.1f seconds", time.time() - start)
    except Exception as err:
        log.error("Load failed, nothing was changed: %s", err)
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()