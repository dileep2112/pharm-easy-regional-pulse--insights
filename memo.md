# One-Page Recommendation Memo — PharmEasy Regional Pulse

## Title
Guntur's April→May sales swing (+122.19%): what the order data shows, and what to check next. [LOW]

## Context
Guntur is a Tier-2 region in Andhra Pradesh tracked by the Telugu-states regional desk. [LOW] Across April, May, and June 2026, Guntur's total monthly sales were Rs.62,442.27, Rs.138,738.93, and Rs.99,745.18 respectively, computed via `SUM(sales_inr) GROUP BY region, month` on the cleaned, SQL-verified `orders_clean` table. [HIGH] The April→May change of +122.19% and the May→June change of −28.11% both exceed the pipeline's fixed ±8% significance-flag threshold, so both transitions were automatically flagged for human review. [HIGH]

## Key Insight
The April→May jump is driven by a combination of more orders and a higher average order value, not by one single event: Guntur went from 51 distinct orders in April to 77 in May (+50.98%), while average order value rose from ~Rs.1,224.36 to ~Rs.1,801.80 (+47.16%). [HIGH] Both effects compound, which is consistent with (though does not on its own prove) the roughly 2.22x total-sales multiple observed. [MEDIUM]

## Evidence
- Category breakdown (April → May, `SUM(sales_inr) GROUP BY category` filtered to Guntur): Wellness & Nutrition rose from Rs.19,297.59 to Rs.53,085.01 (+175.09%), the single largest contributor in absolute Rupee terms; Medical Devices rose from Rs.9,490.63 to Rs.32,766.69 (+245.25%), the largest contributor in percentage terms. [HIGH]
- Total profit for Guntur rose from Rs.9,816.28 in April to Rs.19,676.92 in May (+100.45%), roughly tracking the sales increase — margins do not appear to have collapsed alongside the volume growth. [HIGH]
- The duplicate-key check on `orders_clean` returns zero rows, and the row-count JOIN check confirms exactly one null-padded region (Kurnool, zero orders) — so Guntur's figures are not artifacts of duplicate or missing-key rows in the pipeline. [HIGH]
- May→June: Guntur fell back to Rs.99,745.18 (−28.11% from May), landing above April's baseline but below May's peak — consistent with a temporary spike rather than a permanent step-change, though the pipeline cannot distinguish "spike that faded" from "new baseline still settling" with only three months of data. [MEDIUM]

## Recommendation
Treat May as a genuine, worth-investigating spike rather than noise — a swing of this magnitude across two flagged transitions is the single largest-magnitude case in this dataset. [MEDIUM] The order data itself does not establish *why* Guntur moved; a promotion, a stockist change, and a data-entry pattern are each plausible **hypotheses**, not conclusions, and none is asserted as fact here (see Assumptions). [MEDIUM] Recommend the regional lead for Guntur do a 15-minute check of any local promotions, stock allocations, or store-ops changes specific to Wellness & Nutrition and Medical Devices in May 2026, specifically to test these hypotheses before any of them is treated as the explanation. [MEDIUM]

## Next Check
Re-run this pipeline once July 2026 data is available and check whether Guntur's sales stabilize near the April baseline, the May peak, or somewhere between — this will show whether May was a one-off spike or the start of a new, higher baseline. [LOW]

## Assumptions
This memo assumes the sales and profit figures recorded in the raw monthly export are themselves accurate at the point of entry (i.e. that store-ops correctly recorded quantities and prices) — the cleaning pipeline fixes duplicates, inconsistent region names, and missing category/profit fields, but cannot detect or correct an order that was entered with a wrong price or quantity in the first place. This is the single unverified assumption flagged upfront in this memo. [HIGH]

Separately, the following are unverified **hypotheses** about what caused Guntur's May spike, not facts derived from the data — the order table has no field for promotions, campaigns, or stock events, so none of these can be confirmed or ruled out from `orders_clean` alone: (a) a regional promotion in May, (b) a stockist or store-ops change that temporarily increased fulfillment, (c) a data-entry pattern specific to that month. [MEDIUM]
