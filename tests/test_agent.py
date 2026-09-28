import os

import pytest

# Point at a throwaway SQLite file before importing anything that touches app.db.
os.environ["DATABASE_URL"] = "sqlite:///./test_app.db"
os.environ.pop("ANTHROPIC_API_KEY", None)  # force DEMO_MODE for deterministic tests

from app.db import Base, engine  # noqa: E402
from app.schema import CountyServiceCoverage  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.agent import answer_question  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def seeded_db():
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all([
            CountyServiceCoverage(
                county="Bomet", region="Rift Valley", reporting_year=2024,
                population=1000000, health_facility_coverage_pct=60.0,
                water_access_pct=55.0, electricity_access_pct=50.0,
                education_enrollment_pct=70.0, road_coverage_km_per_1000=2.0,
            ),
            CountyServiceCoverage(
                county="Nairobi", region="Nairobi", reporting_year=2024,
                population=4500000, health_facility_coverage_pct=95.0,
                water_access_pct=90.0, electricity_access_pct=92.0,
                education_enrollment_pct=88.0, road_coverage_km_per_1000=6.0,
            ),
        ])
        session.commit()
    yield
    Base.metadata.drop_all(engine)
    if os.path.exists("./test_app.db"):
        os.remove("./test_app.db")


def test_answers_gap_question():
    result = answer_question("Which counties have the largest gaps in reported service coverage?")
    assert result.error is None
    assert len(result.rows) >= 1
    assert "Bomet" in {r["county"] for r in result.rows}
    assert result.summary


def test_answers_top_n_question():
    result = answer_question("Top 2 counties by water access")
    assert result.error is None
    assert result.rows[0]["county"] == "Nairobi"


def test_rejects_empty_question():
    result = answer_question("")
    assert result.error is not None
