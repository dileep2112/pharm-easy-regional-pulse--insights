"""
queries.py -- PharmEasy Regional Pulse (Part 2).

JOIN validation against pharmeasy.db, plus the region x month sales
metrics and Month-on-Month growth calculation. Run directly to print
every required check.

Run: python3 queries.py   (after python3 build_db.py)
"""

import sqlite3
from collections import defaultdict

DB_PATH = "pharmeasy.db"


def get_conn():
    return sqlite3.connect(DB_PATH)


# ---------------------------------------------------------------------------
# Task 2.2 -- JOIN validation
# ---------------------------------------------------------------------------

def row_count_check(conn):
    left = conn.execute(
        "SELECT COUNT(*) FROM regions_master r LEFT JOIN orders_clean o ON r.region = o.region"
    ).fetchone()[0]
    inner = conn.execute(
        "SELECT COUNT(*) FROM regions_master r INNER JOIN orders_clean o ON r.region = o.region"
    ).fetchone()[0]
    return left, inner


def duplicate_key_check(conn):
    rows = conn.execute(
        "SELECT order_id, COUNT(*) as n FROM orders_clean GROUP BY order_id HAVING COUNT(*) > 1"
    ).fetchall()
    return rows


def null_check(conn):
    """
    For each region, compare COUNT(*) vs COUNT(o.order_id) under a
    LEFT JOIN. For a zero-order region (Kurnool), COUNT(*) wrongly
    reports 1 (it counts the single null-padded row produced by the
    LEFT JOIN), while COUNT(o.order_id) correctly reports 0, since
    COUNT() on a column skips NULLs.
    """
    q = """
    SELECT r.region,
           COUNT(*) AS count_star,
           COUNT(o.order_id) AS count_order_id
    FROM regions_master r
    LEFT JOIN orders_clean o ON r.region = o.region
    GROUP BY r.region
    ORDER BY r.region
    """
    return conn.execute(q).fetchall()


def per_region_order_counts(conn):
    q = """
    SELECT r.region, COUNT(o.order_id) AS order_count
    FROM regions_master r
    LEFT JOIN orders_clean o ON r.region = o.region
    GROUP BY r.region
    ORDER BY order_count ASC
    """
    return conn.execute(q).fetchall()


# ---------------------------------------------------------------------------
# Task 2.3 -- Region x month metrics and MoM growth
# ---------------------------------------------------------------------------

def region_month_sales(conn):
    q = """
    SELECT region, substr(order_date, 1, 7) AS month, SUM(sales_inr) AS total_sales
    FROM orders_clean
    GROUP BY region, month
    ORDER BY region, month
    """
    rows = conn.execute(q).fetchall()
    data = defaultdict(dict)
    for region, month, total_sales in rows:
        data[region][month] = round(total_sales, 2)
    return data


def compute_mom_growth(region_month: dict, month_a: str, month_b: str) -> dict:
    """(month_b - month_a) / month_a * 100 for every region, using 0 when
    month_a is 0 or missing (avoids ZeroDivisionError)."""
    changes = {}
    for region, months in region_month.items():
        prev = months.get(month_a, 0)
        curr = months.get(month_b, 0)
        changes[region] = 0.0 if prev == 0 else round((curr - prev) / prev * 100, 2)
    return changes


if __name__ == "__main__":
    conn = get_conn()

    print("=== Task 2.2 — Row-count check (LEFT vs INNER JOIN) ===")
    left, inner = row_count_check(conn)
    print(f"LEFT JOIN row count:  {left}")
    print(f"INNER JOIN row count: {inner}")
    print(f"Delta: {left - inner} row(s) -- this is Kurnool's null-padded row (zero orders)\n")

    print("=== Task 2.2 — Duplicate-key check (order_id appearing >1 time) ===")
    dups = duplicate_key_check(conn)
    print(f"Rows returned: {len(dups)} (expected 0 -- no duplicate order_ids)\n")

    print("=== Task 2.2 — COUNT(*) vs COUNT(order_id) per region (LEFT JOIN) ===")
    for region, count_star, count_order_id in null_check(conn):
        marker = "  <-- disagreement (zero-order region)" if count_star != count_order_id else ""
        print(f"{region:<15} COUNT(*)={count_star:<4} COUNT(order_id)={count_order_id:<4}{marker}")
    print()

    print("=== Task 2.2 — Per-region order counts (LEFT JOIN + GROUP BY, ascending) ===")
    for region, order_count in per_region_order_counts(conn):
        print(f"{region:<15} {order_count}")
    print()

    print("=== Task 2.3 — Region x month total sales_inr ===")
    region_month = region_month_sales(conn)
    for region in sorted(region_month):
        print(f"{region:<15} {region_month[region]}")
    print()

    print("=== Task 2.3 — MoM growth: April -> May ===")
    apr_may = compute_mom_growth(region_month, "2026-04", "2026-05")
    for region in sorted(apr_may):
        print(f"{region:<15} {apr_may[region]:+.2f}%")
    print()

    print("=== Task 2.3 — MoM growth: May -> June ===")
    may_jun = compute_mom_growth(region_month, "2026-05", "2026-06")
    for region in sorted(may_jun):
        print(f"{region:<15} {may_jun[region]:+.2f}%")

    conn.close()
