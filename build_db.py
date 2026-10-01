"""
build_db.py -- PharmEasy Regional Pulse (Part 2).

Loads Part 1's clean data into a local SQLite database, pharmeasy.db,
as two tables:

    regions_master  (from regions_master.csv, 10 rows)
    orders_clean    (from orders_clean.csv, produced by clean_data.py, 2100 rows)

Run: python3 build_db.py
"""

import sqlite3
import pandas as pd
from clean_data import load_and_clean, CLEAN_PATH

DB_PATH = "pharmeasy.db"
REGIONS_MASTER_PATH = "regions_master.csv"


def build_database(db_path: str = DB_PATH) -> None:
    # Regenerate the clean dataset fresh from the raw file every time,
    # so build_db.py never depends on a stale orders_clean.csv on disk.
    result = load_and_clean()
    orders_df = result["df"]
    orders_df.to_csv(CLEAN_PATH, index=False)

    regions_df = pd.read_csv(REGIONS_MASTER_PATH)

    conn = sqlite3.connect(db_path)
    try:
        regions_df.to_sql("regions_master", conn, if_exists="replace", index=False)
        orders_df.to_sql("orders_clean", conn, if_exists="replace", index=False)
        conn.commit()

        cur = conn.cursor()
        n_regions = cur.execute("SELECT COUNT(*) FROM regions_master").fetchone()[0]
        n_orders = cur.execute("SELECT COUNT(*) FROM orders_clean").fetchone()[0]
        print(f"Built {db_path}")
        print(f"  regions_master: {n_regions} rows")
        print(f"  orders_clean:   {n_orders} rows")
    finally:
        conn.close()


if __name__ == "__main__":
    build_database()
