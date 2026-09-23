CREATE DATABASE IF NOT EXISTS vaccination_db;
USE vaccination_db;

CREATE TABLE IF NOT EXISTS coverage (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    `group` VARCHAR(100),
    code VARCHAR(10),
    name VARCHAR(255),
    year INT,
    antigen VARCHAR(100),
    antigen_description TEXT,
    coverage_category VARCHAR(100),
    coverage_category_description TEXT,
    target_number DOUBLE,
    doses DOUBLE,
    coverage DOUBLE,
    INDEX idx_cov_country_year (code, year),
    INDEX idx_cov_antigen_year (antigen, year)
);

CREATE TABLE IF NOT EXISTS incidence_rate (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    `group` VARCHAR(100),
    code VARCHAR(10),
    name VARCHAR(255),
    year INT,
    disease VARCHAR(100),
    disease_description TEXT,
    denominator TEXT,
    incidence_rate DOUBLE,
    INDEX idx_inc_country_year (code, year),
    INDEX idx_inc_disease_year (disease, year)
);

CREATE TABLE IF NOT EXISTS reported_cases (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    `group` VARCHAR(100),
    code VARCHAR(10),
    name VARCHAR(255),
    year INT,
    disease VARCHAR(100),
    disease_description TEXT,
    cases DOUBLE,
    INDEX idx_cases_country_year (code, year),
    INDEX idx_cases_disease_year (disease, year)
);

CREATE TABLE IF NOT EXISTS vaccine_introduction (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    iso_3_code VARCHAR(10),
    country_name VARCHAR(255),
    who_region VARCHAR(100),
    year INT,
    description TEXT,
    intro VARCHAR(50),
    INDEX idx_intro_country_year (iso_3_code, year)
);

CREATE TABLE IF NOT EXISTS vaccine_schedule (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    iso_3_code VARCHAR(10),
    country_name VARCHAR(255),
    who_region VARCHAR(100),
    year INT,
    vaccine_code VARCHAR(100),
    vaccine_description TEXT,
    schedule_rounds VARCHAR(100),
    target_pop VARCHAR(100),
    target_pop_description TEXT,
    geoarea VARCHAR(255),
    age_administered VARCHAR(255),
    source_comment TEXT,
    INDEX idx_schedule_country_year (iso_3_code, year)
);
