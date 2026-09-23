import pandas as pd
from sqlalchemy import create_engine, text

from config import PROCESSED, DATABASE_URL


# ---------------------------------------------------------
# TABLE CONFIGURATION
# ---------------------------------------------------------

TABLES = {
    "coverage": "coverage_clean.csv",
    "incidence_rate": "incidence_clean.csv",
    "reported_cases": "reported_cases_clean.csv",
    "vaccine_introduction": "vaccine_introduction_clean.csv",
    "vaccine_schedule": "vaccine_schedule_clean.csv",
}


# ---------------------------------------------------------
# LOAD DATA INTO SQL
# ---------------------------------------------------------

def load():

    print("\nStarting SQL database loading...\n")

    # Create database connection
    engine = create_engine(DATABASE_URL)

    for table_name, file_name in TABLES.items():

        file_path = PROCESSED / file_name

        print("=" * 60)
        print(f"Loading table: {table_name}")
        print(f"File: {file_name}")

        # Check file exists
        if not file_path.exists():

            print(
                f"[ERROR] File not found: {file_path}"
            )

            continue

        try:

            # -------------------------------------------------
            # READ CLEANED CSV
            # -------------------------------------------------

            df = pd.read_csv(file_path)

            print(
                f"Rows: {len(df):,}"
            )

            print(
                f"Columns: {len(df.columns)}"
            )

            # -------------------------------------------------
            # LOAD INTO DATABASE
            # -------------------------------------------------

            df.to_sql(
                table_name,
                engine,
                if_exists="replace",
                index=False
            )

            print(
                f"[OK] Loaded {len(df):,} rows "
                f"into {table_name}"
            )

        except Exception as error:

            print(
                f"[ERROR] Failed to load {table_name}"
            )

            print(
                f"Reason: {error}"
            )

    # ---------------------------------------------------------
    # CREATE INDEXES
    # ---------------------------------------------------------

    print("\nCreating database indexes...\n")

    if "sqlite" in DATABASE_URL.lower():

        with engine.begin() as connection:

            # Coverage
            connection.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_coverage_code_year
                    ON coverage(code, year)
                    """
                )
            )

            connection.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_coverage_antigen
                    ON coverage(antigen)
                    """
                )
            )

            # Incidence
            connection.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_incidence_code_year
                    ON incidence_rate(code, year)
                    """
                )
            )

            connection.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_incidence_disease
                    ON incidence_rate(disease)
                    """
                )
            )

            # Reported cases
            connection.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_cases_code_year
                    ON reported_cases(code, year)
                    """
                )
            )

            connection.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_cases_disease
                    ON reported_cases(disease)
                    """
                )
            )

            # Vaccine introduction
            connection.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_intro_code_year
                    ON vaccine_introduction(code, year)
                    """
                )
            )

            # Vaccine schedule
            connection.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_schedule_code_year
                    ON vaccine_schedule(code, year)
                    """
                )
            )

            print("[OK] SQLite indexes created")

    else:

        print(
            "[INFO] Index creation for non-SQLite "
            "databases should be handled by the SQL schema."
        )

    # ---------------------------------------------------------
    # VERIFY TABLES
    # ---------------------------------------------------------

    print("\nVerifying database tables...\n")

    with engine.connect() as connection:

        if "sqlite" in DATABASE_URL.lower():

            result = connection.execute(
                text(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type='table'
                    ORDER BY name
                    """
                )
            )

            tables = [
                row[0]
                for row in result.fetchall()
            ]

        else:

            tables = list(TABLES.keys())

    print("Tables available:")

    for table in tables:
        print(f"  ✓ {table}")

    print("\n" + "=" * 60)
    print("SQL DATABASE LOADING COMPLETED")
    print("=" * 60)


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

if __name__ == "__main__":
    load()