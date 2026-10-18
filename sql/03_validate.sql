-- Validation checks. Each returns (check_name, expected, actual, status).
-- A check passes when actual meets the expectation; failures are explained in docs/data_quality_log.md.
SELECT 'panel has 92 months (2019-01..2026-08)', 92, COUNT(*), CASE WHEN COUNT(*)=92 THEN 'PASS' ELSE 'FAIL' END FROM panel_monthly
UNION ALL
SELECT 'no duplicate months', 0, COUNT(*)-COUNT(DISTINCT month), CASE WHEN COUNT(*)=COUNT(DISTINCT month) THEN 'PASS' ELSE 'FAIL' END FROM panel_monthly
UNION ALL
SELECT 'no gaps: consecutive month count equals span', 92,
  (CAST(substr(MAX(month),1,4) AS INT)-CAST(substr(MIN(month),1,4) AS INT))*12
  + CAST(substr(MAX(month),6,2) AS INT)-CAST(substr(MIN(month),6,2) AS INT)+1,
  CASE WHEN COUNT(*)= (CAST(substr(MAX(month),1,4) AS INT)-CAST(substr(MIN(month),1,4) AS INT))*12
  + CAST(substr(MAX(month),6,2) AS INT)-CAST(substr(MIN(month),6,2) AS INT)+1 THEN 'PASS' ELSE 'FAIL' END FROM panel_monthly
UNION ALL
SELECT 'every series has one value per month (long table)', 0,
  (SELECT COUNT(*) FROM (SELECT series_id, month FROM fact_monthly GROUP BY 1,2 HAVING COUNT(*)>1)),
  CASE WHEN (SELECT COUNT(*) FROM (SELECT series_id, month FROM fact_monthly GROUP BY 1,2 HAVING COUNT(*)>1))=0 THEN 'PASS' ELSE 'FAIL' END
UNION ALL
SELECT 'BTS vs EIA diesel: weeks compared', 405, COUNT(bts_usd_gal), CASE WHEN COUNT(bts_usd_gal)=405 THEN 'PASS' ELSE 'FAIL' END FROM fact_diesel_weekly
UNION ALL
SELECT 'BTS vs EIA diesel: max abs difference (USD/gal)', 0.0, ROUND(MAX(ABS(eia_usd_gal-bts_usd_gal)),4),
  CASE WHEN MAX(ABS(eia_usd_gal-bts_usd_gal))<0.001 THEN 'PASS' ELSE 'FAIL' END FROM fact_diesel_weekly WHERE bts_usd_gal IS NOT NULL
UNION ALL
SELECT 'diesel price range plausible (1.5 to 8 USD/gal)', 0, COUNT(*), CASE WHEN COUNT(*)=0 THEN 'PASS' ELSE 'FAIL' END
  FROM fact_diesel_weekly WHERE eia_usd_gal NOT BETWEEN 1.5 AND 8
UNION ALL
SELECT 'PPI trucking positive', 0, COUNT(*), CASE WHEN COUNT(*)=0 THEN 'PASS' ELSE 'FAIL' END FROM panel_monthly WHERE ppi_trucking_gf <= 0
UNION ALL
SELECT 'bottleneck truck speed in 10-70 mph', 0, COUNT(*), CASE WHEN COUNT(*)=0 THEN 'PASS' ELSE 'FAIL' END FROM panel_monthly WHERE truck_speed_bn NOT BETWEEN 10 AND 70
UNION ALL
SELECT 'null months in freight TSI (known: latest month unpublished)', 1, COUNT(*)-COUNT(tsi_freight), CASE WHEN COUNT(*)-COUNT(tsi_freight)=1 THEN 'PASS' ELSE 'FAIL' END FROM panel_monthly
UNION ALL
SELECT 'null months in inventory-to-sales (known: latest month unpublished)', 1, COUNT(*)-COUNT(inv_sales), CASE WHEN COUNT(*)-COUNT(inv_sales)=1 THEN 'PASS' ELSE 'FAIL' END FROM panel_monthly
UNION ALL
SELECT 'null months in new carriers (known: data ends 2026-06)', 2, COUNT(*)-COUNT(new_carriers_total), CASE WHEN COUNT(*)-COUNT(new_carriers_total)=2 THEN 'PASS' ELSE 'FAIL' END FROM panel_monthly
UNION ALL
SELECT 'spot rate months (2019-01..2024-05)', 65, COUNT(spot_dry_van), CASE WHEN COUNT(spot_dry_van)=65 THEN 'PASS' ELSE 'FAIL' END FROM panel_monthly;
