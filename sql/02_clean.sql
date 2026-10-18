-- Cleaning and modeling layer. Raw tables are never modified.
-- Decisions are logged in docs/data_quality_log.md.

DROP TABLE IF EXISTS dim_series;
CREATE TABLE dim_series(series_id TEXT PRIMARY KEY, label TEXT, role TEXT, units TEXT,
                        ind_like TEXT, measure1 TEXT);
INSERT INTO dim_series VALUES
('ppi_trucking_gf','PPI: General Freight Trucking','price','Index (Dec 2003=100)','Producer Price Index for Trucking%','PPI: General Freight Trucking'),
('ppi_trucking_sp','PPI: Specialized Freight Trucking','price','Index (Dec 2003=100)','Producer Price Index for Trucking%','PPI: Specialized Freight Trucking'),
('ppi_diesel','PPI: Diesel Fuel (SA)','cost driver','Index (1982=100)','Producer Price Index: Diesel Fuel%',NULL),
('tsi_freight','Freight Transportation Services Index','demand','Index (2000=100)','Freight Transportation Services Index%',NULL),
('truck_emp_k','Truck transportation employees (SA)','capacity','Thousands','Number of Non-Farm Truck Transportation%',NULL),
('warehouse_emp_k','Warehousing and storage employees (SA)','capacity','Thousands','Number of Warehousing and Storage%',NULL),
('new_carriers_total','New active carriers added (total)','capacity','Carriers per month','New Active Carriers Added%','Total New Active Carriers Added to MCMIS'),
('new_carriers_forhire','New active for-hire carriers added','capacity','Carriers per month','New Active Carriers Added%','New Active For-hire Carriers Added to MCMIS'),
('truck_speed_bn','Truck speed at 10 bottlenecks','congestion','MPH','Average Truck Speed in MPH at 10 Bottleneck%',NULL),
('pti_bn','Planning Time Index at 10 bottlenecks','congestion','PTI','Average Planning Time Index at 10 Bottleneck%',NULL),
('jolts_openings','Job openings: transport, warehousing, utilities','capacity','Thousands','Job Openings and Labor Turnover: Transportation%','Job Openings'),
('jolts_quits','Quits: transport, warehousing, utilities','capacity','Thousands','Job Openings and Labor Turnover: Transportation%','Quits'),
('imports_musd','U.S. goods imports','demand','Millions USD','U.S. Goods Imports in Millions%',NULL),
('pce_durables_bn','Consumer spending on durable goods','demand','Billions USD','Personal Consumption Expenditures in Billions of $: Durable%',NULL),
('inv_sales','Business inventory-to-sales ratio','demand','Ratio','Total Business: Inventory to Sales%',NULL),
('vmt_sa','Vehicle miles traveled (SA)','demand','Miles','Vehicle Miles Traveled VMT%','VMT Seasonally Adjusted');

DROP TABLE IF EXISTS fact_monthly;
CREATE TABLE fact_monthly AS
SELECT d.series_id,
       substr(r.date,1,7) AS month,                 -- 'YYYY-MM'
       CAST(NULLIF(TRIM(r.value1),'') AS REAL) AS value
FROM raw_bts r
JOIN dim_series d
  ON REPLACE(r.indicator, char(160), ' ') LIKE d.ind_like
 AND (d.measure1 IS NULL OR r.measure1 = d.measure1)
WHERE r.source_file = 'bts_monthly_indicators.json';

-- Weekly diesel (BTS copy) and EIA copy, typed
DROP TABLE IF EXISTS fact_diesel_weekly;
CREATE TABLE fact_diesel_weekly AS
SELECT e.week_start, CAST(e.usd_per_gal AS REAL) AS eia_usd_gal,
       (SELECT CAST(b.value1 AS REAL) FROM raw_bts b
         WHERE REPLACE(b.indicator,char(160),' ') LIKE 'U.S. Diesel Sales Prices%'
           AND substr(b.date,1,10) = e.week_start) AS bts_usd_gal
FROM raw_eia e;

-- Monthly diesel = mean of weeks whose Monday falls in that month
DROP TABLE IF EXISTS fact_diesel_monthly;
CREATE TABLE fact_diesel_monthly AS
SELECT substr(week_start,1,7) AS month, ROUND(AVG(eia_usd_gal),4) AS diesel_usd_gal, COUNT(*) AS weeks
FROM fact_diesel_weekly GROUP BY 1;

-- Spot rates (DAT via BTS): weekly by truck type, monthly mean
DROP TABLE IF EXISTS fact_spot_monthly;
CREATE TABLE fact_spot_monthly AS
SELECT substr(date,1,7) AS month, measure1 AS truck_type,
       ROUND(AVG(CAST(value1 AS REAL)),4) AS usd_per_mile, COUNT(*) AS weeks
FROM raw_bts WHERE indicator LIKE 'Truck Spot Rates%' GROUP BY 1,2;

-- Wide monthly panel, Jan 2019 - Aug 2026 (the span where the core series overlap)
DROP TABLE IF EXISTS panel_monthly;
CREATE TABLE panel_monthly AS
WITH months AS (SELECT DISTINCT month FROM fact_monthly WHERE month BETWEEN '2019-01' AND '2026-08')
SELECT m.month,
  MAX(CASE WHEN f.series_id='ppi_trucking_gf'  THEN f.value END) AS ppi_trucking_gf,
  MAX(CASE WHEN f.series_id='ppi_trucking_sp'  THEN f.value END) AS ppi_trucking_sp,
  MAX(CASE WHEN f.series_id='ppi_diesel'       THEN f.value END) AS ppi_diesel,
  MAX(CASE WHEN f.series_id='tsi_freight'      THEN f.value END) AS tsi_freight,
  MAX(CASE WHEN f.series_id='truck_emp_k'      THEN f.value END) AS truck_emp_k,
  MAX(CASE WHEN f.series_id='warehouse_emp_k'  THEN f.value END) AS warehouse_emp_k,
  MAX(CASE WHEN f.series_id='new_carriers_total'   THEN f.value END) AS new_carriers_total,
  MAX(CASE WHEN f.series_id='new_carriers_forhire' THEN f.value END) AS new_carriers_forhire,
  MAX(CASE WHEN f.series_id='truck_speed_bn'   THEN f.value END) AS truck_speed_bn,
  MAX(CASE WHEN f.series_id='pti_bn'           THEN f.value END) AS pti_bn,
  MAX(CASE WHEN f.series_id='jolts_openings'   THEN f.value END) AS jolts_openings,
  MAX(CASE WHEN f.series_id='jolts_quits'      THEN f.value END) AS jolts_quits,
  MAX(CASE WHEN f.series_id='imports_musd'     THEN f.value END) AS imports_musd,
  MAX(CASE WHEN f.series_id='pce_durables_bn'  THEN f.value END) AS pce_durables_bn,
  MAX(CASE WHEN f.series_id='inv_sales'        THEN f.value END) AS inv_sales,
  MAX(CASE WHEN f.series_id='vmt_sa'           THEN f.value END) AS vmt_sa,
  dm.diesel_usd_gal,
  (SELECT usd_per_mile FROM fact_spot_monthly s WHERE s.month=m.month AND s.truck_type='Dry Van') AS spot_dry_van
FROM months m
LEFT JOIN fact_monthly f ON f.month = m.month
LEFT JOIN fact_diesel_monthly dm ON dm.month = m.month
GROUP BY m.month ORDER BY m.month;
