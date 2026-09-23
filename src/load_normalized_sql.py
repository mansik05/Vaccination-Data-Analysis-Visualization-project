import sqlite3
from pathlib import Path
import hashlib
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
DB_PATH = ROOT / "data" / "vaccination_normalized.db"
SCHEMA_PATH = ROOT / "sql" / "schema_normalized.sql"

FILES = {
    "coverage": PROCESSED / "coverage_clean.csv",
    "incidence": PROCESSED / "incidence_clean.csv",
    "cases": PROCESSED / "reported_cases_clean.csv",
    "introduction": PROCESSED / "vaccine_introduction_clean.csv",
    "schedule": PROCESSED / "vaccine_schedule_clean.csv",
}


def clean_text(value):
    if pd.isna(value):
        return None
    value = str(value).strip()
    return value if value else None


def read_csv(path):
    df = pd.read_csv(path, low_memory=False)
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def country_rows(df, code_col="code", name_col="name", region_col=None):
    out = pd.DataFrame()
    out["country_code"] = df[code_col].map(clean_text)
    out["country_name"] = df[name_col].map(clean_text)
    if region_col and region_col in df.columns:
        out["who_region"] = df[region_col].map(clean_text)
    else:
        out["who_region"] = None
    return out.dropna(subset=["country_code", "country_name"])


def intro_code(description):
    """Stable surrogate natural code for introduction-only vaccine descriptions."""
    digest = hashlib.sha1(description.encode("utf-8")).hexdigest()[:12]
    return f"INTRO_{digest}"


def main():
    print("\nStarting NORMALIZED SQL database loading...")

    coverage = read_csv(FILES["coverage"])
    incidence = read_csv(FILES["incidence"])
    cases = read_csv(FILES["cases"])
    introduction = read_csv(FILES["introduction"])
    schedule = read_csv(FILES["schedule"])

    # Restrict the first three datasets to actual country records.
    if "group" in coverage.columns:
        coverage = coverage[coverage["group"].astype(str).str.upper().eq("COUNTRIES")].copy()
    if "group" in incidence.columns:
        incidence = incidence[incidence["group"].astype(str).str.upper().eq("COUNTRIES")].copy()
    if "group" in cases.columns:
        cases = cases[cases["group"].astype(str).str.upper().eq("COUNTRIES")].copy()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")

    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema)

    # ============================================================
    # 1. DIMENSIONS
    # ============================================================

    countries = pd.concat([
        country_rows(coverage, "code", "name"),
        country_rows(incidence, "code", "name"),
        country_rows(cases, "code", "name"),
        country_rows(introduction, "code", "countryname", "who_region"),
        country_rows(schedule, "code", "countryname", "who_region"),
    ], ignore_index=True)

    countries = (
        countries.dropna(subset=["country_code", "country_name"])
        .sort_values(["country_code", "country_name"])
        .drop_duplicates(subset=["country_code"], keep="first")
    )

    # Prefer a non-null WHO region when available.
    regions = pd.concat([
        country_rows(introduction, "code", "countryname", "who_region"),
        country_rows(schedule, "code", "countryname", "who_region"),
    ], ignore_index=True)
    region_map = (
        regions.dropna(subset=["country_code", "who_region"])
        .drop_duplicates("country_code")
        .set_index("country_code")["who_region"]
        .to_dict()
    )
    countries["who_region"] = countries.apply(
        lambda r: r["who_region"] if r["who_region"] else region_map.get(r["country_code"]),
        axis=1
    )

    conn.executemany(
        """
        INSERT INTO dim_country(country_code, country_name, who_region)
        VALUES (?, ?, ?)
        """,
        countries[["country_code", "country_name", "who_region"]].itertuples(index=False, name=None),
    )

    all_years = pd.concat([
        coverage.get("year", pd.Series(dtype=float)),
        incidence.get("year", pd.Series(dtype=float)),
        cases.get("year", pd.Series(dtype=float)),
        introduction.get("year", pd.Series(dtype=float)),
        schedule.get("year", pd.Series(dtype=float)),
    ], ignore_index=True)

    years = pd.to_numeric(all_years, errors="coerce").dropna()
    years = sorted({int(y) for y in years if 1900 <= int(y) <= 2100})

    conn.executemany(
        "INSERT INTO dim_year(year_id, year) VALUES (?, ?)",
        [(y, y) for y in years],
    )

    # Antigens
    ant = coverage[["antigen", "antigen_description"]].copy()
    ant["antigen"] = ant["antigen"].map(clean_text)
    ant["antigen_description"] = ant["antigen_description"].map(clean_text)
    ant = ant.dropna(subset=["antigen"]).drop_duplicates("antigen")
    conn.executemany(
        """
        INSERT INTO dim_antigen(antigen_code, antigen_description)
        VALUES (?, ?)
        """,
        ant.itertuples(index=False, name=None),
    )

    # Diseases
    dis_parts = []
    for df in [incidence, cases]:
        if "disease" in df.columns:
            tmp = df[["disease", "disease_description"]].copy()
            tmp["disease"] = tmp["disease"].map(clean_text)
            tmp["disease_description"] = tmp["disease_description"].map(clean_text)
            dis_parts.append(tmp)
    diseases = pd.concat(dis_parts, ignore_index=True).dropna(subset=["disease"])
    diseases = diseases.drop_duplicates("disease")
    conn.executemany(
        """
        INSERT INTO dim_disease(disease_code, disease_description)
        VALUES (?, ?)
        """,
        diseases.itertuples(index=False, name=None),
    )

    # Coverage categories
    cc = coverage[["coverage_category", "coverage_category_description"]].copy()
    cc["coverage_category"] = cc["coverage_category"].map(clean_text)
    cc["coverage_category_description"] = cc["coverage_category_description"].map(clean_text)
    cc = cc.dropna(subset=["coverage_category"]).drop_duplicates("coverage_category")
    conn.executemany(
        """
        INSERT INTO dim_coverage_category(
            coverage_category_code, coverage_category_description
        ) VALUES (?, ?)
        """,
        cc.itertuples(index=False, name=None),
    )

    # Vaccines: schedule has code + description; introduction has description only.
    vaccines = schedule[["vaccinecode", "vaccine_description"]].copy()
    vaccines["vaccinecode"] = vaccines["vaccinecode"].map(clean_text)
    vaccines["vaccine_description"] = vaccines["vaccine_description"].map(clean_text)
    vaccines = vaccines.dropna(subset=["vaccine_description"])
    vaccines = vaccines.drop_duplicates("vaccinecode")

    intro_vaccines = introduction[["description"]].copy()
    intro_vaccines["description"] = intro_vaccines["description"].map(clean_text)
    intro_vaccines = intro_vaccines.dropna().drop_duplicates()

    vaccine_rows = []
    seen_codes = set()

    for row in vaccines.itertuples(index=False):
        code = row.vaccinecode
        desc = row.vaccine_description
        if code is None:
            code = intro_code(desc)
        if code not in seen_codes:
            vaccine_rows.append((code, desc))
            seen_codes.add(code)

    # Add introduction-only vaccine descriptions when not already represented.
    existing_desc = {str(x[1]).strip().lower() for x in vaccine_rows}
    for desc in intro_vaccines["description"]:
        if desc.lower() not in existing_desc:
            code = intro_code(desc)
            vaccine_rows.append((code, desc))
            existing_desc.add(desc.lower())

    conn.executemany(
        """
        INSERT INTO dim_vaccine(vaccine_code, vaccine_description)
        VALUES (?, ?)
        """,
        vaccine_rows,
    )

    # Target populations
    tp = schedule[["targetpop", "targetpop_description"]].copy()
    tp["targetpop"] = tp["targetpop"].map(clean_text)
    tp["targetpop_description"] = tp["targetpop_description"].map(clean_text)
    tp = tp.dropna(subset=["targetpop"]).drop_duplicates("targetpop")
    conn.executemany(
        """
        INSERT INTO dim_target_population(target_pop, target_pop_description)
        VALUES (?, ?)
        """,
        tp.itertuples(index=False, name=None),
    )

    # Geographic areas
    geo = schedule[["geoarea"]].copy()
    geo["geoarea"] = geo["geoarea"].map(clean_text)
    geo = geo.dropna().drop_duplicates()
    conn.executemany(
        "INSERT INTO dim_geoarea(geoarea) VALUES (?)",
        [(x,) for x in geo["geoarea"]],
    )

    conn.commit()

    # Lookup dictionaries
    def lookup(table, key_col, id_col, value_col=None):
        rows = conn.execute(
            f"SELECT {id_col}, {key_col}" + (f", {value_col}" if value_col else f" FROM {table}")
        ).fetchall()
        if value_col:
            return {(r[1], r[2]): r[0] for r in rows}
        return {r[1]: r[0] for r in rows}

    country_id = lookup("dim_country", "country_code", "country_id")
    year_id = lookup("dim_year", "year", "year_id")
    antigen_id = lookup("dim_antigen", "antigen_code", "antigen_id")
    disease_id = lookup("dim_disease", "disease_code", "disease_id")
    category_id = lookup("dim_coverage_category", "coverage_category_code", "coverage_category_id")
    target_id = lookup("dim_target_population", "target_pop", "target_pop_id")
    geo_id = lookup("dim_geoarea", "geoarea", "geoarea_id")

    vaccine_rows_db = conn.execute(
        "SELECT vaccine_id, vaccine_code, vaccine_description FROM dim_vaccine"
    ).fetchall()
    vaccine_by_code = {r[1]: r[0] for r in vaccine_rows_db}
    vaccine_by_desc = {r[2].strip().lower(): r[0] for r in vaccine_rows_db}

    # ============================================================
    # 2. FACT TABLES
    # ============================================================

    # Coverage
    cv = coverage.copy()
    cv["country_id"] = cv["code"].map(country_id)
    cv["year_num"] = pd.to_numeric(cv["year"], errors="coerce")
    cv["year_id"] = cv["year_num"].map(year_id)
    cv["antigen_id"] = cv["antigen"].map(lambda x: antigen_id.get(clean_text(x)))
    cv["category_id"] = cv["coverage_category"].map(lambda x: category_id.get(clean_text(x)))
    for col in ["target_number", "doses", "coverage"]:
        cv[col] = pd.to_numeric(cv[col], errors="coerce")

    # The normalized schema enforces coverage 0..100.
    cv = cv[
        cv["country_id"].notna()
        & cv["year_id"].notna()
        & cv["antigen_id"].notna()
        & cv["coverage"].isna() | (
            cv["coverage"].between(0, 100, inclusive="both")
        )
    ].copy()

    # Re-apply key requirements after boolean expression.
    cv = cv[
        cv["country_id"].notna()
        & cv["year_id"].notna()
        & cv["antigen_id"].notna()
    ]

    conn.executemany(
        """
        INSERT INTO fact_coverage(
            country_id, year_id, antigen_id, coverage_category_id,
            target_number, doses, coverage
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        cv[
            ["country_id", "year_id", "antigen_id", "category_id",
             "target_number", "doses", "coverage"]
        ].itertuples(index=False, name=None),
    )

    # Incidence
    inc = incidence.copy()
    inc["country_id"] = inc["code"].map(country_id)
    inc["year_num"] = pd.to_numeric(inc["year"], errors="coerce")
    inc["year_id"] = inc["year_num"].map(year_id)
    inc["disease_id"] = inc["disease"].map(lambda x: disease_id.get(clean_text(x)))
    inc["denominator"] = pd.to_numeric(inc["denominator"], errors="coerce")
    inc["incidence_rate"] = pd.to_numeric(inc["incidence_rate"], errors="coerce")
    inc = inc[
        inc["country_id"].notna()
        & inc["year_id"].notna()
        & inc["disease_id"].notna()
    ]

    conn.executemany(
        """
        INSERT INTO fact_incidence_rate(
            country_id, year_id, disease_id, denominator, incidence_rate
        ) VALUES (?, ?, ?, ?, ?)
        """,
        inc[
            ["country_id", "year_id", "disease_id", "denominator", "incidence_rate"]
        ].itertuples(index=False, name=None),
    )

    # Reported cases
    rc = cases.copy()
    rc["country_id"] = rc["code"].map(country_id)
    rc["year_num"] = pd.to_numeric(rc["year"], errors="coerce")
    rc["year_id"] = rc["year_num"].map(year_id)
    rc["disease_id"] = rc["disease"].map(lambda x: disease_id.get(clean_text(x)))
    rc["cases"] = pd.to_numeric(rc["cases"], errors="coerce")
    rc = rc[
        rc["country_id"].notna()
        & rc["year_id"].notna()
        & rc["disease_id"].notna()
    ]

    conn.executemany(
        """
        INSERT INTO fact_reported_cases(
            country_id, year_id, disease_id, cases
        ) VALUES (?, ?, ?, ?)
        """,
        rc[
            ["country_id", "year_id", "disease_id", "cases"]
        ].itertuples(index=False, name=None),
    )

    # Vaccine introduction
    vi = introduction.copy()
    vi["country_id"] = vi["code"].map(country_id)
    vi["year_num"] = pd.to_numeric(vi["year"], errors="coerce")
    vi["year_id"] = vi["year_num"].map(year_id)
    vi["vaccine_id"] = vi["description"].map(
        lambda x: vaccine_by_desc.get(clean_text(x).lower() if clean_text(x) else None)
    )
    vi = vi[
        vi["country_id"].notna()
        & vi["year_id"].notna()
        & vi["vaccine_id"].notna()
    ]

    conn.executemany(
        """
        INSERT INTO fact_vaccine_introduction(
            country_id, year_id, vaccine_id, intro
        ) VALUES (?, ?, ?, ?)
        """,
        vi[
            ["country_id", "year_id", "vaccine_id", "intro"]
        ].itertuples(index=False, name=None),
    )

    # Vaccine schedule
    vs = schedule.copy()
    vs["country_id"] = vs["code"].map(country_id)
    vs["year_num"] = pd.to_numeric(vs["year"], errors="coerce")
    vs["year_id"] = vs["year_num"].map(year_id)
    vs["vaccine_id"] = vs["vaccinecode"].map(lambda x: vaccine_by_code.get(clean_text(x)))
    vs["target_pop_id"] = vs["targetpop"].map(lambda x: target_id.get(clean_text(x)))
    vs["geoarea_id"] = vs["geoarea"].map(lambda x: geo_id.get(clean_text(x)))
    vs = vs[
        vs["country_id"].notna()
        & vs["year_id"].notna()
        & vs["vaccine_id"].notna()
    ]

    for col in ["schedulerounds", "ageadministered", "sourcecomment"]:
        vs[col] = vs[col].map(clean_text)

    conn.executemany(
        """
        INSERT INTO fact_vaccine_schedule(
            country_id, year_id, vaccine_id, target_pop_id, geoarea_id,
            schedule_rounds, age_administered, source_comment
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        vs[
            ["country_id", "year_id", "vaccine_id", "target_pop_id",
             "geoarea_id", "schedulerounds", "ageadministered", "sourcecomment"]
        ].itertuples(index=False, name=None),
    )

    conn.commit()

    # ============================================================
    # 3. VALIDATION
    # ============================================================

    print("\nNormalized tables:")
    for row in conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%'
        ORDER BY type, name
    """):
        name = row[0]
        count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        print(f"  {name}: {count:,}")

    fk_errors = conn.execute("PRAGMA foreign_key_check;").fetchall()
    print(f"\nForeign-key violations: {len(fk_errors)}")

    print("\nPrimary/foreign-key normalization checks:")
    print("  ✓ Dimension tables separate reusable entities")
    print("  ✓ Fact tables reference dimension IDs")
    print("  ✓ Foreign-key enforcement enabled")
    print("  ✓ Coverage constrained to 0–100 when present")
    print("  ✓ Country aggregate rows excluded from country-level facts")

    conn.close()
    print(f"\nDatabase created: {DB_PATH}")
    print("NORMALIZED SQL DATABASE LOADING COMPLETED")


if __name__ == "__main__":
    main()
