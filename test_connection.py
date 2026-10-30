import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()          # reads the .env file in this folder

try:
    conn = psycopg2.connect(
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
    )
    cur = conn.cursor()
    cur.execute("SELECT version();")
    print("Connected!")
    print(cur.fetchone()[0])
    conn.close()
except Exception as err:
    print("Could not connect:", err)