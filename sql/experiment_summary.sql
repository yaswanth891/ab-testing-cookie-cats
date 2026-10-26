-- Read-only SQL summary. The Python analyzer separately performs inference.
SELECT version AS treatment_group,
       COUNT(*) AS players,
       SUM(CASE WHEN retention_1 = 1 THEN 1 ELSE 0 END) AS day_1_returners,
       SUM(CASE WHEN retention_7 = 1 THEN 1 ELSE 0 END) AS day_7_returners,
       ROUND(AVG(retention_1) * 100.0, 3) AS day_1_pct,
       ROUND(AVG(retention_7) * 100.0, 3) AS day_7_pct
FROM experiment
GROUP BY version ORDER BY version;
