PRAGMA foreign_keys = ON;

-- ============================================================
-- NORMALIZED SCHEMA
-- Vaccination Data Analysis and Visualization
-- SQLite
-- ============================================================

DROP TABLE IF EXISTS fact_vaccine_schedule;
DROP TABLE IF EXISTS fact_vaccine_introduction;
DROP TABLE IF EXISTS fact_reported_cases;
DROP TABLE IF EXISTS fact_incidence_rate;
DROP TABLE IF EXISTS fact_coverage;
DROP TABLE IF EXISTS dim_target_population;
DROP TABLE IF EXISTS dim_geoarea;
DROP TABLE IF EXISTS dim_coverage_category;
DROP TABLE IF EXISTS dim_vaccine;
DROP TABLE IF EXISTS dim_disease;
DROP TABLE IF EXISTS dim_antigen;
DROP TABLE IF EXISTS dim_year;
DROP TABLE IF EXISTS dim_country;

CREATE TABLE dim_country (
    country_id INTEGER PRIMARY KEY AUTOINCREMENT,
    country_code TEXT NOT NULL UNIQUE,
    country_name TEXT NOT NULL,
    who_region TEXT
);

CREATE TABLE dim_year (
    year_id INTEGER PRIMARY KEY,
    year INTEGER NOT NULL UNIQUE
);

CREATE TABLE dim_antigen (
    antigen_id INTEGER PRIMARY KEY AUTOINCREMENT,
    antigen_code TEXT NOT NULL UNIQUE,
    antigen_description TEXT
);

CREATE TABLE dim_disease (
    disease_id INTEGER PRIMARY KEY AUTOINCREMENT,
    disease_code TEXT NOT NULL UNIQUE,
    disease_description TEXT
);

CREATE TABLE dim_vaccine (
    vaccine_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vaccine_code TEXT UNIQUE,
    vaccine_description TEXT NOT NULL
);

CREATE TABLE dim_coverage_category (
    coverage_category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    coverage_category_code TEXT NOT NULL UNIQUE,
    coverage_category_description TEXT
);

CREATE TABLE dim_target_population (
    target_pop_id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_pop TEXT NOT NULL UNIQUE,
    target_pop_description TEXT
);

CREATE TABLE dim_geoarea (
    geoarea_id INTEGER PRIMARY KEY AUTOINCREMENT,
    geoarea TEXT NOT NULL UNIQUE
);

-- ------------------------------------------------------------
-- Fact: vaccination coverage
-- ------------------------------------------------------------
CREATE TABLE fact_coverage (
    coverage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    country_id INTEGER NOT NULL,
    year_id INTEGER NOT NULL,
    antigen_id INTEGER NOT NULL,
    coverage_category_id INTEGER,
    target_number REAL,
    doses REAL,
    coverage REAL,
    FOREIGN KEY (country_id) REFERENCES dim_country(country_id),
    FOREIGN KEY (year_id) REFERENCES dim_year(year_id),
    FOREIGN KEY (antigen_id) REFERENCES dim_antigen(antigen_id),
    FOREIGN KEY (coverage_category_id)
        REFERENCES dim_coverage_category(coverage_category_id),
    CHECK (coverage IS NULL OR coverage BETWEEN 0 AND 100)
);

-- ------------------------------------------------------------
-- Fact: disease incidence
-- ------------------------------------------------------------
CREATE TABLE fact_incidence_rate (
    incidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    country_id INTEGER NOT NULL,
    year_id INTEGER NOT NULL,
    disease_id INTEGER NOT NULL,
    denominator REAL,
    incidence_rate REAL,
    FOREIGN KEY (country_id) REFERENCES dim_country(country_id),
    FOREIGN KEY (year_id) REFERENCES dim_year(year_id),
    FOREIGN KEY (disease_id) REFERENCES dim_disease(disease_id)
);

-- ------------------------------------------------------------
-- Fact: reported disease cases
-- ------------------------------------------------------------
CREATE TABLE fact_reported_cases (
    reported_case_id INTEGER PRIMARY KEY AUTOINCREMENT,
    country_id INTEGER NOT NULL,
    year_id INTEGER NOT NULL,
    disease_id INTEGER NOT NULL,
    cases REAL,
    FOREIGN KEY (country_id) REFERENCES dim_country(country_id),
    FOREIGN KEY (year_id) REFERENCES dim_year(year_id),
    FOREIGN KEY (disease_id) REFERENCES dim_disease(disease_id)
);

-- ------------------------------------------------------------
-- Fact: vaccine introduction
-- ------------------------------------------------------------
CREATE TABLE fact_vaccine_introduction (
    introduction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    country_id INTEGER NOT NULL,
    year_id INTEGER NOT NULL,
    vaccine_id INTEGER NOT NULL,
    intro TEXT,
    FOREIGN KEY (country_id) REFERENCES dim_country(country_id),
    FOREIGN KEY (year_id) REFERENCES dim_year(year_id),
    FOREIGN KEY (vaccine_id) REFERENCES dim_vaccine(vaccine_id)
);

-- ------------------------------------------------------------
-- Fact: vaccine schedule
-- ------------------------------------------------------------
CREATE TABLE fact_vaccine_schedule (
    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    country_id INTEGER NOT NULL,
    year_id INTEGER NOT NULL,
    vaccine_id INTEGER NOT NULL,
    target_pop_id INTEGER,
    geoarea_id INTEGER,
    schedule_rounds TEXT,
    age_administered TEXT,
    source_comment TEXT,
    FOREIGN KEY (country_id) REFERENCES dim_country(country_id),
    FOREIGN KEY (year_id) REFERENCES dim_year(year_id),
    FOREIGN KEY (vaccine_id) REFERENCES dim_vaccine(vaccine_id),
    FOREIGN KEY (target_pop_id) REFERENCES dim_target_population(target_pop_id),
    FOREIGN KEY (geoarea_id) REFERENCES dim_geoarea(geoarea_id)
);

-- Helpful indexes for joins/filtering
CREATE INDEX idx_coverage_country_year
    ON fact_coverage(country_id, year_id);

CREATE INDEX idx_coverage_antigen
    ON fact_coverage(antigen_id);

CREATE INDEX idx_incidence_country_year
    ON fact_incidence_rate(country_id, year_id);

CREATE INDEX idx_incidence_disease
    ON fact_incidence_rate(disease_id);

CREATE INDEX idx_cases_country_year
    ON fact_reported_cases(country_id, year_id);

CREATE INDEX idx_cases_disease
    ON fact_reported_cases(disease_id);

CREATE INDEX idx_intro_country_year
    ON fact_vaccine_introduction(country_id, year_id);

CREATE INDEX idx_schedule_country_year
    ON fact_vaccine_schedule(country_id, year_id);

-- Verification view: coverage with readable dimension names
CREATE VIEW vw_coverage_analysis AS
SELECT
    c.country_code,
    c.country_name,
    c.who_region,
    y.year,
    a.antigen_code,
    a.antigen_description,
    cc.coverage_category_code,
    fc.target_number,
    fc.doses,
    fc.coverage
FROM fact_coverage fc
JOIN dim_country c ON fc.country_id = c.country_id
JOIN dim_year y ON fc.year_id = y.year_id
JOIN dim_antigen a ON fc.antigen_id = a.antigen_id
LEFT JOIN dim_coverage_category cc
    ON fc.coverage_category_id = cc.coverage_category_id;
