"""
draft_report.py -- PharmEasy Regional Pulse (Part 3, Task 3.1).

draft_report_v1(flagged_regions, metrics) produces one
Context-Insight-Implication block per region flagged in Part 2.
If a region was flagged in both the April->May and May->June
transitions, its two flags are merged into a single block covering
both transitions. Every number quoted comes directly from the
metrics dict passed in -- no invented figures.
"""

from queries import get_conn, region_month_sales
from metrics_engine import (
    build_month_summary,
    compute_percentage_change_v1,
    flag_significant_regions_v1,
)


def draft_report_v1(flagged_regions: dict, metrics: dict) -> list:
    """
    flagged_regions: dict like
        {"2026-04_2026-05": ["Guntur", "Hyderabad", ...],
         "2026-05_2026-06": ["Guntur", "Vijayawada", ...]}
    metrics: dict like
        {"region_month_sales": {region: {month: sales}},
         "changes": {"2026-04_2026-05": {region: pct}, "2026-05_2026-06": {region: pct}}}

    Returns a list of dicts, one per unique flagged region (deduped
    across transitions), each with populated context/insight/implication
    text plus the raw numbers used, so a reviewer can check every figure
    against Part 2's SQL output.
    """
    region_month = metrics["region_month_sales"]
    changes = metrics["changes"]

    # collect every transition each region was flagged in
    region_transitions = {}
    for transition, regions in flagged_regions.items():
        for region in regions:
            region_transitions.setdefault(region, []).append(transition)

    month_label = {"2026-04": "April 2026", "2026-05": "May 2026", "2026-06": "June 2026"}
    transition_label = {
        "2026-04_2026-05": "April -> May",
        "2026-05_2026-06": "May -> June",
    }

    blocks = []
    for region in sorted(region_transitions):
        transitions = region_transitions[region]
        sales_by_month = region_month.get(region, {})

        context_parts = []
        insight_parts = []
        for t in transitions:
            m_a, m_b = t.split("_")
            sales_a = sales_by_month.get(m_a, 0)
            sales_b = sales_by_month.get(m_b, 0)
            pct = changes[t][region]
            direction = "grown" if pct > 0 else "declined"
            context_parts.append(
                f"In {month_label[m_a]}, {region} recorded total sales of "
                f"Rs.{sales_a:,.2f}; by {month_label[m_b]} this had {direction} "
                f"to Rs.{sales_b:,.2f}."
            )
            insight_parts.append(
                f"{transition_label[t]} change: {pct:+.2f}% "
                f"(flagged, |change| > 8% significance-flag threshold)."
            )

        implication = (
            f"{region}'s sales movement in the flagged transition(s) above "
            f"the 8% operational-alert threshold means this region's numbers "
            f"are worth a human review before being presented to the regional "
            f"lead -- it does not by itself prove a root cause, since an "
            f"8% swing can occur from ordinary month-to-month order-mix "
            f"variation given the order volumes involved."
        )

        blocks.append({
            "region": region,
            "transitions_flagged": transitions,
            "context": " ".join(context_parts),
            "insight": " ".join(insight_parts),
            "implication": implication,
        })

    return blocks


def build_metrics_and_flags():
    """Helper: reproduces Part 2's metrics + flags so this module can be
    run standalone for a demo/print."""
    conn = get_conn()
    region_month = region_month_sales(conn)
    conn.close()

    april = build_month_summary(region_month, "2026-04")
    may = build_month_summary(region_month, "2026-05")
    june = build_month_summary(region_month, "2026-06")

    apr_may_changes = {
        region: round(compute_percentage_change_v1(may[region], april[region]), 2)
        for region in april
    }
    may_jun_changes = {
        region: round(compute_percentage_change_v1(june[region], may[region]), 2)
        for region in may
    }

    flagged = {
        "2026-04_2026-05": flag_significant_regions_v1(apr_may_changes, threshold=8),
        "2026-05_2026-06": flag_significant_regions_v1(may_jun_changes, threshold=8),
    }
    metrics = {
        "region_month_sales": region_month,
        "changes": {
            "2026-04_2026-05": apr_may_changes,
            "2026-05_2026-06": may_jun_changes,
        },
    }
    return flagged, metrics


if __name__ == "__main__":
    flagged, metrics = build_metrics_and_flags()

    union_regions = sorted(set(flagged["2026-04_2026-05"]) | set(flagged["2026-05_2026-06"]))
    print(f"Union of flagged regions across both transitions ({len(union_regions)}): {union_regions}\n")

    blocks = draft_report_v1(flagged, metrics)
    for b in blocks:
        print(f"### {b['region']}  (flagged in: {', '.join(b['transitions_flagged'])})")
        print(f"Context:     {b['context']}")
        print(f"Insight:     {b['insight']}")
        print(f"Implication: {b['implication']}")
        print()
