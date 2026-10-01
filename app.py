"""
app.py -- PharmEasy Regional Pulse dashboard (Part 4).

Run:  streamlit run app.py

Reads from pharmeasy.db (built by build_db.py). No API key, no network
access required -- everything runs locally on SQLite + pandas +
streamlit + plotly.
"""

import sqlite3
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from metrics_engine import (
    build_month_summary,
    compute_percentage_change_v1,
    flag_significant_regions_v1,
)
from draft_report import draft_report_v1
from review_gate import review_gate_v1

DB_PATH = "pharmeasy.db"
HIGHLIGHT_COLOR = "#D62728"   # reserved for the flagged element only
BASE_COLOR = "#4C78A8"
MONTH_ORDER = ["2026-04", "2026-05", "2026-06"]
MONTH_LABEL = {"2026-04": "Apr 2026", "2026-05": "May 2026", "2026-06": "Jun 2026"}

st.set_page_config(page_title="PharmEasy Regional Pulse", layout="wide")


@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    orders = pd.read_sql("SELECT * FROM orders_clean", conn)
    regions = pd.read_sql("SELECT * FROM regions_master", conn)
    conn.close()
    orders["month"] = orders["order_date"].str.slice(0, 7)
    return orders, regions


@st.cache_data
def compute_flags(orders: pd.DataFrame):
    region_month = (
        orders.groupby(["region", "month"])["sales_inr"].sum().unstack(fill_value=0)
    )
    region_month_dict = {
        region: {m: region_month.loc[region, m] for m in region_month.columns}
        for region in region_month.index
    }
    april = build_month_summary(region_month_dict, "2026-04")
    may = build_month_summary(region_month_dict, "2026-05")
    june = build_month_summary(region_month_dict, "2026-06")

    apr_may = {r: round(compute_percentage_change_v1(may[r], april[r]), 2) for r in april}
    may_jun = {r: round(compute_percentage_change_v1(june[r], may[r]), 2) for r in may}

    flagged_apr_may = flag_significant_regions_v1(apr_may, threshold=8)
    flagged_may_jun = flag_significant_regions_v1(may_jun, threshold=8)
    return region_month_dict, apr_may, may_jun, flagged_apr_may, flagged_may_jun


orders, regions_master = load_data()
region_month_dict, apr_may_changes, may_jun_changes, flagged_apr_may, flagged_may_jun = compute_flags(orders)

# ---------------------------------------------------------------------------
# Region filter (connects all 3 hierarchy levels)
# ---------------------------------------------------------------------------
region_options = ["All regions"] + sorted(orders["region"].unique())
selected_region = st.sidebar.selectbox("Region filter", region_options)

if selected_region == "All regions":
    filtered = orders
else:
    filtered = orders[orders["region"] == selected_region]

# ---------------------------------------------------------------------------
# Executive summary (CII format, 3-5 sentences)
# ---------------------------------------------------------------------------
total_sales_all = orders["sales_inr"].sum()
total_profit_all = orders["profit_inr"].sum()
total_orders_all = orders["order_id"].nunique()
guntur_apr_may = apr_may_changes.get("Guntur", 0)
top_category = orders.groupby("category")["sales_inr"].sum().idxmax()
top_category_share = (
    orders.groupby("category")["sales_inr"].sum().max() / total_sales_all * 100
)

st.title("PharmEasy Regional Pulse")

st.markdown(
    f"""
> **Executive Signal Summary.** Across April–June 2026 the nine active regions recorded
> **Rs.{total_sales_all:,.0f}** in total sales, **Rs.{total_profit_all:,.0f}** in profit,
> across **{total_orders_all:,}** distinct orders. The month-on-month trend is
> uneven rather than steady: Guntur's April→May sales swung **{guntur_apr_may:+.2f}%**,
> the largest single move in the dataset and one of eight regions flagged by the
> pipeline's ±8% significance-alert threshold across the two transitions.
> **{top_category}** is the single largest category, driving **{top_category_share:.1f}%**
> of total sales, meaning any regional swing in that category moves the region's
> whole number. Guntur's spike is worth a human follow-up before it's treated as
> a new baseline — see the Category and Detail views below, and `memo.md` /
> `presentation_storyline.md` in this repo for the full recommendation and how
> it would be defended live.
"""
)

st.divider()

# ---------------------------------------------------------------------------
# Embedded CII narrative -- generated live by draft_report_v1(), the same
# function used in Part 3, not retyped by hand. Nothing here is
# auto-approved: each block sits in front of a real reviewer control
# (Approve / Edit / Reject + a reviewer note) and only calls
# review_gate_v1() -- writing to audit_log.jsonl -- when a human actually
# clicks a decision button. This is the "draft -> human review gate ->
# decision -> audit trail" chain that makes this one connected pipeline
# rather than four separate exercises; the dashboard itself never decides
# on the reviewer's behalf.
# ---------------------------------------------------------------------------
st.header("Insight Narrative (Context - Insight - Implication)")
st.caption(
    "Generated live by draft_report_v1() from this session's own SQL-verified "
    "metrics. Nothing below is approved automatically -- each block waits for "
    "a human reviewer to Approve, Edit, or Reject it before that decision is "
    "logged to audit_log.jsonl."
)

flagged_regions_dict = {
    "2026-04_2026-05": flagged_apr_may,
    "2026-05_2026-06": flagged_may_jun,
}
metrics_for_narrative = {
    "region_month_sales": region_month_dict,
    "changes": {
        "2026-04_2026-05": apr_may_changes,
        "2026-05_2026-06": may_jun_changes,
    },
}
cii_blocks = draft_report_v1(flagged_regions_dict, metrics_for_narrative)

if selected_region != "All regions":
    cii_blocks = [b for b in cii_blocks if b["region"] == selected_region]

if not cii_blocks:
    st.info(f"{selected_region} was not flagged by the ±8% significance check in either transition.")
else:
    if "review_decisions" not in st.session_state:
        st.session_state["review_decisions"] = {}  # region -> reviewed dict, only set on a real button click

    for block in cii_blocks:
        region = block["region"]
        already_reviewed = st.session_state["review_decisions"].get(region)

        status_label = (
            f"decision: {already_reviewed['review_decision']}" if already_reviewed else "awaiting human review"
        )
        with st.expander(
            f"{'⭐ ' if region == 'Guntur' else ''}{region} "
            f"(flagged in: {', '.join(block['transitions_flagged'])}) -- {status_label}"
        ):
            st.markdown(f"**Context.** {block['context']}")
            st.markdown(f"**Insight.** {block['insight']}")
            st.markdown(f"**Implication.** {block['implication']}")

            st.divider()

            if already_reviewed:
                decision = already_reviewed["review_decision"]
                icon = {"approve": "✅", "edit": "✏️", "reject": "🚫"}[decision]
                st.markdown(f"{icon} **Reviewed: {decision}.** Reviewer note: {already_reviewed['reviewer_note'] or '(none)'}")
            else:
                st.markdown("**Human review gate** -- this block is not shown as reviewed until you decide:")
                note_key = f"note_{region}"
                reviewer_note = st.text_area(
                    "Reviewer note (optional but recommended)",
                    key=note_key,
                    placeholder="e.g. Numbers checked against Part 2 SQL output; ready for the regional lead.",
                )
                b_approve, b_edit, b_reject = st.columns(3)
                decision_made = None
                if b_approve.button("✅ Approve", key=f"approve_{region}"):
                    decision_made = "approve"
                if b_edit.button("✏️ Edit", key=f"edit_{region}"):
                    decision_made = "edit"
                if b_reject.button("🚫 Reject", key=f"reject_{region}"):
                    decision_made = "reject"

                if decision_made:
                    # Only fires on an actual click -- this is the one place
                    # review_gate_v1() is called for the dashboard's live
                    # narrative, and only with the decision a human just made.
                    st.session_state["review_decisions"][region] = review_gate_v1(
                        block, decision_made, reviewer_note=reviewer_note
                    )
                    st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Level 1: Overview KPIs
# ---------------------------------------------------------------------------
st.header("1. Overview")

k_sales = filtered["sales_inr"].sum()
k_profit = filtered["profit_inr"].sum()
k_orders = filtered["order_id"].nunique()  # distinct-count, not row count

c1, c2, c3 = st.columns(3)
c1.metric("Total Sales (INR)", f"Rs.{k_sales:,.0f}")
c2.metric("Total Profit (INR)", f"Rs.{k_profit:,.0f}")
c3.metric("Total Orders (distinct order_id)", f"{k_orders:,}")

st.divider()

# ---------------------------------------------------------------------------
# Level 2: Category breakdown
# ---------------------------------------------------------------------------
st.header("2. Category Revenue Mix")

cat_sales = (
    filtered.groupby("category")["sales_inr"].sum().sort_values(ascending=False).reset_index()
)

col_a, col_b = st.columns([3, 2])

with col_a:
    fig_bar_cat = go.Figure(
        go.Bar(
            x=cat_sales["category"],
            y=cat_sales["sales_inr"],
            marker_color=BASE_COLOR,
        )
    )
    fig_bar_cat.update_layout(
        title=f"Which category drives sales in {selected_region}? (INR)",
        xaxis_title="Category",
        yaxis_title="Total sales (INR)",
        yaxis=dict(rangemode="tozero"),
    )
    st.plotly_chart(fig_bar_cat, width="stretch")

with col_b:
    # Pie / donut: 6 categories max, within 5-6 slice limit
    fig_pie = go.Figure(
        go.Pie(
            labels=cat_sales["category"],
            values=cat_sales["sales_inr"],
            hole=0.4,
        )
    )
    fig_pie.update_layout(title=f"Sales share by category in {selected_region}")
    st.plotly_chart(fig_pie, width="stretch")

st.divider()

# ---------------------------------------------------------------------------
# Level 3: Detail — per-region, per-month table + trend/comparison charts
# ---------------------------------------------------------------------------
st.header("3. Regional Performance by Period")

detail_df = (
    orders.groupby(["region", "month"])
    .agg(total_sales_inr=("sales_inr", "sum"), total_profit_inr=("profit_inr", "sum"),
         distinct_orders=("order_id", "nunique"))
    .reset_index()
)

# MoM change + flag come straight from the pipeline's existing results
# (compute_flags -> metrics_engine); nothing is recalculated here.
# Apr -> May change is attached to May rows, May -> Jun to Jun rows.
_mom_lookup = {"2026-05": apr_may_changes, "2026-06": may_jun_changes}
_flag_lookup = {"2026-05": set(flagged_apr_may), "2026-06": set(flagged_may_jun)}
detail_df["mom_sales_change_pct"] = detail_df.apply(
    lambda r: _mom_lookup.get(r["month"], {}).get(r["region"]), axis=1
)
detail_df["alert"] = detail_df.apply(
    lambda r: r["region"] in _flag_lookup.get(r["month"], set()), axis=1
)

if selected_region != "All regions":
    detail_df = detail_df[detail_df["region"] == selected_region]

# Sort on the real YYYY-MM key before swapping in display labels.
detail_df = detail_df.sort_values(["region", "month"]).copy()
detail_df["month"] = detail_df["month"].map(MONTH_LABEL)

display_df = detail_df.rename(columns={
    "region": "Region",
    "month": "Period",
    "distinct_orders": "Order Volume",
    "total_sales_inr": "Revenue (₹)",
    "total_profit_inr": "Net Profit (₹)",
    "mom_sales_change_pct": "Revenue Shift (%)",
    "alert": "Review Flag",
})
display_df = display_df[["Region", "Period", "Order Volume", "Revenue (₹)",
                         "Net Profit (₹)", "Revenue Shift (%)", "Review Flag"]]

display_df["Revenue (₹)"] = display_df["Revenue (₹)"].map(lambda x: f"{x:,.2f}")
display_df["Net Profit (₹)"] = display_df["Net Profit (₹)"].map(lambda x: f"{x:,.2f}")
display_df["Revenue Shift (%)"] = display_df["Revenue Shift (%)"].map(
    lambda x: "—" if pd.isna(x) else f"{x:.2f}%"
)
display_df["Review Flag"] = display_df["Review Flag"].apply(
    lambda x: "⚑ Review" if x else "—"
)

st.dataframe(display_df, width="stretch", hide_index=True)

st.subheader("Revenue Trend Across Regions")
trend = (
    orders.groupby(["region", "month"])["sales_inr"].sum().reset_index()
)
# Highlight color is reserved for an actually flagged region (Task 4.1's
# anti-pattern rule), never just for whatever the viewer happens to have
# selected -- e.g. selecting Nellore must not turn it red, since Nellore is
# never flagged in either transition by design.
all_flagged_regions = set(flagged_apr_may) | set(flagged_may_jun)
fig_line = go.Figure()
for region in sorted(trend["region"].unique()):
    r_data = trend[trend["region"] == region].set_index("month").reindex(MONTH_ORDER)
    is_selected = region in all_flagged_regions and (
        (selected_region != "All regions" and region == selected_region)
        or (selected_region == "All regions" and region == "Guntur")
    )
    fig_line.add_trace(
        go.Scatter(
            x=[MONTH_LABEL[m] for m in MONTH_ORDER],
            y=r_data["sales_inr"],
            mode="lines+markers",
            name=region,
            line=dict(color=HIGHLIGHT_COLOR if is_selected else BASE_COLOR, width=3 if is_selected else 1.5),
            opacity=1.0 if is_selected else 0.55,
        )
    )
fig_line.update_layout(
    title="Monthly sales by region, April-June 2026 (INR)",
    xaxis_title="Month",
    yaxis_title="Total sales (INR)",
    yaxis=dict(rangemode="tozero"),
)
st.plotly_chart(fig_line, width="stretch")
if selected_region != "All regions" and selected_region not in all_flagged_regions:
    st.caption(
        f"{selected_region} is not flagged in either transition, so no line is "
        f"highlighted above — the highlight color is reserved for flagged regions only."
    )

st.subheader("Total sales by region (bar chart)")
region_totals = orders.groupby("region")["sales_inr"].sum().sort_values(ascending=False).reset_index()
bar_colors = [HIGHLIGHT_COLOR if r == "Guntur" else BASE_COLOR for r in region_totals["region"]]
fig_bar_region = go.Figure(
    go.Bar(x=region_totals["region"], y=region_totals["sales_inr"], marker_color=bar_colors)
)
fig_bar_region.update_layout(
    title="Which region contributes the most total sales, Apr-Jun 2026? (INR)",
    xaxis_title="Region",
    yaxis_title="Total sales (INR)",
    yaxis=dict(rangemode="tozero"),
)
st.plotly_chart(fig_bar_region, width="stretch")

st.caption(
    "Highlight color (red) is reserved for Guntur, the flagship flagged region "
    "from Part 2/3's analysis — every other region uses the same base color."
)
