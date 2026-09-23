-- 1. Average vaccination coverage by year
SELECT year, AVG(coverage) AS avg_coverage
FROM coverage
GROUP BY year
ORDER BY year;

-- 2. Lowest coverage countries
SELECT name, AVG(coverage) AS avg_coverage
FROM coverage
WHERE coverage IS NOT NULL
GROUP BY name
ORDER BY avg_coverage ASC
LIMIT 20;

-- 3. Coverage by antigen
SELECT antigen, AVG(coverage) AS avg_coverage
FROM coverage
GROUP BY antigen
ORDER BY avg_coverage DESC;

-- 4. Disease incidence by year
SELECT year, disease, AVG(incidence_rate) AS avg_incidence
FROM incidence_rate
GROUP BY year, disease
ORDER BY year, disease;

-- 5. Reported cases by disease and year
SELECT year, disease, SUM(cases) AS total_cases
FROM reported_cases
GROUP BY year, disease
ORDER BY year, disease;

-- 6. High vaccination + high incidence combinations
SELECT c.code, c.name, c.year,
       AVG(c.coverage) AS avg_coverage,
       AVG(i.incidence_rate) AS avg_incidence
FROM coverage c
JOIN incidence_rate i
  ON c.code = i.code AND c.year = i.year
GROUP BY c.code, c.name, c.year
HAVING AVG(c.coverage) >= 90
ORDER BY avg_incidence DESC;

-- 7. Vaccine introduction timeline
SELECT who_region, description, MIN(year) AS first_introduction_year,
       COUNT(DISTINCT iso_3_code) AS countries
FROM vaccine_introduction
WHERE LOWER(CAST(intro AS CHAR)) IN ('1','yes','y','true','introduced')
GROUP BY who_region, description
ORDER BY first_introduction_year;

-- 8. Coverage target gap to 95%
SELECT name, year, antigen,
       AVG(coverage) AS coverage,
       GREATEST(0, 95 - AVG(coverage)) AS gap_to_95
FROM coverage
GROUP BY name, year, antigen
ORDER BY gap_to_95 DESC;

-- NOTE:
-- A causal claim that vaccination "caused" disease reduction should not be made
-- from these observational tables alone. Use correlation/trend language unless
-- a suitable causal design and confounder controls are added.
