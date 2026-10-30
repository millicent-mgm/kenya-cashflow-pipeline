#this scripts reads the .sql file and sends it to PostgreSQL using  .env login.

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

load_dotenv()

if len(sys.argv) != 2:
    print("Usage: python run_sql.py sql/create_tables.sql")
    sys.exit(1)

sql_file = Path(sys.argv[1])
if not sql_file.exists():
    print("File not found:", sql_file)
    sys.exit(1)

conn = psycopg2.connect(
    host=os.getenv("PGHOST"),
    port=os.getenv("PGPORT"),
    dbname=os.getenv("PGDATABASE"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
)
try:
    with conn:                          # saves everything if it works, undoes everything if it fails
        with conn.cursor() as cur:
            cur.execute(sql_file.read_text(encoding="utf-8"))
    print("Ran", sql_file, "successfully")
except Exception as err:
    print("Failed:", err)
    sys.exit(1)
finally:
    conn.close()