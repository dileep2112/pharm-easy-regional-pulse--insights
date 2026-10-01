"""
clean_data.py -- PharmEasy Regional Pulse cleaning pipeline (Part 1).

Loads pharmeasy_orders_raw.csv and produces a clean, validated DataFrame
through a fixed, ordered sequence of fixes:

    1. Remove exact duplicate rows (all 8 columns identical).
    2. Normalize the `region` column (strip + title-case) so every raw
       string variant collapses onto one of the 9 canonical region names.
    3. Impute missing `category` using an exact product -> category
       lookup built from the non-missing rows.
    4. Impute missing `profit_inr` using each category's mean profit
       margin (profit_inr / sales_inr) computed from that category's
       non-missing rows.

Also implements validate_schema(), a small reusable schema-validation
gate used both here and by later pipeline stages.

Run directly (`python3 clean_data.py`) to execute the full pipeline,
print a log of what was fixed, write orders_clean.csv, and demonstrate
both the "validated" and "blocked_schema" paths of validate_schema().
"""

import pandas as pd

RAW_PATH = "pharmeasy_orders_raw.csv"
CLEAN_PATH = "orders_clean.csv"
ALL_COLUMNS = [
    "order_id", "order_date", "region", "category", "product",
    "quantity", "sales_inr", "profit_inr",
]
REQUIRED_COLUMNS = ALL_COLUMNS  # every column is required for this dataset


def validate_schema(df: pd.DataFrame, required_columns: list) -> dict:
    """
    Check that every column in `required_columns` is present in `df`.

    Returns a dict with:
        status: "validated" if nothing is missing, else "blocked_schema"
        row_count: number of rows in df
        missing_columns: list of required columns not found in df
    """
    missing = [c for c in required_columns if c not in df.columns]
    status = "blocked_schema" if missing else "validated"
    return {
        "status": status,
        "row_count": len(df),
        "missing_columns": missing,
    }


def remove_exact_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Remove rows that are identical across all 8 raw columns."""
    before = len(df)
    deduped = df.drop_duplicates(subset=ALL_COLUMNS, keep="first").reset_index(drop=True)
    removed = before - len(deduped)
    return deduped, removed


def normalize_region(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace and title-case the region column."""
    df = df.copy()
    df["region"] = df["region"].astype(str).str.strip().str.title()
    return df


def impute_missing_category(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Build an exact product -> category lookup from rows where category
    is known, then use it to fill every row where category is missing.
    """
    df = df.copy()
    is_missing = df["category"].isna() | (df["category"].astype(str).str.strip() == "")
    n_missing = int(is_missing.sum())

    known = df.loc[~is_missing, ["product", "category"]].drop_duplicates()
    lookup = dict(zip(known["product"], known["category"]))

    def fill(row):
        if is_missing.loc[row.name]:
            return lookup.get(row["product"], row["category"])
        return row["category"]

    df["category"] = df.apply(fill, axis=1)
    return df, n_missing


def impute_missing_profit(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    For each category, compute the mean profit margin
    (profit_inr / sales_inr) over that category's non-missing rows,
    then fill missing profit_inr as sales_inr * category_mean_margin.
    """
    df = df.copy()
    profit_numeric = pd.to_numeric(df["profit_inr"], errors="coerce")
    is_missing = profit_numeric.isna()
    n_missing = int(is_missing.sum())

    known = df.loc[~is_missing].copy()
    known["margin"] = pd.to_numeric(known["profit_inr"]) / known["sales_inr"]
    mean_margin_by_cat = known.groupby("category")["margin"].mean()

    filled_profit = profit_numeric.copy()
    for idx in df.index[is_missing]:
        cat = df.loc[idx, "category"]
        margin = mean_margin_by_cat.get(cat)
        sales = df.loc[idx, "sales_inr"]
        filled_profit.loc[idx] = round(float(sales) * float(margin), 2)

    df["profit_inr"] = filled_profit
    return df, n_missing


def load_and_clean(raw_path: str = RAW_PATH) -> dict:
    """
    Run the full cleaning pipeline end-to-end and return a dict with the
    cleaned DataFrame plus a log of what happened at each step (used by
    data_quality_report.md and by the console printout below).
    """
    raw_df = pd.read_csv(raw_path, dtype={"category": "object", "profit_inr": "object"})
    log = {"raw_rows": len(raw_df)}

    df, dup_removed = remove_exact_duplicates(raw_df)
    log["duplicates_removed"] = dup_removed
    log["rows_after_dedup"] = len(df)

    raw_region_variants = raw_df["region"].nunique()
    df = normalize_region(df)
    log["raw_region_variants"] = int(raw_region_variants)
    log["canonical_regions_after_normalize"] = int(df["region"].nunique())

    df, cat_missing = impute_missing_category(df)
    log["category_missing_imputed"] = cat_missing

    df, profit_missing = impute_missing_profit(df)
    log["profit_missing_imputed"] = profit_missing

    df["quantity"] = pd.to_numeric(df["quantity"])
    df["sales_inr"] = pd.to_numeric(df["sales_inr"])
    df["profit_inr"] = pd.to_numeric(df["profit_inr"]).round(2)

    log["remaining_missing_category"] = int(
        (df["category"].isna() | (df["category"].astype(str).str.strip() == "")).sum()
    )
    log["remaining_missing_profit"] = int(df["profit_inr"].isna().sum())

    return {"df": df, "log": log}


if __name__ == "__main__":
    result = load_and_clean()
    df, log = result["df"], result["log"]

    print("=== PharmEasy Regional Pulse: cleaning pipeline log ===")
    print(f"Raw rows loaded:                    {log['raw_rows']}")
    print(f"Exact duplicate rows removed:        {log['duplicates_removed']}")
    print(f"Rows after de-duplication:           {log['rows_after_dedup']}")
    print(f"Distinct raw region strings:         {log['raw_region_variants']}")
    print(f"Canonical regions after normalize:   {log['canonical_regions_after_normalize']}")
    print(f"Missing category values imputed:     {log['category_missing_imputed']}")
    print(f"Missing profit_inr values imputed:   {log['profit_missing_imputed']}")
    print(f"Remaining missing category:          {log['remaining_missing_category']}")
    print(f"Remaining missing profit_inr:        {log['remaining_missing_profit']}")

    df.to_csv(CLEAN_PATH, index=False)
    print(f"\nWrote cleaned dataset -> {CLEAN_PATH} ({len(df)} rows)")

    print("\n=== validate_schema() on clean data ===")
    result_ok = validate_schema(df, REQUIRED_COLUMNS)
    print(result_ok)

    print("\n=== validate_schema() on deliberately broken copy (drop 'profit_inr') ===")
    broken = df.drop(columns=["profit_inr"])
    result_broken = validate_schema(broken, REQUIRED_COLUMNS)
    print(result_broken)
