-- Profiling queries run BEFORE cleaning. Results are recorded in docs/data_quality_log.md
-- 1. Row count and date span per series
SELECT REPLACE(indicator, char(160), ' ') AS indicator, COALESCE(measure1,'') AS measure1,
       COUNT(*) AS n, MIN(substr(date,1,10)) AS first_date, MAX(substr(date,1,10)) AS last_date
FROM raw_bts GROUP BY 1,2 ORDER BY 1,2;
-- 2. Missing or non-numeric values
SELECT COUNT(*) AS bad_values FROM raw_bts
WHERE value1 IS NULL OR TRIM(value1)='' OR CAST(value1 AS REAL)=0 AND value1 NOT LIKE '0%';
-- 3. Duplicate keys
SELECT indicator, measure1, date, COUNT(*) c FROM raw_bts GROUP BY 1,2,3 HAVING c>1 LIMIT 20;
-- 4. Hidden characters in labels (non-breaking spaces)
SELECT DISTINCT indicator FROM raw_bts WHERE indicator LIKE '%' || char(160) || '%';
