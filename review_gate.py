"""
review_gate.py -- PharmEasy Regional Pulse (Part 3, Task 3.4).

review_gate_v1(report, decision, reviewer_note="") is the human
checkpoint every draft (CII block or memo) must pass through before
it can be used downstream (in the dashboard or shared externally).

Every call appends one line to audit_log.jsonl with fields:
    timestamp, run_id, region, decision, reviewer_note

following the standard audit-logging principle of tracking every
action, its parameters, and its timestamp.
"""

import json
import uuid
from datetime import datetime, timezone

AUDIT_LOG_PATH = "audit_log.jsonl"
VALID_DECISIONS = {"approve", "edit", "reject"}


def review_gate_v1(report: dict, decision: str, reviewer_note: str = "") -> dict:
    """
    report: a dict describing the draft being reviewed. Must contain at
        least a "region" key (use "ALL" / a memo title for non-region
        reports such as memo.md).
    decision: one of "approve", "edit", "reject".
    reviewer_note: free-text note explaining the decision.

    Returns an updated copy of `report` with the review outcome
    attached, and appends one audit-log line to audit_log.jsonl.

    Raises ValueError if `decision` is not one of the 3 allowed values
    -- the gate must not silently accept an invalid decision.
    """
    if decision not in VALID_DECISIONS:
        raise ValueError(
            f"Invalid decision {decision!r}: must be one of {sorted(VALID_DECISIONS)}"
        )

    downstream_allowed = decision == "approve"

    updated = dict(report)
    updated["review_decision"] = decision
    updated["reviewer_note"] = reviewer_note
    updated["downstream_use_allowed"] = downstream_allowed

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": str(uuid.uuid4()),
        "region": report.get("region", "UNKNOWN"),
        "decision": decision,
        "reviewer_note": reviewer_note,
    }
    with open(AUDIT_LOG_PATH, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return updated


if __name__ == "__main__":
    # Small test harness exercising all 3 decision paths at least once
    # each, printing the before/after state for each call.

    print("=== Test 1: approve ===")
    before = {"region": "Guntur", "context": "Guntur sales rose +122.19% Apr->May."}
    print("Before:", before)
    after = review_gate_v1(before, "approve", reviewer_note="Numbers check out against SQL output; approved for dashboard.")
    print("After: ", after)
    print()

    print("=== Test 2: edit ===")
    before = {"region": "Hyderabad", "context": "Hyderabad sales rose +16.29% Apr->May, +20.61% May->Jun."}
    print("Before:", before)
    after = review_gate_v1(before, "edit", reviewer_note="Wording implies a trend; soften to 'two consecutive increases' pending a 3rd data point.")
    print("After: ", after)
    print()

    print("=== Test 3: reject ===")
    before = {"region": "Visakhapatnam", "context": "Visakhapatnam sales fell due to a competitor promotion."}
    print("Before:", before)
    after = review_gate_v1(before, "reject", reviewer_note="Draft invents an external cause ('competitor promotion') not derivable from order data -- rejected, must be relabeled as hypothesis or removed.")
    print("After: ", after)
    print()

    print("=== Test 4: invalid decision is rejected ===")
    try:
        review_gate_v1({"region": "Nellore"}, "approve_with_changes")
    except ValueError as e:
        print(f"Raised ValueError as expected: {e}")
    print()

    print("=== Test 5: memo.md human sign-off (distinct from the CII-block reviews above) ===")
    memo_report = {
        "region": "Guntur",
        "artifact": "memo.md",
        "summary": "One-page recommendation memo on Guntur's April->May +122.19% swing.",
    }
    print("Before:", memo_report)
    after = review_gate_v1(
        memo_report,
        "approve",
        reviewer_note=(
            "memo.md reviewed against reliability_checklist.md: all 7 template fields "
            "present, every claim risk-tagged, candidate causes labeled as hypotheses "
            "(not facts) in the Assumptions field. Approved for inclusion in the "
            "submission package."
        ),
    )
    print("After: ", after)
    print(
        "\nNote: this entry's region is 'Guntur' (the memo's subject), same as Test 1's "
        "CII-block review of Guntur -- the two are distinguished in audit_log.jsonl by "
        "their reviewer_note ('memo.md reviewed...' vs the CII-block note) and their "
        "distinct run_id and timestamp."
    )

    print(f"\nAudit log entries written to {AUDIT_LOG_PATH}. Contents:")
    with open(AUDIT_LOG_PATH) as f:
        for line in f:
            print(line.strip())
