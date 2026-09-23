import sqlite3
import pandas as pd
from pathlib import Path


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "vaccination.db"
OUTPUT_DIR = BASE_DIR / "outputs" / "sql_analysis"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Connect to SQLite database
# ---------------------------------------------------------

conn = sqlite3.connect(DB_PATH)


# ---------------------------------------------------------
# Helper function
# ---------------------------------------------------------

def run_query(query, output_file):
    """Run SQL query, display result and save as CSV."""

    df = pd.read_sql_query(query, conn)

    print("\n" + "=" * 70)
    print(output_file)
    print("=" * 70)

    print(df.head(10))

    print(f"\nRows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    output_path = OUTPUT_DIR / output_file
    df.to_csv(output_path, index=False)

    print(f"Saved to: {output_path}")

    return df


# =========================================================
# 1. Average Vaccination Coverage by Year
# =========================================================

query_1 = """
SELECT
    year,
    ROUND(AVG(coverage), 2) AS avg_coverage
FROM coverage
WHERE coverage BETWEEN 0 AND 100
  AND UPPER("group") = 'COUNTRIES'
GROUP BY year
ORDER BY year;
"""

run_query(
    query_1,
    "01_coverage_by_year.csv"
)


# =========================================================
# 2. Countries with Lowest Average Vaccination Coverage
# =========================================================

query_2 = """
SELECT
    code,
    name,
    ROUND(AVG(coverage), 2) AS avg_coverage
FROM coverage
WHERE coverage BETWEEN 0 AND 100
  AND UPPER("group") = 'COUNTRIES'
  AND code IS NOT NULL
  AND name IS NOT NULL
GROUP BY code, name
ORDER BY avg_coverage ASC
LIMIT 20;
"""

run_query(
    query_2,
    "02_lowest_coverage_countries.csv"
)


# =========================================================
# 3. Average Vaccination Coverage by Antigen
# =========================================================

query_3 = """
SELECT
    antigen,
    ROUND(AVG(coverage), 2) AS avg_coverage
FROM coverage
WHERE coverage BETWEEN 0 AND 100
  AND UPPER("group") = 'COUNTRIES'
  AND antigen IS NOT NULL
GROUP BY antigen
ORDER BY avg_coverage DESC;
"""

run_query(
    query_3,
    "03_coverage_by_antigen.csv"
)


# =========================================================
# 4. Disease Incidence by Year
# =========================================================

query_4 = """
SELECT
    year,
    disease,
    ROUND(AVG(incidence_rate), 2) AS avg_incidence_rate
FROM incidence_rate
WHERE incidence_rate IS NOT NULL
  AND UPPER("group") = 'COUNTRIES'
  AND disease IS NOT NULL
GROUP BY year, disease
ORDER BY year, disease;
"""

run_query(
    query_4,
    "04_disease_incidence_by_year.csv"
)


# =========================================================
# 5. Reported Cases by Disease and Year
# =========================================================

query_5 = """
SELECT
    year,
    disease,
    SUM(cases) AS total_reported_cases
FROM reported_cases
WHERE cases IS NOT NULL
  AND UPPER("group") = 'COUNTRIES'
  AND disease IS NOT NULL
GROUP BY year, disease
ORDER BY year, disease;
"""

run_query(
    query_5,
    "05_reported_cases_by_disease_year.csv"
)


# =========================================================
# 6. High Vaccination Coverage + High Disease Incidence
# =========================================================
#
# First aggregate vaccination coverage to:
# Country + Year + Antigen
#
# Then aggregate incidence to:
# Country + Year + Disease
#
# This prevents a many-to-many join and duplicate rows.
# =========================================================

query_6 = """
WITH coverage_summary AS (

    SELECT
        code,
        name,
        year,
        antigen,
        ROUND(AVG(coverage), 2) AS coverage

    FROM coverage

    WHERE coverage BETWEEN 0 AND 100
      AND UPPER("group") = 'COUNTRIES'
      AND code IS NOT NULL
      AND name IS NOT NULL
      AND antigen IS NOT NULL

    GROUP BY
        code,
        name,
        year,
        antigen
),

incidence_summary AS (

    SELECT
        code,
        name,
        year,
        disease,
        ROUND(AVG(incidence_rate), 2) AS incidence_rate

    FROM incidence_rate

    WHERE incidence_rate IS NOT NULL
      AND UPPER("group") = 'COUNTRIES'
      AND code IS NOT NULL
      AND name IS NOT NULL
      AND disease IS NOT NULL

    GROUP BY
        code,
        name,
        year,
        disease
),

overall_incidence AS (

    SELECT
        AVG(incidence_rate) AS overall_avg_incidence

    FROM incidence_rate

    WHERE incidence_rate IS NOT NULL
      AND UPPER("group") = 'COUNTRIES'
)

SELECT
    c.code,
    c.name,
    c.year,
    c.antigen,
    c.coverage,
    i.disease,
    i.incidence_rate

FROM coverage_summary c

JOIN incidence_summary i
    ON c.code = i.code
    AND c.year = i.year

WHERE c.coverage >= 90
  AND i.incidence_rate > (
      SELECT overall_avg_incidence
      FROM overall_incidence
  )

ORDER BY
    i.incidence_rate DESC;
"""

run_query(
    query_6,
    "06_high_coverage_high_incidence.csv"
)


# =========================================================
# 7. Vaccine Introduction Timeline
# =========================================================

query_7 = """
SELECT
    who_region,
    description,
    MIN(year) AS first_introduction_year,
    COUNT(DISTINCT code) AS countries
FROM vaccine_introduction
WHERE year IS NOT NULL
  AND description IS NOT NULL
GROUP BY who_region, description
ORDER BY first_introduction_year;
"""

run_query(
    query_7,
    "07_vaccine_introduction_timeline.csv"
)


# =========================================================
# 8. Vaccination Coverage Gap to 95%
# =========================================================
#
# We first calculate average coverage for each:
# Country + Year + Antigen
#
# Then we calculate the gap to the 95% target.
#
# 0% records are excluded because they can represent
# missing/non-applicable reporting rather than a useful
# coverage measurement for this particular analysis.
# =========================================================

query_8 = """
WITH coverage_summary AS (

    SELECT
        code,
        name,
        year,
        antigen,
        ROUND(AVG(coverage), 2) AS coverage

    FROM coverage

    WHERE coverage > 0
      AND coverage < 95
      AND UPPER("group") = 'COUNTRIES'
      AND code IS NOT NULL
      AND name IS NOT NULL
      AND antigen IS NOT NULL

    GROUP BY
        code,
        name,
        year,
        antigen
)

SELECT
    code,
    name,
    year,
    antigen,
    coverage,
    ROUND(95 - coverage, 2) AS gap_to_95

FROM coverage_summary

ORDER BY
    gap_to_95 DESC;
"""

run_query(
    query_8,
    "08_coverage_gap_to_95.csv"
)


# =========================================================
# 9. Data Quality Summary
# =========================================================

quality_queries = {

    "coverage_total_rows": """
        SELECT COUNT(*) AS total_rows
        FROM coverage;
    """,

    "coverage_missing": """
        SELECT COUNT(*) AS missing_coverage
        FROM coverage
        WHERE coverage IS NULL;
    """,

    "coverage_invalid": """
        SELECT COUNT(*) AS invalid_coverage
        FROM coverage
        WHERE coverage < 0
           OR coverage > 100;
    """,

    "coverage_missing_country_code": """
        SELECT COUNT(*) AS missing_country_code
        FROM coverage
        WHERE code IS NULL;
    """,

    "coverage_missing_country_name": """
        SELECT COUNT(*) AS missing_country_name
        FROM coverage
        WHERE name IS NULL;
    """
}


quality_results = []


for metric, query in quality_queries.items():

    result = pd.read_sql_query(query, conn)

    value = result.iloc[0, 0]

    quality_results.append({
        "metric": metric,
        "value": value
    })


quality_df = pd.DataFrame(quality_results)


print("\n" + "=" * 70)
print("DATA QUALITY SUMMARY")
print("=" * 70)

print(quality_df)


quality_path = OUTPUT_DIR / "09_data_quality_summary.csv"

quality_df.to_csv(
    quality_path,
    index=False
)

print(f"\nSaved to: {quality_path}")


# ---------------------------------------------------------
# Close database connection
# ---------------------------------------------------------

conn.close()


print("\n" + "=" * 70)
print("SQL ANALYSIS COMPLETED SUCCESSFULLY")
print("=" * 70)