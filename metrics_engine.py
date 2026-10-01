"""
metrics_engine.py -- PharmEasy Regional Pulse (Part 2, Task 2.4).

Significance flagging with state persistence:

    compute_percentage_change_v1(current, previous)
    flag_significant_regions_v1(changes, threshold=8)
    save_state_v1(month_summary, path)
    load_previous_state_v1(path)

flag_significant_regions_v1 is a simple fixed-percentage operational
alert, not a statistical significance test: with only a few dozen
orders per region per month, an 8% swing can easily arise from
ordinary month-to-month order-mix noise. A flag means "worth a human
glancing at this number", not "proof something changed" -- Guntur's
April->May +122.19% swing is the one case in this dataset large
enough to stand out even against that noisy backdrop, which is why it
is the flagship story used in Parts 3-4.
"""

import json
from queries import get_conn, region_month_sales


def compute_percentage_change_v1(current, previous):
    """(current - previous) / previous * 100, returning 0 if previous is 0."""
    if previous == 0:
        return 0
    return (current - previous) / previous * 100


def flag_significant_regions_v1(changes: dict, threshold: float = 8) -> list:
    """Return the list of regions whose abs(% change) exceeds threshold."""
    return [region for region, change in changes.items() if abs(change) > threshold]


def save_state_v1(month_summary: dict, path: str) -> None:
    """Persist a month's computed summary (region -> total_sales) as JSON."""
    with open(path, "w") as f:
        json.dump(month_summary, f, indent=2, sort_keys=True)


def load_previous_state_v1(path: str) -> dict:
    """Reload a previously saved month summary from JSON."""
    with open(path) as f:
        return json.load(f)


def build_month_summary(region_month: dict, month: str) -> dict:
    """Extract {region: total_sales} for a single month key, e.g. '2026-04'."""
    return {region: months.get(month, 0) for region, months in region_month.items()}


if __name__ == "__main__":
    conn = get_conn()
    region_month = region_month_sales(conn)
    conn.close()

    april = build_month_summary(region_month, "2026-04")
    may = build_month_summary(region_month, "2026-05")
    june = build_month_summary(region_month, "2026-06")

    # --- round-trip state persistence for April ---
    save_state_v1(april, "state_2026-04.json")
    april_reloaded = load_previous_state_v1("state_2026-04.json")
    assert april_reloaded == april, "state round-trip mismatch!"
    print("State persistence round-trip check: OK (reloaded April summary matches original)\n")

    print("=== April -> May: percentage change + significance flags (threshold=8) ===")
    apr_may_changes = {
        region: round(compute_percentage_change_v1(may[region], april_reloaded[region]), 2)
        for region in april_reloaded
    }
    for region in sorted(apr_may_changes):
        print(f"{region:<15} {apr_may_changes[region]:+.2f}%")
    flagged_apr_may = flag_significant_regions_v1(apr_may_changes, threshold=8)
    print(f"\nFlagged (Apr->May): {sorted(flagged_apr_may)}")

    save_state_v1(may, "state_2026-05.json")
    may_reloaded = load_previous_state_v1("state_2026-05.json")

    print("\n=== May -> June: percentage change + significance flags (threshold=8) ===")
    may_jun_changes = {
        region: round(compute_percentage_change_v1(june[region], may_reloaded[region]), 2)
        for region in may_reloaded
    }
    for region in sorted(may_jun_changes):
        print(f"{region:<15} {may_jun_changes[region]:+.2f}%")
    flagged_may_jun = flag_significant_regions_v1(may_jun_changes, threshold=8)
    print(f"\nFlagged (May->Jun): {sorted(flagged_may_jun)}")

    save_state_v1(june, "state_2026-06.json")

    print(f"\nNellore flagged in Apr->May? {'Nellore' in flagged_apr_may}")
    print(f"Nellore flagged in May->Jun? {'Nellore' in flagged_may_jun}")
