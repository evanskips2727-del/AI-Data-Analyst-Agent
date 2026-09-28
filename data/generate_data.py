"""
Generates a synthetic, de-identified county-level service-coverage dataset,
modeled loosely on the kind of M&E / service-delivery indicators reported at
county level in Kenya. No real records are used.

Run:
    python data/generate_data.py
Produces:
    data/county_service_coverage.csv
"""
import csv
import os
import random

random.seed(42)

COUNTIES = [
    ("Mombasa", "Coast"), ("Kwale", "Coast"), ("Kilifi", "Coast"),
    ("Tana River", "Coast"), ("Lamu", "Coast"), ("Taita-Taveta", "Coast"),
    ("Garissa", "North Eastern"), ("Wajir", "North Eastern"), ("Mandera", "North Eastern"),
    ("Marsabit", "Eastern"), ("Isiolo", "Eastern"), ("Meru", "Eastern"),
    ("Tharaka-Nithi", "Eastern"), ("Embu", "Eastern"), ("Kitui", "Eastern"),
    ("Machakos", "Eastern"), ("Makueni", "Eastern"), ("Nyandarua", "Central"),
    ("Nyeri", "Central"), ("Kirinyaga", "Central"), ("Murang'a", "Central"),
    ("Kiambu", "Central"), ("Turkana", "Rift Valley"), ("West Pokot", "Rift Valley"),
    ("Samburu", "Rift Valley"), ("Trans-Nzoia", "Rift Valley"), ("Uasin Gishu", "Rift Valley"),
    ("Elgeyo-Marakwet", "Rift Valley"), ("Nandi", "Rift Valley"), ("Baringo", "Rift Valley"),
    ("Laikipia", "Rift Valley"), ("Nakuru", "Rift Valley"), ("Narok", "Rift Valley"),
    ("Kajiado", "Rift Valley"), ("Kericho", "Rift Valley"), ("Bomet", "Rift Valley"),
    ("Kakamega", "Western"), ("Vihiga", "Western"), ("Bungoma", "Western"),
    ("Busia", "Western"), ("Siaya", "Nyanza"), ("Kisumu", "Nyanza"),
    ("Homa Bay", "Nyanza"), ("Migori", "Nyanza"), ("Kisii", "Nyanza"),
    ("Nyamira", "Nyanza"), ("Nairobi", "Nairobi"),
]

YEARS = [2022, 2023, 2024]

# Regions get a base "development index" that nudges coverage stats, so gaps
# are structural/plausible rather than pure noise.
REGION_BASE = {
    "Nairobi": 0.90, "Central": 0.80, "Rift Valley": 0.62, "Coast": 0.58,
    "Western": 0.55, "Nyanza": 0.57, "Eastern": 0.53, "North Eastern": 0.32,
}


def clamp(x, lo=1, hi=100):
    return max(lo, min(hi, x))


def make_row(county, region, year):
    base = REGION_BASE[region] * 100
    year_gain = (year - 2022) * random.uniform(0.5, 2.5)  # slow improvement over time
    noise = lambda spread: random.uniform(-spread, spread)

    population = random.randint(150_000, 4_500_000) if county != "Nairobi" else random.randint(4_000_000, 4_800_000)

    return {
        "county": county,
        "region": region,
        "reporting_year": year,
        "population": population,
        "health_facility_coverage_pct": round(clamp(base + year_gain + noise(12)), 1),
        "water_access_pct": round(clamp(base + year_gain + noise(15)), 1),
        "electricity_access_pct": round(clamp(base + year_gain + noise(18)), 1),
        "education_enrollment_pct": round(clamp(base + year_gain + noise(10)), 1),
        "road_coverage_km_per_1000": round(clamp(base / 20 + noise(2), lo=0.5, hi=8), 2),
    }


def main():
    rows = [make_row(c, r, y) for (c, r) in COUNTIES for y in YEARS]

    out_path = os.path.join(os.path.dirname(__file__), "county_service_coverage.csv")
    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
