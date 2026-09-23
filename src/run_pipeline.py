from data_cleaning import clean_and_save
from load_sql import load
from eda import run

if __name__ == "__main__":
    print("=== 1. CLEANING ===")
    clean_and_save()
    print("\n=== 2. SQL LOAD ===")
    load()
    print("\n=== 3. EDA ===")
    run()
    print("\nPipeline complete.")
