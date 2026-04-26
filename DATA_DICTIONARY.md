# Data Dictionary & Output Guide

This document describes every output file produced by `funnel_analysis.ipynb`, explains what each column means, and traces how each column was derived.

---

## Output Files Overview

| File | Level | Rows | Primary audience |
|---|---|---|---|
| `dashboard_products_v2.csv` | Product | 1 per product (≥50 view sessions) | Seller |
| `dashboard_category_v2.csv` | Category | 1 per `cat_level_2` (≥1,000 view sessions) | Platform operator |
| `dashboard_brand_v2.csv` | Brand × category | 1 per brand × `cat_level_2` (≥3 actionable products) | Seller |

---

## dashboard_products_v2.csv

One row per product. Only products with ≥ 50 view sessions are included.

### Identity columns

| Column | Description |
|---|---|
| `product_id` | Unique product identifier |
| `category_code` | Full category path, e.g. `electronics.smartphone` |
| `cat_level_1` | Top-level category, e.g. `electronics` |
| `cat_level_2` | Subcategory, e.g. `smartphone` |
| `brand` | Brand name (null for ~14% of products) |

### Pricing columns

| Column | How derived | What it means |
|---|---|---|
| `price` | Median of all view-event prices | The price users most commonly saw when browsing |
| `price_percentile` | Percentile rank of `price` within `cat_level_2` | 80 = priced higher than 80% of products in the same subcategory |
| `quadrant` | Combines `price_percentile` and `view_to_purchase_pct` vs category median | One of: High Price / High CR, High Price / Low CR, Low Price / High CR, Low Price / Low CR |

### Funnel count columns

| Column | How derived | What it means |
|---|---|---|
| `view` | `nunique(user_session)` where event = view | Distinct sessions that viewed this product |
| `cart` | `nunique(user_session)` where event = cart | Distinct sessions that added to cart |
| `purchase` | `nunique(user_session)` where event = purchase | Distinct sessions that purchased |
| `total_interactions` | `view + cart + purchase` | Total session-level touchpoints |
| `path_b_flag` | True if `cart_to_purchase_pct > 100%` | Path B (direct purchase) dominates — more purchase sessions than cart sessions |

> **Why session-deduplicated?**
> If one user views the same product 10 times in one session, that counts as 1 session, not 10. This makes conversion rates meaningful and comparable across products.

### Funnel rate columns

| Column | Formula | What it means |
|---|---|---|
| `view_to_cart_pct` | `cart / view × 100` | % of view sessions that added to cart |
| `view_to_purchase_pct` | `purchase / view × 100` | % of view sessions that resulted in purchase |
| `cart_to_purchase_pct` | `purchase / cart × 100` | % of cart sessions that completed purchase — **unreliable if `path_b_flag = True`** |
| `conversion_rate` | `purchase / view` (0–1 scale) | Overall view-to-purchase rate |
| `cart_rate` | `cart / view` (0–1 scale) | View-to-cart rate |

### Category situation columns

These columns encode the category's purchase behaviour pattern, derived in §7 of the notebook.

| Column | How derived | What it means |
|---|---|---|
| `situation` | Assigned based on bottleneck stage + path_b_rate | The purchase behaviour pattern of this product's category |
| `primary_metric` | Determined by `situation` | The funnel metric that matters most for this category |
| `primary_percentile` | Percentile rank of `primary_metric` within the benchmark group | How this product ranks on the metric that matters most |
| `cat_v2c_benchmark` | Category-level average `view_to_cart_pct` | The View→Cart rate for this category as a whole |
| `cat_c2p_benchmark` | Category-level average `cart_to_purchase_pct` | The Cart→Purchase rate for this category as a whole |
| `cat_v2p_benchmark` | Category-level average `view_to_purchase_pct` | The View→Purchase rate for this category as a whole |
| `path_b_rate` | Category-level % of purchases with no cart event | How common direct purchase is in this category |
| `benchmark_level` | `level_1` or `level_2` | Which category level is used as the benchmark for this product |

**The three situations:**

| Situation | Path B | Primary bottleneck | Primary metric | Interpretation |
|---|---|---|---|---|
| Healthy | any | None — metrics at or above average | — | No action needed |
| 1: Cart barrier | Low | View→Cart gap > Cart→Purchase gap | `view_to_cart_%` | Cart is a real intent signal — product page is failing to convert interest |
| 2: Discovery/appeal problem | High | View→Purchase below median | `view_to_purchase_%` | Users buy directly — low overall conversion means product lacks visibility or appeal |
| 3: Checkout friction | Low | Cart→Purchase gap ≥ View→Cart gap | `cart_to_purchase_%` | Users intend to buy but something blocks checkout |

### Signal columns

| Column | How derived | What it means |
|---|---|---|
| `signal_v2` | `primary_percentile` vs 25th/75th thresholds, modified by `path_b_flag` | The diagnostic label for this product |
| `priority_focus_v2` | Mapped from `signal_v2` | One-line action priority |
| `recommended_actions_v2` | Mapped from `signal_v2` | Pipe-separated list of specific actions |
| `business_hypothesis_v2` | Mapped from `signal_v2` | Why this signal occurs in this category context |

**Signal labels:**

| Signal | Condition | Action type | Priority focus |
|---|---|---|---|
| `Strong Performer` | `primary_percentile ≥ 75` | Monitor | Maintain and Monitor |
| `Normal` | `25 ≤ primary_percentile < 75` | Monitor | Maintain and Monitor |
| `Low Cart Rate — fix product page` | Situation 1, `primary_percentile ≤ 25` | Fix | Product Page Quality |
| `Low Direct Purchase Rate — fix visibility` | Situation 2, `primary_percentile ≤ 25` | Fix | Product Visibility and Appeal |
| `Low Checkout Rate — fix checkout` | Situation 3, `primary_percentile ≤ 25` | Fix | Checkout Friction |
| `High Direct Purchase (Path B)` | `path_b_flag = True` | Scale | Increase Exposure |
| `Underperformer` | Category join failed | Review | Check category assignment |
| `Insufficient data` | `primary_percentile = NaN` | Wait | Insufficient Data |

### Business value columns

| Column | How derived | What it means |
|---|---|---|
| `revenue_proxy` | Sum of purchase-event prices | Actual revenue generated (proxy — no cost data) |
| `avg_purchase_price` | Mean of purchase-event prices | Average price at time of purchase |
| `purchase_count` | Number of purchase events | Total units sold |
| `revenue_rank_in_category` | Dense rank within `cat_level_2` by `revenue_proxy` | 1 = highest revenue product in this subcategory |
| `revenue_percentile_in_category` | Percentile rank within `cat_level_2` | 90 = higher revenue than 90% of products in subcategory |
| `lost_revenue_est` | `view × price × (benchmark_cr − conversion_rate)`, clipped at 0 | Estimated revenue lost due to non-conversion vs category benchmark |
| `benchmark_cr` | Category benchmark CR for the primary metric | The target CR this product is compared against |
| `cr_gap` | `benchmark_cr − conversion_rate`, clipped at 0 | How far below benchmark this product is |
| `popularity_score` | Weighted: `0.45×view + 0.8×cart + 1.6×purchase`, normalised 0–100 | Combined engagement score |
| `popularity_label` | Quartile of `popularity_score` | High / Medium / Low |

---

## dashboard_category_v2.csv

One row per `cat_level_2` category. Only categories with ≥ 1,000 view sessions are included.

**Purpose:** Help the platform operator understand which categories need the most attention and what type of optimization is needed.

**How this table was built:**
```
Step A → corrected session-level funnel rates per category (Path B purchases excluded from c2p)
Step B → Path B rate + situation assignment per category
Step C → actionable lost revenue aggregated from product_df_v2
         (only products with actionable signals counted)
```

### Column Reference

| Column | How derived | What it means |
|---|---|---|
| `cat_level_1` | Raw data | Top-level category |
| `cat_level_2` | Raw data | Subcategory |
| `situation` | Step B | Purchase behaviour pattern for this category |
| `primary_metric` | Step B | The funnel metric that matters most here |
| `path_b_rate` | Step A | % of purchases that bypassed cart |
| `v2c_pct` | Step A | Category-level View→Cart rate |
| `c2p_pct` | Step A (Path B excluded) | Category-level Cart→Purchase rate |
| `view_sessions` | From `df_cat` | Total view sessions in this category |
| `total_product_count` | Count from `product_df_v2` | All products above view threshold |
| `actionable_product_count` | Products with actionable signals | Products that actually need attention |
| `actionable_rate` | `actionable_product_count / total_product_count × 100` | % of products in this category with a problem |
| `actionable_lost_revenue` | Sum of `lost_revenue_est` for actionable products only | Revenue at risk from products that need fixing |
| `avg_lost_revenue_per_product` | `actionable_lost_revenue / actionable_product_count` | Average revenue impact per problem product |
| `priority_rank` | Rank by `v2c_benchmark_gap` descending | 1 = category most underperforming vs platform median |

> **Why `actionable_lost_revenue` and not total lost revenue?**
> Strong Performers have high lost revenue by definition (high traffic × non-zero non-conversion rate), but they do not need optimization. Including them would inflate the ranking for well-performing categories. Only products with actionable signals are counted.

---

## dashboard_brand_v2.csv

One row per `brand × cat_level_2` combination. Only combinations with ≥ 3 actionable products are included.

**Purpose:** Help sellers understand the main problem type across their product portfolio within each category they operate in.

**How this table was built:**
```
product_df_v2 (actionable products only, with brand info)
    → grouped by brand × cat_level_2
    → dominant_signal = signal with highest lost_revenue_est in this brand×category
    → action_type derived from dominant_signal
```

> **Why dominant signal by lost revenue, not product count?**
> A brand may have 10 Normal products and 2 problem products, but those 2 might represent 80% of the lost revenue. Lost-revenue weighting surfaces the most impactful problem, not just the most common one.

### Column Reference

| Column | How derived | What it means |
|---|---|---|
| `cat_level_2` | From `product_df_v2` | Subcategory this brand operates in |
| `brand` | From `product_df_v2` | Brand name |
| `situation` | Joined from category table | Purchase behaviour pattern for this category |
| `dominant_signal` | Signal with highest `lost_revenue_est` in this brand×category | The main problem type for this brand in this category |
| `action_type` | Mapped from `dominant_signal` | **Fix** = conversion problem / **Scale** = growth opportunity |
| `priority_focus_v2` | Mapped from `dominant_signal` | One-line action priority |
| `actionable_product_count` | Count of actionable products | How many of this brand's products have a problem |
| `total_actionable_lost_revenue` | Sum of `lost_revenue_est` for actionable products | Total revenue at risk for this brand in this category |
| `avg_lost_revenue_per_product` | `total / count` | Average impact per problem product |
| `rank_in_category` | Dense rank within `cat_level_2` by `total_actionable_lost_revenue` | 1 = highest-impact brand in this subcategory |
| `brand_rank_label` | e.g. `"3 of 9 brands"` | Relative rank within category |
| `situation_summary` | Mapped from `situation` | One-sentence description of the category's problem |
| `primary_metric` | Joined from category table | The funnel metric that matters most for this category |
| `path_b_rate` | Joined from category table | How common direct purchase is in this category |

**Interpreting `action_type`:**

| action_type | Signal | What it means | Recommended action |
|---|---|---|---|
| **Fix** | Low Cart Rate / Low Direct Purchase Rate / Low Checkout Rate | Conversion problem — users are not buying at expected rate | Improve product page, visibility, or checkout |
| **Scale** | High Direct Purchase (Path B) | Growth opportunity — users convert immediately when they find the product | Increase exposure, traffic, and promotion |

> Example: `Apple in smartphone → action_type = Scale`
> This does NOT mean Apple has a problem. It means Apple's products convert well on direct purchase — the opportunity is to reach more users, not to fix the funnel.
