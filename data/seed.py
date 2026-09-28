"""
Loads data/county_service_coverage.csv into the configured database
(SQLite by default, or DATABASE_URL if set).

Run:
    python data/generate_data.py   # if you haven't already
    python data/seed.py
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import engine, Base  # noqa: E402
from app.schema import CountyServiceCoverage  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

CSV_PATH = os.path.join(os.path.dirname(__file__), "county_service_coverage.csv")


def main():
    if not os.path.exists(CSV_PATH):
        raise SystemExit("Run `python data/generate_data.py` first to create the CSV.")

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with open(CSV_PATH, newline="") as f, Session(engine) as session:
        reader = csv.DictReader(f)
        rows = [
            CountyServiceCoverage(
                county=r["county"],
                region=r["region"],
                reporting_year=int(r["reporting_year"]),
                population=int(r["population"]),
                health_facility_coverage_pct=float(r["health_facility_coverage_pct"]),
                water_access_pct=float(r["water_access_pct"]),
                electricity_access_pct=float(r["electricity_access_pct"]),
                education_enrollment_pct=float(r["education_enrollment_pct"]),
                road_coverage_km_per_1000=float(r["road_coverage_km_per_1000"]),
            )
            for r in reader
        ]
        session.add_all(rows)
        session.commit()
        print(f"Seeded {len(rows)} rows into the database.")


if __name__ == "__main__":
    main()
