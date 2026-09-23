-- Normalization validation queries
-- Run against data/vaccination_normalized.db

PRAGMA foreign_keys = ON;

-- 1. List normalized tables
SELECT name
FROM sqlite_master
WHERE type = 'table'
  AND name NOT LIKE 'sqlite_%'
ORDER BY name;

-- 2. Row counts
SELECT 'dim_country' AS table_name, COUNT(*) AS row_count FROM dim_country
UNION ALL SELECT 'dim_year', COUNT(*) FROM dim_year
UNION ALL SELECT 'dim_antigen', COUNT(*) FROM dim_antigen
UNION ALL SELECT 'dim_disease', COUNT(*) FROM dim_disease
UNION ALL SELECT 'dim_vaccine', COUNT(*) FROM dim_vaccine
UNION ALL SELECT 'dim_coverage_category', COUNT(*) FROM dim_coverage_category
UNION ALL SELECT 'dim_target_population', COUNT(*) FROM dim_target_population
UNION ALL SELECT 'dim_geoarea', COUNT(*) FROM dim_geoarea
UNION ALL SELECT 'fact_coverage', COUNT(*) FROM fact_coverage
UNION ALL SELECT 'fact_incidence_rate', COUNT(*) FROM fact_incidence_rate
UNION ALL SELECT 'fact_reported_cases', COUNT(*) FROM fact_reported_cases
UNION ALL SELECT 'fact_vaccine_introduction', COUNT(*) FROM fact_vaccine_introduction
UNION ALL SELECT 'fact_vaccine_schedule', COUNT(*) FROM fact_vaccine_schedule;

-- 3. Foreign-key integrity
PRAGMA foreign_key_check;

-- 4. Coverage range validation
SELECT COUNT(*) AS invalid_coverage_rows
FROM fact_coverage
WHERE coverage IS NOT NULL
  AND (coverage < 0 OR coverage > 100);

-- 5. Example normalized join
SELECT
    c.country_code,
    c.country_name,
    c.who_region,
    y.year,
    a.antigen_code,
    a.antigen_description,
    fc.coverage
FROM fact_coverage fc
JOIN dim_country c ON fc.country_id = c.country_id
JOIN dim_year y ON fc.year_id = y.year_id
JOIN dim_antigen a ON fc.antigen_id = a.antigen_id
LIMIT 20;
