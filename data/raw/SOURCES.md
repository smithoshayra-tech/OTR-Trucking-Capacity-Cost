# Data sources and provenance (pulled 2026-10-18)

| File | Source | How it was pulled | Notes |
|---|---|---|---|
| bts_monthly_indicators.json | BTS "Supply Chain and Freight Indicators" (data.bts.gov, dataset y5ut-ibwt), public domain | Socrata SoQL query filtered to trucking, labor, diesel PPI and macro indicators | 1,907 rows, Jan 2019 to Aug 2026, saved exactly as returned |
| bts_weekly_diesel_spot.json | Same dataset | Same API, filtered to diesel retail price and DAT truck spot rates | 1,560 rows; spot rates end May 2024 |
| eia_weekly_diesel.csv | U.S. EIA API v2, route petroleum/pri/gnd, series EMD_EPD2D_PTE_NUS_DPG | Independent pull used to reconcile the BTS diesel series | 406 weekly rows, 2019-01-07 to 2026-10-12 |

Nothing in this project is simulated or synthetic. Raw files are never edited; every change happens in SQL or Python and is logged.
