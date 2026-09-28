from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

TABLE_NAME = "county_service_coverage"


class CountyServiceCoverage(Base):
    """One row = one county's reported service-coverage indicators for one year."""

    __tablename__ = TABLE_NAME

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    county: Mapped[str] = mapped_column(String(64), nullable=False)
    region: Mapped[str] = mapped_column(String(64), nullable=False)
    reporting_year: Mapped[int] = mapped_column(Integer, nullable=False)
    population: Mapped[int] = mapped_column(Integer, nullable=False)
    health_facility_coverage_pct: Mapped[float] = mapped_column(Float, nullable=False)
    water_access_pct: Mapped[float] = mapped_column(Float, nullable=False)
    electricity_access_pct: Mapped[float] = mapped_column(Float, nullable=False)
    education_enrollment_pct: Mapped[float] = mapped_column(Float, nullable=False)
    road_coverage_km_per_1000: Mapped[float] = mapped_column(Float, nullable=False)


# Explicit whitelist the SQL guard checks generated queries against.
# Keeping this separate from the ORM model definition (rather than introspecting
# it) makes the security boundary easy to audit at a glance.
ALLOWED_TABLES = {TABLE_NAME}
ALLOWED_COLUMNS = {
    "id", "county", "region", "reporting_year", "population",
    "health_facility_coverage_pct", "water_access_pct", "electricity_access_pct",
    "education_enrollment_pct", "road_coverage_km_per_1000",
}

SCHEMA_DESCRIPTION = f"""\
Table: {TABLE_NAME}
Columns:
  - county (text): county name
  - region (text): region the county belongs to
  - reporting_year (integer): year of the reported figures (2022-2024)
  - population (integer): estimated county population
  - health_facility_coverage_pct (float): % of population within reach of a health facility
  - water_access_pct (float): % of population with access to clean water
  - electricity_access_pct (float): % of population with electricity access
  - education_enrollment_pct (float): % net enrollment rate
  - road_coverage_km_per_1000 (float): km of maintained road per 1000 people
"""
