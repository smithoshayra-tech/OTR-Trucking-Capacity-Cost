# Tableau build spec

Data sources are the flat CSVs in `outputs/`. Each file has one grain, so no joins are needed.

| File | Grain | Used for |
|---|---|---|
| tableau_monthly_panel.csv | month | Trend sheets |
| tableau_monthly_changes.csv | month (changes) | Pass-through scatter |
| tableau_model_test.csv | horizon x model | Out-of-time bar chart |
| tableau_planning_estimate.csv | forecast month | Planning sheet |
| tableau_shock_events.csv | event | Shock table |

## Sheets
1. **Fuel vs price.** Dual line from the panel: `ppi_trucking_gf` and `diesel_usd_gal`, each indexed to Jan 2019 = 100 with a table calculation (First value). Reference lines on 2022-03 and 2026-03.
2. **Pass-through scatter.** `diesel_mom` on columns, `ppi_mom` on rows, trend line on, label the three highest diesel months.
3. **Out-of-time test.** Clustered bars of RMSE by horizon, colored by model. Title states the conclusion.
4. **Planning estimate.** Line of published index plus estimate with low and high as a band. Add a parameter `Diesel change vs prior month (%)` and a calculated field `0.131 * [Parameter]` for the same-month price effect, so a reader can test a scenario. Label it as the estimated coefficient from the analysis.
5. **Capacity context.** Dual axis: `truck_emp_k` and `new_carriers_total`.

## Dashboard layout
Top row: KPI tiles (latest diesel price, latest published index, estimated Sep index). Middle: sheets 1 and 4. Bottom: sheets 2 and 3. Capacity context goes on a second dashboard tab. Keep the written limitations in a footer text box.

Publish to Tableau Public and link it from the README once it is live.
