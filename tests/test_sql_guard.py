import pytest

from app.sql_guard import SqlGuardError, validate_and_finalize


def test_allows_simple_select():
    sql = "SELECT county, region FROM county_service_coverage LIMIT 5"
    out = validate_and_finalize(sql)
    assert out.startswith("SELECT county, region")
    assert "LIMIT 5" in out


def test_adds_limit_when_missing():
    sql = "SELECT county FROM county_service_coverage"
    out = validate_and_finalize(sql)
    assert "LIMIT 100" in out


def test_caps_excessive_limit():
    sql = "SELECT county FROM county_service_coverage LIMIT 999999"
    out = validate_and_finalize(sql)
    assert "LIMIT 500" in out


@pytest.mark.parametrize("sql", [
    "DROP TABLE county_service_coverage",
    "DELETE FROM county_service_coverage",
    "INSERT INTO county_service_coverage (county) VALUES ('x')",
    "UPDATE county_service_coverage SET county='x'",
    "SELECT 1; DROP TABLE county_service_coverage",
])
def test_rejects_destructive_statements(sql):
    with pytest.raises(SqlGuardError):
        validate_and_finalize(sql)


def test_rejects_unknown_table():
    with pytest.raises(SqlGuardError):
        validate_and_finalize("SELECT * FROM users")


def test_rejects_unknown_column():
    with pytest.raises(SqlGuardError):
        validate_and_finalize("SELECT password FROM county_service_coverage")
