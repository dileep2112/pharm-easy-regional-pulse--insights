# PharmEasy Regional Pulse

A reproducible regional analytics pipeline for a Telugu-states regional desk covering Telangana, Andhra Pradesh, and the Bengaluru hub. The project takes a raw monthly order export through deterministic cleaning, SQL verification, movement flagging, plain-language narrative drafting, human review, and a Streamlit dashboard. The project uses local Python, SQLite, and Streamlit only — no API keys, paid services, or network access are required.

---

## Cover note: the 4-artifact package

### Executive headline

Guntur shows the largest movement in the dataset: revenue increased by **122.19% from April to May**, moving from **₹62,442.27 to ₹138,738.93**, before easing back by **28.11% in June**.

### The four artifacts

Consume the submission in this order:

1. **Streamlit dashboard** (`app.py`) — live data exploration.
2. **CII narrative** (embedded in the dashboard) — what the data means: plain-language insight blocks for flagged regions.
3. **One-page memo** (`memo.md`) — the recommendation.
4. **Presentation storyline** (`presentation_storyline.md`) — how you'd defend it live: executive and regional-manager framing with pushback Q&A.

### Single unverified assumption

`memo.md` flags one assumption upfront: the sales and profit figures recorded in the raw monthly export are accurate at the point of entry (i.e. that store-ops correctly recorded quantities and prices). The cleaning pipeline fixes duplicates, inconsistent region names, and missing category/profit fields, but cannot detect or correct an order that was entered with a wrong price or quantity in the first place.

---

## Quick start

### 1. Install dependencies

    pip install -r requirements.txt

### 2. Run the complete pipeline

    python run_pipeline.py

The pipeline runs all seven stages sequentially using the same Python interpreter through `sys.executable`:

    generate_dataset.py
    clean_data.py
    build_db.py
    queries.py
    metrics_engine.py
    draft_report.py
    review_gate.py

The review-gate test harness can be run on its own with `python review_gate.py`. It exercises approve / edit / reject and appends the results to `audit_log.jsonl`.

Nothing in the production dashboard is auto-approved. Human review is performed from the dashboard through the Insight Narrative section using a reviewer note and the Approve / Edit / Reject controls.

### 3. Launch the dashboard

    streamlit run app.py

The dashboard opens at `http://localhost:8501`. The deployed version is linked under Links below.

---

## Pipeline stages

| Stage | Script | Purpose |
|---|---|---|
| 1 | `generate_dataset.py` | Generate the deterministic raw order export |
| 2 | `clean_data.py` | Remove duplicates, normalize regions, impute missing values, and validate schema |
| 3 | `build_db.py` | Build the SQLite database and master region table |
| 4 | `queries.py` | Validate JOIN behavior and calculate regional/monthly metrics |
| 5 | `metrics_engine.py` | Calculate movement and significance flags with persisted state |
| 6 | `draft_report.py` | Generate CII narrative blocks for flagged regions |
| 7 | `review_gate.py` | Exercise approve / edit / reject review decisions and write the test results to the audit log |
| Dashboard | `app.py` | Present the verified analysis and provide the human review checkpoint |

---

## What the pipeline guarantees

The deterministic pipeline guarantees the following checks:

- Exactly **2,159 raw rows** are generated.
- Exactly **59 exact duplicate rows** are removed.
- Exactly **2,100 clean rows** remain.
- The raw data contains **16 distinct region-name variants**.
- Those variants normalize to **9 canonical active regions**.
- The master region table contains **10 regions**, including **Kurnool** as the zero-order region.
- Exactly **94 missing profit values** are imputed.
- Exactly **48 missing category values** are imputed.
- No unresolved missing profit or category values remain after cleaning.
- No duplicate `order_id` values remain in the clean dataset.
- The SQLite `orders_clean` table contains **2,100 rows**.
- The SQLite `regions_master` table contains **10 rows**.
- The LEFT JOIN validation returns **2,101 rows**.
- The INNER JOIN validation returns **2,100 rows**.
- Kurnool has `COUNT(*) = 1` while `COUNT(order_id) = 0`, demonstrating the zero-order-region behavior.
- Month-over-month movement is calculated deterministically.
- Movement is flagged only when it is **greater than +8% or less than -8%**.
- Exactly **+8% and -8% are not flagged** because the comparison is strictly greater/less than the threshold.
- State is persisted for April, May, and June.
- The expected April→May flag set contains **7 of 9 active regions**.
- Vijayawada and Nellore are not flagged for April→May.
- The expected May→June flag set contains **7 of 9 active regions**.
- Nellore and Bengaluru are not flagged for May→June.
- `draft_report_v1()` generates CII blocks for the union of the **8 unique flagged regions**.
- The human review gate supports **approve / edit / reject**.
- Review decisions are appended to `audit_log.jsonl` with the required fields:
  - `timestamp`
  - `run_id`
  - `region`
  - `decision`
  - `reviewer_note`

---

## Dashboard map

### Insight Narrative

The dashboard starts with CII narrative blocks generated from the verified metrics. Each block can be reviewed by a human using a reviewer note and Approve / Edit / Reject controls.

Review decisions are written to `audit_log.jsonl`, while the current dashboard review status is maintained in Streamlit session state.

### 1. Overview

The Overview section contains three KPI cards:

- **Total Sales**
- **Total Profit**
- **Total Orders** — distinct order count

### 2. Category Revenue Mix

Shows category-level revenue using both a bar chart and a pie chart.

### 3. Regional Performance by Period

Provides regional performance by month with:

- Region
- Period
- Order volume
- Revenue
- Net profit
- Revenue shift
- Review flag

The existing movement and ±8% flagging logic is reused rather than creating a separate dashboard calculation.

### Charts

- **Revenue Trend Across Regions** (line chart)
- **Total sales by region** (bar chart)

The region filter is connected to the regional analysis so that the selected region controls the displayed detail.

---

## Repository map

    pharmeasy-regional-pulse/
    │
    ├── generate_dataset.py
    ├── clean_data.py
    ├── data_quality_report.md
    ├── build_db.py
    ├── queries.py
    ├── metrics_engine.py
    ├── draft_report.py
    ├── memo.md
    ├── review_gate.py
    ├── audit_log.jsonl
    ├── reliability_checklist.md
    ├── app.py
    ├── presentation_storyline.md
    ├── README.md
    ├── requirements.txt
    ├── run_pipeline.py
    │
    ├── pharmeasy_orders_raw.csv
    ├── orders_clean.csv
    ├── regions_master.csv
    ├── pharmeasy.db
    │
    ├── state_2026-04.json
    ├── state_2026-05.json
    ├── state_2026-06.json
    │
    └── .gitignore

---

## Data quality and validation

`clean_data.py` performs deterministic cleaning and schema validation before the data reaches the SQL and metrics stages.

The process handles exact duplicates, inconsistent region names, missing profit, missing category, and schema validation. The resulting clean dataset is then used consistently by the database, metrics engine, narrative generator, and dashboard.

---

## SQLite validation

`build_db.py` creates the SQLite database with `regions_master` and `orders_clean`.

The project explicitly validates LEFT JOIN versus INNER JOIN behavior so that the zero-order Kurnool region remains visible in the master-region analysis rather than disappearing from the reporting layer.

---

## Metrics and flagging

Monthly regional sales are aggregated from the cleaned SQLite data and compared across April→May and May→June.

The significance rule is:

    Movement > +8%  → Flag
    Movement < -8%  → Flag
    Otherwise        → No flag

Exactly +8% or -8% does not trigger a flag.

---

## CII narrative

`draft_report.py` uses `draft_report_v1()` to generate one narrative block per unique flagged region.

Each block follows:

    Context → Insight → Implication

The generated CII blocks then go to human review through the dashboard review gate.

---

## Human review gate

The project separates automated analysis from human sign-off.

The review gate supports:

    approve
    edit
    reject

The dashboard provides:

1. Insight narrative
2. Reviewer note
3. Approve / Edit / Reject action

The `review_gate_v1()` function writes review decisions to `audit_log.jsonl`.

The test harness in `review_gate.py` exercises all three decisions and appends those test results to the same audit log.

The dashboard review status itself is maintained in Streamlit session state and is not reconstructed from the audit log after a page reload.

---

## Reliability workflow

The project follows this sequence:

    1. Safety check
           ↓
    2. Validation
           ↓
    3. Critique / refine
           ↓
    4. Human sign-off

The reliability checklist documents the checks that should happen before an insight is treated as decision-ready.

---

## Presentation storyline

`presentation_storyline.md` frames the same finding two ways: for executives (Situation → Complication → Resolution) and for regional managers (Overview → Category → Detail). It ends with a pushback Q&A ("Why should I believe this number?", "What if an alternative explanation is driving this?", "What did you not check?").

---

## Reproducibility

Run the three commands in Quick start. No external APIs or paid services are needed.

---

## Links

**GitHub repository**

    https://github.com/dileep2112/pharm-easy-regional-pulse--insights

**Live Streamlit dashboard**

    https://pharm-easy-regional-pulse--insightsgit-ce6mr2lkysj5jqvt9co3rz.streamlit.app/

**GitHub profile**

    https://github.com/dileep2112

---

## Author

**Dileep — @dileep2112**