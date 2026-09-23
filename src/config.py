from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///vaccination.db")

FILES = {
    "coverage": RAW / "coverage-data.xlsx",
    "incidence": RAW / "incidence-rate-data.xlsx",
    "reported_cases": RAW / "reported-cases-data.xlsx",
    "vaccine_introduction": RAW / "vaccine-introduction-data.xlsx",
    "vaccine_schedule": RAW / "vaccine-schedule-data.xlsx",
}