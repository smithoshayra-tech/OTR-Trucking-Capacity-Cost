-- Feature layer: year-over-year changes remove seasonality/level drift; lags are added in Python.
DROP TABLE IF EXISTS features_monthly;
CREATE TABLE features_monthly AS
SELECT month,
  ppi_trucking_gf, diesel_usd_gal, tsi_freight, truck_emp_k, new_carriers_total, pti_bn, truck_speed_bn,
  ROUND(100.0*(ppi_trucking_gf / LAG(ppi_trucking_gf,12) OVER w - 1),3) AS ppi_trk_yoy,
  ROUND(100.0*(ppi_diesel      / LAG(ppi_diesel,12)      OVER w - 1),3) AS ppi_diesel_yoy,
  ROUND(100.0*(diesel_usd_gal  / LAG(diesel_usd_gal,12)  OVER w - 1),3) AS diesel_yoy,
  ROUND(100.0*(tsi_freight     / LAG(tsi_freight,12)     OVER w - 1),3) AS tsi_yoy,
  ROUND(100.0*(truck_emp_k     / LAG(truck_emp_k,12)     OVER w - 1),3) AS truck_emp_yoy,
  ROUND(100.0*(imports_musd    / LAG(imports_musd,12)    OVER w - 1),3) AS imports_yoy,
  ROUND(100.0*(pce_durables_bn / LAG(pce_durables_bn,12) OVER w - 1),3) AS durables_yoy,
  ROUND(tsi_freight / truck_emp_k, 5) AS freight_per_trucker,        -- utilization proxy: demand index per truck employee (thousands)
  ROUND(100.0*(ppi_trucking_gf / LAG(ppi_trucking_gf,1) OVER w - 1),3) AS ppi_trk_mom,
  ROUND(100.0*(ppi_diesel      / LAG(ppi_diesel,1)      OVER w - 1),3) AS ppi_diesel_mom,
  spot_dry_van,
  inv_sales, new_carriers_forhire, jolts_openings, jolts_quits, pti_bn AS pti
FROM panel_monthly
WINDOW w AS (ORDER BY month);
