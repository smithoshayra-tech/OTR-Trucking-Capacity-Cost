# Data dictionary

## panel_monthly (one row per month, Jan 2019 to Aug 2026)

| Column | Meaning | Unit | Source series |
|---|---|---|---|
| month | Calendar month, YYYY-MM | | |
| ppi_trucking_gf | Producer price index, general freight trucking | Index (Dec 2003 = 100) | BTS / BLS |
| ppi_trucking_sp | Producer price index, specialized freight trucking | Index (Dec 2003 = 100) | BTS / BLS |
| ppi_diesel | Producer price index, diesel fuel (seasonally adjusted) | Index (1982 = 100) | BTS / BLS |
| diesel_usd_gal | Mean weekly U.S. diesel retail price in the month | USD per gallon | EIA |
| tsi_freight | Freight Transportation Services Index (freight volume) | Index (2000 = 100) | BTS |
| truck_emp_k | Truck transportation employees (SA) | Thousands | BLS via BTS |
| warehouse_emp_k | Warehousing and storage employees (SA) | Thousands | BLS via BTS |
| new_carriers_total | New active carriers added to MCMIS | Carriers per month | FMCSA via BTS |
| new_carriers_forhire | New active for-hire carriers added | Carriers per month | FMCSA via BTS |
| truck_speed_bn, pti_bn | Truck speed and Planning Time Index at 10 bottleneck locations | MPH, index | BTS |
| jolts_openings, jolts_quits | Job openings and quits, transportation, warehousing and utilities | Thousands | BLS via BTS |
| imports_musd | U.S. goods imports (nominal) | Millions USD | BTS |
| pce_durables_bn | Consumer spending on durable goods | Billions USD | BTS |
| inv_sales | Business inventory-to-sales ratio | Ratio | BTS |
| vmt_sa | Vehicle miles traveled (SA) | Miles | BTS |
| spot_dry_van | DAT dry-van spot rate, monthly mean (to May 2024) | USD per mile | DAT via BTS |

## features_monthly (derived)
`*_yoy` = percent change versus 12 months earlier. `*_mom` = percent change versus prior month. `freight_per_trucker` = tsi_freight divided by truck_emp_k, a rough demand-per-worker measure with no verified link to actual utilization.

## Other tables
`fact_monthly` (long form, one row per series and month), `fact_diesel_weekly` (EIA and BTS copies side by side), `fact_spot_monthly`, `dim_series` (series definitions and roles).
