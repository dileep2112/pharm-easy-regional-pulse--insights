# Presentation Storyline — Guntur's April→May +122.19% Sales Swing

This is the same finding (Guntur's total sales rose from Rs.62,442.27 in
April 2026 to Rs.138,738.93 in May 2026, a +122.19% change, verified by
SQL `GROUP BY region, month` on `pharmeasy.db`), reframed for two
different audiences.

---

## For an executive: Situation → Complication → Resolution

**Situation.** Regional sales across the Telugu-states desk (Telangana,
Andhra Pradesh, and the Bengaluru hub) grew steadily overall in the
April–June 2026 window, and the pipeline now computes every region's
month-on-month change automatically and flags any move above an 8%
operational threshold instead of relying on manual spreadsheet review.

**Complication.** One region — Guntur — moved far more than the rest:
its sales more than doubled from April to May (+122.19%), then gave
back roughly a third of that gain in June (−28.11%). This is the
single largest-magnitude swing anywhere in the dataset. The increase
spans multiple categories (Wellness & Nutrition and Medical Devices
both grew sharply), although the dataset does not establish the
underlying cause.

**Resolution.** Recommend a 15-minute on-the-ground check with
Guntur's regional lead on any May-specific promotion, stock
allocation, or store-ops change before June's numbers are finalized,
and re-run this pipeline in July to see whether Guntur settles near
its April baseline, its May peak, or somewhere in between. Until then,
treat May as a confirmed spike worth investigating, not yet as a new
normal to plan around.

---

## For a regional manager: Overview → Category → Detail

**Overview.** Guntur's total sales went from Rs.62,442.27 in April to
Rs.138,738.93 in May — a +122.19% jump, the largest single-region
swing this quarter, automatically flagged by the pipeline's
significance check.

**Category.** The increase spans multiple categories, although the
dataset does not establish the underlying cause: Wellness & Nutrition
sales in Guntur rose from Rs.19,297.59 to Rs.53,085.01 (+175.09%),
the largest contributor in absolute terms, while Medical Devices rose
from Rs.9,490.63 to Rs.32,766.69 (+245.25%), the largest contributor
in percentage terms. A promotion, a stock release, and a store event
are each plausible hypotheses for what happened, but none is
confirmed by this data and each would need to be checked on the
ground before being treated as the explanation.

**Detail.** These figures come from `SUM(sales_inr) GROUP BY region,
month, category` run against the cleaned, deduplicated `orders_clean`
table (2100 rows, verified against zero duplicate `order_id`s and a
confirmed JOIN row-count of 2101 vs 2100, a delta of exactly one
null-padded zero-order region). Order count in Guntur rose from 51 to
77 (+50.98%) and average order value rose from ~Rs.1,224 to ~Rs.1,802
(+47.16%) — both effects contributed to the total, so this was driven
by more orders *and* bigger orders, not just one or the other.

---

## Anticipated Pushback Q&A

### Q1. "Why should I believe this number?" (category: Why should I believe this number?)

1. **Acknowledge:** Fair question — a 122% swing is a big enough number that it's worth being skeptical of before acting on it.
2. **Verified vs. not verified:** Verified: the underlying `orders_clean` table has zero duplicate `order_id`s (checked via `GROUP BY order_id HAVING COUNT(*) > 1`), region names are normalized from 16 raw string variants down to 9 canonical names before this number was computed, and the SUM itself was run directly against SQLite, not eyeballed from a spreadsheet. Not verified: whether every underlying order in the raw export was itself entered correctly at the point of sale (price, quantity) — the pipeline can't check upstream data-entry accuracy, only structural correctness (duplicates, nulls, schema).
3. **What would resolve it, and by when:** Cross-check May's Guntur order count and value against the store-ops system of record (outside this pipeline) before this figure goes into a board-level report — recommend this be done within the next business week, ahead of any planning decision that assumes the May level is a new baseline.

### Q2. "What if an alternative explanation is driving this?" (category: What if an alternative explanation is driving this?)

1. **Acknowledge:** Yes — the pipeline flags *that* Guntur moved, not *why* it moved, and there are several plausible alternative explanations (a promotion, a stockist restock, a data-entry batch, a genuine demand shift).
2. **Verified vs. not verified:** Verified: the increase is broad-based across at least three categories rather than one single order or product, which weakens (but doesn't fully rule out) a "one bulk order" explanation. Not verified: which, if any, of the plausible causes above actually occurred — the order-level data has no field for promotions, campaigns, or stock events, so this cannot be determined from the dataset alone.
3. **What would resolve it, and by when:** A short conversation with the Guntur regional lead about what changed operationally in May — recommend this happens before the June review cycle closes, so the cause (if any) is documented alongside the July numbers.

### Q3. "What did you not check?" (category: What did you not check?)

1. **Acknowledge:** Good challenge — this pipeline validates structure (duplicates, schema, nulls, region-name consistency) and computes the metrics correctly, but it does not validate the semantic accuracy of the source data.
2. **Verified vs. not verified:** Verified: no duplicate order IDs, no missing values remain after imputation, region-month totals reconcile with a direct SQL SUM, and the JOIN logic correctly preserves Guntur's zero-order sibling case (Kurnool) as a sanity check on the pipeline's JOIN behavior. Not verified: whether the original price, quantity, or date fields entered by store-ops for any individual May order in Guntur were themselves correct — a wrong quantity or price entered at the source would flow through cleanly and be counted as if correct.
3. **What would resolve it, and by when:** A sample audit of ~10–15 of Guntur's highest-value May orders against original invoices/receipts, ideally completed before this finding is escalated beyond the regional desk.
