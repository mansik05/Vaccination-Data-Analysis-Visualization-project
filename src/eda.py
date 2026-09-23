import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from config import PROCESSED, OUTPUTS

sns.set_theme(style="whitegrid")
OUTPUTS.mkdir(parents=True, exist_ok=True)

def load(name):
    return pd.read_csv(PROCESSED / f"{name}_clean.csv")

def run():
    cov_path = PROCESSED / "coverage_clean.csv"
    inc_path = PROCESSED / "incidence_clean.csv"
    if not cov_path.exists():
        print("Run data_cleaning.py first.")
        return

    cov = pd.read_csv(cov_path)
    if {"year","coverage"}.issubset(cov.columns):
        yearly = cov.groupby("year", dropna=True)["coverage"].mean()
        plt.figure(figsize=(10,5))
        yearly.plot(marker="o")
        plt.title("Average Vaccination Coverage Over Time")
        plt.ylabel("Coverage (%)")
        plt.tight_layout()
        plt.savefig(OUTPUTS / "vaccination_trend.png", dpi=160)
        plt.close()

    if {"name","coverage"}.issubset(cov.columns):
        low = cov.groupby("name")["coverage"].mean().sort_values().head(15)
        plt.figure(figsize=(9,6))
        low.sort_values().plot(kind="barh")
        plt.title("Countries with Lowest Average Coverage")
        plt.xlabel("Coverage (%)")
        plt.tight_layout()
        plt.savefig(OUTPUTS / "low_coverage_countries.png", dpi=160)
        plt.close()

    if inc_path.exists():
        inc = pd.read_csv(inc_path)
        if {"incidence_rate","year"}.issubset(inc.columns):
            yearly_inc = inc.groupby("year")["incidence_rate"].mean()
            plt.figure(figsize=(10,5))
            yearly_inc.plot(marker="o")
            plt.title("Average Disease Incidence Rate Over Time")
            plt.ylabel("Incidence rate")
            plt.tight_layout()
            plt.savefig(OUTPUTS / "incidence_trend.png", dpi=160)
            plt.close()

    print("EDA charts written to outputs/")

if __name__ == "__main__":
    run()
