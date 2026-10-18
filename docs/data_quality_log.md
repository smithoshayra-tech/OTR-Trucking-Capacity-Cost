# Data quality log

Profiling ran before any cleaning (`sql/01_profile.sql`). Decisions are listed in the order they were made.

| # | Finding | Decision |
|---|---|---|
| 1 | 3,467 BTS rows and 406 EIA weeks loaded. No duplicate (indicator, measure, date) keys. | None needed. |
| 2 | Two indicator labels contain non-breaking spaces (truck employees, diesel prices), so plain text matches fail silently. | Replaced with normal spaces inside the join, so raw labels stay as received. |
| 3 | One missing value: Freight Transportation Services Index, Aug 2026 (not yet published). | Left as NULL. Never filled or carried forward. Models drop that month. |
| 4 | Inventory-to-sales ends Jul 2026 (91 months). New carrier counts end Jun 2026. Truck and warehouse employment run one month longer (Sep 2026). | Panel limited to Jan 2019 to Aug 2026 (92 months, where the core series overlap). Missing months stay NULL. |
| 5 | Diesel is weekly, everything else is monthly. | Monthly diesel is the mean of the weekly prices dated in that month. Documented in `02_clean.sql`. |
| 6 | DAT truck spot rates end 2024-05-12. | Used only to validate the price index (65 overlapping months), never as a model input. |
| 7 | BTS-hosted diesel prices versus the EIA source. | Compared 405 weeks: maximum difference $0.000. The BTS copy is a faithful copy of EIA. |
| 8 | Validation check "bottleneck truck speed in 20 to 70 mph" failed on one month (Aug 2019, 19.99 mph). | My threshold was set too tight, not bad data: the series averages about 25 mph and neighboring months read 20.1 to 21.0. Threshold corrected to 10 to 70 mph. Recorded here because the first run failed. |
| 9 | April and June 2022 trucking price index both read 215.56. | Checked. It is the published value, not a duplication error. Only one pair of identical consecutive months exists in the panel (Jul/Aug 2019: 151.0). |
| 10 | Year-over-year series are non-stationary (ADF p = 0.50 for trucking, 0.30 for diesel). | Analysis uses month-over-month changes (p < 0.01). YoY correlation reported only as a caution. |
