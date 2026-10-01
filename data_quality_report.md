# Data Quality Report — PharmEasy Regional Pulse

This report maps every fix applied in `clean_data.py` to the specific
data-quality dimension it addresses. The seven standard dimensions
considered are: **Accuracy, Completeness, Consistency, Timeliness,
Validity, Uniqueness, Relevance.**

## Summary of what was found and fixed

| # | Problem in raw data | Fix applied | Rows affected |
|---|---|---|---|
| 1 | Exact duplicate rows (identical across all 8 columns), caused by copy-paste from multiple source sheets | `drop_duplicates()` on all 8 columns, keep first occurrence | 59 rows removed (2159 → 2100) |
| 2 | Region names typed inconsistently across store-ops teams (16 raw string variants of 9 real regions, e.g. `" hyderabad"`, `"HYDERABAD "`, `"Hyderabad"`) | Strip whitespace, title-case | 16 raw variants → 9 canonical names |
| 3 | Missing `category` (blank cells) | Exact product→category lookup built from non-missing rows, applied to missing rows | 48 rows imputed |
| 4 | Missing `profit_inr` (didn't make it through the nightly sync) | Per-category mean profit margin (profit_inr / sales_inr) applied to sales_inr for that row | 94 rows imputed |

## Mapping to data-quality dimensions

1. **Uniqueness** — Removing the 59 exact-duplicate rows directly
   addresses uniqueness: each real order should appear exactly once in
   `orders_clean`, and duplicate rows would have double-counted sales
   and profit for the affected regions/months.

2. **Consistency** — Normalizing the `region` column (whitespace
   stripping + title-casing) addresses consistency: the same physical
   region ("Hyderabad") was being recorded as up to 3 different string
   values depending on which store-ops team's export it came from.
   Without this fix, GROUP BY region in Part 2 would silently split one
   region's numbers across several rows.

3. **Completeness** — Imputing the 48 missing `category` values and 94
   missing `profit_inr` values addresses completeness: every row now
   has a value in every required column, so no order is silently
   dropped or excluded from category- or profit-based metrics just
   because one field failed to sync.

4. **Accuracy** — The imputation *methods* themselves are chosen to
   preserve accuracy as much as possible given missing data: category
   is recovered via an **exact** deterministic product→category
   lookup (every product belongs to exactly one category, so this is
   not a guess), and missing profit is estimated using that specific
   category's own observed mean margin rather than a single global
   average, keeping the imputed figure close to what the true value
   would plausibly have been.

5. **Validity** — `validate_schema()` addresses validity: it enforces
   that the dataset conforms to the expected shape (all 8 required
   columns present) before any downstream metric is computed,
   returning `"blocked_schema"` and refusing to proceed if a column is
   missing, rather than allowing a malformed feed to silently pass
   through to the metrics engine.

6. **Timeliness** — Not directly remediated by a cleaning step in this
   dataset (all rows do carry an `order_date` within the expected
   April–June 2026 window), but it is the reason `profit_inr` went
   missing in the first place: the brief states these gaps are caused
   by figures that "didn't make it through the nightly sync," i.e. a
   timeliness failure upstream that this pipeline compensates for
   through imputation rather than preventing at the source.

7. **Relevance** — All 8 columns retained (`order_id`, `order_date`,
   `region`, `category`, `product`, `quantity`, `sales_inr`,
   `profit_inr`) are relevant to the region-level performance metrics
   this pipeline exists to produce; no columns were dropped as
   irrelevant, and `regions_master.csv`'s `state`/`tier` columns are
   kept because they support the regional-lead framing used in Parts
   3–4.

## Net result

Raw file: 2159 rows, 16 region string variants, 94 missing
`profit_inr`, 48 missing `category`.

Clean file (`orders_clean.csv`): 2100 rows, 9 canonical region names,
0 missing `profit_inr`, 0 missing `category` — validated by
`validate_schema()` returning `status: "validated"`.
