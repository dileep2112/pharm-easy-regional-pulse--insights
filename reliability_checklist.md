# Reliability Checklist — memo.md (Guntur, +122.19% Apr→May)

Before `memo.md` is marked "approved" in the review gate, it must pass
all 4 steps below.

## 1. Safety check
No personally identifiable customer data appears anywhere in the memo
or the underlying dataset — `orders_clean` and `regions_master` only
contain order-level and region-level aggregates (order id, date,
region, category, product, quantity, sales, profit); there is no
customer name, phone number, address, or payment detail in the
pipeline at any stage.

## 2. Validation
Every numeric claim in `memo.md` was cross-checked against the
printed output of `queries.py` and `metrics_engine.py` before writing
the memo — specifically, the +122.19% April→May figure, the
51→77 order-count change, the ~Rs.1,224→Rs.1,802 average-order-value
change, and the per-category sales breakdown were all re-derived
directly from `pharmeasy.db` via SQL, not typed from memory.

## 3. Critique / refine
On first draft, the memo's Recommendation section originally implied
a specific cause ("likely a promotion drove the spike") without any
supporting data; on review this was flagged as an invented external
fact and rewritten to explicitly recommend a human check the cause on
the ground, with the promotion/stockist/store-ops possibilities
labeled as unverified hypotheses in the Assumptions field rather than
stated as fact.

## 4. Human sign-off
`review_gate.py`'s test harness includes a sign-off call specifically
for `memo.md` (Test 5), separate from the CII-block reviews of
individual flagged regions (Tests 1–3): it passes a report dict
tagged `"artifact": "memo.md"` through `review_gate_v1()` with
decision `"approve"` and a reviewer note stating the memo was checked
against this checklist (all 7 fields present, every claim risk-tagged,
candidate causes labeled as hypotheses rather than facts) before
downstream use was marked as allowed. This is logged to
`audit_log.jsonl` as its own entry, with its own `run_id` and
timestamp and a reviewer note that starts with "memo.md reviewed" —
distinguishing it from the audit-log entry for the Guntur *CII block*
(Test 1), which reviews a different artifact (the dashboard's
Context–Insight–Implication summary) even though both entries share
`region: "Guntur"`.
