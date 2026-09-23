import re
import pandas as pd

from config import FILES, PROCESSED


def clean_columns(df):
    """
    Standardize column names:
    - Convert to lowercase
    - Replace spaces/special characters with _
    - Remove duplicate underscores
    """
    df = df.copy()

    df.columns = [
        re.sub(
            r"_+",
            "_",
            re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower())
        ).strip("_")
        for column in df.columns
    ]

    return df


def standardize(df, table_name):
    """
    Standardize data types and common column names.
    """

    df = clean_columns(df)

    # Common column-name variations
    aliases = {
        "target_number": "target_number",
        "target_pop": "target_pop",
        "dodge": "doses",
        "dose": "doses",
        "iso_3_code": "code",
        "country_name": "name",
        "who_region": "who_region",
        "coverage_category_description":
            "coverage_category_description",
        "antigen_description":
            "antigen_description",
        "disease_description":
            "disease_description",
    }

    df = df.rename(
        columns={
            old: new
            for old, new in aliases.items()
            if old in df.columns
        }
    )

    # Convert year to numeric
    if "year" in df.columns:
        df["year"] = pd.to_numeric(
            df["year"],
            errors="coerce"
        ).astype("Int64")

    # Numeric columns
    numeric_columns = [
        "coverage",
        "incidence_rate",
        "cases",
        "target_number",
        "doses",
        "target_pop",
        "schedule_rounds",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # Clean text columns
    for column in df.select_dtypes(
        include=["object", "string"]
    ).columns:

        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

        df[column] = df[column].replace(
            {
                "": pd.NA,
                "nan": pd.NA,
                "NaN": pd.NA,
                "None": pd.NA,
                "null": pd.NA,
            }
        )

    return df


def read_source_file(file_path):
    """
    Read Excel or CSV source files.
    """

    extension = file_path.suffix.lower()

    if extension in [".xlsx", ".xls"]:
        return pd.read_excel(file_path)

    elif extension == ".csv":
        return pd.read_csv(file_path)

    else:
        raise ValueError(
            f"Unsupported file format: {extension}"
        )


def clean_and_save():

    # Make sure processed directory exists
    PROCESSED.mkdir(
        parents=True,
        exist_ok=True
    )

    cleaned_data = {}

    print("\nStarting data cleaning...\n")

    for table_name, file_path in FILES.items():

        print("=" * 60)
        print(f"Processing: {table_name}")
        print(f"File: {file_path.name}")

        # Check whether file exists
        if not file_path.exists():

            print(
                f"[ERROR] File not found: {file_path}"
            )

            continue

        try:

            # -------------------------------------------------
            # 1. READ DATA
            # -------------------------------------------------

            df = read_source_file(file_path)

            print(
                f"Original shape: {df.shape}"
            )

            # -------------------------------------------------
            # 2. STANDARDIZE DATA
            # -------------------------------------------------

            df = standardize(
                df,
                table_name
            )

            # -------------------------------------------------
            # 3. REMOVE DUPLICATES
            # -------------------------------------------------

            before_duplicates = len(df)

            df = df.drop_duplicates()

            duplicates_removed = (
                before_duplicates - len(df)
            )

            print(
                f"Duplicates removed: "
                f"{duplicates_removed}"
            )

            # -------------------------------------------------
            # 4. CHECK MISSING VALUES
            # -------------------------------------------------

            missing_values = (
                df.isnull()
                .sum()
                .sort_values(
                    ascending=False
                )
            )

            missing_values = (
                missing_values[
                    missing_values > 0
                ]
            )

            if len(missing_values) > 0:

                print("\nMissing values:")

                for column, count in (
                    missing_values.items()
                ):
                    print(
                        f"  {column}: {count}"
                    )

            else:

                print(
                    "Missing values: None"
                )

            # -------------------------------------------------
            # 5. SAVE CLEANED DATA
            # -------------------------------------------------

            output_file = (
                PROCESSED
                / f"{table_name}_clean.csv"
            )

            df.to_csv(
                output_file,
                index=False
            )

            cleaned_data[
                table_name
            ] = df

            print(
                f"\nCleaned shape: {df.shape}"
            )

            print(
                f"Saved to: {output_file}"
            )

        except Exception as error:

            print(
                f"[ERROR] Failed to process "
                f"{file_path.name}"
            )

            print(
                f"Reason: {error}"
            )

    print("\n" + "=" * 60)
    print("DATA CLEANING COMPLETED")
    print("=" * 60)

    return cleaned_data


if __name__ == "__main__":
    clean_and_save()